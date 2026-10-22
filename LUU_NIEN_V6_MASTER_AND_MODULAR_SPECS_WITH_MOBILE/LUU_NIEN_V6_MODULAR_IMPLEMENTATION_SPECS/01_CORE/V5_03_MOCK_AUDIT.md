# V5.3 — MOCK_AUDIT

> **Nguồn:** Trích không lược bỏ từ `LUU_NIEN_V5_PRODUCTION_COMPLETION_AND_NEW_FEATURES_GEMINI_FLASH_FULL_MASTER_SPEC.md` (`V5.3`). **Nhận định mã nguồn trong V5 là audit tĩnh, chưa chứng minh production hoạt động.**
> **Dùng cho Gemini:** Chỉ mở tài liệu này với một ticket và tối đa 3–8 file source tương ứng.

## V5.3 — SỔ PHÁT HIỆN CỤ THỂ VÀ LUẬT ĐÓNG MOCK/SKELETON

**Quan trọng:** Đây là code-observation từ ZIP và rủi ro cần khắc phục, không phải kết luận rằng toàn bộ API backend tương ứng hiện đang lỗi. Kết quả runtime và quyền truy cập cần kiểm chứng ở môi trường disposable/staging. Dấu `P0` có nghĩa không được bật journey liên quan tại production trước khi sửa.

| ID | Mức | Bằng chứng mã nguồn | Hiện tượng/rủi ro | Yêu cầu đóng | Gate |
|---|---|---|---|---|---|
| GAP-001 | P0 | `frontend/src/lib/rbpc/inquiries.ts` ~337–369 | `submitInquiryToApi` tự sinh reference/token và thông báo đã ghi nhận khi 404/network error | Bỏ fabricated success. Trả typed error; nếu offline có outbox riêng và `pending_sync` rõ ràng, không hứa đối tác nhận | E2E backend unavailable -> không tạo “đã ghi nhận” |
| GAP-002 | P0 | Cùng file ~375–416 | `fetchInquiryStatusByToken` có thể khớp dữ liệu seed nếu API lỗi | Tra DB thật; token vô hiệu -> 404/410 đúng, không lộ PII | invalid token never maps to fake customer |
| GAP-003 | P0 | Cùng file ~420–460 | `fetchPartnerInquiries` trả `SEED_PARTNER_INQUIRIES` khi thiếu dữ liệu, lỗi hoặc unauthenticated | 200 empty list -> UI empty; 401/403/5xx -> error/retry; seed chỉ nằm trong demo DB | 0 fake inquiry on fresh tenant |
| GAP-004 | P0 | Cùng file ~462–484 | `updatePartnerInquiryStatusApi` swallow backend reject | Propagate typed failure; optimistic rollback; audit log server | 403/409/500 UI never persists changed status |
| GAP-005 | P0 | `frontend/src/app/rbpc/partner/page.tsx` ~90–145 | Dashboard preloads seed; empty list reverts seed | initial state `[]`, skeleton loading, explicit empty & error; provider server-scoped | tenant without inquiry sees 0 records |
| GAP-006 | P0 | `frontend/src/lib/imperial/map-api.ts` ~383–474 | create/update/delete annotation fabricate success on API failure | Remove fake returns; offline draft outbox separate; optimistic concurrency 409 | network down cannot appear published/saved |
| GAP-007 | P0 | `frontend/src/lib/imperial/submissions-api.ts` 1–250+ | Mock student work, grades and personal names seeded into localStorage | Real submissions, gradebook, RBAC, audit; demo fixtures isolated; privacy purge | account A cannot see/change account B; no fake names in prod |
| GAP-008 | P0 | `backend/services/heritage_import.py` ~1695–1720 | Import `RbpcClaimEvidence` với `review_status="verified"` khi tạo claim | `draft_pending_review`; evidence locator & human approval trước publish | import unsupported claim remains unverified |
| GAP-009 | P0 | `data/*Data*Dinh.json` | 162/162 `is_ai_generated=true`; 0 source field trên seed raw | Evidence-backed ETL, mapping canonical + citations, Hán–Nôm verification, safe publication | public listing only approved records |
| GAP-010 | P1 | `mobile/lib/routing/app_router.dart` ~270–281, ~505+ | Quests route trỏ `QuestsPlaceholder` & `QuestDetailPlaceholder`; class placeholder khác còn tồn tại | Thay active route bằng feature hoàn chỉnh; xóa/ẩn unreachable placeholders | navigation smoke on iOS/Android |
| GAP-011 | P1 | `frontend/src/lib/imperial/map-api.ts` ~70–370, 500+ | GET có nhiều `FALLBACK_*`; read-only fallback có thể che database outage | Static canonical 2D được đánh dấu fallback kỹ thuật; never substitute fictional data | outage presents retry/verified static only |
| GAP-012 | P1 | `backend/routers/live.py` ~1601–1922 | `used_mock` xuất hiện ở các nhánh Live AI | phân biệt safety fallback vs AI giả; trả provenance `provider_mode`; không ghi “AI live” nếu mock | monitor live mode and fallback |
| GAP-013 | P1 | `frontend/src/lib/imperial/submissions-api.ts` | Điểm/rubric và `graded_by` do client/localStorage định | Server authority, rubric version, immutable review records | can't forge grade with browser devtools |
| GAP-014 | P1 | `frontend/src/lib/imperial/map-api.ts` ~484–535 | publish/export có fallback trả dữ liệu local | Publish atomic DB snapshot có duyệt và error contract | export exactly matches published revision |
| GAP-015 | P1 | `docs/rbpc/FINANCIAL_ASSUMPTIONS.md`, `CUSTOMER_VALUE_METRICS.md` | Business plan có dự báo 1.100 completed, time saved, conversions | Tag assumption/target; chỉ dùng analytics production + đối tác xác nhận để tạo traction | pitch metrics evidence registry |
| GAP-016 | P1 | `frontend/src/lib/imperial/v51-api.ts`, `fallback-data.ts` | Nhiều fallback/mocks ở nội dung, hình ảnh, API | lập inventory từng exported function, default fail-closed khi mutation; browse graceful only with verified local asset | zero fake-success production scan |
| GAP-017 | P1 | `frontend/src/lib/rbpc/inquiries.ts` ~283–332 | Opaque inquiry token tồn trong `localStorage` browser | đánh giá threat model XSS, chỉ giữ opaque token cần thiết với TTL/clear, không contact PII | security tests + retention |
| GAP-018 | P2 | `docs/rbpc/AI_EVAL.md` | Benchmark ghi `zero hallucination` như tuyệt đối | đổi thành measurable groundedness policy; test citation faithfulness và abstention | benchmark with measured rates |

### 3.1. Trạng thái hiển thị thống nhất

`loading` / `empty` / `ready` / `offline_cached_verified` / `pending_sync` / `sync_failed` / `conflict` / `unauthorized` / `forbidden` / `unavailable` / `review_required` / `success_confirmed`. Không hiển thị `success_confirmed` nếu response backend không xác nhận kết quả đã commit. Frontend phải phân biệt lỗi mạng, 401/403, 404, 409 và 429. Retry mutation cần idempotency key + optimistic rollback + no duplicate push.

### 3.2. Production mock policy

- Mock tồn tại trong `*.test.*`, storybook, docs, local fixture -> ALLOWED.
- Mock tồn tại trong runtime code nhưng chỉ truy cập qua `demo.<domain>` / `DEMO_MODE=true` và DB demo -> ALLOWED WITH CONTROLS.
- Mock trả lên production như người thật, lịch thật, số liệu học tập thật, nguồn thật, thanh toán thật -> BLOCKED.
- Read-only verified static 2D thay cho WebGL lỗi -> ALLOWED WITH LABEL.
- AI abstention có giải thích và hiển thị nguồn thực -> ALLOWED.
- AI tự thêm `[SOURCE]` không truy xuất được -> BLOCKED.

**Chỉ số release:** `production_mock_success_count = 0`, `fake_inquiry_count=0`, `fake_student_grade_count=0`, `fake_citation_count=0` trên các bài test lỗi/golden fixture. Không được hiểu các counter bằng 0 do instrumentation chưa bật là đạt.

