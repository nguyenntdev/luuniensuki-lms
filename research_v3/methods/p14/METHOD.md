# P14 METHOD — UDL learning-object design & accessibility audit (frozen before results)

Paper: P14 — Thiết kế và đánh giá học liệu di sản đa phương thức theo Universal Design for Learning.
Status of this run: `ENGINEERING_PASS` + `PARTIAL` (external media BLOCKED; synthetic manifest used; no human study).

## 1. Research question, estimand, hypotheses

**RQ.** Mức độ tương đương nhiệm vụ và khả năng tiếp cận của học liệu đa phương thức thay đổi như thế nào khi áp dụng rubric UDL có đánh giá người dùng? (How do task equivalence and accessibility of multimodal learning objects change when a UDL rubric with user evaluation is applied?)

**Frozen estimand for this run (no human data available).** The audit-based estimand is the **accessibility conformance rate**: the proportion of applicable (PASS/FAIL) object×criterion audits that PASS, over a frozen manifest, under rubric `p14-udl-rubric-1.0.0`. Secondary: UDL-principle coverage per framework; missing-affordance count per object.

**H0 (preregistered, must be published if not rejected).** The UDL workflow does not improve task completion and accessibility after controlling for content. **This run cannot test H0**: task completion and SUS/teacher scoring require human participants (P14-T19 BLOCKED). Only the accessibility-audit half is measured, on synthetic objects, and is reported descriptively. No H0 rejection, no effect claim.

**Boundary vs P07 (collision check).** P07 = object *selection/retrieval* (which object to serve; NDCG@K, affordance recall, false-completion). P14 = *design & evaluation of the objects themselves* (UDL rubric + WCAG 2.2 AA audit with per-object verdicts and remediation). No shared primary table. See `research_artifacts_v3/runs/p14/overlap_decision.json` (decision: KEEP_SEPARATE / DISTINCT).

## 2. Fixed constraints vs learned parameters

- **Learned parameters: none.** `LEARNED_PARAMETERS = {}` is recorded in every artifact. The rubric is a fixed, versioned constraint set (UDL 3 principles + WCAG 2.2 AA affordances).
- Criterion applicability is a pure function of the object's media types (`criteria_for_media_type`); verdicts are pure functions of (object, rubric). No randomness, no thresholds fitted on data.

## 3. Data contract (P14-T03)

Input: `LearningObject` (schema `p14-schema-1.0.0`, see `research_v3/methods/p14/schema.py`):
- `object_id` (slug), `title`, `origin` (`external:<provider>` | `synthetic:<label>`), `source_url`, `rights` (mandatory string; synthetic objects must say "Synthetic - no third-party rights"), `assets[]` (`MediaAsset`: `asset_id`, `media_type` ∈ {image, audio, video, model3d, text}, mandatory `rights`, optional affordance flags: `has_text_alternative`, `has_transcript`, `has_captions`, `keyboard_operable`, `interactive`, `caption`), optional `low_bandwidth_variant[]`, `metadata` (declared `learning_goal`, `non_pointer_response`, `contrast_pair`, `respects_reduced_motion`, `player_keyboard_operable`, `focus_visible`, `keyboard_trap`).

Output: per-`CriterionResult` verdicts + `ObjectAuditVerdict` + `RemediationItem[]` + aggregate metrics.

**Verdict semantics (spec §3.1).** `PASS`/`FAIL` are real judgements; `NOT_APPLICABLE` (criterion does not apply to this object's media types) is excluded from the conformance denominator; `ABSTAIN` (evidence missing, e.g. no declared contrast pair) is excluded from numerator and denominator and reported separately. `FAIL is the only negative verdict` — NOT_APPLICABLE/ABSTAIN are never folded into FAIL.

## 4. Audit algorithm (pseudocode)

```
audit_object(obj, rubric):
  applicable := { c in rubric | c.applies_to ∩ media_types(obj) ≠ ∅ or c.applies_to = [all] }
  for c in applicable:
    verdict(c) := fixed rule c.criterion_id(obj)     # deterministic
    if verdict = FAIL: remediation += item(severity = c.critical ? critical : minor)
  whole := FAIL if any FAIL else ABSTAIN if all ABSTAIN else PASS
  return results, ObjectAuditVerdict(counts reconcile exactly)

compute_metrics(results, verdicts):
  real := {r | verdict(r) ∈ {PASS, FAIL}}
  conformance_rate := |{r ∈ real : PASS}| / |real|
  udl_coverage[framework] := pass-rate over real results of that framework
  missing_affordance_count := Σ_objects |missing_affordances(object)|
```

Complexity: O(|objects| × |criteria|) with constant-time per-criterion rules; memory O(|results|). No training, no GPU; wall time for the 12-object synthetic manifest is < 1 s on CPU.

## 5. Baselines (frozen, not tuned)

- **C0 "has an image"** (sanity): object PASSes iff it contains any visual asset. Expected to over-pass badly.
- **C1 WCAG-checklist-only**: media-type-appropriate asset flags only (`image→alt`, `model3d→alt+keyboard`, `audio→transcript`, `video→transcript+captions`); deliberately blind to UDL principles, low-bandwidth variants, keyboard traps, contrast and multi-modality at object level.
- **Proposed**: full UDL + WCAG audit (`audit_manifest`), same frozen manifest, same rubric version.

## 6. Metrics and statistics (P14-T14 scope, descriptive only)

- Conformance rate with Wilson + Clopper-Pearson 95% CIs (`research_v3/eval/statistics.py:proportion_ci`), unit = object×criterion audit.
- Paired proposed-vs-baseline object verdicts: exact McNemar (verdict comparison only; the fixed note forbids reporting it as a learning outcome).
- Missingness/abstains are reported, never imputed; denominators are exact.

## 7. Ablations / mutation counterexamples (P14-T10)

Named-mechanism mutations on synthetic objects (deterministic): `remove_alt_text`, `remove_transcript`, `remove_keyboard`, `remove_lbw`. Each mutation must flip exactly the criterion named by its mechanism (mutation-reveals-mechanism test); expected failure families are asserted post-run, never pre-declared as outcomes.

## 8. Rights and external data (P14-T02)

- Smithsonian Open Access: **BLOCKED** — API key required (HTTP 403 without key, verified 2026-11-15); only CC0-marked items would be eligible.
- Europeana: **BLOCKED** — API key required (HTTP 401 without wskey, verified 2026-11-15); metadata CC0 but item-level media rights vary.
- Huế heritage imagery: **BLOCKED and excluded** by study rule (no written permission; copyrighted imagery must not be reused).
- Fallback: documented synthetic manifest, every object labelled `synthetic:*` with rights "Synthetic - no third-party rights"; study mark **PARTIAL for external media**.

## 9. Limitations / threats to validity (manuscript-facing)

1. **No human user study** → no learning-benefit claim of any kind is permitted (`claims_guard` rejects benefit wording; H0 untestable this run).
2. Synthetic objects are rules-oracle instances: results characterise the *audit system*, not real heritage collections; no SOTA and no external-generalisation claim.
3. Contrast is audited from *declared* pairs, not rendered pixels; rendering-level contrast, screen-reader testing and keyboard walkthroughs require a real browser/human pass.
4. Affordance flags are declarative manifest fields; a hostile manifest could lie. The audit verifies internal consistency, not ground truth of deployed artefacts.
5. External media unavailable → external validity unverified (single synthetic "domain"; spec requires ≥2 external domains for generalisation claims, which is therefore **not claimed**).
