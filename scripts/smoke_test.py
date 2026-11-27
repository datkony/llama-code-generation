#!/usr/bin/env python3
"""End-to-end smoke test: prompt -> generation -> extract -> sandbox -> test.

Dùng ``--offline`` để kiểm tra pipeline khi chưa có token/GPU.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.evaluator import evaluate  # noqa: E402
from src.generator import GenerationResult, generate_code  # noqa: E402
from src.logging_utils import append_jsonl, load_config  # noqa: E402
from src.model_loader import decoding_from_config, load_model  # noqa: E402
from src.prompt_builder import build_messages  # noqa: E402


def load_tasks(path: str | Path) -> list[dict]:
    with Path(path).open("r", encoding="utf-8") as fh:
        return [json.loads(line) for line in fh if line.strip()]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default=None)
    parser.add_argument("--offline", action="store_true", help="dùng reference_code làm output giả")
    parser.add_argument("--backend", choices=["auto", "endpoint", "local"], default=None)
    parser.add_argument("--task", default=None, help="task_id; mặc định lấy bài đầu tiên")
    parser.add_argument("--variant", default="B", choices=["A", "B"])
    parser.add_argument("--log", action="store_true", help="ghi vào results/raw/smoke_test.jsonl")
    args = parser.parse_args()

    config = load_config(args.config)
    tasks = load_tasks(ROOT / config["dataset"]["path"])
    task = next((t for t in tasks if t["task_id"] == args.task), tasks[0])
    decoding = decoding_from_config(config)

    latency = 0.0
    n_new_tokens = None
    if args.offline:
        text = "```python\n" + task["reference_code"] + "\n```"
        info = {"backend": "offline-fixture", "model_id": "reference_code", "provider": None}
    else:
        try:
            model, info = load_model(config, backend_override=args.backend)
        except (RuntimeError, ValueError) as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            return 2
        messages = build_messages(task, args.variant)
        result: GenerationResult = generate_code(model, messages, decoding)
        text = result.text
        latency = result.latency_s
        n_new_tokens = result.n_new_tokens
        info = {**info, **result.info}

    from src.code_extractor import extract_code

    code = extract_code(text)
    score = evaluate(code, task, config)

    record = {
        "task_id": task["task_id"],
        "split": task.get("split"),
        "prompt_variant": args.variant,
        "model_id": info.get("model_id"),
        "revision": config["model"].get("revision"),
        "backend": info.get("backend"),
        "provider": info.get("provider"),
        "decoding_config": vars(decoding),
        "latency_s": latency,
        "n_new_tokens": n_new_tokens,
        "syntax_valid": score["syntax_valid"],
        "test_passed": score["test_passed"],
        "error_type": score["error_type"],
        "exec_seconds": score["exec_seconds"],
        "stderr": score["stderr"],
    }
    if args.log:
        append_jsonl(ROOT / "results" / "raw" / "smoke_test.jsonl", record)

    print(json.dumps({**record, "generated_code": code}, ensure_ascii=False, indent=2))
    return 0 if record["syntax_valid"] and record["test_passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
