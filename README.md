# Llama for Code Generation

Đồ án: **Mô hình Llama trong bài toán sinh mã nguồn** — sinh hàm Python từ mô tả tự nhiên, trích xuất mã, kiểm tra cú pháp và chạy unit test trong sandbox.

> Mốc nộp cuối cùng: **30/11/2026** (điều chỉnh từ 13/12). proposal gốc nằm trong thư mục `document/` (nội bộ, đã bị `.gitignore` chặn không push lên GitHub).

## 1. Trạng thái nhanh

- Pipeline đã chạy **thật trên GPU Colab (T4)** với `meta-llama/Llama-3.1-8B-Instruct`, backend `local` 4-bit. `run_id = 20261127T192206Z`, 70 bản ghi (35 bài × 2 prompt). Xem `results/README.md`.
- Máy local hiện tại: Windows 11, Python 3.13.5, `torch==2.10.0+cpu`, **CUDA unavailable**, GPU 2 GB. Ổ C: ~26 GB trống nhưng ổ F: (workspace) ~453 GB → **không chạy Llama 3.1 8B tại local do thiếu CUDA/VRAM, không phải do dung lượng**.
- Checkpoint đã chốt: `meta-llama/Llama-3.1-8B-Instruct` @ `0e9e39f249a16976918f6564b8830bc894c89659` (gated, cần chấp nhận license trên Hugging Face).
- HF Inference Providers **không có provider mapping** cho checkpoint này (`inferenceProviderMapping: {}`) → endpoint không dùng được. Runtime ngoài localhost đáp ứng (CUDA=true, VRAM đủ) nên **giữ 8B**, không fallback. Chế độ `--offline` chỉ validate pipeline, không báo cáo số liệu.

## 2. Cài đặt

```bash
python -m venv .venv
# Windows PowerShell:
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env      # rồi điền HF_TOKEN để tải checkpoint gated
```

Không bao giờ commit `.env` hay token.

## 3. Kiểm tra runtime

```bash
python scripts/check_runtime.py
```

Lệnh in JSON gồm: đang ở Colab/Kaggle hay local, CUDA/VRAM, token có present hay không, gói đã cài, backend được khuyến nghị.

### Nếu dùng Colab từ VS Code (extension `google.colab` đã cài)

1. Mở `scripts/runtime_probe.ipynb` trong VS Code.
2. `Select Kernel` → `Colab` → `Auto Connect` → đăng nhập Google, rồi bật **Runtime → Change runtime type → T4 GPU**.
3. Chạy lần lượt cell 1–8: cài dependency → clone/pull repo → probe CUDA → nhập HF token → smoke → benchmark A/B → unit test → đóng gói `results_export_<run_id>.zip`.
4. **Vì sao clone?** Kernel Colab chạy trên máy ảo của Google, không phải máy bạn; clone chỉ copy mã nguồn vào máy ảo đó.
5. HF token được nhập ở cell 4 và chỉ nằm trong biến môi trường của kernel. Extension Colab trên VS Code **không đọc được `google.colab.userdata`**, nên không dùng Secrets. Cell 8 tạo zip kết quả để bạn tải về; trước khi commit cần xóa output notebook.

## 4. Chạy pipeline

```bash
# Kiểm tra pipeline không cần model (dùng reference_code làm output giả)
python scripts/smoke_test.py --offline
python scripts/run_benchmark.py --offline --variants A,B

# Chạy thật trên Colab/Kaggle có GPU (đường được dùng cho số liệu báo cáo)
python scripts/smoke_test.py --backend local
python scripts/run_benchmark.py --backend local --variants A,B

# Giao diện demo
python app/demo.py
# hoặc không cần Gradio:
python app/demo.py --cli --offline
```

Kết quả: `results/raw/*.jsonl` (thô) và `results/summary/*.json` (pass@1, syntax validity, latency, error counts).

## 5. Cấu trúc

```text
configs/        experiment.yaml (JSON hợp lệ, load bằng stdlib)
data/           tasks.jsonl (40 bài: 5 tune + 35 report) + README
prompts/        direct.txt (A), structured.txt (B)
src/            model_loader, prompt_builder, generator, code_extractor,
                sandbox, evaluator, logging_utils
app/            demo.py (Gradio + CLI)
scripts/        check_runtime.py, smoke_test.py, run_benchmark.py, runtime_probe.ipynb
tests/          unittest (chạy được cả bằng pytest)
docs/           architecture.md, experiment_protocol.md, report_draft.md,
                model_architecture.md, generation_pipeline.md, model_comparison.md,
                dataset.md, metrics.md, baseline.md, sandbox.md
results/        raw/, summary/, README.md (nguồn gốc số liệu)
document/       tài liệu nội bộ — KHÔNG push GitHub
```

## 6. An toàn

- Mã do model sinh ra **không** chạy trong tiến trình chính; luôn qua `src/sandbox.py`.
- Tiến trình con dùng env đã lọc, thư mục tạm, timeout; trên POSIX có thêm RLIMIT CPU/RAM/process.
- Runner có import guard/audit hook (best-effort) chặn import mạng/tiến trình, tạo socket và đọc file ngoài miền cho phép; network **vẫn không bị cắt ở tầng OS**.
- Windows không giới hạn RAM được bằng stdlib → phải nêu giới hạn này trong báo cáo. Xem [docs/sandbox.md](docs/sandbox.md).
- Guard sandbox được bổ sung sau lượt đo `20261127T192206Z`; nếu chạy lại dùng `run_id` mới, không gộp số liệu.

## 7. Test

```bash
python -m unittest discover -s tests -v
```

Lần chạy gần nhất: **16 test, OK**.

## 8. Tài liệu kỹ thuật công khai

- [Kiến trúc Llama 3.1 8B](docs/model_architecture.md) · [Quy trình sinh mã](docs/generation_pipeline.md) · [So sánh Llama/Code Llama/Llama 4](docs/model_comparison.md)
- [Dataset](docs/dataset.md) · [Metric](docs/metrics.md) · [Baseline](docs/baseline.md) · [Sandbox](docs/sandbox.md)
- [Giao thức thí nghiệm](docs/experiment_protocol.md) · [Kiến trúc demo](docs/architecture.md) · [Bản nháp báo cáo](docs/report_draft.md)
