# P10 — Method specification (frozen before engine implementation)

**Task tickets:** P10-T01 (RQ freeze), P10-T03 (schema), P10-T09 (method contract).
**Status of this paper:** DESIGN + PEDAGOGICAL_VALIDATION_REQUIRED. No algorithmic-optimality claim (that is P02's boundary; see `01_AUDIT/LN_TO_P_MAPPING.md`: "P02 vs P10: algorithm/optimization vs instructional design/teacher validation").

## 1. Research question, estimand, null (P10-T01)

**RQ (verbatim from paper packet §1):**
"Tính liên tục, tăng độ sâu nhận thức và phù hợp CTGDPT của chuỗi học liệu di sản số theo 3 lớp được chuyên gia đánh giá như thế nào?"
(How do experts rate the continuity, cognitive-depth ascent, and GDPT-2018 fit of the three-layer digital heritage learning sequence?)

**Machine-checkable proxy estimand (this repo, pending human validation):** the proportion of
generated spiral sequences over the documented Cửu Đỉnh learning objects that pass all four
design invariants below, together with curriculum-anchor coverage and the count of anchors whose
GDPT-2018 mapping still requires expert confirmation (`needs_expert_review`).

**H0 (mandatory disclosure if not rejected; from packet §1):**
"Chuỗi xoắn ốc không có ưu thế nhất quán theo rubric so với chuỗi chuẩn do giáo viên xây dựng."
(The spiral sequence has no consistent rubric advantage over a teacher-built standard sequence.)
This H0 can only be tested with real teacher raters; it is **NOT tested** by this code. The code
produces the sequence artifacts that such a study would evaluate, plus the machine-checkable
invariant validity rate. Any expert-CVI/rubric claim is BLOCKED (P10-T19).

**Collision check with other P papers:** P02 owns constrained path *optimization*; P10 owns the
*instructional design artifact* (spiral sequence + curriculum crosswalk) and its pedagogical
validation protocol. P10's primary outcome is content validity by humans, not algorithmic
optimality; the machine metrics here are engineering gates, never re-interpreted as student gains
(spec `04_METHODOLOGY/ETHICS_AND_INTEGRITY.md` §5).

## 2. Domain model

### 2.1 Learning objects
The documented heritage corpus of this repo: 9 urns × 18 motifs = **162 motifs** (Cửu Đỉnh,
Đại Nội Huế, cast 1835–1837), loaded read-only from `data/0x_Data_*.json`. Each motif record
carries `id`, `name_vi`, `name_en`, `name_han_nom`, `category` (one of 9 documented categories:
`dia_ly, dong_vat, giao_thong, kien_truc, linh_thu, nong_nghiep, thao_moc, thien_van, vo_bi`),
`is_ai_generated` (currently True for all 162 — recorded honestly as a provenance limitation),
plus educational descriptions. Object media rights are NOT claimed; only the factual motif
inventory is referenced (AGENTS.md documents 9 urns / 162 motifs as repo ground truth).

### 2.2 Curriculum anchors (the honesty core)
An **anchor** is a claimed mapping from a learning object to a GDPT-2018 History curriculum
element for grades 10–12. GDPT 2018 is the public ministerial document Thông tư
32/2018/TT-BGDĐT. Each anchor carries:

- `anchor_code`: short identifier of the curriculum element.
- `confidence_status`: `"documented"` — the mapping rests on curriculum content the authors are
  certain is in the public document (e.g. "Chuyên đề 10.2: Bảo tồn và phát huy giá trị di sản
  văn hóa" exists in Lịch sử 10, per Thông tư 32/2018); or `"needs_expert_review"` — the specific
  competency-code/motif pairing requires a teacher to confirm.
- `source_citation`: exact citation string of the ministerial document (or repo-local catalog
  file with its SHA-256) that the mapping rests on.

**Fabrication guard (fail-closed):** any anchor whose `anchor_code` is not found in the frozen
anchor registry raises `UnknownAnchorError` at build time — an invented competency code can never
be silently accepted into a sequence. Unknown *category→competency* pairings flip
`confidence_status` to `needs_expert_review` and are counted, not hidden.

### 2.3 Three spiral layers (Bruner)
Bruner's spiral curriculum: the same structural ideas revisited with increasing complexity
(Bruner, 1960, *The Process of Education*, Harvard University Press). For this design paper the
three layers over grades 10–12 are:

- **L1 grade 10 — Nhận diện (Identify):** recognition of urns/motifs and their categories.
  Bloom: Remember/Understand (levels 1–2).
- **L2 grade 11 — Đối chiếu (Corroborate):** cross-referencing motif epigraphy with primary
  sources; Bloom: Apply/Analyze (levels 3–4).
- **L3 grade 12 — Đánh giá (Evaluate):** evidence-weighted argumentation about heritage value,
  territorial sovereignty inscriptions; Bloom: Evaluate (level 5). (Create=6 exists in the
  revised taxonomy but is out of scope for grade-12 history assessments here.)

The grade→Bloom-band gate is a **fixed constraint**, not a learned parameter.

## 3. Formal contract (P10-T09)

### 3.1 Types
```python
@dataclass(frozen=True) class CurriculumAnchor:
    anchor_code, grade (10|11|12), competency_ref, source_citation,
    confidence_status ("documented"|"needs_expert_review")

@dataclass(frozen=True) class LearningObject:
    object_id, urn_slug, motif_name_vi, category, bloom_level (int 1..6),
    anchor_code (must exist in registry), layer (1|2|3)

@dataclass(frozen=True) class SpiralSequence:
    ordered object ids; per-invariant certificates; overall VALID/INVALID
```

### 3.2 The four invariants (checked in this order; fail-closed)
1. **I-ACYCLIC** — prerequisite DAG over objects must be acyclic (Kahn DFS). Cycles are
   rejected, never topologically "resolved".
2. **I-GRADE-MONOTONE** — along every prerequisite edge, `grade(u) <= grade(v)`; grades confined
   to {10, 11, 12}. Grade inversion is rejected.
3. **I-BLOOM-ASCENT** — along every progression edge, `bloom(v) >= bloom(u)` with a configurable
   minimum ascent `min_ascent` (default 0 within-layer, >=1 across layers). A **leap** of more
   than `max_leap` (default 2) Bloom levels across one edge is flagged `bloom_leap_flagged`
   (warning-level certificate, not auto-rejection — an expert judges jumps; the run report
   counts them).
4. **I-ANCHOR** — every object's `anchor_code` must exist in the frozen anchor registry AND the
   anchor must be usable for the object's grade. Missing/unknown anchors are rejected
   (`UnknownAnchorError`), never silently dropped.

### 3.3 Sequence builders (designs under comparison)
- **C0 `linear_playlist`** — chronological-category playlist; no DAG, no gating (sanity floor).
- **C1 `topological_no_bloom`** — Kahn topological order over the prerequisite DAG with the
  anchor gate on, Bloom ascent gate off (tests the mechanism of depth gating).
- **Proposed `spiral_dag`** — layer-clustered topological order with across-layer bridge edges,
  Bloom ascent + leap flagging, anchor crosswalk gate.

Determinism: iteration is over sorted keys; ordering ties broken by `object_id`; no RNG in the
proposed builder. The A4 ablation (random order) uses a seeded RNG and is the only stochastic
design, by construction.

### 3.4 Complexity
Cycle check O(V+E); topological sort O(V+E); grade/Bloom/anchor gates O(E + V).
V = 162 objects (+ bridge nodes), E = prerequisite edges (<= ~1000 for this corpus). Millisecond
scale on CPU; no GPU.

### 3.5 What is fixed vs learned
Nothing is learned. All thresholds (`min_ascent`, `max_leap`, grade bands) are fixed constraints
preregistered here. This is a constraint-checked design generator, not a fitted model; there are
no hyperparameters to tune, hence no tuning budget to report (P10-T11 records wall time only).

## 4. Honest scope boundaries
- The engine's VALID/INVALID certificates are **software engineering gates**, never pedagogical
  endorsement. Pedagogical validation (expert CVI, rubric ratings) requires real teachers:
  P10-T19/T20/T21 remain BLOCKED.
- The GDPT-2018 anchor registry contains only content the authors can cite; specific
  competency-code pairings that a teacher must confirm are marked `needs_expert_review` and
  counted in every run report.
- Motif descriptions are AI-generated repo content (`is_ai_generated: true` for all 162);
  the sequence design references object identities, not asserted historical truth. Historical
  truth gating is P12's boundary.
- No archival permission is claimed for Huế sources; the external dataset card
  `hue-heritage-corpus` stays BLOCKED in `research_v3/datasets/registry.yaml`.

## 5. Reuse
- `research_v3/contracts/cards.py` (EvidenceCard/ExperimentCard/DatasetCard) for provenance.
- `research_v3/eval/statistics.py` (`proportion_ci`) for validity-rate uncertainty.
- `research_v3/eval/splitters.py` is NOT used for sequence design (no learner data) but the
  deterministic-hash convention (`research_v2.contracts.canonical_hash.sha256_input`) is reused
  for artifact hashing.
- Conceptual reuse of LN-01's spiral-progression gate semantics (reject_cycle /
  reject_grade_order / reject_missing_anchor / reject_no_progression), reimplemented fresh for
  P10's three-layer design rather than importing the V2 decision engine, because P10 sequences
  carry layers + bridges that LN-01's per-case graph schema does not model. The divergence is
  documented here per the LN→P reuse map.
