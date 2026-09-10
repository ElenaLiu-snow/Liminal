import copy
import unittest
from pathlib import Path

from engine.v2.contracts import ContractError, SCHEMA_VERSION
from engine.v2.pass2 import Pass2Pipeline
from engine.v2.pipeline import Pass1Pipeline
from engine.v2.tests.test_v2_phase3 import make_pass1_output


class Pass2PipelineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pass1_pipeline = Pass1Pipeline()
        cls.pipeline = Pass2Pipeline()

    def make_fixture(self):
        pass1_request = self.pass1_pipeline.prepare_request(
            session_id="phase4-session",
            card_ref="The Chariot",
            orientation="upright",
            raw_transcript="The figure is prepared to move but seems to check both directions first.",
        )
        pass1_output = make_pass1_output(
            pass1_request,
            transformation_type="agency_shift",
            user_evidence="The figure checks both directions before moving.",
        )
        frozen = self.pass1_pipeline.freeze(pass1_output, pass1_request).to_dict()
        question = (
            "I submitted an application, but I worry I will withdraw before the interview."
        )
        request = self.pipeline.prepare_request(
            frozen_pass1=frozen,
            user_question=question,
            question_shift="clarified",
            question_shift_note="The concern narrowed from the outcome to following through.",
        )
        canonical = request["situated_traditional_request"]["canonical_reading"]
        situated = {
            "card_id": canonical["card_id"],
            "orientation": canonical["orientation"],
            "card_role_in_question": "The card frames movement as coordinated rather than guaranteed.",
            "practical_tension": "Preparation can support action or become indefinite delay.",
            "bounded_direction": "Use a limited commitment to learn what action changes.",
            "reflection_point": "What would count as one completed movement?",
            "source_refs": canonical["source_refs"],
        }
        integration = {
            "schema_version": SCHEMA_VERSION,
            "session_id": request["session_id"],
            "card_id": frozen["payload"]["card_id"],
            "orientation": frozen["payload"]["orientation"],
            "pass1_sha256": frozen["pass1_sha256"],
            "question_shift": "clarified",
            "central_axis": "Preparation protects movement but may also postpone it.",
            "pattern_inheritance": [
                {
                    "pattern_id": "pattern-1",
                    "status": "integrated",
                    "rationale": "The revealed concern repeats the frozen sequence of checking before movement.",
                }
            ],
            "question_activation": "Anticipated difficulty may be treated as evidence of future withdrawal.",
            "reality_evidence": [
                {
                    "id": "reality-1",
                    "source": "user_question",
                    "quote": "submitted an application",
                    "role": "action_already_taken",
                    "interpretation": "The feared repetition is not the only available trajectory.",
                }
            ],
            "situated_compensation": "Coordinated movement does not require the absence of hesitation.",
            "integrated_third_meaning": "Preparation can become a container for action rather than its replacement.",
            "bounded_direction": {
                "answer": "Following through is plausible when success is defined as completing the next bounded step.",
                "uncertainty_boundary": "The reading cannot predict the interview or establish a stable pattern.",
                "evidence_pattern_ids": ["pattern-1"],
                "reality_evidence_ids": ["reality-1"],
            },
            "practical_translation": {
                "mode": "action",
                "redefined_success": "Success is attending the interview, not controlling its outcome.",
                "step_or_practice": "Prepare one question and attend the scheduled conversation.",
                "rationale": "This converts coordinated preparation into a finite movement.",
                "evidence_pattern_ids": ["pattern-1"],
                "reality_evidence_ids": ["reality-1"],
            },
            "epistemic_limits": {
                "unsupported_inferences": [
                    "stable_trait",
                    "developmental_origin",
                    "clinical_diagnosis",
                ],
                "limitations": ["A single reading cannot establish future behavior."],
            },
            "takeaway_question": "What is the smallest completed movement that would create new evidence?",
        }
        writing = {
            "schema_version": SCHEMA_VERSION,
            "session_id": request["session_id"],
            "card_id": frozen["payload"]["card_id"],
            "pass1_sha256": frozen["pass1_sha256"],
            "complete_reading": "The frozen pattern meets the revealed question through a bounded next movement.",
            "takeaway_question": integration["takeaway_question"],
        }
        return request, situated, integration, writing

    def test_question_reveal_preserves_frozen_pass1_and_isolates_situated_layer(self):
        request, situated, _, _ = self.make_fixture()
        self.pass1_pipeline.verify_frozen(request["frozen_pass1"])
        situated_request = request["situated_traditional_request"]
        self.assertEqual(set(situated_request), {"canonical_reading", "user_question"})
        self.assertNotIn("frozen_pass1", situated_request)
        self.assertNotIn("psychological_patterns", situated_request)
        prompt = self.pipeline.render_situated_prompt(request)
        self.assertNotIn("pattern-1", prompt)
        self.pipeline.validate_situated_output(request, situated)

    def test_tampered_pass1_cannot_enter_pass2(self):
        request, _, _, _ = self.make_fixture()
        tampered = copy.deepcopy(request["frozen_pass1"])
        tampered["payload"]["user_display"]["integrated_reading"] += " changed"
        with self.assertRaises(ContractError):
            self.pipeline.prepare_request(
                frozen_pass1=tampered,
                user_question="What should receive attention?",
                question_shift="unchanged",
            )

    def test_end_to_end_assembly_preserves_lineage_and_one_display_answer(self):
        request, situated, integration, writing = self.make_fixture()
        output = self.pipeline.assemble(request, situated, integration, writing)
        self.assertEqual(output["pass1_sha256"], request["frozen_pass1"]["pass1_sha256"])
        self.assertEqual(output["user_display"], {
            "complete_reading": writing["complete_reading"],
            "takeaway_question": writing["takeaway_question"],
        })
        self.assertEqual(output["pattern_inheritance"][0]["status"], "integrated")

    def test_every_frozen_pattern_requires_an_explicit_inheritance_status(self):
        request, situated, integration, writing = self.make_fixture()
        integration["pattern_inheritance"] = []
        with self.assertRaises(ContractError):
            self.pipeline.assemble(request, situated, integration, writing)

    def test_reality_evidence_must_be_verbatim_and_cannot_be_invented(self):
        request, situated, integration, writing = self.make_fixture()
        integration["reality_evidence"][0]["quote"] = "completed the interview"
        with self.assertRaises(ContractError):
            self.pipeline.assemble(request, situated, integration, writing)

    def test_writing_cannot_replace_the_takeaway_question(self):
        request, situated, integration, writing = self.make_fixture()
        writing["takeaway_question"] = "What unrelated advice should I follow?"
        with self.assertRaises(ContractError):
            self.pipeline.assemble(request, situated, integration, writing)

    def test_integration_and_writing_prompts_keep_roles_separate(self):
        request, situated, integration, _ = self.make_fixture()
        integration_prompt = self.pipeline.render_integration_prompt(request, situated)
        self.assertIn("frozen_pass1", integration_prompt)
        self.assertIn("submitted an application", integration_prompt)
        writing_prompt = self.pipeline.render_writing_prompt(request, situated, integration)
        self.assertNotIn("raw_transcript", writing_prompt)
        self.assertNotIn(request["user_question"], writing_prompt)
        self.assertIn("bounded_direction", writing_prompt)

    def test_phase4_prompts_do_not_contain_human_test_case_terms(self):
        prompts = "\n".join(
            path.read_text(encoding="utf-8").casefold()
            for path in (Path(__file__).resolve().parents[1] / "prompts").glob("pass2_*.txt")
        )
        for term in ("spain", "spanish", "coffee chat", "luma", "infj", "queen of cups"):
            self.assertNotIn(term, prompts)


if __name__ == "__main__":
    unittest.main()
