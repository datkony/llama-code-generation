# Llama for Code Generation

Đồ án: **Mô hình Llama trong bài toán sinh mã nguồn** — sinh hàm Python từ mô tả tự nhiên, trích xuất mã, kiểm tra cú pháp và chạy unit test trong sandbox.

> Mốc nộp báo cáo rút gọn: **01/12/2026**. proposal gốc nằm trong thư mục `document/` (nội bộ, đã bị `.gitignore` chặn không push lên GitHub).

## 1. Trạng thái nhanh

- Khung code đã chạy được pipeline **end-to-end ở chế độ offline** (không cần token/GPU).
- Máy local hiện tại: Windows 11, Python 3.13.5, `torch==2.10.0+cpu`, **CUDA unavailable**, GPU 2 GB. Ổ C: ~26 GB trống nhưng ổ F: (workspace) ~453 GB → **không chạy Llama 3.1 8B tại local do thiếu CUDA/VRAM, không phải do dung lượng**.
- Checkpoint tham chiếu: `meta-llama/Llama-3.1-8B-Instruct` @ `0e9e39f249a16976918f6564b8830bc894c89659` (gated, cần chấp nhận license trên Hugging Face).
- Chiến lược: thử runtime ngoài localhost (Colab/Kaggle/HF endpoint). Nếu đáp ứng → giữ 8B; nếu không → fallback `Llama-3.2-3B/1B-Instruct` và ghi rõ lý do.

## 2. Cài đặt

```bash
python -m venv .venv
# Windows PowerShell:
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env      # rồi điền HF_TOKEN nếu dùng endpoint
```

Không bao giờ commit `.env` hay token.

## 3. Kiểm tra runtime

```bash
python scripts/check_runtime.py
```

Lệnh in JSON gồm: đang ở Colab/Kaggle hay local, CUDA/VRAM, token có present hay không, gói đã cài, backend được khuyến nghị.

### Nếu dùng Colab từ VS Code (extension `google.colab` đã cài)

1. Mở `scripts/runtime_probe.ipynb` trong VS Code.
2. `Select Kernel` → `Colab` → `Auto Connect` → đăng nhập Google.
3. Chạy cell 1–2 để cài dependencies, cell 3 để clone repo, cell 4 để probe GPU. **Vì sao clone?** Cell của kernel Colab chạy trên máy ảo của Google, không phải máy bạn; clone chỉ để copy mã nguồn vào máy ảo đó, không tạo repo mới.
4. Tạo Colab Secret tên `HF_TOKEN`, rồi chạy cell 5–6. Kết quả nằm trong bản sao Colab → tải `results/summary/*.json` về hoặc commit/push từ Colab.

## 4. Chạy pipeline

```bash
# Kiểm tra pipeline không cần model (dùng reference_code làm output giả)
python scripts/smoke_test.py --offline
python scripts/run_benchmark.py --offline --variants A,B

# Chạy thật với endpoint (cần HF_TOKEN)
python scripts/smoke_test.py --backend endpoint
python scripts/run_benchmark.py --variants A,B

# Chạy thật trên Colab/Kaggle có GPU
python scripts/smoke_test.py --backend local

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
docs/           architecture.md, experiment_protocol.md, report_draft.md
results/        raw/, summary/
document/       tài liệu nội bộ — KHÔNG push GitHub
```

## 6. An toàn

- Mã do model sinh ra **không** chạy trong tiến trình chính; luôn qua `src/sandbox.py`.
- Tiến trình con dùng env đã lọc, thư mục tạm, timeout; trên POSIX có thêm RLIMIT CPU/RAM/process.
- Windows không giới hạn RAM được bằng stdlib và network chưa bị chặn hoàn toàn → phải nêu giới hạn này trong báo cáo.

## 7. Test

```bash
python -m unittest discover -s tests -v
```
