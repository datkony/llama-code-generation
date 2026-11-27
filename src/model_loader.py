"""Model/inference backend loader.

Two backends are supported:

* ``endpoint`` — Hugging Face Inference Providers via ``InferenceClient``.
  Recommended while the local machine has no CUDA runtime.
* ``local`` — Transformers + PyTorch, optionally 4-bit on CUDA.

Dependencies are imported lazily so the repository can be cloned and tested
without installing model libraries first.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field

TOKEN_ENV_NAMES = (
    "HF_TOKEN",
    "HUGGINGFACEHUB_API_TOKEN",
    "HUGGING_FACE_HUB_TOKEN",
)


@dataclass
class DecodingConfig:
    temperature: float = 0.0
    top_p: float = 1.0
    max_new_tokens: int = 256
    do_sample: bool = False
    seed: int | None = None


@dataclass
class GenerationOutput:
    text: str
    info: dict = field(default_factory=dict)


def resolve_token() -> str | None:
    """Read a token from environment variables without printing its value.

    `google.colab.userdata` is intentionally NOT used: it times out when the
    notebook runs through the VS Code Colab extension. The notebook sets
    ``HF_TOKEN`` in the kernel environment instead.
    """
    for name in TOKEN_ENV_NAMES:
        value = os.environ.get(name)
        if value:
            return value
    return None


def decoding_from_config(config: dict) -> DecodingConfig:
    raw = config.get("decoding", {})
    return DecodingConfig(
        temperature=float(raw.get("temperature", 0.0)),
        top_p=float(raw.get("top_p", 1.0)),
        max_new_tokens=int(raw.get("max_new_tokens", 256)),
        do_sample=bool(raw.get("do_sample", False)),
        seed=raw.get("seed"),
    )


class EndpointModel:
    """Hugging Face Inference Providers backend."""

    backend = "endpoint"

    def __init__(self, model_id: str, provider: str | None = None, token: str | None = None):
        try:
            from huggingface_hub import InferenceClient
        except ImportError as exc:  # pragma: no cover - depends on environment
            raise RuntimeError(
                "huggingface_hub chưa được cài. Chạy: pip install -r requirements.txt"
            ) from exc

        self.model_id = model_id
        # `provider=None` makes huggingface_hub auto-pick a provider. For this
        # checkpoint auto-picking can raise StopIteration (empty provider map),
        # so default to an explicitly live provider and allow an override.
        self.provider = provider or os.environ.get("INFERENCE_PROVIDER") or "groq"
        self.token = token or resolve_token()
        if not self.token:
            raise RuntimeError(
                "Không tìm thấy HF_TOKEN. Đặt biến môi trường HF_TOKEN trước khi dùng backend endpoint."
            )

        try:
            self.client = InferenceClient(
                model=model_id, token=self.token, provider=self.provider
            )
        except TypeError:
            # Older huggingface_hub versions do not accept provider in constructor.
            self.client = InferenceClient(model=model_id, token=self.token)

    def generate(self, messages: list[dict], decoding: DecodingConfig) -> GenerationOutput:
        kwargs = {
            "max_tokens": decoding.max_new_tokens,
            "temperature": decoding.temperature,
            "top_p": decoding.top_p,
        }
        try:
            response = self.client.chat.completions.create(
                model=self.model_id, messages=messages, **kwargs
            )
        except Exception as exc:
            raise RuntimeError(
                f"Endpoint thất bại với provider='{self.provider}': {exc}. "
                "Thử INFERENCE_PROVIDER=deepinfra hoặc kiểm tra credit/license HF."
            ) from exc
        text = response.choices[0].message.content or ""
        info = {"backend": self.backend, "model_id": self.model_id, "provider": self.provider}
        usage = getattr(response, "usage", None)
        if usage is not None:
            info["usage"] = {
                "prompt_tokens": getattr(usage, "prompt_tokens", None),
                "completion_tokens": getattr(usage, "completion_tokens", None),
            }
        return GenerationOutput(text=text, info=info)


class LocalTransformersModel:
    """Transformers/PyTorch backend for Colab, Kaggle or a CUDA machine."""

    backend = "local"

    def __init__(self, model_id: str, config: dict | None = None):
        try:
            import torch
            from transformers import AutoModelForCausalLM, AutoTokenizer
        except ImportError as exc:  # pragma: no cover - depends on environment
            raise RuntimeError(
                "torch/transformers chưa được cài. Chạy: pip install -r requirements.txt"
            ) from exc

        model_cfg = (config or {}).get("model", {})
        self.model_id = model_id
        self.token = resolve_token()
        self.torch = torch
        self.tokenizer = AutoTokenizer.from_pretrained(model_id, token=self.token)

        dtype_name = model_cfg.get("dtype", "bfloat16")
        dtype = getattr(torch, dtype_name, torch.float32)
        use_cuda = torch.cuda.is_available()
        # T4 (compute capability 7.5) has no native bfloat16. Fall back to fp16
        # so Colab's most common GPU does not fail or run in a bad dtype.
        if (
            dtype_name == "bfloat16"
            and use_cuda
            and torch.cuda.get_device_capability(0)[0] < 8
        ):
            dtype = torch.float16
        self.dtype = str(dtype).replace("torch.", "")
        load_kwargs: dict = {"torch_dtype": dtype}
        if model_cfg.get("load_in_4bit", False) and use_cuda:
            try:
                from transformers import BitsAndBytesConfig

                load_kwargs["quantization_config"] = BitsAndBytesConfig(
                    load_in_4bit=True,
                    bnb_4bit_quant_type="nf4",
                    bnb_4bit_compute_dtype=dtype,
                    bnb_4bit_use_double_quant=True,
                )
            except ImportError as exc:
                raise RuntimeError("load_in_4bit=true nhưng bitsandbytes chưa được cài") from exc

        try:
            self.model = AutoModelForCausalLM.from_pretrained(
                model_id, token=self.token, **load_kwargs
            )
            self.device = "cuda" if use_cuda else "cpu"
            self.model.to(self.device)
        except Exception as exc:  # pragma: no cover - environment dependent
            raise RuntimeError(f"Không nạp được model {model_id}: {exc}") from exc
        self.model.eval()

    def generate(self, messages: list[dict], decoding: DecodingConfig) -> GenerationOutput:
        inputs = self.tokenizer.apply_chat_template(
            messages, add_generation_prompt=True, return_tensors="pt"
        ).to(self.model.device)
        kwargs = {
            "max_new_tokens": decoding.max_new_tokens,
            "do_sample": decoding.do_sample,
            "pad_token_id": self.tokenizer.eos_token_id,
        }
        if decoding.do_sample:
            kwargs["temperature"] = decoding.temperature
            kwargs["top_p"] = decoding.top_p
        with self.torch.inference_mode():
            output = self.model.generate(inputs, **kwargs)
        new_tokens = output[0][inputs.shape[-1]:]
        text = self.tokenizer.decode(new_tokens, skip_special_tokens=True)
        info = {
            "backend": self.backend,
            "model_id": self.model_id,
            "device": str(self.model.device),
            "dtype": getattr(self, "dtype", None),
            "n_new_tokens": int(new_tokens.shape[-1]),
        }
        return GenerationOutput(text=text, info=info)


def load_model(config: dict | None = None, backend_override: str | None = None):
    """Return ``(model_handle, info)`` for the requested backend."""
    config = config or {}
    model_cfg = config.get("model", {})
    backend = (backend_override or os.environ.get("MODEL_BACKEND") or model_cfg.get("backend") or "auto").lower()
    model_id = os.environ.get("MODEL_ID") or model_cfg.get("model_id")
    if not model_id:
        raise RuntimeError("Chưa cấu hình model_id")

    if backend == "auto":
        # Inference Providers currently has no providerMapping for these
        # gated Llama checkpoints, so prefer local GPU when available.
        try:
            import torch

            has_gpu = bool(torch.cuda.is_available())
        except Exception:
            has_gpu = False
        backend = "local" if has_gpu else "endpoint"

    if backend == "endpoint":
        handle = EndpointModel(
            model_id,
            provider=model_cfg.get("provider"),
            token=resolve_token(),
        )
    elif backend == "local":
        handle = LocalTransformersModel(model_id, config)
    else:
        raise ValueError(f"Backend không hợp lệ: {backend}")

    return handle, {
        "backend": backend,
        "model_id": model_id,
        "revision": model_cfg.get("revision"),
        "provider": getattr(handle, "provider", None),
    }
