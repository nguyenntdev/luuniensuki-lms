# V3.C6: research factory deep specification

> **Nguồn:** Trích không lược bỏ từ `LUU_NIEN_V5_PRODUCTION_COMPLETION_AND_NEW_FEATURES_GEMINI_FLASH_FULL_MASTER_SPEC.md` (`V3.C6`). **Nhận định mã nguồn trong V5 là audit tĩnh, chưa chứng minh production hoạt động.**
> **Dùng cho Gemini:** Chỉ mở tài liệu này với một ticket và tối đa 3–8 file source tương ứng.

## C6. Contract API + Admin Console để vận hành 120 vai trò subagent

### C6.1. Admin endpoints `[TARGET]` — namespace `/api/v1/admin/research-factory`

> Tất cả endpoint yêu cầu authentication, CSRF protection cho cookie sessions (nếu có), role authorization theo object, rate limit và append-only audit. Các endpoint **không có trong branch hiện tại** cho đến khi đội dev triển khai và OpenAPI ghi nhận. Tên và HTTP verbs dưới đây là **đặc tả đề xuất**, không tuyên bố code hiện có.

| Method | Path | Request payload chính | Response | Vai trò |
|---|---|---|---|---|
| GET | `/inventory` | `scope, urn_id, status` | 9×18 identity/coverage | curator, editor |
| POST | `/runs/dry-run` | `scope, subject_ids, release, budget` | execution plan, warnings | research_admin |
| POST | `/runs` | manifest, `Idempotency-Key` | `202 {run_id,status}` | research_admin |
| GET | `/runs/{run_id}` | - | progress, phase status, blocking reasons | researcher/editor |
| POST | `/runs/{run_id}/cancel` | reason, expected version | canceled or conflict | research_admin |
| POST | `/runs/{run_id}/retry` | phase, slots, reason | new attempt/lease | research_admin |
| GET | `/runs/{run_id}/agents` | `phase, wave, status` | exactly 10 role/job records per wave | researcher |
| GET | `/runs/{run_id}/manifest` | - | immutable config input/output hashes | editor |
| GET | `/runs/{run_id}/costs` | group_by phase/agent | spent+estimated vs budget | researcher/admin |
| GET | `/runs/{run_id}/blocked` | - | active blockers and remediation | editor |
| GET | `/sources/candidates` | `subject, stage, provider` | provenance candidates | research_editor |
| POST | `/sources/{source_id}/rights-decision` | grant evidence, allowed usage | signed rights decision | legal/rights reviewer |
| GET | `/sources/{source_id}/snapshots` | - | redacted immutable versions | source reviewer |
| GET | `/passages/{passage_id}` | - | locator, displayed excerpt if rights allow | evidence reviewer |
| POST | `/passages/{passage_id}/review` | score, correction, version | review audit | expert_transcriber |
| GET | `/claims/{claim_id}/evidence-graph` | - | supporting/contradicting passages | historian |
| POST | `/claims/{claim_id}/expert-review` | status, reason, version | signed review | historical expert |
| GET | `/drafts/{draft_id}` | `locale, format` | entire structured full draft + citations | editor |
| POST | `/drafts/{draft_id}/revise` | diff patch, expected revision | new draft revision | editor |
| GET | `/drafts/{draft_id}/qa` | - | ten QA agents findings + deterministic checks | reviewer |
| POST | `/drafts/{draft_id}/approve` | signature, scope, decision | approval record | authorized human reviewer |
| POST | `/drafts/{draft_id}/reject` | reason, claim IDs | rejected state and backlog | authorized human reviewer |
| POST | `/releases/preflight` | draft IDs, run ID | diff, rights/a11y/API/index validation | publisher |
| POST | `/releases` | signed preflight hash, idempotency key | prepared release; published only after atomic swap | publisher |
| POST | `/releases/{id}/rollback` | previous version, reason, signature | active release pointer reverted | admin+reviewer |
| GET | `/coverage/reliefs` | filter urn/status/gap | 162 row coverage matrix | curator/editor |
| GET | `/audit/events` | cursor, resource_id, event | redacted append-only audit | audit_reader |
| GET | `/research-exports` | paper, release snapshot, scope | archive index (no student PII) | research_admin |

### C6.2. API tạo run — ví dụ hợp đồng Request

```http
POST /api/v1/admin/research-factory/runs
Authorization: Bearer <scoped-admin-token>
Idempotency-Key: <uuid>
Content-Type: application/json
```

```json
{
  "mode":"STRICT_PRODUCTION",
  "content_scope":"NINE_URNS",
  "subject_selector":{"type":"URN","id":"<canonical-urn-uuid>"},
  "source_release_id":"<approved-policy-uuid>",
  "target_locales":["vi-VN","en-US"],
  "audiences":["secondary_history","museum_public"],
  "enabled_phases":["P00","P01","P02","P03","P04","P05","P06","P07","P08","P09","P10","P11"],
  "concurrency":{"slots_per_phase":10,"max_active_phases_per_run":1},
  "budgets":{"max_llm_tokens":100000,"max_total_cost_usd":25.0,"max_sources":50},
  "policy_flags":{"require_two_human_approvals":true,"disable_unapproved_publication":true}
}
```

**Nhắc lại:** số token và USD trong ví dụ là **giá trị minh họa**, phải điều chỉnh sau khi khảo sát giá và tốc độ thực tế; không sử dụng để dự đoán chi phí toàn bộ 162 bản đúc nổi. `enabled_phases` trong production phải đủ thứ tự; không cho client bỏ P08/P09 bằng JSON.

### C6.3. API response và lỗi

```json
{
  "run_id":"<uuid>",
  "status":"QUEUED",
  "phase":"P00",
  "run_manifest_sha256":"<sha256>",
  "worker_slots_per_phase":10,
  "max_active_phases_per_run":1,
  "human_approval_required":true,
  "links":{"status":"/api/v1/admin/research-factory/runs/<uuid>"}
}
```

| HTTP | Error code | Ý nghĩa | Client action |
|---|---|---|---|
| 400 | `INVALID_SUBJECT_ID` | ID relief/urn không thuộc catalog | sửa selector |
| 401/403 | `AUTH_REQUIRED` / `SCOPE_DENIED` | role hoặc scope không hợp lệ | không leak nguồn private |
| 409 | `DUPLICATE_RUN` | cùng idempotency key | trả run cũ |
| 409 | `INVALID_PHASE_TRANSITION` | gọi gate/publish trước thời điểm | xem current state |
| 409 | `STALE_REVISION` | nội dung đã được người khác sửa | reload conflict diff |
| 422 | `INVALID_PHASE_WIDTH` | `slots_per_phase != 10` trong mode bắt buộc | sửa config |
| 423 | `HUMAN_REVIEW_REQUIRED` | thiếu chữ ký duyệt thật | mở review queue |
| 424 | `SOURCE_RIGHTS_BLOCKED` | nguồn chưa được phép sử dụng | xin phép/thay nguồn |
| 429 | `PROVIDER_CAPACITY` | quota/concurrency broker | retry có backoff |
| 503 | `PIPELINE_UNAVAILABLE` | DB/queue/object store not ready | giữ draft, không giả success |

### C6.4. Admin UI `[TARGET]` theo route

| Route đề xuất | UI panels | UX/Authorization rules |
|---|---|---|
| `/admin/research-factory` | queue, recent runs, budget, active agent count | chỉ admin/researcher, no public indexing |
| `/admin/research-factory/runs/[runId]` | 12 phase timeline × 10 agent lanes, input/output hash, error | hiển thị job `RUNNING` thực, không dùng progress giả |
| `/admin/research-factory/sources` | candidates, canonical refs, permission status, snapshots | excerpt restricted theo quyền |
| `/admin/research-factory/ocr` | viewer scan crop ↔ OCR ↔ transcription | script Hán–Nôm cần reviewer thật |
| `/admin/research-factory/evidence` | claim graph, support/contradict, origin versions | reviewer nhận diện claim chưa nguồn |
| `/admin/research-factory/drafts` | full VI/EN document, inline citations, source panel | draft watermark `AI-generated, not approved` |
| `/admin/research-factory/reviews` | review queue, diff, independent QA + human signatures | two-person approval, no self-approve |
| `/admin/research-factory/coverage` | 9×18 heatmap: evidence/rights/review/lesson/media | “162 records” tách “162 verified” |
| `/admin/research-factory/releases` | release manifest, current pointer, previous, rollback | destructive actions require confirmation and audit |
| `/admin/research-factory/analytics` | run cost, latency, QA, source overlap, model drift | thống kê có mẫu số/cửa sổ thời gian |

### C6.5. UI 10 agent lanes / phase

Mỗi phase hiển thị **đúng 10 hàng** cố định A01–A10; mỗi hàng cần `dispatched_at`, `started_at`, `provider_request_id`, `state`, `attempt`, `cost`, `output_uri`, `blocking_reason`. Header hiển thị hai chỉ số độc lập: `scheduled=10/10` và `running_live=n/10`. Khi provider bị quota, có thể hiện `running_live=5/10, capacity_wait=5`, không in “đã chạy 10 đồng thời” một cách sai lệch. Khi một agent fail, không mất 9 kết quả còn lại; retry chỉ slot lỗi. Các thao tác đặc quyền `replay`, `skip` (chỉ sandbox), `cancel`, `approve` ghi user actor và reason.

### C6.6. OpenAPI, auth và frontend contracts

- Backend generate OpenAPI từ Pydantic v2/schema tương ứng version ứng dụng thật; frontend `npm run gen:api` chỉ sau khi schema ổn định.
- Dùng enum `AI_DRAFT`, `EDITOR_REVIEWED`, `EXPERT_VERIFIED`, `PUBLISHED`, `DISPUTED`, `REVOKED` có source of truth chung, không hardcode nhiều danh sách trạng thái rời rạc JS/Python/Rust.
- Errors có `request_id`, `code`, `reason`, `retry_after_seconds`, `remediation_link` nhưng không lộ raw prompt, storage credentials, token hay thông tin học sinh.
- Client public tuyệt đối không có route gọi trực tiếp các agent để tự tạo claims hoặc đăng nguồn không qua review.
- Preview draft server trả cache-control private, no-store; role-based and content-scope filtering; logging không chứa raw excerpt private.

---

