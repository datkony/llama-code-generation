"""Conservative extraction and syntax checking of model-generated code."""

from __future__ import annotations

import ast
import re

_FENCE = re.compile(r"```(?:python|py)?[ \t]*\r?\n(.*?)```", re.IGNORECASE | re.DOTALL)
_CODE_START = re.compile(r"^\s*(?:async\s+def|def|class|import|from|@)\b")


def extract_code(text: str) -> str:
    """Return the first fenced Python block, or a conservative fallback.

    The fallback only starts at a line that looks like Python and stops at the
    first line that looks like prose after code has begun.
    """
    if not text:
        return ""

    fenced = _FENCE.findall(text)
    if fenced:
        return fenced[0].strip() + "\n"

    lines = text.replace("\r\n", "\n").split("\n")
    start = None
    for i, line in enumerate(lines):
        if _CODE_START.match(line):
            start = i
            break
    if start is None:
        return ""

    kept: list[str] = []
    for line in lines[start:]:
        stripped = line.strip()
        if kept and stripped and not _CODE_START.match(line):
            # A prose-looking line after code: stop, unless it is indented or
            # clearly part of an expression.
            if not line.startswith((" ", "\t")) and re.match(r"^[A-ZÀ-Ỹ][^(){}[\]=:]*[.!?]$", stripped):
                break
        kept.append(line)

    return "\n".join(kept).strip() + "\n"


def check_syntax(code: str) -> tuple[bool, str]:
    """Return ``(ok, message)`` from ``ast.parse``."""
    if not code.strip():
        return False, "empty code"
    try:
        ast.parse(code)
    except SyntaxError as exc:
        return False, f"SyntaxError: {exc.msg} (line {exc.lineno})"
    return True, "ok"
