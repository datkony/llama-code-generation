"""Generation orchestration: messages -> model -> formatted output."""

from __future__ import annotations

import time
from dataclasses import dataclass

from .code_extractor import check_syntax, extract_code
from .model_loader import DecodingConfig, GenerationOutput


@dataclass
class GenerationResult:
    text: str
    code: str
    latency_s: float
    syntax_ok: bool
    syntax_message: str
    n_new_tokens: int | None
    info: dict


def generate_code(model, messages: list[dict], decoding: DecodingConfig) -> GenerationResult:
    """Call the model once and post-process its output."""
    started = time.perf_counter()
    output: GenerationOutput = model.generate(messages, decoding)
    latency = time.perf_counter() - started

    code = extract_code(output.text)
    syntax_ok, syntax_message = check_syntax(code)
    n_new = output.info.get("n_new_tokens")
    if n_new is None and isinstance(output.info.get("usage"), dict):
        n_new = output.info["usage"].get("completion_tokens")

    return GenerationResult(
        text=output.text,
        code=code,
        latency_s=round(latency, 3),
        syntax_ok=syntax_ok,
        syntax_message=syntax_message,
        n_new_tokens=n_new,
        info=output.info,
    )
