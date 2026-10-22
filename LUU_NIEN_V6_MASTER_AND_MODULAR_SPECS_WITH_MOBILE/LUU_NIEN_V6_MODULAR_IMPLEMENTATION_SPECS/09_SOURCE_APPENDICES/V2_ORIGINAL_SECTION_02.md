# V2 original archival technical chapter — SECTION_02

> Extracted without rewriting from V2 snapshot documentation, **not verified current code**.

## 2. AUDIT HIỆN TRẠNG — SOURCE OF TRUTH TRONG ZIP

### 2.1 Topology và inventory đã đối chiếu

| Bộ phận | Thực tế từ snapshot | Đường dẫn bằng chứng | Trạng thái |
|---|---|---|---|
| Frontend | Next.js 15, React 19, TS/JSX, Zustand, React Three Fiber, Tailwind, Leaflet | `frontend/package.json`, `frontend/src/app`, `frontend/src/components` | `[CODE]` |
| Rust API | Axum 0.7 gateway + các routes native; dispatcher mode và Python fallback | `backend-rust/src/main.rs`, `backend-rust/src/gateway.rs`, `backend-rust/config/route-modes.toml` | `[CODE]` |
| Python API | FastAPI modular backend, SQLAlchemy, services đa domain | `backend/main.py`, `backend/app.py`, `backend/routers`, `backend/services` | `[CODE]` |
| Mobile | Flutter/Dart, Riverpod, go_router, Dio, model_viewer_plus, offline libs | `mobile/pubspec.yaml`, `mobile/lib` | `[CODE]` |
| Data Cửu Đỉnh | 9 JSON × 18 mục = 162 JSON records; 162 JPG theo bộ sưu tập | `data/05_Data_*.json` ... `13_Data_*.json`, `ban-duc-noi/` | `[STATIC-VERIFIED]` |
| Nội dung Huế | inventory 14 UNESCO component và child/craft seed | `data/heritage-hue/inventory.unesco-14.yaml`, `data/heritage-hue/*.yaml` | `[DATA]`; chưa verify sử liệu độc lập |
| Core historical model | entity/source/claim/binding/relation/geography/asset/story/collection | `backend/history_models.py` | `[CODE]` |
| RBPC business model | place/source/media/story/creator/experience/inquiry/audit | `backend/models_rbpc.py`, `backend/routers/rbpc.py` | `[CODE]` |
| 3D GLB | các độ phân giải Cao Đỉnh; duplicate giữa web/backend/mobile/models_upload | `frontend/public/assets/models`, `backend/assets/models`, `models_upload`, `mobile/assets/models` | `[DATA]` |
| Learning | lesson, quiz, progress, FSRS, gamification, classroom; `/learn` có roadmaps | `backend/models.py`, `backend/routers/history_learning.py`, `frontend/src/app/learn/page.tsx` | `[CODE]`; chưa xác minh tất cả theo sáu bước |
| AI | `history_tutor.py`, `rbpc_ai.py`, nhãn certainty + kiểm tra citation trong code | `backend/services/*`, `backend/routers/history_tutor.py` | `[CODE]`, benchmark runtime chưa chạy |
| Test & CI | pytest, Playwright, Vitest, Rust unit tests (mã), GitHub workflow | `tests/`, `frontend/e2e/`, `backend-rust/src/*`, `.github/workflows` | `[TEST-CODE]` |
| RBPC records | 40 markdown về quyền, nguồn, business, handoff, evaluation | `docs/rbpc/*.md` | `[DOC-CLAIM]`, KHÔNG là chứng thực pháp lý hoặc hiệu năng |
| Survey raw | không thấy bản xuất Google Forms cấp người trong ZIP | dò `backend`, `frontend/src`, `migrations`, `data`, `scripts` | `[NEED-PROOF]` từ tài liệu nhóm giữ bên ngoài |

### 2.2 Những điểm tốt cần bảo tồn (Do Not Rebuild Blindly)

1. Đã có hai lớp model lịch sử tương đối chi tiết (`HistoricalClaim`, `HistoricalClaimSource`, `HistoricalSource`) có trạng thái kiểm chứng, độ chắc chắn, nguồn, loại nguồn, quan hệ; ưu tiên *mở rộng* thay vì viết bảng thứ ba tương tự.
2. RBPC heritage models có trường `editorial_status`, `content_scope`, `accuracy_grade`, rights/consent; giữ tách scope `RBPC_HUE` với dữ liệu dự án Cửu Đỉnh và module khác.
3. Rust gateway có cơ chế rollout `native/gateway`, bảo toàn đường di chuyển an toàn từng nhóm endpoint; giữ mô hình strangler có contract tests.
4. Có UI tình trạng chứng cứ (`EvidenceStatus`, `EpistemicBadge`, `CitationDrawer`), CulturalBridgePanel, creator card, partner inbox và inquiry form; sử dụng lại với audit accessibility.
5. Có `lesson_plan_45m.json`, `fieldwork_worksheet.json`, các dữ liệu nguồn mở rộng, cho phép nhanh chóng hoàn thiện ELLO đầu tiên.
6. Có 162 ảnh bản đúc nổi và 162 item seed ban đầu; đây là *inventory khởi điểm*, không phải dữ liệu đã chứng thực.
7. Có script dữ liệu, bộ test đa dạng (security, RBPC, history, ownership, import, migrations) và tài liệu hiện trạng; giữ lại, kết hợp với gates tự động mạnh hơn.
8. Có tính đến quyền model 3D và quyền nghệ nhân; phải chứng minh bằng bản ghi/giấy phép cụ thể thay vì chỉ dựa trên status trong documentation.

### 2.3 FINDINGS — ưu tiên theo Severity × Likelihood × Impact

**AU-001 [P0/BLOCKER — tính đúng di sản]: `data/05_Data_*.json` đến `data/13_Data_*.json`.** 162/162 mục có `is_ai_generated=true`, 0/162 có trường nguồn trực tiếp `sources`, `source_url`, `source_ids` hoặc `bibliography`; 162/162 có bài quiz nhưng không gắn nguồn tại cấp câu hỏi. Kiểm tra tự động đã xác nhận. Ví dụ item đầu `urn_cao_dinh_01` có `name_han_nom: "艇"` trong khi tên hiển thị “Cao Đỉnh”; phép đối chiếu chữ Hán cần chuyên gia, đây là **cờ đỏ kiểm tra**, không tự sửa dựa vào suy đoán. Item đầu của từng đỉnh còn mang tên *đỉnh* nên cần xác minh mapping liệu 162 mục có đúng 162 hình đúc nổi hay trộn nhãn/biểu tượng urn. **Tác động:** không thể đưa toàn bộ corpus seed vào chế độ “verified” hoặc dùng làm căn cứ AI/đánh giá học sinh. **Fix:** import vào staging `AI_DRAFT`, đối chiếu ID–ảnh–bản kiểm kê chuẩn, bổ sung claim–source–locator, chuyên gia duyệt, hard gate publish.

**AU-002 [P0/BLOCKER — tính trung thực giao dịch]: `frontend/src/lib/rbpc/inquiries.ts`, hàm `submitInquiryToApi`.** Khi API 404/network error, client tự tạo reference/statusToken và trả `status: "new"` cùng thông điệp “Yêu cầu đã được ghi nhận ... liên hệ ... trong vòng 24 giờ”, dù chưa có bằng chứng server đã nhận inquiry. **Fix:** production phải throw lỗi / hiển thị “chưa gửi thành công”, không tạo booking giả; `demo` hiện rõ nhãn và namespace `demo_*`; thêm E2E thử tắt API, khẳng định không có success toast.

**AU-003 [P0/HIGH — dashboard dữ liệu giả]: `frontend/src/lib/rbpc/inquiries.ts` và `frontend/src/app/rbpc/partner/page.tsx`.** `fetchPartnerInquiries()` trả `SEED_PARTNER_INQUIRIES` khi API thiếu/fail hoặc không có dữ liệu; PartnerDashboard khởi tạo chính bằng seed. **Fix:** demo/production hard switch; server trả empty list đúng, lỗi API hiện lỗi; không trình bày số liệu demo như doanh thu/inquiry thực; kiểm thử authorized-empty/401/403/timeout.

**AU-004 [P0 — database evolution]: `.github/workflows/deploy.yml` và `migrations/versions/*`.** Deploy thực hiện `alembic upgrade head || true`, cho phép bỏ qua thất bại migrations và vẫn báo deploy thành công. Static graph của 71 revision file có **26 terminal revisions** theo `revision/down_revision` khai báo (con số không thay thế lệnh `alembic heads`, cần kiểm tra thực tế khi đủ dependencies). Có ít nhất hai nhánh cùng nối từ revision `0053`: `0054_imperial_city_core` và `0054_rbpc_heritage_schema`. **Fix:** xóa `|| true`; audit chain bằng Alembic CLI; viết merge revision hợp lệ (không ép tuần tự trái phép), backup/restore test; pipeline dừng khi nhiều heads chưa giải quyết. **Không tự merge schema trước DB snapshot.**

**AU-005 [P1/HIGH — rate limit/proxy trust]: `backend/app.py`, `backend/routers/rbpc.py`, `backend-rust/src/routes/auth.rs`.** Hàm lấy IP dùng phần đầu `X-Forwarded-For` nếu có; nếu không ràng buộc trusted proxy và Nginx overwrite headers, client có thể giả mạo khóa rate limit. Python rate limiter giữ state trong dict theo process, không có tính nhất quán nhiều worker/replica. **Fix:** trusted proxy chain/real IP ở edge + limiter tập trung Redis/edge cho public mutation và auth, CAPTCHA/adaptive defenses khi cần; test forged header.

**AU-006 [P1/HIGH — CI thiếu branch + migration gate]: `.github/workflows/ci.yml`, `.github/workflows/deploy.yml`.** CI hiện trigger `push/pull_request` vào `main`, không bao phủ mọi push trên feature branch; branch mới có thể không có kết quả build độc lập. `.github/workflows/deploy.yml` có `skip_tests` input; cần protected environments/approvals. **Fix:** PR required check, branch policy, tests Python/Rust/Node/Flutter, migration graph validation, secret scanner, SBOM + artifact signing; không cho deploy trên branch experiment.

**AU-007 [P1 — AI groundedness là mục tiêu, không phải bảo đảm toán học]: `backend/services/history_tutor.py`, `backend/services/rbpc_ai.py`, `docs/rbpc/AI_EVAL.md`.** Code có delimiter, citation checker, verified-only retrieval và deterministic fallback. Tuy vậy, tài liệu gắn nhãn “zero-hallucination/100% verified” là claim riêng của tài liệu; chưa chạy benchmark độc lập trong phiên audit này. **Fix:** provenance coverage, claim-level entailment, multilingual adversarial set, measured acceptance/abstention metrics, human gold labels, release threshold, real deployed router tests; không dùng ngữ nghĩa “zero error”.

**AU-008 [P1 — 3D coverage/asset provenance]: `frontend/public/assets/models`, `backend/assets/models`, `mobile/assets/models`, `models_upload`.** Snapshot có GLB Cao Đỉnh với LOD 512/1k/2k, chưa thấy đủ mô hình 3D chín đỉnh tương ứng toàn bộ 162 hình; một số file lặp lại ở nhiều nơi. **Fix:** asset registry, SHA-256, single object storage origin, CDN renditions/LODs, mesh measurement/error/version/license per file; 2D fallback luôn sẵn có. Không tuyên bố có 3D chất lượng kiểm chứng cho đủ 9 đỉnh.

**AU-009 [P1 — khả năng tái lập khoa học]: các bài Q2/HCMUS và repo.** Chưa thấy bộ Google Forms gốc, bản xuất dữ liệu học sinh, questionnaire version, sampling metadata, mapping từ item tới published tables trong source ZIP. **Fix:** research vault tách riêng; import ẩn danh, validate 1502, gộp câu trả lời minh bạch; công khai aggregate reproducibility scripts, không phát tán PII.

**AU-010 [P1 — xung đột thông điệp trạng thái thực tế]: `frontend/src/app/learn/page.tsx`, `frontend/src/lib/rbpc/learnModules.ts`.** `/learn` hiển thị cả module available và roadmap; UI có logic phân biệt status nhưng cần E2E bảo đảm không gọi mục roadmap là môn học đã kiểm chứng/cấp chứng chỉ. **Fix:** trạng thái `available_in_repo`, `pilot_verified`, `research_tested`, `roadmap_only` có định nghĩa audit được; khóa chứng chỉ chưa có phê duyệt.

**AU-011 [P1 — privacy of minors/partners]: `backend/models.py`, `backend/models_rbpc.py`, `frontend/src/lib/rbpc/inquiries.ts`.** Hệ thống lưu dữ liệu tài khoản học sinh và liên hệ đối tác. Dữ liệu người học, phản hồi nghiên cứu và liên hệ du khách phải có lawful basis, retention, deletion, role boundaries và masking; tham chiếu token lưu `localStorage` cần đánh giá threat model cụ thể. **Fix:** data classification, encryption at rest/in transit, rights workflows và privacy test.

**AU-012 [P2 — kiến trúc hai backend và monolith legacy]: root `main.py`, `models.py`, `schemas.py`; `backend/main.py`, Rust routes.** Snapshot chứa file root khổng lồ bên cạnh backend modular, Rust strangler và mobile. Tăng nguy cơ drift tài liệu/cấu trúc; cần xác định entrypoint duy nhất bằng runtime config và dependency graph. **Fix:** architecture inventory động, contract parity và tiến trình ngừng root legacy có kiểm chứng; không xóa file theo cảm giác.

**AU-013 [P2 — giới hạn test snapshot]:** Python source compilation đạt 390/390; JSON parse đạt 83/83. Chạy `pytest -q tests/backend/test_rbpc_endpoints.py tests/unit/test_rbpc_ai.py` bị chặn ở import `backend.db` do thiếu `psycopg` (`ModuleNotFoundError`), exit 4; **không suy ra bài test pass/fail**. Môi trường audit không có `cargo`, `flutter` hoặc frontend `node_modules`; chưa thể khẳng định Rust/Flutter/Next builds đạt. **Fix:** tái chạy trong dev container hoặc CI có pin deps.

**AU-014 [P2 — tính nhất quán claim/UNESCO/rights]: `data/heritage-hue/*.yaml`, `docs/rbpc/HERITAGE_FACT_CHECK_LEDGER.md`, `docs/rbpc/CONTENT_RIGHTS.md`.** Tài liệu có policies và claim “verified”, nhưng cần liên kết với nguồn có locator, bản scan nguồn, giấy phép, người duyệt và mốc thời gian; các quyền Sketchfab phụ thuộc tác giả và điều kiện cụ thể, không dựa vào loại giấy phép ghi trong narrative. **Fix:** evidence ledger có file proof, expiration/withdrawal monitor, no-public-if-unclear.

**AU-015 [P2 — tính toán/giá trị khảo sát]:** nguồn giấy của bài Q2 báo 1.502, sở thích học liệu 1.350+1.250+1.220+686=4.506=1.502×3; cần đối chiếu Google Forms nếu câu cho chọn tối đa 3. Câu awareness 544 có thể khác nghĩa với kênh SGK 812; không gọi mâu thuẫn trước khi kiểm nguyên văn câu hỏi. **Fix:** research audit pipeline làm rõ item wording, skip logic, response mode, denominator.

**AU-016 [P0/HIGH — media rights/public 3D flag]: `backend/routers/heritage.py`, `_has_cleared_3d_asset`, heritage list `has_3d` subquery, `/3d` listing.** Các điều kiện hiện tại chỉ loại `embed_permission_status == "blocked"` và `commercial_use_status == "blocked_nc"`, không đòi `embed_permission_status == "permitted"` hoặc `commercial_use_status == "permitted"`. Vì vậy asset `needs_rights_review`, `author_contacted`, `unreviewed`, `requires_custom_grant` có nguy cơ lọt điều kiện `has_3d=true`/endpoint `/3d` nếu các điều kiện khác thỏa. **Fix:** định nghĩa predicate thống nhất fail-closed `is_public_view_allowed(asset, purpose)`; chỉ approved embed/self-host rõ proof và rights status, tách accuracy vs permission, áp dụng ở SQL và serializer; hồi quy với từng enum negative. Không mặc định visibility = phép phân phối hoặc phép thương mại.

**AU-017 [P1 — Rust DB readiness]: `backend-rust/src/main.rs`, `db::pool(&settings).await.ok()`.** Ứng dụng tiếp tục khởi động với `pool: None` nếu DB pool setup thất bại và một số route trả 503; có thể hữu ích cho degraded-mode nhưng không phù hợp nếu hệ thống báo readiness healthy cho deployment yêu cầu DB. **Fix:** tách `/livez` (process alive) và `/readyz` (DB reachable, schema compatible, required workers), không đưa pod/container vào rotation trước khi readiness pass; chủ động fail closed đối với business mutations.


### 2.4 Audit coverage: Done / Not Done

- **Đã làm:** ZIP file inspection; inventory; đọc tài liệu README/spec/đa số nhóm RBPC; đọc cross-section source code Python/Rust/frontend/mobile/config; kiểm static 162 JSON–162 JPG–9 groups; kiểm types/coverage nguồn; parse migration dependencies; đọc CI; compile Python + validate JSON; thử pytest RBPC.
- **Chưa làm:** checkout có `.git`; đo runtime trên DB thực; deploy/penetration test ngoài thực địa; chạy Rust tests, Flutter tests, Node test; validate toàn bộ claim lịch sử bằng sách gốc; kiểm giấy phép hình ảnh và các văn bản consent; kiểm CSV Google Forms; so hash 3D với scan gốc; verify live infrastructure; scan dependencies online/CVE. Phải giữ trạng thái `UNVERIFIED` cho phần này.

---

