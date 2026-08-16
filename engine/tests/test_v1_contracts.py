import hashlib
import json
import re
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
ENGINE_DIR = PROJECT_ROOT / "engine"


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


class AnalysisSchemaContractTests(unittest.TestCase):
    def setUp(self):
        self.schema = load_json(ENGINE_DIR / "analysis_schema.json")

    def test_schema_has_only_the_canonical_v1_top_level_contract(self):
        self.assertEqual(self.schema["version"], "1.1")
        self.assertEqual(
            set(self.schema),
            {
                "version",
                "description",
                "input_schema",
                "analysis_layer_output",
                "pipeline_notes",
            },
        )
        self.assertNotIn("writing_layer_input", self.schema)
        self.assertNotIn("writing_layer_output", self.schema)

    def test_three_direct_to_user_output_parts_exist(self):
        output = self.schema["analysis_layer_output"]
        expected_parts = (
            "part_1_projection",
            "part_2_synchronicity",
            "part_3_closing_question",
        )
        for part in expected_parts:
            self.assertIn(part, output)
        self.assertIn(
            "shown directly to user",
            self.schema["pipeline_notes"]["mvp_output"],
        )

    def test_deviation_threshold_is_consistently_inclusive(self):
        files = (
            ENGINE_DIR / "analysis_schema.json",
            ENGINE_DIR / "prompts" / "analysis_layer.txt",
            ENGINE_DIR / "tarot_card_schema.md",
        )
        for path in files:
            text = path.read_text(encoding="utf-8")
            self.assertIn(">= 0.3", text, msg=f"missing inclusive threshold in {path}")
            self.assertIsNone(
                re.search(r"(?<![=])>\s*0\.3", text),
                msg=f"exclusive threshold remains in {path}",
            )


class TarotDatasetContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.expected_counts = {
            "cards_major.json": 22,
            "cards_cups.json": 14,
            "cards_pentacles.json": 14,
            "cards_swords.json": 14,
            "cards_wands.json": 14,
        }
        cls.cards_by_file = {
            filename: load_json(ENGINE_DIR / filename)
            for filename in cls.expected_counts
        }

    def test_deck_contains_78_unique_cards(self):
        all_cards = []
        for filename, expected_count in self.expected_counts.items():
            cards = self.cards_by_file[filename]
            self.assertIsInstance(cards, list)
            self.assertEqual(len(cards), expected_count, msg=filename)
            all_cards.extend(cards)

        ids = [card["id"] for card in all_cards]
        self.assertEqual(len(ids), 78)
        self.assertEqual(len(set(ids)), 78)

    def test_theme_space_numeric_invariants(self):
        for filename, cards in self.cards_by_file.items():
            for card in cards:
                with self.subTest(file=filename, card=card["id"]):
                    theme = card["theme_space"]
                    bounded_values = (
                        theme["emotional_tone"]["valence"],
                        theme["emotional_tone"]["arousal"],
                        theme["agency"]["score"],
                        theme["conflict_harmony"]["score"],
                    )
                    for value in bounded_values:
                        self.assertGreaterEqual(value, 0)
                        self.assertLessEqual(value, 1)

                    time_total = sum(
                        theme["time_orientation"][key]
                        for key in ("past", "present", "future")
                    )
                    relation_total = sum(
                        theme["relational_direction"][key]
                        for key in ("inward", "outward")
                    )
                    self.assertAlmostEqual(time_total, 1.0, places=6)
                    self.assertAlmostEqual(relation_total, 1.0, places=6)


class BaselineManifestContractTests(unittest.TestCase):
    def test_manifest_is_parseable_and_complete(self):
        manifest = load_json(ENGINE_DIR / "baselines" / "v1" / "manifest.json")
        self.assertEqual(manifest["baseline_id"], "liminal-v1.1-phase0")
        self.assertEqual(
            manifest["architecture"]["deviation_threshold"],
            {"operator": ">=", "value": 0.3},
        )

        entries = manifest["files"]
        self.assertEqual(len(entries), 6)
        for entry in entries:
            self.assertRegex(entry["sha256"], r"^[0-9a-f]{64}$")
            baseline_path = PROJECT_ROOT / entry["path"]

            if not baseline_path.is_file():
                self.assertEqual(
                    entry.get("source_status"),
                    "user_owned_untracked_at_freeze",
                    msg=f"undeclared missing baseline file: {baseline_path}",
                )
                continue

            actual_sha256 = hashlib.sha256(baseline_path.read_bytes()).hexdigest()
            self.assertEqual(actual_sha256, entry["sha256"], msg=baseline_path)


if __name__ == "__main__":
    unittest.main()
