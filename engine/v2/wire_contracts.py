"""Machine-visible JSON shapes appended at the provider boundary.

The accepted prompt templates describe the analytical task. API models cannot
open the local schema files referenced by those templates, so this module adds
only transport structure: exact keys, enums, and nesting. It adds no case facts
or analytical guidance.
"""

from __future__ import annotations

import json
from typing import Any

from .contracts import ContractError


WIRE_CONTRACT_VERSION = "1"


STAGE_CONTRACTS: dict[str, dict[str, Any]] = {
    "pass1_observations": {
        "cardinality_rules": [
            "Each symbolic_transformations[].observation_ids array must contain at least 1 item.",
            "Each symbolic_transformations[].user_evidence array must contain at least 1 item copied verbatim from the user transcript.",
            "Each symbolic_transformations[].card_evidence array must contain at least 1 item."
        ],
        "reference_integrity": [
            "Every symbolic_transformations[].observation_ids value must copy an exact symbolic_observations[].id value from this output. Never invent, translate, rename, or shorten an id."
        ],
        "top_level_keys": [
            "schema_version", "session_id", "card_id",
            "symbolic_observations", "symbolic_transformations",
        ],
        "symbolic_observation_item_keys": [
            "id", "kind", "description", "user_evidence", "card_evidence", "confidence",
        ],
        "symbolic_transformation_item_keys": [
            "id", "type", "observation_ids", "description", "user_evidence",
            "card_evidence", "confidence", "alternative_explanation",
            "disconfirming_evidence",
        ],
        "object_keys": {
            "symbolic_observations[]": [
                "id", "kind", "description", "user_evidence", "card_evidence", "confidence"
            ],
            "symbolic_transformations[]": [
                "id", "type", "observation_ids", "description", "user_evidence",
                "card_evidence", "confidence", "alternative_explanation",
                "disconfirming_evidence",
            ],
        },
        "field_types": {
            "schema_version": "string",
            "session_id": "string",
            "card_id": "string",
            "symbolic_observations": "array<object>",
            "symbolic_observations[].id": "string",
            "symbolic_observations[].kind": "string",
            "symbolic_observations[].description": "string",
            "symbolic_observations[].user_evidence": "array<string>",
            "symbolic_observations[].card_evidence": "array<string>",
            "symbolic_observations[].confidence": "string",
            "symbolic_transformations": "array<object>",
            "symbolic_transformations[].id": "string",
            "symbolic_transformations[].type": "string",
            "symbolic_transformations[].observation_ids": "array<string>",
            "symbolic_transformations[].description": "string",
            "symbolic_transformations[].user_evidence": "array<string>",
            "symbolic_transformations[].card_evidence": "array<string>",
            "symbolic_transformations[].confidence": "string",
            "symbolic_transformations[].alternative_explanation": "string",
            "symbolic_transformations[].disconfirming_evidence": "array<string>"
        },
        "enums": {
            "kind": ["noticed", "omitted", "added", "linguistic"],
            "type": [
                "convergence", "omission", "inversion", "addition",
                "emotional_recoding", "agency_shift", "identification_shift",
                "temporal_shift",
            ],
            "confidence": ["low", "medium", "high"],
        },
    },
    "pass1_patterns": {
        "cardinality_rules": [
            "Each psychological_patterns[].sequence array must contain at least 2 items.",
            "Each psychological_patterns[].evidence_transformation_ids array must contain at least 1 item.",
            "Each psychological_patterns[].user_evidence array must contain at least 1 item copied verbatim from the user transcript.",
            "Each jungian_hypotheses[].pattern_ids array must contain at least 1 item.",
            "When epistemic_limits.weak_signal is false, psychological_patterns must contain at least 1 item and central_pattern_id must not be null."
        ],
        "reference_integrity": [
            "Every psychological_patterns[].evidence_transformation_ids value must copy an exact symbolic_transformations[].id value from PATTERN_INPUT.",
            "central_pattern_id must be null only for a weak signal; otherwise it must copy an exact psychological_patterns[].id value from this output.",
            "Every jungian_hypotheses[].pattern_ids value must copy an exact psychological_patterns[].id value from this output. Never invent, translate, rename, or shorten an id."
        ],
        "top_level_keys": [
            "schema_version", "session_id", "card_id", "psychological_patterns",
            "central_pattern_id", "jungian_hypotheses", "epistemic_limits",
        ],
        "psychological_pattern_item_keys": [
            "id", "scope", "sequence", "emotional_function", "adaptive_value",
            "current_cost", "evidence_transformation_ids", "user_evidence",
            "confidence", "alternative_explanation", "disconfirming_evidence",
        ],
        "jungian_hypothesis_item_keys": [
            "concept", "pattern_ids", "interpretation", "confidence",
            "alternative_explanation",
        ],
        "epistemic_limits_keys": [
            "weak_signal", "weak_signal_reason", "unsupported_inferences", "limitations",
        ],
        "object_keys": {
            "psychological_patterns[]": [
                "id", "scope", "sequence", "emotional_function", "adaptive_value",
                "current_cost", "evidence_transformation_ids", "user_evidence",
                "confidence", "alternative_explanation", "disconfirming_evidence",
            ],
            "jungian_hypotheses[]": [
                "concept", "pattern_ids", "interpretation", "confidence",
                "alternative_explanation",
            ],
            "epistemic_limits": [
                "weak_signal", "weak_signal_reason", "unsupported_inferences", "limitations"
            ],
        },
        "field_types": {
            "schema_version": "string",
            "session_id": "string",
            "card_id": "string",
            "psychological_patterns": "array<object>",
            "psychological_patterns[].id": "string",
            "psychological_patterns[].scope": "string",
            "psychological_patterns[].sequence": "array<string>",
            "psychological_patterns[].emotional_function": "string",
            "psychological_patterns[].adaptive_value": "string",
            "psychological_patterns[].current_cost": "string",
            "psychological_patterns[].evidence_transformation_ids": "array<string>",
            "psychological_patterns[].user_evidence": "array<string>",
            "psychological_patterns[].confidence": "string",
            "psychological_patterns[].alternative_explanation": "string",
            "psychological_patterns[].disconfirming_evidence": "array<string>",
            "central_pattern_id": "string_or_null",
            "jungian_hypotheses": "array<object>",
            "jungian_hypotheses[].concept": "string",
            "jungian_hypotheses[].pattern_ids": "array<string>",
            "jungian_hypotheses[].interpretation": "string",
            "jungian_hypotheses[].confidence": "string",
            "jungian_hypotheses[].alternative_explanation": "string",
            "epistemic_limits": "object",
            "epistemic_limits.weak_signal": "boolean",
            "epistemic_limits.weak_signal_reason": "string_or_null",
            "epistemic_limits.unsupported_inferences": "array<string>",
            "epistemic_limits.limitations": "array<string>"
        },
        "fixed_values": {
            "psychological_patterns[].scope": "session_pattern",
            "epistemic_limits.unsupported_inferences_must_include": [
                "stable_trait", "developmental_origin", "clinical_diagnosis"
            ],
            "weak_signal_rule": (
                "When weak_signal is true, weak_signal_reason must be a non-empty string; "
                "when false, weak_signal_reason must be null."
            ),
        },
        "enums": {
            "confidence": ["low", "medium", "high"],
            "concept": [
                "projection", "complex_autonomy", "compensation", "shadow",
                "amplification", "transcendent_function", "archetype",
            ],
        },
    },
    "pass1_compensation": {
        "reference_integrity": [
            "Every compensatory_reading.evidence_pattern_ids value must copy an exact psychological_patterns[].id value from COMPENSATION_INPUT. Never invent, translate, rename, or shorten an id.",
            "If COMPENSATION_INPUT.central_pattern_id is not null, compensatory_reading.evidence_pattern_ids must include that exact id."
        ],
        "top_level_keys": [
            "schema_version", "session_id", "card_id", "compensatory_reading"
        ],
        "compensatory_reading_keys": [
            "tension", "card_contribution", "temporary_third_meaning",
            "evidence_pattern_ids",
        ],
        "object_keys": {
            "compensatory_reading": [
                "tension", "card_contribution", "temporary_third_meaning",
                "evidence_pattern_ids",
            ]
        },
        "field_types": {
            "schema_version": "string",
            "session_id": "string",
            "card_id": "string",
            "compensatory_reading": "object",
            "compensatory_reading.tension": "string",
            "compensatory_reading.card_contribution": "string",
            "compensatory_reading.temporary_third_meaning": "string",
            "compensatory_reading.evidence_pattern_ids": "array<string>"
        },
    },
    "pass1_writing": {
        "top_level_keys": [
            "schema_version", "session_id", "card_id", "integrated_reading"
        ],
        "field_types": {
            "schema_version": "string",
            "session_id": "string",
            "card_id": "string",
            "integrated_reading": "string"
        },
    },
    "traditional_situated": {
        "cardinality_rules": ["tension_axes must contain at least two distinct strings."],
        "top_level_keys": [
            "card_id", "orientation", "question_relevant_card_structure",
            "orientation_mechanism", "tension_axes", "scope_boundary", "source_refs",
        ],
        "enums": {"orientation": ["upright", "reversed"]},
        "field_types": {
            "card_id": "string",
            "orientation": "string",
            "question_relevant_card_structure": "string",
            "orientation_mechanism": "string",
            "tension_axes": "array<string>",
            "scope_boundary": "string",
            "source_refs": "array<string>"
        },
    },
    "pass2_integration": {
        "cardinality_rules": [
            "bounded_direction must cite at least one id across evidence_pattern_ids and reality_evidence_ids.",
            "Every integrated pattern must map at least two distinct frozen sequence steps in frozen order; held patterns map fewer than two; not_relevant patterns map none.",
            "Every process_step_mappings[].reality_evidence_ids array must contain at least one item.",
            "question_structure.decisive_unknowns must contain at least one item and alternative_hypotheses must contain at least two items."
        ],
        "reference_integrity": [
            "pattern_inheritance must contain every frozen Pass 1 psychological_patterns[].id exactly once, copied without renaming.",
            "Every process_step_mappings[].pass1_step must copy an exact sequence item from its own frozen psychological pattern.",
            "All evidence_pattern_ids values must copy exact process-integrated frozen Pass 1 psychological_patterns[].id values.",
            "All reality_evidence_ids values must copy exact reality_evidence[].id values from this output. Never invent, translate, rename, or shorten an id.",
            "Each reality_evidence[].quote must occur verbatim in the source declared by reality_evidence[].source."
        ],
        "conditional_rules": [
            "integrated requires match_basis=process_recurrence and at least two ordered process mappings.",
            "held requires match_basis=theme_overlap_only or insufficient_process_evidence and fewer than two process mappings.",
            "not_relevant requires match_basis=no_material_match and no process mappings.",
            "When practical_translation.mode is none, step_or_practice must be null; otherwise step_or_practice must be a non-empty string.",
            "practical_translation.decisive_unknown_id and takeaway.decisive_unknown_id must reference question_structure.decisive_unknowns[].id.",
            "epistemic_limits.unsupported_inferences must include stable_trait, developmental_origin, and clinical_diagnosis."
        ],
        "top_level_keys": [
            "schema_version", "session_id", "card_id", "orientation", "pass1_sha256",
            "question_shift", "central_axis", "question_structure",
            "pattern_inheritance", "causal_process_synthesis", "reality_evidence",
            "perspective_shift", "alternative_hypotheses", "bounded_direction",
            "practical_translation", "takeaway", "epistemic_limits",
        ],
        "question_structure_keys": [
            "core_experience", "lived_stakes", "current_explanatory_frame",
            "contemplated_decision", "decisive_unknowns",
        ],
        "question_component_keys": ["summary", "reality_evidence_ids"],
        "decisive_unknown_item_keys": [
            "id", "question", "why_decisive", "reality_evidence_ids"
        ],
        "pattern_inheritance_item_keys": [
            "pattern_id", "status", "match_basis", "rationale", "process_step_mappings",
        ],
        "process_step_mapping_item_keys": [
            "pass1_step", "question_manifestation", "reality_evidence_ids"
        ],
        "reality_evidence_item_keys": [
            "id", "source", "quote", "role", "interpretation"
        ],
        "causal_process_synthesis_keys": [
            "narrative_spine", "pass1_origin_bridge", "adaptive_value_in_context", "current_cost_in_context",
            "evidence_pattern_ids", "reality_evidence_ids",
        ],
        "perspective_shift_keys": [
            "current_frame", "card_specific_counterweight", "relocated_attention",
            "revised_decision_criterion",
        ],
        "alternative_hypothesis_item_keys": [
            "id", "decisive_unknown_id", "possibility",
            "supporting_reality_evidence_ids", "missing_evidence"
        ],
        "bounded_direction_keys": [
            "answer", "uncertainty_boundary", "evidence_pattern_ids",
            "reality_evidence_ids",
        ],
        "practical_translation_keys": [
            "mode", "information_goal", "step_or_practice", "rationale",
            "decisive_unknown_id",
        ],
        "takeaway_keys": [
            "decisive_unknown_id", "alternative_hypothesis_ids", "question"
        ],
        "epistemic_limits_keys": ["unsupported_inferences", "limitations"],
        "object_keys": {
            "question_structure": [
                "core_experience", "lived_stakes", "current_explanatory_frame",
                "contemplated_decision", "decisive_unknowns",
            ],
            "question_structure.core_experience": ["summary", "reality_evidence_ids"],
            "question_structure.lived_stakes[]": ["summary", "reality_evidence_ids"],
            "question_structure.decisive_unknowns[]": [
                "id", "question", "why_decisive", "reality_evidence_ids"
            ],
            "pattern_inheritance[]": [
                "pattern_id", "status", "match_basis", "rationale", "process_step_mappings",
            ],
            "pattern_inheritance[].process_step_mappings[]": [
                "pass1_step", "question_manifestation", "reality_evidence_ids"
            ],
            "reality_evidence[]": ["id", "source", "quote", "role", "interpretation"],
            "causal_process_synthesis": [
                "narrative_spine", "pass1_origin_bridge", "adaptive_value_in_context", "current_cost_in_context",
                "evidence_pattern_ids", "reality_evidence_ids",
            ],
            "perspective_shift": [
                "current_frame", "card_specific_counterweight", "relocated_attention",
                "revised_decision_criterion",
            ],
            "alternative_hypotheses[]": [
                "id", "decisive_unknown_id", "possibility",
                "supporting_reality_evidence_ids", "missing_evidence"
            ],
            "bounded_direction": [
                "answer", "uncertainty_boundary", "evidence_pattern_ids",
                "reality_evidence_ids",
            ],
            "practical_translation": [
                "mode", "information_goal", "step_or_practice", "rationale",
                "decisive_unknown_id",
            ],
            "takeaway": [
                "decisive_unknown_id", "alternative_hypothesis_ids", "question"
            ],
            "epistemic_limits": ["unsupported_inferences", "limitations"],
        },
        "field_types": {
            "schema_version": "string",
            "session_id": "string",
            "card_id": "string",
            "orientation": "string",
            "pass1_sha256": "string",
            "question_shift": "string",
            "central_axis": "string",
            "question_structure": "object",
            "question_structure.core_experience": "object",
            "question_structure.core_experience.summary": "string",
            "question_structure.core_experience.reality_evidence_ids": "array<string>",
            "question_structure.lived_stakes": "array<object>",
            "question_structure.lived_stakes[].summary": "string",
            "question_structure.lived_stakes[].reality_evidence_ids": "array<string>",
            "question_structure.current_explanatory_frame": "object_or_null",
            "question_structure.contemplated_decision": "object_or_null",
            "question_structure.decisive_unknowns": "array<object>",
            "question_structure.decisive_unknowns[].id": "string",
            "question_structure.decisive_unknowns[].question": "string",
            "question_structure.decisive_unknowns[].why_decisive": "string",
            "question_structure.decisive_unknowns[].reality_evidence_ids": "array<string>",
            "pattern_inheritance": "array<object>",
            "pattern_inheritance[].pattern_id": "string",
            "pattern_inheritance[].status": "string",
            "pattern_inheritance[].match_basis": "string",
            "pattern_inheritance[].rationale": "string",
            "pattern_inheritance[].process_step_mappings": "array<object>",
            "pattern_inheritance[].process_step_mappings[].pass1_step": "string",
            "pattern_inheritance[].process_step_mappings[].question_manifestation": "string",
            "pattern_inheritance[].process_step_mappings[].reality_evidence_ids": "array<string>",
            "causal_process_synthesis": "object",
            "causal_process_synthesis.narrative_spine": "string",
            "causal_process_synthesis.pass1_origin_bridge": "string_or_null",
            "causal_process_synthesis.adaptive_value_in_context": "string",
            "causal_process_synthesis.current_cost_in_context": "string",
            "causal_process_synthesis.evidence_pattern_ids": "array<string>",
            "causal_process_synthesis.reality_evidence_ids": "array<string>",
            "reality_evidence": "array<object>",
            "reality_evidence[].id": "string",
            "reality_evidence[].source": "string",
            "reality_evidence[].quote": "string",
            "reality_evidence[].role": "string",
            "reality_evidence[].interpretation": "string",
            "perspective_shift": "object",
            "perspective_shift.current_frame": "string",
            "perspective_shift.card_specific_counterweight": "string",
            "perspective_shift.relocated_attention": "string",
            "perspective_shift.revised_decision_criterion": "string",
            "alternative_hypotheses": "array<object>",
            "alternative_hypotheses[].id": "string",
            "alternative_hypotheses[].decisive_unknown_id": "string",
            "alternative_hypotheses[].possibility": "string",
            "alternative_hypotheses[].supporting_reality_evidence_ids": "array<string>",
            "alternative_hypotheses[].missing_evidence": "string",
            "bounded_direction": "object",
            "bounded_direction.answer": "string",
            "bounded_direction.uncertainty_boundary": "string",
            "bounded_direction.evidence_pattern_ids": "array<string>",
            "bounded_direction.reality_evidence_ids": "array<string>",
            "practical_translation": "object",
            "practical_translation.mode": "string",
            "practical_translation.information_goal": "string",
            "practical_translation.step_or_practice": "string_or_null",
            "practical_translation.rationale": "string",
            "practical_translation.decisive_unknown_id": "string",
            "takeaway": "object",
            "takeaway.decisive_unknown_id": "string",
            "takeaway.alternative_hypothesis_ids": "array<string>",
            "takeaway.question": "string",
            "epistemic_limits": "object",
            "epistemic_limits.unsupported_inferences": "array<string>",
            "epistemic_limits.limitations": "array<string>"
        },
        "enums": {
            "orientation": ["upright", "reversed"],
            "question_shift": [
                "unchanged", "clarified", "shifted_focus", "different_question"
            ],
            "status": ["integrated", "held", "not_relevant"],
            "match_basis": [
                "process_recurrence", "theme_overlap_only",
                "insufficient_process_evidence", "no_material_match"
            ],
            "source": ["user_question", "question_shift_note"],
            "role": [
                "supporting", "disconfirming", "constraint", "action_already_taken",
                "reported_experience", "lived_stake", "current_explanatory_frame",
                "contemplated_decision"
            ],
            "mode": ["action", "reflection", "none"],
        },
    },
    "pass2_writing": {
        "top_level_keys": [
            "schema_version", "session_id", "card_id", "pass1_sha256",
            "complete_reading", "takeaway_question",
        ],
        "field_types": {
            "schema_version": "string",
            "session_id": "string",
            "card_id": "string",
            "pass1_sha256": "string",
            "complete_reading": "string",
            "takeaway_question": "string"
        },
    },
}


def render_wire_prompt(prompt: str, stage: str) -> str:
    contract = STAGE_CONTRACTS.get(stage)
    if contract is None:
        raise KeyError(f"no runtime JSON contract for stage {stage}")
    envelope = {
        "wire_contract_version": WIRE_CONTRACT_VERSION,
        "language_rule": (
            "Write prose values in the predominant natural language of the supplied user "
            "transcript for Pass 1, or of the revealed user question for situated and Pass 2 "
            "stages. Preserve verbatim evidence quotes in their original language."
        ),
        "output_rule": (
            "Return the required object itself. Use exactly the listed top-level and nested "
            "keys. Do not wrap it in stage, evidence, result, data, output, or markdown. "
            "Copy identity and digest values exactly from the supplied input. Arrays may be "
            "empty only when the analytical prompt and contract allow it."
        ),
        "contract": contract,
    }
    return (
        f"{prompt}\n\nRUNTIME_JSON_CONTRACT:\n"
        f"{json.dumps(envelope, ensure_ascii=False, indent=2, sort_keys=True)}"
    )


def _path_values(root: Any, path: str) -> list[Any]:
    values = [root]
    for segment in path.split("."):
        is_array = segment.endswith("[]")
        key = segment[:-2] if is_array else segment
        next_values: list[Any] = []
        for value in values:
            if not isinstance(value, dict) or key not in value:
                raise ContractError(f"wire output is missing {path}")
            child = value[key]
            if is_array:
                if not isinstance(child, list):
                    raise ContractError(f"wire output {key} must be an array")
                next_values.extend(child)
            else:
                next_values.append(child)
        values = next_values
    return values


def _matches_type(value: Any, expected: str) -> bool:
    if expected == "string":
        return isinstance(value, str) and bool(value.strip())
    if expected == "string_or_null":
        return value is None or (isinstance(value, str) and bool(value.strip()))
    if expected == "boolean":
        return isinstance(value, bool)
    if expected == "object":
        return isinstance(value, dict)
    if expected == "object_or_null":
        return value is None or isinstance(value, dict)
    if expected == "array<object>":
        return isinstance(value, list) and all(isinstance(item, dict) for item in value)
    if expected == "array<string>":
        return isinstance(value, list) and all(
            isinstance(item, str) and bool(item.strip()) for item in value
        )
    raise ContractError(f"unknown wire contract type {expected}")


def validate_wire_payload(payload: Any, stage: str) -> None:
    contract = STAGE_CONTRACTS.get(stage)
    if contract is None:
        raise ContractError(f"no runtime JSON contract for stage {stage}")
    if not isinstance(payload, dict):
        raise ContractError(f"{stage} wire output must be an object")
    expected_top = set(contract["top_level_keys"])
    if set(payload) != expected_top:
        raise ContractError(
            f"{stage} wire output keys must be exactly {sorted(expected_top)}; "
            f"got {sorted(payload)}"
        )
    for path, expected_type in contract.get("field_types", {}).items():
        for value in _path_values(payload, path):
            if not _matches_type(value, expected_type):
                raise ContractError(f"{stage} wire output {path} must be {expected_type}")
    for path, keys in contract.get("object_keys", {}).items():
        for value in _path_values(payload, path):
            if not isinstance(value, dict) or set(value) != set(keys):
                raise ContractError(
                    f"{stage} wire output {path} keys must be exactly {sorted(keys)}"
                )
