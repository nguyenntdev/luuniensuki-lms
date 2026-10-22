# V2 original archival technical chapter — SECTION_19

> Extracted without rewriting from V2 snapshot documentation, **not verified current code**.

## 19. TECHNICAL ISSUE WORKSHEETS — FILE-LEVEL FIX DESIGN

### FIX AU-002 / AU-003 — Fail-closed inquiry UI

**Current** `frontend/src/lib/rbpc/inquiries.ts`: `catch 404/network` returns locally fabricated `reference` and `statusToken`; `fetchPartnerInquiries` returns seed list on failure.  
**Required:**

```ts
// PSEUDOCODE, not a drop-in compiled patch
export async function submitInquiry(payload: CreateInquiryApiPayload) {
  const result = await apiRequest<InquirySubmissionResult>("/api/v1/rbpc/inquiries", {
    method: "POST", body: payload,
  });
  if (!result.reference || !result.statusToken) throw new ApiContractError();
  return result; // success only after actual HTTP 202 commit response
}
export async function getPartnerInbox() {
  // HTTP 200 [] means no entries; 401/403/5xx remain explicit errors
  return apiRequest<PartnerInboxList>("/api/v1/rbpc/partner/inquiries");
}
```

- Add `IS_DEMO_MODE && hostname allowlist` only for explicitly labeled demo route; no client-controlled demo flag in production.
- In UI: show retry action, draft-save notice (not “received”), correlation ID, no 24h promise absent server record.
- API test: disconnect server while submit, expect failure UI; 200 zero list empty; 401 does not display mock customer PII.

### FIX AU-004 — Migration reliability

- Use branch snapshot with reproducible PostgreSQL disposable schema; parse `revision/down_revision` and call Alembic native graph to confirm actual heads; compare against current production version table.
- Require merge revisions only after both content trees reviewed, avoid `stamp head` as a repair shortcut.
- Deployment:

```bash
set -euo pipefail
alembic upgrade <approved_head>
python scripts/smoke/check_core.py
```

- Abort deploy when migration fails; do not suppress (`|| true`).
- Add deploy journal marking artifact SHA, schema version and rollback potential.

### FIX AU-001 — 162 source completeness

- `raw_seed`: preserve original JSON with hash (don't silently alter originals).
- Map 162 candidate IDs against independent verified checklist.
- Generate `claim_review_queue.csv` with one claim per row, current AI text excerpt, source_id/locator blank, owner/review_state.
- Disallow `editorial_status='published'` when `source_bindings` for material claim empty.
- Export audit of each of 162 items and display 2D only with `unverified` label if reviewer approval missing.

### FIX AU-005 — Rate limit

- In edge, overwrite `X-Forwarded-For`, restrict which proxy IP ranges trusted.
- Rate limiter key = verified client IP + endpoint + tenant with TTL in Redis/edge; budget and burst documented.
- Test fake `X-Forwarded-For: 1.2.3.4` arriving directly to service cannot rotate IP identity.
- Avoid leaking IP in application error JSON or logs; add privacy retention limits.

### FIX AU-007 — RAG reliability

- DB query only expert/editor published claims; query-scoped permissions.
- Retrieval returns evidence id, citation locator; answer sentences require mapping to evidence spans.
- Split deterministic precheck, model draft, post-citation check, factual entailment evaluator, abstain/handoff.
- Keep gold set unseen during tuning; test knowledge holes and invented citations.
- Report `source-attributed factual assertion rate`, `unsupported assertion rate`, `citation validity`, `abstention precision`, runtime/cost; publish denominator and version.

---

