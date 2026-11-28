# Chỉ số đánh giá

Mỗi bài ở tập `report` được sinh **một** lần nên `pass@1` bằng tỉ lệ bài chạy đúng test.

| Chỉ số | Cách tính |
|---|---|
| `pass@1` | Số bài `test_passed = true` / 35 |
| `syntax_validity` | Số bài trích được code và parse được bằng `ast.parse` / 35 |
| `latency_mean_s` | Trung bình `latency_s` (thời gian sinh, đo quanh bước gọi mô hình) |
| p50 / median | Giá trị trung vị của `latency_s` |
| p95 | Phần tử thứ `ceil(0.95 × N)` sau khi sắp xếp `latency_s` tăng dần |
| `error_counts` | Số bản ghi theo loại lỗi: `none`, `assertion`, `runtime`, `name`, `syntax`, `timeout`, v.v. |

Kết quả thật từ `results/summary/benchmark_20261127T192206Z.json` (`run_id = 20261127T192206Z`, `offline = false`, 35 bài × 2 prompt = 70 bản ghi):

| Prompt | pass@1 | syntax validity | mean (s) | p50 (s) |
|---|---:|---:|---:|---:|
| A | 0.914 (32/35) | 1.000 (35/35) | 1.649 | 1.341 |
| B | 0.914 (32/35) | 1.000 (35/35) | 5.185 | 4.770 |

Ví dụ: `pass@1 = 32 / 35 = 0.9142857142857143 ≈ 0.914`; `syntax_validity = 35 / 35 = 1.000`.

Chưa có giá trị p95: file log thô từ lần chạy trên Colab chưa được copy vào repo và summary không lưu p95, nên không suy từ giá trị trung bình/trung vị. Không báo cáo số liệu chế độ offline và không dùng số từ bài báo làm kết quả đo của nhóm.
