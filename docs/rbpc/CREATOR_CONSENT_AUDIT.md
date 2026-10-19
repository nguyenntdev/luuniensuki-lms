# LƯU NIÊN — The Living Heritage Platform
## RBPC 2026: CREATOR CONSENT LIFECYCLE, FAIL-CLOSED ACCESS GOVERNANCE & EDUCATIONAL BRIDGE AUDIT REPORT
### Phase 7 Verification: Artisan Sovereignty, Inquiry State Machine, Multi-Tenant Partner Scoping, and Educational Pathway

**Document ID:** `DOC-RBPC-AUDIT-008`  
**Version:** 1.0.0 Final Verified  
**Date:** 18 October 2026  
**Status:** PASS / VERIFIED FOR RBPC SUBMISSION & CODEBASE AUDIT  
**Controlling Specifications:** Master Execution Goal V2 (§0.2, §0.3, §1.2, §4.2, §4.4, §5.1–§5.4, §6.1), `CREATE_LEARN_SPEC.md` (`DOC-RBPC-SPEC-007`), `DEMO_CREATE_SCRIPT.md` (`DOC-RBPC-DEMO-007`), `CONTENT_RIGHTS.md` (`DOC-RBPC-RIGHTS-001`), `DATABASE_CONTRACTS.md` (`DOC-RBPC-DB-001`), `API_CONTRACTS.md` (`DOC-RBPC-API-001`), `STUDENT_READINESS_GUIDE.md` (`DOC-RBPC-GUIDE-001`)  
**Base Commit SHA:** `e19aebc0e7f66f7863659fd658c204739e199687`  
**Branch:** `feat/rbpc-cultural-bridge-2026`  
**Target Scope:** `RBPC_HUE` (Imperial Heritage & Living Artisan Quarter)  
**Author:** AGENT 07 — Frontend Create & Learn Engineer / Phase 7 Verification Lead  
**Supervision:** Student Founders (S1 Integrator, S2 Engineering Lead, S3 Business Lead, S4 Creative Lead)  

---

## 1. Executive Summary & Audit Mandate

### 1.1 Purpose & Regulatory Context (RMIT RBPC 2026)
Under the **RMIT Business Plan Competition (RBPC) 2026 Guidelines** ("AI and Humanity: Building What's Next", Competition Rules 1.11, 4.2, 4.3) and the **LƯU NIÊN Artisan Dignity Charter**, the cultural bridge platform is bound by four non-negotiable architectural mandates:
1. **Practitioner Sovereignty:** Living heritage custodians (artisan masters and traditional craft cooperatives) must maintain absolute, perpetual control over their names, portraits, biographies, audio recordings, and workshop offerings. Consent is never assumed or irrevocable.
2. **Fail-Closed Default:** If consent status transitions away from actively verified agreement (`consented` or `verified_written_consent`), public discovery endpoints, database queries, and client-side view components must immediately withhold all personally identifiable information (PII) and conceal linked commercial offerings.
3. **Multi-Tenant Partner Isolation:** Experience providers (guild masters, workshop hosts, and cooperative managers) must be strictly isolated at the query level. Cross-tenant access to customer booking inquiries must be blocked with HTTP 403 `FORBIDDEN_SCOPE` before any query processing occurs.
4. **Epistemic Honesty & Pedagogical Grounding:** The educational experience (`/learn`) must ground historical metallurgy and craft techniques in primary imperial archives (*Khâm Định Đại Nam Hội Điển Sự Lệ*) and interactive 3D digital twins, clearly distinguishing implemented learning modules from 2027–2028 future school curriculum roadmaps.

### 1.2 Audited Systems & Coverage Matrix
This audit encompasses full-stack verification across four distinct engineering subsystems:

```
+───────────────────────────────────────────────────────────────────────────────────────────────────+
|                           PHASE 7 FOUR-PILLAR VERIFICATION ARCHITECTURE                           |
+───────────────────────────────────────────────────────────────────────────────────────────────────+
|                                                                                                   |
|   [ PILLAR 1: CONSENT LIFECYCLE ]           [ PILLAR 2: FAIL-CLOSED ENFORCEMENT ]                 |
|   • Model: RbpcConsentStatus enum           • Endpoint: GET /api/v1/rbpc/creators/{slug}         |
|   • States: consented -> pending_review      • Endpoint: GET /api/v1/rbpc/experiences/{slug}      |
|             -> revoked                      • Endpoint: GET /api/v1/rbpc/stories/{slug}          |
|   • Endpoint: POST /editor/.../consent      • Component: CreatorProfileCard.tsx                   |
|   • RBAC: STAFF_ROLES (admin, super_admin)  • Component: StoryArtisanBridge.tsx                   |
|   • Cryptographic SHA-256 audit chaining    • Component: LivingBridgeCard.tsx                     |
|                                                                                                   |
|   [ PILLAR 3: INQUIRY STATE MACHINE ]       [ PILLAR 4: EDUCATIONAL PATHWAY ]                     |
|   • States: new -> contacted -> confirmed   • Route: /learn (App Router)                          |
|             / declined -> closed            • 4-Phase Roadmap: P1_HERITAGE_BASELINE               |
|   • Scoping: provider_id ownership isolation                   P2_INTERACTIVE_3D                  |
|   • Zero-PII public status token                               P3_MAKER_MASTERCLASS               |
|   • 90-day retention policy & purge                            P4_ACCREDITED_CURRICULUM           |
|                                                                                                   |
+───────────────────────────────────────────────────────────────────────────────────────────────────+
```

---

## 2. Artisan Consent Lifecycle Audit (`consented` $\rightarrow$ `pending_review` $\rightarrow$ `revoked`)

### 2.1 State Definitions & Transition Semantics
The artisan consent lifecycle is formalized in `backend/models_rbpc.py` (lines 528–534, 599–610) and `backend/apischemas/rbpc.py` (lines 145–185):

```
                        ┌──────────────────────────────┐
                        │          consented           │
                        │ (Active bilateral agreement) │
                        └───────┬──────────────▲───────┘
                                │              │
                    Annual audit│              │Re-certified
                        trigger │              │agreement
                                ▼              │
                        ┌──────────────────────┴───────┐
                        │        pending_review        │
                        │  (Under compliance review)   │
                        └───────┬──────────────────────┘
                                │
                        Artisan │ Practitioner
                        request │ withdrawal
                                ▼
                        ┌──────────────────────────────┐
                        │           revoked            │
                        │    (Withdrawn / blocked)     │
                        └──────────────────────────────┘
```

| Consent State | Enum Identifier | Operational Semantics | Public Visibility | Inquiry Acceptance |
|---|---|---|:---:|:---:|
| **Consented** | `consented` | Active bilateral consent agreement on file; standard operational tier. | **PUBLIC** | **ENABLED** |
| **Verified Written** | `verified_written_consent` | High-assurance tier with verified physical paper archive reference (`display_consent_ref`). | **PUBLIC** | **ENABLED** |
| **Pending Review** | `pending_review` | Temporary administrative hold for annual re-certification, syllabus adjustment, or fee structure review. | **WITHHELD (404)** | **BLOCKED (400)** |
| **Revoked** | `revoked` | Permanent or indefinite practitioner withdrawal under Dignity Charter "Right to be Forgotten". | **WITHHELD (404)** | **BLOCKED (400)** |

### 2.2 Administrative Mutation Endpoint (`POST /api/v1/rbpc/editor/creators/{id}/consent`)
Administrative mutations of artisan consent are handled by `update_creator_consent_status` in `backend/routers/rbpc.py`:

```python
# Location: backend/routers/rbpc.py (lines 1007-1065)
@router.post("/api/v1/rbpc/editor/creators/{id}/consent", response_model=RbpcCreatorOut)
def update_creator_consent_status(
    id: UUID,
    payload: RbpcCreatorConsentUpdateIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Allow editors to update artisan consent state (consented, pending_review, revoked).

    Enforces editor/staff permissions (STAFF_ROLES) and logs cryptographic audit trail.
    """
    _require_role(current_user, STAFF_ROLES)
    ...
```

#### Security & Access Control Enforcement:
1. **Authentication Requirement:** Unauthenticated callers receive HTTP 401 Unauthorized (`test_unauthenticated_partner_endpoints_return_401`).
2. **Role-Based Access Control (RBAC):** Callers with non-staff roles (`learner`, `teacher`) are immediately rejected with HTTP 403 `FORBIDDEN_SCOPE` (`test_non_staff_editor_consent_returns_403`). Only `admin` and `super_admin` identities can execute consent mutations.
3. **Audit Trail Generation:** Every invocation triggers `record_creator_consent_change()` in `backend/services/rbpc_audit.py`, generating an immutable cryptographic hash chain block (`RbpcContentAudit`).

### 2.3 Re-Seeding & Re-Import Preservation Guardrail
A critical operational vulnerability in content platforms is the silent accidental reversion of manual consent revocations when automated data seed scripts re-run. In LƯU NIÊN, this is prevented at the database service layer in `backend/services/heritage_import.py`:

```python
# Location: backend/services/heritage_import.py (lines 1428-1453)
existing_creator = existing_creators_by_slug.get(slug)
if existing_creator:
    # Preservation guardrail: manual consent revocation must never be silently overturned by re-seeding
    # Also preserve verified_written_consent and pending_review against incoming default seed statuses
    should_preserve_consent = (
        (
            existing_creator.consent_status == RbpcConsentStatus.revoked.value
            and consent_status != RbpcConsentStatus.revoked.value
        )
        or (
            existing_creator.consent_status == RbpcConsentStatus.verified_written_consent.value
            and consent_status in (RbpcConsentStatus.consented.value, RbpcConsentStatus.pending_review.value)
        )
        or (
            existing_creator.consent_status == RbpcConsentStatus.pending_review.value
            and consent_status == RbpcConsentStatus.consented.value
        )
    )
    if should_preserve_consent:
        stats.creators_preserved_consent += 1
        # Update biographical text and operational metadata WITHOUT touching consent_status
        existing_creator.public_name = public_name
        ...
```

**Empirical Verification:** Tested in `tests/backend/test_commercial_seed.py` (`test_commercial_idempotency_and_revocation_preservation`), which revokes consent on artisan Đỗ Hữu Triết, re-runs the full YAML import pipeline, and asserts that `consent_status` remains `revoked` while non-consent fields are updated.

---

## 3. Fail-Closed Consent Revocation Verification (Empirical Proof)

### 3.1 Public Creator Profile Cutoff (`GET /api/v1/rbpc/creators/{slug}`)
When an artisan's consent is transitioned to `pending_review` or `revoked`, the public lookup endpoint immediately treats the record as nonexistent:

```python
# Location: backend/routers/rbpc.py (lines 539-548)
if not creator:
    raise AppError("RBPC_CREATOR_NOT_FOUND", f"Creator '{slug}' not found.", status.HTTP_404_NOT_FOUND)

# Consent gate: only consented artisans are published
if creator.consent_status not in (
    RbpcConsentStatus.consented.value,
    RbpcConsentStatus.verified_written_consent.value,
):
    raise AppError("RBPC_CREATOR_NOT_FOUND", f"Creator '{slug}' not found.", status.HTTP_404_NOT_FOUND)
```

**Empirical Proof:** In `tests/backend/test_partner_security.py` (`test_editor_creator_consent_workflow_and_revocation_effect`):
- `GET /api/v1/rbpc/creators/artisan-sec-a` initially returns HTTP 200 with public name.
- Transition to `pending_review` $\rightarrow$ `GET` returns HTTP 404 `RBPC_CREATOR_NOT_FOUND`.
- Transition to `revoked` $\rightarrow$ `GET` returns HTTP 404 `RBPC_CREATOR_NOT_FOUND`.
- Re-consent to `consented` $\rightarrow$ `GET` immediately restores HTTP 200.

### 3.2 Workshop Offering Concealment (`GET /api/v1/rbpc/experiences/{slug}`)
Workshop offerings linked to an artisan whose consent has been revoked must not be publicly viewable or indexable:

```python
# Location: backend/routers/rbpc.py (lines 559-570)
exp = db.scalar(
    select(RbpcExperience)
    .options(selectinload(RbpcExperience.creator))
    .where(
        RbpcExperience.slug == valid_slug,
        RbpcExperience.publication_state == "published",
    )
)
if not exp:
    raise AppError("RBPC_EXPERIENCE_NOT_FOUND", f"Experience '{slug}' not found.", status.HTTP_404_NOT_FOUND)

# Consent gate: if linked to an artisan creator, creator must be actively consented
if exp.creator and exp.creator.consent_status not in (
    RbpcConsentStatus.consented.value,
    RbpcConsentStatus.verified_written_consent.value,
):
    raise AppError("RBPC_EXPERIENCE_NOT_FOUND", f"Experience '{slug}' not found.", status.HTTP_404_NOT_FOUND)
```

**Empirical Proof:** In `tests/backend/test_partner_security.py`:
- `GET /api/v1/rbpc/experiences/exp-sec-a` returns HTTP 200 when creator is `consented`.
- Transition creator to `pending_review` $\rightarrow$ `GET /api/v1/rbpc/experiences/exp-sec-a` returns HTTP 404 `RBPC_EXPERIENCE_NOT_FOUND`.
- Transition creator to `revoked` $\rightarrow$ `GET /api/v1/rbpc/experiences/exp-sec-a` returns HTTP 404 `RBPC_EXPERIENCE_NOT_FOUND`.
- Re-consent creator $\rightarrow$ `GET /api/v1/rbpc/experiences/exp-sec-a` immediately restores HTTP 200.

### 3.3 Dynamic Story Detail Integration Fail-Closed Guardrail
When visitors read historical stories (e.g. *Tiếng chuông Khiêm Cung*), the story references both historical facts and living artisans. When an artisan's consent is revoked:

```python
# Location: backend/routers/rbpc.py (lines 457-469)
# Consented creator
creator_out = None
if story.creator and story.creator.consent_status in (
    RbpcConsentStatus.consented.value,
    RbpcConsentStatus.verified_written_consent.value,
):
    creator_out = _creator_to_out(story.creator)

# Experience (fail-closed: hidden if linked creator consent is not active)
experience_out = None
if story.experience and story.experience.publication_state == "published":
    exp_creator = story.experience.creator or story.creator
    if not exp_creator or exp_creator.consent_status in (
        RbpcConsentStatus.consented.value,
        RbpcConsentStatus.verified_written_consent.value,
    ):
        experience_out = _experience_to_out(story.experience)
```

The story continues to deliver its historical and educational value, while completely suppressing the artisan biography (`creator: null`) and workshop offering card (`experience: null`).

### 3.4 Booking Inquiry Halting (`POST /api/v1/rbpc/inquiries`)
If an external client attempts to submit a booking inquiry for an experience belonging to a revoked or pending artisan:

```python
# Location: backend/routers/rbpc.py (lines 642-647)
if exp.creator and exp.creator.consent_status not in ("consented", "verified_written_consent"):
    raise AppError(
        "RBPC_CREATOR_CONSENT_UNAVAILABLE",
        "Nghệ nhân chưa hoàn tất thỏa thuận đồng thuận công khai.",
        status.HTTP_400_BAD_REQUEST,
    )
```

**Empirical Proof:** Tested in `tests/backend/test_partner_security.py` line 428; submission halts with HTTP 400 and error code `RBPC_CREATOR_CONSENT_UNAVAILABLE`.

### 3.5 Frontend UI Fallback Safeguards
On the Next.js client, components implement graceful degradation when encountering a revoked status badge:

1. **`CreatorProfileCard.tsx` (lines 90–117):**
   ```tsx
   if (creator.consentStatus === "revoked") {
     return (
       <RbpcCard elevation="inset" padding="lg" className="border-dashed border-[var(--rbpc-error-border)] bg-[var(--rbpc-error-subtle)] text-center">
         <ShieldAlert className="h-6 w-6 text-[var(--rbpc-error)] mb-4" />
         <h3>{locale === "vi" ? "Hồ sơ tạm thời không khả dụng" : "Profile Temporarily Unavailable"}</h3>
         <p>{copy.consent.withdrawnNotice}</p>
       </RbpcCard>
     );
   }
   ```
2. **`StoryArtisanBridge.tsx` (lines 165–194):** Suppresses the workshop booking CTA, replaces maker links with a dignified privacy banner, and prevents opening the `InquiryFormModal`.
3. **`LivingBridgeCard.tsx` (lines 253–280):** Removes the artisan card from the Explore feed with an accessible non-commercial explanation.

---

## 4. Inquiry State Machine Audit & Provider Isolation

### 4.1 Inquiry Lifecycle States & Allowed Transitions
Visitor availability requests follow a deterministic 5-stage state machine defined in `backend/models_rbpc.py` and `backend/routers/rbpc.py`:

```
          ┌────────────────────────────────────────────────────────┐
          │                          new                           │
          │             (Visitor submitted inquiry)                │
          └───────────────────────────┬────────────────────────────┘
                                      │
                                      │ Provider reaches out
                                      ▼
          ┌────────────────────────────────────────────────────────┐
          │                       contacted                        │
          │         (Direct communication established)             │
          └───────────────┬────────────────────────┬───────────────┘
                          │                        │
            Dates & slot  │          Overbooked or │
            agreed        │          unavailable   │
                          ▼                        ▼
          ┌────────────────────────┐      ┌────────────────────────┐
          │       confirmed        │      │        declined        │
          │  (Scheduled workshop)  │      │  (Respectful decline)  │
          └───────────────┬────────┘      └────────┬───────────────┘
                          │                        │
                          │ Workshop held          │ Archive
                          │ or cancelled           │
                          ▼                        ▼
          ┌────────────────────────────────────────────────────────┐
          │                         closed                         │
          │                 (Terminal archive)                     │
          └────────────────────────────────────────────────────────┘
```

#### Transition Invariants & Guardrails:
- **`new` $\rightarrow$ `contacted`:** Only valid forward path from initial state. Skipping to `confirmed` without contacting visitor is rejected with HTTP 400 `RBPC_INVALID_TRANSITION`.
- **`contacted` $\rightarrow$ `confirmed` | `declined`:** Provider evaluates calendar capacity and reaches agreement with visitor.
- **`confirmed` $\rightarrow$ `closed`:** Workshop completed or schedule expired.
- **`declined` $\rightarrow$ `closed`:** Archived request.
- **`closed` is Terminal:** Inquiries in `closed` status cannot transition back to `new`, `contacted`, or `confirmed` (enforced in `test_invalid_inquiry_state_transitions`).

### 4.2 Multi-Tenant Provider Isolation Verification
LƯU NIÊN serves multiple independent craft cooperatives and family foundries. Strict tenant isolation ensures no provider can inspect or tamper with another provider's customer leads:

```python
# Location: backend/routers/rbpc.py (lines 871-895)
@router.get("/api/v1/rbpc/partner/inquiries", response_model=RbpcPartnerInquiryListOut)
def list_partner_inquiries(
    status_filter: Optional[str] = Query(default=None, alias="status"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve incoming visitor inquiries for the authenticated provider.

    Enforces strict server-side scoping: non-staff callers only view inquiries
    where provider_id matches current_user.id or linked experience provider matches.
    """
    stmt = select(RbpcInquiry).options(selectinload(RbpcInquiry.experience))
    if current_user.role not in STAFF_ROLES:
        stmt = stmt.outerjoin(RbpcExperience, RbpcInquiry.experience_id == RbpcExperience.id).where(
            or_(
                RbpcInquiry.provider_id == current_user.id,
                RbpcExperience.provider_id == current_user.id,
            )
        )
```

```python
# Location: backend/routers/rbpc.py (lines 932-944)
# In update_partner_inquiry_status:
if current_user.role not in STAFF_ROLES:
    is_owner = (
        inquiry.provider_id == current_user.id
        or (exp is not None and exp.provider_id == current_user.id)
    )
    if not is_owner:
        raise AppError("FORBIDDEN_SCOPE", "You do not have permission to manage this inquiry.", status.HTTP_403_FORBIDDEN)
```

**Empirical Proof (`tests/backend/test_partner_security.py`):**
1. **`test_provider_inquiry_scoping`:** Partner A logs in and fetches `/api/v1/rbpc/partner/inquiries`. Sees `INQ-SEC-A-001`, does **not** see `INQ-SEC-B-002`. Partner B logs in and sees only `INQ-SEC-B-002`. Admin logs in and sees both inquiries across all providers.
2. **`test_cross_provider_access_returns_403`:** Partner A attempts `PATCH /api/v1/rbpc/partner/inquiries/{inquiry_b.id}`. Operation halts with HTTP 403 `FORBIDDEN_SCOPE`.

### 4.3 Cryptographic Audit Trail Chaining (SHA-256)
Every state change appends a tamper-evident record in `rbpc_content_audit`:
- **Genesis Block:** First mutation sets `previous_hash = None`.
- **Chained Blocks:** Subsequent mutations compute `previous_hash = prior_record.new_hash`.
- **Payload Hash:** `new_hash = SHA-256(canonical_json(diff_payload) + previous_hash)`.
- **Zero-PII Storage:** The `diff_payload` stores only `{"old_state": ..., "new_state": ..., "note": ...}` without storing visitor phone numbers, names, or email addresses.

**Empirical Proof:** Tested in `tests/backend/test_audit_trail.py` (`test_inquiry_state_transitions_audit_trail`, `test_tamper_detection_in_hash_chain`), validating that altering any bit in `diff_payload` triggers cryptographic tamper detection.

### 4.4 Zero-PII Status Tracking & Retention Policy
- **High-Entropy Opaque Bearer Token:** When visitors submit an inquiry, they receive an opaque token (e.g. `tok_7f89a23c...`).
- **Public Status Check (`GET /api/v1/rbpc/inquiries/status/{opaqueToken}`):** Returns reference code, status (`contacted`, `confirmed`), workshop title, and preferred date. **Returns 0 PII:** no names, emails, phone numbers, or IP addresses.
- **Automated Retention Purge:** After 90 days (`retention_due_at`), background jobs execute `purge_expired_inquiry_pii()`, redacting contact values to `[PURGED_RETENTION_POLICY]` while preserving anonymous aggregated research metrics (`test_inquiry_retention_policy_purge_and_audit`).

---

## 5. Educational Bridge Audit (`/learn` Pathway Verification)

### 5.1 UNESCO SDG 4 Alignment & Non-Speculative Scope
In adherence to Master Spec §0.2, LƯU NIÊN designates **SDG 8 (Decent Work & Economic Growth)** as its primary commercial impact metric, and **SDG 4 (Quality Education)** as its secondary educational pathway. The `/learn` page avoids speculative "AI EdTech" claims; instead, it provides a structured, source-grounded curriculum bridging imperial history to living craft.

### 5.2 Four-Phase Pedagogical Progression Architecture
The curriculum is organized into four distinct phases defined in `frontend/src/lib/rbpc/learnModules.ts`:

```
+───────────────────────────────────────────────────────────────────────────────────────────────────+
|                                4-PHASE HERITAGE LEARNING FRAMEWORK                                 |
+───────────────────────────────────────────────────────────────────────────────────────────────────+
|                                                                                                   |
|   PHASE 1: IMPERIAL ARCHIVAL FOUNDATION (P1_HERITAGE_BASELINE) [Available in Repo]                |
|   • Module mod-p1-01: Khâm Định Đại Nam Administrative Statutes (1835 casting edicts)            |
|   • Module mod-p1-02: Phường Đúc 1835 Land Records & Royal Foundry Directorate Decree             |
|   • Pedagogy: Primary archival investigation, classical Sino-Nom translation, administrative law   |
|                                                                                                   |
|   PHASE 2: INTERACTIVE 3D METALLURGY (P2_INTERACTIVE_3D) [Available in Repo]                      |
|   • Module mod-p2-01: Decoding the 18 Relief Inscriptions of Cao Đỉnh (Territorial Sovereignty)   |
|   • Module mod-p2-02: Hollow Casting & Loam Mold Engineering on Thuần Đỉnh (Alloy Fluidity Ratios)|
|   • Pedagogy: 3D spatial exploration, relief chiseling comparison, structural mold breakdown      |
|                                                                                                   |
|   PHASE 3: LIVING MAKER MASTERCLASSES (P3_MAKER_MASTERCLASS) [Available in Repo]                  |
|   • Module mod-p3-01: Acoustic Tuning & Bronze Pouring with Master Cửu / Sinh (Phường Đúc Guild)  |
|   • Module mod-p3-02: Hue Vitreous Enamel (Pháp Lam) Masterclass with Master Đỗ Hữu Triết         |
|   • Pedagogy: Active foundry practicum, clay preparation, acoustic pitch discernment, 850°C kiln  |
|                                                                                                   |
|   PHASE 4: ACCREDITED SCHOOL CURRICULUM (P4_ACCREDITED_CURRICULUM) [Roadmap 2027–2028]            |
|   • Module mod-p4-01: Hue Heritage Micro-Credential Curriculum Framework (Secondary Schools)      |
|   • Module mod-p4-02: Museum & Artisan Guild Experiential Practicum Framework (HMCC Collaboration)|
|   • Pedagogy: Structured fieldwork investigation logs, Open Badges, ethics protocols for elders   |
|                                                                                                   |
+───────────────────────────────────────────────────────────────────────────────────────────────────+
```

### 5.3 Client Route Implementation & Component Verification
The educational route (`frontend/src/app/learn/page.tsx`) was audited for accessibility, responsive layout, and epistemic honesty:
1. **Interactive Phase & Audience Filtering:** Visitors can filter modules by phase (`All`, `Phase 1`, `Phase 2`, `Phase 3`, `Phase 4`) and by target audience (`visitor`, `student`, `educator`).
2. **Epistemic Honesty Badges:** Phase 4 modules are explicitly tagged with `status: "roadmap_phase_2"`, clearly communicating to competition evaluators that accredited school credentials represent a 2027–2028 roadmap goal rather than an existing commercial feature.
3. **WCAG 2.2 AA Compliance:** All filter tabs and roadmap cards implement minimum $44\times 44$px touch targets and visible focus indicators (`--rbpc-focus: #1E675A`).
4. **Bilingual Copy Verification:** Verified across Vietnamese (`vi`) and English (`en`) via `frontend/src/lib/rbpc/copy.ts` and `frontend/src/components/rbpc/createLearnComponents.test.ts`.

---

## 6. Empirical Test Execution Ledger & Verification Matrices

### 6.1 Backend Automated Test Matrix (Pytest)

| Test File | Test Identifier | Verification Objective | Result | Status |
|---|---|---|:---:|:---:|
| `test_partner_security.py` | `test_unauthenticated_partner_endpoints_return_401` | Verifies unauthenticated callers receive HTTP 401 across all partner endpoints. | 401 Unauthorized | **PASS** |
| `test_partner_security.py` | `test_cross_provider_access_returns_403` | Verifies Partner A cannot access or patch Partner B's inquiries. | 403 Forbidden | **PASS** |
| `test_partner_security.py` | `test_non_staff_editor_consent_returns_403` | Verifies non-staff users cannot mutate artisan consent. | 403 Forbidden | **PASS** |
| `test_partner_security.py` | `test_provider_inquiry_scoping` | Verifies `GET /api/v1/rbpc/partner/inquiries` filters by authenticated provider ID. | Scoped List | **PASS** |
| `test_partner_security.py` | `test_valid_inquiry_state_transitions_and_audit` | Verifies sequence `new` $\rightarrow$ `contacted` $\rightarrow$ `confirmed` $\rightarrow$ `closed` with hash chain. | Audit Chain Valid | **PASS** |
| `test_partner_security.py` | `test_invalid_inquiry_state_transitions` | Verifies skipping states or reopening `closed` inquiries is rejected. | 400 Invalid Transition | **PASS** |
| `test_partner_security.py` | `test_editor_creator_consent_workflow_and_revocation_effect` | Full lifecycle verification: `consented` $\rightarrow$ `pending_review` $\rightarrow$ `revoked` blocks profiles & workshops. | 404 Fail-Closed | **PASS** |
| `test_inquiry_hardening.py` | `test_missing_or_unaccepted_consent_rejection` | Verifies unaccepted consent checkbox rejects submission with HTTP 422. | 422 Unprocessable | **PASS** |
| `test_inquiry_hardening.py` | `test_idempotency_replay_and_conflict` | Verifies replay returns cached 202; conflicting parameters return 409. | 202 Replay / 409 | **PASS** |
| `test_inquiry_hardening.py` | `test_invalid_client_uuid_idempotency_key` | Verifies malformed idempotency keys are rejected. | 422 Unprocessable | **PASS** |
| `test_inquiry_hardening.py` | `test_status_lookup_zero_pii_leakage` | Verifies opaque token lookup exposes zero visitor PII. | Zero PII | **PASS** |
| `test_inquiry_hardening.py` | `test_rate_limit_enforcement` | Verifies rate limiting halts spam submissions (max 5/hour). | 429 Too Many Req | **PASS** |
| `test_audit_trail.py` | `test_creator_consent_modification_audit_chain` | Verifies SHA-256 hash chaining on artisan consent updates. | Cryptographic Chain | **PASS** |
| `test_audit_trail.py` | `test_tamper_detection_in_hash_chain` | Verifies modifying diff payload breaks cryptographic validation. | Tamper Detected | **PASS** |
| `test_commercial_seed.py` | `test_commercial_idempotency_and_revocation_preservation` | Verifies re-importing YAML preserves manual consent revocations. | Preserved | **PASS** |
| `test_openapi_snapshot.py` | `test_openapi_schema_matches_snapshot` | Verifies zero OpenAPI drift across all route schemas. | Byte-for-byte Match | **PASS** |

### 6.2 Frontend Automated Test Matrix (Vitest)

| Test File | Test Suite / Case | Verification Objective | Result | Status |
|---|---|---|:---:|:---:|
| `createLearnComponents.test.ts` | `CreatorProfileCard Component Contract` | Verifies artisan profile displays lineage, tradition, and fail-closed notice on revocation. | 3/3 passed | **PASS** |
| `createLearnComponents.test.ts` | `ExperienceCard Component Contract` | Verifies inquiry-only availability mode, duration, transparent pricing, and notice. | 3/3 passed | **PASS** |
| `createLearnComponents.test.ts` | `InquiryFormModal Component Contract` | Verifies explicit consent checkbox, anti-spam validation, and concept demonstration banner. | 5/5 passed | **PASS** |
| `createLearnComponents.test.ts` | `LearnRoadmapCard Component Contract` | Verifies 4-phase roadmap progression, 3D linkages, and bibliographic source counts. | 3/3 passed | **PASS** |
| `storyArtisanBridge.test.ts` | `StoryArtisanBridge Component Contract` | Verifies seamless transition from imperial history story to living maker profile. | 21/21 passed | **PASS** |
| `inquiriesPages.test.ts` | `Inquiry Submission & Partner Inbox Views` | Verifies client-side inquiry submission and partner inbox state transitions. | 13/13 passed | **PASS** |
| `exploreComponents.test.ts` | `LivingBridgeCard & Explore Feed Contracts` | Verifies fail-closed privacy safeguard in Explore feed when consent is revoked. | 50/50 passed | **PASS** |

---

## 7. Compliance Verification & Sign-Off Checklist

```
+───────────────────────────────────────────────────────────────────────────────────────────────────+
|                      AGENT 07 PHASE 7 COMPLIANCE VERIFICATION CHECKLIST                           |
+───────────────────────────────────────────────────────────────────────────────────────────────────+
| [X] MANDATE 1: Living Artisan Consent Lifecycle Audit                                              |
|     - States 'consented', 'pending_review', 'revoked' formalized in ORM and Pydantic schemas.      |
|     - Administrative endpoint POST /editor/creators/{id}/consent enforced with STAFF_ROLES.       |
|     - Re-import seed idempotency strictly preserves manual consent revocations.                   |
|                                                                                                   |
| [X] MANDATE 2: Fail-Closed Consent Revocation Proof                                               |
|     - Public creator profile lookup returns HTTP 404 RBPC_CREATOR_NOT_FOUND when revoked.         |
|     - Associated workshop offering returns HTTP 404 RBPC_EXPERIENCE_NOT_FOUND when revoked.       |
|     - Story detail endpoint omits creator and experience objects when creator consent is revoked. |
|     - Inquiry submission returns HTTP 400 RBPC_CREATOR_CONSENT_UNAVAILABLE.                       |
|     - Client components render dignified privacy notice and withhold all personal portraits/bios. |
|                                                                                                   |
| [X] MANDATE 3: Inquiry State Machine & Provider Isolation                                         |
|     - States 'new' -> 'contacted' -> 'confirmed'/'declined' -> 'closed' verified sequentially.    |
|     - Multi-tenant provider scoping enforced in database queries.                                 |
|     - Cross-provider unauthorized mutations rejected with HTTP 403 FORBIDDEN_SCOPE.               |
|     - Cryptographic SHA-256 hash chaining active on all state transitions in rbpc_content_audit.  |
|     - Zero-PII public status lookup via high-entropy opaque bearer tokens.                        |
|                                                                                                   |
| [X] MANDATE 4: Educational Bridge (/learn) Verification                                           |
|     - 4-Phase pedagogical framework connecting archives (P1), 3D (P2), makers (P3), schools (P4). |
|     - Clear epistemic distinction between implemented tech and 2027-2028 school curriculum.       |
|     - Full WCAG 2.2 AA accessibility and bilingual language support verified.                     |
|                                                                                                   |
+───────────────────────────────────────────────────────────────────────────────────────────────────+
```

---

## 8. Section VIII — Verification, Compliance Audit & Test Evidence (Phase 7)

This section serves as the formal Section VIII compliance report for **Phase 7 (Test creator consent, inquiries, partner controls, and educational experience)** executed by **AGENT 07 (Frontend Create & Learn Engineer / Phase 7 Verification Lead)**.

### 8.1 Empirical Verification of Core System Invariants

| Invariant / Requirement | Audited Artifact | Observed Behavioral Outcome | Audit Verdict |
|---|---|---|:---:|
| **Artisan Consent Lifecycle** | `models_rbpc.py`, `rbpc.py` | State transitions (`consented` $\rightarrow$ `pending_review` $\rightarrow$ `revoked`) execute cleanly; non-staff updates are blocked with HTTP 403. | **PASS** |
| **Fail-Closed Profile Cutoff** | `GET /api/v1/rbpc/creators/{slug}` | Returning HTTP 404 `RBPC_CREATOR_NOT_FOUND` immediately upon consent revocation. | **PASS** |
| **Fail-Closed Offering Hiding** | `GET /api/v1/rbpc/experiences/{slug}` | Returning HTTP 404 `RBPC_EXPERIENCE_NOT_FOUND` immediately when host artisan consent is revoked. | **PASS** |
| **Fail-Closed Story Omission** | `GET /api/v1/rbpc/stories/{slug}` | Creator and experience objects dynamically stripped (`null`) when consent is revoked. | **PASS** |
| **Fail-Closed Booking Block** | `POST /api/v1/rbpc/inquiries` | Booking requests rejected with HTTP 400 `RBPC_CREATOR_CONSENT_UNAVAILABLE`. | **PASS** |
| **Inquiry State Machine** | `PATCH /api/v1/rbpc/partner/inquiries/{id}` | State transitions follow `new` $\rightarrow$ `contacted` $\rightarrow$ `confirmed`/`declined` $\rightarrow$ `closed`; invalid jumps rejected with HTTP 400. | **PASS** |
| **Tenant Multi-Tenancy Scoping** | `GET /api/v1/rbpc/partner/inquiries` | Providers only receive inquiries linked to their own provider ID; cross-tenant updates return HTTP 403 `FORBIDDEN_SCOPE`. | **PASS** |
| **Cryptographic Hash Chaining** | `RbpcContentAudit` | Every inquiry state transition and consent mutation writes SHA-256 chained audit record; tamper detection proven. | **PASS** |
| **Zero-PII Status Tracking** | `GET /api/v1/rbpc/inquiries/status/{token}` | Returns reference, state, and notes with zero email, phone, or visitor PII. | **PASS** |
| **Re-Seed Consent Preservation** | `backend/services/heritage_import.py` | Bulk re-import preserves manual revocations and reviews without silent overwrite. | **PASS** |
| **Educational Bridge (/learn)** | `frontend/src/app/learn/page.tsx` | 4-Phase pedagogical pathway active; interactive filters responsive; Phase 4 labeled as 2027–2028 roadmap. | **PASS** |

### 8.2 Automated Test Suite Execution Evidence

```bash
# ==============================================================================
# 1. Full Backend RBPC Security, Hardening & Audit Test Suite
# ==============================================================================
pytest tests/backend/test_partner_security.py \
       tests/backend/test_inquiry_hardening.py \
       tests/backend/test_audit_trail.py \
       tests/backend/test_commercial_seed.py \
       tests/backend/test_rbpc_endpoints.py \
       tests/unit/test_ai_benchmark_suite.py \
       tests/unit/test_rbpc_ai.py -v

# Results: 80 passed in 18.48s (100% pass rate)
# Coverage Highlights:
# - test_partner_security.py: 7 passed (scoping, RBAC, state transitions, fail-closed revocation)
# - test_inquiry_hardening.py: 7 passed (consent validation, idempotency, anti-spam, zero-PII)
# - test_audit_trail.py: 7 passed (SHA-256 hash chains, tamper detection, 90-day retention purge)
# - test_commercial_seed.py: 11 passed (YAML validation, re-import revocation preservation)
# - test_rbpc_endpoints.py: 9 passed (public discovery, AI tutor bridge, metrics verification)
# - test_ai_benchmark_suite.py: 33 passed (30-question benchmark, prompt injection defense)
# - test_rbpc_ai.py: 6 passed (epistemic honesty, 5-point citation validator)

# ==============================================================================
# 2. Strict OpenAPI Snapshot Validation (Byte-for-Byte Contract Lock)
# ==============================================================================
pytest tests/backend/test_openapi_snapshot.py -v
# Results: 1 passed in 2.67s (Zero contract drift)

# ==============================================================================
# 3. Frontend Unit & Component Contract Test Suite (Vitest)
# ==============================================================================
npm --prefix frontend test
# Results: 13 test files passed, 210 tests passed in 2.19s (100% pass rate)
# Coverage Highlights:
# - createLearnComponents.test.ts: 14 passed (CreatorProfileCard, ExperienceCard, InquiryFormModal, LearnRoadmapCard)
# - storyArtisanBridge.test.ts: 21 passed (Story-to-Maker transitions, fail-closed privacy safeguards)
# - inquiriesPages.test.ts: 13 passed (Inquiry modal validation, partner inbox state updates)
# - exploreComponents.test.ts: 50 passed (LivingBridgeCard, fail-closed privacy fallback)
# - media.test.ts: 23 passed (Rights clearance, Sketchfab license verification)

# ==============================================================================
# 4. Strict Frontend Code Quality (ESLint Flat Config & TypeScript Typecheck)
# ==============================================================================
npm --prefix frontend run lint:ci
# Results: 0 errors, 0 warnings (--max-warnings=0 passed cleanly)

npm --prefix frontend run type-check
# Results: Clean compilation across 100% of Next.js App Router files
```

---

## 9. Conclusion & Final Status

All four mission mandates for Phase 7 of LƯU NIÊN RBPC 2026 have been empirically verified, hardened against privilege escalation and regression, and validated by comprehensive unit, integration, and contract test suites. The creator consent lifecycle fails closed deterministically across public profiles, workshop offerings, story bridges, and booking inquiries. Partner multi-tenancy is cryptographically audited and strictly isolated, and the educational pathway provides an honest, source-grounded learning framework aligned with UNESCO SDG 4.

**Final Audit Status:** `PASS`

---
*Section VIII verified and signed off by AGENT 07 (Frontend Create & Learn Engineer / Phase 7 Verification Lead) for Phase 7 of LƯU NIÊN RBPC 2026.*
