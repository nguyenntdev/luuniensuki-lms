# Incident Runbook: Service Outage & Kill Switch Procedures

**Classification:** P0 Operational Runbook  
**Target Systems:** Luuniensuki LMS (Axum Rust Gateway + FastAPI Python Backend + Next.js Web)  
**Last Updated:** 2026-11-05  
**Version:** 1.0.0

---

## 1. Overview & Operational Principles

This runbook establishes deterministic incident handling procedures for system degradation, upstream provider blackouts, network partitions, and emergency traffic shedding.

### Golden Rules:
1. **Preserve Public Availability First:** The public heritage catalog (Cửu Đỉnh, 9 Urns, 162 Motifs, Imperial Citadel sites, curated stories) must remain online and responsive even during catastrophic downstream AI or media outages.
2. **Fail Closed on Security & Privacy; Fail Open/Graceful on Degradation:** If an AI provider or WebRTC cluster fails, trip the targeted kill switch immediately. Do not allow cascading timeout stalls or hung HTTP connections.
3. **503 Service Unavailable with User-Friendly Maintenance Notice:** Tripped kill switches immediately return `HTTP 503` with a localized maintenance notice (`Retry-After: 300`), allowing clients to render friendly UI notices instead of generic connection errors.

---

## 2. Granular Kill Switches & Feature Flags

| Flag Key | Environment Variable | Targeted Scope | Fallback Behavior |
|---|---|---|---|
| `FEATURE_FLAG_AI_TUTOR_ENABLED` | `FEATURE_FLAG_AI_TUTOR_ENABLED=false` | AI Tutor (`/api/v1/ai/tutor`, `/api/v1/history/tutor/ask`) | Returns HTTP 503. Public heritage catalog, motif exploration, and stories remain 100% accessible. |
| `FEATURE_FLAG_LIVEKIT_MEDIA_ENABLED` | `FEATURE_FLAG_LIVEKIT_MEDIA_ENABLED=false` | LiveKit token issuance & room join (`/api/v1/live-sessions/*/token`, `/join`) | Returns HTTP 503. Students can still access asynchronous classroom assignments & rubrics. |
| `FEATURE_FLAG_RBPC_COMMERCE_ENABLED` | `FEATURE_FLAG_RBPC_COMMERCE_ENABLED=false` | Workshop booking inquiry submission (`/api/v1/rbpc/inquiries`) | Returns HTTP 503. Cultural stories and artisan profiles remain readable. |

---

## 3. Incident Severity Levels & Triage Matrix

| Severity | Definition | Target MTTR | Examples | Immediate Action |
|---|---|---|---|---|
| **SEV-1 (Critical)** | Core platform down, DB corrupted, or widespread data leak. | < 15 mins | Database unreachable, authentication broken for all users. | Engage Incident Commander; check container health; database rollback if migration issue. |
| **SEV-2 (High)** | Major subservice down (AI provider outage, LiveKit cluster packet loss). | < 30 mins | DeepSeek / Clara API returns 5xx; LiveKit media bridge unreachable. | Trip targeted kill switch (`FEATURE_FLAG_AI_TUTOR_ENABLED` or `FEATURE_FLAG_LIVEKIT_MEDIA_ENABLED`). |
| **SEV-3 (Medium)** | Non-critical feature degraded; commerce booking backlog. | < 2 hours | Partner notification queue delayed, workshop booking spam flood. | Trip `FEATURE_FLAG_RBPC_COMMERCE_ENABLED`; investigate queue backlog. |

---

## 4. Execution Procedures: Tripping & Restoring Kill Switches

### Option A: Admin Runtime API (Zero Downtime / Instant)
Operators with `admin` or `super_admin` credentials can toggle kill switches instantly without redeploying:

#### 1. Check Current Kill Switch Status
```bash
curl -X GET "https://lms.histolab.icu/api/v1/admin/kill-switches" \
  -H "Authorization: Bearer <ADMIN_JWT_TOKEN>"
```
**Sample Response:**
```json
{
  "flags": {
    "FEATURE_FLAG_AI_TUTOR_ENABLED": true,
    "FEATURE_FLAG_LIVEKIT_MEDIA_ENABLED": true,
    "FEATURE_FLAG_RBPC_COMMERCE_ENABLED": true
  },
  "overrides": {}
}
```

#### 2. Trip Kill Switch (Emergency Disable)
```bash
curl -X POST "https://lms.histolab.icu/api/v1/admin/kill-switches/FEATURE_FLAG_AI_TUTOR_ENABLED/toggle" \
  -H "Authorization: Bearer <ADMIN_JWT_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"enabled": false, "reason": "DeepSeek API upstream 502 outage"}'
```

#### 3. Restore Kill Switch (Recovery)
```bash
curl -X POST "https://lms.histolab.icu/api/v1/admin/kill-switches/FEATURE_FLAG_AI_TUTOR_ENABLED/toggle" \
  -H "Authorization: Bearer <ADMIN_JWT_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"enabled": true, "reason": "Upstream provider recovered and healthcheck verified"}'
```

---

### Option B: Environment Variable Override (Container Restart)
For persistent configuration across full cluster restarts:

1. Edit `.env` or deployment secrets:
   ```env
   FEATURE_FLAG_AI_TUTOR_ENABLED=false
   FEATURE_FLAG_LIVEKIT_MEDIA_ENABLED=false
   FEATURE_FLAG_RBPC_COMMERCE_ENABLED=false
   ```
2. Reload backend service:
   ```bash
   docker compose restart api
   ```

---

## 5. Diagnostic & Verification Steps

### Step 1: Verify Core Heritage Browse is Intact
```bash
curl -s -o /dev/null -w "%{http_code}\n" https://lms.histolab.icu/api/v1/heritage/catalog
# Expected: 200
```

### Step 2: Verify Tripped Kill Switch Responds with HTTP 503
```bash
curl -s -i -X POST https://lms.histolab.icu/api/v1/history/tutor/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "Thế Miếu thờ ai?"}'
# Expected: HTTP/1.1 503 Service Unavailable
# Body: {"error": {"code": "HTTP_ERROR", "message": "Hệ thống Trợ lý AI đang tạm ngưng bảo trì...", "details": {}}}
```

### Step 3: Verify LiveKit / Media Kill Switch
```bash
curl -s -i -X POST https://lms.histolab.icu/api/v1/live-sessions/00000000-0000-0000-0000-000000000001/token \
  -H "Authorization: Bearer <USER_TOKEN>"
# Expected: HTTP/1.1 503 Service Unavailable
```

---

## 6. Post-Incident Review (PIR) Checklist

- [ ] Record root cause (upstream outage, rate limit exhaustion, cloud networking).
- [ ] Confirm zero PII was logged during the incident.
- [ ] Verify error envelope compliance (`{"error": {"code": ...}}`) across all client logs.
- [ ] Measure total downtime of targeted subservice vs public uptime.
- [ ] Document recovery timeline and update automated alerts if needed.
