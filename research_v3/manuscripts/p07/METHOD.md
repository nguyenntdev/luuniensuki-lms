# P07 Method — Affordance-Complete Multimodal Learning Object Selection

**Version:** p07-proposed-v1.0 · **Frozen:** 2026-11-15 (before any scored run)

## 1. Problem

Given a learning task T, a device/accessibility context D, and candidate
multimodal learning objects O = {o1..on} with provider-recorded rights, select
a cognitively equivalent object that (a) affords every affordance T requires,
(b) is deliverable under D's bandwidth/device/AT constraints, and (c) carries a
license permitting the use — or return an explicit typed failure
(`reject_missing_affordance`, `reject_rights_violation`,
`reject_infeasible`, `abstain`), never a silent substitution.

## 2. Affordance ontology

Closed 11-axis multilabel vocabulary (`affordances.AFFORDANCE_VOCAB`):
`image, visual_detail, spatial_relation, relief_depth, inscription_text,
audio, audio_transcript, description, keyboard_accessible,
screen_reader_ready, spatial_interaction`.

Tri-state semantics: `True` (verified present, with a recorded derivational
fact), `False` (verified absent), `None` (**NOT_APPLICABLE / unverifiable**).
`None` is distinct from `False` and never satisfies a requirement.

**The V2 LN-07 lesson is an axiom here:** an object that HAS an image but
OMITS `inscription_text` is NOT cognitively equivalent for a task requiring
the inscription. Image presence never implies text presence.

## 3. Objective and decision rules (E1)

No learned weights exist in v1.0 — every rule is a fixed constraint. The
selector is a pure function:

```
feasible(o) ⇔ rights_ok(o) ∧ bandwidth_ok(o, D) ∧ device_ok(o, D) ∧ covers(o, R(T))
rights_ok(o)     ⇔ license_status(o) ∈ {CC0, CC-BY-4.0, CC-BY-SA-4.0, public_domain}
bandwidth_ok(o,D) ⇔ kb(o) ≤ max_payload(D) ∧ network_kbps(D) ≥ ceiling(modality(o))
                    ceilings: 3d=500, image/rubbing/audio=100, text=10 (kbps)
device_ok(o,D)   ⇔ (modality(o) ≠ 3d ∨ webgl(D))
                    ∧ (¬keyboard_only(D) ∨ keyboard_accessible(o))
                    ∧ (¬screen_reader(D) ∨ screen_reader_ready(o))
covers(o, R(T))  ⇔ ∀ r ∈ R(T): o.affords(r) = True        (None/False both fail)
select argmin over feasible(o) of (kb(o), object_id(o))     — deterministic
```

Typed failures (fail-closed):
- ALL candidates fail only the rights screen → `reject_rights_violation`
- some candidate has minimal missing-required-affordances > 0 and nothing is
  feasible → `reject_missing_affordance` (naming the missing axes + device codes)
- nothing feasible, no affordance gap identified → `reject_infeasible`
- empty candidate pool → `abstain`

`ABSTAIN` (nothing to judge) is distinct from all rejections (something was
judged and failed).

Complexity: O(n·|R(T)|) per case. Runtime cap: none needed (selection is
rule evaluation, no training).

## 4. What is novel vs reused

**Novel (this paper):** the derivational-fact affordance recording for
museum metadata (inscription status only when the provider record itself
states a transcription/translation; ambiguity → curator abstain), the
identifiability-by-paired-stress-stratum evaluation design (G16), and the
rights/affordance/constraint joint selection contract with typed failures.

**Reused (cited):** tri-state handling conventions and closed-vocabulary
multilabel affordances follow the V2 LN-07 policy engine's observable label
space (research_v2/methods/ln07, internal predecessor). Statistical
machinery (McNemar exact, cluster bootstrap, Holm, Wilson/Clopper-Pearson,
Cliff's delta) is the shared V2/V3 evaluation standard
(`research_v3/eval/statistics.py`, re-exporting
`research_v2/evaluation/statistical_tests.py`). Accessibility axes follow
WCAG 2.1 success criteria 1.2.1 (audio transcript), 2.1.1 (keyboard),
4.1.2 (semantics for AT).

## 5. Data rules

- External records: Smithsonian Open Access metadata repository (S3),
  unit FSG, snapshot state 2021-12-21, license CC0 1.0 (license text cached,
  SHA-256 pinned). Only records with `objectRights: CC0` AND all media
  `usage.access: CC0` are eligible. Rights are **copied observations**, never
  inferred from URL presence.
- Affordances are **derivational facts**: `image` from a CC0 Images media
  item; `inscription_text` only from an explicit transcription/translation
  statement in the record's Inscriptions notes. A record with an Inscriptions
  field lacking an explicit transcription statement is AMBIGUOUS → curator
  abstain (excluded from scoring, never guessed).
- Synthetic stress suites: LICENSE "synthetic, no third-party rights",
  `synthetic: true` on every case, used as regression/identifiability canary
  only — never pooled into external scores.

## 6. Limitations

- No learned parameters ⇒ no overfitting risk, but also no personalization;
  ranking is a fixed lexicographic rule.
- External pool is single-provider (FSG) ⇒ external generalization UNVERIFIED.
- No human evaluation of learning benefit (P14's scope); WCAG compliance is
  not certified (manual audit required);kb values for external objects are a
  studied delivery-size convention (320 KB), not measured payloads.
