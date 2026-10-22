# V2 B1: source-derived engineering detail

> **Nguồn:** Trích không lược bỏ từ `LUU_NIEN_V5_PRODUCTION_COMPLETION_AND_NEW_FEATURES_GEMINI_FLASH_FULL_MASTER_SPEC.md` (`V2.B1`). **Nhận định mã nguồn trong V5 là audit tĩnh, chưa chứng minh production hoạt động.**
> **Dùng cho Gemini:** Chỉ mở tài liệu này với một ticket và tối đa 3–8 file source tương ứng.

## B1. ARCHITECTURE V2 — SỰ TƯƠNG TÁC GIỮA CÁC CONTEXT

### B1.1 Ranh giới miền và chủ sở hữu dữ liệu

| Bounded context | Nguồn chân lý được chỉ định | Có quyền ghi | Chỉ đọc/đồng bộ từ nơi khác | Không được làm |
|---|---|---|---|---|
| Heritage Registry | PostgreSQL `historical_entities`, urn/motif mapping | curator/ingestion | explore, map, 3D, lessons | tạo hiện vật từ suy diễn chatbot |
| Evidence Registry | source, locator, claim, source binding, review | historian/editor | ELLO, AI, tourism | AI tự đưa claim chưa duyệt lên public |
| Digital Asset | asset registry + immutable object storage | media curator | UI, XR, article renderer | coi có URL = có quyền thương mại |
| Pedagogy | ELLO, objectives, tasks, rubric, revisions | teacher/editor | student runner, research | chấm “đúng” bằng số lần chạm/click |
| Student Progress | enrollment, attempts, feedback, mastery | learning service | student, teacher scope, analytics | ghi PII vào public telemetry |
| Living Heritage | creator consent, workshops, stories, inquiry | consent manager/partner | visitor UI | tự động xác nhận booking khi inquiry mới tạo |
| AI Retrieval | published claim/source read index | indexing pipeline | AI chat | lưu bản AI viết như nguồn lịch sử độc lập |
| Research Vault | study protocol, survey, pseudonymized analysis | research custodian | aggregate export | public API trả dữ liệu định danh học sinh |
| Auth/RBAC | identities, sessions, role assignments | identity service | mọi module | dùng role client làm nguồn xác thực |

**Quyết định triển khai:** không yêu cầu microservices ngay. Có thể giữ FastAPI + Rust gateway + Next.js theo “modular monolith + gateway”, nhưng domain modules phải có owners, schema contracts, CI parity và explicit dependencies. Tách dịch vụ vật lý chỉ khi có nhu cầu vận hành thật và đội đủ khả năng duy trì.

### B1.2 Dependency policy

- `heritage` phụ thuộc `source/evidence` để publish; `source` không phụ thuộc LMS.
- `pedagogy` chỉ link canonical entity/claim/asset IDs; không copy nguyên văn claim làm authority.
- `research` chỉ lấy dữ liệu qua snapshot có kiểm soát, không query trực tiếp production vào notebook tự phát.
- `AI` sử dụng published claim snapshot; LLM không có quyền gọi content-write/publish APIs.
- `RBPC` dùng identity và evidence theo content scope, nhưng mất RBPC không làm gián đoạn LMS.
- Frontend không quyết định trạng thái pháp lý của asset; API cung cấp field `capabilities` đã được server kiểm quyền.

### B1.3 Context propagation cho HTTP và background jobs

**TARGET** headers: `X-Request-ID`, `traceparent`, `Accept-Language`, `X-Client-Version` (optional), `Idempotency-Key` (mutation cần idempotency). Không log access token, email học sinh, số điện thoại khách, prompt chứa dữ liệu cá nhân. Phân biệt public correlation ID và internal trace IDs.

**Command lifecycle**: validate input -> authenticate -> authorize per resource -> DB transaction -> append outbox event -> commit -> worker tiêu thụ event -> reconcile -> expose read projection. Không phát event trước commit rồi hiển thị state khác DB.

### B1.4 Background workers và outbox

Events dự kiến: `heritage.claim.reviewed.v1`, `heritage.asset.rights_changed.v1`, `pedagogy.lesson.published.v1`, `learning.attempt.submitted.v1`, `rbpc.inquiry.created.v1`, `rbpc.creator.consent_withdrawn.v1`, `research.dataset.imported.v1`. Mỗi event cần `event_id`, `schema_version`, `occurred_at`, `aggregate_id`, `aggregate_version`, `trace_id`, `payload` cho phép. Event consumer xử lý at-least-once, bắt buộc idempotent, dead-letter sau retry giới hạn, có replay procedure. Dữ liệu liên hệ khách không xuất hiện trong event public.

### B1.5 Luồng yêu cầu và phân xử backend Rust/FastAPI

1. Router Rust tra `route-modes.toml` (existing) để quyết định native hay Python fallback.
2. Mỗi route có **một owner canonical** trong registry dự kiến; không tạo hai implementation không có parity test.
3. Gateway chuyển tiếp principal, scope, request-id và timeouts theo allowlist; không tin `X-User-Role` từ client.
4. Khi fallback Python không khả dụng, trả 503 có `request_id`; tuyệt đối không biến thành success giả.
5. Circuit breaker mở/đóng ghi metric; không làm thay đổi semantics của giao dịch.
6. Contract CI chạy cùng bộ fixtures đối với Rust native và Python cho route chuyển đổi; phải so semantic output, không chỉ status 200.

**Target API versioning:** REST `/api/v1/*` hiện có; schema mới dạng `/api/v2/*` nếu phá tương thích. Chỉ thêm field optional trong v1, không đổi nghĩa của `has_3d`, `status` hoặc `score` âm thầm. Deprecation tối thiểu một chu kỳ release có báo cáo clients thực tế.

### B1.6 ADR cần ký quyết định trước khi code

| ADR | Quyết định cần ký | Phương án thay thế | Điều kiện chọn |
|---|---|---|---|
| ADR-101 | PostgreSQL authoritative relational+JSONB | graph DB riêng | chưa đủ use case cần graph DB, quan hệ claim-source có thể kiểm bằng JOIN |
| ADR-102 | One immutable object store + CDN renditions | copy GLB 4 nơi | provenance, cache, quyền và dedup phải kiểm được |
| ADR-103 | Historical claims được version | sửa đè row | cần tái lập bài học và công bố |
| ADR-104 | LMS essay chấm bằng human/rubric trước, AI gợi ý | AI chấm kết quả chính | chưa có validation/ethics để AI quyết định điểm chính thức |
| ADR-105 | Customer inquiry never simulated in production | fallback client giả | chống xác nhận sai và gian lận thương mại |
| ADR-106 | Research data warehouse isolated | query live DB trực tiếp | bảo vệ người chưa thành niên, repeatable release |
| ADR-107 | Server-side rights predicate reused | filter phía client | fail-closed, chống direct URL bypass |
| ADR-108 | 2D baseline accessibility | chỉ 3D/AR | không phụ thuộc thiết bị và bandwidth |

---

