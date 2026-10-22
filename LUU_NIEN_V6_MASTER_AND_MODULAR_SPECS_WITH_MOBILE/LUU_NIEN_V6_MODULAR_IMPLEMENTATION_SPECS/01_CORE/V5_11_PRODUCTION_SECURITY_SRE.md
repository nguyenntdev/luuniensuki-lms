# V5.11 — PRODUCTION_SECURITY_SRE

> **Nguồn:** Trích không lược bỏ từ `LUU_NIEN_V5_PRODUCTION_COMPLETION_AND_NEW_FEATURES_GEMINI_FLASH_FULL_MASTER_SPEC.md` (`V5.11`). **Nhận định mã nguồn trong V5 là audit tĩnh, chưa chứng minh production hoạt động.**
> **Dùng cho Gemini:** Chỉ mở tài liệu này với một ticket và tối đa 3–8 file source tương ứng.

## V5.11 — PRODUCTION HARDENING GATES, SRE VÀ SECURITY

### 11.1. Required launch gates

| Gate | Check | Pass evidence | Release blocker |
|---|---|---|---|
| GATE-PROD-01 | Integrity | no simulated success from API errors, audited inquiry/grades | ANY synthetic success accessible publicly |
| GATE-PROD-02 | Data | published claims supported by reviewed sources and rights | unreviewed AI content visible as historical fact |
| GATE-PROD-03 | Security | RBAC multi-tenant, CSRF/XSS, cookies, secrets, logs, upload | other partner/student data can be accessed |
| GATE-PROD-04 | Migrations | migrate empty + seeded + staging clone, downgrade strategy | data loss/unresolved heads |
| GATE-PROD-05 | Backup | measured RPO/RTO restore drill on isolated env | backups never restored successfully |
| GATE-PROD-06 | Resilience | 500/timeouts/429, queue retry, idempotency, SLO | fake success or unbounded retries |
| GATE-PROD-07 | Accessibility | WCAG-oriented checks for critical journeys; offline low-end 2D | users blocked if no AR |
| GATE-PROD-08 | Observability | errors correlated, trace/log/metrics, alert owner, on-call | silent failures |
| GATE-PROD-09 | Rights/consent | revoked creator/asset hidden across CDN/cache/offline sync policy | copyrighted/consent revoked asset public |
| GATE-PROD-10 | Analytics truth | no fixture/test traffic counted as traction | pitch shows projected as actual |
| GATE-PROD-11 | Mobile | route smoke and offline reconciliation | quests stub public / lost grade |
| GATE-PROD-12 | AI | groundedness/refusal benchmark, source citation replay, cost | hallucinated source auto published |
| GATE-PROD-13 | Commerce | partner contract and complaint/refund support where relevant | payment without approved compliance |
| GATE-PROD-14 | Disaster response | rollback, feature flag kill switch, incident drill | inability to disable dangerous feature |

### 11.2. Reliability targets (proposed SLO, not measured)

Initial pilot targets to negotiate: core read endpoints p95 latency <= 800ms on typical regional network excluding image media; inquiry P95 <= 2s; availability >= 99.5% monthly excluding approved maintenance; API 5xx ratio < 1% across normal traffic; no successful fake state; model3D progressive and 2D fallback; offline sync reconciliation within 10min after reconnect in test; restore RPO<=24h RTO<=4h for pilot; choose values according to real hosting and business impact and publish measured windows. No claim these are currently achieved.

### 11.3. Security checklist actionable

- Secrets: environment-managed secret store, rotate keys; grep for tokens only under authorized security CI; never print secrets.
- Browser auth: `HttpOnly` cookies with Secure always on prod, SameSite decision tested against CSRF, logout/revocation, refresh rotation, role scoping; `_set_auth_cookies` currently logs insecure override warning — deploy policy must **reject startup** if insecure cookie in production, not warn only.
- Account security: password rate limit, MFA for editors/partners, strong session invalidation, device trust.
- API: role/scope enforcement in DB query and route (don't trust providerParam), CSRF protection, request schema validation, audit for changes, idempotency, PII redaction.
- Data: student/visitor contact encryption at rest where sensitive, separate keys, retention/erasure, data export only authorized; never push raw Google Forms to repo/LLM prompts.
- Files: MIME/magic byte, size limits, virus scan, storage ACL, SVG sanitization, iframe sandbox/allowed hosts, CSP consistent with Sketchfab/AR/LiveKit if used.
- AI: prompt injection, retriever document policy, tool allowlist, rate budgets, no auto-approval, provenance enforcement.
- Payments: introduce only when legal/partner/payment readiness; ensure idempotency, refunds, reconciliation and disputes.
- Ops: separate dev/staging/prod DB and object stores; DB backups, immutable audit, metrics alerts, rollback; infra docs “PASS” must be validated on deployed hosts.

### 11.4. CI/CD matrix

| Stage | Commands/checks | Mandatory outcome |
|---|---|---|
| static | `python -m compileall -q backend`; `ruff`/lint where configured | zero syntax errors |
| TypeScript | `cd frontend && npm ci && npm run type-check && npm run lint:ci && npm run test` | no type/test regressions |
| Next build | `cd frontend && npm run build` | real production build succeeds |
| Rust | `cd backend-rust && cargo fmt --check && cargo test` | formatting/tests pass |
| Python | isolated test DB; `pytest` backend tests with sane env | auth, RBPC, LMS, sources pass |
| DB | `alembic heads`; staging `upgrade head` or approved graph; migration smoke | no destructive drift |
| security | dependency SCA, secret detection, SAST, API auth negative tests | no critical exploitable finding |
| integration | browser E2E with Rust→Python→DB and mock provider failure | all core journeys pass |
| demo isolation | prod deploy with `DEMO_MODE=false` and empty tenant | zero fixture user/inquiry/grade |
| release | rollout 5/25/100 %, health+metrics, rollback rehearsal | measured SLO, owner signoff |

If CI cannot install deps, mark `NOT_RUN_ENVIRONMENT`, do not mask PASS. Config needed for Rust/Python forwarding is branch-specific and must be checked in `backend-rust/config/route-modes.toml` and OpenAPI snapshot.

