# V5.0 — HOW_TO_USE

> **Nguồn:** Trích không lược bỏ từ `LUU_NIEN_V5_PRODUCTION_COMPLETION_AND_NEW_FEATURES_GEMINI_FLASH_FULL_MASTER_SPEC.md` (`V5.0`). **Nhận định mã nguồn trong V5 là audit tĩnh, chưa chứng minh production hoạt động.**
> **Dùng cho Gemini:** Chỉ mở tài liệu này với một ticket và tối đa 3–8 file source tương ứng.

## V5.0 — CÁCH DÙNG FILE NÀY KHI GIAO CHO GEMINI

1. Đọc V5.0 → V5.6, chọn đúng 1 ticket `V5-T###`, load thêm entry của ticket và tối đa 3–8 source files liên quan; không nạp cả file ~1MB vào một prompt.
2. Chạy preflight an toàn ở checkout branch thật; không giả vờ đã fetch HEAD khi chỉ có ZIP. Điền `BASELINE_REPORT` kèm đường dẫn/line numbers và kết quả thực thi.
3. Giao **một phase với 10 concurrent subagent task envelopes**, mỗi task có file ownership, input hash, expected output, timeout/cost budget và fail policy. Các subagent chỉ được sửa file non-overlapping; với schema chung dùng patch proposals để integrator duyệt.
4. Chọn 1–2 patch hẹp để tích hợp mỗi lượt; test ngay, log PASS/FAIL/BLOCKED/NOT_RUN. Không merge khi report thiếu bằng chứng.
5. Kết thúc ticket bằng PR diff + migration + contract tests + rollback plan + provenance/PII/rights checklist + người duyệt. Chỉ bật cờ sản phẩm ở staging rồi mới production.
6. Viết báo cáo theo template V5.15. Không ghi `100% complete` hay `production-ready` chỉ vì các unit tests đi qua.

**Định nghĩa nhãn**: `[CODE_OBSERVED]` = có trong ZIP; `[RUNTIME_VERIFIED]` = đã chạy với log; `[TARGET]` = cần triển khai; `[OPEN_QUESTION]` = cần xác minh với owner; `[NO_EVIDENCE]` = chưa có bằng chứng; `[DEMO_ONLY]` = dùng trong sandbox trình diễn; `[HUMAN_REQUIRED]` = quyết định/đồng thuận/duyệt sử học của người thật. Đánh dấu rõ nhãn tại mọi bảng dữ liệu/trạng thái.

