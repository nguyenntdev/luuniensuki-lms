# LƯU NIÊN V6 — Modular Engineering Specification Pack

**Start here:** [`MASTER_SPEC.md`](MASTER_SPEC.md) → [`04_MOBILE/MOBILE_MASTER_SPEC.md`](04_MOBILE/MOBILE_MASTER_SPEC.md) when working on mobile → one ticket/wave/spec only.

This package restructures the 16,525-line V5 into smaller, navigable Markdown specs while preserving the full V5 verbatim in `99_ARCHIVE/V5_FULL_UNMODIFIED_SOURCE.md`. New V6 mobile specs are based on static checks of the user-supplied branch ZIP and clearly label proposed API endpoints and iOS targets.

## Relevant user objectives

- Eliminate production runtime mock data, placeholder screens and fabricated success paths across web/backend/mobile.
- Connect 9 urns / 162 reliefs to verified primary/secondary historical sources and a source-linked LMS.
- Preserve the 12-phase AI content research factory with 10 concurrent research subagents **per phase**, subject to real quota and independent expert review.
- Preserve 13 V5 development waves × 10 agent slots and provide 6 new mobile waves × 10 slots, but require true parallel execution telemetry rather than labels.
- Deliver a real Flutter Android app and develop/test iOS target when platform prerequisites exist.
- Add startup-ready school, visitor and artisan experiences supported by verifiable real-world metrics, not fake traction.

## Folder directory

| Directory | Description |
|---|---|
| `01_CORE/` | V5 product mission, audit, contracts, workflows, data, startup and ops in separate chapters |
| `03_AI_FACTORY/` | 12 research phase-specific 10-agent packets; AIR engineering tickets; deep orchestration/safety |
| `04_MOBILE/` | Platform and feature specs for Android/iOS Flutter, 60 tickets, QA and contracts |
| `05_CROSS_PLATFORM/` | Single source-of-truth ownership, production/startup gates |
| `06_RESEARCH/` | Papers, source/learning evidence, Google Forms boundaries |
| `07_DELIVERY/` | W00–W12 production-completion waves, 10 development agents each |
| `08_GEMINI_OPERATOR/` | Practical prompts and test/NOT_RUN policy |
| `09_SOURCE_APPENDICES/` | V2 audit and technical blueprint, source route inventory |
| `99_ARCHIVE/` | V5 full verbatim for completeness, **never preload** |

## Fast-start paths

- Complete web/backend production: `MASTER_SPEC.md` → `01_CORE/V5_03_MOCK_AUDIT.md` → `07_DELIVERY/W00...` and W01.
- Complete Flutter: `MASTER_SPEC.md` → `04_MOBILE/MOBILE_MASTER_SPEC.md` → `MOBILE_SOURCE_AUDIT.md` → one mobile domain spec and one Mxx-Ayy ticket.
- Implement historical AI: `MASTER_SPEC.md` → `03_AI_FACTORY/V3_C02_FACTORY_ARCHITECTURE.md` → one `PHASE_Pxx_TEN_RESEARCH_AGENTS.md` → AIR packet if engineering changes.
- Preparing startup: `05_CROSS_PLATFORM/PRODUCT_PRODUCTION_AND_STARTUP_GATES.md` → relevant W09–W12, pilot evidence.

## Critical audit notes (source snapshot)

- Mobile Android release can fallback to debug signing if release keystore is absent.
- No `mobile/ios/` folder was present in the uploaded branch ZIP; iOS is a new target.
- Quest routes still use placeholder screens; practice, notification and friend data have mock paths.
- Flutter outbox sync endpoint needs server verification.
- 162 AI-generated source records must be vetted before presenting as historically approved.

## Integrity and limitations

- The V5 source has been preserved; extracted source modules retain their original text, although they are distributed across folders and complemented by new V6 contracts.
- Audit findings are static unless associated with a runnable command and captured result. This task does not assert production deploy, app store build or end-to-end tests passed.
- See [`FILE_MANIFEST.json`](FILE_MANIFEST.json) for file inventory, source lineage and hashes; [`MODULE_INDEX.md`](MODULE_INDEX.md) for directory listing.

**Gemini handoff:** Open [`GEMINI_START_HERE.md`](GEMINI_START_HERE.md) after MASTER and select a single ticket.
