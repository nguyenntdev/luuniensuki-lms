# Secrets Management & Rollout

This document enumerates every externally supplied secret each backend requires in
production and explains how to provision them. It exists so operators can prepare all
required credentials **before** a deployment, avoiding a failed or partial startup.

> Audience: platform operators and anyone deploying the Python (FastAPI) or Rust (axum)
> backend to a production environment.

## Fail-closed posture

Both backends **refuse to start** in production unless every required secret is supplied
with a real, non-placeholder value. This is enforced at configuration-load time, before
any database engine, HTTP router, or background job is constructed — so the service never
runs in a partially initialized state with a missing credential.

- **Python** — `config.py` defines a Pydantic `@model_validator(mode="after")`
  (`_validate_production_security`). When `is_production` is true it collects offending
  keys and raises a fatal `RuntimeError` naming them. It checks **two** things:
  - `JWT_SECRET_KEY` is not a sentinel, **and**
  - `CORS_ORIGINS` is not a `*` wildcard combined with `CORS_ALLOW_CREDENTIALS=true`
    (reflecting any origin with credentials is unsafe). Reported as
    `CORS_ORIGINS (wildcard with credentials)`.
- **Rust** — `backend-rust/src/config.rs` exposes `Settings::validate(&self)`, called from
  `main.rs` immediately after `Settings::from_env()` and before the DB pool, router, or job
  scheduler are built. In production it returns an error naming any offending keys among
  `JWT_SECRET_KEY`, `JANUS_ADMIN_SECRET`, `JANUS_API_SECRET`, `LIVE_INTERNAL_TOKEN`, and
  `TURN_STATIC_AUTH_SECRET`.

What counts as a **sentinel** differs slightly per backend (both reject the empty string):

- **Python** rejects an empty string **or** the exact value `CHANGE_ME_IN_PRODUCTION`
  (`SENTINELS = {"", "CHANGE_ME_IN_PRODUCTION"}`).
- **Rust** rejects an empty string **or** any value with the `CHANGE_ME` prefix
  (e.g. `CHANGE_ME`, `CHANGE_ME_IN_PRODUCTION`, `CHANGE_ME_JANUS_ADMIN`);
  `TURN_STATIC_AUTH_SECRET` is rejected only when empty.

To stay safe across both, **never** ship any `CHANGE_ME*` (or empty) value to production.
Error messages name the offending environment-variable **keys only** — secret values are
never printed to logs.

> Note: `DATABASE_URL` and the environment indicator are operationally required (see the
> table below) but are not part of the sentinel check — both backends fall back to a local
> default `DATABASE_URL` if unset, so always set it explicitly in production.

## Required secrets

| Env Var | Used by | Purpose | Prod-required |
|---|---|---|---|
| `JWT_SECRET_KEY` | Both (Python + Rust) | JWT signing & verification. **Must be the SAME value in both backends** — see below. | Yes |
| `JANUS_ADMIN_SECRET` | Rust | Janus WebRTC gateway admin API authentication. | Yes |
| `JANUS_API_SECRET` | Rust | Janus WebRTC gateway API authentication. | Yes |
| `LIVE_INTERNAL_TOKEN` | Rust | Internal live-service auth (Rust ↔ Python AI worker service-to-service calls; distinct from user JWTs). | Yes |
| `TURN_STATIC_AUTH_SECRET` | Rust | coturn REST API static-auth-secret for signing time-limited ICE/TURN credentials. | Yes |
| `DATABASE_URL` | Both (Python + Rust) | Database connection string. May embed credentials (user/password) — treat as a secret. | Yes |
| `CORS_ORIGINS` | Python | Explicit cross-origin allowlist. Must **not** be `*` while `CORS_ALLOW_CREDENTIALS=true`, or the Python backend fails closed. | Yes (explicit origins) |
| `ENVIRONMENT` (Python) / `APP_ENV` (Rust) | Both | Environment indicator. Set to `production` in prod to activate fail-closed validation. | Yes (set to `production`) |

### Shared JWT secret constraint

`JWT_SECRET_KEY` **must be identical in both backends**. Tokens are issued under a shared
JWT contract (same HS256 algorithm, signing secret, and claim set), so an access token
minted by one backend must validate in the other. If the two backends are given different
secrets, cross-service token acceptance breaks and authenticated requests fail across the
boundary.

Generate a strong value once and provision the same string to both services:

```bash
python -c "import secrets; print(secrets.token_urlsafe(64))"
```

### Environment indicator

The fail-closed validators only run when the environment indicator denotes production:

- **Python** reads `ENVIRONMENT`; `is_production` is true when it equals `production`
  (case-insensitive).
- **Rust** reads `APP_ENV`; `is_production()` is true when it equals `production`
  (case-insensitive).

Set the appropriate variable to `production` in every production deployment. Leaving it at
the default (`development`) disables the secret validation and is unsafe for a live system.

## Local development

In development and test, secrets come from each service's local `.env` file (never from
committed source defaults):

- The Python backend and the Rust backend both load the repository-root `.env`
  (see [`.env.example`](../.env.example) for the full set of keys).
- The frontend loads its own `.env` (see [`frontend/.env.example`](../frontend/.env.example)).

Copy the example file and fill in local values:

```bash
cp .env.example .env
```

Source defaults are intentionally non-usable: secret fields default to empty (a sentinel),
so a backend started with `ENVIRONMENT=production` / `APP_ENV=production` and no real
secrets will fail closed rather than run with a placeholder credential. Never commit a real
secret value to `.env.example` or any source file.

## Provisioning checklist

Before deploying to production, confirm:

- [ ] `ENVIRONMENT=production` (Python) and `APP_ENV=production` (Rust) are set.
- [ ] `JWT_SECRET_KEY` is generated with a cryptographically strong value and is **identical** in both backends.
- [ ] `JANUS_ADMIN_SECRET` is a strong, non-placeholder value (Rust).
- [ ] `JANUS_API_SECRET` is a strong, non-placeholder value (Rust).
- [ ] `LIVE_INTERNAL_TOKEN` is a strong, non-placeholder value (Rust).
- [ ] `TURN_STATIC_AUTH_SECRET` is set to a non-empty value (Rust).
- [ ] `DATABASE_URL` points at the production database and its embedded credentials are correct.
- [ ] `CORS_ORIGINS` is an explicit origin allowlist (not `*` with credentials enabled).
- [ ] No secret is left at an empty or `CHANGE_ME*` placeholder value.
- [ ] Secrets are supplied through the deployment environment or a secrets manager — not from committed files.
- [ ] A staging boot has been performed to confirm both backends start without raising a configuration error.
