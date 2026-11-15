# P11 Blind Annotation Pack — README & Status

**Paper:** P11 — Rubric for historical reasoning competency (S1–S4).
**Status: `BLOCKED_AWAITING_HUMAN_RATERS`** — the pack is a *protocol + instrument*
artifact. No annotations exist. No annotator IDs, timestamps, or agreement numbers are
filled anywhere; every such field is an empty template.

## Contents

| File | Purpose | Fabricated content? |
|---|---|---|
| `CODEBOOK.md` | S1–S4 descriptors, NA/ABSTAIN rules, decision rules, blind protocol | No — instrument definition |
| `ANNOTATION_CARD.md` | Batch card per the 09_REFERENCE template; every evidence field empty | No — blank form |
| `assignment_template.csv` | Blind assignment sheet: columns only, zero rows | No — headers only |
| `ratings_template.csv` | Long-format rating record: columns only, zero rows | No — headers only |
| `adjudication_log_template.csv` | Disagreement/adjudication log: columns only, zero rows | No — headers only |
| `adjudication_protocol.md` | How disagreements are adjudicated; first ratings immutable | No |
| `constructed_cases/CC01..CC06.json` | Built deterministic calibration cases (not human data) | Labeled constructed |
| `constructed_cases/expected_levels.csv` | Scorer pinning table for the 6 cases | Labeled constructed |
| `make_wide_matrix.py` | Long→wide export for the reliability harness | Tool, no data |

## What happens when real raters exist (unblocks P11-T19)

1. Ethics approval + guardian consent records verified (per 04_METHODOLOGY/ETHICS_AND_INTEGRITY.md) — *actual documents, not assertions*.
2. Recruit ≥2 independent raters; assign pseudonyms `rater_A`, `rater_B`, ... in `ANNOTATION_CARD.md`; identity mapping stays outside Git.
3. Fill `assignment_template.csv` (randomized, blind, no rater sees another's scores).
4. Calibration round on `constructed_cases/`, codebook version bump if needed.
5. Blind round on real consented responses; ratings in `ratings_template.csv` format.
6. Export wide matrix via `make_wide_matrix.py`; run `research_v3/methods/p11/reliability.py::compute_reliability` with `is_synthetic_toy=False`.
7. Only then may κ_w / α / ICC appear in `research_artifacts_v3/runs/p11/` and the manuscript — with the annotation batch card ID as provenance.

Until step 1 is real: every results cell in the P11 manuscript says **BLOCKED**.
