# V5.1 — PRODUCT_MISSION

> **Nguồn:** Trích không lược bỏ từ `LUU_NIEN_V5_PRODUCTION_COMPLETION_AND_NEW_FEATURES_GEMINI_FLASH_FULL_MASTER_SPEC.md` (`V5.1`). **Nhận định mã nguồn trong V5 là audit tĩnh, chưa chứng minh production hoạt động.**
> **Dùng cho Gemini:** Chỉ mở tài liệu này với một ticket và tối đa 3–8 file source tương ứng.

## V5.1 — ĐỊNH NGHĨA HỆ THỐNG ĐẦY ĐỦ, KHÔNG NHẦM ĐÍCH

### 1.1. Sứ mệnh sản phẩm

LƯU NIÊN là nền tảng **source-grounded HeritageTech / EdTech / living-culture marketplace** kết nối ba giá trị có thể kiểm chứng: (i) di sản có nguồn và bản quyền minh bạch, (ii) hoạt động học tập có sản phẩm và đánh giá, (iii) khám phá và trải nghiệm với nghệ nhân thật, giao dịch hỏi lịch thật. Các sản phẩm B2B/B2B2C phát triển thêm phải dùng cùng canonical knowledge graph, moderation, account/consent model và audit trails.

### 1.2. Hai trục sản phẩm; một lõi dữ liệu

| Trục | Người dùng | Hành trình | Doanh thu giả thuyết | Bằng chứng thành công thật |
|---|---|---|---|---|
| `LEARN` EdTech | học sinh, giáo viên, trường, bảo tàng | quan sát → hỏi → nguồn → giải thích → nộp bài → phản hồi | license trường/bảo tàng, training, nội dung được cấp phép | lớp triển khai, hoạt động hoàn thành thực, chất lượng bài làm được chấm; không lấy 1.502 cảm nhận làm learning gain |
| `EXPERIENCE` HeritageTech | khách, nghệ nhân, đối tác văn hoá | khám phá → nguồn → nghệ nhân → inquiry → xác nhận → trải nghiệm → đánh giá thật | phí dịch vụ giao dịch hoàn tất hoặc SaaS đối tác nếu hợp đồng cho phép | inquiries ghi DB, partner xác nhận, hoàn tất có evidence, doanh thu thực, chi phí thực |
| `PLATFORM` hạ tầng | curator, researcher, editor, developer | nhập → xác minh → ấn bản → sử dụng → kiểm toán → cập nhật | không phải tuyến doanh thu độc lập mặc định | verified claims, citations, quyền media, data lineage, SLO/uptime |

Không đồng nhất ba tuyến; một lớp trung học không phải khách du lịch, và một phiên inquiry chưa phải booking đã thanh toán. **No fake traction, no inferred GMV.**

### 1.3. Definition of Done theo 5 cấp

- **L0 Prototype:** UI chạy bằng mock/seed, không đại diện dữ liệu người dùng thật.
- **L1 Integrated:** các flows liên kết DB/API thật, nhưng chưa đạt security/ops gate.
- **L2 Staging-ready:** toàn bộ negative paths, concurrency, migrations, security E2E và rollback đã kiểm chứng.
- **L3 Production-ready (technical):** cấu hình production được test, quan sát được, backup/restore drill, privacy, nguồn dẫn, đối tác, 3D/AR fallback và release controls đạt gate.
- **L4 Market-pilot-ready:** người dùng/đối tác có đồng thuận, onboarding, support, phân tích funnel thật, phản hồi thật và hợp đồng/giấy phép hợp lệ.
- **L5 Startup-scale-ready:** unit economics thực nghiệm, vận hành đa tenant, churn/cohort đo được, đáp ứng tăng tải và rủi ro pháp lý được xử lý.

**Cấm ghi L3/L4/L5** nếu các blocker trong V5.3 chưa được xác nhận đóng bằng evidence. Release một vertical slice L3 tốt hơn 50 màn hình L0.

### 1.4. Triết lý NO-MOCK-IN-PRODUCTION

Production phải trả: dữ liệu thật / trạng thái rỗng đúng (`200 []`) / lỗi có code và correlation ID / unavailable nghiêm túc / queued-offline được hiển thị chưa đồng bộ; **không bao giờ** nhảy sang dữ liệu mẫu, câu trả lời AI bịa hoặc đánh giá giả. Demo environment có fixture riêng, banner rõ, DB riêng, `DEMO_MODE=1`, URL riêng, không chung analytics và không được xuất hóa đơn giả như thật.

