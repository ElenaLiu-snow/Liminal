"""Prompt-neutral analysis-method specification and validation."""

from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from .contracts import ContractError, TRANSFORMATION_TYPES


METHODOLOGY_DIR = Path(__file__).resolve().parent / "methodology"
METHOD_PATH = METHODOLOGY_DIR / "analysis_method.json"
SOURCE_REGISTRY_PATH = METHODOLOGY_DIR / "source_registry.json"
EVIDENCE_MAP_PATH = METHODOLOGY_DIR / "method_evidence_map.json"


def load_analysis_method(path: Path = METHOD_PATH) -> dict[str, Any]:
    method = json.loads(path.read_text(encoding="utf-8"))
    validate_analysis_method(method)
    return method


def load_method_evidence(
    source_path: Path = SOURCE_REGISTRY_PATH,
    evidence_path: Path = EVIDENCE_MAP_PATH,
) -> tuple[dict[str, Any], dict[str, Any]]:
    registry = json.loads(source_path.read_text(encoding="utf-8"))
    evidence_map = json.loads(evidence_path.read_text(encoding="utf-8"))
    validate_method_evidence(registry, evidence_map)
    return registry, evidence_map


def validate_analysis_method(method: Mapping[str, Any]) -> None:
    if method.get("method_version") != "0.2.0":
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


def validate_method_evidence(
    registry: Mapping[str, Any], evidence_map: Mapping[str, Any]
) -> None:
    if registry.get("registry_version") != "0.1.0":
        raise ContractError("unsupported method source registry_version")
    if evidence_map.get("map_version") != "0.1.0":
        raise ContractError("unsupported method evidence map_version")
    if evidence_map.get("integration_status") != "shadow_only_not_prompt_input":
        raise ContractError("method evidence must remain isolated until activation")

    sources = registry.get("sources")
    if not isinstance(sources, list) or not sources:
        raise ContractError("method source registry must contain sources")
    source_ids = [source.get("id") for source in sources if isinstance(source, Mapping)]
    if len(source_ids) != len(sources) or len(source_ids) != len(set(source_ids)):
        raise ContractError("method source ids must be present and unique")
    for source in sources:
        if not isinstance(source, Mapping):
            raise ContractError("method sources must be objects")
        for field in ("citation", "url", "source_type", "verification", "supports", "does_not_support"):
            if not source.get(field):
                raise ContractError(f"method source {source.get('id')} is missing {field}")
        if not str(source["url"]).startswith("https://"):
            raise ContractError(f"method source {source['id']} must use HTTPS")

    claims = evidence_map.get("claims")
    if not isinstance(claims, list) or not claims:
        raise ContractError("method evidence map must contain claims")
    claim_ids = [claim.get("id") for claim in claims if isinstance(claim, Mapping)]
    if len(claim_ids) != len(claims) or len(claim_ids) != len(set(claim_ids)):
        raise ContractError("method claim ids must be present and unique")
    known_sources = set(source_ids)
    for claim in claims:
        if not isinstance(claim, Mapping):
            raise ContractError("method claims must be objects")
        for field in (
            "claim", "basis_type", "source_ids", "evidence_status",
            "product_rule", "does_not_establish",
        ):
            if not claim.get(field):
                raise ContractError(f"method claim {claim.get('id')} is missing {field}")
        unknown = set(claim["source_ids"]) - known_sources
        if unknown:
            raise ContractError(f"method claim {claim['id']} has unknown sources: {sorted(unknown)}")

    linked_claims = {
        claim_id
        for source in sources
        for claim_id in source["supports"]
    }
    unknown_claims = linked_claims - set(claim_ids)
    if unknown_claims:
        raise ContractError(f"method sources reference unknown claims: {sorted(unknown_claims)}")
