"""Conservative multilingual feature preparation for the v2 prompt."""

from __future__ import annotations

import re
from typing import Any

from engine.feature_extractor import extract_features


HAN_RE = re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff]")
ENGLISH_WORD_RE = re.compile(r"\b[a-zA-Z']+\b")
CHINESE_HESITATION_MARKERS = ("嗯", "呃", "额", "唔")
CHINESE_HEDGING_MARKERS = ("我猜", "可能", "也许", "应该", "我觉得", "好像", "似乎")


def _found_markers(text: str, markers: tuple[str, ...]) -> list[dict[str, Any]]:
    found: list[dict[str, Any]] = []
    for marker in markers:
        count = text.count(marker)
        if count:
            found.append({"marker": marker, "count": count})
    return found


def extract_v2_features(
    raw_transcript: str, speaking_duration_seconds: float | None = None
) -> dict[str, Any]:
    """Return v1 features plus explicitly uncalibrated multilingual signals.

    Chinese values remain raw counts rather than pseudo-normalized psychological
    scores. They are evidence aids for a model, never standalone triggers.
    """

    base = extract_features(raw_transcript, speaking_duration_seconds)
    han_count = len(HAN_RE.findall(raw_transcript))
    english_count = len(ENGLISH_WORD_RE.findall(raw_transcript))
    if han_count and english_count:
        language_hint = "mixed"
    elif han_count:
        language_hint = "zh"
    elif english_count:
        language_hint = "en"
    else:
        language_hint = "unknown"

    return {
        **base,
        "language_hint": language_hint,
        "han_character_count": han_count,
        "english_word_count": english_count,
        "first_person_mentions_zh": raw_transcript.count("我"),
        "hesitation_markers_zh": _found_markers(raw_transcript, CHINESE_HESITATION_MARKERS),
        "hedging_markers_zh": _found_markers(raw_transcript, CHINESE_HEDGING_MARKERS),
        "multilingual_feature_status": "heuristic_unvalidated",
    }
