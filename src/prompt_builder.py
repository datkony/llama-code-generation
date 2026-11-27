"""Build prompts for Prompt A (direct) and Prompt B (structured).

No third-party dependency. Templates can be overridden in ``prompts/``.
"""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

DEFAULT_A = """Write a Python function that solves the task below.
Return only Python source code. Do not include explanations or tests.

Task: {task_description}
Function name: {entry_point}
"""

DEFAULT_B = """You are a precise Python assistant. Follow the specification exactly.

Language: Python 3
Task: {task_description}
Function signature: {entry_point}

Requirements:
- Implement only the requested function.
- Honour the input/output contract and the stated constraints.
- Handle the listed edge cases.
- Do not print, read files, use the network, or call APIs.
- Return exactly ONE fenced Python code block and nothing else.
{examples_section}
Output format:
```python
# your implementation here
```
"""


def _load_template(variant: str) -> str:
    path = ROOT / "prompts" / ("direct.txt" if variant.upper() == "A" else "structured.txt")
    if path.exists():
        return path.read_text(encoding="utf-8")
    return DEFAULT_A if variant.upper() == "A" else DEFAULT_B


def _render(template: str, values: dict[str, str]) -> str:
    """Replace {key} placeholders without using str.format (code braces are safe)."""
    for key, value in values.items():
        template = template.replace("{" + key + "}", value)
    return template


def build_messages(task: dict, variant: str = "B") -> list[dict[str, str]]:
    """Return chat messages for a task record from ``data/tasks.jsonl``."""
    variant = variant.upper()
    if variant not in {"A", "B"}:
        raise ValueError("variant must be 'A' or 'B'")

    description = task.get("prompt") or task.get("description") or ""
    entry_point = task.get("entry_point") or "solution"
    examples = task.get("examples") or []
    examples_section = ""
    if examples:
        lines = "\n".join(f"- {item}" for item in examples)
        examples_section = f"\nExamples:\n{lines}\n"

    template = _load_template(variant)
    rendered = _render(
        template,
        {
            "task_description": description.strip(),
            "entry_point": entry_point,
            "examples_section": examples_section,
        },
    ).strip()

    if variant == "A":
        return [{"role": "user", "content": rendered}]

    system = (
        "You write correct, minimal Python code. Never reveal hidden tests. "
        "Answer with one fenced Python code block only."
    )
    return [{"role": "system", "content": system}, {"role": "user", "content": rendered}]
