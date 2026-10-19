# LƯU NIÊN — RBPC 2026: ARCHITECTURAL & STRATEGIC DECISIONS (PHASE 0)

**Date:** 17 October 2026 | **Status:** APPROVED | **Gate:** G0

---

## ADR 01: Product Branding Architecture
- **Decision:** The top-level product brand is **LƯU NIÊN — The Living Heritage Platform** (Vietnamese: *Lưu Niên — Di sản sống*).
- **Rationale:** The legacy brand *Lưu Niên Sử Kí* and its Cửu Đỉnh-only identity restricted the platform to an edtech school LMS about 9 imperial urns. The new brand covers the entirety of Huế heritage, living craft practitioners, and commercial experience discovery.
- **Scope Isolation:** The Nine Dynastic Urns (*Cửu Đỉnh*) remain as an authentic, featured historic collection card on `/explore`, but no longer dictate the homepage, navigation, or AI persona. Historical proper nouns remain untouched in factual texts.

---

## ADR 02: API Namespacing & Route Dispatching
- **Decision:** All new RBPC endpoints are strictly additive and placed under two dedicated namespaces:
  1. `/api/v1/heritage/*` — Huế-wide heritage knowledge catalogue, places, relations, media assets, and search.
  2. `/api/v1/rbpc/*` — Commercial MVP slice: stories, Cultural Bridge AI, consented creator profiles, experience offerings, and booking inquiries.
- **Routing Implementation:** Handled via the existing Rust gateway's fallback mechanism (`.fallback(gateway::fallback_to_python)`). Requests proxy directly to FastAPI without requiring native Rust handler development during initial phases.
- **OpenAPI Synchronization:** Route inventory updated via `scripts/dev/generate_route_inventory.py`, and snapshots deliberately updated via `tests/backend/test_openapi_snapshot.py`.

---

## ADR 03: Additive Database Schema & Migration Strategy
- **Decision:** New tables (`heritage_places`, `heritage_source_evidence`, `heritage_media_assets`, `rbpc_stories`, `rbpc_creators`, `rbpc_experiences`, `rbpc_inquiries`) will be created via an additive Alembic migration.
- **Trunk Alignment:** Migration branches directly off `0053_user_mission_quest_compound_indexes`.
- **Constraint Safety:** All new enum-like columns will be stored as PostgreSQL `TEXT` with Python `Enum` validation to avoid PostgreSQL DDL table locks and satisfy `scripts/ci/lint-migration-safety.sh`. Zero destructive operations (`DROP`, `ALTER TYPE`, `RENAME`) permitted.

---

## ADR 04: AI Cultural Bridge & Fail-Closed Scoping
- **Decision:** Parameterize the AI Tutor with `HeritageScope` (`RBPC_HUE` vs `CUU_DINH`).
- **Retrieval Engine:** Scoped strictly to verified claims and sources with `content_scope = 'RBPC_HUE'`.
- **Delimiters & Citations:** Delimited prompt structure (`[[[CLAIM_START]]] ... [[[CLAIM_END]]]`) prevents prompt injection. Every citation is verified across 5 checks (UUID, DB lookup, retrieval set presence, claim-source join, locator check).
- **Router Integration:** Use `https://router.theclaracare.com/v1` with model `gemini-3.8-flash-tiered`. For vector search, rely on existing lexical/token overlap ranking in `history_tutor.py` to prevent HTTP 400 errors from the embedding-less Clara router.
- **Fail-Closed Fallback:** When external LLM APIs fail or claims are absent, fall back to deterministic database-backed summaries; never hallucinate.

---

## ADR 05: Sketchfab 3D Media Governance & Copyright Gate
- **Decision:** Implement a strict Rights Decision Gate for external 3D embeds.
- **Rejections:** `SF-020` is permanently rejected as inaccurate/imagined.
- **Restrictions:** `SF-010` and `SF-017` (`CC BY-NC-SA` / `NoAI`) are blocked from commercial self-hosting or AI training.
- **Embeds:** `SF-009`, `SF-011`, and `SF-016` (`CC BY`) are permitted for user-initiated lazy iframe embeds with prominent attribution.
- **2D Fallback:** Any asset without cleared rights defaults to a licensed 2D photograph and citation card.

---

## ADR 06: Honest Commercial Conversion (Inquiry vs Booking)
- **Decision:** The commercial flow implements a **Booking Inquiry / Request** workflow (`InquiryForm.tsx`), NOT a simulated instant checkout.
- **Transparency:** The interface explicitly informs the visitor: *"Request received. The provider has not confirmed availability yet."*
- **Privacy & Idempotency:** Inquiries require client-generated UUID idempotency keys, explicit unchecked consent checkboxes, and status tracking via high-entropy opaque tokens (no auto-incrementing integer IDs).

---

## ADR 07: Preservation of STTTNNĐ Assets
- **Decision:** The separate STTTNNĐ aerial-map and heritage annotation project (`/dai-noi`) is strictly quarantined. No RBPC migration or rebranding shall touch, delete, or redirect `/dai-noi` routes or its underlying annotation datasets.
