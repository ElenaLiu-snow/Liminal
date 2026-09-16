import unittest

from engine.v2.demo_api import DemoInputError, DemoService, parse_origins
from engine.v2.pipeline import Pass1Pipeline
from engine.v2.tests.test_v2_phase3 import make_pass1_output


class FakeWorkflow:
    def run_pass1(self, request):
        pipeline = Pass1Pipeline()
        output = make_pass1_output(request)
        frozen = pipeline.freeze(output, request).to_dict()
        return {
            "frozen_pass1": frozen,
            "output": output,
        }

    def run_pass2(self, request):
        return {
            "output": {
                "user_display": {
                    "complete_reading": "A bounded Pass 2 reading.",
                    "takeaway_question": "What would distinguish the live possibilities?",
                }
            }
        }


class DemoServiceTests(unittest.TestCase):
    def setUp(self):
        self.service = DemoService(workflow_factory=FakeWorkflow)

    def test_pass1_returns_only_session_and_user_facing_reading(self):
        result = self.service.start_pass1(
            {
                "card": "major_07",
                "orientation": "upright",
                "transcript": "The figure appears prepared to move.",
            }
        )
        self.assertEqual(set(result), {"session_id", "reading"})
        self.assertNotIn("frozen_pass1", result)

    def test_pass2_uses_ephemeral_frozen_session(self):
        first = self.service.start_pass1(
            {
                "card": "major_07",
                "orientation": "upright",
                "transcript": "The figure appears prepared to move.",
            }
        )
        result = self.service.start_pass2(
            {
                "session_id": first["session_id"],
                "question": "Can I follow through on a plan?",
                "question_shift": "unchanged",
            }
        )
        self.assertEqual(set(result), {"reading", "takeaway_question"})

    def test_missing_session_is_rejected(self):
        with self.assertRaises(KeyError):
            self.service.start_pass2(
                {
                    "session_id": "expired",
                    "question": "Can I follow through on a plan?",
                    "question_shift": "unchanged",
                }
            )

    def test_empty_text_and_invalid_orientation_are_rejected(self):
        with self.assertRaises(DemoInputError):
            self.service.start_pass1(
                {"card": "major_07", "orientation": "sideways", "transcript": ""}
            )

    def test_origin_parser_uses_local_defaults_and_normalizes_custom_values(self):
        self.assertIn("http://127.0.0.1:5173", parse_origins(None))
        self.assertIn("http://127.0.0.1:3002", parse_origins(None))
        self.assertEqual(
            parse_origins("https://demo.example/, http://localhost:5173"),
            {"https://demo.example", "http://localhost:5173"},
        )


if __name__ == "__main__":
    unittest.main()
