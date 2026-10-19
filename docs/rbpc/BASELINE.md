# LƯU NIÊN — RBPC 2026: BASELINE AUDIT CONSOLIDATION (PHASE 0)

**Date:** 17 October 2026 | **Base Commit:** `e19aebc0e7f66f7863659fd658c204739e199687`  
**Branch:** `feat/rbpc-cultural-bridge-2026` | **Gate:** G0 PASS  
**Audited By:** 10 Concurrent Subagents across Engineering, AI, UX, Heritage, 3D Rights, and Business.

---

## 1. Repository & Architecture State

- **Monorepo Topology:**
  - Active Python backend: modular `backend/` package (`backend/app.py` factory, `backend/main.py` shim, 15 domain routers, 55 services, 91 SQLAlchemy tables).
  - Obsolete monolith files at root (`main.py` ~18.3k lines, `models.py`, `schemas.py`, `seed.py`, `config.py`, `rbac.py`, `security.py`, `errors.py`, and root `versions/` terminating at revision 0037) are confirmed inactive and unimported.
  - Rust gateway: `backend-rust/` with ~168 native Axum handler bindings across 20 route groups. Strangler Fig fallback proxies unmatched routes to Python FastAPI.
  - Frontend: Next.js 15.0.0, React 19.2.3, TailwindCSS, Zustand, Three.js/R3F, Leaflet, Radix UI.
  - Mobile: Flutter client (`mobile/`, v1.5.0+6) with Riverpod code generation.

---

## 2. CI/CD & Baseline Failures Root Cause Analysis

1. **Frontend E2E Login Test Strict-Mode Violation (`ci.yml`)**:
   - *Location:* `frontend/src/components/LoginPage.tsx` (lines 64–75 vs 149–155).
   - *Cause:* Both the segmented mode toggle `<button>` and the form submit `<button>` expose the identical accessible name `"Đăng nhập"`. Playwright's `getByRole('button', { name: 'Đăng nhập' })` in `smoke.spec.ts` fails with a strict-mode violation because 2 elements match.
   - *Scheduled Fix (Phase 2):* Use semantic `role="tab"` for the mode switcher and distinct accessible labels for form submission.

2. **Deploy Workflow Failure (`deploy.yml`)**:
   - *Location:* `.github/workflows/deploy.yml` step `appleboy/ssh-action`.
   - *Cause:* Secret `SERVER_HOST` is unset in the GitHub environment `production`. Production deployments are executed via `./scripts/deployment/deploy-safe.sh`.

3. **Database Migration Heads**:
   - Real migrations live in `migrations/versions/` (67 revision files).
   - Active trunk head is `0053_user_mission_quest_compound_indexes`.
   - Alembic reports 14 heads due to unmerged historical feature branches. The new RBPC additive migration must branch explicitly from `0053`.

---

## 3. Infrastructure & Staging Specification

- **Target VPS:** IP `36.50.27.240`, User `root`, Port `22`.
- **Domain:** `luunien.histolab.icu` proxied through Cloudflare.
- **WebRTC UDP Media Warning:** Cloudflare CDN drops UDP packets. Port ranges `50000-50100/udp` (LiveKit) and `20000-20100/udp` (Janus) must bind directly to public IP `36.50.27.240`.
- **API Router Verified:** Live test against `https://router.theclaracare.com/v1/chat/completions` using model `gemini-3.8-flash-tiered` succeeded (HTTP 200 OK, latency ~1.2s). Embeddings are not supported on this router; lexical ranking in `history_tutor.py` will be used for grounding.

---

## 4. Heritage & 3D Copyright Baseline

- **UNESCO 14 Components (678-001 to 678-014):**
  - Mapped as the official structural taxonomy for Huế heritage.
  - `678-001` (Kinh thành Huế) acts as the parent container enclosing the Citadel, Imperial City, and Thế Miếu (where Cửu Đỉnh is located).
- **Sketchfab 23 Model Inventory (SF-001 to SF-023):**
  - `SF-020` (`nguyenduc0`) is **EXPLICITLY REJECTED** as an unverified, imagined architectural model (negative-test guardrail).
  - `SF-010` (Agisoft) and `SF-017` (Miguel Bandera) are **BLOCKED** from commercial redistribution and AI ingestion due to `CC BY-NC-SA` and `NoAI` restrictions.
  - `SF-009` (Tự Đức Tomb), `SF-011` (Stele Building), and `SF-016` (An Định Palace) are **CC BY** candidates for safe embedding with attribution.
  - In all unverified cases, the platform defaults to a 2D image and citation fallback.

---

## 5. Strategic & Business Baseline

- **Verified In-Kind Sponsorship Total:** **202,360,638 VND** (BNIX 1,142,400 VND + Phổ Tuệ 201,218,238 VND). The verbal claim of "206M VND" is unverified and rejected. In-kind compute credits are not revenue or cash.
- **RMIT Rule 4.3 Eligibility:** Officially logged as `RBPC_ELIGIBILITY = UNRESOLVED` pending written confirmation from `RBPC@rmit.edu.vn`.
- **Pilot Journey:** `Sourced Story (Explore) → Consented Artisan (Create) → Experience Listing → Availability Inquiry (NOT instant booking)`.
- **STTTNNĐ Safety:** Protected aerial map routes (`/dai-noi`) and annotation datasets are strictly quarantined and preserved.
