# Giao thức thực nghiệm (rút gọn cho deadline 01/12)

## 1. Đóng băng trước khi đo

| Thành phần | Giá trị hiện tại |
|---|---|
| Model | `meta-llama/Llama-3.1-8B-Instruct` @ `0e9e39f249a16976918f6564b8830bc894c89659` |
| Fallback | `meta-llama/Llama-3.2-3B-Instruct` (chỉ khi VRAM < 8 GB; ghi lý do) |
| Backend | `local` 4-bit trên GPU CUDA. HF Inference Providers không có provider mapping cho checkpoint này → không dùng endpoint. |
| Decoding | greedy (`do_sample=false`, `temperature=0`, `top_p=1`, `max_new_tokens=256`) |
| Dataset | 35 bài `split=report` trong `data/tasks.jsonl` (5 bài `split=tune` chỉ dùng thử prompt, không tính số liệu) |
| Prompt | A = trực tiếp, B = có cấu trúc; cùng model/decoding/task |

Không đổi checkpoint giữa hai lượt A/B. Không sửa tay output trước khi chấm.

## 2. Lệnh chạy

```bash
python scripts/check_runtime.py
python scripts/smoke_test.py --offline              # validate pipeline, không cần token
python scripts/smoke_test.py --backend local        # GPU + HF_TOKEN
python scripts/run_benchmark.py --backend local --variants A,B
```

Trên Colab dùng `scripts/runtime_probe.ipynb` (cell 1–8) để làm toàn bộ các bước trên và đóng gói artifact.

## 3. Chỉ số

- `pass_at_1` = số bài `test_passed=true` / số bài.
- `syntax_validity` = số bài parse được / số bài.
- `latency_mean_s`, `latency_median_s` tính từ `latency_s`.
- `error_counts`: `syntax`, `timeout`, `assertion`, `import`, `name`, `runtime`, `generation_error`.

## 4. Schema log thô

Mỗi dòng trong `results/raw/benchmark_*.jsonl` có:

```text
timestamp, task_id, split, prompt_variant, model_id, revision,
backend, provider, decoding_config, latency_s, n_new_tokens,
syntax_valid, test_passed, error_type, exec_seconds, stderr, generation
```

`results/summary/benchmark_*.json` chứa metric theo từng variant.

## 5. Quy tắc chạy lại

Chỉ chạy lại khi có lỗi hạ tầng được ghi rõ (OOM, mất mạng, restart runtime). Giữ lại log lỗi cũ. Không loại mẫu vì kết quả xấu. Mỗi lần chạy phải có `run_id` riêng; không ghi đè file cũ.

## 6. Threats to validity

- Tập mẫu nhỏ; không ngoại suy ra toàn bộ họ Llama.
- Prompt bằng tiếng Anh trong khi đề bài gốc có thể tiếng Việt.
- Token/provider/quantization khác nhau có thể làm đổi kết quả; phải log.
- Sandbox làm latency cao hơn inference thuần.
