"""Run the frozen two-pass prompt workflow through a JSON model provider."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any, Mapping

from .contracts import ContractError, SCHEMA_VERSION
from .pass2 import Pass2Pipeline
from .pipeline import Pass1Pipeline
from .providers import JsonModelClient, JsonModelResponse
from .wire_contracts import (
    WIRE_CONTRACT_VERSION,
    render_wire_prompt,
    validate_wire_payload,
)


RUN_VERSION = "1"
CONTRACT_ATTEMPTS = 2


class ModelWorkflow:
    def __init__(
        self,
        client: JsonModelClient,
        *,
        pass1_pipeline: Pass1Pipeline | None = None,
        pass2_pipeline: Pass2Pipeline | None = None,
        on_stage: Callable[[str], None] | None = None,
    ) -> None:
        self.client = client
        self.pass1_pipeline = pass1_pipeline or Pass1Pipeline()
        self.pass2_pipeline = pass2_pipeline or Pass2Pipeline()
        self.on_stage = on_stage

    def _complete(
        self,
        prompt: str,
        stage: str,
        validator: Callable[[Mapping[str, Any]], None] | None = None,
    ) -> JsonModelResponse:
        if self.on_stage is not None:
            self.on_stage(stage)
        base_prompt = render_wire_prompt(prompt, stage)
        attempt_prompt = base_prompt
        discarded_receipts: list[dict[str, Any]] = []
        last_error: ContractError | None = None
        for contract_attempt in range(1, CONTRACT_ATTEMPTS + 1):
            response = self.client.complete_json(attempt_prompt, stage=stage)
            try:
                validate_wire_payload(response.payload, stage)
                if validator is not None:
                    validator(response.payload)
            except ContractError as exc:
                last_error = exc
                discarded_receipts.append(response.receipt)
                if contract_attempt == CONTRACT_ATTEMPTS:
                    raise ContractError(
                        f"{stage} failed runtime contract after {CONTRACT_ATTEMPTS} attempts: {exc}"
                    ) from exc
                attempt_prompt = (
                    f"{base_prompt}\n\nRUNTIME_CONTRACT_REPAIR:\n"
                    "Your previous JSON object was rejected by the local validator. "
                    "Regenerate the complete object from the original inputs; do not return "
                    "a patch or commentary. Correct this validation error exactly:\n"
                    f"{exc}"
                )
                continue

            receipt = dict(response.receipt)
            receipt["contract_attempts"] = contract_attempt
            if discarded_receipts:
                receipt["discarded_contract_attempts"] = [
                    {
                        "response_id": item.get("response_id"),
                        "served_model": item.get("served_model"),
                        "usage": item.get("usage", {}),
                    }
                    for item in discarded_receipts
                ]
            return JsonModelResponse(payload=response.payload, receipt=receipt)
        raise ContractError(f"{stage} failed runtime contract: {last_error}")

    def _validate_pass1_partial(
        self,
        request: Mapping[str, Any],
        evidence: Mapping[str, Any],
        patterns: Mapping[str, Any] | None = None,
        compensation: Mapping[str, Any] | None = None,
        writing: Mapping[str, Any] | None = None,
    ) -> None:
        card_id = request["card_stimulus"]["id"]
        if patterns is None:
            patterns = {
                "schema_version": SCHEMA_VERSION,
                "session_id": request["session_id"],
                "card_id": card_id,
                "psychological_patterns": [],
                "central_pattern_id": None,
                "jungian_hypotheses": [],
                "epistemic_limits": {
                    "weak_signal": True,
                    "weak_signal_reason": "Runtime validation placeholder.",
                    "unsupported_inferences": [
                        "stable_trait", "developmental_origin", "clinical_diagnosis"
                    ],
                    "limitations": [],
                },
            }
        if compensation is None:
            central_id = patterns.get("central_pattern_id")
            compensation = {
                "schema_version": SCHEMA_VERSION,
                "session_id": request["session_id"],
                "card_id": card_id,
                "compensatory_reading": {
                    "tension": "Runtime validation placeholder.",
                    "card_contribution": "Runtime validation placeholder.",
                    "temporary_third_meaning": "Runtime validation placeholder.",
                    "evidence_pattern_ids": [central_id]
                    if isinstance(central_id, str) and central_id
                    else [],
                },
            }
        if writing is None:
            writing = {
                "schema_version": SCHEMA_VERSION,
                "session_id": request["session_id"],
                "card_id": card_id,
                "integrated_reading": "Runtime validation placeholder.",
            }
        self.pass1_pipeline.assemble(
            request, evidence, patterns, compensation, writing
        )

    def _validate_pass2_integration(
        self,
        request: Mapping[str, Any],
        situated: Mapping[str, Any],
        integration: Mapping[str, Any],
    ) -> None:
        pass1 = request["frozen_pass1"]["payload"]
        synthesis = integration.get("causal_process_synthesis")
        narrative_spine = (
            synthesis.get("narrative_spine") if isinstance(synthesis, Mapping) else None
        )
        origin_bridge = (
            synthesis.get("pass1_origin_bridge")
            if isinstance(synthesis, Mapping)
            else None
        )
        if isinstance(narrative_spine, str):
            validation_parts = [origin_bridge, narrative_spine]
            validation_reading = " ".join(
                part for part in validation_parts if isinstance(part, str) and part
            )
            validation_reading = (
                validation_reading.replace("用户", "你")
                .replace("The user", "You")
                .replace("the user", "you")
            )
        else:
            validation_reading = narrative_spine
        writing = {
            "schema_version": SCHEMA_VERSION,
            "session_id": request["session_id"],
            "card_id": pass1["card_id"],
            "pass1_sha256": request["frozen_pass1"]["pass1_sha256"],
            "complete_reading": validation_reading,
            "takeaway_question": (
                integration.get("takeaway", {}).get("question")
                if isinstance(integration.get("takeaway"), Mapping)
                else None
            ),
        }
        self.pass2_pipeline.assemble(request, situated, integration, writing)

    def run_pass1(self, request: Mapping[str, Any]) -> dict[str, Any]:
        self.pass1_pipeline.validate_request(request)
        receipts: list[dict[str, Any]] = []

        evidence_response = self._complete(
            self.pass1_pipeline.render_observation_prompt(request),
            "pass1_observations",
            lambda payload: self._validate_pass1_partial(request, payload),
        )
        evidence = evidence_response.payload
        receipts.append(evidence_response.receipt)

        pattern_response = self._complete(
            self.pass1_pipeline.render_pattern_prompt(request, evidence),
            "pass1_patterns",
            lambda payload: self._validate_pass1_partial(
                request, evidence, patterns=payload
            ),
        )
        patterns = pattern_response.payload
        receipts.append(pattern_response.receipt)

        compensation_response = self._complete(
            self.pass1_pipeline.render_compensation_prompt(request, evidence, patterns),
            "pass1_compensation",
            lambda payload: self._validate_pass1_partial(
                request, evidence, patterns=patterns, compensation=payload
            ),
        )
        compensation = compensation_response.payload
        receipts.append(compensation_response.receipt)

        writing_response = self._complete(
            self.pass1_pipeline.render_writing_prompt(
                request, evidence, patterns, compensation
            ),
            "pass1_writing",
            lambda payload: self._validate_pass1_partial(
                request,
                evidence,
                patterns=patterns,
                compensation=compensation,
                writing=payload,
            ),
        )
        writing = writing_response.payload
        receipts.append(writing_response.receipt)

        output = self.pass1_pipeline.assemble(
            request, evidence, patterns, compensation, writing
        )
        frozen = self.pass1_pipeline.freeze(output, request).to_dict()
        return {
            "run_version": RUN_VERSION,
            "wire_contract_version": WIRE_CONTRACT_VERSION,
            "request": dict(request),
            "stages": {
                "observations": evidence,
                "patterns": patterns,
                "compensation": compensation,
                "writing": writing,
            },
            "output": output,
            "frozen_pass1": frozen,
            "provider_receipts": receipts,
        }

    def run_pass2(self, request: Mapping[str, Any]) -> dict[str, Any]:
        self.pass2_pipeline.validate_request(request)
        receipts: list[dict[str, Any]] = []

        situated_response = self._complete(
            self.pass2_pipeline.render_situated_prompt(request),
            "traditional_situated",
            lambda payload: self.pass2_pipeline.validate_situated_output(
                request, payload
            ),
        )
        situated = situated_response.payload
        receipts.append(situated_response.receipt)

        integration_response = self._complete(
            self.pass2_pipeline.render_integration_prompt(request, situated),
            "pass2_integration",
            lambda payload: self._validate_pass2_integration(
                request, situated, payload
            ),
        )
        integration = integration_response.payload
        receipts.append(integration_response.receipt)

        writing_response = self._complete(
            self.pass2_pipeline.render_writing_prompt(request, situated, integration),
            "pass2_writing",
            lambda payload: self.pass2_pipeline.assemble(
                request, situated, integration, payload
            ),
        )
        writing = writing_response.payload
        receipts.append(writing_response.receipt)

        output = self.pass2_pipeline.assemble(
            request, situated, integration, writing
        )
        return {
            "run_version": RUN_VERSION,
            "wire_contract_version": WIRE_CONTRACT_VERSION,
            "request": dict(request),
            "stages": {
                "situated": situated,
                "integration": integration,
                "writing": writing,
            },
            "output": output,
            "provider_receipts": receipts,
        }
