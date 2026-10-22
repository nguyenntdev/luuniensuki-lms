# MOBILE / WEB / BACKEND API CONTRACTS — V6 DRAFT

> Các endpoint sau là **đề xuất hoặc yêu cầu xác minh**, không phải danh sách API đã tồn tại. Trước khi code: `rg` router, `backend/main.py`, gateway Axum, so OpenAPI thật và giải quyết owner thống nhất. Các method/status dưới đây là mục tiêu thiết kế, chưa là kết quả test.

## Endpoint contract registry

| Method | Path | Domain | Status | Payload/result summary | Errors |
|---|---|---|---|---|---|
| `GET` | `/api/v1/mobile/bootstrap` | Public/read | `[TARGET]` | api_version,flags,min_supported_build | 200,426,503 |
| `POST` | `/api/v1/auth/login` | auth | `VERIFY_EXISTING` | credential,device_id | 200,401,403,429 |
| `POST` | `/api/v1/auth/refresh` | refresh | `VERIFY_EXISTING` | refresh_token | 200,401,409,429 |
| `GET` | `/api/v1/auth/me` | identity | `VERIFY_EXISTING` | server-verified user roles and memberships | 200,401,403 |
| `GET` | `/api/v1/heritage/urns` | public heritage | `TARGET/VERIFY_EXISTING` | published nine urns,source_rev | 200,403,503 |
| `GET` | `/api/v1/heritage/reliefs/{id}` | heritage | `TARGET/VERIFY_EXISTING` | published_revision,review_status,rights | 200,403,404,410 |
| `GET` | `/api/v1/heritage/claims/{id}/sources` | evidence | `[TARGET]` | source_id,passage_id,locator,review | 200,403,404 |
| `GET` | `/api/v1/media/objects/{id}/manifest` | media | `[TARGET]` | asset_id,sha,rights,hotspots,LOD | 200,403,404,410 |
| `GET` | `/api/v1/lessons/{id}/manifest` | classroom | `[TARGET]` | course_revision,rubric_revision,ELLO | 200,403,404,409 |
| `POST` | `/api/v1/attempts/{id}/submissions` | classroom | `[TARGET]` | attempt,idempotency,evidence,source_rev | 201,403,409,422 |
| `GET` | `/api/v1/attempts/{id}/feedback` | classroom | `[TARGET]` | human rubric,version,reviewer | 200,403,404 |
| `GET` | `/api/v1/practice/due` | practice | `TARGET/VERIFY_EXISTING` | server due queue,FSRS | 200,401,403 |
| `POST` | `/api/v1/quiz/{id}/submit` | quiz | `TARGET/VERIFY_EXISTING` | answers,idempotency,server-grade | 200,403,409,422 |
| `GET` | `/api/v1/gamification/wallet` | wallet | `[TARGET]` | xp,hearts,gems server ledger | 200,401,403 |
| `GET` | `/api/v1/quests` | quests | `TARGET/VERIFY_EXISTING` | quest list for user and target | 200,403,404 |
| `GET` | `/api/v1/notifications` | notifications | `[TARGET]` | persistent user inbox | 200,403,404 |
| `POST` | `/api/v1/notifications/devices` | push | `[TARGET]` | installation_id,token,consent | 201,403,409 |
| `POST` | `/api/v1/offline/sync` | offline | `[TARGET/VERIFY_ROUTER]` | versioned operations,per-item ack | 207/200,403,409,422,429 |
| `POST` | `/api/v1/history-tutor/answers` | AI | `[TARGET]` | answer,citations,abstain,model_version | 200,403,422,429,503 |
| `POST` | `/api/v1/passport/stamps/claims` | visitor | `[TARGET]` | signed QR/nonce,device evidence | 201,403,409,422 |
| `GET` | `/api/v1/experiences` | visitors | `[TARGET]` | verified partner listings | 200,403,503 |
| `POST` | `/api/v1/rbpc/inquiries` | partner inquiry | `VERIFY_EXISTING` | durably stored request, idempotency | 201/202,403,409,422,503 |
| `GET` | `/api/v1/privacy/preferences` | privacy | `[TARGET]` | consent and purposes | 200,401,403 |
| `POST` | `/api/v1/privacy/delete-request` | privacy | `[TARGET]` | request/receipt scoped | 202,401,403,409 |

## JSON envelope chuẩn

```json
{
  "meta": {"request_id":"opaque", "api_contract_version":"2026-10", "server_time":"RFC3339"},
  "data": {"resource_id":"server-created", "revision":7, "status":"confirmed"}
}
```

Error payload:

```json
{"error":{"code":"CONFLICT_REVISION","message":"Resource changed","request_id":"opaque","details":{"current_revision":8,"retryable":false}}}
```

## Idempotency semantics

- Client sends `Idempotency-Key` for create/submit/checkpoint request; server binds key to actor, scope, normalized request hash and TTL. Same key + same payload returns same receipt, never duplicates; same key + different payload returns 409.
- Do **not** treat `HTTP 202` as completed if it only queues background processing. Response must expose `status: accepted_pending` and receipt/lookup URI.
- Server-side role and tenant ownership checked within transaction. Never rely on `user_id`, `school_id`, `provider_id` fields supplied by client to authorize.
- ETag or expected revision on PATCH/PUT; on 409 client preserves draft and displays recoverable comparison.
- Strict failure states: 401→session renew/logout; 403→forbidden; 404→not found; 409→conflict; 422→field error; 429→backoff; 5xx→unavailable/retry.

## Representative sample: offline sync `[TARGET]`

```json
{
  "client_schema_version": 2,
  "device_install_id": "pseudonymous-installation-id",
  "operations": [
    {"operation_id":"01J...", "idempotency_key":"idem-...",
      "resource":"lesson_draft", "resource_id":"server-assigned",
      "resource_version":3,"created_at":"2026-10-21T09:00:00Z",
      "payload":{"text":"draft content", "approved_source_ids":["src-1"]}}
  ]
}
```

Return per-item `accepted|already_applied|conflict|rejected`, `server_receipt`, `server_version`, field-level conflict where applicable; no phantom success.

## Contract ownership + generation

- Backend owner writes and version-pins OpenAPI, DTO and migrations. Gateway owner verifies Rust route routing and fallback authority. Web/Flutter owners generate clients from **same pinned OpenAPI** and verify type/schema diff in CI.
- If API owner and paths unknown, status `BLOCKED_BY_CONTRACT`: do not implement fake local server or silently call an invented route.
- For each endpoint add smoke test using disposable DB and two tenants + invalid idempotency/error test; sign owner/handoff.

## Full mobile schema fields by resource

| Resource | Required stable fields | Server authority | Mobile cache rule |
|---|---|---|---|
| Relief | `id,urn_id,revision,published,source_links,rights_status` | curator/DB | cache approved only |
| Source passage | `source_id,version_id,page_locator,quote_hash,rights` | evidence service | purge on revocation |
| Lesson | `id,revision,objective,rubric_version,approved_source_ids` | LMS | pin assignment snapshot |
| Submission | `id,actor,attempt_id,idempotency,version,state` | server grading | local pending only |
| Wallet | `ledger_ref,balance,award_rule_version` | ledger | cache read-only |
| Inquiry | `id,partner_id,status,version,receipt` | partner scoped DB | no fabricated confirmation |
| AI answer | `model_id,source_ids,passage_ids,abstained` | evidence validator | optional short TTL and purge |
| Device token | `installation_id,user_id,rotated_at,consent_state` | notifications service | secure only |
