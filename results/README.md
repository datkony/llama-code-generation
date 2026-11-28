# Kết quả thực nghiệm

Thư mục này chứa log do pipeline của nhóm tự đo. **Không** chép số benchmark từ paper/model card vào đây.

| File | Nội dung |
|---|---|
| `raw/benchmark_<run_id>.jsonl` | Một dòng cho mỗi (task, prompt variant): output, latency, syntax/test result, error type. |
| `summary/benchmark_<run_id>.json` | Metric tổng hợp theo từng variant: `pass_at_1`, `syntax_validity`, `latency_mean_s`, `latency_median_s`, `error_counts`. |

## Lần chạy hiện tại

- `run_id`: `20261127T192206Z`
- Model: `meta-llama/Llama-3.1-8B-Instruct` @ `0e9e39f249a16976918f6564b8830bc894c89659`
- Backend: `local`, 4-bit trên GPU Colab (T4)
- Dữ liệu: 35 bài `split=report`, Prompt A/B, 70 bản ghi
- File: `summary/benchmark_20261127T192206Z.json`

> File summary được trích từ output của `scripts/runtime_probe.ipynb` (lần chạy thành công). File raw tương ứng nằm trong bản sao Colab tại `/content/llama-code-generation/results/raw/` và cần được copy về repo bằng cell 8 của notebook trước khi chốt báo cáo cuối. Không tạo file raw giả. Chưa có p95 vì thiếu file raw; không suy từ summary.

> Cấu hình sandbox của lượt này là bản trước khi bổ sung import guard/audit hook ngày 28/11/2026. Nếu chạy lại, dùng `run_id` mới và giữ summary này nguyên vẹn; không gộp số liệu của hai cấu hình sandbox khác nhau. Xem [docs/sandbox.md](../docs/sandbox.md).
