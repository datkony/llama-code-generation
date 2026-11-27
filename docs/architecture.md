# Kiến trúc demo

## 1. Luồng dữ liệu

```mermaid
flowchart LR
    U[Đề bài Python] --> PB[prompt_builder: A/B]
    PB --> ML[model_loader: endpoint hoặc local]
    ML --> G[generator: timing + decode]
    G --> CE[code_extractor: code block đầu tiên]
    CE --> SY[ast.parse]
    SY --> SB[sandbox: tiến trình con, timeout, env sạch]
    SB --> EV[evaluator: pass/fail + error_type]
    EV --> LOG[JSONL + summary]
    G --> UI[Gradio / CLI]
```

## 2. Vai trò module

| Module | Trách nhiệm | Không làm |
|---|---|---|
| `src/prompt_builder.py` | Tạo messages cho Prompt A/B từ `prompts/*.txt` | Không chứa đáp án/test |
| `src/model_loader.py` | Chọn backend `endpoint` (HF Inference Providers) hoặc `local` (Transformers/PyTorch), 4-bit khi có CUDA | Không log token |
| `src/generator.py` | Gọi model một lần, đo latency, trả text + metadata | Không tự sửa output |
| `src/code_extractor.py` | Trích code block đầu tiên, kiểm tra cú pháp | Không thực thi code |
| `src/sandbox.py` | Chạy solution + test trong tiến trình con, timeout, env sạch, giới hạn POSIX | Không chạy trong tiến trình chính |
| `src/evaluator.py` | Gom syntax/test/error_type | Không quyết định "đúng về mặt học thuật" thay test |
| `src/logging_utils.py` | Đọc config, ghi JSONL, tính pass@1/syntax validity/latency | Không chỉnh sửa bản ghi thô |
| `app/demo.py` | Gradio UI + CLI fallback | Không gọi thẳng `exec()` |
| `scripts/*` | Smoke test, benchmark, probe runtime | Không chứa secret |

## 3. Quyết định backend

Máy hiện tại: Windows 11, Python 3.13.5, PyTorch 2.10.0+cpu, CUDA unavailable, GPU 2 GB. Ổ C: chỉ ~26 GB trống nhưng workspace nằm trên ổ F: (~453 GB trống), nên **dung lượng không phải blocker**; blocker là CUDA/VRAM. Vì vậy:

1. **Ưu tiên endpoint** (`HF_TOKEN` + Inference Providers) để giữ `Llama-3.1-8B-Instruct`.
2. Nếu có Colab/Kaggle GPU (≥8 GB VRAM): dùng `local` + 4-bit, vẫn giữ 8B.
3. Nếu không có cả hai: fallback `Llama-3.2-3B/1B-Instruct`, ghi rõ model ID/revision và lý do.

Chạy `python scripts/check_runtime.py` để in ra quyết định hiện tại dưới dạng JSON.

## 4. Giới hạn an toàn cần ghi trong báo cáo

- Mã sinh ra chạy ở tiến trình con, thư mục tạm, env đã lọc, có timeout.
- Trên POSIX có thêm RLIMIT_CPU/AS/FSIZE/NPROC; trên Windows stdlib không giới hạn RAM được — phải nêu rõ.
- Network **không bị chặn hoàn toàn** bằng stdlib; không truyền secret vào env con.
- Sandbox là giảm thiểu rủi ro cho đồ án, không phải hardening production.
