import copy
import json
import unittest
from pathlib import Path

from engine.v2.contracts import ContractError, SCHEMA_VERSION, validate_pass1_output
from engine.v2.pipeline import Pass1Pipeline
from engine.v2.traditional import TraditionalTarotLayer


V2_DIR = Path(__file__).resolve().parents[1]


def make_pass1_output(
    request,
    *,
    transformation_type="inversion",
    observation_text="A defended structure is described as enclosing the figure.",
    user_evidence="It feels more like a cage than protection.",
):
    return {
        "schema_version": SCHEMA_VERSION,
        "session_id": request["session_id"],
        "card_id": request["card_stimulus"]["id"],
        "orientation": request["orientation"],
        "question_blind": True,
        "symbolic_observations": [
            {
                "id": "obs-1",
                "kind": "noticed",
                "description": observation_text,
                "user_evidence": [user_evidence],
                "card_evidence": [request["card_stimulus"]["visual_inventory"][0]],
                "confidence": "medium",
            }
        ],
        "symbolic_transformations": [
            {
                "id": "tx-1",
                "type": transformation_type,
                "observation_ids": ["obs-1"],
                "description": "The image is reorganized into a different functional relationship.",
                "user_evidence": [user_evidence],
                "card_evidence": [request["canonical_traditional_reading"]["core_themes"][0]],
                "confidence": "medium",
                "alternative_explanation": "The wording may be a direct response to composition rather than a wider pattern.",
                "disconfirming_evidence": [],
            }
        ],
        "psychological_patterns": [
            {
                "id": "pattern-1",
                "scope": "session_pattern",
                "sequence": [
                    "register the overall structure",
                    "reassign the structure's function",
                ],
                "emotional_function": "Makes an ambiguous image easier to organize in this reading.",
                "adaptive_value": "Supports rapid recognition of possible constraints.",
                "current_cost": "May narrow attention before alternative functions are considered.",
                "evidence_transformation_ids": ["tx-1"],
                "user_evidence": [user_evidence],
                "confidence": "medium",
                "alternative_explanation": "This may be a one-off visual association.",
                "disconfirming_evidence": [],
            }
        ],
        "central_pattern_id": "pattern-1",
        "jungian_hypotheses": [
            {
                "concept": "projection",
                "pattern_ids": ["pattern-1"],
                "interpretation": "The image is organized through the user's present meaning-making process.",
                "confidence": "low",
                "alternative_explanation": "Ordinary visual association remains sufficient.",
            }
        ],
        "canonical_traditional_reading": request["canonical_traditional_reading"],
        "compensatory_reading": {
            "tension": "The canonical function differs from the user's assigned function.",
            "card_contribution": "The card preserves a second possible function for the same image.",
            "temporary_third_meaning": "Both protection and constraint can remain available for reflection.",
            "evidence_pattern_ids": ["pattern-1"],
        },
        "epistemic_limits": {
            "weak_signal": False,
            "weak_signal_reason": None,
            "unsupported_inferences": [
                "stable_trait",
                "developmental_origin",
                "childhood_experience",
                "trauma_source",
                "clinical_diagnosis",
            ],
            "limitations": ["One transcript supports a session pattern, not a longitudinal conclusion."],
        },
        "user_display": {
            "integrated_reading": "The reading keeps both the observed reorganization and its alternative visible."
        },
    }


def split_pass1_output(output):
    evidence = {
        key: output[key]
        for key in (
            "schema_version",
            "session_id",
            "card_id",
            "symbolic_observations",
            "symbolic_transformations",
        )
    }
    patterns = {
        key: output[key]
        for key in (
            "schema_version",
            "session_id",
            "card_id",
            "psychological_patterns",
            "central_pattern_id",
            "jungian_hypotheses",
            "epistemic_limits",
        )
    }
    compensation = {
        key: output[key]
        for key in ("schema_version", "session_id", "card_id", "compensatory_reading")
    }
    writing = {
        "schema_version": output["schema_version"],
        "session_id": output["session_id"],
        "card_id": output["card_id"],
        "integrated_reading": output["user_display"]["integrated_reading"],
    }
    return evidence, patterns, compensation, writing


class SchemaContractTests(unittest.TestCase):
    def test_v2_schema_files_are_valid_json(self):
        for path in sorted((V2_DIR / "schemas").glob("*.json")):
            with self.subTest(path=path.name):
                json.loads(path.read_text(encoding="utf-8"))

    def test_pass1_schema_contains_process_pattern_and_question_blind_contract(self):
        schema = json.loads(
            (V2_DIR / "schemas" / "pass1_output.schema.json").read_text(encoding="utf-8")
        )
        self.assertIn("psychological_patterns", schema["required"])
        pattern = schema["$defs"]["psychologicalPattern"]
        self.assertEqual(pattern["properties"]["scope"]["const"], "session_pattern")
        for required in ("sequence", "emotional_function", "adaptive_value", "current_cost"):
            self.assertIn(required, pattern["required"])
        self.assertEqual(schema["properties"]["question_blind"]["const"], True)


class TraditionalLayerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.layer = TraditionalTarotLayer()

    def test_canonical_layer_is_question_and_transcript_blind_for_all_cards(self):
        self.assertEqual(len(self.layer._cards), 78)
        for card in self.layer._cards:
            with self.subTest(card=card["id"]):
                canonical = self.layer.canonical(card["id"], "upright")
                self.assertEqual(set(canonical), {
                    "card_id",
                    "orientation",
                    "stable_meaning",
                    "visual_symbols",
                    "core_themes",
                    "source_refs",
                    "source_status",
                })
                self.assertNotIn("user_question", canonical)
                self.assertNotIn("raw_transcript", canonical)
                self.assertEqual(canonical["source_status"], "provisional_v1_dataset")

    def test_situated_request_accepts_only_canonical_reading_and_question(self):
        request = self.layer.prepare_situated_request(
            "The Hermit", "upright", "What deserves sustained attention?"
        )
        self.assertEqual(set(request), {"canonical_reading", "user_question"})
        contaminated = dict(request, raw_transcript="private association")
        with self.assertRaises(ContractError):
            self.layer.validate_situated_request(contaminated)

    def test_situated_output_preserves_card_identity_and_sources(self):
        request = self.layer.prepare_situated_request(
            "Two of Swords", "reversed", "What tension requires a conscious response?"
        )
        canonical = request["canonical_reading"]
        output = {
            "card_id": canonical["card_id"],
            "orientation": canonical["orientation"],
            "card_role_in_question": "The card describes a decision tension without predicting its outcome.",
            "practical_tension": "Avoidance and premature action remain competing possibilities.",
            "bounded_direction": "Clarify the trade-off before treating uncertainty as an answer.",
            "reflection_point": "Which information would materially change the choice?",
            "source_refs": canonical["source_refs"],
        }
        self.layer.validate_situated_output(output, request)

        output["source_refs"] = []
        with self.assertRaises(ContractError):
            self.layer.validate_situated_output(output, request)


class Pass1PipelineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pipeline = Pass1Pipeline()

    def make_request(self, card, transcript="The figure looks contained, yet ready to move."):
        return self.pipeline.prepare_request(
            session_id=f"session-{card.lower().replace(' ', '-')}",
            card_ref=card,
            orientation="upright",
            raw_transcript=transcript,
        )

    def test_request_is_question_blind_and_keeps_multilingual_features_uncalibrated(self):
        request = self.make_request("The Moon", "嗯，我觉得前面可能还有东西，但我不确定。")
        self.assertEqual(set(request), {
            "schema_version",
            "session_id",
            "card_stimulus",
            "orientation",
            "raw_transcript",
            "features",
            "canonical_traditional_reading",
        })
        self.assertNotIn("user_question", request)
        self.assertNotIn("theme_space", request["card_stimulus"])
        self.assertNotIn("jungian_mapping", request["card_stimulus"])
        self.assertEqual(request["features"]["language_hint"], "zh")
        self.assertEqual(request["features"]["multilingual_feature_status"], "heuristic_unvalidated")

    def test_three_different_cards_and_transformations_validate(self):
        cases = (
            ("Nine of Wands", "inversion", "The boundary feels like confinement."),
            ("Ten of Wands", "addition", "The figure is carrying these for a ruler."),
            ("The Sun", "emotional_recoding", "The bright light feels exposing rather than joyful."),
        )
        for card, transformation_type, evidence in cases:
            with self.subTest(card=card, transformation=transformation_type):
                request = self.make_request(card, evidence)
                output = make_pass1_output(
                    request,
                    transformation_type=transformation_type,
                    user_evidence=evidence,
                )
                validate_pass1_output(output)

    def test_staged_prompts_preserve_input_isolation_and_assemble(self):
        request = self.make_request("Eight of Cups", "The figure is leaving before dawn.")
        output = make_pass1_output(request, transformation_type="temporal_shift")
        evidence, patterns, compensation, writing = split_pass1_output(output)

        observation_prompt = self.pipeline.render_observation_prompt(request)
        self.assertNotIn("canonical_traditional_reading", observation_prompt)
        self.assertNotIn("standard_meaning", observation_prompt)
        self.assertNotIn("jungian_mapping", observation_prompt)

        pattern_prompt = self.pipeline.render_pattern_prompt(request, evidence)
        self.assertNotIn("canonical_traditional_reading", pattern_prompt)
        self.assertNotIn("stable_meaning", pattern_prompt)

        compensation_prompt = self.pipeline.render_compensation_prompt(
            request, evidence, patterns
        )
        self.assertNotIn("raw_transcript", compensation_prompt)
        self.assertNotIn("user_question", compensation_prompt)

        writing_prompt = self.pipeline.render_writing_prompt(
            request, evidence, patterns, compensation
        )
        self.assertNotIn("raw_transcript", writing_prompt)
        self.assertNotIn("user_question", writing_prompt)

        assembled = self.pipeline.assemble(
            request, evidence, patterns, compensation, writing
        )
        self.assertEqual(assembled, output)

    def test_question_or_trait_in_pass1_is_rejected(self):
        request = self.make_request("The Star")
        output = make_pass1_output(request)
        output["user_question"] = "Should I accept the offer?"
        with self.assertRaises(ContractError):
            validate_pass1_output(output)

    def test_weak_signal_does_not_force_a_psychological_pattern(self):
        request = self.make_request("Four of Cups", "A person sits under a tree.")
        output = make_pass1_output(request)
        output["psychological_patterns"] = []
        output["central_pattern_id"] = None
        output["jungian_hypotheses"] = []
        output["compensatory_reading"]["evidence_pattern_ids"] = []
        output["epistemic_limits"]["weak_signal"] = True
        output["epistemic_limits"]["weak_signal_reason"] = (
            "The transcript is descriptive but does not support a coherent process sequence."
        )
        validate_pass1_output(output)

        output = make_pass1_output(request)
        output["psychological_patterns"][0]["scope"] = "stable_trait"
        with self.assertRaises(ContractError):
            validate_pass1_output(output)

    def test_broken_evidence_links_are_rejected(self):
        request = self.make_request("Justice")
        output = make_pass1_output(request)
        output["psychological_patterns"][0]["evidence_transformation_ids"] = ["missing"]
        with self.assertRaises(ContractError):
            validate_pass1_output(output)

    def test_freeze_detects_tampering(self):
        request = self.make_request("The World")
        output = make_pass1_output(request)
        frozen = self.pipeline.freeze(output, request).to_dict()
        self.pipeline.verify_frozen(frozen)

        tampered = copy.deepcopy(frozen)
        tampered["payload"]["user_display"]["integrated_reading"] += " changed"
        with self.assertRaises(ContractError):
            self.pipeline.verify_frozen(tampered)

    def test_prompts_contain_no_exploratory_case_content(self):
        prompts = "\n".join(
            path.read_text(encoding="utf-8").casefold()
            for path in sorted((V2_DIR / "prompts").glob("*.txt"))
        )
        for case_specific_term in ("spain", "serpent", "goddess", "the lovers"):
            self.assertNotIn(case_specific_term, prompts)


if __name__ == "__main__":
    unittest.main()
