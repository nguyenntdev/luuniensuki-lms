# HISTORY-FIRST RELEASE REPORT — Lưu Niên Sử Kí

**Date:** 2026-08-18
**Production:** https://lms.histolab.icu

## Commit SHA

`3c01391` (main) — last deployed revision. Full history at
`docs/specs/HISTORY_FIRST_EXECUTION.md`.

## Migrations

| Revision | Purpose | Prod applied |
|----------|---------|--------------|
| 0048_history_governance | entities/claims/sources/relations/geography/assets/audit | ✅ |
| 0049_content_validation_status | quiz/lesson content_validation_status | ✅ |
| 0050_history_questions | question V2 columns + question-type registry | ✅ |
| 0051_history_stories | block-based story engine | ✅ |
| 0052_history_collections | teacher/editorial collections | ✅ |

## Routes shipped (public, no login)

- `/` history-first homepage
- `/cuu-dinh` + `/cuu-dinh/[urnSlug]` — Nine Urns overview + canonical urn pages
- `/atlas` + `/atlas/[urnSlug]/[reliefSlug]` — Atlas of the 162 reliefs
- `/map` — heritage map with uncertainty UX + accessible list fallback
- `/timeline` — heritage timeline (Rust-backed, with `?entity=` deep links)
- `/stories` + `/stories/[slug]` — block-based story engine
- `/sources` + `/sources/[sourceId]` — public source library
- `/explore/connections` — contextual knowledge graph explorer
- `/compare` — compare mode
- `/urns/[urnSlug]?relief=[reliefSlug]` — 3D hotspot deep-link focus

## History API surface (22 public + admin routes)

Entities, claims, claim-sources, sources, relations, geography, search, map,
urns, events, graph, questions/grade/skills, tutor ask/entities, stories,
collections + admin mutations/audit. Regenerated OpenAPI snapshot.

## Test counts (2026-08-18)

- **Python backend:** `pytest tests/backend` → **192 passed**
- **Rust gateway:** `cargo test` → **291 passed**
- **Frontend:** type-check ✅, lint:ci ✅ (0 warnings), vitest 29 ✅, `next build` ✅
- **Content validator:** `validate_history_content.py` → pass (0 errors, 0 warnings)

## Performance

- Public history pages are static/prerendered where possible; map/3D lazy-loaded.
- Homepage does not eagerly import the 3D viewer or map (client-only, dynamic).

## AI eval (History Tutor)

- Deterministic path never fabricates: returns explicit "insufficient evidence"
  (confidence low, empty citations) when no verified claims match — verified on
  production.
- Citation validator drops fabricated/non-retrieved sources (tested).
- Legacy-unverified content is never treated as authority (tested).

## Content verification counts (production)

- 9 urn entities + 153 relief entities (canonical slugs)
- 765 claims — all `origin=ai_generated`, `verification_status=unreviewed`
- 153 `located_on` relations
- 347 quiz questions flagged `blocked_for_authoritative_learning`
- No sources fabricated; no AI content auto-verified

## Known historical review backlog

- **765 claims** require human editorial/expert review with eligible sources
  before they can be marked verified (Source-verified factual claims only).
- **347 quiz questions** blocked for authoritative learning until backing
  claims are source-verified.
- No authoritative sources/bibliographic records are yet attached — the source
  library and citation UI are live but empty pending editorial import.

## Known technical debt

- Container alembic 1.18.4 doesn't commit migrations; host venv via docker
  bridge used for prod schema changes (documented).
- Migration history branched (pre-existing 3 alembic heads); new migrations
  chain linearly onto the live head.
- Production host disk ~92% — image builds require pre-build cache pruning and
  the web image now excludes large GLB models (served via Nginx proxy).

## Rollback plan

- Public routes can be disabled by removing prefixes from
  `frontend/src/lib/publicPaths.ts` (middleware reverts to login-gated).
- Additive migrations only; downgrades defined for 0048–0052.
- Rust gateway fallback proxies history routes to Python; reverting the API
  image alone keeps the gateway and existing routes intact.
