"""Phase 3 Pass 1 request, validation, and immutable freeze workflow."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from .contracts import ContractError, SCHEMA_VERSION, validate_pass1_output
from .features import extract_v2_features
from .traditional import TraditionalTarotLayer


PROMPT_DIR = Path(__file__).resolve().parent / "prompts"
PROMPT_PATHS = {
    "observations": PROMPT_DIR / "pass1_observations.txt",
    "patterns": PROMPT_DIR / "pass1_patterns.txt",
    "compensation": PROMPT_DIR / "pass1_compensation.txt",
    "writing": PROMPT_DIR / "pass1_writing.txt",
}
PASS1_INPUT_KEYS = {
    "schema_version",
    "session_id",
    "card_stimulus",
    "orientation",
    "raw_transcript",
    "features",
    "canonical_traditional_reading",
}
EVIDENCE_STAGE_KEYS = {
    "schema_version",
    "session_id",
    "card_id",
    "symbolic_observations",
    "symbolic_transformations",
}
PATTERN_STAGE_KEYS = {
    "schema_version",
    "session_id",
    "card_id",
    "psychological_patterns",
    "central_pattern_id",
    "jungian_hypotheses",
    "epistemic_limits",
}
COMPENSATION_STAGE_KEYS = {
    "schema_version",
    "session_id",
    "card_id",
    "compensatory_reading",
}
WRITING_STAGE_KEYS = {"schema_version", "session_id", "card_id", "integrated_reading"}


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


@dataclass(frozen=True)
class FrozenPass1:
    payload: dict[str, Any]
    sha256: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "freeze_version": "1",
            "pass1_sha256": self.sha256,
            "payload": self.payload,
        }


class Pass1Pipeline:
    """Prepare a question-blind prompt and freeze validated model output."""

    def __init__(self, traditional_layer: TraditionalTarotLayer | None = None) -> None:
        self.traditional_layer = traditional_layer or TraditionalTarotLayer()

    def prepare_request(
        self,
        *,
        session_id: str,
        card_ref: str,
        orientation: str,
        raw_transcript: str,
        speaking_duration_seconds: float | None = None,
    ) -> dict[str, Any]:
        if not isinstance(session_id, str) or not session_id.strip():
            raise ContractError("session_id must be a non-empty string")
        if not isinstance(raw_transcript, str) or not raw_transcript.strip():
            raise ContractError("raw_transcript must be a non-empty string")

        card_stimulus = self.traditional_layer.stimulus(card_ref)
        request = {
            "schema_version": SCHEMA_VERSION,
            "session_id": session_id.strip(),
            "card_stimulus": card_stimulus,
            "orientation": orientation,
            "raw_transcript": raw_transcript,
            "features": extract_v2_features(raw_transcript, speaking_duration_seconds),
            "canonical_traditional_reading": self.traditional_layer.canonical(
                card_stimulus["id"], orientation
            ),
        }
        self.validate_request(request)
        return request

    @staticmethod
    def validate_request(request: Mapping[str, Any]) -> None:
        keys = set(request)
        if keys != PASS1_INPUT_KEYS:
            raise ContractError(
                f"Pass 1 input keys must be exactly {sorted(PASS1_INPUT_KEYS)}; got {sorted(keys)}"
            )
        if "user_question" in request or "question_shift" in request:
            raise ContractError("Pass 1 input must remain question-blind")
        card = request["card_stimulus"]
        canonical = request["canonical_traditional_reading"]
        if canonical["card_id"] != card["id"]:
            raise ContractError("card and canonical traditional reading do not match")
        if canonical["orientation"] != request["orientation"]:
            raise ContractError("orientation and canonical traditional reading do not match")

    @staticmethod
    def _render_template(stage: str, variable: str, payload: Mapping[str, Any]) -> str:
        template = PROMPT_PATHS[stage].read_text(encoding="utf-8")
        input_json = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True)
        return template.replace(variable, input_json)

    @staticmethod
    def _validate_stage_identity(
        stage: Mapping[str, Any], expected_keys: set[str], request: Mapping[str, Any], name: str
    ) -> None:
        if set(stage) != expected_keys:
            raise ContractError(
                f"{name} keys must be exactly {sorted(expected_keys)}; got {sorted(stage)}"
            )
        if stage.get("schema_version") != SCHEMA_VERSION:
            raise ContractError(f"{name} schema_version mismatch")
        if stage.get("session_id") != request["session_id"]:
            raise ContractError(f"{name} session_id mismatch")
        if stage.get("card_id") != request["card_stimulus"]["id"]:
            raise ContractError(f"{name} card_id mismatch")

    def render_observation_prompt(self, request: Mapping[str, Any]) -> str:
        self.validate_request(request)
        evidence_input = {
            "schema_version": request["schema_version"],
            "session_id": request["session_id"],
            "card_stimulus": request["card_stimulus"],
            "orientation": request["orientation"],
            "raw_transcript": request["raw_transcript"],
            "features": request["features"],
        }
        return self._render_template(
            "observations", "{{EVIDENCE_INPUT}}", evidence_input
        )

    def render_pattern_prompt(
        self, request: Mapping[str, Any], evidence_stage: Mapping[str, Any]
    ) -> str:
        self.validate_request(request)
        self._validate_stage_identity(
            evidence_stage, EVIDENCE_STAGE_KEYS, request, "evidence stage"
        )
        pattern_input = {
            "schema_version": request["schema_version"],
            "session_id": request["session_id"],
            "card_id": request["card_stimulus"]["id"],
            "raw_transcript": request["raw_transcript"],
            "features": request["features"],
            "evidence_stage": evidence_stage,
        }
        return self._render_template("patterns", "{{PATTERN_INPUT}}", pattern_input)

    def render_compensation_prompt(
        self,
        request: Mapping[str, Any],
        evidence_stage: Mapping[str, Any],
        pattern_stage: Mapping[str, Any],
    ) -> str:
        self.validate_request(request)
        self._validate_stage_identity(
            evidence_stage, EVIDENCE_STAGE_KEYS, request, "evidence stage"
        )
        self._validate_stage_identity(
            pattern_stage, PATTERN_STAGE_KEYS, request, "pattern stage"
        )
        compensation_input = {
            "schema_version": request["schema_version"],
            "session_id": request["session_id"],
            "card_id": request["card_stimulus"]["id"],
            "symbolic_transformations": evidence_stage["symbolic_transformations"],
            "psychological_patterns": pattern_stage["psychological_patterns"],
            "central_pattern_id": pattern_stage["central_pattern_id"],
            "jungian_hypotheses": pattern_stage["jungian_hypotheses"],
            "canonical_traditional_reading": request["canonical_traditional_reading"],
        }
        return self._render_template(
            "compensation", "{{COMPENSATION_INPUT}}", compensation_input
        )

    def render_writing_prompt(
        self,
        request: Mapping[str, Any],
        evidence_stage: Mapping[str, Any],
        pattern_stage: Mapping[str, Any],
        compensation_stage: Mapping[str, Any],
    ) -> str:
        self.validate_request(request)
        self._validate_stage_identity(
            evidence_stage, EVIDENCE_STAGE_KEYS, request, "evidence stage"
        )
        self._validate_stage_identity(
            pattern_stage, PATTERN_STAGE_KEYS, request, "pattern stage"
        )
        self._validate_stage_identity(
            compensation_stage,
            COMPENSATION_STAGE_KEYS,
            request,
            "compensation stage",
        )
        writing_input = {
            "schema_version": request["schema_version"],
            "session_id": request["session_id"],
            "card_id": request["card_stimulus"]["id"],
            "orientation": request["orientation"],
            "symbolic_observations": evidence_stage["symbolic_observations"],
            "symbolic_transformations": evidence_stage["symbolic_transformations"],
            "psychological_patterns": pattern_stage["psychological_patterns"],
            "central_pattern_id": pattern_stage["central_pattern_id"],
            "jungian_hypotheses": pattern_stage["jungian_hypotheses"],
            "canonical_traditional_reading": request["canonical_traditional_reading"],
            "compensatory_reading": compensation_stage["compensatory_reading"],
            "epistemic_limits": pattern_stage["epistemic_limits"],
        }
        return self._render_template("writing", "{{WRITING_INPUT}}", writing_input)

    def assemble(
        self,
        request: Mapping[str, Any],
        evidence_stage: Mapping[str, Any],
        pattern_stage: Mapping[str, Any],
        compensation_stage: Mapping[str, Any],
        writing_stage: Mapping[str, Any],
    ) -> dict[str, Any]:
        """Assemble staged outputs and run the full cross-reference contract."""

        self.validate_request(request)
        self._validate_stage_identity(
            evidence_stage, EVIDENCE_STAGE_KEYS, request, "evidence stage"
        )
        self._validate_stage_identity(
            pattern_stage, PATTERN_STAGE_KEYS, request, "pattern stage"
        )
        self._validate_stage_identity(
            compensation_stage,
            COMPENSATION_STAGE_KEYS,
            request,
            "compensation stage",
        )
        self._validate_stage_identity(
            writing_stage, WRITING_STAGE_KEYS, request, "writing stage"
        )
        output = {
            "schema_version": SCHEMA_VERSION,
            "session_id": request["session_id"],
            "card_id": request["card_stimulus"]["id"],
            "orientation": request["orientation"],
            "question_blind": True,
            "symbolic_observations": evidence_stage["symbolic_observations"],
            "symbolic_transformations": evidence_stage["symbolic_transformations"],
            "psychological_patterns": pattern_stage["psychological_patterns"],
            "central_pattern_id": pattern_stage["central_pattern_id"],
            "jungian_hypotheses": pattern_stage["jungian_hypotheses"],
            "canonical_traditional_reading": request["canonical_traditional_reading"],
            "compensatory_reading": compensation_stage["compensatory_reading"],
            "epistemic_limits": pattern_stage["epistemic_limits"],
            "user_display": {"integrated_reading": writing_stage["integrated_reading"]},
        }
        validate_pass1_output(output)
        return output

    @staticmethod
    def freeze(output: Mapping[str, Any], request: Mapping[str, Any]) -> FrozenPass1:
        Pass1Pipeline.validate_request(request)
        validate_pass1_output(output)
        if output["session_id"] != request["session_id"]:
            raise ContractError("Pass 1 output session_id does not match its request")
        if output["card_id"] != request["card_stimulus"]["id"]:
            raise ContractError("Pass 1 output card_id does not match its request")
        if output["orientation"] != request["orientation"]:
            raise ContractError("Pass 1 output orientation does not match its request")

        payload = json.loads(canonical_json(output))
        digest = hashlib.sha256(canonical_json(payload).encode("utf-8")).hexdigest()
        return FrozenPass1(payload=payload, sha256=digest)

    @staticmethod
    def verify_frozen(frozen: Mapping[str, Any]) -> None:
        if frozen.get("freeze_version") != "1":
            raise ContractError("unsupported Pass 1 freeze version")
        payload = frozen.get("payload")
        if not isinstance(payload, Mapping):
            raise ContractError("frozen Pass 1 payload must be an object")
        validate_pass1_output(payload)
        expected = hashlib.sha256(canonical_json(payload).encode("utf-8")).hexdigest()
        if frozen.get("pass1_sha256") != expected:
            raise ContractError("frozen Pass 1 digest mismatch; payload was modified")
