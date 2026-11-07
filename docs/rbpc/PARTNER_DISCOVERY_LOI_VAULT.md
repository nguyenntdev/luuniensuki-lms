# LƯU NIÊN — The Living Heritage Platform
## RBPC 2026: PARTNER DISCOVERY AND LETTER OF INTENT (LOI) VAULT
### Phase 8 Verification: Artisan Guilds, Institutional Partners, Cryptographic Agreement Evidence & Active Partner Discovery

**Document ID:** `DOC-RBPC-LOI-001`  
**Version:** 1.0.0 Final Verified  
**Date:** 2026-11-06  
**Status:** PASS / VERIFIED FOR RBPC SUBMISSION & CODEBASE AUDIT  
**Controlling Specifications:** Master Execution Goal V2, `DOC-RBPC-DISCOVERY-001` (Customer Discovery Protocols), `DOC-RBPC-AUDIT-008` (Creator Consent Lifecycle), `DOC-RBPC-VAL-001` (Validation Register), `DOC-RBPC-API-001` (API Contracts)  
**Slot:** W11-A03  
**Ticket:** `V5-T113`  
**Classification:** `NEW_PRODUCT_FEATURE`  

---

## 1. Executive Summary & Epistemic Boundaries

The **Partner Discovery and Letter of Intent (LOI) Vault** serves as the authoritative, cryptographically verified repository of bilateral partnerships between LƯU NIÊN and living heritage masters, craft guilds, educational institutions, and heritage organizations across Thừa Thiên Huế.

### 1.1 Non-Binding LOI Epistemic Classification
In strict compliance with RMIT Business Plan Competition (RBPC) 2026 guidelines and standard international venture due diligence standards:
- **Letters of Intent (LOIs) and Memoranda of Understanding (MOUs) represent pre-contractual commercial intent and collaboration frameworks.**
- They are legally distinct from finalized commercial transactions or recognized cash revenue.
- Under no circumstances may an LOI, MOU, or charter be booked or presented as recognized historical revenue.
- Projected GMV derived from LOI workshop commitments is categorized strictly as `FORECAST`, distinct from `OBSERVED` platform actuals.

### 1.2 NEGATIVE ABUSE INVARIANT (Critical Requirement V5-T113)
To protect platform integrity, prevent misleading commercial representations, and honor practitioner sovereignty:

> **REVOKED OR EXPIRED PARTNERSHIPS ARE NEVER DISPLAYED AS ACTIVE PARTNERS.**
>
> 1. **Public Discovery Exclusion:** Any partner agreement where `status != 'active'`, `consent_status != 'consented'`, `revoked_at IS NOT NULL`, or `expiration_date < CURRENT_DATE` is **strictly excluded** from public partner discovery queries (`GET /api/v1/rbpc/partners`).
> 2. **Fail-Closed Direct Lookup:** Querying a specific partner by ID or slug (`GET /api/v1/rbpc/partners/{id}`) for an expired or revoked partnership returns `HTTP 404 NOT FOUND` (`RBPC_PARTNER_INACTIVE`), completely concealing commercial listings and active verified badges.
> 3. **Raw Signature & PII Prohibition:** Raw biometric signatures, scanned citizen identity cards, personal phone numbers, and private bank documents **MUST NEVER** be committed to the public Git repository or returned in public API payloads.
> 4. **Cryptographic Checksum Verification:** Every LOI and bilateral charter is verified and tracked via a deterministic **SHA-256 cryptographic checksum** (`agreement_checksum_sha256`) of the executed document. This guarantees immutability and provenance without exposing sensitive personal data.

---

## 2. Partner Discovery Methodology & Selection Framework

### 2.1 Target Partner Categories
The LƯU NIÊN partner discovery framework focuses on four distinct institutional categories in the Huế heritage ecosystem:

| Category Code | Category Name | Description & Focus | Example Institution |
|---|---|---|---|
| `craft_guild` | Traditional Craft Guilds & Lineage Ateliers | Master artisans preserving imperial metallurgy, enamel, wood, or embroidery lineages. | Hợp tác xã Đúc đồng Phường Đúc Huế |
| `educational_institution` | Secondary & Higher Education Partners | High schools and universities integrating heritage curriculum (GDPT 2018). | CLB Di sản THPT Chuyên Quốc Học Huế |
| `cultural_association` | Cultural Heritage Collectives | Artist studios and contemporary craft innovators connecting past and present. | Không gian Nghệ thuật Trúc Chỉ Huế |
| `tourism_operator` | Heritage Tourism & Guide Collectives | Certified local guides and ethical heritage experience curators. | Chi hội Thuyết minh viên Di sản Huế |

### 2.2 Four-Pillar Partner Safeguards (Dignity Charter)
Every registered partner in the LOI Vault is bound by the **LƯU NIÊN Artisan Dignity Charter**:
1. **Practitioner Sovereignty:** Artisans maintain total ownership over their likeness, biography, and craft representations. Consent can be revoked at any time.
2. **Zero Upfront Fees:** Zero listing, hosting, or subscription fees are charged to craft partners.
3. **Transparent Take-Rate:** Platform take-rate is strictly capped at 10% on completed, verified visits (90% retained by the artisan).
4. **Data Retention & Consent Expiration:** Agreements have explicit expiration dates (max 24 months before mandatory mutual review).

---

## 3. Canonical Partner Evidence & LOI Vault Register

The vault maintains an immutable registry of verified partner agreements. Each record contains validated metadata, operational scope, bilateral consent terms, and cryptographic SHA-256 agreement checksums:

| LOI ID | Partner ID | Partner Name | Category | Scope Summary | Effective Dates | Agreement Checksum (SHA-256) | Status | Dignity Charter |
|---|---|---|---|---|---|---|---|---|
| `LOI-HUE-BRONZE-001` | `PARTNER-BRONZE-001` | Hợp tác xã Đúc đồng Phường Đúc Huế | `craft_guild` | Chế tác đồng mỹ nghệ, lưu giữ kỹ thuật đúc Cửu Đỉnh truyền thống, tổ chức workshop đúc mẫu. | 2026-01-01 to 2027-12-31 | `7b988f912445e999c0da27845ba0e64c18c17375a0df1248ab3c7a07530e3860` | `active` | ✅ True |
| `LOI-HUE-PHAPLAM-002` | `PARTNER-PHAPLAM-002` | Xưởng Pháp lam Thái Hưng Huế | `craft_guild` | Khôi phục nghệ thuật Pháp lam cung đình Nguyễn, tổ chức trải nghiệm tráng men và nung lò. | 2026-02-01 to 2027-06-30 | `23dcae32d5e78393eef1dc9ea338db714d64ef817c9b0e2ad0b0c649938b8ca7` | `active` | ✅ True |
| `LOI-HUE-TRUCCHI-003` | `PARTNER-TRUCCHI-003` | Nghệ thuật Trúc Chỉ Việt Nam - Không gian Huế | `cultural_association` | Trình diễn chế tác đồ họa trúc chỉ trên xơ tre/dừa, kết hợp họa tiết Cửu Đỉnh vào mỹ thuật ứng dụng. | 2026-01-15 to 2027-12-31 | `a1bc40285a214d4e3cb481e370e515d6ad05e04cb212e105a5a7dc64ecb90e9e` | `active` | ✅ True |
| `LOI-HUE-EMBROID-004` | `PARTNER-EMBROID-004` | Hợp tác xã Thêu Cung đình Phú Cam | `craft_guild` | Phục dựng hoa văn thêu chỉ vàng triều Nguyễn trên gấm lụa, hướng dẫn học viên thực hành thêu tay. | 2026-03-01 to 2027-08-31 | `59f42de63467c9c0d16c528f8f260335e3ec7fa6d38e65e68379b3ee42a6c8b9` | `active` | ✅ True |
| `LOI-HUE-QUOCHOC-005` | `PARTNER-QUOCHOC-005` | CLB Di sản & Sử học THPT Chuyên Quốc Học Huế | `educational_institution` | Thí điểm dự án học tập trải nghiệm tích hợp GDPT 2018, đồng tổ chức tour thực địa Cửu Đỉnh cho học sinh. | 2026-01-10 to 2027-05-31 | `a9062eb1ea2e0fb525046e7f722ec10b501cf5681aa3ee7e9114f04642ef9982` | `active` | ✅ True |
| `LOI-HUE-HMCC-006` | `PARTNER-HMCC-006` | Chi hội Hướng dẫn viên Di sản Huế (Liên kết TTBTDT Cố đô) | `tourism_operator` | Đào tạo và kiểm định thuyết minh viên di sản theo tài liệu Đại Nam Thực Lục, cung cấp tour chuyên gia. | 2026-02-15 to 2027-12-31 | `80145c256eefbfd67b255543c7262dc1e7b6d131f4228c2e2e987910ffbe97f2` | `active` | ✅ True |
| `LOI-HUE-WOOD-007` | `PARTNER-WOOD-007` | Xưởng Mộc Chạm Mỹ nghệ Hương Thủy (Đã hết hạn) | `craft_guild` | Thí điểm chạm khắc mộc mô phỏng quai vạc Cửu Đỉnh (Hợp đồng thử nghiệm 2025). | 2025-01-01 to 2025-12-31 | `8680d249f7ba3e8992ad81335ee9191d45129656461665a3c9be087799b66bb2` | `expired` | ✅ True |
| `LOI-HUE-POTTERY-008` | `PARTNER-POTTERY-008` | Doanh nghiệp Gốm Sứ Mỹ Nghệ Phước Tích (Thu hồi) | `tourism_operator` | Hợp tác tour gốm di sản (Đã chấm dứt do vi phạm quy chế định giá khách hàng). | 2026-01-01 to 2026-12-31 | `8d5be1449bca0f5236ad650085ec351ee2bc3d7bc05503b0d4aa697966ea64e3` | `revoked` | ❌ Revoked |

---

## 4. Architectural Implementation & Endpoints

### 4.1 Schema Definition (`rbpc_partner_loi_vault`)
The table `rbpc_partner_loi_vault` is defined in `backend/partner_loi_models.py` with strict indexing and additive PostgreSQL constraints:
- `loi_id`: Unique alphanumeric identifier (e.g. `LOI-HUE-BRONZE-001`).
- `partner_id`: Normalized partner business identifier.
- `agreement_checksum_sha256`: Hexadecimal SHA-256 digest of original signed bilateral LOI document.
- `expiration_date`: Temporal boundary. When `expiration_date < CURRENT_DATE`, status automatically computes as expired.
- `status` & `consent_status`: Governed by controlled enums (`active`, `expired`, `revoked`, `pending_review`).

### 4.2 API Routing & Role Guardrails
The router `backend/routers/partner_loi.py` provides RESTful access under `/api/v1/rbpc/*`:

1. `GET /api/v1/rbpc/partners`:
   - Public endpoint returning verified active partners.
   - **Enforces Negative Abuse Invariant:** Strictly filters out `status != 'active'`, `consent_status != 'consented'`, `revoked_at IS NOT NULL`, and `expiration_date < CURRENT_DATE`.
2. `GET /api/v1/rbpc/partners/{id_or_slug}`:
   - Public endpoint returning active partner profile.
   - **Enforces Negative Abuse Invariant:** Returns `HTTP 404 NOT FOUND` (`RBPC_PARTNER_INACTIVE`) if partner agreement is expired or revoked.
3. `GET /api/v1/rbpc/loi-vault`:
   - Vault listing endpoint returning full evidence records with counts of active, expired, and revoked LOIs.
4. `GET /api/v1/rbpc/loi-vault/{loi_id}`:
   - Detail lookup with agreement checksum and scope breakdown.
5. `POST /api/v1/rbpc/admin/loi-vault`:
   - Admin/Staff endpoint to register verified LOI agreement into vault.
   - Validates agreement checksum (strict 64-char hex SHA-256; rejects raw image/PII strings).
6. `POST /api/v1/rbpc/admin/loi-vault/{loi_id}/revoke`:
   - Admin/Staff endpoint to immediately revoke partnership upon breach or artisan request.
   - Instantly drops partner from public discovery.
7. `POST /api/v1/rbpc/admin/loi-vault/{loi_id}/verify-checksum`:
   - Auditing endpoint verifying provided document bytes match recorded SHA-256 digest.

---

## 5. Verification Matrix & Quality Gates

| Verification Gate | Validation Criteria | Automated Test Case | Status |
|---|---|---|---|
| **Gate 1: Canonical Register Integrity** | All 8 canonical agreements load with valid dates, categories, and 64-char SHA-256 checksums. | `test_v5_t113_canonical_register_integrity` | PASS |
| **Gate 2: Active Partner Discovery** | `GET /api/v1/rbpc/partners` returns ONLY non-expired, non-revoked active partners. | `test_v5_t113_public_partner_discovery_active_only` | PASS |
| **Gate 3: Negative Abuse (Expired Partners)** | Expired partners are NEVER displayed in discovery and fail direct lookup with 404. | `test_v5_t113_negative_abuse_expired_partner_excluded` | PASS |
| **Gate 4: Negative Abuse (Revoked Partners)** | Revoked partners are NEVER displayed in discovery and fail direct lookup with 404. | `test_v5_t113_negative_abuse_revoked_partner_excluded` | PASS |
| **Gate 5: Revocation State Transition** | Revoking an active partner immediately removes them from public discovery. | `test_v5_t113_revocation_lifecycle_and_immediate_exclusion` | PASS |
| **Gate 6: Checksum Provenance & Anti-PII** | Validates SHA-256 digest; rejects raw signatures, base64 strings, or data URIs. | `test_v5_t113_checksum_verification_and_anti_pii_guards` | PASS |
| **Gate 7: RBAC Authorization Defense** | Non-staff users cannot register or revoke vault agreements (HTTP 403 FORBIDDEN_SCOPE). | `test_v5_t113_admin_role_enforcement_and_scope_security` | PASS |
| **Gate 8: Documentation Parity** | Service exports match documentation table exactly in IDs, names, and checksums. | `test_v5_t113_documentation_and_export_parity` | PASS |

---

## 6. Conclusion & Audit Sign-Off

The Partner Discovery and LOI Vault implementation satisfies all RMIT RBPC 2026 due diligence standards, preserving artisan sovereignty, guaranteeing cryptographic document provenance without PII leakage, and enforcing fail-closed negative abuse defenses.
