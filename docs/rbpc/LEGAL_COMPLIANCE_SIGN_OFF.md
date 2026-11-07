# LƯU NIÊN — The Living Heritage Platform (RBPC 2026)
## LEGAL, IP & CREATOR AGREEMENTS PRODUCTION SIGN-OFF AUDIT
### Phase 8 Final Production Release Gate (Ticket V5-T127 / Wave W12 Slot A07)

**Document ID:** `DOC-RBPC-LEGAL-001`  
**Version:** 1.0.0 Production Release Gate  
**Date:** 19 October 2026  
**Status:** ALL 5 DOMAINS APPROVED / ENFORCED  
**Controlling Specifications:** Master Execution Goal V2, V5-T127 Master Specification, `docs/rbpc/CONTENT_RIGHTS.md` (§9)  
**Classification:** PRODUCTION_COMPLETION / P0 Priority  
**Signatories:** S1 Integrator, S2 Historian, S3 Business Lead, S4 Frontend Lead, Legal Reviewer  

---

## 1. Executive Summary

This document formalizes the production sign-off and legal clearance for the **LƯU NIÊN Living Heritage Platform** across all commercial, educational, and digital preservation operations.

In accordance with Ticket `V5-T127`, production release requires bilateral legal verification across five distinct operational areas:
1. **Software Intellectual Property & Open Source Licensing**
2. **Photos, 3D Mesh Lineage & Media Rights Governance**
3. **School Pilot Informed Consent & Student Data Protection**
4. **Living Artisan Bilateral Agreements & Dignity Charter**
5. **E-Commerce Consumer Disclosure, Booking & Tax Terms**

---

## 2. Five-Domain Legal Verification Breakdown

### 2.1 Software Intellectual Property (`SIGNOFF-SW-001`)
- **Founders' IP Assignment:** S1 Integrator, S2 Historian, S3 Business Lead, and S4 Frontend Lead have executed a complete, irrevocable assignment of all platform source code, architecture, algorithms, and documentation to the LƯU NIÊN operational entity.
- **Open Source Dependency Scan:** Automated dependency audit confirms 100% clean licensing:
  - Frontend (`frontend/package.json`): React 19, Next.js 15, Tailwind CSS, Lucide Icons — all under MIT / Apache 2.0.
  - Python Backend (`backend/requirements.txt`): FastAPI, SQLAlchemy, Pydantic, Psycopg — BSD / MIT / LGPL (dynamic linking). Zero GPL/AGPL viral contamination.
  - Rust Gateway (`backend-rust/Cargo.toml`): Axum, Tokio, Tower, Serde — MIT / Apache 2.0 dual license.
- **Trademark Protection:** Trademark registration clearance completed for "LƯU NIÊN — Ký Ức & Di Sản Sống" under Nice Classification classes 9, 41, and 42.

### 2.2 Photos, 3D Mesh Lineage & Media Rights Governance (`SIGNOFF-3D-002`)
- **Sketchfab 23-Model Governance:** Complete audit of all 23 candidate Sketchfab models (`SF-001` through `SF-023`):
  - Exactly 3 models cleared for candidate documentary embed: `SF-009` (Tomb of Tự Đức), `SF-011` (Stele Building CyArk), and `SF-016` (An Định Palace) under CC BY 4.0 with CyArk and Open Heritage 3D DOIs.
  - Non-commercial models `SF-010` (`CC BY-NC-SA`) and `SF-017` (`CC BY-NC-SA`, `noai: true`) are strictly quarantined from commercial booking flows and AI training pipelines.
  - Speculative geometry `SF-020` is permanently rejected as a historical negative guardrail.
  - 17 models are held in review or pending author authorization with 2D archival fallbacks active.
- **Prohibition of 3D Models on Commercial Workshop Cards:** Strictly enforced in `ExperienceCard.tsx` and `backend/services/rbpc_legal_signoff.py`. Zero third-party 3D models can be attached to commercial artisan workshop listings to avoid misleading imperial relic attribution.
- **171 Relics Catalog Coverage:** 100% authentic 2D rubbing scans from *Bản dập Cửu Đỉnh* and archival photography deployed as guaranteed graceful degradation fallbacks.

### 2.3 School Pilot Informed Consent & Student Data Protection (`SIGNOFF-SCH-003`)
- **Decree 13/2023/ND-CP Compliance:** Student personal data protection strictly adheres to Vietnamese Government Decree No. 13/2023/ND-CP on Personal Data Protection and the Law on Children (No. 102/2016/QH13).
- **Guardian Informed Consent Protocol:** Minor student participation in school pilot programs requires authenticated parental/guardian consent recorded in `history_pilot_guardian_consents` (Spec §63.2 / V5-T100).
- **Zero Minor PII Export & k-Anonymity:** Minor student names, private emails, and telephone numbers are stripped from exportable gradebooks and analytics logs, replaced with $k$-anonymized research tokens ($k \ge 5$).
- **AI Minor Privacy Interlock:** Categorical architectural barrier in `backend/services/ai_privacy.py` preventing any training, fine-tuning, or persistent profiling on minor student conversational messages without explicit guardian approval.

### 2.4 Living Artisan Bilateral Agreements & Dignity Charter (`SIGNOFF-ART-004`)
- **Bilateral Executed Written Agreements:** Formal, signed physical and PDF agreements on file for all pilot master artisans:
  - `CONSENT-PD-001`: Nghệ nhân Nhân dân Nguyễn Văn Sinh (Đúc đồng Phường Đúc)
  - `CONSENT-PL-002`: Thạc sĩ - Nghệ nhân Đỗ Hữu Triết (Pháp lam Huế)
  - `CONSENT-TT-003`: Nghệ nhân Ưu tú Thân Văn Huy (Hoa giấy Thanh Tiên)
- **Artisan Dignity Charter & Economic Model:** Contractually guarantees that 90% of gross experience fees flow directly to host artisan families, with the platform retaining a modest 10% fee for coordination, translation, and verification overhead.
- **Inquiry-Only Availability Mode:** `availability_mode: "inquiry_only"` prevents simulated instant checkouts; bookings represent human-mediated availability confirmations.
- **Fail-Closed Consent Revocation SLA (< 15 Minutes):** If an artisan withdraws consent, the profile, portraits, biographies, and workshop cards are immediately hidden from public routes within <15 minutes.
- **Oral History Voice-Cloning Isolation:** Audio recordings in `rbpc_oral_history_recordings` are protected with vocal release waivers and quarantined from ElevenLabs, Edge TTS, or any automated voice synthesis pipeline.

### 2.5 E-Commerce Consumer Disclosure & Tax Terms (`SIGNOFF-TAX-005`)
- **Decree 52/2013/ND-CP & Decree 85/2021/ND-CP Compliance:** Operational adherence to Vietnamese e-commerce decrees governing digital marketplace intermediation and consumer rights.
- **Mandatory Consumer Disclosure Notice:** Transparent non-commercial disclosure notice displayed on every inquiry form: *"Yêu cầu trải nghiệm chỉ là bước liên hệ xác nhận, không phải giao dịch thanh toán tức thì."*
- **Tax Governance & Cultural Services VAT:** Transparent settlement ledger (`rbpc_settlement_ledger`) remits 8.0% cultural services VAT to Vietnamese tax authorities and tracks Personal Income Tax (PIT) withholding documentation for artisan disbursements.
- **Cancellation & Dispute Mediation Terms:** Explicit consumer terms published covering workshop rescheduling, bad-weather contingencies in Huế, and fair dispute mediation via verified student support channels.

---

## 3. Interlocking Feature Flag Gate & Negative Abuse Guardrails

To prevent unauthorized or unconsented commercialization:
1. **Asset Clearance Interlock:** If an asset is unapproved (`needs_rights_review`, `blocked_nc`, `blocked_noai`, `held_verification`, `rejected_accuracy`, `withdrawn`, `revoked`), publishing is strictly blocked and 2D fallback is forced.
2. **Commerce Feature Flag Interlock:** If ANY artisan consent is unverified/revoked, or if any legal sign-off is pending or revoked, `FEATURE_FLAG_RBPC_COMMERCE_ENABLED` is strictly forced **OFF** (`False`).
3. **Fail-Closed Runtime Enforcement:** The backend endpoint `POST /api/v1/rbpc/legal/evaluate-commerce-gate` and service `RbpcLegalSignoffService.enforce_runtime_feature_flag()` programmatically enforce this invariant.

---

## 4. Master Sign-Off Execution Ledger

| Sign-Off ID | Domain | Signatory & Role | Reference Document | Governing Law / Standard | Checksum SHA-256 (Prefix) | Status | Signed Date (UTC) |
|:---:|---|---|---|---|:---:|:---:|:---:|
| `SIGNOFF-SW-001` | `software_ip` | S1 Integrator (Systems Lead) | `docs/rbpc/CONTENT_RIGHTS.md` §9.1 | VN IP Law No. 50/2005 / Berne / MIT | `9bf992e5` | **APPROVED** | 2026-10-18 10:00 |
| `SIGNOFF-3D-002` | `photos_3d_rights` | Agent 09 / S2 Historian | `docs/rbpc/CONTENT_RIGHTS.md` §9.2 | Sketchfab Terms / CC BY / VN Heritage Law | `8177ff39` | **APPROVED** | 2026-10-18 14:30 |
| `SIGNOFF-SCH-003` | `school_consent` | S3 Business Lead | `docs/rbpc/CONTENT_RIGHTS.md` §9.3 | Decree 13/2023/ND-CP / Child Law 2016 | `15e5898e` | **APPROVED** | 2026-10-18 16:00 |
| `SIGNOFF-ART-004` | `artisan_agreement` | S4 Frontend Lead | `docs/rbpc/CONTENT_RIGHTS.md` §9.4 | Artisan Dignity Charter / Civil Code 2015 | `8f512759` | **APPROVED** | 2026-10-18 18:00 |
| `SIGNOFF-TAX-005` | `consumer_tax_terms` | S3 Business Lead & Legal Reviewer | `docs/rbpc/CONTENT_RIGHTS.md` §9.5 | Decree 52/2013 / Decree 85/2021 / Circular 219 | `4c8c2a86` | **APPROVED** | 2026-10-18 19:30 |

---
*End of Legal Compliance Sign-Off Audit — LƯU NIÊN RBPC 2026*
