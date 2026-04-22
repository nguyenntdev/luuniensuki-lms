# 10_Observability.md (Logging • Health • Monitoring)

## Goal

Make production diagnosable:

- structured logs
- health endpoints
- error tracking
- basic monitoring hooks

## Current State

- Backend uses Python logging, but not structured JSON.
- No dedicated `/health` endpoint yet.
- No error tracking (Sentry) or metrics (Prometheus).

## Recommended MVP

### 1) Health endpoint

- `GET /api/v1/health`
  - returns `{ status: "ok", db: "ok", time: "...", version: "..." }`
  - used by deploy scripts and uptime monitors

### 2) Request IDs

- Add middleware:
  - generate `X-Request-Id` if missing
  - include it in logs

### 3) Structured logs

- JSON logs to stdout:
  - timestamp
  - level
  - request_id
  - route/method/status
  - user_id (when available)

### 4) Error tracking (optional early)

- Sentry DSN env var:
  - `SENTRY_DSN`
  - enable only in production

## Tasks

- [ ] **OBS-01**: Add `/api/v1/health` endpoint + tests
- [ ] **OBS-02**: Add request-id middleware
- [ ] **OBS-03**: Switch to JSON logging (or add a JSON formatter)
- [ ] **OBS-04**: Add slow query logging threshold (optional)
- [ ] **OBS-05**: Add Sentry integration (optional)
- [ ] **OBS-06**: Add Prometheus `/metrics` (optional)

## Definition of Done

- On any 500 error, logs contain request id + endpoint + traceback.
- Deployment script can verify health before declaring success.

