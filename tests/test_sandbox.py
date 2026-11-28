import os
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.sandbox import _limits, run_tests  # noqa: E402


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

    def test_blocked_import(self):
        result = run_tests(
            "import socket\n\ndef identity(x):\n    return x\n",
            "assert identity(1) == 1\n",
            timeout_s=5,
        )
        self.assertFalse(result.passed)
        self.assertEqual(result.error_type, "import")
        self.assertIn("blocked import", result.stderr)

    def test_file_access_outside_workdir_is_blocked(self):
        with tempfile.TemporaryDirectory(prefix="llama_sandbox_outside_") as outside:
            secret = Path(outside) / "secret.txt"
            secret.write_text("SHOULD_NOT_READ", encoding="utf-8")
            solution = (
                "def read_secret(path):\n"
                "    with open(path, encoding='utf-8') as fh:\n"
                "        return fh.read()\n"
            )
            result = run_tests(
                solution,
                f"assert read_secret({str(secret)!r}) == 'SHOULD_NOT_READ'\n",
                timeout_s=5,
            )
        self.assertFalse(result.passed)
        self.assertIn("PermissionError", result.stderr)

    def test_network_import_is_blocked(self):
        result = run_tests(
            "def fetch():\n"
            "    import urllib.request\n"
            "    return urllib.request.urlopen('http://example.com').status\n",
            "assert fetch() == 200\n",
            timeout_s=5,
        )
        self.assertFalse(result.passed)
        self.assertIn("blocked import", result.stderr)

    def test_subprocess_import_is_blocked(self):
        result = run_tests(
            "import subprocess\n\ndef run():\n    return subprocess.run(['echo', 'hi'])\n",
            "assert run().returncode == 0\n",
            timeout_s=5,
        )
        self.assertFalse(result.passed)
        self.assertEqual(result.error_type, "import")

    def test_process_creation_via_os_system_is_blocked(self):
        result = run_tests(
            "import os\n\ndef run():\n    return os.system('echo hi')\n",
            "assert run() == 0\n",
            timeout_s=5,
        )
        self.assertFalse(result.passed)
        self.assertIn("PermissionError", result.stderr)

    def test_memory_limits_configured_on_posix(self):
        # Chỉ kiểm tra cấu hình giới hạn; không cấp phát bộ nhớ lớn trong test.
        limits = _limits(512, 6)
        if os.name == "posix":
            self.assertTrue(callable(limits))
        else:
            self.assertIsNone(limits)


if __name__ == "__main__":
    unittest.main()
