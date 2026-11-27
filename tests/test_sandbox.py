import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.sandbox import run_tests  # noqa: E402


class TestSandbox(unittest.TestCase):
    def test_passing_code(self):
        result = run_tests(
            "def add(a, b):\n    return a + b\n",
            "assert add(1, 2) == 3\n",
            timeout_s=5,
        )
        self.assertTrue(result.passed, result.stderr)
        self.assertTrue(result.syntax_ok)

    def test_failing_assertion(self):
        result = run_tests(
            "def add(a, b):\n    return a - b\n",
            "assert add(1, 2) == 3\n",
            timeout_s=5,
        )
        self.assertFalse(result.passed)
        self.assertEqual(result.error_type, "assertion")

    def test_syntax_error_is_caught_before_execution(self):
        result = run_tests("def broken(:\n", "assert True\n", timeout_s=5)
        self.assertFalse(result.passed)
        self.assertEqual(result.error_type, "syntax")

    def test_infinite_loop_times_out(self):
        result = run_tests(
            "def spin():\n    while True:\n        pass\n",
            "spin()\n",
            timeout_s=1,
        )
        self.assertFalse(result.passed)
        self.assertEqual(result.error_type, "timeout")


if __name__ == "__main__":
    unittest.main()
