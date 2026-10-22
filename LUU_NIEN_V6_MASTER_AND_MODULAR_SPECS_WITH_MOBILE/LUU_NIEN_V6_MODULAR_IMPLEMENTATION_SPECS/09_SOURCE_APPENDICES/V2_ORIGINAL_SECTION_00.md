# V2 original archival technical chapter — SECTION_00

> Extracted without rewriting from V2 snapshot documentation, **not verified current code**.

## 0. EXECUTIVE DECISIONS — quyết định bắt buộc trước khi code

1. **Một nguồn chân lý sử học có thể kiểm tra**: `historical_entity → claim → claim_source_binding → source → locator → review_state`; 3D/AR/chatbot chỉ là các lớp trình bày; nội dung AI-generated phải được cách ly khỏi tri thức đã duyệt cho tới khi người kiểm chứng chịu trách nhiệm.
2. **Một định danh xuyên hệ thống** cho 9 đỉnh và 162 bản đúc nổi; không dùng trực tiếp file/slug làm khóa nghiệp vụ. Kho Cửu Đỉnh khác với taxonomy 14 thành phần di sản thuộc Quần thể Di tích Cố đô Huế, và khác với mạng lưới di sản sống.
3. **Học tập có thể kiểm chứng**: mọi bài mẫu phải có mục tiêu, nguồn, câu hỏi, bài làm, rubric, feedback và revision trace. Không lấy completion, số lượt bấm, hài lòng hay tự đánh giá làm bằng chứng tăng điểm tư duy lịch sử.
4. **Tách `DEMO` / `STAGING` / `PRODUCTION`** bằng cấu hình fail-closed. Production không được trả booking giả, danh sách partner giả hoặc câu trả lời mô phỏng không được gắn nhãn; không chuyển sự cố mạng thành xác nhận giao dịch.
5. **Dữ liệu Google Forms là bộ nghiên cứu bên ngoài codebase cho đến khi nhập có kiểm soát**: không có CSV cấp người trong ZIP hiện tại. Bảng tổng hợp 1.502 là thống kê đã báo cáo trong bài, chưa phải dữ liệu gốc đã audit tại đây.
6. **Ba tuyến sản phẩm vận hành độc lập trên core dữ liệu chung**: (A) di sản–học lịch sử, (B) khám phá Huế–nghệ nhân–inquiry minh bạch, (C) nghiên cứu/AI/CALL có điều kiện. Tắt B/C không làm hỏng A.
7. **An toàn phát hành**: khóa và kiểm tra migration graph, CI chạy mọi PR vào feature branch, contract tests hai backend, bảo mật cookie/CSRF/PII, quy tắc bản quyền và đồng thuận, xác thực status người thẩm định.
8. **Không hứa “zero hallucination” tuyệt đối**: chỉ chấp nhận đầu ra có dẫn chứng hợp lệ, phát hiện unsupported claims theo bộ đánh giá, abstain khi thiếu căn cứ; không ghi tỷ lệ 100% khi chưa chạy benchmark trên môi trường đích.
9. **Phát hành theo gates thay vì theo số tính năng**: Gate dữ liệu 162, Gate history inquiry, Gate học sinh–giáo viên, Gate rights, Gate AI, Gate tourism, Gate research; chức năng không qua gate không được gắn nhãn released.
10. **Bảo vệ khả năng công bố khoa học**: version-lock học liệu và công cụ khảo sát, lưu protocol, consent, provenance; phân biệt user acceptance (đo bằng bảng hỏi) và learning effectiveness (chỉ đo nếu có assessment thích hợp).

