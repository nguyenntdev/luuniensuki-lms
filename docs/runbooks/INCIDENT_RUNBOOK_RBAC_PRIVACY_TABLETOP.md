# Security Incident Response & Tabletop Rehearsal Runbook

**Runbook Code:** RUNBOOK-SEC-INC-001  
**Classification:** P0 Confidential / Operational Security Runbook  
**Target Systems:** Luuniensuki LMS Polyglot Stack (Axum Rust Gateway + FastAPI Python Backend + Next.js Web + PostgreSQL 15)  
**Regulatory Frameworks:** Vietnam Decree 13/2023/ND-CP (Personal Data Protection Decree), COPPA Compliance, ISO/IEC 27001 / NIST SP 800-61 Rev. 2  
**Last Updated:** 2026-11-07  
**Version:** 1.0.0  

---

## 1. Overview & Incident Response Charter

This runbook establishes deterministic operational procedures, severity classifications, escalation channels, and tabletop simulation exercises for privacy breaches, malicious multi-tenant attacks, consent revocation enforcement failures, and credential compromises across Luuniensuki LMS.

### Core Tenets
1. **Zero Information Leakage Under Attack:** Cross-tenant malicious operations (e.g., School A probing School B, Partner A scraping Partner B inquiries, unverified teachers harvesting student rosters) MUST fail closed with `HTTP 403 Forbidden` or `HTTP 404 Not Found` without disclosing record counts, names, emails, or status tokens.
2. **Immediate Consent Revocation & Right-to-Erasure (Article 11, Decree 13/2023/ND-CP):** Revocation requests must scrub visitor PII and minor student records synchronously. Subsequent processing, AI fine-tuning exports, and empirical research analysis must immediately halt for revoked entities.
3. **Tabletop Drill Reproducibility:** Incident containment procedures, kill switch isolations, credential resets, and data purge verifications must be rehearsed systematically with zero impact on production data.

---

## 2. Incident Classification & Severity Matrix

| Severity | Impact Description | Detection Triggers | Target Containment | Escalation Path |
|---|---|---|---|---|
| **SEV-1 (Critical Privacy Breach)** | Cross-tenant data exposure (e.g. School A accessing School B rosters, PII leak in public API, unconsented minor data leak). | Cross-tenant probe alert, DLPs, anomaly detection in database query patterns. | < 15 minutes | Incident Commander (IC), Lead Security Engineer, DPO (Data Protection Officer), CTO. |
| **SEV-2 (High Privilege Escalation)** | Unverified teacher attempts access to student PII, unauthorized consent tampering, or high-rate IDOR scans. | 403 rate spike (`UNVERIFIED_TEACHER_ACCESS_DENIED`, `FORBIDDEN_SCOPE`), automated pen-test triggers. | < 30 minutes | Security On-Call, Engineering Lead, Infrastructure Lead. |
| **SEV-3 (Consent / Retention Audit Finding)** | Student guardian consent withdrawal failure, inquiry retention past 90-day due date without scrubbing. | Nightly retention audit alerting, guardian withdrawal dispute. | < 2 hours | Privacy Officer, Compliance Lead, Backend On-Call. |
| **SEV-4 (Low / Informational)** | Isolated failed login burst from untrusted IP, malformed token probes. | Sliding-window IP rate limit alerts (HTTP 429). | < 24 hours | Security Operations triage. |

---

## 3. Incident Handling Protocols (Phase-by-Phase)

### Phase 1: Detection & Triage
1. **Identify Anomaly:** Ingest security alert from structured JSON logs (`event="security_alert"`, `reason="UNVERIFIED_TEACHER_ACCESS_DENIED"` or `event="cross_tenant_probe"`).
2. **Log Correlation:** Extract `trace_id`, `request_id`, client IP, user ID, and target resource ID from request headers.
3. **Declare Severity:** Incident Commander declares SEV level based on Matrix Section 2.

### Phase 2: Containment & Isolation
1. **Kill Switch Activation (If broad leakage suspected):**
   ```bash
   curl -X POST "https://lms.histolab.icu/api/v1/admin/kill-switches/FEATURE_FLAG_AI_TUTOR_ENABLED/toggle" \
     -H "Authorization: Bearer <ADMIN_JWT_TOKEN>" \
     -H "Content-Type: application/json" \
     -d '{"enabled": false, "reason": "Emergency containment during incident INC-SEC-2026-01"}'
   ```
2. **Account Suspension:**
   For compromised credentials or rogue accounts, set `is_active = false` via Admin API or database session.
3. **Session Revocation:**
   Rotate JWT secrets or invalidate refresh tokens (`_revoke_refresh_jti`).

### Phase 3: Eradication & Remediation
1. **Audit Blast Radius:** Check PostgreSQL access logs for all resources touched by the malicious actor:
   ```sql
   SELECT * FROM audit_logs WHERE user_id = '<MALICIOUS_USER_ID>' ORDER BY created_at DESC;
   ```
2. **Enforce Consent Scrubbing:**
   If unconsented minor or visitor records were processed, execute right-to-erasure workflows:
   - For marketplace inquiries: `withdraw_inquiry_consent(db, opaque_token)`
   - For school research pilots: `withdraw_pilot_guardian_consent(db, consent_id, reason)`
   - For student AI chat history: `purge_user_ai_history(db, user)`

### Phase 4: Recovery & Verification
1. Verify database integrity and verify no orphaned PII remains.
2. Run automated test suites:
   ```bash
   DATABASE_URL="postgresql+psycopg://postgres:postgres@localhost:5432/luuniensuki_test" pytest tests/v5/test_v5_t082.py tests/v5/test_v5_t124.py -v
   ```
3. Re-enable feature flags once containment and validation criteria are satisfied.

### Phase 5: Post-Incident Review & Regulatory Reporting
1. **Statutory Notification:** Per Decree 13/2023/ND-CP Article 23, notify the Department of Cybersecurity and High-Tech Crime Prevention (A05) within 72 hours if personal data breach occurs.
2. **Post-Mortem Documentation:** Document root cause, timeline, blast radius, corrective actions, and prevention roadmap within 5 business days.

---

## 4. Tabletop Simulation Scenarios & Execution Drill

### Scenario A: Malicious Cross-School Tenant Access (IDOR Attempt)
- **Actors:**
  - School A: "Trường THPT Chuyên Quốc Học Huế" (Teacher A, Student A1)
  - School B: "Trường THPT Hai Bà Trưng Huế" (Teacher B, Student B1)
- **Attack Vector:** Teacher B obtains Classroom A UUID and attempts to view Gradebook, Roster, or export CSV with student emails and scores.
- **Expected Defense:**
  - `_ensure_class_access` detects teacher mismatch and immediately terminates execution with `HTTP 403 Forbidden` (`detail="Not authorized"`).
  - No names, scores, or school metadata are leaked in the error body.

### Scenario B: Rogue Student Cross-Submission & Assignment Snooping
- **Actors:** Student B1 (School B) vs Assignment A1 (School A).
- **Attack Vector:** Student B1 attempts to submit homework to Assignment A1 or view other students' submissions.
- **Expected Defense:**
  - `submit_history_assignment` checks `ClassMember` enrollment and raises `HTTP 403 NOT_CLASS_MEMBER`.
  - `get_history_assignment_submission` checks ownership and teacher association, raising `HTTP 403 FORBIDDEN`.

### Scenario C: Unverified Teacher PII Harvesting Probe
- **Actors:** Unverified Teacher (User with `role=teacher`, `is_school_verified=False`).
- **Attack Vector:** Teacher attempts to inspect live student rosters or gradebooks.
- **Expected Defense:**
  - System blocks access with `HTTP 403 UNVERIFIED_TEACHER_ACCESS_DENIED`.
  - Zero PII (guardian emails, full names, phone numbers) is disclosed.

### Scenario D: Consent Revocation & Research Isolation Drill (Decree 13/2023/ND-CP)
- **Actors:** Parent / Legal Guardian of Student under Pilot Research Protocol.
- **Action:** Guardian submits withdrawal of informed consent.
- **Expected Defense:**
  - `withdraw_pilot_guardian_consent` marks status as `withdrawn`.
  - Student is immediately excluded from cohort empirical learning metrics calculations.
  - Subsequent assessment submissions for research fail with `HTTP 403 GUARDIAN_CONSENT_WITHDRAWN`.

### Scenario E: Marketplace Partner Isolation & Inquiry Consent Withdrawal
- **Actors:** Partner A (Kim Hoàn Đồng Khánh) vs Partner B (Gốm Phước Tích); Visitor.
- **Attack Vector:** Partner A probes inquiries of Partner B using `?provider=<target_id>`.
- **Expected Defense:**
  - Scoping logic ignores `?provider` param for non-admins and filters strictly by `current_user.id`.
  - Inquiries list contains 0 items belonging to Partner B.
  - Direct PATCH returns `HTTP 403 FORBIDDEN_SCOPE`.
  - Visitor token withdrawal immediately redacts visitor name to `[ANONYMIZED]` and contact value to `[REDACTED]`.

---

## 5. Verification Checklist

- [x] Two-school / two-tenant isolation verified across classrooms, rosters, gradebooks, and assignments.
- [x] Negative abuse validated: zero sensitive cross-account or cross-tenant leakage.
- [x] Unverified teacher access blocked from accessing student PII.
- [x] Guardian consent withdrawal immediately suspends student research metrics and empirical submissions.
- [x] Visitor inquiry consent withdrawal scrubs contact PII synchronously.
- [x] All negative abuse responses return standard error envelopes with empty details.
