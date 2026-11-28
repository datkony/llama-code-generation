# Tập bài toán

`data/tasks.jsonl` là tập đã khóa: **40 bài tự biên soạn**, gồm 5 bài `tune` để thử prompt và 35 bài `report` để báo cáo số liệu.

| Trường | Nội dung |
|---|---|
| `task_id` | Định danh ổn định (`sample-001` … `sample-040`) |
| `prompt` | Mô tả bài toán |
| `entry_point` | Tên hàm cần sinh |
| `examples` | Ví dụ minh họa (chỉ dùng trong Prompt B) |
| `test_code` | Test công khai chạy trong sandbox |
| `reference_code` | Đáp án tham chiếu, chỉ dùng khi validate pipeline ở chế độ offline |
| `source`, `split` | Nguồn bài và nhóm sử dụng |

Quy tắc:

- Không dùng bài `tune` để tính kết quả; không đọc test của tập `report` khi viết prompt.
- Mỗi bài có mô tả rõ, chữ ký hàm duy nhất, ví dụ và test chạy được bằng Python 3 + thư viện chuẩn; bài mơ hồ hoặc trùng lặp bị loại.
- Đã kiểm tra: 40 ID, mô tả, tên hàm, test và đáp án đều không trùng; 35/5 bài theo đúng split.
- Tập không chứa thông tin xác thực, dữ liệu cá nhân hay test ẩn. Khi mở rộng cần ghi nguồn/phiên bản và danh sách task ID vào log thí nghiệm.
