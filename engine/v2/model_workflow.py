"""Run the frozen two-pass prompt workflow through a JSON model provider."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any, Mapping

from .pass2 import Pass2Pipeline
from .pipeline import Pass1Pipeline
from .providers import JsonModelClient
from .wire_contracts import (
    WIRE_CONTRACT_VERSION,
    render_wire_prompt,
    validate_wire_payload,
)


RUN_VERSION = "1"


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

    def _complete(self, prompt: str, stage: str):
        if self.on_stage is not None:
            self.on_stage(stage)
        response = self.client.complete_json(render_wire_prompt(prompt, stage), stage=stage)
        validate_wire_payload(response.payload, stage)
        return response

    def run_pass1(self, request: Mapping[str, Any]) -> dict[str, Any]:
        self.pass1_pipeline.validate_request(request)
        receipts: list[dict[str, Any]] = []

        evidence_response = self._complete(
            self.pass1_pipeline.render_observation_prompt(request),
            "pass1_observations",
        )
        evidence = evidence_response.payload
        receipts.append(evidence_response.receipt)

        pattern_response = self._complete(
            self.pass1_pipeline.render_pattern_prompt(request, evidence),
            "pass1_patterns",
        )
        patterns = pattern_response.payload
        receipts.append(pattern_response.receipt)

        compensation_response = self._complete(
            self.pass1_pipeline.render_compensation_prompt(request, evidence, patterns),
            "pass1_compensation",
        )
        compensation = compensation_response.payload
        receipts.append(compensation_response.receipt)

        writing_response = self._complete(
            self.pass1_pipeline.render_writing_prompt(
                request, evidence, patterns, compensation
            ),
            "pass1_writing",
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
        )
        situated = situated_response.payload
        receipts.append(situated_response.receipt)
        self.pass2_pipeline.validate_situated_output(request, situated)

        integration_response = self._complete(
            self.pass2_pipeline.render_integration_prompt(request, situated),
            "pass2_integration",
        )
        integration = integration_response.payload
        receipts.append(integration_response.receipt)

        writing_response = self._complete(
            self.pass2_pipeline.render_writing_prompt(request, situated, integration),
            "pass2_writing",
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
