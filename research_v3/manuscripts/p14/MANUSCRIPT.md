# P14 — Thiết kế và đánh giá học liệu di sản đa phương thức theo Universal Design for Learning
**Manuscript skeleton (P14-T17). Status: DRAFT_SKELETON — audit-only run, human-evaluation arm BLOCKED (P14-T19). Venue target per spec: Tạp chí Khoa học Trường ĐH Sư phạm TP.HCM; CFP/rank verification outstanding (P14-T21 BLOCKED).**

Release status: `ENGINEERING_PASS` + `PARTIAL` (external media BLOCKED → synthetic manifest; no human data → no benefit claims permitted).

---

## 1. Title & claims frame
- Working title (VI): Thiết kế và đánh giá học liệu di sản đa phương thức theo Universal Design for Learning: một hệ thống kiểm toán tiếp cận và rà soát UDL.
- Working title (EN): Designing and auditing multimodal heritage learning objects under Universal Design for Learning: an accessibility audit system.
- **Claims gate:** every numeric/causal claim in this manuscript must bind to an Evidence ID in `research_artifacts_v3/runs/p14/` and pass `research_v3/methods/p14/claims_guard.py`. No learning-benefit wording is permitted in this run (no human study).

## 2. Abstract (skeleton)
- [ ] Problem: heritage learning objects are often single-modality and inaccessible; UDL offers a design framework but adoption lacks an auditable protocol.
- [x] Method: versioned UDL + WCAG 2.2 AA rubric; deterministic per-object audit engine; remediation list; C0/C1 baselines. [EV: P14-AUDIT-001]
- [ ] Results: audit-only descriptive results on a labelled synthetic manifest (external media BLOCKED). [EV: P14-AUDIT-001]
- [x] Explicit limitation: **no human user study was conducted; no claim is made that the UDL workflow improves task completion or learning.** H0 remains not rejected / untested.

## 3. Research question
Mức độ tương đương nhiệm vụ và khả năng tiếp cận của học liệu đa phương thức thay đổi như thế nào khi áp dụng rubric UDL có đánh giá người dùng? (Human-evaluation arm pending; this run covers the audit arm only.)

## 4. Related work (to be completed with verified citations)
- [ ] Universal Design for Learning (CAST UDL Guidelines) — principles of representation, engagement, action/expression; cite the original framework, note no causal-learning evidence is imported from it.
- [ ] WCAG 2.2 (W3C) — AA success criteria used: 1.1.1, 1.2.2, 1.4.3, 1.4.11, 2.1.1, 2.1.2, 2.4.7.
- [ ] Multimedia learning (Mayer) — modality/redundancy principles; cited as design motivation only, not as measured effect.
- [ ] Digital accessibility audit methodologies in cultural heritage (nearest-work scan pending; P14-T20 BLOCKED).
- [ ] Boundary statement vs object-selection work (P07 family): selection/ranking vs object design audit; no shared primary outcome (see `overlap_decision.json`).

## 5. Method (summary; full: `research_v3/methods/p14/METHOD.md`)
- [x] Fixed rubric `p14-udl-rubric-1.0.0`: 3 UDL principles + WCAG 2.2 AA affordances; no learned parameters. [EV: P14-AUDIT-001]
- [x] Typed object schema with NOT_APPLICABLE / ABSTAIN distinct from FAIL. [EV: P14-AUDIT-001]
- [x] Deterministic audit engine; per-object verdict + remediation list. [EV: P14-AUDIT-001]
- [x] Baselines C0 "has an image", C1 WCAG-checklist-only (not tuned). [EV: P14-AUDIT-001]

## 6. Data & rights
- [x] Smithsonian Open Access: BLOCKED (API key required; HTTP 403 verified 2026-11-15). [EV: P14-RIGHTS-001]
- [x] Europeana: BLOCKED (API key required; HTTP 401 verified 2026-11-15). [EV: P14-RIGHTS-001]
- [x] Huế imagery: excluded (unlicensed). [EV: P14-RIGHTS-001]
- [x] Synthetic manifest `p14-synthetic-manifest-1.0.0`, every object labelled "Synthetic - no third-party rights". [EV: P14-AUDIT-001]
- [ ] Human annotations: BLOCKED (P14-T19).

## 7. Results (audit-only; fill from frozen artifacts — no hand-entered numbers)
- [ ] Table 1: per-criterion conformance with Wilson/Clopper-Pearson CIs. [EV: P14-AUDIT-001 → metrics_summary.json]
- [ ] Table 2: C0 / C1 / proposed object verdicts + exact McNemar (verdict comparison only). [EV: P14-AUDIT-001 → baseline_results.json]
- [ ] Table 3: UDL-principle coverage per framework. [EV: P14-AUDIT-001]
- [ ] Figure 1: missing-affordance heatmap per object×criterion. [EV: P14-AUDIT-001]
- [ ] Remediation list excerpt (appendix). [EV: P14-AUDIT-001]
- [ ] Mutation/ablation results (named mechanisms). [EV: P14-AUDIT-001 → ablation_results.json]

## 8. Discussion (skeleton)
- [ ] What the audit catches that a checklist misses (verdict-level, descriptive only).
- [ ] Design guidance for rights-cleared heritage media production (CC0 pipelines, per-item rights checks).

## 9. Threats to Validity (mandatory)
1. **No human user study** → **no learning-benefit claim**; task completion, SUS and teacher scoring were not measured; H0 untested.
2. Synthetic objects = rules-oracle: results characterise the audit system, not real collections; no SOTA, no external generalisation.
3. Manifest-level audit: contrast from declared pairs, not rendered pixels; no screen-reader/AT testing; declarative flags could misdescribe deployed artefacts.
4. Single synthetic domain: spec requires ≥2 external domains for generalisation — not met, not claimed.
5. External media unavailable (Smithsonian/Europeana keys) → external validity unverified.

## 10. Ethics & integrity
- No human participants; no fabricated annotator IDs; rights labels are declarations of absence (synthetic), never claims of permission.
- H0 must be published as not rejected/untested if the human arm never runs.

## 11. Evidence ledger
| Evidence ID | Artifact | sha256 (see run_manifest.sha256) |
|---|---|---|
| P14-AUDIT-001 | research_artifacts_v3/runs/p14/audit_report.json | (frozen at release) |
| P14-RIGHTS-001 | research_artifacts_v3/runs/p14/prereg_snapshot.json + rights cards in audit_report.json | (frozen at release) |

## 12. Reproduction
```bash
python -m research_v3.experiments.p14.run_experiment   # regenerates all artifacts deterministically
python -m research_v3.methods.p14.cli_audit --out research_artifacts_v3/runs/p14 --baselines
python -m pytest tests/research_v3/method -q
```
