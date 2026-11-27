#!/usr/bin/env python3
"""Run Prompt A vs Prompt B on the fixed task list and write JSONL + summary."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.code_extractor import extract_code  # noqa: E402
from src.evaluator import evaluate  # noqa: E402
from src.generator import GenerationResult, generate_code  # noqa: E402
from src.logging_utils import append_jsonl, load_config, summarize, write_json  # noqa: E402
from src.model_loader import decoding_from_config, load_model  # noqa: E402
from src.prompt_builder import build_messages  # noqa: E402


def load_tasks(path: str | Path) -> list[dict]:
    with Path(path).open("r", encoding="utf-8") as fh:
        return [json.loads(line) for line in fh if line.strip()]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default=None)
    parser.add_argument("--variants", default="A,B")
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--split", default=None, help="ghi đè split trong config")
    parser.add_argument("--all-tasks", action="store_true", help="dùng cả tập tune + report")
    parser.add_argument("--offline", action="store_true", help="dùng reference_code làm output giả")
    parser.add_argument("--backend", choices=["auto", "endpoint", "local"], default=None)
    args = parser.parse_args()

    config = load_config(args.config)
    tasks = load_tasks(ROOT / config["dataset"]["path"])
    split = args.split or config["dataset"].get("report_split")
    if split and not args.all_tasks:
        chosen = [t for t in tasks if t.get("split") == split]
    else:
        chosen = list(tasks)
    if args.limit:
        chosen = chosen[: args.limit]
    if not chosen:
        print("Không có task nào để chạy.", file=sys.stderr)
        return 1

    variants = [v.strip().upper() for v in args.variants.split(",") if v.strip()]
    decoding = decoding_from_config(config)
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    if args.offline:
        run_id += "_offline"
    raw_path = ROOT / config["output"]["raw"] / f"benchmark_{run_id}.jsonl"
    summary_path = ROOT / config["output"]["summary"] / f"benchmark_{run_id}.json"

    model = None
    model_info = {"backend": "offline-fixture", "model_id": "reference_code", "provider": None}
    if not args.offline:
        try:
            model, model_info = load_model(config, backend_override=args.backend)
        except (RuntimeError, ValueError) as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            return 2

    records: list[dict] = []
    for variant in variants:
        for task in chosen:
            latency = 0.0
            n_new_tokens = None
            if args.offline:
                text = "```python\n" + task["reference_code"] + "\n```"
            else:
                messages = build_messages(task, variant)
                try:
                    result: GenerationResult = generate_code(model, messages, decoding)
                    text = result.text
                    latency = result.latency_s
                    n_new_tokens = result.n_new_tokens
                except Exception as exc:  # keep the run going, log the failure
                    text = ""
                    score = {
                        "syntax_valid": False,
                        "test_passed": False,
                        "error_type": "generation_error",
                        "exec_seconds": 0.0,
                        "stderr": str(exc)[:2000],
                        "syntax_message": str(exc)[:500],
                    }
                    records.append(_record(task, variant, model_info, config, decoding, score, latency, n_new_tokens, text))
                    continue

            score = evaluate(extract_code(text), task, config)
            records.append(_record(task, variant, model_info, config, decoding, score, latency, n_new_tokens, text))

    for row in records:
        append_jsonl(raw_path, row)
    summary = {
        "run_id": run_id,
        "model": model_info,
        "model_revision": config["model"].get("revision"),
        "decoding_config": vars(decoding),
        "dataset": {"path": config["dataset"]["path"], "split": split, "n_tasks": len(chosen)},
        "prompt_variants": variants,
        "offline": args.offline,
        **summarize(records),
    }
    write_json(summary_path, summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


def _record(task, variant, model_info, config, decoding, score, latency, n_new_tokens, text):
    return {
        "task_id": task["task_id"],
        "split": task.get("split"),
        "prompt_variant": variant,
        "model_id": model_info.get("model_id"),
        "revision": config["model"].get("revision"),
        "backend": model_info.get("backend"),
        "provider": model_info.get("provider"),
        "decoding_config": vars(decoding),
        "latency_s": latency,
        "n_new_tokens": n_new_tokens,
        "syntax_valid": score["syntax_valid"],
        "syntax_message": score.get("syntax_message"),
        "test_passed": score["test_passed"],
        "error_type": score["error_type"],
        "exec_seconds": score["exec_seconds"],
        "stderr": score["stderr"],
        "generation": text[:4000],
    }


if __name__ == "__main__":
    sys.exit(main())
