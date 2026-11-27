"""Config loading, JSONL logging and metric aggregation (stdlib only)."""

from __future__ import annotations

import json
import statistics
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = ROOT / "configs" / "experiment.yaml"

RECORD_FIELDS = [
    "timestamp",
    "task_id",
    "split",
    "prompt_variant",
    "model_id",
    "revision",
    "backend",
    "provider",
    "decoding_config",
    "latency_s",
    "n_new_tokens",
    "syntax_valid",
    "test_passed",
    "error_type",
    "exec_seconds",
    "generation",
]


def load_config(path: str | Path | None = None) -> dict:
    """Load the JSON-formatted YAML config without requiring PyYAML."""
    cfg_path = Path(path) if path else DEFAULT_CONFIG
    with cfg_path.open("r", encoding="utf-8-sig") as fh:
        return json.load(fh)


def append_jsonl(path: str | Path, record: dict) -> None:
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    row = dict(record)
    row.setdefault("timestamp", datetime.now(timezone.utc).isoformat())
    with out.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(row, ensure_ascii=False) + "\n")


def write_json(path: str | Path, payload: dict) -> None:
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def summarize(records: list[dict]) -> dict:
    """Compute the metrics defined in the proposal for each prompt variant."""
    groups: dict[str, list[dict]] = {}
    for row in records:
        groups.setdefault(str(row.get("prompt_variant", "unknown")), []).append(row)

    summary: dict[str, dict] = {}
    for variant, rows in groups.items():
        n = len(rows)
        latencies = [float(r["latency_s"]) for r in rows if r.get("latency_s") is not None]
        error_counts: dict[str, int] = {}
        for row in rows:
            key = str(row.get("error_type") or "none")
            error_counts[key] = error_counts.get(key, 0) + 1
        summary[variant] = {
            "n_tasks": n,
            "pass_at_1": sum(bool(r.get("test_passed")) for r in rows) / n if n else 0.0,
            "syntax_validity": sum(bool(r.get("syntax_valid")) for r in rows) / n if n else 0.0,
            "latency_mean_s": round(statistics.fmean(latencies), 3) if latencies else None,
            "latency_median_s": round(statistics.median(latencies), 3) if latencies else None,
            "error_counts": error_counts,
        }
    return {"variants": summary, "n_records": len(records)}
