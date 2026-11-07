# LƯU NIÊN — The Living Heritage Platform
## RBPC 2026: STARTUP EVIDENCE ROOM SPECIFICATION & VERIFICATION DOSSIER

**Document ID:** `DOC-RBPC-EVID-ROOM-001`  
**Version:** 1.0.0 Final  
**Date:** 07 November 2026  
**Auditor / Role:** W11-A10 (Ticket V5-T120)  
**Classification:** NEW_PRODUCT_FEATURE / DUE DILIGENCE & GOVERNANCE  
**Status:** APPROVED FOR INVESTOR DUE DILIGENCE & RBPC DOSSIER  
**Controlling Documents:** `DOC-RBPC-EXH-011` (`PITCH_EXHIBITS.md`), `DOC-RBPC-FIN-001` (`FINANCIAL_ASSUMPTIONS.md`), `DOC-RBPC-STRAT-001` (`PITCH_THESIS.md`), `DOC-RBPC-EVID-001` (`MARKET_CLAIMS_EVIDENCE_REGISTER.md`)

---

## 1. Executive Purpose & Governance Architecture

The **LƯU NIÊN Startup Evidence Room** serves as the authoritative, versioned truth foundation for all corporate, investor, and academic reviews in the **RMIT Business Plan Competition (RBPC) 2026**. 

In conventional startup pitches, quantitative slides frequently contain ungrounded verbal claims, inflated TAM figures, or synthetic traction metrics. Under the **V5-T120 Governance Charter**, every single quantitative slide assertion must cite a versioned, cryptographically hashed evidence pointer across **7 Canonical Domains**:

1. **`product`**: 3D/AR WebGL models, primary source lineage, and delimited AI tutor pipelines.
2. **`customer`**: 5-stage value journey, Citadel field intercepts, and consented living master records.
3. **`market`**: Bottom-up TAM/SAM/SOM sizing and OTA commission arbitrage audits.
4. **`finances`**: Multi-scenario unit economics, audited corporate sponsorship runway, and dual P&L pro-forma.
5. **`impact`**: UN SDG 8 (90% direct artisan share, 50% commission pledge) and UN SDG 4 (100% cited provenance).
6. **`legal`**: Bilingual creator consent agreements, 24-hour right of erasure SLA, and executed corporate contracts.
7. **`team`**: Multidisciplinary student founders (S1–S4 cap table) and institutional advisory roster.

---

## 2. Negative Abuse Invariant & Pitch Review Guardrail

> **Non-Negotiable Negative Abuse Rule (V5-T120):**
> **Every quantitative pitch claim must have an immutable evidence reference and status; ungrounded metrics are strictly flagged (`UNGROUNDED_FLAGGED`) and pitch readiness is marked `FLAGGED_UNREADY`.**

Any pitch deck slide evaluated by the automated due diligence engine (`/api/v1/rbpc/pitch-review/evaluate`) that violates this rule cannot receive `APPROVED_FOR_PITCH` status. Specifically:
- **Missing Pointer:** A quantitative assertion lacking an `evidence_pointer_id` is immediately rejected.
- **Unknown Pointer:** Referencing a non-existent pointer ID triggers a critical audit failure.
- **Non-Verified Pointer:** Referencing a pointer whose status is `archived` or `needs_review` triggers `UNGROUNDED_FLAGGED`.
- **Metric Contradiction:** Claiming numbers that contradict the audited payload (e.g., claiming 206,000,000 VND sponsorship when the executed contracts audit 202,360,638 VND, or claiming 15% platform take rate when policy is 10%) triggers `UNGROUNDED_FLAGGED`.

---

## 3. Master Evidence Room Pointer Catalog (7 Domains)

| Pointer ID | Domain | Title | Controlling Doc Ref | Version | Status | Audited Key Metrics | Owner |
|---|---|---|---|---|---|---|---|
| **EVID-PROD-001** | `product` | 3D/AR WebGL Engine & Heritage Motifs Lineage | `docs/rbpc/3D_LINEAGE_REPORT.md` | 1.0.0 | `active_verified` | 9 Urns, 162 Motifs, 3 LOD Levels, 100% 2D Rubbing Fallback | S4 Frontend Lead |
| **EVID-PROD-002** | `product` | Delimited Scoped RAG AI Tutor Pipeline | `docs/rbpc/AI_DEMO_CASES.md` | 1.0.0 | `active_verified` | Latency <1.2s, router.theclaracare.com, 100% Primary Annals Citation | S1 Integrator |
| **EVID-CUST-001** | `customer` | 5-Stage Value Journey & Visitor Intercept Discovery | `docs/rbpc/CUSTOMER_DISCOVERY_PROTOCOLS_EXPERIMENTS.md` | 1.0.0 | `active_verified` | N=50 Citadel intercepts, 78% context gap, 15% inquiry conversion | S3 Business Lead |
| **EVID-CUST-002** | `customer` | Living Master Lineage & Consent Studio Records | `docs/rbpc/CREATOR_CONSENT_AUDIT.md` | 1.0.0 | `active_verified` | 5 Verified Masters, 24h Right of Erasure SLA, EVID-ARTISAN-001 | S2 Historian |
| **EVID-MKT-001** | `market` | TAM / SAM / SOM Bottom-Up Market Sizing Model | `docs/rbpc/FINANCIAL_ASSUMPTIONS.md` | 1.0.0 | `active_verified` | TAM: 28.5B VND, SAM: 5.7B VND, SOM Y1: 1,100 experiences (570M VND) | S3 Business Lead |
| **EVID-MKT-002** | `market` | OTA Commission Arbitrage & Competitive Audit | `docs/rbpc/BUSINESS_PLAN_DRAFT.md` | 1.0.0 | `active_verified` | Mass OTAs 25-30% vs LƯU NIÊN 10%, 4.5 hrs/wk operator time saved | S3 Business Lead |
| **EVID-FIN-001** | `finances` | Unit Economics & Sensitivity Model (10/30/60 Bookings) | `docs/rbpc/PITCH_EXHIBITS.md` | 1.0.0 | `active_verified` | 700k VND avg price, 90% artisan (630k), 92.4% contrib margin, 2.9 breakeven | S3 Business Lead |
| **EVID-FIN-002** | `finances` | Documented In-Kind Corporate Sponsorship Audit | `docs/rbpc/PITCH_EXHIBITS.md` | 1.0.0 | `active_verified` | 202,360,638 VND audited actual (BNIX + Phổ Tuệ); verbal 206M rejected | S1 Integrator |
| **EVID-FIN-003** | `finances` | Dual P&L Pro-Forma: Sponsored Runway vs Commercial | `docs/rbpc/FINANCIAL_ASSUMPTIONS.md` | 1.0.0 | `active_verified` | 12M GBV: 1.05B VND, 91M net profit sponsored vs 86.4M commercial | S3 Business Lead |
| **EVID-IMP-001** | `impact` | UN SDG 8 Decent Work & Artisan Wage Retention Framework | `docs/rbpc/PITCH_EXHIBITS.md` | 1.0.0 | `active_verified` | 90% direct transfer, 50% commission youth guild pledge, +4.2M-12.6M uplift | S3 Business Lead |
| **EVID-IMP-002** | `impact` | UN SDG 4 Quality Education & Verified Open Cultural Literacy | `docs/rbpc/CUSTOMER_VALUE_METRICS.md` | 1.0.0 | `active_verified` | 100% cited provenance, 18,000+ open readers target, 5 ateliers preserved | S2 Historian |
| **EVID-LEG-001** | `legal` | Creator Oral History Consent & Right of Erasure SLA | `docs/rbpc/CONTENT_RIGHTS.md` | 1.0.0 | `active_verified` | Bilingual written consent, 24h erasure SLA, zero minor PII retention | S1 Integrator |
| **EVID-LEG-002** | `legal` | Corporate In-Kind Sponsorship Executed Contracts | `docs/rbpc/BASELINE.md` | 1.0.0 | `active_verified` | 2 executed contracts (BNIX, Phổ Tuệ), Vietnamese governing jurisdiction | S1 Integrator |
| **EVID-TEAM-001** | `team` | Core Student Founder Cap Table & S1–S4 Architecture | `docs/rbpc/PITCH_THESIS.md` | 1.0.0 | `active_verified` | 4 student co-founders (S1–S4), 4-year vesting, 120 hrs/mo commitment | S3 Business Lead |
| **EVID-TEAM-002** | `team` | Academic Advisory Board & Heritage Mentorship Roster | `docs/rbpc/PITCH_EXHIBITS.md` | 1.0.0 | `active_verified` | HMCC conservation experts, RMIT Business faculty, Craft Guild leaders | S2 Historian |

---

## 4. API Endpoints & Developer Integration

The evidence room is accessible via standard REST endpoints on the platform backend:
- `GET /api/v1/rbpc/evidence-room/pointers`: List all versioned pointers with domain and status filtering.
- `GET /api/v1/rbpc/evidence-room/pointers/{pointer_id}`: Retrieve full details and metrics payload for a pointer.
- `POST /api/v1/rbpc/pitch-review/evaluate`: Evaluate pitch claims and persist due diligence audit report.
- `GET /api/v1/rbpc/pitch-review/audits/{audit_ref}`: Retrieve an immutable pitch audit report.
- `GET /api/v1/rbpc/evidence-room/export`: Export evidence room catalog in `json` or `markdown` format.

---
**RBPC 2026 Audit Stamp:** Verified against database schema `rbpc_evidence_room_pointers` and `rbpc_pitch_reviews`.
