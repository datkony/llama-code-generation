import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.prompt_builder import build_messages  # noqa: E402


class TestPromptBuilder(unittest.TestCase):
    task = {
        "prompt": "Return True if n is even.",
        "entry_point": "is_even",
        "examples": ["is_even(4) -> True"],
    }

    def test_variant_a_has_single_user_message(self):
        messages = build_messages(self.task, "A")
        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0]["role"], "user")
        self.assertIn("is_even", messages[0]["content"])

    def test_variant_b_is_structured(self):
        messages = build_messages(self.task, "B")
        self.assertEqual([m["role"] for m in messages], ["system", "user"])
        user = messages[1]["content"]
        self.assertIn("Function signature", user)
        self.assertIn("Examples", user)

    def test_bad_variant_raises(self):
        with self.assertRaises(ValueError):
            build_messages(self.task, "C")


if __name__ == "__main__":
    unittest.main()
