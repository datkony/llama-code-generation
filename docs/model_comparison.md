# So sánh Llama 3.1, Code Llama và Llama 4

Bảng dưới dùng để đặt mô hình chính của đồ án (`Llama 3.1 8B Instruct`) vào bối cảnh họ Llama. Các giá trị là thông tin từ tài liệu chính thức, **không phải kết quả đo của nhóm**; số benchmark trong paper/blog không được dùng làm số liệu thực nghiệm ở đây.

| Tiêu chí | Llama 3.1 8B Instruct | Code Llama | Llama 4 Scout / Maverick |
|---|---|---|---|
| Kiến trúc | Dense, decoder-only, **GQA** | Dựa trên **Llama 2**, tinh chỉnh cho mã | **MoE** đa phương thức (early fusion) |
| Biến thể / quy mô | 8B (cùng họ có 70B, 405B) | base / Python / Instruct; 7B–70B | Scout: 109B tổng, **17B active**, 16 experts; Maverick: 400B tổng, **17B active**, 128 experts |
| Ngữ cảnh | 128k | Huấn luyện 16k; báo cáo tới 100k (có ngoại lệ theo biến thể) | Scout 10M; Maverick 1M |
| Định hướng code | Năng lực tổng quát, bản Instruct tuân chỉ dẫn | **Chuyên biệt** cho tổng hợp/hiểu mã; biến thể Python tinh chỉnh thêm dữ liệu Python | Sinh text và code theo model card, không phải dòng chuyên code |
| Tính năng riêng | Chat template cho bản Instruct | Infilling với token `<PRE>`, `<SUF>`, `<MID>` (phạm vi hỗ trợ giữa các biến thể chưa thống nhất giữa nguồn chính thức) | System prompt/steerability; đa phương thức text + image |
| Ngôn ngữ | 8 ngôn ngữ, không liệt kê tiếng Việt | Chủ yếu mã/tiếng Anh | 12 ngôn ngữ, có tiếng Việt |
| License | Llama 3.1 Community License | **Llama 2 Community License** (hạn chế dùng output để cải thiện LLM khác; >700M MAU cần license riêng) | Llama 4 Community License |
| Vai trò trong đồ án | **Mô hình chính**, đã chạy thật với 4-bit trên GPU T4 | Đối chiếu về chuyên biệt hóa cho code | Mở rộng xu hướng MoE; không demo bắt buộc |

## Phân biệt hai khái niệm

- **Có khả năng sinh code:** Llama 3.1 8B Instruct viết được hàm Python — đây là năng lực quan sát được của mô hình tổng quát sau chỉ dẫn.
- **Chuyên biệt cho code:** Code Llama được xây dựng và tinh chỉnh cho mã (base/Python/Instruct, infilling). Đây là mục tiêu thiết kế và dữ liệu huấn luyện, không suy ra chỉ từ việc mô hình sinh ra code được.

Llama 4 không phải phiên bản kế tiếp trực tiếp của Code Llama: nó là dòng MoE đa phương thức, trong khi Code Llama xây trên Llama 2.

## Lý do lựa chọn

- **Chọn Llama 3.1 8B Instruct:** kích thước vừa sức với GPU 16 GiB khi dùng 4-bit; có cấu hình và tài liệu rõ ràng để giải thích GQA/RoPE/RMSNorm/SwiGLU/KV cache; bản Instruct phù hợp để so sánh prompt trực tiếp và prompt có cấu trúc; điều khoản output rõ ràng.
- **Không dùng Code Llama làm mô hình chính:** license Llama 2 hạn chế hơn, định dạng prompt/infilling riêng và chưa được nạp thử trong môi trường đã chốt. Giữ lại như một điểm đối chiếu về chuyên biệt hóa.
- **Không dùng Llama 4 cho demo:** tổng tham số 109B/400B và yêu cầu hạ tầng vượt phạm vi; đa phương thức nằm ngoài bài toán sinh hàm Python. Giữ lại trong phần xu hướng kiến trúc: MoE chỉ kích hoạt 17B tham số cho mỗi token.

Không xếp hạng ba dòng bằng benchmark của nhà phát triển: điều kiện đánh giá (checkpoint, prompt, precision, tập dữ liệu, metric) khác nhau. Mọi số liệu pass@1 của đồ án chỉ lấy từ pipeline thực thi của chính dự án.

## Nguồn

1. Llama Team, AI @ Meta (2024). *The Llama 3 Herd of Models.* arXiv:2407.21783.
2. Meta AI (2024). *Llama 3.1 8B Instruct — Model Card.* https://huggingface.co/meta-llama/Llama-3.1-8B-Instruct
3. Rozière et al. (2023; v3 2024). *Code Llama: Open Foundation Models for Code.* arXiv:2308.12950.
4. Meta AI. *Code Llama blog, model card và prompt formats.* https://ai.meta.com/blog/code-llama-large-language-model-coding ; https://huggingface.co/meta-llama/CodeLlama-7b-Instruct-hf
5. Meta AI (2025). *Llama 4 Model Card và blog.* https://github.com/meta-llama/llama-models/blob/main/models/llama4/MODEL_CARD.md ; https://ai.meta.com/blog/llama-4-multimodal-intelligence

Xem thêm [docs/model_architecture.md](model_architecture.md) và [docs/generation_pipeline.md](generation_pipeline.md).
