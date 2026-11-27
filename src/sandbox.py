"""Run generated Python code plus tests in a restricted child process.

Safety notes (important for the report):
- Generated code never runs in the main process.
- The child gets a scrubbed environment, an isolated temp directory, a timeout
  and, on POSIX, CPU/memory/process limits.
- On Windows there is no stdlib memory limit; this limitation must be stated in
  the report. Network access is NOT fully disabled by stdlib alone.
"""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

_SENTINEL = "__ALL_TESTS_PASSED__"

_RUNNER = """\
import sys
import traceback

sys.path.insert(0, ".")
from solution import *  # noqa: F401,F403

ns = dict(globals())
try:
    exec(compile(TEST_CODE, "<unit_tests>", "exec"), ns)
except BaseException:
    traceback.print_exc()
    sys.exit(1)
print(SENTINEL)
"""


@dataclass
class ExecutionResult:
    passed: bool
    syntax_ok: bool
    syntax_message: str
    stdout: str
    stderr: str
    duration_s: float
    error_type: str | None = None


def _clean_env() -> dict[str, str]:
    keep = {"PATH", "SYSTEMROOT", "TEMP", "TMP", "LANG", "LC_ALL"}
    env = {k: v for k, v in os.environ.items() if k in keep}
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONUTF8"] = "1"
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    return env


def _limits(memory_mb: int, cpu_s: int):
    if os.name != "posix":
        return None

    def apply() -> None:
        import resource

        resource.setrlimit(resource.RLIMIT_CPU, (cpu_s, cpu_s + 1))
        memory_bytes = memory_mb * 1024 * 1024
        resource.setrlimit(resource.RLIMIT_AS, (memory_bytes, memory_bytes))
        resource.setrlimit(resource.RLIMIT_FSIZE, (1024 * 1024, 1024 * 1024))
        try:
            resource.setrlimit(resource.RLIMIT_NPROC, (32, 32))
        except (ValueError, OSError):
            pass

    return apply


def run_tests(
    solution_code: str,
    test_code: str,
    timeout_s: float = 5.0,
    memory_mb: int = 512,
) -> ExecutionResult:
    """Compile then execute ``solution_code`` with ``test_code`` in a child."""
    from .code_extractor import check_syntax

    ok, message = check_syntax(solution_code)
    if not ok:
        return ExecutionResult(False, False, message, "", "", 0.0, "syntax")

    runner = _RUNNER.replace("TEST_CODE", repr(test_code)).replace("SENTINEL", repr(_SENTINEL))

    import time

    started = time.perf_counter()
    with tempfile.TemporaryDirectory(prefix="llama_sandbox_") as tmp:
        workdir = Path(tmp)
        (workdir / "solution.py").write_text(solution_code, encoding="utf-8")
        (workdir / "runner.py").write_text(runner, encoding="utf-8")

        kwargs = {
            "cwd": str(workdir),
            "env": _clean_env(),
            "stdin": subprocess.DEVNULL,
            "stdout": subprocess.PIPE,
            "stderr": subprocess.PIPE,
            "text": True,
            "timeout": timeout_s,
            "preexec_fn": _limits(memory_mb, max(1, int(timeout_s) + 1)),
        }
        if os.name == "nt":
            kwargs.pop("preexec_fn", None)
            kwargs["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP

        try:
            proc = subprocess.run([sys.executable, "-I", "runner.py"], **kwargs)
        except subprocess.TimeoutExpired as exc:
            duration = time.perf_counter() - started
            return ExecutionResult(
                False, True, message,
                (exc.stdout or "") if isinstance(exc.stdout, str) else "",
                (exc.stderr or "") if isinstance(exc.stderr, str) else "TIMEOUT",
                duration, "timeout",
            )
        except OSError as exc:
            duration = time.perf_counter() - started
            return ExecutionResult(False, True, message, "", str(exc), duration, "sandbox_error")

    duration = time.perf_counter() - started
    stdout = proc.stdout or ""
    stderr = proc.stderr or ""
    passed = proc.returncode == 0 and _SENTINEL in stdout
    if passed:
        error_type = None
    elif proc.returncode == 1 and "AssertionError" in stderr:
        error_type = "assertion"
    elif proc.returncode == 1 and ("ImportError" in stderr or "ModuleNotFoundError" in stderr):
        error_type = "import"
    elif proc.returncode == 1 and "NameError" in stderr:
        error_type = "name"
    else:
        error_type = "runtime"

    return ExecutionResult(passed, True, message, stdout, stderr, duration, error_type)
