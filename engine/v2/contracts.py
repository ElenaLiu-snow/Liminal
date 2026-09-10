"""Runtime validation for v2 structures using only the Python standard library."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any


SCHEMA_VERSION = "2.0-alpha.1"
ORIENTATIONS = {"upright", "reversed"}
CONFIDENCE_LEVELS = {"low", "medium", "high"}
OBSERVATION_KINDS = {"noticed", "omitted", "added", "linguistic"}
TRANSFORMATION_TYPES = {
    "convergence",
    "omission",
    "inversion",
    "addition",
    "emotional_recoding",
    "agency_shift",
    "identification_shift",
    "temporal_shift",
}
JUNGIAN_CONCEPTS = {
    "projection",
    "complex_autonomy",
    "compensation",
    "shadow",
    "amplification",
    "transcendent_function",
    "archetype",
}
UNSUPPORTED_SINGLE_SESSION_INFERENCES = {
    "stable_trait",
    "developmental_origin",
    "childhood_experience",
    "trauma_source",
    "clinical_diagnosis",
}
QUESTION_SHIFTS = {"unchanged", "clarified", "shifted_focus", "different_question"}
INHERITANCE_STATUSES = {"integrated", "held", "not_relevant"}
REALITY_EVIDENCE_SOURCES = {"user_question", "question_shift_note"}
REALITY_EVIDENCE_ROLES = {
    "supporting",
    "disconfirming",
    "constraint",
    "action_already_taken",
}
PRACTICAL_MODES = {"action", "reflection", "none"}
FORBIDDEN_PASS1_KEYS = {
    "user_question",
    "question",
    "question_shift",
    "developmental_origin",
    "trait",
    "diagnosis",
}
PASS1_OUTPUT_KEYS = {
    "schema_version",
    "session_id",
    "card_id",
    "orientation",
    "question_blind",
    "symbolic_observations",
    "symbolic_transformations",
    "psychological_patterns",
    "central_pattern_id",
    "jungian_hypotheses",
    "canonical_traditional_reading",
    "compensatory_reading",
    "epistemic_limits",
    "user_display",
}
OBSERVATION_KEYS = {"id", "kind", "description", "user_evidence", "card_evidence", "confidence"}
TRANSFORMATION_KEYS = {
    "id",
    "type",
    "observation_ids",
    "description",
    "user_evidence",
    "card_evidence",
    "confidence",
    "alternative_explanation",
    "disconfirming_evidence",
}
PATTERN_KEYS = {
    "id",
    "scope",
    "sequence",
    "emotional_function",
    "adaptive_value",
    "current_cost",
    "evidence_transformation_ids",
    "user_evidence",
    "confidence",
    "alternative_explanation",
    "disconfirming_evidence",
}
HYPOTHESIS_KEYS = {
    "concept",
    "pattern_ids",
    "interpretation",
    "confidence",
    "alternative_explanation",
}
CANONICAL_KEYS = {
    "card_id",
    "orientation",
    "stable_meaning",
    "visual_symbols",
    "core_themes",
    "source_refs",
    "source_status",
}
COMPENSATION_KEYS = {
    "tension",
    "card_contribution",
    "temporary_third_meaning",
    "evidence_pattern_ids",
}
LIMIT_KEYS = {"weak_signal", "weak_signal_reason", "unsupported_inferences", "limitations"}
DISPLAY_KEYS = {"integrated_reading"}
PASS2_OUTPUT_KEYS = {
    "schema_version",
    "session_id",
    "card_id",
    "orientation",
    "pass1_sha256",
    "user_question",
    "question_shift",
    "question_shift_note",
    "central_axis",
    "pattern_inheritance",
    "question_activation",
    "reality_evidence",
    "situated_traditional_reading",
    "situated_compensation",
    "integrated_third_meaning",
    "bounded_direction",
    "practical_translation",
    "epistemic_limits",
    "user_display",
}
INHERITANCE_KEYS = {"pattern_id", "status", "rationale"}
REALITY_EVIDENCE_KEYS = {"id", "source", "quote", "role", "interpretation"}
BOUNDED_DIRECTION_KEYS = {
    "answer",
    "uncertainty_boundary",
    "evidence_pattern_ids",
    "reality_evidence_ids",
}
PRACTICAL_TRANSLATION_KEYS = {
    "mode",
    "redefined_success",
    "step_or_practice",
    "rationale",
    "evidence_pattern_ids",
    "reality_evidence_ids",
}
PASS2_DISPLAY_KEYS = {"complete_reading", "takeaway_question"}


class ContractError(ValueError):
    """Raised when a v2 payload breaks an engine contract."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ContractError(message)


def _require_exact_keys(value: Mapping[str, Any], expected: set[str], path: str) -> None:
    actual = set(value)
    _require(
        actual == expected,
        f"{path} keys must be exactly {sorted(expected)}; got {sorted(actual)}",
    )


def _require_mapping(value: Any, path: str) -> Mapping[str, Any]:
    _require(isinstance(value, Mapping), f"{path} must be an object")
    return value


def _require_list(value: Any, path: str) -> list[Any]:
    _require(isinstance(value, list), f"{path} must be an array")
    return value


def _require_nonempty_string(value: Any, path: str) -> str:
    _require(isinstance(value, str) and bool(value.strip()), f"{path} must be a non-empty string")
    return value


def _require_string_list(value: Any, path: str, *, min_items: int = 0) -> list[str]:
    items = _require_list(value, path)
    _require(len(items) >= min_items, f"{path} must contain at least {min_items} item(s)")
    for index, item in enumerate(items):
        _require_nonempty_string(item, f"{path}[{index}]")
    return items


def _require_enum(value: Any, allowed: set[str], path: str) -> str:
    _require(value in allowed, f"{path} must be one of {sorted(allowed)}")
    return value


def _collect_forbidden_keys(value: Any, path: str = "$") -> list[str]:
    found: list[str] = []
    if isinstance(value, Mapping):
        for key, child in value.items():
            child_path = f"{path}.{key}"
            if key in FORBIDDEN_PASS1_KEYS:
                found.append(child_path)
            found.extend(_collect_forbidden_keys(child, child_path))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            found.extend(_collect_forbidden_keys(child, f"{path}[{index}]"))
    return found


def _unique_ids(items: Iterable[Mapping[str, Any]], path: str) -> set[str]:
    ids: list[str] = []
    for index, item in enumerate(items):
        ids.append(_require_nonempty_string(item.get("id"), f"{path}[{index}].id"))
    _require(len(ids) == len(set(ids)), f"{path} ids must be unique")
    return set(ids)


def validate_pass1_output(payload: Mapping[str, Any]) -> None:
    """Validate Pass 1 structure plus evidence-link and epistemic invariants."""

    data = _require_mapping(payload, "pass1")
    _require_exact_keys(data, PASS1_OUTPUT_KEYS, "pass1")
    forbidden = _collect_forbidden_keys(data)
    _require(not forbidden, f"Pass 1 is question-blind; forbidden keys found: {forbidden}")

    _require(data.get("schema_version") == SCHEMA_VERSION, "unsupported Pass 1 schema_version")
    _require_nonempty_string(data.get("session_id"), "pass1.session_id")
    _require_nonempty_string(data.get("card_id"), "pass1.card_id")
    _require_enum(data.get("orientation"), ORIENTATIONS, "pass1.orientation")
    _require(data.get("question_blind") is True, "pass1.question_blind must be true")

    observations = [
        _require_mapping(item, f"pass1.symbolic_observations[{index}]")
        for index, item in enumerate(_require_list(data.get("symbolic_observations"), "pass1.symbolic_observations"))
    ]
    observation_ids = _unique_ids(observations, "pass1.symbolic_observations")
    for index, observation in enumerate(observations):
        path = f"pass1.symbolic_observations[{index}]"
        _require_exact_keys(observation, OBSERVATION_KEYS, path)
        _require_enum(observation.get("kind"), OBSERVATION_KINDS, f"{path}.kind")
        _require_nonempty_string(observation.get("description"), f"{path}.description")
        _require_string_list(observation.get("user_evidence"), f"{path}.user_evidence")
        _require_string_list(observation.get("card_evidence"), f"{path}.card_evidence")
        _require_enum(observation.get("confidence"), CONFIDENCE_LEVELS, f"{path}.confidence")

    transformations = [
        _require_mapping(item, f"pass1.symbolic_transformations[{index}]")
        for index, item in enumerate(_require_list(data.get("symbolic_transformations"), "pass1.symbolic_transformations"))
    ]
    transformation_ids = _unique_ids(transformations, "pass1.symbolic_transformations")
    for index, transformation in enumerate(transformations):
        path = f"pass1.symbolic_transformations[{index}]"
        _require_exact_keys(transformation, TRANSFORMATION_KEYS, path)
        _require_enum(transformation.get("type"), TRANSFORMATION_TYPES, f"{path}.type")
        references = set(
            _require_string_list(
                transformation.get("observation_ids"), f"{path}.observation_ids", min_items=1
            )
        )
        _require(references <= observation_ids, f"{path}.observation_ids contains unknown ids")
        _require_nonempty_string(transformation.get("description"), f"{path}.description")
        _require_string_list(transformation.get("user_evidence"), f"{path}.user_evidence", min_items=1)
        _require_string_list(transformation.get("card_evidence"), f"{path}.card_evidence", min_items=1)
        _require_enum(transformation.get("confidence"), CONFIDENCE_LEVELS, f"{path}.confidence")
        _require_nonempty_string(
            transformation.get("alternative_explanation"), f"{path}.alternative_explanation"
        )
        _require_string_list(
            transformation.get("disconfirming_evidence"), f"{path}.disconfirming_evidence"
        )

    patterns = [
        _require_mapping(item, f"pass1.psychological_patterns[{index}]")
        for index, item in enumerate(_require_list(data.get("psychological_patterns"), "pass1.psychological_patterns"))
    ]
    pattern_ids = _unique_ids(patterns, "pass1.psychological_patterns")
    for index, pattern in enumerate(patterns):
        path = f"pass1.psychological_patterns[{index}]"
        _require_exact_keys(pattern, PATTERN_KEYS, path)
        _require(pattern.get("scope") == "session_pattern", f"{path}.scope must be session_pattern")
        _require_string_list(pattern.get("sequence"), f"{path}.sequence", min_items=2)
        _require_nonempty_string(pattern.get("emotional_function"), f"{path}.emotional_function")
        _require_nonempty_string(pattern.get("adaptive_value"), f"{path}.adaptive_value")
        _require_nonempty_string(pattern.get("current_cost"), f"{path}.current_cost")
        references = set(
            _require_string_list(
                pattern.get("evidence_transformation_ids"),
                f"{path}.evidence_transformation_ids",
                min_items=1,
            )
        )
        _require(references <= transformation_ids, f"{path} references unknown transformation ids")
        _require_string_list(pattern.get("user_evidence"), f"{path}.user_evidence", min_items=1)
        _require_enum(pattern.get("confidence"), CONFIDENCE_LEVELS, f"{path}.confidence")
        _require_nonempty_string(pattern.get("alternative_explanation"), f"{path}.alternative_explanation")
        _require_string_list(pattern.get("disconfirming_evidence"), f"{path}.disconfirming_evidence")

    limits = _require_mapping(data.get("epistemic_limits"), "pass1.epistemic_limits")
    _require_exact_keys(limits, LIMIT_KEYS, "pass1.epistemic_limits")
    _require(isinstance(limits.get("weak_signal"), bool), "pass1.epistemic_limits.weak_signal must be boolean")
    unsupported = set(
        _require_string_list(
            limits.get("unsupported_inferences"), "pass1.epistemic_limits.unsupported_inferences"
        )
    )
    _require(
        unsupported <= UNSUPPORTED_SINGLE_SESSION_INFERENCES,
        "pass1.epistemic_limits.unsupported_inferences contains an unknown category",
    )
    _require(
        {"stable_trait", "developmental_origin", "clinical_diagnosis"} <= unsupported,
        "Pass 1 must explicitly mark trait, developmental-origin, and clinical claims as unsupported",
    )
    _require_string_list(limits.get("limitations"), "pass1.epistemic_limits.limitations")

    weak_signal = limits["weak_signal"]
    central_pattern_id = data.get("central_pattern_id")
    if weak_signal:
        _require_nonempty_string(
            limits.get("weak_signal_reason"), "pass1.epistemic_limits.weak_signal_reason"
        )
        _require(
            central_pattern_id is None or central_pattern_id in pattern_ids,
            "central_pattern_id must be null or reference an existing pattern",
        )
    else:
        _require(
            limits.get("weak_signal_reason") is None,
            "non-weak Pass 1 requires weak_signal_reason=null",
        )
        _require(patterns, "non-weak Pass 1 requires at least one psychological pattern")
        _require(central_pattern_id in pattern_ids, "central_pattern_id must reference an existing pattern")

    hypotheses = _require_list(data.get("jungian_hypotheses"), "pass1.jungian_hypotheses")
    for index, hypothesis_value in enumerate(hypotheses):
        hypothesis = _require_mapping(hypothesis_value, f"pass1.jungian_hypotheses[{index}]")
        path = f"pass1.jungian_hypotheses[{index}]"
        _require_exact_keys(hypothesis, HYPOTHESIS_KEYS, path)
        _require_enum(hypothesis.get("concept"), JUNGIAN_CONCEPTS, f"{path}.concept")
        references = set(_require_string_list(hypothesis.get("pattern_ids"), f"{path}.pattern_ids", min_items=1))
        _require(references <= pattern_ids, f"{path}.pattern_ids contains unknown ids")
        _require_nonempty_string(hypothesis.get("interpretation"), f"{path}.interpretation")
        _require_enum(hypothesis.get("confidence"), CONFIDENCE_LEVELS, f"{path}.confidence")
        _require_nonempty_string(hypothesis.get("alternative_explanation"), f"{path}.alternative_explanation")

    canonical = _require_mapping(
        data.get("canonical_traditional_reading"), "pass1.canonical_traditional_reading"
    )
    _require_exact_keys(canonical, CANONICAL_KEYS, "pass1.canonical_traditional_reading")
    _require(canonical.get("card_id") == data["card_id"], "canonical reading card_id mismatch")
    _require(canonical.get("orientation") == data["orientation"], "canonical reading orientation mismatch")
    _require_nonempty_string(
        canonical.get("stable_meaning"), "pass1.canonical_traditional_reading.stable_meaning"
    )
    _require_string_list(
        canonical.get("visual_symbols"), "pass1.canonical_traditional_reading.visual_symbols"
    )
    _require_string_list(canonical.get("core_themes"), "pass1.canonical_traditional_reading.core_themes")
    _require_string_list(canonical.get("source_refs"), "pass1.canonical_traditional_reading.source_refs", min_items=1)

    compensation = _require_mapping(data.get("compensatory_reading"), "pass1.compensatory_reading")
    _require_exact_keys(compensation, COMPENSATION_KEYS, "pass1.compensatory_reading")
    for field in ("tension", "card_contribution", "temporary_third_meaning"):
        _require_nonempty_string(compensation.get(field), f"pass1.compensatory_reading.{field}")
    compensation_pattern_ids = set(
        _require_string_list(
            compensation.get("evidence_pattern_ids"),
            "pass1.compensatory_reading.evidence_pattern_ids",
        )
    )
    _require(compensation_pattern_ids <= pattern_ids, "compensatory_reading references unknown pattern ids")
    if not weak_signal:
        _require(
            central_pattern_id in compensation_pattern_ids,
            "compensatory_reading must reference the central psychological pattern",
        )

    display = _require_mapping(data.get("user_display"), "pass1.user_display")
    _require_exact_keys(display, DISPLAY_KEYS, "pass1.user_display")
    _require_nonempty_string(display.get("integrated_reading"), "pass1.user_display.integrated_reading")


def validate_pass2_output(
    payload: Mapping[str, Any],
    *,
    pass1_payload: Mapping[str, Any],
    pass1_sha256: str,
    user_question: str,
    question_shift: str,
    question_shift_note: str | None,
    situated_reading: Mapping[str, Any],
) -> None:
    """Validate Pass 2 lineage, inheritance, evidence, and display contracts."""

    validate_pass1_output(pass1_payload)
    data = _require_mapping(payload, "pass2")
    _require_exact_keys(data, PASS2_OUTPUT_KEYS, "pass2")
    _require(data.get("schema_version") == SCHEMA_VERSION, "unsupported Pass 2 schema_version")
    _require(data.get("session_id") == pass1_payload["session_id"], "Pass 2 session_id mismatch")
    _require(data.get("card_id") == pass1_payload["card_id"], "Pass 2 card_id mismatch")
    _require(data.get("orientation") == pass1_payload["orientation"], "Pass 2 orientation mismatch")
    _require(data.get("pass1_sha256") == pass1_sha256, "Pass 2 must preserve Pass 1 digest")
    _require(data.get("user_question") == user_question, "Pass 2 user_question mismatch")
    _require_enum(data.get("question_shift"), QUESTION_SHIFTS, "pass2.question_shift")
    _require(data.get("question_shift") == question_shift, "Pass 2 question_shift mismatch")
    _require(
        data.get("question_shift_note") == question_shift_note,
        "Pass 2 question_shift_note mismatch",
    )
    _require_nonempty_string(data.get("central_axis"), "pass2.central_axis")
    _require_nonempty_string(data.get("question_activation"), "pass2.question_activation")
    _require_nonempty_string(data.get("situated_compensation"), "pass2.situated_compensation")
    _require_nonempty_string(
        data.get("integrated_third_meaning"), "pass2.integrated_third_meaning"
    )

    pass1_pattern_ids = {
        pattern["id"] for pattern in pass1_payload["psychological_patterns"]
    }
    inheritance = [
        _require_mapping(item, f"pass2.pattern_inheritance[{index}]")
        for index, item in enumerate(
            _require_list(data.get("pattern_inheritance"), "pass2.pattern_inheritance")
        )
    ]
    inheritance_id_list = [
        _require_nonempty_string(
            item.get("pattern_id"), f"pass2.pattern_inheritance[{index}].pattern_id"
        )
        for index, item in enumerate(inheritance)
    ]
    _require(
        len(inheritance_id_list) == len(set(inheritance_id_list)),
        "pass2.pattern_inheritance pattern_ids must be unique",
    )
    inheritance_ids = set(inheritance_id_list)
    _require(
        inheritance_ids == pass1_pattern_ids,
        "Pass 2 must explicitly map every frozen Pass 1 pattern",
    )
    for index, item in enumerate(inheritance):
        path = f"pass2.pattern_inheritance[{index}]"
        _require_exact_keys(item, INHERITANCE_KEYS, path)
        _require_enum(item.get("status"), INHERITANCE_STATUSES, f"{path}.status")
        _require_nonempty_string(item.get("rationale"), f"{path}.rationale")

    evidence = [
        _require_mapping(item, f"pass2.reality_evidence[{index}]")
        for index, item in enumerate(
            _require_list(data.get("reality_evidence"), "pass2.reality_evidence")
        )
    ]
    evidence_ids = _unique_ids(evidence, "pass2.reality_evidence")
    evidence_sources = {
        "user_question": user_question,
        "question_shift_note": question_shift_note,
    }
    for index, item in enumerate(evidence):
        path = f"pass2.reality_evidence[{index}]"
        _require_exact_keys(item, REALITY_EVIDENCE_KEYS, path)
        source = _require_enum(
            item.get("source"), REALITY_EVIDENCE_SOURCES, f"{path}.source"
        )
        quote = _require_nonempty_string(item.get("quote"), f"{path}.quote")
        source_text = evidence_sources[source]
        _require(
            isinstance(source_text, str) and quote in source_text,
            f"{path}.quote must occur verbatim in its declared source",
        )
        _require_enum(item.get("role"), REALITY_EVIDENCE_ROLES, f"{path}.role")
        _require_nonempty_string(item.get("interpretation"), f"{path}.interpretation")

    situated = _require_mapping(
        data.get("situated_traditional_reading"), "pass2.situated_traditional_reading"
    )
    _require(
        dict(situated) == dict(situated_reading),
        "Pass 2 must preserve the independently generated situated reading",
    )

    def validate_traceable_section(
        value: Any,
        expected_keys: set[str],
        path: str,
        text_fields: tuple[str, ...],
    ) -> Mapping[str, Any]:
        section = _require_mapping(value, path)
        _require_exact_keys(section, expected_keys, path)
        for field in text_fields:
            _require_nonempty_string(section.get(field), f"{path}.{field}")
        pattern_refs = set(
            _require_string_list(
                section.get("evidence_pattern_ids"),
                f"{path}.evidence_pattern_ids",
            )
        )
        reality_refs = set(
            _require_string_list(
                section.get("reality_evidence_ids"),
                f"{path}.reality_evidence_ids",
            )
        )
        _require(pattern_refs <= pass1_pattern_ids, f"{path} references unknown pattern ids")
        _require(reality_refs <= evidence_ids, f"{path} references unknown reality evidence ids")
        return section

    direction = validate_traceable_section(
        data.get("bounded_direction"),
        BOUNDED_DIRECTION_KEYS,
        "pass2.bounded_direction",
        ("answer", "uncertainty_boundary"),
    )
    _require(
        direction["evidence_pattern_ids"] or direction["reality_evidence_ids"],
        "bounded direction must cite Pass 1 or reality evidence",
    )

    practical = validate_traceable_section(
        data.get("practical_translation"),
        PRACTICAL_TRANSLATION_KEYS,
        "pass2.practical_translation",
        ("redefined_success", "rationale"),
    )
    mode = _require_enum(practical.get("mode"), PRACTICAL_MODES, "pass2.practical_translation.mode")
    step = practical.get("step_or_practice")
    if mode == "none":
        _require(step is None, "practical_translation mode=none requires step_or_practice=null")
    else:
        _require_nonempty_string(step, "pass2.practical_translation.step_or_practice")

    limits = _require_mapping(data.get("epistemic_limits"), "pass2.epistemic_limits")
    _require_exact_keys(limits, {"unsupported_inferences", "limitations"}, "pass2.epistemic_limits")
    unsupported = set(
        _require_string_list(
            limits.get("unsupported_inferences"),
            "pass2.epistemic_limits.unsupported_inferences",
        )
    )
    _require(
        {"stable_trait", "developmental_origin", "clinical_diagnosis"} <= unsupported,
        "Pass 2 must preserve single-session epistemic limits",
    )
    _require_string_list(limits.get("limitations"), "pass2.epistemic_limits.limitations")

    display = _require_mapping(data.get("user_display"), "pass2.user_display")
    _require_exact_keys(display, PASS2_DISPLAY_KEYS, "pass2.user_display")
    _require_nonempty_string(display.get("complete_reading"), "pass2.user_display.complete_reading")
    _require_nonempty_string(display.get("takeaway_question"), "pass2.user_display.takeaway_question")
