# V2 original archival technical chapter — SECTION_20

> Extracted without rewriting from V2 snapshot documentation, **not verified current code**.

## 20. SCIENTIFIC PAPER TRACEABILITY / EVIDENCE REGISTER

### 20.1 Coverage matrix requirement→paper→artifact→status

| Scientific statement | Code evidence | Data evidence required | Artifact/release | Current claim status |
|---|---|---|---|---|
| 3D facilitates looking at geometry | viewer/assets | usability/accuracy test optional | A3D demo | only capability |
| 162 reliefs provided as case | 162 JSON + 162 JPG | authoritative 162 match + rights | canonical catalog | candidate inventory |
| Source-linked six-step sequence | models/learn roadmap partially | 3 end-to-end ELLO implemented | ELLO v1 | design proposal |
| Traceable sources | historical_claim_sources | review and locators per claim | source packet | partial framework |
| In-school feedback via LMS | quiz/classroom code | actual use, grader feedback | attempt history | not established for 1.502 |
| 1.502 respondents | article aggregate | raw Forms + questionnaire metadata | study snapshot | reported aggregate |
| 63.8% prior unfamiliar | published table | item reproducibility | analytics output | descriptive |
| 94.0% digital interest | published table | respondent level validation | analytics output | descriptive |
| 95.5% perceived effective | published table | original wording | analytics output | perception ONLY |
| Better historical reasoning | no measured outcome | comparison/rubric and direct scores | future trial | NOT demonstrated |
| AI trustworthy | RAG code + benchmark docs | blind independent benchmark actual production | eval report | hypothesis until tested |
| Tourism visitor benefit | discovery/inquiry | visitor/partner pilot data | ICTIM track | not inferred from student survey |
| CALL language learning | partial bilingual content | genuine language tasks + language outcomes | GLoCALL track | conditional module |

### 20.2 Paper evidence freeze protocol

For each submission: `paper_id`, `paper_title`, `intended venue`, `experiment?`, `data_snapshot_id`, `instrument_version`, `ELLO_release_sha`, `figures_sha`, `claims_used`, `funding/COI`, `prior-overlap-declaration`, `authors_contributions`, `analysis_script_sha`, `ethics_ref`, `review_log`. Khi thay đổi hệ thống sau khi khảo sát, **không backdate** chức năng như thể 1.502 học sinh đã dùng phiên bản mới.

### 20.3 Reviewer-facing reproducibility bundle

- Public: README, sample synthetic records, schema, aggregate counts, scripts, source-register metadata appropriate for license, screenshot and ELLO walkthrough.
- Restricted: anonymized respondent-level CSV under data access agreement only if appropriate/consented; consent forms not in public bundle.
- Cite original project dossier provenance and distinguish publications to avoid duplicate publication/salami slicing.

---

