# Runbook: AI Teacher LiveKit 3D (Production)

## 1. Deploy Checklist

1. Apply DB migrations:
   - `alembic upgrade head`
2. Update environment variables from `.env.example` (LiveKit + AI safety + retention + cost).
3. Restart API service.
4. Restart AI worker:
   - `python services/ai_teacher_agent/realtime_worker.py --interval 1.0 --log-level INFO`
5. Smoke test critical endpoints:
   - `POST /api/v1/live-sessions/{id}/join`
   - `POST /api/v1/live-sessions/{id}/ai-teacher/reply`
   - `GET /api/v1/live-sessions/{id}/dashboard`

## 2. Monitoring Targets

- Join success rate >= 98%
- p95 latency (`observability.p95_latency_ms`) <= 2500ms
- Drop rate <= 1%
- Session crash/disconnect <= 1%
- AI cost/session <= configured ceiling

Use:
- `GET /api/v1/live-sessions/{id}/observability`
- `GET /api/v1/live-sessions/{id}/dashboard`

## 3. Safety and Compliance

- Guardrails enabled:
  - `LIVE_AI_ENABLE_GUARDRAILS=true`
  - `LIVE_AI_BLOCK_UNSAFE_CONTENT=true`
- Transcript/summary are encrypted at rest (service layer).
- Retention controls:
  - `LIVE_TRANSCRIPT_RETENTION_DAYS`
  - `LIVE_SUMMARY_RETENTION_DAYS`
  - `LIVE_AUDIO_RETENTION_DAYS`

## 4. Maintenance Jobs

Run daily (cron):
- `POST /api/v1/admin/live-sessions/maintenance/cleanup?max_age_hours=24`

Purpose:
- purge expired transcript/summary/action rows
- purge old rate-limit logs

## 5. Incident Handling

### 5.1 STT/TTS/LLM provider degraded

Symptoms:
- elevated `drop_rate`
- repeated provider errors / circuit open

Actions:
1. Check `GET /api/v1/live-sessions/{id}/observability`.
2. Verify circuit breaker state via logs.
3. Temporarily disable AI in host panel if needed.
4. Re-enable after provider recovery window.

### 5.2 Cost spike

Actions:
1. Check dashboard `ai_cost.total_usd` vs ceiling.
2. Lower ceiling via host settings (`ai_cost_ceiling_usd`).
3. Force hint-first mode in moderation policy.

## 6. QA Regression Matrix

- 1 host + 3 learners + AI, 30 minutes
- voice request -> transcript -> AI reply -> TTS
- unsafe prompt blocked by guardrail
- cost ceiling exceeded -> request rejected
- end session -> summary generated + export JSON/CSV works
