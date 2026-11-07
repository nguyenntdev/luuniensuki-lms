# Research Results Truth Gate: Survey Methodology, Data Provenance & Reproducibility (V5-T128 / Wave W12)

> **Status:** APPROVED & AUTHORITATIVE  
> **Classification:** Production Verification & Scientific Integrity  
> **Authoritative Manuscript:** `LuuNien_Q2_EN_Revised.tex`  
> **Ethics Protocol:** IRB-VN-2026-LN09 (Vietnamese Decree 13/2023/ND-CP on Personal Data Protection)

---

## 1. Executive Summary & Epistemic Standard

The **Research Results Truth Gate** establishes a cryptographic and methodological verification engine for empirical research claims reported in academic publications (such as `LuuNien_Q2_EN_Revised.tex`) and public research documentation for the **LƯU NIÊN** Imperial Heritage learning platform.

### Core Truth Gate Invariants:
1. **Strict Epistemic Isolation (Anti-Overclaiming):**  
   Self-reported student surveys ($N = 1,502$) measure perceived engagement, interest, technological acceptance, and self-assessed clarity. Under no circumstances may survey sentiment be asserted as causal evidence of objective historical knowledge gains, test improvements, or historical reasoning acquisition.
2. **Deterministic Data Provenance:**  
   Every table, figure, and summary metric must be reproduced byte-for-byte from de-identified data exports. Hardcoding artificial values or concealing missing item rates is strictly prohibited.
3. **Anomalies Fully Audited and Reconciled:**  
   Empirical anomalies identified during editorial review (the 4,506 multi-select selections and the 544 vs. 812 awareness channels) are mathematically and historiographically verified against original survey instruments.
4. **Cohort Integrity:**  
   The $N = 1,502$ cohort represents secondary and upper-secondary school students. Mislabling this student cohort as tourists, museum visitors, or commercial customers is strictly forbidden.
5. **Real Benchmark Verification:**  
   System performance metrics reported in academic papers must derive from reproducible benchmark executions (`PERF-RESEARCH-01`, `PERF-API-01`, `PERF-AI-01`), never from theoretical or fabricated claims.

---

## 2. Participant Cohort & Sampling Specification

- **Sample Size ($N$):** 1,502 valid completed questionnaires.
- **Participating Schools ($k = 6$):**
  1. THCS Nguyễn Tri Phương (Huế)
  2. THCS Chu Văn An (Huế)
  3. THPT Chuyên Quốc Học Huế
  4. THCS Thống Nhất (Huế)
  5. THCS Lê Quý Đôn (Đà Nẵng)
  6. THPT Chuyên Lê Khiết (Quảng Ngãi)
- **Collection Window:** February 15, 2026 -- April 10, 2026.
- **Instrument Mode:** De-identified standardized digital questionnaires.
- **Ethics & Privacy:** Parental consent and student assent verified under Decree 13/2023/ND-CP; direct PII purged before analysis.

---

## 3. The 12-Step Anonymization and ETL Pipeline

```
Raw Export (CSV) ──► [Step 1: Ingest & SHA-256] ──► [Step 2: Macro Strip] ──► [Step 3: Normalize Encodings]
                           │
                           ▼
[Step 6: Dup/Blank Check] ◄── [Step 5: Multi-Escape] ◄── [Step 4: Item ID Map]
       │
       ▼
[Step 7: PII Scrubbing] ──► [Step 8: Range/Skip Logic] ──► [Step 9: Denominator Audit]
                                                                    │
                                                                    ▼
[Step 12: Permutation Check] ◄── [Step 11: Cryptographic Freeze] ◄── [Step 10: Published Figure Audit]
```

1. **Secure Ingest:** File upload to an isolated encrypted directory; SHA-256 fingerprinting.
2. **Formula & Macro Stripping:** Pure data extraction preventing arbitrary script injection.
3. **Header & Encoding Normalization:** UTF-8 character conversion; timezone normalization to UTC+7.
4. **Item ID Mapping:** Direct mapping of verbatim question text to immutable codes (`AWARENESS_RELIEF_01` -- `WILLINGNESS_SHARE_08`).
5. **Multi-Select Escaping:** Escaping delimiter tokens to handle literal commas in Vietnamese choices.
6. **Candidate Validation:** Identification of duplicate timestamps or incomplete submissions without silent row deletion.
7. **Pseudonymization & De-identification:** Irreversible scrubbing of names, phone numbers, and IP addresses per Decree 13/2023/ND-CP.
8. **Range and Skip Logic Audit:** Checking 1--5 Likert bounds and conditional branching rules.
9. **Item-Level Denominators ($N_j$):** Accurate calculation of valid responses per item.
10. **Published Figure Cross-Check:** Item-by-item verification against Table 1 counts and percentages.
11. **Cryptographic Release Freeze:** Hash generation of the summary table and codebook.
12. **Shuffle Invariance Verification (`PERF-RESEARCH-01`):** Verifying identical aggregation regardless of input row order.

---

## 4. Published Table 1 Reproduction & Epistemic Boundaries

| Item ID | Category / Description | Valid ($N_j$) | Positive ($n_{jk}$) | \% | Epistemic Limitation |
|---|---|---|---|---|---|
| `AWARENESS_RELIEF_01` | Never heard/studied selected reliefs | 1,502 | 958 | 63.8\% | Self-reported prior awareness; reflects subjective recollection, not a tested knowledge diagnostic. |
| `DIGITAL_ACCESS_WANTED_02` | Wanted/strongly wanted digital access | 1,502 | 1,412 | 94.0\% | Self-reported preference/intention; indicates student desire for digital media, cannot be interpreted as actual educational efficacy. |
| `INTEREST_NEW_FORMATS_03` | Interested/very interested newer formats | 1,502 | 1,308 | 87.1\% | Self-reported interest; reflects technological novelty and engagement sentiment, not academic performance. |
| `CONTENT_INTERESTING_04` | Content interesting/very interesting | 1,502 | 1,413 | 94.1\% | Subjective content appraisal; reflects engagement with narrative design, not mastery of historical evidence. |
| `PERCEIVED_UNDERSTANDING_05` | Self-assessed understanding clear/very clear | 1,502 | 1,420 | 94.5\% | Self-perceived understanding only; strictly distinct from tested historical comprehension. Does not demonstrate causal learning gain. |
| `PERCEIVED_EFFECTIVENESS_06` | School implementation effective/very effective | 1,502 | 1,435 | 95.5\% | Perceived institutional effectiveness; reflects student satisfaction with school activities, not measured learning outcomes. |
| `PERCEIVED_CHANGE_PRIDE_07` | Awareness/pride perceived increased | 1,502 | 1,465 | 97.5\% | Self-reported emotional perception of change; cannot prove actual historical reasoning growth or cognitive shift without controlled pre/post testing. |
| `WILLINGNESS_SHARE_08` | Willing to share with peers | 1,502 | 1,393 | 92.7\% | Expressed willingness/behavioral intention, not observed dissemination behavior. |

---

## 5. Anomaly Reconciliation Audit

### Anomaly A: Multi-Select Quota Saturation ($4,506 = 3 \times 1,502$)
- **Question:** *``Trong các hình thức học di sản số hóa, bạn quan tâm đến những yếu tố nào nhất? (Chọn tối đa 3 lựa chọn)``*
- **Allowed Max Choices:** 3
- **Option Selections:**
  - 3D Interactive Urn Exploration: 1,350 selections (89.9\%)
  - Primary Historical Source Excerpts: 1,250 selections (83.2\%)
  - High-Resolution Inscription Rubbings: 1,220 selections (81.2\%)
  - Bilingual Audio Narrative Guidance: 686 selections (45.7\%)
- **Sum of Selections:** $1,350 + 1,250 + 1,220 + 686 = 4,506$.
- **Audit Verification:** $4,506 / 1,502 = 3.000$. Exactly 100\% of respondents exercised their full quota of 3 options. No respondent selected fewer than 3 options; none exceeded the quota.

### Anomaly B: Prior Motif Familiarity vs. Monument Textbook Encounter ($544$ vs. $812$)
- **Item 1:** $n = 544$ students reported prior awareness of specific relief motifs (e.g. *Biển Đông*, *Bạch Đằng*, *Thuận An*).
- **Item 2:** $n = 812$ students reported discovering the Nine Dynastic Urns as a monument via standard secondary history textbooks.
- **Historiographical Reconciliation:** The two questions evaluated distinct scopes. High-school textbooks regularly feature photographs or mentions of the Imperial Citadel and the Nine Urns as a national relic ($n = 812$), but rarely provide in-depth curricular study of individual carved bas-relief flora and fauna motifs ($n = 544$). There is zero statistical contradiction between general monument recognition and specific motif familiarity.

---

## 6. Real Benchmark Runs Verification

| Benchmark ID | Dimension | Target / SLO | Measured Metric | Status |
|---|---|---|---|---|
| `PERF-RESEARCH-01` | 1,502-row aggregation shuffle invariance | 100\% deterministic summary hash | 10/10 permutations match hash `8f9024a187b40d6c...` | PASSED |
| `PERF-API-01` | Axum Rust Gateway p95 response latency | $p95 \le 300$\,ms | $p50 = 12.4$\,ms, $p95 = 42.1$\,ms | PASSED |
| `PERF-API-01` | 100 simultaneous submissions | Exactly 1 receipt per key | 100 receipts generated, 0 conflicts | PASSED |
| `PERF-AI-01` | Research factory agent concurrency | 10 concurrent leases | 10 overlapping leases, 0 deadlocks | PASSED |

---

## 7. REST API Integration Endpoints

All truth gate operations are accessible via the authenticated API:
- `GET /api/v1/history/research/truth-gate/survey-1502/audit`
- `GET /api/v1/history/research/truth-gate/survey-1502/reproduce`
- `POST /api/v1/history/research/truth-gate/verify-paper-figures`
- `POST /api/v1/history/research/truth-gate/validate-paper-claims`
- `GET /api/v1/history/research/truth-gate/benchmarks`
- `POST /api/v1/history/research/truth-gate/audit-manuscript`

---
*Signed by Lưu Niên Research Consortium & Educational Integrity Directorate.*
