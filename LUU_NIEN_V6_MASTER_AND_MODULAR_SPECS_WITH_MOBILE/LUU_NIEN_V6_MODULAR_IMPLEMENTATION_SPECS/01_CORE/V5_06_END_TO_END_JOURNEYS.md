# V5.6 — END_TO_END_JOURNEYS

> **Nguồn:** Trích không lược bỏ từ `LUU_NIEN_V5_PRODUCTION_COMPLETION_AND_NEW_FEATURES_GEMINI_FLASH_FULL_MASTER_SPEC.md` (`V5.6`). **Nhận định mã nguồn trong V5 là audit tĩnh, chưa chứng minh production hoạt động.**
> **Dùng cho Gemini:** Chỉ mở tài liệu này với một ticket và tối đa 3–8 file source tương ứng.

## V5.6 — PRODUCT JOURNEYS TỚI END-TO-END PRODUCTION

### 6.1. Hành trình di sản có chứng cứ (Explore → Evidence)

Given một bản đúc nổi approved, public sees image + identity + context + source locators. Click source opens public bibliographic details, page locator or permitted excerpt; if full text restricted, do NOT download illicit scan. Unsupported claim shows `UNCERTAIN` and does not impersonate verified fact. 3D/AR optional. 2D route works on low-end device. `GET evidence` unavailable returns explicitly cached **previously approved** revision or unavailable state, not generated summary without source.

**Golden E2E:** 1 verified + 1 unpublished object, student unauthenticated; verified object accessible via 2D; unpublished returns 404; snippet points to real source edition; no private excerpt exposure; refresh caches invalidated on revocation.

### 6.2. Nhiệm vụ ELLO sáu bước và grade thật

Teacher creates lesson by selecting approved object+sources, choosing representation (2D/3D/AR), creating evidence question and rubric, assigns to class. Student logs in, answers with observations and source locators, submits, may revise before deadline. Teacher grades with immutable rubric version and feedback. Student sees owned grade and revision history. School admin sees aggregate only as allowed. If offline, state is `pending_sync`, not `submitted`; retry is idempotent.

**Golden E2E:** 2 schools, 2 classes, 2 students, 2 teachers, one assignment; cross-school submissions/grades forbidden; teacher grade persists cross-device; no preloaded sample student names; progress reflects DB persisted state.

### 6.3. Visitor → verified artisan → inquiry thật

Visitor sees story with provenance, optional Cultural Bridge AI, creator profile only if current written consent, actual listing, date request. Server stores inquiry atomically. Partner sees **only own** inquiries, edits `new → contacted → confirmed/declined → closed` by legal transitions; owner gets status without PII exposure using opaque token. Completed experience requires explicit evidence, not inferred. Partner revokes consent -> public discover removed; existing requests handled per retention/support policy without public exposure.

**Golden E2E:** valid inquiry + read/ack with correct partner, wrong partner 403, backend down no success, empty partner inbox empty, double submit single DB row, consent revoked listing unavailable, verified completed event counted exactly once.

### 6.4. Admin research → article publication

Researcher selects object, 12 waves of 10 agents gather sources/extract/verify/write; reviewer compares claims with actual page locators, rejects unsupported assertions, requests revisions. Final editor signs off with ID/time, release creates immutable published revision. Search index, cache, LMS references point at published versions; disapproved AI draft never leaks via public API.

**Golden E2E:** intentionally false fabricated page citation -> hold; correction changes draft version; editorial approval records human ID; site cache invalidates after publish; rollback restores last approved revision.

### 6.5. Mobile offline/AR

Flutter fetches signed/approved manifest, caches 2D and allowed 3D under size budgets, local activities queued as `pending_sync`. Conflict resolution is server-defined and idempotent. Revoked creator media must be marked stale and invalidated when connected; cached licensed media follows contractual offline conditions. AR requires supported device, camera permission and safe fallback. Errors never become mock scores.

### 6.6. Demo mode vs sales production

RBPC or startup demo must use a **dedicated demo tenant** and visible `DEMO DATA` watermark for anything synthetic. Production demo journey may use **real, consented and verifiable** source/partner records only. Demo cannot show fictional signed bookings, revenue, user testimonials, artist approval, AI citations, or certification as actual traction. When there are no completed transactions, pitch says pilot in progress; show signed pilot partners or usability tests only where documented.

