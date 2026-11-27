#!/usr/bin/env python3
"""Minimal code-generation demo (Gradio UI with CLI fallback).

Không thực thi mã sinh ra ở tiến trình chính: nút "Run tests" luôn gọi sandbox.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.code_extractor import extract_code  # noqa: E402
from src.evaluator import evaluate  # noqa: E402
from src.generator import generate_code  # noqa: E402
from src.logging_utils import load_config  # noqa: E402
from src.model_loader import DecodingConfig, load_model  # noqa: E402
from src.prompt_builder import build_messages  # noqa: E402

DEFAULT_TESTS = "assert solution() == 42\n"
DEFAULT_REFERENCE = "def solution():\n    return 42\n"


def run_once(
    description: str,
    entry_point: str,
    variant: str,
    temperature: float,
    top_p: float,
    max_new_tokens: int,
    offline: bool,
    reference_code: str,
    config: dict,
) -> dict:
    task = {
        "task_id": "demo",
        "prompt": description,
        "entry_point": entry_point or "solution",
        "examples": [],
    }
    decoding = DecodingConfig(
        temperature=temperature, top_p=top_p, max_new_tokens=max_new_tokens, do_sample=temperature > 0
    )

    if offline:
        text = "```python\n" + (reference_code or DEFAULT_REFERENCE) + "\n```"
        info = {"backend": "offline-fixture", "model_id": "reference_code"}
        latency = 0.0
    else:
        model, info = load_model(config)
        messages = build_messages(task, variant)
        result = generate_code(model, messages, decoding)
        text = result.text
        info = {**info, **result.info}
        latency = result.latency_s

    code = extract_code(text)
    return {
        "code": code,
        "info": {**info, "variant": variant, "latency_s": latency, "temperature": temperature, "top_p": top_p},
    }


def build_ui() -> None:
    try:
        import gradio as gr
    except ImportError:
        print("Gradio chưa cài: chạy `pip install -r requirements.txt` hoặc dùng `--cli`.")
        return

    config = load_config()

    def on_generate(description, entry, variant, temperature, top_p, max_tokens, offline, reference):
        if not description.strip():
            return "", "Lỗi: mô tả bài toán đang trống.", ""
        try:
            out = run_once(
                description, entry, variant, temperature, top_p, int(max_tokens),
                offline, reference, config,
            )
            return out["code"], json.dumps(out["info"], ensure_ascii=False, indent=2), out["code"]
        except Exception as exc:
            return "", f"Lỗi: {exc}", ""

    def on_test(code, tests, entry):
        if not code.strip():
            return "Chưa có mã để test."
        task = {"test_code": tests or DEFAULT_TESTS, "entry_point": entry or "solution"}
        score = evaluate(code, task, config)
        return json.dumps(score, ensure_ascii=False, indent=2)

    with gr.Blocks(title="Llama Code Generation Demo") as demo:
        gr.Markdown("# Llama sinh mã Python + kiểm thử trong sandbox\nMã sinh ra **không** chạy trong tiến trình chính.")
        description = gr.Textbox(label="Mô tả bài toán", lines=3, value="Return 42 from a function named solution.")
        entry = gr.Textbox(label="Tên hàm (entry point)", value="solution")
        tests = gr.Textbox(label="Unit tests (assert ...)", lines=3, value=DEFAULT_TESTS)
        with gr.Row():
            variant = gr.Dropdown(["A", "B"], value="B", label="Prompt")
            temperature = gr.Slider(0.0, 1.0, value=0.0, step=0.1, label="Temperature")
            top_p = gr.Slider(0.1, 1.0, value=1.0, step=0.1, label="Top-p")
            max_tokens = gr.Slider(32, 512, value=256, step=32, label="Max new tokens")
        offline = gr.Checkbox(value=False, label="Offline fixture (không gọi model)")
        reference = gr.Textbox(label="Reference code (chỉ dùng khi Offline)", lines=3, value=DEFAULT_REFERENCE)
        generate_btn = gr.Button("Sinh mã")
        code_out = gr.Code(label="Mã được sinh", language="python", lines=12)
        info_out = gr.Textbox(label="Thông tin cấu hình", lines=6)
        state = gr.State("")
        test_btn = gr.Button("Chạy test trong sandbox")
        test_out = gr.Textbox(label="Kết quả test", lines=8)

        generate_btn.click(
            on_generate,
            [description, entry, variant, temperature, top_p, max_tokens, offline, reference],
            [code_out, info_out, state],
        )
        test_btn.click(on_test, [state, tests, entry], [test_out])

    demo.launch()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cli", action="store_true", help="chạy không cần Gradio")
    parser.add_argument("--description", default="Return 42 from a function named solution.")
    parser.add_argument("--entry", default="solution")
    parser.add_argument("--tests", default=DEFAULT_TESTS)
    parser.add_argument("--variant", default="B", choices=["A", "B"])
    parser.add_argument("--offline", action="store_true")
    parser.add_argument("--reference", default=DEFAULT_REFERENCE)
    parser.add_argument("--temperature", type=float, default=0.0)
    parser.add_argument("--top-p", type=float, default=1.0)
    parser.add_argument("--max-tokens", type=int, default=256)
    args = parser.parse_args()

    if args.cli:
        out = run_once(
            args.description, args.entry, args.variant, args.temperature, args.top_p,
            args.max_tokens, args.offline, args.reference, load_config(),
        )
        score = evaluate(out["code"], {"test_code": args.tests, "entry_point": args.entry}, load_config())
        print(json.dumps({**out, "evaluation": score}, ensure_ascii=False, indent=2))
        return 0

    build_ui()
    return 0


if __name__ == "__main__":
    sys.exit(main())
