# V2 B13: source-derived engineering detail

> **Nguồn:** Trích không lược bỏ từ `LUU_NIEN_V5_PRODUCTION_COMPLETION_AND_NEW_FEATURES_GEMINI_FLASH_FULL_MASTER_SPEC.md` (`V2.B13`). **Nhận định mã nguồn trong V5 là audit tĩnh, chưa chứng minh production hoạt động.**
> **Dùng cho Gemini:** Chỉ mở tài liệu này với một ticket và tối đa 3–8 file source tương ứng.

## B13. READINESS REVIEW MẪU CHO CTO / RESEARCH LEAD

### Release R0/G0
- [ ] 1. CI chạy trên commit cần phát hành? **Evidence URL/ID:** `PENDING`; **Sign-off:** `PENDING`.
- [ ] 2. Migrations reproducible từ DB sạch và snapshot? **Evidence URL/ID:** `PENDING`; **Sign-off:** `PENDING`.
- [ ] 3. Production credentials không nằm trong artifacts? **Evidence URL/ID:** `PENDING`; **Sign-off:** `PENDING`.
- [ ] 4. Rollback playbook được thử trên staging? **Evidence URL/ID:** `PENDING`; **Sign-off:** `PENDING`.
- [ ] 5. No simulated success path trong prod? **Evidence URL/ID:** `PENDING`; **Sign-off:** `PENDING`.

### Release R1/G1
- [ ] 1. 9x18 canonical IDs đã được reviewer ký? **Evidence URL/ID:** `PENDING`; **Sign-off:** `PENDING`.
- [ ] 2. Các claim dùng trong bài học có locator kiểm được? **Evidence URL/ID:** `PENDING`; **Sign-off:** `PENDING`.
- [ ] 3. Chữ Hán/phiên âm có bản gốc và reviewer? **Evidence URL/ID:** `PENDING`; **Sign-off:** `PENDING`.
- [ ] 4. Nguồn nào bị tranh luận đã được hiển thị đúng trạng thái? **Evidence URL/ID:** `PENDING`; **Sign-off:** `PENDING`.
- [ ] 5. Có thể hash/rebuild release với cùng input? **Evidence URL/ID:** `PENDING`; **Sign-off:** `PENDING`.

### Release R2/G3-G4
- [ ] 1. Chứng cứ quyền ảnh/GLB được lưu riêng? **Evidence URL/ID:** `PENDING`; **Sign-off:** `PENDING`.
- [ ] 2. Unknown/expired rights có bị chặn kể cả CDN? **Evidence URL/ID:** `PENDING`; **Sign-off:** `PENDING`.
- [ ] 3. Tất cả nhiệm vụ core có 2D fallback tương đương? **Evidence URL/ID:** `PENDING`; **Sign-off:** `PENDING`.
- [ ] 4. Hotspot canonical id map đã được kiểm? **Evidence URL/ID:** `PENDING`; **Sign-off:** `PENDING`.
- [ ] 5. Tải mô hình không làm hỏng truy cập trên điện thoại yếu? **Evidence URL/ID:** `PENDING`; **Sign-off:** `PENDING`.

### Release R3/G2
- [ ] 1. Bài học thực tế có đủ sáu bước? **Evidence URL/ID:** `PENDING`; **Sign-off:** `PENDING`.
- [ ] 2. Học sinh giải thích nguồn chứ không chỉ click? **Evidence URL/ID:** `PENDING`; **Sign-off:** `PENDING`.
- [ ] 3. Rubric được giáo viên/historian duyệt? **Evidence URL/ID:** `PENDING`; **Sign-off:** `PENDING`.
- [ ] 4. Attempts và revisions immutable? **Evidence URL/ID:** `PENDING`; **Sign-off:** `PENDING`.
- [ ] 5. Teacher role/class authorization test pass? **Evidence URL/ID:** `PENDING`; **Sign-off:** `PENDING`.

### Release R4/G6
- [ ] 1. Bản Google Forms gốc có question wording/skip logic? **Evidence URL/ID:** `PENDING`; **Sign-off:** `PENDING`.
- [ ] 2. N=1502 có được tái lập theo từng item? **Evidence URL/ID:** `PENDING`; **Sign-off:** `PENDING`.
- [ ] 3. 4,506 lựa chọn đã có histogram cấp người? **Evidence URL/ID:** `PENDING`; **Sign-off:** `PENDING`.
- [ ] 4. Raw PII được cách ly? **Evidence URL/ID:** `PENDING`; **Sign-off:** `PENDING`.
- [ ] 5. Paper tables có analysis hash? **Evidence URL/ID:** `PENDING`; **Sign-off:** `PENDING`.

### Release R5/G5
- [ ] 1. Corpus chỉ gồm claim nguồn được duyệt? **Evidence URL/ID:** `PENDING`; **Sign-off:** `PENDING`.
- [ ] 2. Gold eval độc lập có human rating? **Evidence URL/ID:** `PENDING`; **Sign-off:** `PENDING`.
- [ ] 3. AI biết abstain khi thiếu căn cứ? **Evidence URL/ID:** `PENDING`; **Sign-off:** `PENDING`.
- [ ] 4. Prompt injection suite pass? **Evidence URL/ID:** `PENDING`; **Sign-off:** `PENDING`.
- [ ] 5. Citations có source locator thực? **Evidence URL/ID:** `PENDING`; **Sign-off:** `PENDING`.

### Release R6/G4-G8
- [ ] 1. Partner consent có bằng chứng? **Evidence URL/ID:** `PENDING`; **Sign-off:** `PENDING`.
- [ ] 2. Inquiry là inquiry, không giả booking/payment? **Evidence URL/ID:** `PENDING`; **Sign-off:** `PENDING`.
- [ ] 3. Backend down không tạo receipt? **Evidence URL/ID:** `PENDING`; **Sign-off:** `PENDING`.
- [ ] 4. Rate limit shared và anti-IDOR pass? **Evidence URL/ID:** `PENDING`; **Sign-off:** `PENDING`.
- [ ] 5. Retention và deletion được kiểm? **Evidence URL/ID:** `PENDING`; **Sign-off:** `PENDING`.

### Paper submission/G7
- [ ] 1. Mọi figure map đúng product/data snapshot? **Evidence URL/ID:** `PENDING`; **Sign-off:** `PENDING`.
- [ ] 2. Survey perceptions không bị viết thành measured learning gains? **Evidence URL/ID:** `PENDING`; **Sign-off:** `PENDING`.
- [ ] 3. Tác giả và quyền tái sử dụng dataset đã xác minh? **Evidence URL/ID:** `PENDING`; **Sign-off:** `PENDING`.
- [ ] 4. Không nộp trùng bài có đóng góp thực chất? **Evidence URL/ID:** `PENDING`; **Sign-off:** `PENDING`.
- [ ] 5. Các số nghiên cứu mới đều có protocol và results thật? **Evidence URL/ID:** `PENDING`; **Sign-off:** `PENDING`.

**Tình trạng tài liệu:** `SPEC_COMPLETED` không đồng nghĩa `PRODUCT_IMPLEMENTED`; `AUDIT_STATIC` không đồng nghĩa `PEN_TEST_PASSED`; `RESEARCH_METHOD_DESCRIBED` không đồng nghĩa `EMPIRICAL_EFFECTIVENESS_ESTABLISHED`.


---

