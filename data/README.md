# Tập bài toán

`tasks.jsonl` gồm **40 bài tự biên soạn**: 5 bài `split=tune` để thử prompt và 35 bài `split=report` để báo cáo số liệu. Mỗi dòng là một JSON object:

| Trường | Ý nghĩa |
|---|---|
| `task_id` | Định danh ổn định |
| `prompt` | Mô tả bài toán (đưa vào prompt) |
| `entry_point` | Tên hàm cần sinh |
| `examples` | Ví dụ minh họa (chỉ đưa vào Prompt B) |
| `test_code` | Test công khai chạy trong sandbox |
| `reference_code` | **Chỉ dùng cho `--offline`** để kiểm tra evaluator; không bao giờ đưa vào prompt |
| `source` | Nguồn bài |
| `split` | `tune` (thử prompt) hoặc `report` (báo cáo số liệu) |

## Lưu ý khi mở rộng

- Tập hiện tại có **40 bài** (5 tune + 35 report), nằm trong khoảng 30–50 của proposal. Nếu muốn thay bằng MBPP/HumanEval, giữ nguyên cấu trúc từng dòng và ghi nguồn/phien bản vào log.
- Không dùng `test_code` của tập `report` để viết prompt. Không đưa `reference_code` vào prompt.
- Khi đổi dataset, ghi `task_ids`, version/nguồn và split vào log thí nghiệm.
