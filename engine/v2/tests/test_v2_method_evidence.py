import unittest

from engine.v2.methodology import load_analysis_method, load_method_evidence


class MethodEvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.method = load_analysis_method()
        cls.registry, cls.evidence_map = load_method_evidence()
        cls.sources = {source["id"]: source for source in cls.registry["sources"]}
        cls.claims = {claim["id"]: claim for claim in cls.evidence_map["claims"]}

    def test_method_references_every_evidence_claim_exactly_once(self):
        basis = self.method["research_basis"]
        referenced = (
            basis["interpretive_theory_claim_ids"]
            + basis["validity_and_safety_claim_ids"]
            + basis["method_claim_ids"]
        )
        self.assertEqual(len(referenced), len(set(referenced)))
        self.assertEqual(set(referenced), set(self.claims))

    def test_every_source_has_a_non_support_boundary(self):
        for source in self.sources.values():
            with self.subTest(source=source["id"]):
                self.assertTrue(source["does_not_support"])
                self.assertTrue(source["verification"].endswith("2026-09-11"))

    def test_empirical_risk_claim_is_not_supported_only_by_jungian_theory(self):
        for claim_id in (
            "felt_personal_accuracy_is_not_sufficient_validation",
            "symbolic_interpretation_is_not_clinical_measurement",
            "single_session_inference_requires_a_conservative_scope",
        ):
            source_types = {
                self.sources[source_id]["source_type"]
                for source_id in self.claims[claim_id]["source_ids"]
            }
            self.assertTrue(
                any("peer_reviewed" in source_type for source_type in source_types),
                claim_id,
            )

    def test_projective_technique_disagreement_is_preserved(self):
        claim = self.claims["symbolic_interpretation_is_not_clinical_measurement"]
        self.assertEqual(claim["basis_type"], "contested_empirical_review")
        self.assertIn("lilienfeld_wood_garb_2000", claim["source_ids"])
        self.assertIn("hibbard_2003_projective_critique", claim["source_ids"])

    def test_reporting_guidance_is_not_treated_as_validity_proof(self):
        claim = self.claims["reporting_checklists_do_not_certify_methodological_truth"]
        self.assertIn("not be used as a score", claim["claim"])
        self.assertIn("validity scores", claim["product_rule"])

    def test_evidence_activation_remains_disabled(self):
        self.assertEqual(
            self.evidence_map["integration_status"],
            "shadow_only_not_prompt_input",
        )
        self.assertEqual(self.evidence_map["activation_gate"]["status"], "disabled")
        self.assertEqual(self.method["change_control"]["prompt_consumption"], "disabled")


if __name__ == "__main__":
    unittest.main()
