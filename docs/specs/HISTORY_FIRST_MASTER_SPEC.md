# LƯU NIÊN SỬ KÍ — HISTORY-FIRST REBUILD MASTER SPECIFICATION

**Document type:** Product Requirements + System Requirements + Technical Design + Data Governance + Migration Plan + Test Plan + Agent Execution Contract  
**Target repository:** `nguyenntdev/luuniensuki-lms`  
**Canonical destination in repository:** `docs/specs/HISTORY_FIRST_MASTER_SPEC.md`  
**Status:** Authoritative implementation specification  
**Audience:** DeepSeek/Coding Agent, maintainers, frontend/backend/mobile engineers, content editors, historians/reviewers, QA, DevOps  
**Primary language:** Vietnamese user experience; technical implementation may use English identifiers  
**Normative keywords:** MUST, MUST NOT, SHOULD, SHOULD NOT, MAY have RFC-style meaning.  

---

## 0. Executive Directive

Lưu Niên Sử Kí must be transformed from a **generic gamified LMS with a Cửu Đỉnh theme** into a **history-first interactive historical atlas, digital museum-learning platform, and evidence-aware learning system focused on the Nine Dynastic Urns (Cửu Đỉnh)**.

The rebuild MUST preserve working infrastructure and existing product capabilities where they remain useful. It is not a greenfield rewrite. The new system must place **historical objects, claims, evidence, provenance, relationships, geography, chronology, interpretation, and learning** above generic retention mechanics in the information hierarchy.

The desired mental model is:

```text
PUBLIC HISTORICAL KNOWLEDGE PLATFORM
        │
        ├── Nine Urns
        ├── 162 Reliefs / Motifs
        ├── Historical Map
        ├── Timeline
        ├── People / Places / Events / Periods
        ├── Sources and Evidence
        ├── Stories / Guided Explorations
        └── Source-grounded History Tutor
                 │
                 ▼
LEARNING LAYER
        ├── Lessons
        ├── Historical reasoning exercises
        ├── Quiz / assessment
        ├── FSRS review
        ├── Mastery
        └── Personal progress
                 │
                 ▼
ENGAGEMENT / LMS LAYER
        ├── Streak
        ├── XP
        ├── Badges
        ├── Collection
        ├── Classroom
        ├── Teacher tools
        ├── Live learning
        └── Social / community features
```

The public product MUST feel like a historical atlas and digital heritage experience even when all gamification is ignored.

---

# PART I — PRODUCT VISION, SCOPE, AND NON-GOALS

## 1. Product Vision

### 1.1 Public positioning

Primary brand:

> **Lưu Niên Sử Kí**

Preferred descriptor:

> **Bách khoa tương tác về Cửu Đỉnh**

English descriptor:

> **Interactive Historical Atlas of the Nine Dynastic Urns**

“LMS” MAY remain in repository/internal/admin terminology but MUST NOT be the dominant public identity.

### 1.2 Core user promise

Within 30 seconds, a new visitor should understand that they can:

1. discover what the Nine Dynastic Urns are;
2. inspect each urn and each relief/motif;
3. see where a relief appears on the 3D object;
4. understand its historical/geographical context;
5. inspect sources supporting important historical claims;
6. navigate related people, places, events, periods, and objects;
7. explore represented geography on a map;
8. place historical information on a timeline;
9. learn through history-native questions;
10. optionally create an account to retain progress and receive spaced repetition.

### 1.3 Product north-star scenario

A visitor searches for a relief such as a river, mountain, species, weapon, celestial phenomenon, or historical object and enters directly on its canonical detail page.

The page should allow the visitor to:

```text
identify the object
→ understand what is confidently known
→ distinguish fact from interpretation
→ inspect supporting sources
→ see the object on the relevant urn in 3D
→ locate associated geography
→ place relevant events in time
→ discover related motifs/entities
→ answer a contextual question
→ optionally save progress
```

The journey MUST NOT require starting from a generic dashboard or course list.

---

## 2. Guiding Principles

### HP-01 — History before gamification

Historical knowledge and evidence MUST outrank XP, streak, hearts, ranks, badges, leaderboards, and retention loops in public IA and visual hierarchy.

### HP-02 — Evidence before assertion

Important historical statements MUST be representable as claims connected to sources. A text blob alone is not sufficient provenance.

### HP-03 — AI is not historical authority

AI MAY draft, summarize, translate, retrieve, tutor, or assist reviewers, but MUST NOT automatically confer verification status on historical content.

### HP-04 — Public discovery before authentication

Core historical reading and exploration MUST be accessible without login. Authentication is for persistence, personalization, classroom, contribution, and private functionality.

### HP-05 — 3D is a historical instrument

3D MUST connect physical object location to historical entity identity, sources, context, and exercises. It MUST NOT remain an isolated “wow” viewer.

### HP-06 — Connected history

Urns, reliefs, people, places, events, periods, sources, objects, concepts, and stories SHOULD be navigable as a connected knowledge network.

### HP-07 — Uncertainty is data

Uncertain, disputed, approximate, traditional, and interpretive assertions MUST be representable explicitly instead of flattened into factual prose.

### HP-08 — Preserve working infrastructure

Prefer incremental extension of current PostgreSQL, Rust backend, Next.js web, Python AI/live worker, existing auth, FSRS, timeline, trails, R3F, and Flutter code over replacement.

### HP-09 — Learning measures historical understanding

Assessment SHOULD test chronology, evidence reasoning, spatial understanding, comparison, identification, contextualization, and corroboration—not only factual recall.

### HP-10 — No fake completion

A coding agent MUST NOT mark a task complete because scaffolding exists. Completion requires the phase gate and acceptance tests defined later in this spec.

---

## 3. Scope

### 3.1 In scope

- repository truth reconciliation;
- historical data governance;
- normalized historical domain model;
- provenance/source model;
- review/editorial workflow;
- data migration from existing motif datasets;
- public history-first navigation;
- Nine Urns overview and urn detail pages;
- Atlas of the 162 reliefs;
- search and discovery;
- heritage/historical geography map;
- connected timeline;
- contextual knowledge graph;
- source library;
- evidence UI;
- story/guided exploration engine;
- history-native assessments;
- mastery model extension;
- FSRS integration;
- source-grounded AI History Tutor;
- AI evaluation suite;
- 3D historical integration;
- mobile history-first architecture;
- offline/cache strategy;
- teacher/editorial extensions;
- accessibility;
- SEO;
- i18n readiness;
- rights/licensing metadata;
- analytics and learning metrics;
- migration/cutover/rollback;
- CI/content validation/performance/security tests.

### 3.2 Explicitly preserved

The rebuild MUST preserve or safely migrate existing working functionality including, where present:

- authentication and registration;
- profiles;
- quiz/progress;
- FSRS/review;
- streak/hearts;
- badges/ranks;
- collections;
- classroom/teacher/admin;
- trails;
- timeline;
- certificates;
- live learning;
- AI worker/live teacher infrastructure;
- existing 3D capability;
- existing mobile app.

### 3.3 Temporarily frozen expansion

Until the historical core passes Phase 8, do not prioritize new:

- streak economy mechanics;
- badge families;
- gems/economy mechanics;
- leaderboard modes;
- friend competitions;
- cosmetic reward systems;
- generic social feeds;
- generic AI personas;
- retention features unrelated to historical learning.

Existing versions MAY remain operational.

---

# PART II — REPOSITORY TRUTH RECONCILIATION

## 4. Mandatory Phase 0 Audit

Repository documents inspected before this specification show stale/contradictory states. Examples include the README describing an incremental Rust migration while the full Rust migration ledger reports all inventoried native routes complete; older feature proposals may list implemented systems such as FSRS as proposals. The coding agent MUST therefore treat code/config/tests/migrations as runtime truth and documentation as claims to verify.

### REPO-001 — Create current system ledger

Create:

`docs/CURRENT_SYSTEM_STATE.md`

It MUST include:

- default branch and audited commit SHA;
- service inventory;
- frontend framework and route map;
- Rust API route inventory;
- Python service responsibilities;
- AI/live worker responsibilities;
- PostgreSQL schemas and migrations;
- auth model;
- current FSRS implementation state;
- current lesson/quiz model;
- current timeline/trail state;
- current 3D assets and supported urns;
- current mobile feature state;
- current deployment topology;
- current CI checks;
- current automated test coverage;
- current public routes;
- current admin/teacher routes;
- remaining explicit unchecked tasks in `.kiro/specs`;
- stale documents and planned corrections.

### REPO-002 — Reconcile documentation

Update as needed:

- `README.md`
- `docs/ARCHITECTURE.md`
- `docs/DOCUMENTATION_INDEX.md`
- migration ledger(s)
- feature proposal status documents
- mobile implementation state documents

Do not silently delete historical planning documents. Mark stale documents as `Historical/Archived` and point to the canonical replacement.

### REPO-003 — Finish known frontend consolidation debt

Verify and, if still incomplete:

- generate committed `frontend/src/types/api.ts`;
- verify deterministic regeneration;
- run typecheck;
- run lint;
- run existing Playwright suite;
- update task ledger only after success.

### REPO-004 — Establish baseline test artifact

Create:

`artifacts/baseline-system-verification.json`

Suggested shape:

```json
{
  "audited_commit": "...",
  "timestamp": "...",
  "rust": {"tests": "pass", "count": 0},
  "python": {"tests": "pass", "count": 0},
  "frontend": {"typecheck": "pass", "lint": "pass", "unit": "pass"},
  "playwright": {"status": "pass", "count": 0},
  "flutter": {"status": "pass", "count": 0},
  "known_failures": []
}
```

If pre-existing failures exist, record them explicitly rather than hiding them.

### Phase 0 gate

Phase 0 is complete only when:

- architecture truth is documented;
- stale docs are identified;
- baseline tests are executed or inability is documented with concrete cause;
- no new feature implementation has relied on an unverified architecture assumption.

---

# PART III — HISTORICAL DOMAIN MODEL AND EVIDENCE GOVERNANCE

## 5. Historical Content State Model

The system must model two distinct completion dimensions:

### 5.1 Engineering state

Examples:

- imported;
- normalized;
- indexed;
- renderable;
- test-covered.

### 5.2 Historical verification state

Examples:

- unreviewed;
- needs source;
- source attached;
- editor reviewed;
- expert verified;
- disputed;
- rejected.

A record MAY be engineering-complete while historical review remains incomplete.

**Critical invariant:** Engineering completion MUST NOT imply historical verification.

---

## 6. Historical Entity Model

Create a canonical historical entity table/model.

### 6.1 `historical_entities`

Recommended fields:

```sql
id UUID PRIMARY KEY,
entity_type TEXT NOT NULL,
slug TEXT NOT NULL UNIQUE,
name_vi TEXT NOT NULL,
name_en TEXT,
name_han_nom TEXT,
alternative_names JSONB NOT NULL DEFAULT '[]',
summary_vi TEXT,
summary_en TEXT,
start_date DATE,
end_date DATE,
date_precision TEXT,
latitude DOUBLE PRECISION,
longitude DOUBLE PRECISION,
geo_precision TEXT,
thumbnail_asset_id UUID,
publication_status TEXT NOT NULL DEFAULT 'draft',
content_version INTEGER NOT NULL DEFAULT 1,
created_by UUID,
updated_by UUID,
created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
deleted_at TIMESTAMPTZ
```

### 6.2 Allowed entity types

Initial controlled vocabulary:

```text
urn
relief
person
place
event
period
dynasty
reign
object
species
concept
institution
document
artwork
technique
water_body
mountain
island
settlement
region
```

Do not encode every subtype in application logic. Maintain a registry/table or enum with migration-safe evolution.

### 6.3 Entity naming requirements

Each entity SHOULD support:

- preferred Vietnamese name;
- English name where useful;
- historical spelling/name;
- Hán-Nôm representation where verified and available;
- aliases;
- normalized search tokens.

Aliases MUST NOT automatically imply historical identity unless reviewed.

### 6.4 Entity slug rules

- lowercase ASCII or normalized Vietnamese slug;
- stable once published;
- old slug redirects if changed;
- unique globally unless architecture explicitly namespaces types;
- public URLs MUST be canonical and deterministic.

### 6.5 Publication status

Allowed:

```text
draft
internal_review
public_unverified
verified
published
disputed
archived
```

`public_unverified` may be used for legacy content displayed with a visible warning only if product owner accepts it.

---

## 7. Historical Claim Model

Historical prose MUST be decomposable into claims when the assertion matters to factual interpretation.

### 7.1 `historical_claims`

Recommended fields:

```sql
id UUID PRIMARY KEY,
entity_id UUID NOT NULL REFERENCES historical_entities(id),
claim_key TEXT,
claim_type TEXT NOT NULL,
statement_vi TEXT NOT NULL,
statement_en TEXT,
valid_from DATE,
valid_to DATE,
date_precision TEXT,
confidence TEXT NOT NULL DEFAULT 'unknown',
verification_status TEXT NOT NULL DEFAULT 'unreviewed',
origin TEXT NOT NULL,
risk_level TEXT NOT NULL DEFAULT 'normal',
review_notes TEXT,
created_by UUID,
reviewed_by UUID,
reviewed_at TIMESTAMPTZ,
verified_by UUID,
verified_at TIMESTAMPTZ,
created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
supersedes_claim_id UUID REFERENCES historical_claims(id),
is_current BOOLEAN NOT NULL DEFAULT true
```

### 7.2 Claim types

At minimum:

```text
factual
chronology
geographic
identification
attribution
material
measurement
production
symbolism
interpretation
traditional_account
modern_interpretation
disputed
classification
relationship
translation
etymology
```

### 7.3 Epistemic class shown to user

The UI MUST be capable of exposing a human-readable epistemic label:

- **Được nguồn xác nhận / Documented**
- **Diễn giải / Interpretation**
- **Ghi chép/truyền thống / Traditional account**
- **Chưa chắc chắn / Uncertain**
- **Có tranh luận / Disputed**
- **Chưa kiểm chứng / Unreviewed**

### 7.4 Verification statuses

```text
unreviewed
needs_source
source_attached
editor_reviewed
expert_verified
rejected
disputed
superseded
```

### 7.5 Confidence

```text
high
medium
low
unknown
disputed
```

Confidence and verification status are separate. A claim can be source-attached yet low confidence.

### 7.6 Origin

```text
legacy_import
editorial
authoritative_import
ai_generated
community
teacher
student
system_inferred
```

System-inferred claims MUST be clearly identified and MUST NOT become expert_verified without review.

---

## 8. Source / Bibliographic Model

### 8.1 `historical_sources`

Recommended fields:

```sql
id UUID PRIMARY KEY,
source_type TEXT NOT NULL,
title TEXT NOT NULL,
subtitle TEXT,
author_text TEXT,
editor_text TEXT,
publisher TEXT,
publication_year INTEGER,
publication_date DATE,
edition TEXT,
volume TEXT,
issue TEXT,
pages TEXT,
isbn TEXT,
issn TEXT,
doi TEXT,
url TEXT,
archive_url TEXT,
repository_identifier TEXT,
language TEXT,
citation_text TEXT,
rights_status TEXT,
license TEXT,
attribution_text TEXT,
public_display_allowed BOOLEAN,
derivative_allowed BOOLEAN,
verification_status TEXT NOT NULL DEFAULT 'unreviewed',
accessed_at TIMESTAMPTZ,
created_by UUID,
created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
```

### 8.2 Source types

```text
primary_source
royal_record
archival_record
inscription
museum_catalog
heritage_authority
government_publication
scholarly_book
peer_reviewed_article
dissertation
conference_paper
critical_edition
reference_work
trusted_website
newspaper
oral_history
community_source
other
```

### 8.3 Source verification state

At minimum:

```text
unreviewed
metadata_verified
accessible
inaccessible
rights_restricted
rejected
```

### 8.4 Source identity constraints

Where present:

- DOI should be unique after normalization;
- ISBN should be normalized;
- URL canonicalization should strip tracking parameters where safe;
- duplicate source detector SHOULD warn on title+author+year similarity.

### 8.5 No fabricated bibliography rule

Agents and LLMs MUST NOT invent:

- author names;
- publication years;
- page numbers;
- DOI;
- ISBN;
- archive IDs;
- journal titles;
- quotations;
- URLs.

If source metadata cannot be verified, store only known fields and mark uncertainty.

---

## 9. Claim–Source Binding

Create:

`historical_claim_sources`

Recommended fields:

```sql
claim_id UUID NOT NULL REFERENCES historical_claims(id),
source_id UUID NOT NULL REFERENCES historical_sources(id),
support_type TEXT NOT NULL,
locator_type TEXT,
page_start TEXT,
page_end TEXT,
chapter TEXT,
section TEXT,
figure TEXT,
folio TEXT,
inscription_location TEXT,
quotation_excerpt TEXT,
quotation_language TEXT,
editor_note TEXT,
created_by UUID,
created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
PRIMARY KEY (claim_id, source_id, support_type)
```

### 9.1 Support types

```text
supports
partially_supports
contextualizes
contradicts
mentions
primary_evidence_for
secondary_interpretation_of
```

### 9.2 Verification invariant

A factual/chronology/geographic/identification claim MUST NOT reach `expert_verified` unless at least one eligible source binding exists.

High-risk claims SHOULD require either:

- two independent acceptable sources; or
- one primary/authoritative source plus reviewer approval.

### 9.3 Citation locators

Store the narrowest locator available. Page ranges are preferred when meaningful, but the system MUST support non-paginated sources.

---

## 10. Historical Entity Relations

Create:

`historical_entity_relations`

Recommended fields:

```sql
id UUID PRIMARY KEY,
subject_entity_id UUID NOT NULL REFERENCES historical_entities(id),
predicate TEXT NOT NULL,
object_entity_id UUID NOT NULL REFERENCES historical_entities(id),
claim_id UUID REFERENCES historical_claims(id),
source_id UUID REFERENCES historical_sources(id),
confidence TEXT NOT NULL DEFAULT 'unknown',
verification_status TEXT NOT NULL DEFAULT 'unreviewed',
valid_from DATE,
valid_to DATE,
created_by UUID,
created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
UNIQUE(subject_entity_id, predicate, object_entity_id)
```

### 10.1 Initial predicates

```text
located_on
depicts
associated_with
commissioned_by
cast_during
cast_at
created_during
predecessor_of
successor_of
represents
located_in
flows_through
part_of
member_of
mentioned_in
contemporaneous_with
commemorates
identified_as
related_to
source_for
influenced_by
near
maps_to_modern_place
```

### 10.2 Relation rules

- Subject and object MUST exist.
- Self-relations are invalid except explicitly whitelisted predicates.
- Directionality MUST be documented by predicate registry.
- Inverse predicates SHOULD be computable rather than redundantly stored unless needed for performance.
- Verified relation claims require evidence just like textual claims.

---

## 11. Historical Geography Model

Modern map coordinates are not sufficient for historical geography.

### 11.1 `historical_geographies`

Suggested fields:

```sql
entity_id UUID PRIMARY KEY REFERENCES historical_entities(id),
historical_name TEXT,
modern_name TEXT,
historical_geometry JSONB,
modern_geometry JSONB,
valid_from DATE,
valid_to DATE,
geo_precision TEXT NOT NULL,
mapping_status TEXT NOT NULL,
source_claim_id UUID,
notes TEXT
```

### 11.2 Geo precision

```text
exact
approximate
settlement
region
water_body
historical_boundary
modern_correspondence
unknown
```

### 11.3 Mapping status

```text
verified
probable
disputed
unknown
```

### 11.4 UX requirement

A historical place mapped only approximately MUST NOT be displayed as an exact pin without uncertainty indication.

---

## 12. Media / Asset Model

Create or extend a generic asset model rather than storing loose URLs everywhere.

Suggested `historical_assets` fields:

```text
id
asset_type
storage_url
thumbnail_url
mime_type
width
height
duration
byte_size
sha256
rights_status
license
attribution
source_origin
public_display_allowed
derivative_allowed
entity_id
created_at
```

Asset types:

```text
photo
relief_crop
3d_model
3d_texture
map
scan
illustration
audio
video
document_thumbnail
```

No public page may display a rights-restricted asset unless policy explicitly permits it.

---

## 13. Editorial Governance and Review Workflow

### 13.1 Admin routes

Create or extend:

```text
/admin/history
/admin/history/entities
/admin/history/claims
/admin/history/sources
/admin/history/relations
/admin/history/assets
/admin/history/review
/admin/history/conflicts
/admin/history/imports
/admin/history/audit
```

### 13.2 Roles

Minimum RBAC roles:

```text
history_viewer
history_contributor
history_editor
history_reviewer
history_expert
history_admin
```

Suggested permissions:

- viewer: inspect internal content;
- contributor: draft entity/claim/source;
- editor: edit, attach sources, request review;
- reviewer: approve/reject editorial quality;
- expert: confer expert verification;
- admin: schema/import/workflow administration.

### 13.3 State machine

Recommended claim workflow:

```text
UNREVIEWED
   ├── no source → NEEDS_SOURCE
   └── source attached → SOURCE_ATTACHED
                         ↓
                   EDITOR_REVIEWED
                         ↓
                  EXPERT_VERIFIED
```

Alternate exits:

```text
REJECTED
DISPUTED
SUPERSEDED
```

### 13.4 Human review requirements

DeepSeek MAY automate:

- legacy extraction;
- deduplication suggestions;
- metadata normalization;
- source matching suggestions;
- claim segmentation;
- translation drafts;
- review queue prioritization.

DeepSeek MUST NOT automate final expert verification without a policy explicitly authorizing a trusted external source import.

### 13.5 Review UI

Reviewer screen SHOULD show side-by-side:

```text
Claim
Entity context
Source metadata
Source locator / excerpt if available
Existing related claims
Conflicting claims
AI/legacy origin
Revision history
Approve / request source / dispute / reject
```

---

## 14. Historical Audit Log

Create append-only `historical_content_audit_log`.

Fields:

```text
id
actor_id
action
resource_type
resource_id
before_json
after_json
reason
request_id
created_at
```

Actions include:

```text
create
update
attach_source
detach_source
submit_review
editor_approve
expert_verify
reject
dispute
publish
unpublish
supersede
import
merge
```

The audit log MUST NOT be editable through normal UI.

---

# PART IV — LEGACY DATA MIGRATION

## 15. Legacy Data Policy

Existing enriched motif JSON contains useful content but historically authoritative status MUST NOT be inferred from presence in the repository.

Legacy fields such as:

- `description_short`;
- `description_educational`;
- `historical_context`;
- `symbolism`;
- `fun_fact`;
- `quiz_questions`;
- `is_ai_generated`;

must be migrated in a way that preserves provenance.

### MIG-001 — Non-destructive migration

Do not delete legacy files during first migration.

### MIG-002 — Stable mapping

Maintain a mapping table/file:

```text
legacy_motif_id → historical_entity_id
```

### MIG-003 — AI-generated state

If `is_ai_generated=true`:

```text
origin = ai_generated
verification_status = unreviewed or needs_source
```

Never `expert_verified` by migration.

### MIG-004 — Claim segmentation

Migration MAY split text into candidate claims, but generated segmentation MUST be marked `legacy_import` or `ai_generated` and remain reviewable.

### MIG-005 — Quiz safety

Questions depending on unverified claims MUST be marked:

```text
content_validation_status = blocked_for_authoritative_learning
```

They may remain visible to admins but SHOULD NOT enter authoritative learner review until source-backed.

---

## 16. Migration Pipeline

Implement scripts under:

`scripts/history/`

Recommended commands:

```text
inventory_legacy_content
normalize_entities
segment_claims
migrate_sources
build_relations
migrate_questions
validate_history_content
generate_migration_report
```

### 16.1 Required properties

- idempotent where practical;
- dry-run mode;
- deterministic IDs or mapping for re-runs;
- transaction-safe batch writes;
- explicit error file;
- no silent row loss;
- resumable after failure.

### 16.2 Migration report

Generate:

`artifacts/history-migration-report.json`

Required metrics:

```json
{
  "legacy_files_scanned": 0,
  "legacy_records_scanned": 0,
  "urn_entities_created": 0,
  "relief_entities_created": 0,
  "other_entities_created": 0,
  "claims_created": 0,
  "ai_generated_claims": 0,
  "claims_needing_source": 0,
  "sources_created": 0,
  "relations_created": 0,
  "questions_migrated": 0,
  "questions_blocked_for_verification": 0,
  "duplicates": [],
  "invalid_records": [],
  "unmapped_records": []
}
```

### 16.3 Gate

Migration passes only when every legacy motif is either:

- mapped;
- intentionally excluded with reason; or
- listed as an unresolved error.

No silent omission.

---

# PART V — PUBLIC INFORMATION ARCHITECTURE

## 17. Navigation Architecture

Preferred primary navigation:

```text
Khám phá
Cửu Đỉnh
162 Hình đúc
Bản đồ
Dòng thời gian
Câu chuyện
Nguồn tư liệu
Luyện tập
```

Account-level features MAY live in profile/dashboard menus:

```text
Tiến độ
Ôn tập
Bộ sưu tập
Thành tích
Lớp học
Bạn bè
Cài đặt
```

### IA-001

A user MUST be able to reach any canonical urn or relief page in <= 3 meaningful navigation actions from homepage.

### IA-002

Public history URLs MUST not redirect unauthenticated users to login.

### IA-003

Authenticated personalization MAY decorate public history pages but MUST not replace their historical content.

---

## 18. Homepage V2

Route: `/`

### 18.1 Guest structure

1. Hero: what Cửu Đỉnh is and why it matters.
2. Interactive overview of the Nine Urns.
3. Entry to Atlas 162.
4. Geographic exploration teaser.
5. Timeline teaser.
6. Featured historical stories.
7. “Object/relief of the day”.
8. Sources/research credibility section.
9. Learning CTA.
10. Account CTA as secondary action.

### 18.2 Required copy behavior

Avoid public copy about:

- retention KPI;
- DAU;
- engagement loops;
- “keep users coming back”;
- internal growth mechanics.

### 18.3 Hero CTA hierarchy

Primary:

> Khám phá 162 hình đúc

Secondary:

> Xem Cửu Đỉnh 3D

Tertiary:

> Bắt đầu học / Đăng nhập

### 18.4 Homepage acceptance

Without signing in, the visitor can navigate to:

- all urns;
- atlas;
- map;
- timeline;
- at least one story;
- sources.

---

## 19. Cửu Đỉnh Overview

Route: `/cuu-dinh`

Must become a substantive historical entry rather than a marketing page.

Required sections:

- definition and location;
- commissioning/casting context;
- historical period;
- overview of all nine urns;
- relationship between urns and relief corpus;
- materials/production technique if verified;
- geographic/natural/cultural categories represented;
- historical interpretations with epistemic labels;
- timeline;
- selected sources;
- 3D exploration entry.

Major factual sections SHOULD expose citation affordances.

---

## 20. Urn Detail Pages

Canonical route:

`/cuu-dinh/[urnSlug]`

Required modules:

```text
Title / identity
Hero photo or rights-safe visual
3D viewer
Basic verified facts
Historical context
Casting / physical information
Associated reign/person if supported
18 relief grid or correct corpus count from data
Category distribution
Geographic distribution
Timeline connections
Sources
Related stories
Learning progress for signed-in user
Practice CTA
```

### 20.1 3D integration

Clicking a relief card from the urn page SHOULD focus that location in 3D.

### 20.2 Canonical entity identity

The urn page MUST use the same historical entity ID as graph, timeline, source, and tutor systems.

---

# PART VI — ATLAS OF THE 162 RELIEFS

## 21. Atlas Route

Create:

`/atlas`

The Atlas is a P1 signature feature.

### 21.1 User goals

Users can:

- browse all reliefs;
- search by name/alias;
- filter by urn;
- filter by semantic category;
- filter by geographic association;
- filter by verification state if appropriate;
- sort;
- share filter state in URL;
- open canonical relief pages.

### 21.2 Filters

At minimum:

```text
urn
flora
fauna
river/water
mountain
sea/island
place/region
architecture
weapon/military
transport/vessel
astronomy/weather
mythical/symbolic
object/technique
verification status
```

Do not hardcode an assumption that old legacy categories are complete. Build a category registry and map legacy values.

### 21.3 Search behavior

Search SHOULD support:

- Vietnamese with diacritics;
- Vietnamese without diacritics;
- aliases;
- English names;
- historical names;
- fuzzy typo tolerance;
- prefix suggestions.

PostgreSQL `unaccent`, full-text search, and `pg_trgm` are preferred before adding separate search infrastructure.

### 21.4 Card design

Each card SHOULD include:

- image/thumbnail;
- Vietnamese preferred name;
- urn;
- category;
- one-line description;
- evidence status where meaningful;
- 3D availability icon if relevant.

Mastery/collection status MAY appear for signed-in users but not dominate the card.

---

## 22. Relief Detail Page

Canonical route:

`/atlas/[urnSlug]/[reliefSlug]`

### 22.1 Required information architecture

```text
A. Identity header
B. Relief visual
C. “What you are seeing”
D. Documented historical facts
E. Historical context
F. Interpretation / symbolism, explicitly labeled
G. Location on urn + 3D focus
H. Geographic relationship/map
I. Timeline relationship
J. Evidence / sources
K. Related entities and motifs
L. Compare action
M. Practice question
N. Ask History Tutor
```

### 22.2 Evidence display

Important claims SHOULD expose source chips/footnotes that open a side panel or source detail page.

### 22.3 Unverified state

If a page contains unreviewed migrated content, display a non-alarmist but clear note such as:

> Một số diễn giải trên trang này đang trong quá trình kiểm chứng nguồn.

Do not falsely label it verified.

### 22.4 Shareability

Canonical URL must be stable and social metadata should identify the specific relief and urn.

---

## 23. Compare Mode

Create a compare experience reachable from atlas/entity pages.

Suggested route:

`/compare?entities=id1,id2`

Support 2–4 entities initially.

Comparison dimensions:

- urn;
- category;
- iconography;
- historical context;
- geography;
- time association;
- sources;
- interpretations;
- 3D location.

Compare is especially useful for historical reasoning exercises.

---

# PART VII — MAP AND HISTORICAL GEOGRAPHY

## 24. Heritage Map

Route:

`/map`

### 24.1 Purpose

The map is not a generic tourist map. It should help answer:

> What geography was represented on the Cửu Đỉnh, and how do those representations connect to the historical worldview encoded in the monument?

### 24.2 Core map features

- pan/zoom;
- clustered markers;
- entity side panel;
- filter by urn;
- filter by entity/category;
- filter by historical/modern mapping status;
- URL share state;
- search;
- link to relief detail;
- link to urn/3D;
- link to sources;
- optional compare selections.

### 24.3 Data contract

Map endpoint should return only data needed for the viewport/filter state where practical.

Example response:

```json
{
  "items": [
    {
      "entity_id": "uuid",
      "name": "...",
      "lat": 0,
      "lng": 0,
      "geo_precision": "approximate",
      "mapping_status": "probable",
      "related_reliefs": ["uuid"],
      "urns": ["uuid"]
    }
  ],
  "meta": {"count": 1}
}
```

### 24.4 Historical boundary caution

No modern boundary overlay should imply exact historical administrative boundaries without sources.

### 24.5 Accessibility

Provide a list/table alternative containing the same entities and uncertainty information.

---

# PART VIII — TIMELINE AND KNOWLEDGE GRAPH

## 25. Timeline V2

Reuse current timeline where viable.

### 25.1 Event model

Historical event entities SHOULD connect to:

- date/range;
- period/reign;
- people;
- places;
- urns;
- reliefs;
- sources;
- stories.

### 25.2 Timeline filters

- reign;
- person;
- urn;
- topic;
- place;
- source-backed only.

### 25.3 Deep links

Entity pages SHOULD be able to open timeline with relevant filter state.

Example:

`/timeline?entity=cao-dinh`

---

## 26. Contextual Knowledge Graph

Route:

`/explore/connections`

### 26.1 Scope

Do not build an all-node graph first. Start with a contextual graph:

```text
selected entity
→ 1-hop verified/usable neighbors
→ explicit expand to 2-hop
```

### 26.2 Node types

Initial:

```text
urn
relief
person
place
event
period
source
```

### 26.3 Edge UX

Hover/tap edge should show predicate in natural language.

### 26.4 Graph database non-requirement

PostgreSQL adjacency relations are sufficient initially. Do not introduce Neo4j or another graph database without measurable need.

---

# PART IX — SOURCE LIBRARY AND EVIDENCE UX

## 27. Public Source Library

Routes:

```text
/sources
/sources/[sourceId-or-slug]
```

### 27.1 Source index

Filter by:

- source type;
- author;
- year;
- language;
- related urn;
- related topic;
- rights/access state.

### 27.2 Source detail

Show:

- bibliographic metadata;
- source type;
- rights/access;
- external/archive link if known;
- claims supported/contextualized/contradicted;
- related entities;
- preferred citation;
- export formats.

### 27.3 Citation export

Support at least:

- plain text;
- APA;
- Chicago;
- BibTeX where metadata is sufficient.

Never fabricate missing fields just to produce a formatted citation.

---

## 28. Evidence Panel Component

Build shared frontend components:

```text
EvidenceBadge
ClaimWithSources
CitationChip
SourceDrawer
EpistemicLabel
ConflictNotice
ReviewStatusBadge
```

These components MUST be reusable in:

- relief pages;
- urn pages;
- stories;
- tutor responses;
- teacher materials;
- admin review.

---

# PART X — HISTORY-FIRST SEARCH

## 29. Global Historical Search

Global command palette and search should prioritize historical entities.

### 29.1 Search targets

```text
urns
reliefs
people
places
events
periods
stories
sources
```

### 29.2 Ranking

Suggested ranking factors:

```text
exact preferred-name match
alias exact match
prefix match
trigram similarity
historical relevance/popularity
verified/published state
language match
```

Learning/admin navigation may appear after historical results.

### 29.3 Search endpoint

Suggested:

`GET /api/v1/history/search?q=&types=&limit=`

Response groups by entity type.

### 29.4 Performance

P95 search API target under normal load: < 300 ms where infrastructure permits.

---

# PART XI — STORIES AND GUIDED HISTORICAL EXPLORATION

## 30. Story Engine

Routes:

```text
/stories
/stories/[slug]
```

### 30.1 Story data model

A story should consist of ordered blocks, not one giant HTML field.

Suggested block types:

```text
text
image
quote
relief_focus
urn_3d_focus
map_focus
timeline_focus
source_excerpt
compare
reflection_question
quiz
callout
```

### 30.2 Story step schema

Example:

```json
{
  "type": "map_focus",
  "entity_ids": ["..."],
  "title": "...",
  "body": "...",
  "source_claim_ids": ["..."]
}
```

### 30.3 Reuse trails

Existing trail infrastructure SHOULD be reused where semantically compatible. Do not create a parallel system if trail sequencing can support story blocks cleanly.

### 30.4 Initial story themes

Suggested editorial themes, subject to source review:

- Cửu Đỉnh as a bronze representation of the realm;
- rivers and waters;
- mountains and geography;
- animals and plants;
- maritime imagery;
- casting and material production;
- court representation and memory;
- the monument’s later heritage status.

These are story concepts, not pre-verified historical claims.

---

# PART XII — HISTORY-NATIVE LEARNING ENGINE

## 31. Learning Philosophy

Existing quiz and FSRS systems should be retained, but question design must expand beyond generic MCQ/true-false.

Historical learning should target:

- recognition;
- factual recall;
- chronology;
- spatial/geographic reasoning;
- sourcing;
- contextualization;
- corroboration;
- comparison;
- evidence interpretation.

---

## 32. Question Model V2

Add/extend question types:

```text
multiple_choice
true_false
chronology_order
image_identification
map_location
urn_hotspot
evidence_match
entity_match
compare_two
source_interpretation
short_response
multi_select
relationship_chain
```

### 32.1 Common fields

```text
id
question_type
prompt
entity_ids
claim_ids
source_ids
difficulty
skill_dimensions
answer_contract
explanation
content_validation_status
publication_status
created_by
reviewed_by
```

### 32.2 Content validity invariant

A published factual question MUST depend only on claims permitted for learning.

If claim verification is revoked, affected questions MUST be automatically discoverable and optionally deactivated.

---

## 33. Question Type Contracts

### 33.1 Chronology order

Input:

```json
{"entity_ids": ["eventA", "eventB", "eventC"]}
```

Answer:

```json
{"ordered_entity_ids": ["eventB", "eventA", "eventC"]}
```

Server grades exact/partial ordering according to explicit rubric.

### 33.2 Image identification

Image must be rights-cleared. Distractors should come from semantically plausible entities, not random options.

### 33.3 Map location

Answer may use:

- exact marker selection;
- region selection;
- distance tolerance;
- categorical geography.

Tolerance MUST account for `geo_precision`.

### 33.4 Urn hotspot

User selects hotspot/mesh/region on 3D urn. Server receives canonical hotspot/entity ID, not arbitrary client score.

### 33.5 Evidence match

Given a claim, select which source best supports/contextualizes/contradicts it.

### 33.6 Source interpretation

A source excerpt must have clear rights/quotation handling. Questions should distinguish what can and cannot be inferred from the excerpt.

### 33.7 Short response

LLM grading MAY assist but SHOULD NOT be the sole authoritative grader for high-stakes classroom results without rubric safeguards.

---

## 34. Mastery Model V2

Add skill dimensions:

```text
recognition
factual_recall
chronology
geography
source_literacy
evidence_reasoning
comparison
contextualization
```

Suggested mastery state:

```json
{
  "entity_id": "...",
  "recognition": 0.91,
  "factual_recall": 0.83,
  "chronology": 0.61,
  "geography": 0.74,
  "source_literacy": 0.45,
  "evidence_reasoning": 0.42
}
```

Do not replace current progress metrics immediately. Introduce compatibility/mapping.

---

## 35. FSRS Integration

Do not rebuild FSRS if current implementation is functioning.

### 35.1 Eligible review units

Good FSRS units:

- identity recall;
- image recognition;
- place association;
- chronology facts;
- source/entity relationship recall;
- concise comparisons.

Avoid scheduling long essays as atomic FSRS cards.

### 35.2 Traceability

Each review card SHOULD reference:

- entity IDs;
- claim IDs;
- source IDs where relevant;
- question version.

If a claim is invalidated, dependent review items can be retired.

---

# PART XIII — SOURCE-GROUNDED AI HISTORY TUTOR

## 36. Tutor Mission

Transform generic AI assistance into a **source-grounded historical tutor** that answers from curated system knowledge and explicitly represents uncertainty.

The tutor must optimize for:

1. factual correctness;
2. traceable evidence;
3. epistemic transparency;
4. helpful explanation;
5. connection to app entities;
6. learning progression.

It must NOT optimize only for fluent completion.

---

## 37. Retrieval Pipeline

Required logical pipeline:

```text
User question
  ↓
Authentication/context (optional)
  ↓
Entity resolver
  ↓
Intent classifier
  ↓
Query planner
  ↓
Historical entity/claim retrieval
  ↓
Source retrieval
  ↓
Verification filter
  ↓
Conflict/uncertainty assembly
  ↓
Prompt/context construction
  ↓
LLM generation
  ↓
Citation validator
  ↓
Unsupported-claim checker
  ↓
Structured tutor response
```

### 37.1 Retrieval precedence

Default priority:

1. expert-verified claims;
2. editor-reviewed/source-backed claims;
3. authoritative heritage/primary sources;
4. reviewed scholarly secondary sources;
5. approved editorial stories;
6. unreviewed content only when explicitly requested and clearly labeled.

Unreviewed AI-generated legacy prose MUST NOT silently become tutor authority.

---

## 38. Tutor Response Contract

API should return structured response, for example:

```json
{
  "answer_markdown": "...",
  "confidence": "medium",
  "epistemic_summary": "Some interpretation remains disputed.",
  "citations": [
    {
      "source_id": "uuid",
      "claim_ids": ["uuid"],
      "locator": "..."
    }
  ],
  "related_entities": [
    {"id": "uuid", "type": "relief", "label": "..."}
  ],
  "uncertainties": [],
  "suggested_actions": [
    {"type": "open_entity", "entity_id": "uuid"}
  ]
}
```

### 38.1 Suggested actions

Supported action types MAY include:

```text
open_entity
view_urn_3d
open_map
open_timeline
open_source
compare_entities
start_practice
save_for_review
```

---

## 39. Tutor Citation Validation

Every citation returned to the learner MUST pass:

```text
source exists
source was retrieved for this answer
claim-source binding exists or citation is explicitly general/contextual
locator is not fabricated
user has permission to see the source metadata
```

Invalid citations MUST be removed or answer regenerated.

### 39.1 Unsupported assertion check

Post-generation evaluation should detect material claims not grounded in retrieved context.

If unsupported:

- remove/qualify claim;
- regenerate with stricter prompt;
- or explicitly state insufficient evidence.

---

## 40. Tutor Epistemic Behavior

Tutor MUST distinguish:

- documented fact;
- interpretation;
- traditional account;
- uncertain attribution;
- disputed conclusion;
- absence of evidence.

Example acceptable behavior:

> “Các nguồn đã được kiểm chứng trong hệ thống hiện chưa đủ để kết luận chắc chắn về điểm này.”

This is preferable to plausible invention.

### 40.1 Prompt injection resistance

Historical source text is data, not instructions. Retrieved documents MUST be delimited and treated as untrusted content.

---

## 41. Tutor Evaluation Suite

Create persistent evaluation cases.

Categories:

```text
simple verified fact
multi-source synthesis
chronology
geographic relationship
entity disambiguation
interpretive question
disputed claim
unanswerable question
source comparison
citation requirement
prompt injection
citation hallucination
legacy-unverified trap
```

Metrics:

```text
answer correctness
claim support rate
unsupported assertion rate
citation precision
citation recall
citation validity
entity-link accuracy
uncertainty calibration
appropriate refusal/qualification
latency
cost/tokens if relevant
```

### 41.1 Release gate

Do not call History Tutor production-ready unless:

- citation validity is effectively 100% under validator-enforced output;
- known injection cases fail closed;
- unsupported assertion rate is measured and below project-defined threshold;
- regression suite passes.

Store results:

`artifacts/history-tutor-eval.json`

---

# PART XIV — 3D HISTORY EXPERIENCE

## 42. 3D Product Role

The 3D viewer must provide spatial-historical linkage.

### 42.1 Required capabilities

- canonical urn model loading;
- relief hotspot registry;
- entity-linked hotspots;
- deep-link focus;
- camera focus animation;
- highlight selected region/mesh;
- open history side panel;
- open source/evidence panel;
- navigate to relief page;
- quiz hotspot mode;
- accessible text fallback.

### 42.2 Deep link contract

Example:

`/cuu-dinh/cao-dinh?relief=dong-hai`

Expected behavior:

1. page loads Cao Đỉnh;
2. 3D viewer loads appropriate LOD;
3. relief resolver maps slug to entity/hotspot;
4. camera focuses it;
5. visual highlight appears;
6. linked historical summary is available.

### 42.3 Hotspot registry

Each hotspot needs:

```text
hotspot_id
urn_entity_id
relief_entity_id
mesh_id or normalized surface location
camera_target
camera_position
bounding region
coordinate_version
model_version
```

Hotspot data MUST be versioned against the model to prevent coordinate drift.

---

## 43. 3D Asset Pipeline

Preferred pipeline:

```text
source model
→ geometry cleanup
→ texture optimization
→ Meshopt/Draco as appropriate
→ KTX2/Basis textures
→ LOD generation
→ integrity hash
→ manifest
→ object storage/CDN
```

### 43.1 Manifest

Example:

```json
{
  "urn_slug": "cao-dinh",
  "model_version": 3,
  "hotspot_version": 3,
  "lods": {
    "low": {"url": "...", "sha256": "...", "bytes": 0},
    "medium": {"url": "...", "sha256": "...", "bytes": 0},
    "high": {"url": "...", "sha256": "...", "bytes": 0}
  }
}
```

### 43.2 Adaptive quality

Select initial LOD from:

- device memory if available;
- viewport;
- network hints;
- platform;
- user quality preference.

Load low/medium first rather than blocking page on a huge high-detail asset.

### 43.3 Performance telemetry

Track:

- model download bytes;
- time to first visible model;
- time to interactive rotation;
- hotspot focus latency;
- model load failure rate.

---

# PART XV — MOBILE HISTORY-FIRST REBUILD

## 44. Mobile Goals

The mobile app should expose the same historical domain model, not a separate content truth.

Preferred primary tabs:

```text
Khám phá
Bản đồ
Học
Bộ sưu tập
Tôi
```

### 44.1 Mobile home

Prioritize:

- continue historical story/lesson;
- relief/object of the day;
- explore urns;
- explore map;
- saved offline items;
- next review.

XP/streak may be visible but secondary.

---

## 45. Mobile 3D Package Manager

Do not bundle all high-resolution models in the base app.

Implement:

```text
remote model manifest
→ select package
→ download
→ checksum verification
→ local storage
→ version check
→ LRU eviction
→ offline availability
```

### 45.1 Model state

```text
not_downloaded
downloading
available
update_available
corrupt
failed
```

### 45.2 Storage controls

User can:

- see downloaded models;
- see total space;
- remove individual model;
- clear cache;
- choose Wi-Fi-only download.

---

## 46. Offline Mode

Cacheable content:

- entity metadata;
- selected stories;
- selected source metadata/excerpts if licensing permits;
- lessons;
- thumbnails;
- review queue;
- quiz draft;
- downloaded 3D model.

### 46.1 Offline writes

Use an operation queue with:

```text
operation_id
entity/resource
payload
created_at
retry_count
idempotency_key
```

Sync must be idempotent.

### 46.2 Conflict handling

Learner progress should merge according to existing authoritative server semantics. Editorial/admin content SHOULD NOT be editable offline initially.

---

# PART XVI — TEACHER, EDITORIAL, AND COMMUNITY EXTENSIONS

## 47. Teacher Historical Collections

Teachers should create structured collections from canonical entities/sources rather than copy-pasting content.

A collection can contain:

```text
entities
sources
stories
map states
timeline events
questions
3D hotspots
```

Example use case:

> “Địa lý Việt Nam qua các hình đúc trên Cửu Đỉnh”

Teacher assembles:

- selected reliefs;
- selected map locations;
- source packet;
- chronology events;
- question set.

---

## 48. Citizen Curation — Deferred Until Governance Exists

Community contributions MAY be added only after source/review workflow is operational.

All community claims begin:

```text
origin = community
verification_status = unreviewed
```

Reputation MUST NOT automatically confer expert verification.

Contribution workflow:

```text
submit
→ automated validation
→ moderation
→ source review
→ editorial/expert review
→ publish or reject
```

---

# PART XVII — API TECHNICAL DESIGN

## 49. API Namespace

New historical APIs SHOULD be grouped under:

`/api/v1/history/*`

Admin APIs:

`/api/v1/admin/history/*`

Maintain repository’s existing API conventions for auth, pagination, errors, and response envelopes.

---

## 50. Public Read Endpoints

Suggested minimum:

```text
GET /api/v1/history/entities
GET /api/v1/history/entities/{id}
GET /api/v1/history/entities/by-slug/{slug}
GET /api/v1/history/entities/{id}/claims
GET /api/v1/history/entities/{id}/relations

GET /api/v1/history/urns
GET /api/v1/history/urns/{slug}
GET /api/v1/history/urns/{slug}/reliefs

GET /api/v1/history/reliefs
GET /api/v1/history/reliefs/{urnSlug}/{reliefSlug}

GET /api/v1/history/sources
GET /api/v1/history/sources/{id}
GET /api/v1/history/sources/{id}/claims

GET /api/v1/history/map
GET /api/v1/history/timeline
GET /api/v1/history/search
GET /api/v1/history/stories
GET /api/v1/history/stories/{slug}
```

### 50.1 Pagination

Use consistent cursor or offset pagination based on existing project convention. Cursor is preferred for large continuously-changing collections, but avoid unnecessary complexity for the fixed relief atlas.

### 50.2 Filtering

Public APIs SHOULD accept explicit typed filters and reject unknown invalid enum values with 400.

---

## 51. Admin Mutation Endpoints

Suggested:

```text
POST   /api/v1/admin/history/entities
PATCH  /api/v1/admin/history/entities/{id}
POST   /api/v1/admin/history/claims
PATCH  /api/v1/admin/history/claims/{id}
POST   /api/v1/admin/history/sources
PATCH  /api/v1/admin/history/sources/{id}
POST   /api/v1/admin/history/relations
DELETE /api/v1/admin/history/relations/{id}
POST   /api/v1/admin/history/claims/{id}/submit-review
POST   /api/v1/admin/history/claims/{id}/editor-approve
POST   /api/v1/admin/history/claims/{id}/expert-verify
POST   /api/v1/admin/history/claims/{id}/reject
POST   /api/v1/admin/history/claims/{id}/dispute
POST   /api/v1/admin/history/imports/legacy
```

Every state-changing admin endpoint MUST audit actor/action.

---

## 52. API Error Contract

Use existing project error contract if available. If inconsistent, standardize new endpoints to something like:

```json
{
  "error": {
    "code": "HISTORY_CLAIM_MISSING_SOURCE",
    "message": "Verified factual claims require an eligible source.",
    "details": {},
    "request_id": "..."
  }
}
```

Never expose SQL errors/internal stack traces.

---

## 53. API Caching

Public mostly-static endpoints SHOULD use:

- `ETag`;
- `Cache-Control`;
- conditional GET;
- CDN cache where deployment permits.

Invalidate cache when publication state or content version changes.

Do not cache private personalization into public cache keys.

---

# PART XVIII — DATABASE AND INDEX DESIGN

## 54. PostgreSQL Strategy

Prefer PostgreSQL already in the stack.

Recommended extensions if available:

```sql
CREATE EXTENSION IF NOT EXISTS unaccent;
CREATE EXTENSION IF NOT EXISTS pg_trgm;
```

PostGIS is optional and should be added only if deployment complexity is acceptable and map requirements justify it.

### 54.1 Indexes

Suggested:

```text
historical_entities(entity_type)
historical_entities(publication_status)
unique lower(slug) or canonical slug index
GIN search vector on names/aliases
trigram indexes for Vietnamese/alias search
historical_claims(entity_id, verification_status)
historical_claim_sources(claim_id)
historical_claim_sources(source_id)
historical_entity_relations(subject_entity_id)
historical_entity_relations(object_entity_id)
historical_sources(publication_year)
historical_sources(source_type)
```

### 54.2 Soft delete

Published historical entities SHOULD use archival/soft-delete semantics to preserve links and audit history.

### 54.3 Versioning

At minimum, content_version increments on public content changes. High-value entities MAY later support full revision tables.

---

# PART XIX — FRONTEND TECHNICAL DESIGN

## 55. Frontend Route Tree

Illustrative Next.js structure:

```text
frontend/src/app/
  page.tsx
  cuu-dinh/
    page.tsx
    [urnSlug]/page.tsx
  atlas/
    page.tsx
    [urnSlug]/
      [reliefSlug]/page.tsx
  map/page.tsx
  timeline/page.tsx
  stories/
    page.tsx
    [slug]/page.tsx
  sources/
    page.tsx
    [sourceId]/page.tsx
  compare/page.tsx
  explore/
    connections/page.tsx
  practice/
  admin/history/
```

### 55.1 Component domains

Create reusable areas:

```text
components/history/
components/evidence/
components/atlas/
components/history-map/
components/history-3d/
components/stories/
components/history-tutor/
```

### 55.2 Data fetching

Public historical pages SHOULD use server rendering/static revalidation where it improves SEO and performance. Client components should be reserved for interactive map/3D/filter/tutor behavior.

### 55.3 URL state

Search/filter/map/timeline state SHOULD be encoded in query parameters where shareability matters.

---

## 56. Design System

Desired visual language:

```text
museum editorial
bronze
archival paper
ink
stone
subtle imperial accent
high-quality object photography
spacious typography
```

Avoid making core history pages look like:

```text
neon game dashboard
rainbow achievement UI
heavy glassmorphism
mobile game store
```

### 56.1 Semantic tokens

Examples:

```css
--heritage-bronze
--heritage-bronze-muted
--heritage-paper
--heritage-paper-elevated
--heritage-ink
--heritage-ink-muted
--heritage-stone
--evidence-verified
--evidence-review
--evidence-disputed
--evidence-unverified
```

Do not encode verification solely by color.

---

# PART XX — ACCESSIBILITY

## 57. Accessibility Target

Target WCAG 2.2 AA where practical.

Mandatory requirements:

- semantic headings;
- keyboard navigation;
- visible focus;
- accessible names;
- sufficient contrast;
- reduced-motion support;
- screen-reader status messages;
- non-color-only verification labels;
- alt text for images;
- captions/transcripts for media where applicable;
- map list fallback;
- 3D textual fallback;
- accessible quiz interactions.

### 57.1 3D fallback invariant

No essential historical fact may be available only by manipulating a 3D scene.

### 57.2 Map fallback invariant

All mapped historical entities must be available in an equivalent list/table representation.

---

# PART XXI — INTERNATIONALIZATION

## 58. Language Architecture

Vietnamese is primary.

System SHOULD support:

```text
vi
en
```

Historical data should store translations as distinct fields/content versions rather than machine translating on every request.

### 58.1 Translation status

Optional:

```text
missing
machine_draft
human_reviewed
verified
```

Machine-translated historical interpretation MUST not overwrite verified Vietnamese source wording.

---

# PART XXII — SEO AND PUBLIC DISCOVERY

## 59. SEO Requirements

Indexable canonical pages:

- homepage;
- Cửu Đỉnh overview;
- each urn;
- atlas;
- each relief;
- stories;
- sources where public;
- selected entity pages;
- timeline landing;
- map landing.

### 59.1 Metadata

Each canonical historical page SHOULD define:

- title;
- description;
- canonical URL;
- OpenGraph;
- social image where rights permit;
- structured data where semantically valid;
- language alternates when available.

### 59.2 Sitemap

Generate from published historical entities, not a manually maintained fixed route list.

### 59.3 Private routes

Do not index:

- dashboard;
- account;
- classroom private content;
- admin;
- drafts;
- review queue.

---

# PART XXIII — RIGHTS AND LICENSING

## 60. Rights Policy

Every externally sourced media/document SHOULD record:

```text
rights_status
license
attribution
source_origin
public_display_allowed
derivative_allowed
```

### 60.1 Default behavior

Unknown rights ⇒ do not republish full asset by default.

A metadata record and external link may still be shown if lawful.

### 60.2 Source excerpts

Store only excerpts necessary for teaching/evidence and follow project/legal policy. Do not ingest entire protected books by default.

---

# PART XXIV — SECURITY AND PRIVACY

## 61. Security Requirements

Preserve existing hardened auth and server-authoritative grading behavior.

New admin/history mutations MUST have:

- authentication;
- RBAC;
- server validation;
- CSRF model consistent with app architecture;
- rate limiting where appropriate;
- audit logging;
- secure error responses.

### 61.1 Upload security

If editors upload source scans/media:

- file size cap;
- MIME allowlist;
- magic-byte validation;
- filename sanitization;
- isolated/object storage;
- no executable serving;
- optional malware scanning if infrastructure supports it.

### 61.2 AI privacy

Tutor context MUST NOT leak private classroom/user data into public answers. Personalized context must be explicitly scoped.

---

# PART XXV — OBSERVABILITY AND ANALYTICS

## 62. Product Events

Track meaningful history/learning actions:

```text
history_entity_view
relief_view
urn_view
source_open
citation_expand
map_open
map_entity_open
timeline_event_open
relation_follow
3d_model_loaded
3d_relief_focus
story_start
story_complete
practice_start
question_attempt
evidence_question_attempt
tutor_question
tutor_citation_open
compare_open
registration_after_history_explore
```

Avoid logging sensitive free-text tutor queries without privacy policy/retention consideration.

---

## 63. Core Metrics

### 63.1 Product discovery

- homepage → historical entity rate;
- atlas search success;
- entity → related entity traversal;
- source open rate;
- map engagement;
- timeline engagement;
- story completion;
- registration after public exploration.

### 63.2 Learning

- pre/post or first/late accuracy where appropriate;
- D7/D30 recall;
- chronology accuracy;
- geography accuracy;
- source/evidence reasoning accuracy;
- FSRS retention;
- mastery dimension changes.

### 63.3 Historical integrity

- published claims without eligible source (target 0 for verified factual claims);
- claims awaiting source;
- AI-generated claims awaiting review;
- source-link break rate;
- disputed claims shown without label (target 0).

### 63.4 AI quality

- unsupported assertion rate;
- citation validity;
- citation precision;
- answer qualification appropriateness;
- tutor latency.

---

# PART XXVI — TEST STRATEGY

## 64. Unit Tests

Must cover:

- entity validation;
- slug behavior;
- claim state transitions;
- source eligibility;
- verification invariant;
- relation validation;
- chronology grading;
- map tolerance;
- hotspot answer grading;
- citation validator;
- search normalization;
- migration parsing;
- rights visibility rules.

---

## 65. Property / Invariant Tests

Examples:

```text
expert_verified factual claim ⇒ >= 1 eligible source
published entity ⇒ canonical non-empty slug
relation ⇒ subject and object exist
AI citation ⇒ cited source exists and was in retrieval context
hotspot question ⇒ target relief belongs to target urn/model version
chronology answer ⇒ contains exactly expected entity set
public rights-restricted asset ⇒ never returns raw protected URL unless permitted
```

Use Rust property testing where already idiomatic in the repo.

---

## 66. Integration Tests

Required flows:

### FLOW-01 Historical publishing

```text
create source
→ create entity
→ create claim
→ bind source
→ editor review
→ expert verify
→ publish
→ public API retrieval
```

### FLOW-02 Legacy migration

```text
legacy motif
→ canonical relief
→ migrated claims
→ unreviewed AI provenance
→ admin review queue
```

### FLOW-03 Connected history

```text
relief
→ place relation
→ map endpoint
→ event relation
→ timeline endpoint
→ source panel
```

### FLOW-04 Learning

```text
published question
→ submit
→ server grade
→ mastery update
→ FSRS review creation/update
```

### FLOW-05 Tutor

```text
question
→ entity resolution
→ verified retrieval
→ generation
→ citation validation
→ response
```

---

## 67. E2E / Playwright

Minimum scenarios:

1. Guest opens homepage and reaches Atlas.
2. Search for a relief.
3. Open relief page.
4. Expand citation.
5. Open source detail.
6. Open map from relief.
7. Open timeline relation.
8. Deep-link into 3D relief focus.
9. Start a history-native exercise.
10. Register/sign in and preserve progress.
11. Ask tutor and open citation.
12. Admin creates/edits claim.
13. Reviewer verifies source-backed claim.
14. Unverified claim cannot be incorrectly marked verified without required evidence.
15. Mobile viewport public exploration.

---

## 68. Content Integrity CI

Create a validator runnable in CI.

Fail CI on:

- duplicate canonical slug;
- orphan relation;
- broken source FK;
- verified factual claim with no eligible source;
- public question depending on blocked/unverified factual claim where policy forbids it;
- malformed coordinates;
- invalid model/hotspot mapping;
- missing referenced image/model manifest;
- invalid publication state transition;
- duplicate legacy mapping.

Warn on:

- translation missing;
- unreviewed draft;
- source URL temporarily inaccessible;
- low-confidence claim;
- approximate geography;
- asset without derivative rights when only thumbnail is used.

Generate:

`artifacts/history-content-validation.json`

---

# PART XXVII — PERFORMANCE

## 69. Web Performance Budgets

Targets on reasonable mobile hardware/network:

- LCP: <= 2.5s target for public non-3D pages;
- CLS: <= 0.1;
- INP: <= 200ms target;
- avoid JS-heavy map/3D on initial homepage critical path;
- lazy-load heavyweight interactive modules.

### 69.1 Atlas

- first result render should not depend on fetching full descriptions for all 162 items;
- thumbnails optimized/responsive;
- filters should feel instant after data is available;
- URL state should not trigger unnecessary full-page reload.

### 69.2 3D

- low/medium LOD first;
- explicit loading UI;
- abort unused downloads on navigation where feasible;
- CDN/object cache headers;
- no mandatory giant base bundle.

---

# PART XXVIII — DEPLOYMENT, MIGRATION, AND ROLLBACK

## 70. Deployment Strategy

Use additive schema and dual-read/dual-route migration before destructive cleanup.

### 70.1 Suggested sequence

1. deploy new tables/migrations;
2. deploy history APIs hidden/feature-flagged;
3. run legacy import dry-run;
4. run import;
5. validate counts/invariants;
6. deploy admin review UI;
7. deploy public pages behind feature flag;
8. smoke test;
9. enable public routes;
10. observe metrics/errors;
11. retire legacy reads only after parity confidence.

### 70.2 Feature flags

Suggested flags:

```text
history_v2_public
history_atlas
history_map
history_graph
history_tutor_grounded
history_question_types_v2
history_mobile_v2
```

### 70.3 Rollback

Database migrations SHOULD be reversible where safe. If data migration is additive, rollback may disable new reads without deleting imported records.

Never make rollback depend on reconstructing deleted legacy data.

---

# PART XXIX — PHASED EXECUTION PLAN

## 71. Phase 0 — Truth Reconciliation

### Deliverables

- `docs/CURRENT_SYSTEM_STATE.md`
- docs reconciliation;
- baseline test artifact;
- outstanding task audit;
- dependency inventory.

### Gate

No unresolved architecture assumption that blocks Phase 1.

---

## 72. Phase 1 — Historical Governance Foundation

### Deliverables

- entities;
- claims;
- sources;
- claim-source bindings;
- relations;
- geography model;
- asset rights model;
- audit log;
- migrations;
- RBAC;
- Rust domain/service/API;
- admin basic CRUD;
- tests.

### Gate

Can execute full create-source → create-claim → verify → public-read integration flow.

---

## 73. Phase 2 — Legacy Corpus Migration

### Deliverables

- importer;
- deterministic mapping;
- nine urn entities;
- 162 relief identities or exact audited corpus size;
- migrated claims;
- migrated questions;
- provenance preservation;
- migration report;
- unresolved review queue.

### Gate

No legacy motif silently omitted.

---

## 74. Phase 3 — History-First Public Shell

### Deliverables

- redesigned navbar;
- homepage V2;
- `/cuu-dinh` historical landing;
- urn canonical routes;
- updated footer/about/source credibility;
- public no-login access.

### Gate

New visitor can understand product purpose without seeing dashboard/gamification.

---

## 75. Phase 4 — Atlas 162

### Deliverables

- `/atlas`;
- filters/search;
- canonical relief pages;
- evidence panel;
- source links;
- related entities;
- SEO metadata;
- tests.

### Gate

Every migrated relief has a canonical reachable page even if some content is honestly labeled unreviewed.

---

## 76. Phase 5 — Historical Map

### Deliverables

- geography records;
- `/map`;
- filters;
- entity details;
- relief/urn/source links;
- uncertainty UX;
- accessible list fallback.

### Gate

Approximate/disputed mappings never masquerade as exact verified pins.

---

## 77. Phase 6 — Timeline + Knowledge Connections

### Deliverables

- timeline relation integration;
- event/person/place/urn/relief/source links;
- contextual graph explorer;
- reverse navigation.

### Gate

At least the supported core corpus demonstrates bidirectional historical exploration.

---

## 78. Phase 7 — 3D Historical Integration

### Deliverables

- versioned hotspot registry;
- entity deep links;
- focus/highlight;
- history/source panel;
- optimized manifest pipeline;
- performance telemetry;
- hotspot exercise foundation.

### Gate

A relief page can reliably focus the correct relief on the correct urn/model version.

---

## 79. Phase 8 — Historical Learning Engine V2

### Deliverables

- chronology;
- image identification;
- map location;
- hotspot;
- evidence match;
- comparison;
- source interpretation;
- mastery dimensions;
- FSRS integration;
- server-authoritative grading;
- question provenance.

### Gate

At least one end-to-end verified item exists for each implemented question type.

---

## 80. Phase 9 — Source-Grounded History Tutor

### Deliverables

- entity resolver;
- verified retrieval;
- source retrieval;
- structured context;
- tutor contract;
- citation validator;
- unsupported assertion handling;
- adversarial eval;
- release metrics.

### Gate

AI eval passes declared thresholds and fabricated citations cannot escape validator.

---

## 81. Phase 10 — Stories

### Deliverables

- block-based story schema;
- story editor or admin workflow;
- rich map/timeline/3D/source blocks;
- public story routes;
- story completion telemetry.

---

## 82. Phase 11 — Teacher / Editorial Expansion

### Deliverables

- historical collections;
- source packets;
- lesson paths;
- teacher assignment integration;
- richer editorial batch review;
- conflict dashboard.

---

## 83. Phase 12 — Mobile V2

### Deliverables

- history-first navigation;
- atlas;
- map;
- source/evidence views;
- learning integration;
- model package manager;
- offline queue;
- deep links.

### Gate

All nine urn identities are supported even if high-quality models/assets are downloaded on demand.

---

## 84. Phase 13 — Accessibility / SEO / i18n / Performance Hardening

### Deliverables

- accessibility audit;
- keyboard/screen-reader fixes;
- SEO sitemap generation;
- language architecture;
- performance budgets;
- image/model optimization;
- public metadata consistency.

---

## 85. Phase 14 — Stabilization and Release

Run and fix:

```text
cargo fmt/check/test
Rust integration tests
Python tests
frontend typecheck
frontend lint
frontend unit/component tests
Playwright
Flutter analyze/test
migration dry run
migration validation
content validator
security regression tests
AI history tutor eval
production build
smoke tests
```

Produce final:

`artifacts/history-first-release-report.md`

with:

- commit SHA;
- migrations;
- routes shipped;
- test counts;
- performance results;
- AI eval results;
- content verification counts;
- known historical review backlog;
- known technical debt;
- rollback plan.

---

# PART XXX — DEPENDENCY GRAPH

## 86. High-Level Dependencies

```text
Phase 0
  ↓
Phase 1 Governance
  ↓
Phase 2 Migration
  ↓
Phase 3 Public shell
  ↓
Phase 4 Atlas
  ├──→ Phase 5 Map
  ├──→ Phase 6 Timeline/Graph
  └──→ Phase 7 3D
             ↓
        Phase 8 Learning
             ↓
        Phase 9 Tutor

Phase 4 + 5 + 6 + 7
  ↓
Phase 10 Stories

Phase 1 + 8 + 10
  ↓
Phase 11 Teacher/Editorial

Phase 4 + 5 + 7 + 8
  ↓
Phase 12 Mobile

All
  ↓
Phase 13 Hardening
  ↓
Phase 14 Release
```

Parallel work is allowed only when dependencies are genuinely satisfied.

---

# PART XXXI — AGENT EXECUTION CONTRACT

## 87. DeepSeek Operating Rules

The coding agent MUST operate this specification as an implementation contract.

For each phase:

```text
inspect current code
→ identify reusable components/services
→ update execution ledger
→ implement smallest coherent slice
→ write/adjust migrations
→ write tests
→ run tests
→ inspect failures
→ fix
→ update docs
→ mark completed tasks with evidence
→ continue
```

### 87.1 No documentation-only completion

Writing a plan does not satisfy an implementation task.

### 87.2 No fake placeholders

Do not create endpoints returning mock/static placeholder success unless explicitly part of a staged prototype and clearly marked incomplete.

### 87.3 No guessed repository structure

Before editing a path, inspect actual repository structure.

### 87.4 Resolve conflicts by evidence

When docs conflict:

1. inspect registered routes/config;
2. inspect migrations/models;
3. inspect tests;
4. inspect deployment compose/config;
5. record conclusion in `CURRENT_SYSTEM_STATE.md`.

### 87.5 Preserve compatibility

Do not remove working APIs/routes until consumers are migrated and contract tests pass.

### 87.6 No unnecessary infrastructure

Do not add:

- Elasticsearch;
- Neo4j;
- Kafka;
- a new vector database;
- another frontend framework;
- another auth service;

unless a measured requirement cannot be met with the current stack.

### 87.7 Historical truth boundary

If implementation requires a factual historical decision that cannot be supported by repository sources or verified references, the agent MUST:

- implement the structure;
- mark record unresolved;
- create review item;
- continue engineering work.

Do not block the entire build and do not invent the answer.

---

## 88. Execution Ledger

Create:

`docs/specs/HISTORY_FIRST_EXECUTION.md`

Maintain sections:

```text
Audited commit
Current phase
Current branch
Completed task IDs
In-progress task IDs
Tests run and results
Migrations added
API contracts changed
Frontend routes changed
Mobile changes
Historical content imported
Historical content awaiting review
Architectural decisions
Known blockers
Known regressions
Next executable tasks
```

Every completion claim should point to files/tests/commit when practical.

---

## 89. Decision Log

Create or append:

`docs/specs/HISTORY_FIRST_DECISIONS.md`

Each decision:

```text
ID
Date
Context
Options considered
Decision
Reason
Consequences
Revisit trigger
```

Use for material deviations from this specification.

---

# PART XXXII — DEFINITION OF DONE

## 90. System-Level Definition of Done

The rebuild is complete only if all of the following are true.

### DOD-01 Public historical identity

A guest understands this is a Cửu Đỉnh historical exploration product, not merely a course dashboard.

### DOD-02 Nine urn corpus

All nine canonical urn identities exist and are publicly navigable.

### DOD-03 Relief corpus

All audited relief/motif records have canonical IDs and pages, with explicit status where historical verification is incomplete.

### DOD-04 Provenance

Verified factual claims have eligible evidence bindings.

### DOD-05 Source UX

Users can inspect sources from historical pages.

### DOD-06 Atlas

Search/filter/share works.

### DOD-07 Map

Historical geography is explorable and uncertainty is visible.

### DOD-08 Timeline

Events connect to entities and sources.

### DOD-09 Connected graph

Core relations support bidirectional exploration.

### DOD-10 3D

Relief deep link → correct urn → correct hotspot works.

### DOD-11 Learning

History-native question types work server-authoritatively and connect to mastery/FSRS.

### DOD-12 Tutor

History Tutor is source-grounded, citation-validated, uncertainty-aware, and evaluated.

### DOD-13 Mobile

Core historical exploration is available on mobile with on-demand model handling.

### DOD-14 Accessibility

Essential historical knowledge is available without requiring vision-only map/3D interaction.

### DOD-15 CI

All mandatory test gates are green or explicitly waived by maintainers with documented reason.

### DOD-16 No hidden historical fabrication

No migration/tool/LLM automatically converted unreviewed AI-generated history into expert-verified truth.

---

## 91. Golden User Journey Acceptance Test

The following journey must work:

```text
Search engine / direct link
→ canonical relief page
→ identify relief
→ read documented context
→ inspect source citation
→ open source detail
→ view geographic relation
→ view timeline relation
→ open correct urn in 3D focused on relief
→ open related entity
→ answer a history-native question
→ optionally sign in
→ save progress / receive later review
```

This journey is more important than adding another generic engagement mechanic.

---

# PART XXXIII — PRIORITY MATRIX

## 92. P0 — Integrity and foundation

- repository truth audit;
- domain model;
- source/provenance model;
- editorial states;
- migration;
- tests;
- no fabricated verification.

## 93. P1 — Historical public value

- homepage;
- Cửu Đỉnh overview;
- urn pages;
- Atlas 162;
- source UI;
- historical search;
- map;
- timeline connections.

## 94. P2 — Differentiated learning experience

- 3D entity integration;
- history-native assessment;
- mastery V2;
- FSRS bindings;
- source-grounded tutor.

## 95. P3 — Expansion

- stories;
- teacher collections;
- citizen curation;
- advanced mobile/offline;
- richer graph exploration.

Do not let P3 delay P0/P1 quality.

---

# PART XXXIV — RECOMMENDED REPOSITORY STRUCTURE

## 96. Illustrative Final Structure

Adapt to actual repo rather than force this exact structure.

```text
backend-rust/
  src/
    history/
      mod.rs
      models/
      repositories/
      services/
      routes/
      search/
      map/
      review/
      validation/

backend/
  services/
    history_ai/
      entity_resolver.py
      retrieval.py
      context_builder.py
      citations.py
      grounded_tutor.py
      evaluator.py

frontend/src/
  app/
    atlas/
    cuu-dinh/
    map/
    timeline/
    stories/
    sources/
    compare/
    explore/connections/
    admin/history/
  components/
    history/
    evidence/
    atlas/
    history-map/
    history-3d/
    history-tutor/
    stories/

mobile/lib/features/
  history_home/
  atlas/
  urns/
  historical_map/
  history_sources/
  history_learning/
  model_packages/

scripts/history/
  inventory_legacy_content.*
  migrate_legacy_content.*
  validate_history_content.*
  generate_migration_report.*

migrations/
  ...history...

docs/
  CURRENT_SYSTEM_STATE.md
  history/
    CONTENT_GOVERNANCE.md
    SOURCE_POLICY.md
    EDITORIAL_GUIDE.md
    DATA_MODEL.md
  specs/
    HISTORY_FIRST_MASTER_SPEC.md
    HISTORY_FIRST_EXECUTION.md
    HISTORY_FIRST_DECISIONS.md

artifacts/
  baseline-system-verification.json
  history-migration-report.json
  history-content-validation.json
  history-tutor-eval.json
  history-first-release-report.md
```

---

# PART XXXV — REQUIRED TECHNICAL DOCUMENTS TO GENERATE DURING IMPLEMENTATION

## 97. Documentation Deliverables

DeepSeek must create/update these as the implementation evolves:

### `docs/history/CONTENT_GOVERNANCE.md`

- epistemic classes;
- verification policy;
- role responsibilities;
- AI-origin policy;
- dispute policy.

### `docs/history/SOURCE_POLICY.md`

- acceptable source classes;
- citation metadata;
- locator rules;
- duplicate handling;
- rights policy.

### `docs/history/EDITORIAL_GUIDE.md`

- editor workflow;
- how to split claims;
- how to label interpretation;
- review checklist;
- publication criteria.

### `docs/history/DATA_MODEL.md`

- ER diagram;
- tables;
- constraints;
- relation predicate registry;
- state transitions.

### `docs/history/AI_TUTOR_GROUNDING.md`

- retrieval hierarchy;
- prompt boundaries;
- citation validator;
- eval thresholds;
- incident handling.

### `docs/history/3D_ASSET_PIPELINE.md`

- source model handling;
- compression;
- LOD;
- hotspot versioning;
- manifest contract;
- mobile packaging.

---

# PART XXXVI — RELEASE READINESS CHECKLIST

## 98. Historical integrity

- [ ] every published verified factual claim has evidence;
- [ ] no AI-generated legacy claim silently verified;
- [ ] disputed claims display dispute state;
- [ ] source links pass validation or are marked unavailable;
- [ ] rights metadata exists for public assets;
- [ ] quiz dependencies are valid.

## 99. Engineering

- [ ] migrations tested on clean DB;
- [ ] migrations tested on representative existing DB;
- [ ] Rust tests pass;
- [ ] Python tests pass;
- [ ] frontend typecheck passes;
- [ ] lint passes;
- [ ] Playwright passes;
- [ ] Flutter checks pass;
- [ ] content validation passes;
- [ ] API types regenerated deterministically;
- [ ] deployment smoke tests pass.

## 100. UX

- [ ] guest can browse without login;
- [ ] homepage history-first hierarchy verified;
- [ ] all nine urns accessible;
- [ ] atlas works mobile/desktop;
- [ ] citations are understandable;
- [ ] map uncertainty understandable;
- [ ] 3D has fallback;
- [ ] practice is reachable from entity pages;
- [ ] gamification does not dominate public IA.

## 101. AI

- [ ] tutor retrieves verified content by default;
- [ ] citations validated;
- [ ] injection tests pass;
- [ ] unanswerable test cases handled appropriately;
- [ ] unsupported-assertion metric recorded;
- [ ] eval artifact committed/generated according to repo policy.

## 102. Operations

- [ ] feature flags documented;
- [ ] rollback procedure documented;
- [ ] error monitoring checked;
- [ ] cache invalidation tested;
- [ ] database backup verified before production migration;
- [ ] no credentials committed.

---

# PART XXXVII — DEEPSEEK `/goal`

Use the following compact goal after committing this master specification to the repository.

```text
/goal

Implement the complete History-First Rebuild of nguyenntdev/luuniensuki-lms using docs/specs/HISTORY_FIRST_MASTER_SPEC.md as the authoritative product, requirements, technical-design, migration, testing, and release contract. Do real implementation, not planning-only output.

Start by auditing actual code/config/tests and reconcile stale documentation into docs/CURRENT_SYSTEM_STATE.md. Preserve working auth, PostgreSQL, Rust APIs, Python AI/live workers, Next.js, Flutter, FSRS, quiz/progress, classroom, trails, timeline, 3D, admin and existing gamification unless the spec explicitly changes their role. Prefer extension over rewrite.

Execute phases in dependency order: repository truth → historical governance/data model → legacy 9-urn/relief migration → history-first public UX → Atlas 162 → source/evidence UI → historical map → connected timeline/knowledge graph → entity-aware 3D → history-native assessment/mastery/FSRS → source-grounded History Tutor → stories/teacher tools → mobile/offline → accessibility/SEO/performance → stabilization/release.

Critical historical-integrity rule: never invent facts, citations, authors, DOI, pages, archive IDs or references. Never automatically mark legacy/AI-generated material verified. If evidence is unavailable, keep the record unreviewed/needs_source and add it to the human review backlog while continuing engineering work. Verified factual claims must satisfy the source-binding invariants in the master spec.

Maintain docs/specs/HISTORY_FIRST_EXECUTION.md continuously with audited commit, current phase, completed/in-progress task IDs, tests, migrations, decisions, blockers, historical review backlog and next executable tasks. Use docs/specs/HISTORY_FIRST_DECISIONS.md for material deviations.

For every phase: inspect → implement → migrate → test → fix → document → verify acceptance gate → continue. Do not mark tasks complete for scaffolding, placeholders or unrun tests. Keep changes reviewable, migrations safe, APIs typed and regenerated, and existing critical flows compatible.

Do not introduce major infrastructure such as Elasticsearch, graph DB, new auth stack or frontend rewrite unless measurements prove the current stack cannot satisfy a requirement. Do not force login for public historical exploration. Do not expose rights-unknown media by default. Do not let generic gamification expansion displace historical core work.

Continue autonomously through ordinary implementation decisions. Stop only for genuinely unavailable credentials/assets/licenses, destructive production-only operations, or historical verification that cannot responsibly be inferred. In those cases, record the blocker precisely and continue all independent work.

Completion requires the golden journey to work: relief → historical context → evidence/source → map/timeline → correct urn/3D hotspot → related entities → history-native exercise → optional account/progress; plus green mandatory test/content/AI release gates from the master spec.
```

---

# FINAL DIRECTIVE

The most important architectural change in this program is not a framework migration or a new feature. It is a change in the **unit of truth** and the **unit of navigation**:

```text
OLD
course / lesson / gamification state / AI-generated content blob

NEW
historical entity
  ↕
claim
  ↕
evidence/source
  ↕
relations in place/time/object context
  ↕
learning interactions
```

If a design choice makes the product better at retaining users but worse at distinguishing historical evidence from fluent content, reject that choice.

If a design choice makes the product more visually impressive but disconnects 3D/map/timeline from canonical historical entities, reject that choice.

If a design choice requires rewriting stable infrastructure without measurable benefit to historical integrity, discovery, learning, performance, or maintainability, reject that choice.

The intended end state is a platform where a learner, teacher, visitor, or researcher can move naturally among **the physical object, the depicted motif, the place, the period, the historical claim, the source, and the learning task** without losing provenance.

That connected, evidence-aware experience is the product.
