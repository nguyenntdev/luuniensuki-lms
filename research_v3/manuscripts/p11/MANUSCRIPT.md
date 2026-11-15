# P11 — Xây dựng và kiểm định rubric đánh giá năng lực suy luận lịch sử trong môi trường học tập số
# Construction and validation of a rubric for historical reasoning competency in digital learning environments

**Status: `BLOCKED — RATER_AND_SAMPLE_REQUIRED`.** This skeleton complies with the prereg
(`research_v3/methods/p11/pre_registration.yaml`, frozen 2026-11-15). Every results cell
currently reads BLOCKED. **No validity or reliability claim is made anywhere in this
manuscript** because no human raters or consented responses exist yet (P11-T19/T20/T21
BLOCKED). The paper will not be submitted in its current state.

---

## 1. Introduction & RQ
Historical reasoning — sourcing (định vị nguồn), corroboration (đối chiếu), contextualization
(đặt trong bối cảnh), argumentation (lập luận) — is the construct triad established by the
historical-thinking literature (Wineburg 1991; Seixas & Morton's six concepts; Monte-Sano 2011
for rubric-based writing assessment; Breakstone & Smith 2012 for item design; van Boxtel &
van Drie for collaborative reasoning frameworks). Vietnamese heritage education (Cửu Đỉnh
program) lacks a validated competency instrument for these skills in digital environments.

**RQ (frozen).** Does rubric S1–S4 achieve content validity (CVI), inter-rater reliability
(κ_w, α, ICC) and level discrimination appropriate for assessing historical reasoning,
compared with current single-holistic marking?

**H0 (published if not rejected).** The multi-criterion rubric does not increase reliability/
validity over the current single-dimension scale.

**Novelty boundary.** P11 validates an *assessment instrument*; it does not evaluate the AI
tutor (P03), curriculum ordering (P10's spiral rubric is a curriculum-alignment metric, not a
competency instrument), or UDL affordance ratings (P14). No other P paper shares this RQ,
sample type, or principal table (collision audit 2026-11-15, see `experiments/p11/`).

## 2. Related work
- **Historical thinking & assessment:** Wineburg (1991) heuristic triad; Monte-Sano (2011)
  argument-writing rubrics; Breakstone & Smith (2012) disciplined-history items; Nokes
  (2013) evidence-use frameworks; van Drie & van Boxtel (2008) historical-reasoning
  inventory. *These define the construct; none is re-implemented as a comparator without
  license/version pinning (B01/B02/B03 to be pinned at run time or honestly BLOCKED).*
- **Inter-rater reliability methodology:** Krippendorff (2004, 2011) content-analysis
  reliability with missing data; Cohen (1968) weighted kappa; Shrout & Fleiss (1979) ICC;
  Hayes & Krippauer (2007) software-independent alpha practice; Gwet (2014) on benchmark
  interpretation.
- **Rubric validation practice:** content-validity indexing (Lawshe 1975; Polit & Beck 2006
  I-CVI ≥ 0.78/ S-CVI ≥ 0.90), generalizability theory for rater effects (Shavelson & Webb).
- **Gap:** no validated Vietnamese-language historical-reasoning rubric with published
  reliability evidence for digital-environment scoring of declared evidence structures.

## 3. Method (implemented; see METHOD.md + rubric.py)
- **Instrument:** P11_rubric_v1 — 4 criteria × 4 ordinal levels (0–3), canonical bilingual
  descriptors; `NOT_APPLICABLE` and `ABSTAIN` distinguished from level 0; deterministic
  scorer over declared claim–evidence–link structure (not free-text NLP).
- **Decision rules:** zero-evidence cap, fabricated-source cap, single-evidence cap,
  context-must-bind, scope-limit rule for S3 level 3 (codebook §4).
- **Baselines:** C0 keyword-presence (B03 family, implemented); C1 rubric-applied-to-declared
  -evidence (implemented); B00/B02 holistic marking = human-only, BLOCKED; calibrated
  evidence-link-aware variant = hypothesis, requires rater data, not implemented.
- **Reliability analysis:** Krippendorff α (nominal/ordinal/interval), quadratic-weighted κ,
  ICC(A,1), Cronbach α as internal-consistency proxy; cluster (response) bootstrap CIs;
  implementations validated against the reference `krippendorff` package on 12 matrices ×
  3 levels (engineering verification, not a scientific result).
- **Blind protocol + adjudication:** annotation pack
  (`research_v3/annotations/tasks/p11_annotation_pack/`) — codebook 1.0.0, blind assignment
  template, immutable first-round ratings, adjudication log with preserved disagreements.

## 4. Results — **ALL BLOCKED**
| Cell | Content | Status |
|---|---|---|
| CVI (I-CVI, S-CVI) | ≥2 expert raters × 16 descriptors | **BLOCKED** — no expert panel (P11-T19) |
| κ_w per criterion (pre-adjudication, primary) | blind double-marking on real units | **BLOCKED** — no raters/responses |
| α (ordinal), ICC(A,1) | same matrix, ≥3 raters for ICC | **BLOCKED** |
| Discrimination (level usage distribution, rasch-style ordering check) | real rating distributions | **BLOCKED** |
| C0 vs C1 vs holistic contrast (F1–F3) | rater-consensus proxies | **BLOCKED** |
| Instrument internal consistency (Cronbach α) | rater×criterion matrix | **BLOCKED** |
| Scorer-vs-expected pinning on 6 constructed cases | deterministic check | **PASSED (engineering)** — labeled *constructed, not human*; carries no validity evidence |
| Agreement-math verification vs reference library | 36 comparisons | **PASSED (engineering)** — implementation correctness only |

**No synthetic number may replace any BLOCKED cell.** T3-style synthetic responses are
restricted to regression/canary roles and are never pooled into the validity estimate (spec §2).

## 5. Threats to Validity
1. **No human raters yet — the dominant threat.** Every validity/reliability claim is
   currently *unestimable*, not merely unestimated. Nothing in the engineering artifacts
   (deterministic scorer, agreement library, annotation templates) constitutes evidence
   about the instrument's measurement quality.
2. **Construct coverage risk.** S1–S4 may miss affective/procedural aspects of historical
   thinking; the CVI round is the designed check and has not occurred.
3. **Declared-structure dependency.** The scorer operates on declared structures; prose-only
   responses require an extraction step that introduces its own error channel (logged as
   `EXTRACTION_GAP`, units routed to adjudication).
4. **Language/translation risk.** Bilingual descriptors may not be culturally equivalent;
   the calibration round measures descriptor ambiguity only after raters exist.
5. **Circularity risk (mitigated).** The deterministic scorer shares decision rules with the
   codebook; rater agreement could reflect rule adherence, not construct measurement. The
   pre/post-adjudication double reporting and the holistic comparator (F3) are the designed
   mitigations.
6. **Sample risk.** Recruitment shortfall would shrink n and widen CIs; per prereg, achieved
   n and widened CIs are reported honestly; no substitution with constructed cases.
7. **Selection risk.** Consented responses may not represent the population; generalization
   limited to the consented population and stated as such.

## 6. Limitations (stated in the paper if submitted after unblocking)
Instrument validation is population- and language-bound; kappa benchmarks are conventions,
not laws; single-institution samples limit generalization; adjudication is itself a human
judgment and is reported transparently (pre-adjudication primary).

## 7. Data & code availability
- Rubric + scorer: `research_v3/methods/p11/rubric.py` (deterministic; property-tested).
- Reliability harness: `research_v3/methods/p11/reliability.py` (fail-closed on empty input).
- Annotation pack: `research_v3/annotations/tasks/p11_annotation_pack/` (templates empty).
- Run manifests: `research_artifacts_v3/runs/p11/` (status ledger; no metrics).
- Prereg: `research_v3/methods/p11/pre_registration.yaml` (frozen 2026-11-15).

## 8. Authorship & submission gate
**BLOCKED (P11-T21).** No author list, no venue commitment, no submission until: human
ethics approval verified (T19), novelty signoff with full-text overlap matrix (T20), and
coauthor/venue signoff (T21). H0 must be published if not rejected.
