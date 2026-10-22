# V3 AI Research Factory introduction

> **Nguồn:** Trích không lược bỏ từ `LUU_NIEN_V5_PRODUCTION_COMPLETION_AND_NEW_FEATURES_GEMINI_FLASH_FULL_MASTER_SPEC.md` (`V3.C`). **Nhận định mã nguồn trong V5 là audit tĩnh, chưa chứng minh production hoạt động.**
> **Dùng cho Gemini:** Chỉ mở tài liệu này với một ticket và tối đa 3–8 file source tương ứng.

# PHỤ LỤC C — AI HISTORICAL RESEARCH FACTORY (V3): 12 PHASE × 10 CONCURRENT SUBAGENTS

> **TRẠNG THÁI:** `[TARGET / PLANNED]` — toàn bộ kiến trúc orkestrator 120 cấu hình agent trong Phụ lục C là **đặc tả cần xây**, **không phải 120 agent đã tồn tại trong branch**. Các bằng chứng `[CODE]` bên dưới được đối chiếu từ ZIP branch `feat/rbpc-cultural-bridge-2026` người dùng cung cấp. Hệ thống chưa được chạy thực nghiệm end-to-end với 10 tác vụ đồng thời trong phiên soạn spec. Trạng thái tuân thủ, giới hạn tốc độ, chất lượng và chi phí phải được đo khi triển khai.
>
> **Ý nghĩa “1 phase = 10 concurrent subagents at once”:** Đúng **10 logical worker slots độc lập trong mỗi phase**, một wave khởi động đồng thời 10 nhiệm vụ. Orchestrator chỉ chuyển phase sau khi nhận đủ 10 kết quả với trạng thái cuối, đối chiếu/merge và đạt gate. Số kết nối LLM/HTTP thực tế bị giới hạn bởi quota và điều kiện sử dụng; nếu không thể chạy đồng thời 10 request thì phase ghi `CAPACITY_BLOCKED`/backpressure và không khai báo sai rằng đã đạt 10 active executions. Có thể chạy wave kế tiếp nhưng **không hơn 10 slot trong cùng một phase của cùng một run**. Nhân bản pipeline cho nhiều hiện vật phải có **global concurrency budget** để không nhân 162 × 10 vô hạn.
>
> **Mục tiêu:** (1) tự động tìm tài liệu gốc/bài nghiên cứu và đăng ký chúng có xuất xứ; (2) tự thu nhận hợp pháp, trích xuất từng đoạn, trang, tọa độ; (3) tạo mệnh đề lịch sử có bằng chứng; (4) đối chiếu nguồn, xử lý mâu thuẫn; (5) biên soạn **full nội dung** cho 162 bản đúc nổi và các bề mặt LMS/3D/AR/CALL; (6) kiểm tra độc lập, gắn quyền, trình duyệt con người; (7) xuất bản có version, audit trail, rollback; (8) tái tổng hợp khi tư liệu hoặc quyền thay đổi. **Không** được tự xuất bản bản thảo AI là “sử liệu xác thực” mà thiếu chứng cứ và phê duyệt con người.

