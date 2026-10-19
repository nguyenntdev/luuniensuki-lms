# LƯU NIÊN — RBPC 2026: DATABASE & DATA ARCHITECTURE CONTRACTS

**Document ID:** `DOC-RBPC-DB-001`  
**Base Commit SHA:** `e19aebc0e7f66f7863659fd658c204739e199687`  
**Migration Revision:** `0054_rbpc_heritage_schema` (revises `0053_user_mission_quest_compound_indexes`)  
**Content Scope:** `RBPC_HUE` (strictly quarantined from legacy `CUU_DINH` and STTTNNĐ `/dai-noi`)

---

## 1. Executive Summary & Design Principles

The database architecture for **LƯU NIÊN — The Living Heritage Platform** introduces two dedicated, interconnected clusters of tables:
1. **Heritage Knowledge Graph (`heritage_*`)**: Models Huế's monuments, royal tombs, landscape complexes, and living craft traditions with verifiable bibliographic sources, relational ties, and rights-controlled multimedia (including 3D Sketchfab embeds).
2. **Commercial MVP Slice (`rbpc_*`)**: Powers curated bilingual storytelling, consented artisan profiles, bookable cultural workshop experiences, privacy-hardened booking inquiries, allowlisted telemetry, and immutable editorial audit logs.

### Core Non-Negotiable Invariants:
- **Strictly Additive**: Zero `DROP`, `ALTER TYPE`, or `RENAME` statements. Fully compliant with `./scripts/ci/lint-migration-safety.sh`.
- **Text-Backed Enums**: All enum-like columns are stored as PostgreSQL `VARCHAR` / `TEXT` and validated at the application tier via Python/Pydantic `Enum` classes. This eliminates PostgreSQL table locks and migration failures when adding new vocabulary.
- **Scope Isolation**: Every public entity carries a `content_scope` tag (defaulting to `'RBPC_HUE'`) to prevent cross-contamination with the legacy Cửu Đỉnh monograph or the protected STTTNNĐ aerial map project.
- **Privacy by Design**: Visitor inquiry contact channels are encrypted or access-restricted, rate-limited, and queried using high-entropy opaque tokens. Zero PII is exposed through public endpoints.

---

## 2. Entity Relational Architecture

```
[ heritage_places ] (UNESCO 14 & Huế Sites)
   │  │
   │  ├──< [ heritage_heritage_relations ] (Place-to-Place Graph)
   │  ├──< [ heritage_source_evidence ] (Bibliographical Citations)
   │  └──< [ heritage_media_assets ] (Photos, 3D Sketchfab Models with NoAI)
   │
   └──< [ rbpc_stories ] (Curated Bilingual Stories)
           │
           ├──< [ rbpc_claim_evidence ] (Verifiable Sourced Statements)
           └──< [ rbpc_events ] (Anonymous Telemetry)

[ rbpc_creators ] (Consented Living Artisans & Makers)
   │
   └──< [ rbpc_experiences ] (Workshop & Tour Listings)
           │
           └──< [ rbpc_inquiries ] (Availability Requests & State Transitions)

[ rbpc_content_audit ] (Append-only Editorial Ledger)
```

---

## 3. Detailed Table Specifications

### 3.1 `heritage_places`
Canonical registry of physical and intangible heritage in Huế.
- `id` (UUID PK): Unique identifier.
- `slug` (VARCHAR(160) UNIQUE): URL-safe identifier (e.g. `lang-tu-duc`, `kinh-thanh-hue`).
- `name_vi` (VARCHAR(255)): Canonical Vietnamese name.
- `name_en` (VARCHAR(255)): Official English designation.
- `name_han_nom` (VARCHAR(255)): Original Hán-Nôm inscription.
- `entity_type` (VARCHAR(64)): `'site'`, `'monument'`, `'building'`, `'object'`, `'landscape'`, `'intangible'`, `'community'`, `'collection'`.
- `heritage_category` (VARCHAR(64)): `'imperial_architecture'`, `'royal_tomb'`, `'craft_living_culture'`, `'music_performance'`, `'landscape_nature'`, `'religious_spiritual'`, `'museum_archive'`, `'culinary_heritage'`.
- `parent_id` (UUID FK -> `heritage_places.id` ON DELETE SET NULL): Container hierarchy (e.g., `kinh-thanh-hue` encloses `ngo-mon`, `dien-thai-hoa`).
- `official_designation` (VARCHAR(120)): e.g., `'UNESCO World Heritage'`.
- `official_reference_id` (VARCHAR(64)): e.g., `'678-001'`.
- `period_label` (VARCHAR(120)): e.g., `'Thời Nguyễn (1805–1945)'`.
- `historical_state` (VARCHAR(64)): `'standing'`, `'restored'`, `'partially_lost'`, `'archaeological'`.
- `location_lat`, `location_lon` (NUMERIC(10, 7)): WGS84 coordinates.
- `geo_precision` (VARCHAR(32)): `'exact'`, `'centroid'`, `'approximate'`.
- `current_access_status` (VARCHAR(64)): `'open_normal_hours'`, `'restricted'`, `'conservation_in_progress'`.
- `visitor_summary_vi`, `visitor_summary_en` (TEXT): Concise visitor guide.
- `historical_summary_vi`, `historical_summary_en` (TEXT): Verified historical overview.
- `editorial_status` (VARCHAR(32)): S0–S4 status (`'candidate'`, `'draft'`, `'source_backed'`, `'in_review'`, `'approved'`, `'published'`, `'withdrawn'`).
- `content_scope` (VARCHAR(32)): `'RBPC_HUE'`.

### 3.2 `heritage_heritage_relations`
Directed typed relationships between heritage places.
- `from_place_id`, `to_place_id` (UUID FKs).
- `relationship_type` (VARCHAR(64)): `'contains'`, `'contained_in'`, `'honors'`, `'architectural_twin'`, `'historical_successor'`, `'associated_craft'`, `'ceremonial_connection'`.
- `review_state` (VARCHAR(32)): `'draft'`, `'verified'`.

### 3.3 `heritage_source_evidence`
Direct linkage between primary bibliographic sources and place entities.
- `place_id` (UUID FK).
- `source_title`, `source_author`, `publisher`, `cited_section`, `cited_page`.
- `statement` (TEXT): Verbatim or localized factual statement.
- `evidence_status` (VARCHAR(32)): `'needs_review'`, `'verified'`, `'disputed'`, `'rejected'`.
- `reuse_rights` (VARCHAR(32)): `'public_domain'`, `'academic_citation'`, `'fair_use'`, `'licensed'`.

### 3.4 `heritage_media_assets`
Manages 2D photography, documents, and 3D models (including Sketchfab SF-001..SF-023).
- `place_id` (UUID FK).
- `media_type`: `'photo'`, `'sketchfab_embed'`, `'glb'`, `'audio'`, `'video'`, `'document'`.
- `source_platform`, `original_url`, `title`, `creator_name`, `creator_url`.
- `model_uid`: 32-character hexadecimal UID for Sketchfab models.
- `license_label`, `license_url`.
- `noai` (BOOLEAN): Strict flag blocking AI model harvesting.
- `commercial_use_status`: `'permitted'`, `'blocked_nc'`, `'unreviewed'`.
- `embed_permission_status`: `'permitted'`, `'denied'`, `'unreviewed'`.
- `accuracy_grade`: `'survey_grade'`, `'measured_photogrammetry'`, `'historian_reviewed'`, `'illustrative_only'`, `'rejected_accuracy'`.
- `content_status`: `'candidate'`, `'rights_reviewed'`, `'approved_embed'`, `'approved_local_file'`, `'published'`, `'blocked_nc'`, `'blocked_noai'`, `'rejected_accuracy'`.

### 3.5 `rbpc_creators`
Profiles of living craft practitioners who have provided verified written consent.
- `slug` (VARCHAR(160) UNIQUE), `public_name`, `craft_tradition`.
- `approved_bio_vi`, `approved_bio_en` (TEXT).
- `portrait_asset_url`, `public_region`, `workshop_address_approx`.
- `lineage_notes` (TEXT).
- `display_consent_ref` (VARCHAR(120)): Reference to signed consent release.
- `consent_status` (VARCHAR(32)): `'consented'`, `'pending_review'`, `'revoked'`.
- `is_verified` (BOOLEAN).

### 3.6 `rbpc_experiences`
Cultural workshop and experiential tour offerings linked to creators.
- `slug` (VARCHAR(160) UNIQUE), `creator_id` (UUID FK), `provider_name`.
- `title_vi`, `title_en`, `description_vi`, `description_en`.
- `duration_minutes` (INTEGER), `pricing_display` (VARCHAR(64)), `currency` (`'VND'`).
- `availability_mode` (VARCHAR(32)): `'inquiry_only'`, `'disabled'`.
- `cancellation_policy_text` (TEXT).

### 3.7 `rbpc_stories` & `rbpc_claim_evidence`
Curated editorial journeys with claim-level evidence anchoring.
- `rbpc_stories`: `slug`, `title_vi`, `title_en`, `intro_vi`, `intro_en`, `place_id` (UUID FK), `status` (`'draft'`, `'review'`, `'approved'`, `'published'`).
- `rbpc_claim_evidence`: `story_id` (UUID FK), `statement`, `locale`, `claim_category`, `source_title`, `source_url`, `support_type`, `epistemic_certainty` (`'verified_source'`, `'traditional_account'`, `'academic_interpretation'`).

### 3.8 `rbpc_inquiries`
Privacy-hardened visitor booking inquiries.
- `public_ref` (VARCHAR(64) UNIQUE): Non-sequential alphanumeric tracking code (e.g. `INQ-2026-8812`).
- `opaque_token` (VARCHAR(128) UNIQUE): Unguessable high-entropy token for anonymous status checks.
- `experience_id` (UUID FK).
- `name`, `contact_channel` (`'email'`, `'phone'`, `'zalo'`), `contact_value`.
- `desired_date` (DATE), `party_size` (INTEGER), `message` (VARCHAR(1000)).
- `consent_version` (VARCHAR(32)): Explicit consent version recorded.
- `state` (VARCHAR(32)): `'new'`, `'contacted'`, `'confirmed'`, `'declined'`, `'closed'`.
- `idempotency_key` (VARCHAR(128) UNIQUE): Prevents duplicate submissions.

### 3.9 `rbpc_events` & `rbpc_content_audit`
- `rbpc_events`: High-level anonymous event telemetry (zero PII, rotating session IDs).
- `rbpc_content_audit`: Append-only governance ledger tracking editorial state transitions.

---

## 4. Indexing Strategy & Performance Guarantees

| Table | Index Name | Indexed Columns | Justification |
|---|---|---|---|
| `heritage_places` | `idx_heritage_places_editorial` | `(editorial_status, content_scope)` | Fast public filtering of published Huế entities |
| `heritage_places` | `idx_heritage_places_category` | `(heritage_category, editorial_status)` | Category browsing and facet filtering |
| `heritage_media_assets` | `idx_heritage_media_place` | `(place_id, content_status)` | Fetching rights-approved media for place pages |
| `heritage_media_assets` | `idx_heritage_media_uid` | `(model_uid)` WHERE model_uid IS NOT NULL | Quick lookup and deduplication of Sketchfab models |
| `rbpc_stories` | `idx_rbpc_stories_status` | `(status, published_at)` | Reverse-chronological feed of published stories |
| `rbpc_inquiries` | `idx_rbpc_inquiries_exp` | `(experience_id, state)` | Provider inbox filtering by offering and state |
| `rbpc_inquiries` | `idx_rbpc_inquiries_token` | `(opaque_token)` | Constant-time visitor status query with zero PII leakage |

---

## 5. Migration Execution & Verification

To apply the migration against a local or staging PostgreSQL database:
```bash
# Upgrade database to RBPC schema head
alembic upgrade 0054_rbpc_heritage_schema

# Verify no destructive operations
./scripts/ci/lint-migration-safety.sh
```

**Rollback Safety:**
The migration includes a reversible `downgrade()` function that cleanly drops the 11 additive tables in dependency-safe reverse order without touching any pre-existing tables.
