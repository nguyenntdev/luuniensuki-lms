# V2 B0: source-derived engineering detail

> **Nguồn:** Trích không lược bỏ từ `LUU_NIEN_V5_PRODUCTION_COMPLETION_AND_NEW_FEATURES_GEMINI_FLASH_FULL_MASTER_SPEC.md` (`V2.B0`). **Nhận định mã nguồn trong V5 là audit tĩnh, chưa chứng minh production hoạt động.**
> **Dùng cho Gemini:** Chỉ mở tài liệu này với một ticket và tối đa 3–8 file source tương ứng.

## B0. Quy cách bàn giao spec và độ tin cậy của phát hiện

**Đích sử dụng**: để PM có thể tạo backlog, tech lead chia nhánh, lập trình viên code từ contract, QA viết test trước khi code, chuyên gia lịch sử duyệt nguồn, người phụ trách nghiên cứu kiểm toán lại dữ liệu 1.502, và người chịu trách nhiệm xuất bản khoa học truy xuất provenance của mọi biểu đồ/screenshot.

**Biên audit**: snapshot ZIP `feat/rbpc-cultural-bridge-2026`, không có `.git`; không suy ra HEAD của repository hiện tại hoặc các commit phát sinh sau ZIP. `README`, `docs/rbpc` và master goal là chứng cứ thiết kế/tuyên bố nội bộ, không phải bằng chứng thực nghiệm của sản phẩm. Không có dữ liệu Google Forms gốc hay chấp thuận nghiên cứu đính kèm trong ZIP. Không thực hiện pen-test thật, không sử dụng credential production.

### B0.1 Bảng phân định “đã có” và “đạt chuẩn sản phẩm”

| Mục | Trong code hiện tại | Để ghi `PRODUCTION_READY` cần thêm | Chứng cứ chấp nhận |
|---|---|---|---|
| 162 item JSON | EXISTING: 9 file, mỗi file 18 item | mapping thực thể/bản đúc nổi đúng loại; nguồn dẫn; từng claim kiểm chứng; ảnh được phép dùng | import report + 162 editorial records `approved` + provenance snapshot |
| 162 image JPG | EXISTING: collection ảnh | hash, đối tượng/chủ sở hữu, chứng cứ cho quyền, crop/alt text, quality QC | asset ledger + signed/recorded license proof |
| `3d_mesh_id` | EXISTING: 162 identifier string trong JSON | asset tồn tại thật, mesh/hotspot liên kết đúng, version, calibration; không được suy ra đủ 162 GLB | referential-integrity report + viewer smoke/video capture |
| server grading | EXISTING: `history_learning.py` | chuẩn rubric tự luận, câu hỏi có claim được duyệt, pre/post versioning, grading test | grading fixtures + blind double rating |
| inquiry API | EXISTING: `backend/routers/rbpc.py` | client production fail-closed, rate limit dùng shared store, trusted proxy, per-partner RBAC | e2e backend-down, 429 multi-replica, authz matrix |
| rights filter 3D | EXISTING: predicates trong `heritage.py` | allowlist quyền rõ ràng, mục đích dùng, trạng thái thu hồi, CDN deny | policy tests theo từng enum + contract tests |
| AI tutor | EXISTING: retrieval + cite checks | gold-set, human review, abstention, prompt-injection red team, version lock | independent eval report, acceptance thresholds |
| Google Forms 1.502 | EXTERNAL (người dùng xác nhận có) | anonymized import, questionnaire, skip logic, validation, mapping | regenerated tables and comparison with manuscript |
| CALL | TARGET (conditional) | objective ngôn ngữ, content được duyệt, rubric ngôn ngữ, user study nếu claim hiệu quả | language SME signoff + lesson/test fixture |

### B0.2 Quy tắc đóng issue

Một ticket chỉ được chuyển `DONE` khi có: link PR, commit, tài liệu ADR/contract được cập nhật, test tự động pass, bằng chứng QA, reviewer kỹ thuật độc lập và (nếu nội dung di sản) trạng thái duyệt học thuật. `CODE_COMPLETE` không đồng nghĩa `RELEASED`; `RELEASED` không đồng nghĩa `RESEARCH_VALIDATED`.

### B0.3 Tài liệu phải bảo toàn tính nguyên gốc

Không sửa các tệp seed 162 trực tiếp để “làm đẹp số liệu” mà không ghi nguồn gốc sửa đổi. Mọi thay đổi phải tạo bản import mới có `source_snapshot_sha256`, `transform_version`, `changed_fields`, `reviewer`, `decision`, `timestamp`. Lưu manifest ban đầu để có thể tái dựng dữ liệu tại thời điểm đã dùng viết bài.

---

