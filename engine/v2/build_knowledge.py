"""Build the versioned RWS knowledge index from the frozen v1 card files.

This migration is intentionally conservative: it links every card to primary
sources and separates visual facts from interpretations, but it does not claim
that the migrated wording has already been checked against Waite or the image.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


ENGINE_DIR = Path(__file__).resolve().parents[1]
OUTPUT_PATH = Path(__file__).resolve().parent / "data" / "rws_knowledge.json"
DECK_FILES = (
    "cards_major.json",
    "cards_wands.json",
    "cards_cups.json",
    "cards_swords.json",
    "cards_pentacles.json",
)
SACRED_TEXTS_BASE = (
    "https://sacred-texts.com/book/the-pictorial-key-to-the-tarot/shell"
)
MAJOR_DIVINATORY_URL = (
    f"{SACRED_TEXTS_BASE}/section-3-the-greater-arcana-and-their-divinatory-meanings"
)
COMMONS_CATEGORY_URL = (
    "https://commons.wikimedia.org/wiki/Category:Rider-Waite_tarot_deck"
)
MAJOR_SLUGS = {
    0: "zero-the-fool",
    1: "i-the-magician",
    2: "ii-the-high-priestess",
    3: "iii-the-empress",
    4: "iv-the-emperor",
    5: "v-the-hierophant",
    6: "vi-the-lovers",
    7: "vii-the-chariot",
    8: "viii-strength-or-fortitude",
    9: "ix-the-hermit",
    10: "x-wheel-of-fortune",
    11: "xi-justice",
    12: "xii-the-hanged-man",
    13: "xiii-death",
    14: "xiv-temperance",
    15: "xv-the-devil",
    16: "xvi-the-tower",
    17: "xvii-the-star",
    18: "xviii-the-moon",
    19: "xix-the-sun",
    20: "xx-the-last-judgement",
    21: "xxi-the-world",
}
REVERSAL_MODES = ["blocked", "internalized", "excessive", "misdirected", "delayed"]


def _slugify_minor(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", name.casefold()).strip("-")


def _rank(card: dict[str, Any]) -> str:
    if card["suit"] == "major":
        return "major"
    name = card["name"].split(" ", 1)[0].casefold()
    return name


def _card_page(card: dict[str, Any]) -> str:
    if card["suit"] == "major":
        slug = MAJOR_SLUGS[card["number"]]
    else:
        slug = _slugify_minor(card["name"])
    return f"{SACRED_TEXTS_BASE}/{slug}"


def _legacy_cards(engine_dir: Path) -> list[tuple[str, dict[str, Any]]]:
    cards: list[tuple[str, dict[str, Any]]] = []
    for filename in DECK_FILES:
        path = engine_dir / filename
        for card in json.loads(path.read_text(encoding="utf-8")):
            cards.append((filename, card))
    return cards


def build_knowledge(engine_dir: Path = ENGINE_DIR) -> dict[str, Any]:
    records = []
    for filename, card in _legacy_cards(engine_dir):
        card_url = _card_page(card)
        divinatory_url = MAJOR_DIVINATORY_URL if card["suit"] == "major" else card_url
        records.append(
            {
                "id": card["id"],
                "name": card["name"],
                "system": card["system"],
                "arcana": "major" if card["suit"] == "major" else "minor",
                "suit": card["suit"],
                "rank": _rank(card),
                "number": card["number"],
                "visual_inventory": {
                    "items": list(card["theme_space"]["core_imagery"]),
                    "provenance": f"engine/{filename}#{card['id']}",
                    "review_status": "migrated_unreviewed",
                },
                "source_links": {
                    "waite_symbolism": {
                        "source_id": "waite_1911_sacred_texts",
                        "url": card_url,
                        "status": "linked_not_transcribed",
                    },
                    "waite_divinatory": {
                        "source_id": "waite_1911_sacred_texts",
                        "url": divinatory_url,
                        "status": "linked_not_transcribed",
                    },
                    "image_archive": {
                        "source_id": "smith_rws_commons",
                        "url": COMMONS_CATEGORY_URL,
                        "status": "candidate_collection_only",
                    },
                },
                "modern_interpretation": {
                    "upright": card["standard_meaning"]["upright"],
                    "reversed": card["standard_meaning"]["reversed"],
                    "core_themes": list(card["theme_space"]["core_themes"]),
                    "provenance": f"engine/{filename}#{card['id']}",
                    "review_status": "migrated_unreviewed",
                },
                "reversal_framework": {
                    "supported_modes": list(REVERSAL_MODES),
                    "card_specific_modes": [],
                    "review_status": "framework_only_pending",
                },
                "review": {
                    "waite_text": "pending",
                    "visual_inventory": "pending",
                    "modern_interpretation": "pending",
                    "image_asset": "pending",
                },
            }
        )

    return {
        "schema_version": "2.0-alpha.1",
        "knowledge_version": "rws-0.1.0",
        "deck": {
            "name": "Rider-Waite-Smith",
            "card_count": 78,
            "language": "en",
            "integration_status": "shadow_read_only",
            "verification_source_id": "waite_1922_commons_scan",
            "notes": (
                "Primary sources are linked for all cards. Migrated text remains "
                "provisional until field-level review; no Jungian preset is imported."
            ),
        },
        "source_registry": {
            "waite_1911_sacred_texts": {
                "author": "Arthur Edward Waite",
                "title": "The Pictorial Key to the Tarot",
                "publication_year": 1911,
                "url": "https://sacred-texts.com/tarot/pkt/pkttp.htm",
                "role": "primary_text_archive",
                "usage_note": (
                    "Use as the historical RWS baseline; do not copy its wording "
                    "directly into user-facing output."
                ),
            },
            "smith_rws_commons": {
                "creator": "Pamela Colman Smith",
                "title": "Rider-Waite tarot deck media category",
                "url": COMMONS_CATEGORY_URL,
                "role": "candidate_image_archive",
                "usage_note": (
                    "Select and verify each file page separately; some modern "
                    "colorizations can have different rights."
                ),
            },
            "waite_1922_commons_scan": {
                "author": "Arthur Edward Waite",
                "illustrator": "Pamela Colman Smith",
                "title": "The Pictorial Key to the Tarot (1922 reprint scan)",
                "url": "https://commons.wikimedia.org/wiki/File:The_Pictorial_Key_to_the_Tarot.pdf",
                "role": "primary_scan_for_offline_verification",
                "sha256": "2f54bc008cab332b10d9f114ba8dda55845ce850a05e3a707089677bf3d0abb8",
                "usage_note": (
                    "The large PDF is not committed. Use this checksum to verify "
                    "a temporary local copy used during field review."
                ),
            },
            "liminal_v1": {
                "title": "Liminal v1 card dataset",
                "url": "engine/cards_*.json",
                "role": "migration_source",
                "usage_note": "Provisional Liminal-authored summaries awaiting review.",
            },
        },
        "cards": records,
    }


def main() -> None:
    OUTPUT_PATH.write_text(
        json.dumps(build_knowledge(), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
