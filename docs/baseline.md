# Baseline suy luận

| Thành phần | Cấu hình |
|---|---|
| Mô hình | `meta-llama/Llama-3.1-8B-Instruct` @ `0e9e39f249a16976918f6564b8830bc894c89659` |
| Môi trường | GPU Colab T4, CUDA khả dụng, Python 3.13 |
| Backend | Transformers/PyTorch chạy local, lượng tử hóa 4-bit NF4; kiểu tính toán thực tế `float16` trên T4 |
| Giải mã | Greedy, `do_sample=false`, `max_new_tokens=256` |
| Kiểm tra đầu-cuối | Smoke test sinh được hàm Python, parse đúng cú pháp và vượt qua unit test trong sandbox |

Lần đo chính thức có `run_id = 20261127T192206Z`: 35 bài `report`, hai biến thể prompt A/B, 70 bản ghi, không ở chế độ offline. Bảng kết quả xem `docs/metrics.md`; nguồn là `results/summary/benchmark_20261127T192206Z.json`. Log thô của lần này vẫn nằm trong bản sao Colab và cần được export về `results/raw/` trước khi chốt báo cáo; repo không chứa file raw giả.

Dịch vụ inference từ xa không dùng được cho checkpoint này (không có provider mapping; lượt thử với `groq` báo mô hình không được hỗ trợ), nên baseline dùng GPU local. Checkpoint và decoding được giữ cố định giữa hai lượt A/B; mỗi lần chạy lại phải có `run_id` riêng.

```bash
python scripts/check_runtime.py
python scripts/smoke_test.py --offline          # chỉ validate pipeline
python scripts/smoke_test.py --backend local    # cần GPU CUDA
python scripts/run_benchmark.py --backend local --variants A,B
```
