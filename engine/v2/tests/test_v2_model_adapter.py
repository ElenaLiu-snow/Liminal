import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from engine.v2.contracts import ContractError, SCHEMA_VERSION
from engine.v2.model_workflow import ModelWorkflow
from engine.v2.pass2 import Pass2Pipeline
from engine.v2.pipeline import Pass1Pipeline
from engine.v2.providers import (
    DeepSeekClient,
    DeepSeekConfig,
    JsonModelResponse,
    ProviderError,
)
from engine.v2.tests.test_v2_phase3 import make_pass1_output, split_pass1_output
from engine.v2.wire_contracts import (
    STAGE_CONTRACTS,
    WIRE_CONTRACT_VERSION,
    validate_wire_payload,
)


class StubDeepSeekClient(DeepSeekClient):
    def __init__(self, config, responses):
        super().__init__(config)
        self.responses = list(responses)
        self.requests = []

    def _post_json(self, payload):
        self.requests.append(dict(payload))
        return self.responses.pop(0)


class SequenceClient:
    def __init__(self, payloads):
        self.payloads = list(payloads)
        self.stages = []
        self.prompts = []

    def complete_json(self, prompt, *, stage):
        self.assert_safe_prompt(prompt)
        self.stages.append(stage)
        self.prompts.append(prompt)
        return JsonModelResponse(
            payload=self.payloads.pop(0),
            receipt={"provider": "fake", "stage": stage},
        )

    @staticmethod
    def assert_safe_prompt(prompt):
        if not isinstance(prompt, str) or not prompt:
            raise AssertionError("workflow emitted an empty prompt")


class DeepSeekConfigurationTests(unittest.TestCase):
    def test_local_env_loads_without_exposing_key_in_repr(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / ".env.local"
            path.write_text(
                "DEEPSEEK_API_KEY=secret-value\n"
                "DEEPSEEK_BASE_URL=https://api.deepseek.com\n"
                "DEEPSEEK_MODEL=deepseek-v4-pro\n",
                encoding="utf-8",
            )
            path.chmod(0o600)
            with patch.dict(os.environ, {}, clear=True):
                config = DeepSeekConfig.from_env(path)
        self.assertEqual(config.model, "deepseek-v4-pro")
        self.assertNotIn("secret-value", repr(config))
        self.assertEqual(config.thinking, "disabled")
        self.assertEqual(config.reasoning_effort, "high")

    def test_non_https_base_url_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / ".env.local"
            path.write_text(
                "DEEPSEEK_API_KEY=secret-value\nDEEPSEEK_BASE_URL=http://example.test\n",
                encoding="utf-8",
            )
            path.chmod(0o600)
            with patch.dict(os.environ, {}, clear=True):
                with self.assertRaises(ProviderError):
                    DeepSeekConfig.from_env(path)

    def test_json_request_uses_official_mode_without_temperature(self):
        config = DeepSeekConfig(api_key="secret-value", max_attempts=1)
        client = StubDeepSeekClient(
            config,
            [{
                "id": "response-1",
                "model": "DeepSeek-V4-Pro-0813",
                "created": 1,
                "choices": [{
                    "finish_reason": "stop",
                    "message": {"content": '{"status":"ok"}'},
                }],
                "usage": {"prompt_tokens": 10, "completion_tokens": 4, "detail": {}},
            }],
        )
        response = client.complete_json("Return JSON.", stage="test")
        request = client.requests[0]
        self.assertEqual(request["response_format"], {"type": "json_object"})
        self.assertEqual(request["thinking"], {"type": "disabled"})
        self.assertNotIn("reasoning_effort", request)
        self.assertNotIn("temperature", request)
        self.assertEqual(response.payload, {"status": "ok"})
        self.assertEqual(response.receipt["requested_model"], "deepseek-v4-pro")
        self.assertEqual(response.receipt["served_model"], "DeepSeek-V4-Pro-0813")
        self.assertNotIn("secret-value", repr(response.receipt))


class ModelWorkflowTests(unittest.TestCase):
    def setUp(self):
        self.pass1_pipeline = Pass1Pipeline()
        self.pass2_pipeline = Pass2Pipeline()

    def test_pass1_calls_four_locked_stages_and_freezes_output(self):
        request = self.pass1_pipeline.prepare_request(
            session_id="model-pass1",
            card_ref="The Moon",
            orientation="upright",
            raw_transcript="The path is visible, but the distance still feels uncertain.",
        )
        output = make_pass1_output(request, transformation_type="temporal_shift")
        client = SequenceClient(split_pass1_output(output))
        run = ModelWorkflow(client).run_pass1(request)
        self.assertEqual(
            client.stages,
            [
                "pass1_observations",
                "pass1_patterns",
                "pass1_compensation",
                "pass1_writing",
            ],
        )
        self.assertEqual(run["output"], output)
        self.assertEqual(run["wire_contract_version"], WIRE_CONTRACT_VERSION)
        self.assertTrue(all("RUNTIME_JSON_CONTRACT" in prompt for prompt in client.prompts))
        self.assertTrue(all("language_rule" in prompt for prompt in client.prompts))
        self.assertIn("reference_integrity", client.prompts[2])
        self.assertIn("cardinality_rules", client.prompts[0])
        self.pass1_pipeline.verify_frozen(run["frozen_pass1"])

    def test_pass2_calls_three_locked_stages_and_preserves_lineage(self):
        pass1_request = self.pass1_pipeline.prepare_request(
            session_id="model-pass2",
            card_ref="The Chariot",
            orientation="upright",
            raw_transcript="The figure checks both directions before moving.",
        )
        pass1_output = make_pass1_output(
            pass1_request,
            transformation_type="agency_shift",
            user_evidence="The figure checks both directions before moving.",
        )
        frozen = self.pass1_pipeline.freeze(pass1_output, pass1_request).to_dict()
        request = self.pass2_pipeline.prepare_request(
            frozen_pass1=frozen,
            user_question="I applied, but I worry I will withdraw before the interview.",
            question_shift="clarified",
            question_shift_note="The focus narrowed to following through.",
        )
        canonical = request["situated_traditional_request"]["canonical_reading"]
        situated = {
            "card_id": canonical["card_id"],
            "orientation": canonical["orientation"],
            "question_relevant_card_structure": "The card frames movement as coordination rather than certainty.",
            "orientation_mechanism": "Upright movement remains active while opposing forces require coordination.",
            "tension_axes": [
                "Preparation may coordinate movement.",
                "Preparation may delay movement.",
            ],
            "scope_boundary": "The card cannot establish whether withdrawal will occur.",
            "source_refs": canonical["source_refs"],
        }
        integration = {
            "schema_version": SCHEMA_VERSION,
            "session_id": request["session_id"],
            "card_id": frozen["payload"]["card_id"],
            "orientation": frozen["payload"]["orientation"],
            "pass1_sha256": frozen["pass1_sha256"],
            "question_shift": "clarified",
            "central_axis": "Preparation protects movement but may postpone it.",
            "question_structure": {
                "core_experience": {
                    "summary": "An application is underway while withdrawal is feared.",
                    "reality_evidence_ids": ["reality-1", "reality-2"],
                },
                "lived_stakes": [{
                    "summary": "Following through already carries worry.",
                    "reality_evidence_ids": ["reality-3"],
                }],
                "current_explanatory_frame": None,
                "contemplated_decision": None,
                "decisive_unknowns": [{
                    "id": "unknown-1",
                    "question": "Whether hesitation will prevent attendance.",
                    "why_decisive": "It separates present worry from future behavior.",
                    "reality_evidence_ids": ["reality-2", "reality-3"],
                }],
            },
            "pattern_inheritance": [{
                "pattern_id": "pattern-1",
                "status": "integrated",
                "match_basis": "process_recurrence",
                "rationale": "The concern repeats checking before movement.",
                "process_step_mappings": [
                    {
                        "pass1_step": "register the overall structure",
                        "question_manifestation": "The application is recognized as action underway.",
                        "reality_evidence_ids": ["reality-1"],
                    },
                    {
                        "pass1_step": "reassign the structure's function",
                        "question_manifestation": "Uncertainty is recoded as likely withdrawal.",
                        "reality_evidence_ids": ["reality-2"],
                    },
                ],
            }],
            "causal_process_synthesis": {
                "narrative_spine": "Because following through matters, present worry is used to anticipate withdrawal even though action has begun.",
                "pass1_origin_bridge": "This movement from checking the situation to anticipating what comes next was already visible in how you interpreted the card.",
                "adaptive_value_in_context": "Anticipation can support preparation.",
                "current_cost_in_context": "It can make withdrawal feel predetermined.",
                "evidence_pattern_ids": ["pattern-1"],
                "reality_evidence_ids": ["reality-1", "reality-2", "reality-3"],
            },
            "reality_evidence": [
                {
                    "id": "reality-1",
                    "source": "user_question",
                    "quote": "I applied",
                    "role": "action_already_taken",
                    "interpretation": "Action has already begun.",
                },
                {
                    "id": "reality-2",
                    "source": "user_question",
                    "quote": "withdraw before the interview",
                    "role": "reported_experience",
                    "interpretation": "Withdrawal is feared rather than completed.",
                },
                {
                    "id": "reality-3",
                    "source": "user_question",
                    "quote": "I worry",
                    "role": "lived_stake",
                    "interpretation": "The possibility carries emotional weight.",
                },
            ],
            "perspective_shift": {
                "current_frame": "Present hesitation is being used to forecast stopped movement.",
                "card_specific_counterweight": "The Chariot frames movement as coordination of tension.",
                "relocated_attention": "Attention moves from certainty to coordinated follow-through.",
                "revised_decision_criterion": "Evaluate the next completed movement rather than emotional certainty.",
            },
            "alternative_hypotheses": [
                {
                    "id": "alternative-1",
                    "decisive_unknown_id": "unknown-1",
                    "possibility": "Worry may coexist with attendance.",
                    "supporting_reality_evidence_ids": ["reality-1"],
                    "missing_evidence": "Whether comparable worry previously stopped action.",
                },
                {
                    "id": "alternative-2",
                    "decisive_unknown_id": "unknown-1",
                    "possibility": "Worry may signal a material risk of withdrawal.",
                    "supporting_reality_evidence_ids": [],
                    "missing_evidence": "Which conditions precede actual withdrawal.",
                },
            ],
            "bounded_direction": {
                "answer": "Following through is plausible through a bounded next step.",
                "uncertainty_boundary": "The reading cannot predict the outcome.",
                "evidence_pattern_ids": ["pattern-1"],
                "reality_evidence_ids": ["reality-1"],
            },
            "practical_translation": {
                "mode": "action",
                "information_goal": "Learn whether hesitation prevents attendance.",
                "step_or_practice": "Prepare one question and attend.",
                "rationale": "A bounded action creates evidence about the feared outcome.",
                "decisive_unknown_id": "unknown-1",
            },
            "takeaway": {
                "decisive_unknown_id": "unknown-1",
                "alternative_hypothesis_ids": ["alternative-1", "alternative-2"],
                "question": "What is the smallest completed movement?",
            },
            "epistemic_limits": {
                "unsupported_inferences": [
                    "stable_trait", "developmental_origin", "clinical_diagnosis"
                ],
                "limitations": ["One reading cannot establish future behavior."],
            },
        }
        writing = {
            "schema_version": SCHEMA_VERSION,
            "session_id": request["session_id"],
            "card_id": frozen["payload"]["card_id"],
            "pass1_sha256": frozen["pass1_sha256"],
            "complete_reading": "This movement from checking the situation to anticipating what comes next was already visible in how you interpreted the card. The frozen process meets the question through bounded movement.",
            "takeaway_question": integration["takeaway"]["question"],
        }
        integration["reality_evidence"][2]["quote"] = "I worry!"
        integration["question_structure"]["lived_stakes"] = []
        client = SequenceClient([situated, integration, writing])
        run = ModelWorkflow(client).run_pass2(request)
        self.assertEqual(
            client.stages,
            ["traditional_situated", "pass2_integration", "pass2_writing"],
        )
        self.assertEqual(run["output"]["pass1_sha256"], frozen["pass1_sha256"])
        self.assertEqual(
            run["output"]["reality_evidence"][2]["quote"],
            request["user_question"],
        )
        self.assertEqual(
            run["output"]["question_structure"]["lived_stakes"][0][
                "reality_evidence_ids"
            ],
            ["reality-3"],
        )
        receipt = run["provider_receipts"][1]
        self.assertIn("restored_nonverbatim_reality_quote", receipt["mechanical_repairs"])
        self.assertIn("preserved_identified_lived_stake", receipt["mechanical_repairs"])
        self.assertIn("normalized_output_sha256", receipt)

    def test_wire_contracts_cover_every_live_model_stage(self):
        self.assertEqual(
            set(STAGE_CONTRACTS),
            {
                "pass1_observations", "pass1_patterns", "pass1_compensation",
                "pass1_writing", "traditional_situated", "pass2_integration",
                "pass2_writing",
            },
        )
        serialized = repr(STAGE_CONTRACTS).casefold()
        for case_term in ("spain", "coffee chat", "queen of cups", "wheel of fortune"):
            self.assertNotIn(case_term, serialized)

    def test_invalid_nested_type_stops_before_the_next_model_stage(self):
        request = self.pass1_pipeline.prepare_request(
            session_id="invalid-wire-stage",
            card_ref="The Hermit",
            orientation="upright",
            raw_transcript="The figure carries a light.",
        )
        invalid_evidence = {
            "schema_version": SCHEMA_VERSION,
            "session_id": request["session_id"],
            "card_id": request["card_stimulus"]["id"],
            "symbolic_observations": [{
                "id": "obs-1",
                "kind": "noticed",
                "description": "A light is noticed.",
                "user_evidence": "The figure carries a light.",
                "card_evidence": ["lantern"],
                "confidence": "high",
            }],
            "symbolic_transformations": [],
        }
        with self.assertRaises(ContractError):
            validate_wire_payload(invalid_evidence, "pass1_observations")
        client = SequenceClient([invalid_evidence, invalid_evidence])
        with self.assertRaises(ContractError):
            ModelWorkflow(client).run_pass1(request)
        self.assertEqual(
            client.stages, ["pass1_observations", "pass1_observations"]
        )
        self.assertIn("RUNTIME_CONTRACT_REPAIR", client.prompts[1])

    def test_semantic_contract_failure_repairs_only_the_current_stage(self):
        request = self.pass1_pipeline.prepare_request(
            session_id="semantic-repair",
            card_ref="The Hermit",
            orientation="upright",
            raw_transcript="The figure carries a light.",
        )
        output = make_pass1_output(request, transformation_type="temporal_shift")
        stages = split_pass1_output(output)
        invalid_evidence = dict(stages[0])
        invalid_evidence["symbolic_transformations"] = [
            dict(stages[0]["symbolic_transformations"][0], user_evidence=[])
        ]
        client = SequenceClient([invalid_evidence, *stages])
        run = ModelWorkflow(client).run_pass1(request)
        self.assertEqual(run["output"], output)
        self.assertEqual(
            client.stages[:2], ["pass1_observations", "pass1_observations"]
        )
        self.assertEqual(run["provider_receipts"][0]["contract_attempts"], 2)
        self.assertEqual(
            len(run["provider_receipts"][0]["discarded_contract_attempts"]), 1
        )


if __name__ == "__main__":
    unittest.main()
