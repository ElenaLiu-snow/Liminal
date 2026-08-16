"""Input-isolated traditional tarot data and situated-request preparation."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .contracts import ContractError, ORIENTATIONS


ENGINE_DIR = Path(__file__).resolve().parents[1]
PROMPT_PATH = Path(__file__).resolve().parent / "prompts" / "traditional_situated.txt"
DECK_FILES = (
    "cards_major.json",
    "cards_wands.json",
    "cards_cups.json",
    "cards_swords.json",
    "cards_pentacles.json",
)
FORBIDDEN_SITUATED_KEYS = {
    "raw_transcript",
    "features",
    "pass1",
    "symbolic_observations",
    "symbolic_transformations",
    "psychological_patterns",
    "jungian_hypotheses",
}
SITUATED_OUTPUT_KEYS = {
    "card_id",
    "orientation",
    "card_role_in_question",
    "practical_tension",
    "bounded_direction",
    "reflection_point",
    "source_refs",
}


class CardNotFoundError(KeyError):
    """Raised when a card id or exact name is absent from the local deck."""


class TraditionalTarotLayer:
    """Read-only traditional layer backed by the existing 78-card v1 dataset.

    The current source is deliberately marked provisional. Waite text and human
    review can replace individual records later without changing the interface.
    """

    def __init__(self, engine_dir: Path | None = None) -> None:
        self.engine_dir = engine_dir or ENGINE_DIR
        self._cards = self._load_cards()
        self._by_id = {card["id"]: card for card in self._cards}
        self._by_name = {card["name"].casefold(): card for card in self._cards}
        if len(self._cards) != 78 or len(self._by_id) != 78:
            raise ContractError("traditional layer requires 78 uniquely identified cards")

    def _load_cards(self) -> list[dict[str, Any]]:
        cards: list[dict[str, Any]] = []
        for filename in DECK_FILES:
            path = self.engine_dir / filename
            cards.extend(json.loads(path.read_text(encoding="utf-8")))
        return cards

    def get_card(self, card_ref: str) -> dict[str, Any]:
        card = self._by_id.get(card_ref) or self._by_name.get(card_ref.casefold())
        if card is None:
            raise CardNotFoundError(card_ref)
        return card

    def canonical(self, card_ref: str, orientation: str) -> dict[str, Any]:
        """Return the question- and transcript-blind canonical reading."""

        if orientation not in ORIENTATIONS:
            raise ContractError(f"orientation must be one of {sorted(ORIENTATIONS)}")
        card = self.get_card(card_ref)
        meaning_key = "upright" if orientation == "upright" else "reversed"
        source_file = self._source_file_for(card["id"])
        return {
            "card_id": card["id"],
            "orientation": orientation,
            "stable_meaning": card["standard_meaning"][meaning_key],
            "visual_symbols": list(card["theme_space"]["core_imagery"]),
            "core_themes": list(card["theme_space"]["core_themes"]),
            "source_refs": [
                f"engine/{source_file}#{card['id']}",
                "engine/tarot_card_schema.md",
            ],
            "source_status": "provisional_v1_dataset",
        }

    def stimulus(self, card_ref: str) -> dict[str, Any]:
        """Return visual stimulus facts without meanings or psychological presets."""

        card = self.get_card(card_ref)
        return {
            "id": card["id"],
            "name": card["name"],
            "system": card["system"],
            "number": card["number"],
            "suit": card["suit"],
            "visual_inventory": list(card["theme_space"]["core_imagery"]),
        }

    def prepare_situated_request(
        self, card_ref: str, orientation: str, user_question: str
    ) -> dict[str, Any]:
        """Build the only payload permitted to enter the situated tarot prompt."""

        if not isinstance(user_question, str) or not user_question.strip():
            raise ContractError("situated traditional reading requires a revealed question")
        canonical = self.canonical(card_ref, orientation)
        request = {
            "canonical_reading": canonical,
            "user_question": user_question.strip(),
        }
        self.validate_situated_request(request)
        return request

    @staticmethod
    def validate_situated_request(request: dict[str, Any]) -> None:
        unexpected = set(request) - {"canonical_reading", "user_question"}
        forbidden = set(request) & FORBIDDEN_SITUATED_KEYS
        if unexpected or forbidden:
            raise ContractError(
                f"situated traditional input isolation failed: unexpected={sorted(unexpected | forbidden)}"
            )

    def render_situated_prompt(self, request: dict[str, Any]) -> str:
        self.validate_situated_request(request)
        template = PROMPT_PATH.read_text(encoding="utf-8")
        canonical_json = json.dumps(
            request["canonical_reading"], ensure_ascii=False, indent=2, sort_keys=True
        )
        return template.replace("{{CANONICAL_READING}}", canonical_json).replace(
            "{{USER_QUESTION}}", request["user_question"]
        )

    @staticmethod
    def validate_situated_output(output: dict[str, Any], request: dict[str, Any]) -> None:
        """Validate situated output without exposing Pass 1 data to this layer."""

        TraditionalTarotLayer.validate_situated_request(request)
        if set(output) != SITUATED_OUTPUT_KEYS:
            raise ContractError(
                f"situated output keys must be exactly {sorted(SITUATED_OUTPUT_KEYS)}"
            )
        canonical = request["canonical_reading"]
        if output.get("card_id") != canonical["card_id"]:
            raise ContractError("situated output card_id mismatch")
        if output.get("orientation") != canonical["orientation"]:
            raise ContractError("situated output orientation mismatch")
        for field in (
            "card_role_in_question",
            "practical_tension",
            "bounded_direction",
            "reflection_point",
        ):
            value = output.get(field)
            if not isinstance(value, str) or not value.strip():
                raise ContractError(f"situated output {field} must be a non-empty string")
        source_refs = output.get("source_refs")
        if not isinstance(source_refs, list) or not source_refs:
            raise ContractError("situated output source_refs must be a non-empty list")
        if not set(canonical["source_refs"]).issubset(source_refs):
            raise ContractError("situated output must preserve canonical source references")

    @staticmethod
    def _source_file_for(card_id: str) -> str:
        if card_id.startswith("major_"):
            return "cards_major.json"
        for suit in ("wands", "cups", "swords", "pentacles"):
            if card_id.startswith(f"{suit}_"):
                return f"cards_{suit}.json"
        raise ContractError(f"unrecognized card id prefix: {card_id}")
