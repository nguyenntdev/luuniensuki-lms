# V2 original archival technical chapter — SECTION_17

> Extracted without rewriting from V2 snapshot documentation, **not verified current code**.

## 17. BACKLOG IMPLEMENTATION — PRIORITIZED EPICS / TICKETS

**Ước tính là planning points tương đối, không phải cam kết ngày công; một nhóm có thể điều chỉnh sprint capacity.**

### EPIC E00: Engineering baseline & safety (P0)

- `E00-01` Run full reproducible env from disposable DB; write pinned toolchain lock. **AC:** cold-start all backend/frontend/mobile test dependencies successfully.
- `E00-02` Git SHA provenance validation; artifact checksum manifest. **AC:** commit HEAD match documented build.
- `E00-03` Repair/migrate Alembic multi-head graph. **AC:** one approved upgrade path and rollback plan; `alembic heads` documented.
- `E00-04` Remove `alembic upgrade head || true` from CI deploy. **AC:** simulated failed upgrade stops release.
- `E00-05` Enable feature branch PR CI; Rust/Flutter/Node/pytest jobs. **AC:** all required checks run on feature PR.
- `E00-06` Remove production fake inquiry success + fake partner listings. **AC:** API outage negative E2E.
- `E00-07` Harden trusted-proxy IP and cluster rate limits. **AC:** forged XFF test passes.
- `E00-08` Verify secrets/dependencies/rights scanning. **AC:** no critical unaddressed secret alert.

### EPIC E01: Canonical 162 catalog & rights (P0)

- `E01-01` Parse 9 JSON and 162 images into staging manifest with hashed IDs; expose import errors.
- `E01-02` Reconcile catalog with authoritative 162-index; human spot checks all urn headings.
- `E01-03` Audit 158 Hán names and 4 blank fields; glyphs and scripts require scholar review.
- `E01-04` Split long AI narrative into atomic claims; classify observation/inference/speculation.
- `E01-05` Import exact source register bibliographic locations; source scanning/copyright.
- `E01-06` Claim–source binding and status; include contradicts/context evidence.
- `E01-07` Historical editorial dashboard & reviewer signatures; publish gate.
- `E01-08` Map photos/mesh hotspots with verifiable coordinates; media source lineage.
- `E01-09` Add automated source coverage dashboard (published claims only).
- `E01-10` Export machine-readable cultural dataset with provenance/rights tiers.
- `E01-11` Patch `/heritage/.../3d` asset eligibility: only explicit media permission + purpose-specific rights grants, shared predicate across listing/detail and DB query.

### EPIC E02: ELLO + teacher/student workflow (P0/P1)

- `E02-01` ELLO versioned DB and API contracts.
- `E02-02` Source packet frozen hash and UI citation drawer.
- `E02-03` CER editor observation vs inference vs source.
- `E02-04` Reviewer/teacher authoring with curriculum mapping.
- `E02-05` Rubric builder versioned and scored across multiple graders.
- `E02-06` Feedback & immutable revision timeline.
- `E02-07` Classroom assignment and enroll scoping.
- `E02-08` 2D/3D/AR parity and accessibility matrix.
- `E02-09` 45-min lesson and source-use benchmark set.
- `E02-10` PDF/CSV teacher evidence report with anonymity.

### EPIC E03: Media/XR and content discovery (P1)

- `E03-01` Hash-based asset registry with license/accuracy metadata.
- `E03-02` Deduplicate GLBs on storage; build LOD pipeline and verify mesh sizes.
- `E03-03` Photo-based 162 atlas multi-filter/search.
- `E03-04` Source first entity view with right-hand evidence rail.
- `E03-05` Progressive 3D/AR fallback; hardware and loading tests.
- `E03-06` Layered Huế taxonomy with UNESCO designation correctness.
- `E03-07` Maps, timeline and story source binding.
- `E03-08` Accessibility and multilingual content review.

### EPIC E04: Research reproducibility (P1)

- `E04-01` Protocol/ethics/authorship provenance package.
- `E04-02` Encrypted research vault and anonymized import.
- `E04-03` Original Forms question dictionary, item types/branch logic.
- `E04-04` Response cleaning, missing/duplicate report.
- `E04-05` Multi-choice audit 4.506 selection parity.
- `E04-06` All published table reproducibility checks.
- `E04-07` Permissioned study dashboard with scoped export.
- `E04-08` Versioned QA memo for HCMUS/Q2 references.
- `E04-09` Pilot rubric and scorer calibration with expert reviewers.
- `E04-10` Optional 2D vs guided 3D comparative study (new protocol; **not** part of legacy survey).

### EPIC E05: AI historical assistant trust (P1/P2)

- `E05-01` One verified knowledge retrieval service source of truth.
- `E05-02` Versioned prompts and model adapters, no provider lock-in.
- `E05-03` Safe abstention and claim-level citations in every answer.
- `E05-04` Human gold bilingual benchmark plus adversarial prompts.
- `E05-05` Signed benchmark run archive with model/corpus version.
- `E05-06` Risk-based tool calling, PI filter, input/output cost cap.
- `E05-07` Tutor critique suggest-only, teacher-final rubric review.
- `E05-08` AI transparency for users and researchers.

### EPIC E06: Living cultural bridge (P1/P2)

- `E06-01` Verify creator consent docs and per-media rights.
- `E06-02` Role-scoped partner identity and multi-tenant negative tests.
- `E06-03` Inquiry-only request + status token/notification durable outbox.
- `E06-04` Reliable idempotency/retry plus zero-fake-confirmation UX.
- `E06-05` Erasure/withdrawal/cached-content invalidation.
- `E06-06` Visitor use-case analytics separated from 1.502 student survey.
- `E06-07` Truthful conversion and in-kind sponsorship metrics.
- `E06-08` Public documentary source-to-living maker bridge with dignity rules.

### EPIC E07: Language (conditional, GLoCALL)

- `E07-01` Language learning objectives and educator signoff.
- `E07-02` VI/EN/Hán reading/transliteration/translation review.
- `E07-03` Vocabulary/reading tasks with answer evidence and difficulty.
- `E07-04` Language performance rubric and pilot; no historical survey relabeling.
- `E07-05` Showcase package with tasks and user testing.

### EPIC E08: Security, reliability and scale (cross-cutting)

- `E08-01` Private dataset and RBAC/ABAC audit.
- `E08-02` CSRF, cookie, XSS/CSP, SSRF and upload tests.
- `E08-03` Observability with trace IDs and privacy budget.
- `E08-04` Backup/restore disaster test and migration canary.
- `E08-05` Dependency/SBOM/licensing, secret rotation runbook.
- `E08-06` Multi-device a11y/power/network tests.
- `E08-07` CI required checks and release signoffs.
- `E08-08` Security incident/withdrawal response plan.

---

