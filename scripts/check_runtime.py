#!/usr/bin/env python3
"""Probe the current runtime and recommend a model backend.

Chạy được cả trên máy local lẫn trong Colab/Kaggle. Không in giá trị token.
"""

from __future__ import annotations

import importlib.util
import json
import os
import platform
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOKEN_NAMES = ("HF_TOKEN", "HUGGINGFACEHUB_API_TOKEN", "HUGGING_FACE_HUB_TOKEN")


def module_version(name: str) -> str | None:
    try:
        from importlib.metadata import version

        return version(name)
    except Exception:
        return None


def colab_secret_present() -> bool:
    try:
        from google.colab import userdata  # type: ignore

        return bool(userdata.get("HF_TOKEN"))
    except Exception:
        return False


def main() -> int:
    # Windows console mặc định cp1252 không in được tiếng Việt.
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError):
            pass

    in_colab = False
    try:
        import google.colab  # type: ignore  # noqa: F401

        in_colab = True
    except Exception:
        pass

    torch_info = {"installed": False, "version": None, "cuda_available": False, "gpu": None, "vram_mib": 0}
    try:
        import torch

        torch_info["installed"] = True
        torch_info["version"] = torch.__version__
        torch_info["cuda_available"] = bool(torch.cuda.is_available())
        if torch_info["cuda_available"]:
            props = torch.cuda.get_device_properties(0)
            torch_info["gpu"] = props.name
            torch_info["vram_mib"] = int(props.total_memory / (1024 * 1024))
    except Exception:
        pass

    token_present = any(os.environ.get(name) for name in TOKEN_NAMES) or colab_secret_present()
    free_gb = round(shutil.disk_usage(ROOT).free / (1024**3), 2)

    packages = {
        name: module_version(name)
        for name in ("torch", "transformers", "accelerate", "huggingface_hub", "bitsandbytes", "gradio")
    }

    reasons: list[str] = []
    keep_8b = False
    backend = "local-small"

    if token_present:
        keep_8b = True
        backend = "endpoint"
        reasons.append("Có HF token: dùng Inference Providers, giữ được Llama 3.1 8B.")
    if torch_info["cuda_available"] and torch_info["vram_mib"] >= 8000:
        keep_8b = True
        if backend == "local-small":
            backend = "local-4bit"
        reasons.append(f"GPU {torch_info['vram_mib']} MiB: chạy được 8B ở 4-bit.")
    if torch_info["cuda_available"] and torch_info["vram_mib"] >= 16000:
        reasons.append("VRAM >=16 GB: có thể chạy 8B bf16.")
    if in_colab and not torch_info["cuda_available"]:
        reasons.append("Đang ở Colab nhưng chưa bật GPU: Runtime > Change runtime type > T4 GPU.")
    if not token_present and not torch_info["cuda_available"]:
        reasons.append("Không có token cũng không có CUDA: fallback Llama 3.2 3B/1B chạy CPU.")
    if free_gb < 10:
        reasons.append(f"Ổ trống chỉ {free_gb} GB: tránh tải nhiều checkpoint.")

    payload = {
        "runtime": "colab" if in_colab else ("kaggle" if Path("/kaggle").exists() else "localhost"),
        "python": platform.python_version(),
        "platform": platform.platform(),
        "torch": torch_info,
        "hf_token_present": token_present,
        "free_disk_gb": free_gb,
        "packages": packages,
        "recommended_backend": backend,
        "keep_8b": keep_8b,
        "reasons": reasons,
        "next_action": (
            "Chạy: python scripts/smoke_test.py --backend endpoint"
            if backend == "endpoint"
            else "Chạy: python scripts/smoke_test.py --offline để kiểm tra pipeline trước"
        ),
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
