# Implementation Plan: Security Hardening Remediation

## Overview

This plan implements the security- and quality-remediation fixes across the Python/FastAPI backend, the Rust/axum backend, and the Next.js frontend. Tasks are ordered by severity and risk and apply to the current codebase without depending on the `backend-modularization` or `frontend-consolidation-typing` specs. Each remediation is paired with at least one automated test that fails on unfixed code and passes after the fix (Requirement 27). Property references point at the Correctness Properties section of `design.md`.

## Tasks

- [x] 1. Secrets & startup hardening (Python)
  - [x] 1.1 In `config.py`, add an explicit `environment: str = "development"` setting and replace the `is_production` log-level heuristic with `environment.lower() == "production"`.
  - [x] 1.2 In `config.py`, remove usable defaults: set `jwt_secret_key` default to empty and define `SENTINELS = {"", "CHANGE_ME_IN_PRODUCTION"}`.
  - [x] 1.3 In `config.py`, add a `@model_validator(mode="after")` that, when production, raises a fatal `RuntimeError` naming offending keys (never values) if `jwt_secret_key` is a sentinel or if `cors_allow_credentials` is true with `"*"` in `cors_origins_list`.
  - [x] 1.4 Ensure `get_settings()` validation executes before the SQLAlchemy engine and FastAPI app are constructed in `main.py`.
  **Requirements:** 1.1, 1.3, 1.4, 3.1, 28.1, 28.2

- [x] 2. Secrets & startup hardening (Rust)
  - [x] 2.1 In `backend-rust/src/config.rs`, add an `app_env` field (from `APP_ENV`) and a sentinel set covering `CHANGE_ME_*` values and empty strings.
  - [x] 2.2 In `config.rs`, implement `Settings::validate(&self) -> anyhow::Result<()>` that errors in production if `jwt_secret_key`, `janus_admin_secret`, `janus_api_secret`, or `live_internal_token` is a sentinel, or `turn_static_auth_secret` is empty. Messages name keys, not values.
  - [x] 2.3 In `backend-rust/src/main.rs`, call `settings.validate()?` immediately after `Settings::from_env()` and before constructing the DB pool, router, or job scheduler.
  - [x] 2.4 Remove usable secret defaults from `from_env()` for production paths.
  **Requirements:** 2.1, 2.3, 5.1, 5.2, 5.3, 5.5, 28.1

- [x] 3. Secrets rollout documentation
  - [x] 3.1 Create `docs/SECRETS.md` enumerating every externally supplied secret per backend (JWT, Janus admin/api, live internal token, TURN auth) with provisioning guidance and the shared-JWT-secret constraint.
  **Requirements:** 2.4, 28.4

- [x] 4. Transport: CORS, secure cookies, security headers (Python)
  - [x] 4.1 In `main.py`, configure `CORSMiddleware` from the validated explicit allowlist; confirm no wildcard is used when credentials are enabled.
  - [x] 4.2 Resolve `cookie_secure` to `True` by default in production unless explicitly overridden; in `_set_auth_cookies`, do not issue a cookie if `Secure` is required but cannot be applied.
  - [x] 4.3 Add a Python response middleware injecting `Content-Security-Policy`, `Strict-Transport-Security`, and `X-Content-Type-Options` on all responses.
  **Requirements:** 3.2, 3.3, 3.4, 6.1, 6.2, 6.3, 25.1, 25.3

- [x] 5. Transport: security headers (Rust)
  - [x] 5.1 Add a `tower` middleware layer in the Rust router injecting CSP, HSTS, and X-Content-Type-Options on all responses.
  **Requirements:** 25.2, 25.3

- [x] 6. JWT contract: required exp and identity claims
  - [x] 6.1 In `backend-rust/src/auth.rs`, stop calling `required_spec_claims.clear()`; set required claims to `["exp", "iss", "aud"]` and configure expected issuer/audience.
  - [x] 6.2 In Python decode path, add `options={"require": ["exp"]}` and pass `issuer`/`audience`; reject on mismatch.
  - [x] 6.3 Add `jti`, `iss`, and `aud` claims to token issuance in both `security.py` and `backend-rust/src/auth.rs` using shared configured constants.
  - [x] 6.4 Add a `JWT_VALIDATE_NEW_CLAIMS` transition flag in both backends so they issue new claims before enforcement, gating cross-backend new-claim validation off while versions are inconsistent.
  **Requirements:** 8.1, 8.2, 8.4, 17.1, 17.3, 17.4, 26.1, 26.3, 26.4

- [x] 7. JWT contract: refresh-token revocation
  - [x] 7.1 Create an Alembic migration adding a `revoked_refresh_tokens` table (`jti` PK, `user_id`, `revoked_at`, `expires_at`).
  - [x] 7.2 On logout and password change, persist the refresh token `jti` as revoked; on refresh, reject tokens whose `jti` is revoked.
  **Requirements:** 17.2

- [x] 8. Assessment integrity (server-authoritative exam grading)
  - [x] 8.1 In the Python exam-questions response model, exclude `correct_answer`/`explanation` from the pre-submission payload.
  - [x] 8.2 In `frontend/src/lib/api.js`, remove `getUrnExamFromStatic` and the client-side grading fallback in `submitUrnExam`; on server error, surface it without local grading.
  - [x] 8.3 Remove the static answer-key JSON assets from `frontend/public/urn-exams/` (or strip answer fields) so answer keys are never shipped.
  - [x] 8.4 Verify the server computes and returns the authoritative score on submit.
  **Requirements:** 4.1, 4.2, 4.3, 4.4, 4.5

- [x] 9. Input validation & uploads (Python)
  - [x] 9.1 In the avatar upload handler, validate content via magic bytes, derive the true type, and reject if not allowed OR not matching the client-declared type; use distinct error codes for content-format vs type-authorization.
  - [x] 9.2 In the RAG upload handler, decode with `errors="strict"` and reject with 400 on `UnicodeDecodeError`; fail closed when both content-type and extension are absent. Persist nothing on rejection.
  - [x] 9.3 Introduce a single `settings.avatar_dir` used for both writing and the static mount; derive the served URL from it.
  **Requirements:** 10.1, 10.2, 10.3, 10.4, 10.5, 10.6, 11.1, 11.2, 11.3

- [x] 10. Safe error envelope (Python)
  - [x] 10.1 In `errors.py`, change `AppError.details` annotation to `Optional[dict]`.
  - [x] 10.2 In the validation handler, return field locations + messages only (no echoed input) and redact fields flagged sensitive.
  **Requirements:** 14.1, 14.2, 14.3, 14.4

- [x] 11. Authorization & correctness (Python)
  - [x] 11.1 In `_apply_xp_boost`, coerce `multiplier = user.xp_boost_multiplier or 0` before comparison and ensure no exception escapes XP application.
  - [x] 11.2 Add rate limiting driven by the existing `rate_limit_*` settings on `/api/v1/auth/*`, returning HTTP 429 over limit.
  - [x] 11.3 Import role sets and dependencies from `rbac.py` in `main.py`; delete local duplicates; special-case `super_admin` in `can_manage_user` to match its docstring.
  - [x] 11.4 Extract a shared `_decode_access_token(raw) -> UUID | None` backing both `get_current_user` and `get_current_user_optional`; remove duplication after migration.
  - [x] 11.5 Change `_record_analytics_event` to use a nested transaction or dedicated session so it never commits the shared request session.
  - [x] 11.6 Add a reusable `require_owner_or_authorized(resource)` dependency applied to endpoints taking `{user_id}`/`{content_id}`/`{session_id}`; return a generic 404 on unauthorized access.
  **Requirements:** 9.1, 9.2, 9.3, 9.4, 12.1, 12.2, 12.3, 12.4, 15.1, 15.2, 15.3, 15.4, 18.1, 18.2, 18.3, 18.4, 19.1, 19.2, 19.3, 20.1, 20.2, 20.3

- [x] 12. Frontend safety fixes
  - [x] 12.1 In `frontend/middleware.ts`, verify token validity (signature + `exp`, edge-compatible) rather than cookie presence; deny on absent/expired/malformed; allow additional checks to deny.
  - [x] 12.2 In the maintained navbar component, populate the `en` translation table with real English strings distinct from `vi`, and change `t` to use `translations[lang]?.[key] ?? key`.
  - [x] 12.3 Fix the route-matching regex in `middleware.ts` from `/\\.json$/` to `/\.json$/`.
  **Requirements:** 13.1, 13.2, 13.3, 22.1, 22.2, 22.3, 23.1, 23.2, 23.3

- [x] 13. Type-safety fix
  - [x] 13.1 In `main.py`, annotate `get_db` as `Iterator[Session]` and confirm type checking is clean.
  **Requirements:** 24.1, 24.2

- [x] 14. Tests — secrets, JWT, CORS (Properties 1, 2, 3, 4, 9)
  - [x] 14.1 Python: test production startup with a sentinel/empty `jwt_secret_key` raises and valid secrets start cleanly; test wildcard+credentials config is rejected.
  - [x] 14.2 Python + Rust: tests that a token signed with the wrong key is rejected, and a token lacking `exp` or with past `exp` is rejected by both backends.
  - [x] 14.3 Python: `TestClient` tests asserting allowlisted Origins are reflected and others are never reflected.
  - [x] 14.4 Cross-backend contract test: a token issued by one backend validates in the other under the consistent contract and is rejected when standard validation fails.
  **Requirements:** 1.1, 3.1, 3.3, 8.2, 26.2, 27.1, 27.2

- [x] 15. Tests — assessment, uploads, ownership, XP (Properties 5, 6, 7, 8)
  - [x] 15.1 Tests asserting exam-fetch responses contain no `correct_answer` and the submitted score equals the server-computed score.
  - [x] 15.2 Property test: an upload persists iff its content-derived type is allowed and matches the declared type; otherwise no file is written.
  - [x] 15.3 Tests that resource-scoped endpoints return a generic 404 for non-owners and succeed for owners.
  - [x] 15.4 Property test: applying XP never raises and a null multiplier yields base XP.
  **Requirements:** 4.2, 9.1, 10.5, 20.1, 27.1

- [x] 16. Tests — transport, frontend, error envelope (Property 10)
  - [x] 16.1 Python: tests asserting CSP/HSTS/X-Content-Type-Options present and the auth cookie carries `Secure` in production; Rust header-layer test.
  - [x] 16.2 Python: validation-error response does not echo submitted input and redacts sensitive fields.
  - [x] 16.3 Frontend: route guard redirects on expired token; exam flow surfaces server errors without local grading; the `.json` strip regex works.
  - [x] 16.4 Frontend: i18n test asserting EN strings differ from VI for differing keys and missing keys resolve to the key.
  - [x] 16.5 Rate-limit integration test asserting 429 after exceeding the configured auth-endpoint limit.
  **Requirements:** 6.1, 12.1, 13.1, 14.1, 22.1, 23.2, 25.1, 27.1

## Task Dependency Graph

```json
{
  "waves": [
    {"tasks": ["1", "2"]},
    {"tasks": ["3", "4", "5", "6", "8", "9", "10", "13"]},
    {"tasks": ["7", "11", "12"]},
    {"tasks": ["14", "15", "16"]}
  ]
}
```

## Notes

- **Sequencing:** Workstreams 1 and 2 (fail-closed config) land first because the CORS and JWT fixes depend on validated configuration. JWT identity claims (Task 6) precede revocation (Task 7) and the cross-backend contract test (Task 14.4).
- **Cross-backend coordination:** Task 6.4's `JWT_VALIDATE_NEW_CLAIMS` flag must be deployed in issue-then-enforce order to avoid breaking tokens mid rolling-deploy.
- **Test-per-remediation:** Tasks 14–16 satisfy Requirement 27. For exam-integrity and config fail-closed behavior, write the test first and confirm it fails against current code before fixing.
- **Out of scope here:** `main.py` modularization and frontend TypeScript migration are tracked in the `backend-modularization` and `frontend-consolidation-typing` specs.
- **Migrations:** Task 7.1 adds a new table; coordinate the Alembic `down_revision` with the latest existing migration head at implementation time.
