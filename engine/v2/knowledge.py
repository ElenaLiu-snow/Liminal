"""Read-only access and structural validation for the v2 tarot knowledge base."""

from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from .contracts import ContractError


KNOWLEDGE_PATH = Path(__file__).resolve().parent / "data" / "rws_knowledge.json"
REVIEW_STATES = {"pending", "reviewed", "rejected"}
FORBIDDEN_PRESET_KEYS = {
    "jungian_mapping",
    "complex_signals",
    "emotional_tone",
    "agency",
    "time_orientation",
    "conflict_harmony",
    "relational_direction",
}


def _find_forbidden(value: Any, path: str = "$") -> list[str]:
    found: list[str] = []
    if isinstance(value, Mapping):
        for key, child in value.items():
            child_path = f"{path}.{key}"
            if key in FORBIDDEN_PRESET_KEYS:
                found.append(child_path)
            found.extend(_find_forbidden(child, child_path))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            found.extend(_find_forbidden(child, f"{path}[{index}]") )
    return found


def validate_knowledge_base(data: Mapping[str, Any]) -> None:
    if data.get("schema_version") != "2.0-alpha.1":
        raise ContractError("unsupported knowledge schema_version")
    if data.get("knowledge_version") != "rws-0.1.0":
        raise ContractError("unsupported knowledge_version")
    cards = data.get("cards")
    if not isinstance(cards, list) or len(cards) != 78:
        raise ContractError("knowledge base must contain exactly 78 cards")
    ids = [card.get("id") for card in cards if isinstance(card, Mapping)]
    names = [card.get("name") for card in cards if isinstance(card, Mapping)]
    if len(set(ids)) != 78 or len(set(names)) != 78:
        raise ContractError("knowledge card ids and names must be unique")
    sources = data.get("source_registry")
    if not isinstance(sources, Mapping):
        raise ContractError("knowledge source_registry must be an object")
    for card in cards:
        if not isinstance(card, Mapping):
            raise ContractError("every knowledge card must be an object")
        if card.get("system") != "Waite-Smith":
            raise ContractError(f"unexpected system for {card.get('id')}")
        if card.get("arcana") not in {"major", "minor"}:
            raise ContractError(f"invalid arcana for {card.get('id')}")
        links = card.get("source_links")
        if not isinstance(links, Mapping):
            raise ContractError(f"missing source_links for {card.get('id')}")
        for role in ("waite_symbolism", "waite_divinatory", "image_archive"):
            link = links.get(role)
            if not isinstance(link, Mapping):
                raise ContractError(f"missing {role} source for {card.get('id')}")
            if link.get("source_id") not in sources:
                raise ContractError(f"unknown source_id for {card.get('id')}:{role}")
            if not str(link.get("url", "")).startswith("https://"):
                raise ContractError(f"non-HTTPS source for {card.get('id')}:{role}")
        waite = card.get("waite_text")
        if not isinstance(waite, Mapping):
            raise ContractError(f"missing Waite text for {card.get('id')}")
        for field in ("description", "upright"):
            if not isinstance(waite.get(field), str) or not waite[field].strip():
                raise ContractError(f"empty Waite {field} for {card.get('id')}")
        reversed_text = waite.get("reversed")
        if reversed_text is None:
            if waite.get("reversed_status") != "not_present_in_waite_source":
                raise ContractError(f"unexplained missing Waite reversal for {card.get('id')}")
        elif not isinstance(reversed_text, str) or not reversed_text.strip():
            raise ContractError(f"invalid Waite reversal for {card.get('id')}")
        review = card.get("review")
        if not isinstance(review, Mapping) or set(review.values()) - REVIEW_STATES:
            raise ContractError(f"invalid review state for {card.get('id')}")
    forbidden = _find_forbidden(data)
    if forbidden:
        raise ContractError(f"analysis presets leaked into knowledge base: {forbidden}")


class TarotKnowledgeBase:
    """Versioned, prompt-neutral tarot knowledge records."""

    def __init__(self, path: Path = KNOWLEDGE_PATH) -> None:
        self.path = path
        self.data = json.loads(path.read_text(encoding="utf-8"))
        validate_knowledge_base(self.data)
        self.cards = list(self.data["cards"])
        self._by_id = {card["id"]: card for card in self.cards}
        self._by_name = {card["name"].casefold(): card for card in self.cards}

    def get_card(self, card_ref: str) -> dict[str, Any]:
        card = self._by_id.get(card_ref) or self._by_name.get(card_ref.casefold())
        if card is None:
            raise KeyError(card_ref)
        return card
