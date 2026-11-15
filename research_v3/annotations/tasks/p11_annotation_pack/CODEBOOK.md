# Codebook — P11 Rubric v1 (Historical Reasoning, S1–S4)

**Instrument:** P11_rubric_v1 (version 1.0.0) — canonical descriptor text in
`research_v3/methods/p11/rubric.py` (`LEVEL_DESCRIPTORS`); this codebook repeats it verbatim.
**Status:** instrument + protocol READY FOR CALIBRATION; **no agreement statistic exists yet**
(P11-T19 BLOCKED — no human raters, no ethics approval, no consented responses).
**Language:** raters may rate in Vietnamese or English; descriptors are bilingual.

## 1. What raters judge

Each unit is one student response **declared as structure** — a list of claims, a list of
evidence items, and claim–evidence links (relation: supports / refutes / contextualizes).
Raters do NOT read free prose; if a response's prose contains material not declared in the
structure, the extraction step failed and the unit goes to the adjudication log with reason
`EXTRACTION_GAP`, not a guessed rating.

## 2. The four criteria (ordinal 0–3)

### S1 — Sourcing (Định vị nguồn)
| Level | Descriptor (canonical) |
|---|---|
| 0 | Không sử dụng bằng chứng nào (no evidence used). |
| 1 | Dẫn ra bằng chứng nhưng không nêu nguồn (evidence asserted without provenance). |
| 2 | Mô tả nguồn nhưng không trích dẫn cụ thể (provenance described but not cited). |
| 3 | Trích dẫn nguồn chính/thứ cấp xác thực kèm định vị archival (cited authentic source with locator). |

### S2 — Corroboration (Đối chiếu)
| Level | Descriptor |
|---|---|
| 0 | Chỉ dùng một hoặc không dùng bằng chứng nào (single or no evidence). |
| 1 | Có ≥2 bằng chứng nhưng không gắn với luận điểm (evidence present but unlinked to claims). |
| 2 | Bằng chứng được gắn hỗ trợ ít nhất một luận điểm (linked support, no cross-checking). |
| 3 | Đối chiếu chéo giữa các bằng chứng, kể cả bằng chứng phản bác/giới hạn (cross-checked, incl. refuting evidence). |

### S3 — Contextualization (Đặt trong bối cảnh)
| Level | Descriptor |
|---|---|
| 0 | Không có bối cảnh (no context). |
| 1 | Bối cảnh chung chung, không thời gian/không gian (generic, undated context). |
| 2 | Bối cảnh có thời gian/không gian gắn với luận điểm (dated/spatial context linked to a claim). |
| 3 | Bối cảnh giới hạn phạm vi/giá trị của luận điểm (context constrains claim scope). |

### S4 — Argumentation (Lập luận)
| Level | Descriptor |
|---|---|
| 0 | Luận điểm không có suy luận (claim without inference). |
| 1 | Suy luận mô tả (descriptive inference). |
| 2 | Suy luận giải thích hỗ trợ luận điểm (explanatory inference). |
| 3 | Chuỗi suy luận tường minh, xử lý phản bác hoặc phản chứng (explicit chain incl. refutation/counterfactual). |

## 3. Non-ordinal marks — never merged with 0

| Mark | Use when | Enters agreement math? |
|---|---|---|
| `NOT_APPLICABLE` | The prompt/task did not require this criterion (e.g., a task with no source packet → S1 cannot apply). | No — recorded as coverage, excluded, never imputed |
| `ABSTAIN` | You cannot judge even with the codebook (ambiguity not resolvable; extraction suspect). | No — logged, triggers adjudication |

If you are torn between two levels: **rate the lower level you can defend** and flag `uncertain=1`
in the rating row. Do not ABSTAIN merely because you must choose between adjacent levels.

## 4. Decision rules (deterministic aid, mirrors scorer)

1. **Zero-evidence cap:** a response declaring **no evidence items** cannot exceed level 0 on
   S1/S2/S3 and cannot exceed level 1 on S4, regardless of how rich its claims are.
2. **Fabricated-source cap:** a response whose citations are all non-authentic (invented
   archive names, unverifiable references) is capped at level 1 on S1 — a citation that does
   not point to a real source is not sourcing.
3. **Single-evidence cap:** with exactly one evidence item, S2 cannot exceed level 1 unless
   the item is cross-checked against an external reference the rater can verify — in blind
   rating this is not available, so effectively level ≤ 1.
4. **Context must bind:** context counts for S3 only when it is *linked* to a claim (via a
   contextualizes link or explicit bind in the structure), not mentioned in passing.
5. **Context must constrain for level 3:** S3 reaches level 3 only when the claim itself
   states its validity conditions (time/place bounded — the `scope_limited` flag in the
   declared structure); context attached to an otherwise unbounded claim is level 2.
6. **Refutation handling:** S4 reaches level 3 only when the response engages a counter-
   position (refuting link or counterfactual claim), not merely cites disagreeing evidence.

## 5. Order of work (blind protocol)

1. Calibration round: all raters rate the same 6 constructed cases (§6); discuss divergences
   ONLY after everyone has submitted; update codebook (bump version) if descriptors were
   ambiguous; re-rate from scratch if the codebook changes. **Never edit first-round ratings.**
2. Blind round: units are assigned so that no rater sees another rater's scores; rater pairs
   are rotated; unit order is randomized per rater; response identities (student names,
   schools) are stripped before distribution — pseudonymous `unit_id` only.
3. Disagreements (any criterion differing by ≥2 levels, or any ABSTAIN) go to the
   adjudication log with both first-round ratings preserved.

## 6. Constructed calibration cases (NOT human data — label everywhere)

Six constructed cases ship with this pack (`constructed_cases/*.json`). They are **built,
not observed**: deterministic structures exercising each descriptor boundary. They exist so
(a) the scorer can be pinned to expected levels and (b) future raters have a calibration set.
They are **not** evidence of reliability, and no agreement number may ever be computed from
scorer self-ratings presented as rater data.

| case_id | expected S1 | expected S2 | expected S3 | expected S4 |
|---|---|---|---|---|
| CC01_zero_evidence | 0 | 0 | 0 | ≤1 |
| CC02_asserted_only | 1 | 1 | 1 | 1 |
| CC03_described_cited | 2 | 2 | 2 | 2 |
| CC04_full_chain | 3 | 3 | 3 | 3 |
| CC05_fabricated_citation | ≤1 | 2 | 2 | 2 |
| CC06_refutation_handled | 3 | 3 | 3 | 3 |

## 7. Rating record fields (one CSV row per unit × rater × criterion)

```
unit_id, rater_id (pseudonym), criterion, rating (0|1|2|3|NOT_APPLICABLE|ABSTAIN),
uncertain (0/1), seconds_elapsed, batch_id, codebook_version, rated_at (ISO-8601)
```

Long format is canonical; the reliability harness accepts the wide per-criterion matrix
export (`to_wide_matrix()` in the pack) with one row per unit and one column per rater.

## 8. What this codebook does NOT authorize

- No synthetic raters, no synthetic agreement numbers, no "pilot" ratings by authors
  presented as independent raters.
- No reuse of AI-tutor training conversations (P03) as rating units — P11 measures human
  rater reliability on student work, not model output quality.
- No agreement statistics computed until at least 2 independent human raters have completed
  the blind round under an approved protocol (P11-T19 BLOCKED until then).
