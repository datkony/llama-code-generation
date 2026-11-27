"""Turn generated code into an evaluation record."""

from __future__ import annotations

from .code_extractor import check_syntax
from .sandbox import run_tests


def evaluate(code: str, task: dict, config: dict | None = None) -> dict:
    """Syntax-check and execute ``code`` against the task's public tests."""
    config = config or {}
    sandbox_cfg = config.get("sandbox", {})
    timeout_s = float(sandbox_cfg.get("timeout_s", 5))
    memory_mb = int(sandbox_cfg.get("memory_mb", 512))

    syntax_ok, syntax_message = check_syntax(code)
    if not syntax_ok:
        return {
            "syntax_valid": False,
            "syntax_message": syntax_message,
            "test_passed": False,
            "error_type": "syntax",
            "exec_seconds": 0.0,
            "stdout": "",
            "stderr": "",
        }

    result = run_tests(
        code,
        task.get("test_code", ""),
        timeout_s=timeout_s,
        memory_mb=memory_mb,
    )
    return {
        "syntax_valid": result.syntax_ok,
        "syntax_message": result.syntax_message,
        "test_passed": result.passed,
        "error_type": result.error_type,
        "exec_seconds": round(result.duration_s, 3),
        "stdout": result.stdout.strip()[-2000:],
        "stderr": result.stderr.strip()[-2000:],
    }
