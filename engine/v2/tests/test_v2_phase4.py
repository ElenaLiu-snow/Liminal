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
        pass1_output["psychological_patterns"][0]["sequence"].append(
            "anticipate the next movement"
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
                    "match_basis": "process_recurrence",
                    "rationale": "The revealed concern repeats the frozen sequence of checking before movement.",
                    "process_step_mappings": [
                        {
                            "pass1_step": "register the overall structure",
                            "question_manifestation": "The application is recognized as movement already underway.",
                            "reality_evidence_ids": ["reality-1"],
                        },
                        {
                            "pass1_step": "reassign the structure's function",
                            "question_manifestation": "Possible hesitation is recoded as inevitable withdrawal.",
                            "reality_evidence_ids": ["reality-1"],
                        },
                        {
                            "pass1_step": "anticipate the next movement",
                            "question_manifestation": "The feared interview withdrawal is projected forward.",
                            "reality_evidence_ids": ["reality-1"],
                        },
                    ],
                    "adaptive_value_in_context": "Anticipating hesitation makes preparation possible.",
                    "current_cost_in_context": "The anticipation may turn uncertainty into a foregone withdrawal.",
                }
            ],
            "process_recap": "The revealed question repeats a move from registering action to recoding uncertainty as likely withdrawal.",
            "reality_evidence": [
                {
                    "id": "reality-1",
                    "source": "user_question",
                    "quote": "submitted an application",
                    "role": "action_already_taken",
                    "interpretation": "The feared repetition is not the only available trajectory.",
                }
            ],
            "compensation_bridge": {
                "inherited_process_limit": "Anticipated hesitation is collapsed into a prediction of withdrawal.",
                "card_counterweight": "The card frames coordinated movement as compatible with unresolved tension.",
                "revised_decision_criterion": "Judge movement by the next completed commitment, not by the absence of hesitation.",
            },
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

    def test_theme_overlap_alone_cannot_be_marked_integrated(self):
        request, situated, integration, writing = self.make_fixture()
        item = integration["pattern_inheritance"][0]
        item["match_basis"] = "theme_overlap_only"
        with self.assertRaises(ContractError):
            self.pipeline.assemble(request, situated, integration, writing)

    def test_integrated_pattern_requires_every_frozen_process_step(self):
        request, situated, integration, writing = self.make_fixture()
        integration["pattern_inheritance"][0]["process_step_mappings"].pop()
        with self.assertRaises(ContractError):
            self.pipeline.assemble(request, situated, integration, writing)

    def test_held_theme_match_cannot_drive_direction_or_contextual_cost(self):
        request, situated, integration, writing = self.make_fixture()
        item = integration["pattern_inheritance"][0]
        item.update({
            "status": "held",
            "match_basis": "theme_overlap_only",
            "process_step_mappings": [],
            "adaptive_value_in_context": None,
            "current_cost_in_context": None,
        })
        integration["bounded_direction"]["evidence_pattern_ids"] = []
        integration["practical_translation"]["evidence_pattern_ids"] = []
        output = self.pipeline.assemble(request, situated, integration, writing)
        self.assertEqual(output["pattern_inheritance"][0]["status"], "held")

    def test_process_mapping_must_copy_an_exact_frozen_sequence_step(self):
        request, situated, integration, writing = self.make_fixture()
        integration["pattern_inheritance"][0]["process_step_mappings"][0][
            "pass1_step"
        ] = "a thematic paraphrase rather than the frozen step"
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

    def test_writing_cannot_copy_a_pass1_paragraph(self):
        request, situated, integration, writing = self.make_fixture()
        writing["complete_reading"] = request["frozen_pass1"]["payload"][
            "user_display"
        ]["integrated_reading"]
        with self.assertRaises(ContractError):
            self.pipeline.assemble(request, situated, integration, writing)

    def test_user_facing_writing_must_match_the_question_script(self):
        request, situated, integration, writing = self.make_fixture()
        writing["complete_reading"] = "这段成文与英文问题使用了不同的主要文字系统。"
        with self.assertRaises(ContractError):
            self.pipeline.assemble(request, situated, integration, writing)

    def test_user_facing_writing_cannot_expose_backend_user_label(self):
        request, situated, integration, writing = self.make_fixture()
        writing["complete_reading"] = "The user repeats the frozen process in the question."
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
        self.assertNotIn(
            request["frozen_pass1"]["payload"]["user_display"]["integrated_reading"],
            writing_prompt,
        )
        self.assertIn("bounded_direction", writing_prompt)
        self.assertNotIn("pass1_user_reading", writing_prompt)

    def test_phase4_prompts_do_not_contain_human_test_case_terms(self):
        prompts = "\n".join(
            path.read_text(encoding="utf-8").casefold()
            for path in (Path(__file__).resolve().parents[1] / "prompts").glob("pass2_*.txt")
        )
        for term in ("spain", "spanish", "coffee chat", "luma", "infj", "queen of cups"):
            self.assertNotIn(term, prompts)


if __name__ == "__main__":
    unittest.main()
