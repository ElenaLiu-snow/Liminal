"""Extract per-card Waite text from a locally cached public-domain transcription.

The downloader is intentionally outside this script. Cache the 78 card pages and
the shared Major Arcana divinatory page, then run this deterministic parser. The
result remains machine-transcribed and must be checked against the registered scan.
"""

from __future__ import annotations

import argparse
import html
import json
import re
from pathlib import Path
from typing import Any

from .build_knowledge import DECK_FILES, ENGINE_DIR


DEFAULT_OUTPUT = Path(__file__).resolve().parent / "data" / "waite_transcriptions.json"
MIRROR_BASE = "https://rider-waite.com/symbolism"


def _plain_text(fragment: str) -> str:
    without_tags = re.sub(r"<[^>]+>", " ", fragment)
    decoded = html.unescape(without_tags).replace("\xa0", " ")
    normalized = re.sub(r"\s+", " ", decoded).strip()
    return re.sub(r"\s+([:;,.])", r"\1", normalized)


def _paragraphs(path: Path) -> list[str]:
    source = path.read_text(encoding="utf-8")
    match = re.search(
        r'<div class="entry-content">(.*?)</div><!-- \.entry-content -->',
        source,
        flags=re.DOTALL,
    )
    if match is None:
        raise ValueError(f"entry-content not found in {path}")
    return [
        text
        for fragment in re.findall(r"<p\b[^>]*>(.*?)</p>", match.group(1), re.DOTALL)
        if (text := _plain_text(fragment))
    ]


def _content_paragraphs(path: Path) -> list[str]:
    return [
        paragraph
        for paragraph in _paragraphs(path)
        if not (
            ("previous" in paragraph.casefold() and "next" in paragraph.casefold())
            or paragraph.casefold().startswith("next:")
        )
    ]


def _minor_text(path: Path) -> tuple[str, str, str | None]:
    paragraphs = _content_paragraphs(path)
    div_index = next(
        index
        for index, paragraph in enumerate(paragraphs)
        if paragraph.casefold().startswith("divinatory meanings")
    )
    reversed_index = next(
        (
            index
            for index, paragraph in enumerate(paragraphs)
            if index >= div_index and paragraph.casefold().startswith("reversed")
        ),
        None,
    )
    description = "\n\n".join(paragraphs[:div_index]).strip()
    upright = re.sub(
        r"^Divinatory Meanings\s*:\s*", "", paragraphs[div_index], flags=re.IGNORECASE
    ).strip()
    reversed_text = None
    if reversed_index is not None:
        reversed_text = re.sub(
            r"^Reversed\s*:\s*", "", paragraphs[reversed_index], flags=re.IGNORECASE
        ).strip()
    if not description or not upright:
        raise ValueError(f"incomplete minor text in {path}")
    return description, upright, reversed_text


def _major_divinatory(path: Path) -> dict[int, tuple[str, str]]:
    meanings: dict[int, tuple[str, str]] = {}
    for paragraph in _paragraphs(path):
        start = re.match(r"^(ZERO|\d+)\.\s+", paragraph, flags=re.IGNORECASE)
        if start is None or "Reversed:" not in paragraph:
            continue
        number = 0 if start.group(1).casefold() == "zero" else int(start.group(1))
        body = paragraph[start.end() :]
        title_and_upright, reversed_text = body.split("Reversed:", 1)
        title_split = re.split(r"\.(?:–|-)\s*", title_and_upright, maxsplit=1)
        if len(title_split) != 2:
            raise ValueError(f"major meaning separator not found for {number}: {paragraph}")
        upright = title_split[1].strip()
        meanings[number] = (upright, reversed_text.strip())
    if set(meanings) != set(range(22)):
        raise ValueError(f"expected Major Arcana 0-21, got {sorted(meanings)}")
    return meanings


def _legacy_cards() -> list[dict[str, Any]]:
    cards = []
    for filename in DECK_FILES:
        cards.extend(json.loads((ENGINE_DIR / filename).read_text(encoding="utf-8")))
    return cards


def extract_transcriptions(source_dir: Path) -> dict[str, Any]:
    major_meanings = _major_divinatory(source_dir / "major_divinatory.html")
    records = []
    for card in _legacy_cards():
        if card["suit"] == "major":
            number = card["number"]
            source_path = source_dir / f"major_{number:02d}.html"
            description = "\n\n".join(_content_paragraphs(source_path)).strip()
            upright, reversed_text = major_meanings[number]
            source_url = f"{MIRROR_BASE}/pictorial-key-{number:02d}/"
        else:
            number = card["number"]
            source_number = f"{number:02d}" if number < 10 else str(number)
            source_path = source_dir / f"{card['suit']}_{source_number}.html"
            description, upright, reversed_text = _minor_text(source_path)
            source_url = f"{MIRROR_BASE}/pictorial-key-{card['suit']}{source_number}/"
        if not description:
            raise ValueError(f"empty description for {card['id']}")
        records.append(
            {
                "card_id": card["id"],
                "card_name": card["name"],
                "description": description,
                "upright": upright,
                "reversed": reversed_text,
                "source_url": source_url,
                "review_status": "machine_transcribed_unreviewed",
            }
        )
    if len(records) != 78:
        raise ValueError(f"expected 78 records, got {len(records)}")
    return {
        "schema_version": "1",
        "source_id": "waite_transcription_mirror",
        "extraction_version": "1",
        "review_status": "machine_transcribed_unreviewed",
        "records": records,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    data = extract_transcriptions(args.source_dir)
    args.output.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()
