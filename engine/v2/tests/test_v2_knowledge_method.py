import hashlib
import json
import unittest
from pathlib import Path

from engine.v2.build_knowledge import DECK_FILES, TRANSCRIPTION_PATH, build_knowledge
from engine.v2.contracts import TRANSFORMATION_TYPES
from engine.v2.knowledge import KNOWLEDGE_PATH, TarotKnowledgeBase, validate_knowledge_base
from engine.v2.methodology import METHOD_PATH, load_analysis_method
from engine.v2.traditional import TraditionalTarotLayer


V2_DIR = Path(__file__).resolve().parents[1]
ENGINE_DIR = V2_DIR.parent


class TarotKnowledgeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.knowledge = TarotKnowledgeBase()

    def test_generated_database_is_deterministic(self):
        committed = json.loads(KNOWLEDGE_PATH.read_text(encoding="utf-8"))
        self.assertEqual(committed, build_knowledge())
        validate_knowledge_base(committed)

    def test_all_legacy_cards_have_exactly_one_v2_record(self):
        legacy = []
        for filename in DECK_FILES:
            legacy.extend(json.loads((ENGINE_DIR / filename).read_text(encoding="utf-8")))
        self.assertEqual(len(self.knowledge.cards), 78)
        self.assertEqual(
            {card["id"] for card in legacy},
            {card["id"] for card in self.knowledge.cards},
        )

    def test_every_card_has_direct_primary_source_links_and_explicit_review_state(self):
        for card in self.knowledge.cards:
            with self.subTest(card=card["id"]):
                symbolism = card["source_links"]["waite_symbolism"]
                divinatory = card["source_links"]["waite_divinatory"]
                self.assertIn(card["name"].split()[-1].casefold(), symbolism["url"].casefold())
                self.assertTrue(divinatory["url"].startswith("https://"))
                self.assertEqual(set(card["review"].values()), {"pending"})

    def test_all_cards_have_machine_transcribed_waite_candidates(self):
        transcription = json.loads(TRANSCRIPTION_PATH.read_text(encoding="utf-8"))
        self.assertEqual(len(transcription["records"]), 78)
        self.assertEqual(
            {record["card_id"] for record in transcription["records"]},
            {card["id"] for card in self.knowledge.cards},
        )
        missing_reversals = []
        for card in self.knowledge.cards:
            with self.subTest(card=card["id"]):
                waite = card["waite_text"]
                self.assertTrue(waite["description"].strip())
                self.assertTrue(waite["upright"].strip())
                self.assertEqual(waite["review_status"], "machine_transcribed_unreviewed")
                if waite["reversed"] is None:
                    missing_reversals.append(card["id"])
        self.assertEqual(missing_reversals, ["cups_02"])

    def test_transcription_samples_preserve_source_distinctions(self):
        queen = self.knowledge.get_card("Queen of Cups")["waite_text"]
        wheel = self.knowledge.get_card("Wheel of Fortune")["waite_text"]
        self.assertIn("she sees, but she also acts", queen["description"])
        self.assertIn("stability amidst movement", wheel["description"])
        self.assertIn("Destiny, fortune", wheel["upright"])

    def test_knowledge_database_contains_no_psychological_presets(self):
        serialized = KNOWLEDGE_PATH.read_text(encoding="utf-8")
        for forbidden in (
            "jungian_mapping",
            "complex_signals",
            "emotional_tone",
            "developmental_origin",
            "clinical_diagnosis",
        ):
            self.assertNotIn(forbidden, serialized)

    def test_runtime_payload_stays_on_accepted_provisional_baseline(self):
        layer = TraditionalTarotLayer()
        before_activation = layer.canonical("Wheel of Fortune", "upright")
        shadow_record = layer.knowledge_record("Wheel of Fortune")
        self.assertEqual(before_activation["source_status"], "provisional_v1_dataset")
        self.assertNotIn("source_links", before_activation)
        self.assertEqual(shadow_record["id"], before_activation["card_id"])
        self.assertEqual(
            shadow_record["modern_interpretation"]["upright"],
            before_activation["stable_meaning"],
        )


class AnalysisMethodIsolationTests(unittest.TestCase):
    def test_method_taxonomy_matches_runtime_contract(self):
        method = load_analysis_method()
        self.assertEqual(set(method["transformation_taxonomy"]), TRANSFORMATION_TYPES)

    def test_method_is_not_implicitly_consumed_by_prompts(self):
        method = load_analysis_method()
        self.assertEqual(method["integration_status"], "shadow_only_not_prompt_input")
        self.assertEqual(method["change_control"]["prompt_consumption"], "disabled")
        for prompt in (V2_DIR / "prompts").glob("*.txt"):
            self.assertNotIn(str(METHOD_PATH), prompt.read_text(encoding="utf-8"))

    def test_human_approved_prompt_files_match_lock(self):
        manifest = json.loads((V2_DIR / "prompts" / "manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["status"], "human_approved_revision_candidate")
        for filename, expected in manifest["files"].items():
            digest = hashlib.sha256((V2_DIR / "prompts" / filename).read_bytes()).hexdigest()
            self.assertEqual(digest, expected, filename)

    def test_method_forbids_trait_and_origin_from_one_session(self):
        method = load_analysis_method()
        unsupported = next(
            item for item in method["epistemic_ladder"]
            if item["level"] == "unsupported_single_session"
        )
        self.assertEqual(unsupported["allowed_confidence"], [])
        self.assertIn("stable trait", unsupported["claim_scope"])
        self.assertIn("developmental origin", unsupported["claim_scope"])

    def test_method_version_contains_research_and_safety_boundaries(self):
        method = load_analysis_method()
        self.assertEqual(method["method_version"], "0.2.0")
        self.assertIn("source_registry", method["research_basis"])
        self.assertIn("not a psychological test", method["product_safety_boundary"]["positioning"])


if __name__ == "__main__":
    unittest.main()
