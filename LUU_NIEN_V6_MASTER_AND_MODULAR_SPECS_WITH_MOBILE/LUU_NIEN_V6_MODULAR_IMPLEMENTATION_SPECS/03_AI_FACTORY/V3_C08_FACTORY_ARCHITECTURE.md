# V3.C8: research factory deep specification

> **Nguồn:** Trích không lược bỏ từ `LUU_NIEN_V5_PRODUCTION_COMPLETION_AND_NEW_FEATURES_GEMINI_FLASH_FULL_MASTER_SPEC.md` (`V3.C8`). **Nhận định mã nguồn trong V5 là audit tĩnh, chưa chứng minh production hoạt động.**
> **Dùng cho Gemini:** Chỉ mở tài liệu này với một ticket và tối đa 3–8 file source tương ứng.

## C8. Security, rights, privacy, academic integrity — threat model cho AI tự tìm/trích/viết

### C8.1. Trust boundaries bắt buộc

```text
UNTRUSTED PUBLIC WEB/PDF/TEXT
  └── Search metadata/candidate -> sanitize -> rights check -> immutable snapshot
        └── OCR/parsing in sandbox -> source passages + hash + locator
              └── proposed claims (AI_DRAFT) -> independent evidence QA
                    └── human approval (signed) -> published release
                          └── public History Tutor/Next.js/Flutter (read-only published)

SCHOOL ACCOUNTS + GOOGLE FORMS SURVEY (PRIVATE)
  └── Completely separate tenant + privacy policy + analysis service
      NEVER feeds into public corpus or web research worker by default.
```

- Search/download worker không có quyền database trực tiếp; nhận least-privilege broker token, chỉ ghi candidate/quarantine.
- OCR worker sandbox không có internet arbitrary outbound; tài liệu PDF được coi là untrusted input và scan malware trước parse.
- LLM writer không có raw browser tool hoặc action có thể gửi dữ liệu ra web; chỉ nhận approved dossier subset.
- Reviewer AI không có quyền `editorial_approve`, không thấy chữ ký secret, không được cấp `PUBLISHED` state.
- Human reviewer có MFA nếu triển khai sản xuất, permission theo domain; hai reviewer độc lập không được ký trong cùng tài khoản.
- Release service nhận signed, hashed preflight manifest; không nhận free-form “publish this” từ agent output.

### C8.2. Prompt injection từ sử liệu — 10 attack classes

1. Tài liệu chèn lệnh bỏ qua policy.
2. PDF metadata giả system/developer instructions.
3. Search snippet gắn URL thu thập API key.
4. OCR text chứa XML/JSON role-delimiter giả.
5. Hidden HTML element yêu cầu truy cập database nội bộ.
6. Source PDF chứa đường dẫn tải executable giả là OCR patch.
7. “Official catalog” site spoofing và domain gần giống.
8. Citation laundering: tài liệu dẫn một nguồn không tồn tại, agent nghĩ đã xác minh.
9. Self-referential evidence: bài AI draft cũ được index làm nguồn mới cho chính nó.
10. Reward/prompt hacking: agent viết “QA_PASS=true” vào tài liệu để ép gate.

**Mitigations:** Tất cả tool results được quote/escape và đặt trong `data-only` channel của agent; network destinations allowlist; input/output JSON schema validation; citation verifier independent; source lineage graph; explicit tool permissions; cấm arbitrary code execution từ tài liệu; prompt red-team fixtures bắt buộc trong CI.

### C8.3. Bản quyền và quyền khai thác tư liệu

`license_policy` cần tách tối thiểu các hành động: `discover_metadata`, `fetch_fulltext`, `store_snapshot`, `run_ocr`, `run_ai_extraction`, `show_excerpt`, `distribute_fulltext`, `create_translation`, `public_display`, `commercial_reuse`, `train_model`, `embed_for_search`. `permission_unknown` phải khác `permission_granted`; quyền cho mượn xem không đồng nghĩa quyền tạo bản dịch/công bố lại. Một nguồn có thể cho phép trích dẫn metadata nhưng cấm upload toàn bộ PDF lên server ngoài.

Không thiết kế “tự động chép nguyên văn toàn bộ sử liệu rồi publish” đối với tài liệu còn được bảo hộ nếu thiếu quyền. Hệ thống có thể tự tạo **bài viết nguyên bản do AI soạn** dựa trên các ý có dẫn nguồn, nhưng phải kiểm fact, giới hạn trích nguyên văn và xin phép tác giả/đơn vị giữ bản quyền khi cần. Trích quote chỉ ở độ dài được pháp luật và giấy phép thực tế cho phép, không tạo quota “x từ cho mọi nguồn” thiếu cơ sở pháp lý.

### C8.4. Chính sách sử liệu nhạy cảm và cộng đồng

Tài liệu liên quan di sản sống/nghề truyền thống có thể chứa kiến thức của cộng đồng, hình ảnh cá nhân, giới hạn văn hóa, nghi lễ không phù hợp công bố. Yêu cầu consent cụ thể, khả năng thu hồi, cách diễn giải do chủ thể cộng đồng tham gia; không mặc định tài liệu công khai trên mạng nghĩa là được mô phỏng/AI xuất bản không giới hạn. Mọi `oral_history` phải có consent record và rights. Kiểm lịch sử tác giả/nhóm nghiên cứu, không tự coi bản nháp PDF của tác giả là tài sản free-for-all.

### C8.5. Dữ liệu học sinh và khảo sát

Pipeline sinh nội dung sử học không cần PII hoặc dữ liệu cá nhân từ Google Forms. Dùng thống kê tổng hợp chỉ trong module research sau khi de-identification và ethical review phù hợp; không đưa email, timestamp nhận diện, tên trường+lớp cá thể, nội dung tự luận riêng tư vào embedding. Nếu bài LMS mẫu dùng phản hồi thực tế của học sinh để đánh giá AI, phải có consent/purpose limitation và nghiên cứu riêng. Cần tách phần “AI có thể viết bài học” với “AI đã làm học sinh tiến bộ” — điều sau phải có assessment độc lập.

### C8.6. Audit bất biến và ứng phó sai lệch công khai

- Mỗi nguồn/claim/article phiên bản có `created_by`, `reviewed_by`, `approved_by`, timestamps và SHA-256.
- Khi lỗi sử học có ảnh hưởng, issue `HISTORICAL_CORRECTION` chứa trang/câu sai, bài public đang dùng, severity, patch, reviewer, thời điểm update, changelog công khai.
- Correction không xóa phiên bản đã xuất bản; nếu pháp lý buộc gỡ excerpt/private record, giữ audit metadata đã lọc thông tin nhạy cảm theo chính sách.
- Lộ trình incident: triage 24 giờ đối với lỗi nghiêm trọng; đóng băng release bị ảnh hưởng; gỡ hiển thị nội dung vi phạm; thông báo người phụ trách; kiểm retrieval cache; cập nhật version kèm errata.
- Monitoring P11 chỉ tạo đề xuất sửa; không âm thầm thay câu hoặc nguồn đã có chữ ký duyệt.

---

