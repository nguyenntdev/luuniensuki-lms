# P07 — BLOCKED task ledger (never silently accepted)

| Task | Owner | Status | Exact blocker | Unblock path |
|---|---|---|---|---|
| P07-T19 | human lead | **BLOCKED** | Ethics/human annotation/license approval requires documented actual signatures; no human raters exist for affordance-annotation agreement. Simulated annotators are prohibited. | Recruit ≥2 independent raters with a codebook; capture signed approvals; compute Krippendorff α. |
| P07-T20 | research lead | **BLOCKED** | Novelty/nearest-work signoff requires review of most recent full texts (2026) and a closest-overlap matrix — human judgment. | Research lead reviews 2026 literature; signs overlap matrix. |
| P07-T21 | human lead | **BLOCKED** | Coauthor/venue/submission signoff is human-only (authorship, rights, formatting). | Human lead signoff at submission time. |
| P07-T02 (Europeana portion) | code agent | **BLOCKED** | Europeana API: HTTP 401 without API key. Registration: https://pro.europeana.eu/page/apis ; terms: https://pro.europeana.eu/page/terms-of-use . No metadata invented. | Register key; capture per-item media rights (metadata CC0, media item-level). |
| A3 ablation (no provenance) | code agent | **BLOCKED (dated 2026-11-15)** | Single external provider (Smithsonian FSG); a provenance ablation needs ≥2 providers. | Add 2nd provider (Europeana once unblocked). |
| A4 ablation (no hard rejection) | code agent | **BLOCKED (dated 2026-11-15)** | In selector v1.0 the hard-rejection path IS the affordance-coverage failure path; A1 subsumes its observable surface. A distinct A4 requires a scoring-style variant. | Implement score-ranking variant in a future wave. |
| B00–B03 baselines (BM25/CLIP/metadata/knapsack) | code agent | **BLOCKED (dated 2026-11-15)** | Not implemented in this wave; B01 needs pinned model weights; B03 needs an instance-space spec. Dated rationale recorded (manuscript §7). | Implement with pinned versions + parity checks per spec §4. |
| S1–S7 external slices for every stratum | code agent | **PARTIAL** | Smithsonian Open Access metadata exposes image/inscription derivational facts only; keyboard/ARIA/transcript/3D facts not present in the snapshot records used → external slices limited to the inscription axis. | Providers exposing accessibility metadata (e.g., verified IIIF+transcript collections). |
