# Sandbox thực thi mã

Mã do mô hình sinh ra **không** chạy trong tiến trình chính: nó được ghi vào thư mục tạm và thực thi ở tiến trình con với môi trường đã lọc, stdin đóng, timeout và thu riêng stdout/stderr. Trước khi chạy, code phải parse được bằng `ast.parse`. Trên POSIX có thêm giới hạn CPU, RAM, kích thước file và số tiến trình; trên Windows stdlib không giới hạn RAM.

Bổ sung gần đây: chặn import của các module mạng/tiến trình (`socket`, `urllib`, `requests`, `subprocess`, `multiprocessing`, `ctypes`, …) và dùng audit hook để từ chối tạo tiến trình, mở socket hay đọc file ngoài thư mục cho phép (thư mục tạm và cài đặt Python).

| Tình huống | Trạng thái kiểm chứng |
|---|---|
| Vòng lặp vô hạn / timeout | Đã kiểm chứng bằng unit test |
| Lỗi cú pháp trước khi chạy | Đã kiểm chứng bằng unit test |
| Import bị chặn (`socket`, `urllib`, `subprocess`) | Đã kiểm chứng bằng unit test |
| Đọc file ngoài thư mục làm việc | Đã kiểm chứng bằng unit test |
| `os.system` bị từ chối | Đã kiểm chứng bằng unit test |
| Tạo socket trực tiếp, ghi file ra ngoài, `fork/exec`, giới hạn RAM thực tế | Cần bổ sung test (POSIX) |

Lệnh chạy test: `python -m unittest discover -s tests -q` → 16 test, `OK` (lần chạy gần nhất).

Sandbox là biện pháp giảm thiểu rủi ro cho đồ án, không phải ranh giới bảo mật production: network không bị cắt ở tầng hệ điều hành, Windows không giới hạn RAM, và audit hook có thể bị vượt qua bởi mã native hoặc đường dẫn được phép. Mọi kết quả benchmark phải ghi rõ cấu hình sandbox tương ứng; không trộn số liệu của các lần chạy khác cấu hình.
