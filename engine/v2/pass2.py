"""Phase 4 question reveal and Pass 2 integration workflow."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from .contracts import (
    ContractError,
    QUESTION_SHIFTS,
    SCHEMA_VERSION,
    validate_pass2_output,
)
from .pipeline import Pass1Pipeline, canonical_json
from .traditional import TraditionalTarotLayer


PROMPT_DIR = Path(__file__).resolve().parent / "prompts"
PROMPT_PATHS = {
    "integration": PROMPT_DIR / "pass2_integration.txt",
    "writing": PROMPT_DIR / "pass2_writing.txt",
}
PASS2_REQUEST_KEYS = {
    "schema_version",
    "session_id",
    "frozen_pass1",
    "user_question",
    "question_shift",
    "question_shift_note",
    "situated_traditional_request",
}
INTEGRATION_STAGE_KEYS = {
    "schema_version",
    "session_id",
    "card_id",
    "orientation",
    "pass1_sha256",
    "question_shift",
    "central_axis",
    "question_structure",
    "pattern_inheritance",
    "causal_process_synthesis",
    "reality_evidence",
    "perspective_shift",
    "alternative_hypotheses",
    "bounded_direction",
    "practical_translation",
    "epistemic_limits",
    "takeaway",
}
WRITING_STAGE_KEYS = {
    "schema_version",
    "session_id",
    "card_id",
    "pass1_sha256",
    "complete_reading",
    "takeaway_question",
}


class Pass2Pipeline:
    """Integrate a revealed question without rewriting the frozen Pass 1."""

    def __init__(self, traditional_layer: TraditionalTarotLayer | None = None) -> None:
        self.traditional_layer = traditional_layer or TraditionalTarotLayer()

    def prepare_request(
        self,
        *,
        frozen_pass1: Mapping[str, Any],
        user_question: str,
        question_shift: str,
        question_shift_note: str | None = None,
    ) -> dict[str, Any]:
        Pass1Pipeline.verify_frozen(frozen_pass1)
        if not isinstance(user_question, str) or not user_question.strip():
            raise ContractError("Pass 2 requires a non-empty revealed question")
        if question_shift not in QUESTION_SHIFTS:
            raise ContractError(
                f"question_shift must be one of {sorted(QUESTION_SHIFTS)}"
            )
        if question_shift_note is not None:
            if not isinstance(question_shift_note, str) or not question_shift_note.strip():
                raise ContractError("question_shift_note must be null or a non-empty string")
            question_shift_note = question_shift_note.strip()

        frozen_copy = json.loads(canonical_json(frozen_pass1))
        pass1 = frozen_copy["payload"]
        request = {
            "schema_version": SCHEMA_VERSION,
            "session_id": pass1["session_id"],
            "frozen_pass1": frozen_copy,
            "user_question": user_question.strip(),
            "question_shift": question_shift,
            "question_shift_note": question_shift_note,
            "situated_traditional_request": self.traditional_layer.prepare_situated_request(
                pass1["card_id"], pass1["orientation"], user_question.strip()
            ),
        }
        self.validate_request(request)
        return request

    @staticmethod
    def validate_request(request: Mapping[str, Any]) -> None:
        if set(request) != PASS2_REQUEST_KEYS:
            raise ContractError(
                f"Pass 2 input keys must be exactly {sorted(PASS2_REQUEST_KEYS)}; "
                f"got {sorted(request)}"
            )
        if request.get("schema_version") != SCHEMA_VERSION:
            raise ContractError("unsupported Pass 2 request schema_version")
        frozen = request.get("frozen_pass1")
        if not isinstance(frozen, Mapping):
            raise ContractError("Pass 2 requires a frozen Pass 1 object")
        Pass1Pipeline.verify_frozen(frozen)
        pass1 = frozen["payload"]
        if request.get("session_id") != pass1["session_id"]:
            raise ContractError("Pass 2 request session_id mismatch")
        question = request.get("user_question")
        if not isinstance(question, str) or not question.strip():
            raise ContractError("Pass 2 request user_question must be non-empty")
        if request.get("question_shift") not in QUESTION_SHIFTS:
            raise ContractError("invalid question_shift")
        note = request.get("question_shift_note")
        if note is not None and (not isinstance(note, str) or not note.strip()):
            raise ContractError("question_shift_note must be null or non-empty")
        situated_request = request.get("situated_traditional_request")
        if not isinstance(situated_request, dict):
            raise ContractError("situated_traditional_request must be an object")
        TraditionalTarotLayer.validate_situated_request(situated_request)
        canonical = situated_request["canonical_reading"]
        if canonical != pass1["canonical_traditional_reading"]:
            raise ContractError("situated request must reuse the frozen canonical reading")
        if situated_request["user_question"] != question:
            raise ContractError("situated request question mismatch")

    @staticmethod
    def _render_template(stage: str, variable: str, payload: Mapping[str, Any]) -> str:
        template = PROMPT_PATHS[stage].read_text(encoding="utf-8")
        input_json = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True)
        return template.replace(variable, input_json)

    def render_situated_prompt(self, request: Mapping[str, Any]) -> str:
        self.validate_request(request)
        return self.traditional_layer.render_situated_prompt(
            request["situated_traditional_request"]
        )

    def validate_situated_output(
        self, request: Mapping[str, Any], situated_output: Mapping[str, Any]
    ) -> None:
        self.validate_request(request)
        self.traditional_layer.validate_situated_output(
            dict(situated_output), request["situated_traditional_request"]
        )

    def render_integration_prompt(
        self, request: Mapping[str, Any], situated_output: Mapping[str, Any]
    ) -> str:
        self.validate_situated_output(request, situated_output)
        frozen = request["frozen_pass1"]
        integration_input = {
            "schema_version": request["schema_version"],
            "session_id": request["session_id"],
            "pass1_sha256": frozen["pass1_sha256"],
            "frozen_pass1": frozen["payload"],
            "user_question": request["user_question"],
            "question_shift": request["question_shift"],
            "question_shift_note": request["question_shift_note"],
            "situated_traditional_reading": situated_output,
        }
        return self._render_template(
            "integration", "{{PASS2_INTEGRATION_INPUT}}", integration_input
        )

    @staticmethod
    def _validate_stage_identity(
        stage: Mapping[str, Any],
        expected_keys: set[str],
        request: Mapping[str, Any],
        name: str,
    ) -> None:
        if set(stage) != expected_keys:
            raise ContractError(
                f"{name} keys must be exactly {sorted(expected_keys)}; got {sorted(stage)}"
            )
        pass1 = request["frozen_pass1"]["payload"]
        if stage.get("schema_version") != SCHEMA_VERSION:
            raise ContractError(f"{name} schema_version mismatch")
        if stage.get("session_id") != request["session_id"]:
            raise ContractError(f"{name} session_id mismatch")
        if stage.get("card_id") != pass1["card_id"]:
            raise ContractError(f"{name} card_id mismatch")
        if stage.get("pass1_sha256") != request["frozen_pass1"]["pass1_sha256"]:
            raise ContractError(f"{name} Pass 1 digest mismatch")

    def render_writing_prompt(
        self,
        request: Mapping[str, Any],
        situated_output: Mapping[str, Any],
        integration_stage: Mapping[str, Any],
    ) -> str:
        self.validate_situated_output(request, situated_output)
        self._validate_stage_identity(
            integration_stage, INTEGRATION_STAGE_KEYS, request, "integration stage"
        )
        question_structure = integration_stage["question_structure"]
        unknown_questions = {
            item["id"]: item["question"]
            for item in question_structure["decisive_unknowns"]
        }
        narrative_brief = {
            "central_axis": integration_stage["central_axis"],
            "question_structure": {
                "core_experience": question_structure["core_experience"]["summary"],
                "lived_stakes": [item["summary"] for item in question_structure["lived_stakes"]],
                "current_explanatory_frame": (
                    question_structure["current_explanatory_frame"]["summary"]
                    if question_structure["current_explanatory_frame"] is not None
                    else None
                ),
                "contemplated_decision": (
                    question_structure["contemplated_decision"]["summary"]
                    if question_structure["contemplated_decision"] is not None
                    else None
                ),
                "decisive_unknowns": [
                    {
                        "question": item["question"],
                        "why_decisive": item["why_decisive"],
                    }
                    for item in question_structure["decisive_unknowns"]
                ],
            },
            "causal_process_synthesis": {
                key: integration_stage["causal_process_synthesis"][key]
                for key in (
                    "narrative_spine",
                    "pass1_origin_bridge",
                    "adaptive_value_in_context",
                    "current_cost_in_context",
                )
            },
            "perspective_shift": integration_stage["perspective_shift"],
            "alternative_hypotheses": [
                {
                    "decisive_unknown": unknown_questions[item["decisive_unknown_id"]],
                    "possibility": item["possibility"],
                    "missing_evidence": item["missing_evidence"],
                }
                for item in integration_stage["alternative_hypotheses"]
            ],
            "bounded_direction": {
                key: integration_stage["bounded_direction"][key]
                for key in ("answer", "uncertainty_boundary")
            },
            "practical_translation": {
                key: integration_stage["practical_translation"][key]
                for key in ("mode", "information_goal", "step_or_practice", "rationale")
            },
            "takeaway": {"question": integration_stage["takeaway"]["question"]},
            "epistemic_limits": integration_stage["epistemic_limits"],
        }
        writing_input = {
            "schema_version": request["schema_version"],
            "session_id": request["session_id"],
            "card_id": request["frozen_pass1"]["payload"]["card_id"],
            "pass1_sha256": request["frozen_pass1"]["pass1_sha256"],
            "narrative_brief": narrative_brief,
        }
        return self._render_template("writing", "{{PASS2_WRITING_INPUT}}", writing_input)

    def assemble(
        self,
        request: Mapping[str, Any],
        situated_output: Mapping[str, Any],
        integration_stage: Mapping[str, Any],
        writing_stage: Mapping[str, Any],
    ) -> dict[str, Any]:
        self.validate_situated_output(request, situated_output)
        self._validate_stage_identity(
            integration_stage, INTEGRATION_STAGE_KEYS, request, "integration stage"
        )
        self._validate_stage_identity(
            writing_stage, WRITING_STAGE_KEYS, request, "writing stage"
        )
        if writing_stage["takeaway_question"] != integration_stage["takeaway"]["question"]:
            raise ContractError("writing stage must preserve the integrated takeaway question")

        pass1 = request["frozen_pass1"]["payload"]
        output = {
            "schema_version": SCHEMA_VERSION,
            "session_id": request["session_id"],
            "card_id": pass1["card_id"],
            "orientation": pass1["orientation"],
            "pass1_sha256": request["frozen_pass1"]["pass1_sha256"],
            "user_question": request["user_question"],
            "question_shift": request["question_shift"],
            "question_shift_note": request["question_shift_note"],
            "central_axis": integration_stage["central_axis"],
            "question_structure": integration_stage["question_structure"],
            "pattern_inheritance": integration_stage["pattern_inheritance"],
            "causal_process_synthesis": integration_stage["causal_process_synthesis"],
            "reality_evidence": integration_stage["reality_evidence"],
            "situated_traditional_reading": dict(situated_output),
            "perspective_shift": integration_stage["perspective_shift"],
            "alternative_hypotheses": integration_stage["alternative_hypotheses"],
            "bounded_direction": integration_stage["bounded_direction"],
            "practical_translation": integration_stage["practical_translation"],
            "takeaway": integration_stage["takeaway"],
            "epistemic_limits": integration_stage["epistemic_limits"],
            "user_display": {
                "complete_reading": writing_stage["complete_reading"],
                "takeaway_question": writing_stage["takeaway_question"],
            },
        }
        validate_pass2_output(
            output,
            pass1_payload=pass1,
            pass1_sha256=request["frozen_pass1"]["pass1_sha256"],
            user_question=request["user_question"],
            question_shift=request["question_shift"],
            question_shift_note=request["question_shift_note"],
            situated_reading=situated_output,
        )
        return output
