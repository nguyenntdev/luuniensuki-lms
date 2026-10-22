# CROSS-PLATFORM AUTHORITY MATRIX — Next.js / Flutter / Rust Gateway / FastAPI / PostgreSQL

> Contract IDs are target and must be reconciled with the actual API. No duplicate domain truth in Flutter/localStorage.

| Domain | Authoritative owner | Web interface | Flutter interface | Persistent state | Required invariant |
|---|---|---|---|---|---|
| Identity & roles | FastAPI identity (+ gateway auth) | session/admin | auth/consent | PostgreSQL | server checks tenant on every access |
| 9 urns / 162 reliefs | heritage/evidence backend | research browser | Explore/History | source DB/object store | only published approved revision shown |
| Citations | evidence service | source locator admin | citation panel | immutable snapshot DB | quote exact locator/source edition |
| 3D/AR rights | media service | web viewer | model viewer + fallback | object store/license DB | revoke invalidates cached assets |
| ELLO | learning backend | teacher authoring | student runner | assignment/version/attempt DB | rubric/score server authority |
| Quizzes/FSRS | learning backend | classroom/reports | practice/quests | item and progress DB | mock questions in tests only |
| Wallet/rewards | gamification backend | staff/admin | hearts/XP/gems | immutable event ledger | no client balance writes |
| Notification | inbox service | web inbox/admin | push & inbox | inbox DB + token registry | logout/revoke purges token ownership |
| AI Tutor | retrieval/citation validator | web tutor | history AI tutor | approved passages/answers | unsupported claim => abstain |
| AI Research Factory | worker orchestrator | review/admin console | read released content only | jobs, artifacts, approvals | AI cannot sign expert review |
| Partner experience | RBPC backend | partner portal | heritage passport/inquiries | tenant-scoped inquiry DB | no fabricated booking/status |
| Survey research | research controlled workspace | reporting | not identifying survey | separate restricted dataset | self-report != learning gains |
| Product/startup analytics | analytics server | growth dashboard | consent-bound events | append-only event registry | real events only, no survey merge |

## API change protocol

1. Issue an ADR and owner for route, resource, version, error states, role matrix, acceptance tests.
2. Record current authoritative route in `backend/routers`, Rust gateway mapping, frontend route usage, Flutter constants; run contract inventory.
3. Expand schema/route backward compatibly; migrate on disposable DB; add negative tenant/idempotency tests.
4. Publish pinned OpenAPI, regenerate Next.js + Flutter clients; server contract tests and clients typecheck.
5. Roll out backend first with feature flag off, deploy clients to staging, test offline/version compatibility and auth.
6. Enable flag for pilot cohort; log feature impact, implement graceful rollback, no fabricated fallback.

## Minimum compatibility policy

- Support at least two simultaneously deployed mobile client contract versions during app store rollout unless owner documents narrower policy; record sunset times.
- Old clients encountering retired content revision receive 410/upgrade state, not unsourced fallback.
- Shared `request_id`, `Idempotency-Key`, source revision and error taxonomy must be identical across web/mobile.
- Never use stale frontend seed data to fill failed backend responses, including Partner Portal and Imperial Studio.
