import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.code_extractor import check_syntax, extract_code  # noqa: E402


class TestCodeExtractor(unittest.TestCase):
    def test_prefers_first_fenced_block(self):
        text = "Here you go:\n```python\ndef f():\n    return 1\n```\nExplanation..."
        self.assertEqual(extract_code(text), "def f():\n    return 1\n")

    def test_fallback_starts_at_code(self):
        text = "Sure!\ndef f():\n    return 2\n"
        self.assertTrue(extract_code(text).startswith("def f()"))

    def test_syntax_check(self):
        ok, _ = check_syntax("def f():\n    return 1\n")
        self.assertTrue(ok)
        ok, message = check_syntax("def f(:\n")
        self.assertFalse(ok)
        self.assertIn("SyntaxError", message)


if __name__ == "__main__":
    unittest.main()
