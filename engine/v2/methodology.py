"""Prompt-neutral analysis-method specification and validation."""

from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from .contracts import ContractError, TRANSFORMATION_TYPES


METHOD_PATH = Path(__file__).resolve().parent / "methodology" / "analysis_method.json"


def load_analysis_method(path: Path = METHOD_PATH) -> dict[str, Any]:
    method = json.loads(path.read_text(encoding="utf-8"))
    validate_analysis_method(method)
    return method


def validate_analysis_method(method: Mapping[str, Any]) -> None:
    if method.get("method_version") != "0.1.0":
        raise ContractError("unsupported analysis method_version")
    if method.get("integration_status") != "shadow_only_not_prompt_input":
        raise ContractError("analysis method must remain isolated until an explicit gate")
    taxonomy = method.get("transformation_taxonomy")
    if not isinstance(taxonomy, Mapping) or set(taxonomy) != TRANSFORMATION_TYPES:
        raise ContractError("method taxonomy must match the runtime contract")
    for name, rule in taxonomy.items():
        if not isinstance(rule, Mapping):
            raise ContractError(f"method rule {name} must be an object")
        for field in ("definition", "minimum_evidence", "common_false_positive"):
            if not rule.get(field):
                raise ContractError(f"method rule {name} is missing {field}")
    gate = method.get("session_pattern_gate")
    if not isinstance(gate, Mapping) or gate.get("minimum_sequence_steps", 0) < 2:
        raise ContractError("session patterns require a multi-step sequence")
    change_control = method.get("change_control")
    if not isinstance(change_control, Mapping) or change_control.get("prompt_consumption") != "disabled":
        raise ContractError("method cannot enter prompts without explicit activation")
