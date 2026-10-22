# V2 original archival technical chapter — SECTION_07

> Extracted without rewriting from V2 snapshot documentation, **not verified current code**.

## 7. CHỨC NĂNG SẢN PHẨM CHI TIẾT

### 7.1 Public Explore / Cửu Đỉnh / Atlas

**Functional requirements:** FR-EXP-001 trang chủ di sản truy cập không đăng nhập; FR-EXP-002 danh sách 9 đỉnh với đúng tên và số motif đối chiếu; FR-EXP-003 atlas 162 có filter chủ đề/đỉnh/chữ Hán/nguồn; FR-EXP-004 motif detail 2D, 3D nếu có quyền, nhãn media provenance; FR-EXP-005 source detail rõ author/edition/page; FR-EXP-006 claim badges uncertainty và competing claims; FR-EXP-007 timeline with temporal precision; FR-EXP-008 Huế map precision flags; FR-EXP-009 historical stories sourced; FR-EXP-010 full-text search Unicode VI/Hán/EN, accent-insensitive nhưng không phá chữ Hán; FR-EXP-011 low-data switch; FR-EXP-012 QR/deep-link citation; FR-EXP-013 trails theo chủ đề; FR-EXP-014 browse indexed canonical entity IDs; FR-EXP-015 visible rights credits; FR-EXP-016 item/report correction workflow.

**Acceptance:** public không thấy draft/withdrawn, mỗi khẳng định thực sự mang citation, lỗi viewer không che mất ảnh 2D, không hiển thị nội dung AI seed là “verified”.

### 7.2 3D/AR/VR360

- Registry file `media_assets`: `sha256`, `uri`, `mime`, `format`, `size_bytes`, `poly_count`, `texture_dimensions`, `license`, `rights_proof`, `accuracy_grade`, `source_scan_id`, `photogrammetry_process`, `capture_date`, `coordinate_system`, `camera_alignment`, `quality_report`, `version`.
- Lazy load GLB theo capability/viewport, LOD 512→1k→2k theo thiết bị; load budget được đo thực nghiệm, cache CDN hash immutable.
- Mapping hotspot motif vào mesh/surface có coordinate revision ID; tọa độ từ file JSON Cao/Chương/Huyền và các file còn lại là candidate cho tới khi đối chiếu vật thể cụ thể.
- Camera controls, keyboard keyboard equivalents, touch/gesture, text alternatives, reset-view, high contrast hotspot.
- Markerless AR là progressive enhancement qua thiết bị hỗ trợ, fallback sang model viewer và ảnh tĩnh; không tự báo “AR available” trước capability check.
- Với media Sketchfab: `embed_only` khác `rehostable`; quyền AI extraction và commercial use tách riêng; revoke làm ẩn ngay.
- 3D derived reconstruction khác `measured_scan`; nếu nội suy mặt khuất phải ghi status. Có quality gates trên error/dimensions do chuyên gia 3D xác nhận.
- 360 panoramas, audio guide, map overlay: yêu cầu nguồn/copyright/caption/precision; high-res aerial map sensitive routes cần kiểm chính sách tiếp cận trước public.

### 7.3 Student LMS

- Guest → consent-aware account → onboarding → assigned class → lesson → ELLO steps → submit draft → feedback → revision → personal learning history.
- Các activity types: observe, image hotspot, evidence sorting, source comparison, CER response, map annotation, timeline ordering, quizzes, spaced-repetition flashcard, research task.
- FSRS chỉ phục vụ nhớ/ôn tập; không biến nhớ đúng thành đạt “historical reasoning”. Có study algorithm version và reset/export.
- Gamification: XP, badges, streak, quests, challenge; tắt bảng xếp hạng với học sinh nhỏ tuổi hoặc theo quy định trường; không phạt/chấm điểm học thuật vì thiếu thiết bị.
- Offline: download lesson pack được cấp phép, save drafts local encrypted, sync outbox idempotency, conflict review, delete on account removal.
- Certificate: chỉ ghi “course participation/completion” khi chưa được cơ quan có thẩm quyền phê duyệt chứng chỉ năng lực; không dùng `accredited` không có bằng chứng.

### 7.4 Teacher / classroom / authoring

- Course builder gắn kết chuẩn đầu ra chương trình, thời lượng 15/45/90 phút.
- Classroom enrollment bằng mã riêng TTL, assignments, group size, due dates, source packet freeze per assignment.
- Gradebook chia `completion`, `quiz_score`, `self_report`, `historical_reasoning_rubric`.
- Instructor analytics có learning progress, revision delta, source-use error themes; ẩn danh tổng hợp cho báo cáo.
- Moderator panel: approve/decline claims, side-by-side version diff, provenance of editor, rollback.
- Classroom 3D projected/teacher-led fallback nếu học sinh không có thiết bị.
- Peer review nếu cho phép: không hiển thị email hoặc nhận diện không cần thiết, anti-harassment moderation.

### 7.5 Source-governed AI Tutor

- Chỉ retrieval `published`, scoped theo nguồn/lesson/nhóm tuổi/giấy phép.
- Mỗi câu trả lời: `answer`, `supporting_claim_ids`, `source_locator`, `certainty`, `unsupported_notice`, `model_version`, `knowledge_snapshot_id`.
- Prompt injection protection không chỉ delimiter; dữ liệu nào cũng không được cấp role/system, tool invocation allowlisted và post-check external URLs.
- Khi thiếu nguồn: abstain, gợi nguồn để giáo viên xác minh; không bịa dữ liệu.
- AI giáo viên hỗ trợ gợi rubric/feedback nhưng không tự chấm điểm kết luận cuối đối với bài nghiên cứu khi chưa validated.
- Evaluation có 30 câu Q&A sẵn trong docs (không coi là toàn bộ benchmark), bổ sung adversarial multilingual, null source, conflicting sources, unknown object, DOI invalid, cross-scope, copyright, PII probes, jailbreak, uncertain text.
- Logging AI chỉ lưu tokenized metadata theo consent; không gửi raw thông tin học sinh cho third party nếu không có căn cứ/đồng thuận thích hợp.
- Avoid “zero-hallucination” banner; công bố kết quả benchmark với CI và manual audit.

### 7.6 Living Heritage / Artisan / Inquiry

- Public creator chỉ khi có `consented/verified_written_consent` + asset-specific permission; consent revoked -> fail-closed 404/no cache stale.
- Experience là `inquiry_only`, không instant booking, không “confirmed” trước partner decision.
- Partner inbox chỉ hiển thị inquiries thuộc `provider_id` server-side, không trust client filter.
- Request idempotency (UUID + payload hash), timeout retry with reconciliation; không synthetic success.
- Inquiry lifecycle `new → contacted → confirmed|declined → closed`, có transition allowlist + optimistic concurrency.
- No fake PII and no fake performance data in production; demo labeled and hosted separately.
- Revenue/support: funding in-kind khác doanh thu; công bố metric có `evidence_id`, `measurement_window`, `verification_status`.
- Privacy: retention có thông báo, consent receipt và erasure feasibility; audit log không vô ý giữ PII vĩnh viễn.

### 7.7 CALL extension (conditional)

Hướng riêng chỉ mở khi có bài học ngôn ngữ thực sự: bilingual annotations; chữ Hán có phiên âm/định nghĩa/giải thích từ; English-for-heritage reading; task comprehension/translation/vocabulary; feedback phát âm nếu được kiểm định; chuyên gia ngôn ngữ phê duyệt; pre/post language skills nếu muốn tuyên bố hiệu quả. Dữ liệu về tư duy lịch sử không được đổi nhãn thành dữ liệu CALL.

---

