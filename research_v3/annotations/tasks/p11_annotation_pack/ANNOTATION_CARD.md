# Annotation batch card (per LUU_NIEN_RESEARCH_V3_14_PAPERS_SPEC_20261115/09_REFERENCE/ANNOTATION_CARD_TEMPLATE.md)

> BLANK FORM. Fields marked `(REQUIRED-BEFORE-RATING)` must contain verifiable evidence
> before any rating session. Do not prefill; do not treat a protocol document as approval.

- paper_id: P11
- annotation_batch_id: *(REQUIRED-BEFORE-RATING)* — e.g. `P11_batch_001` (assign at first real session)
- item source + version hash: *(REQUIRED-BEFORE-RATING)* — consented student responses, SHA-256 of the response bundle manifest; constructed calibration cases use `research_v3/annotations/tasks/p11_annotation_pack/constructed_cases/` + its checksum
- ethics approval: *(REQUIRED-BEFORE-RATING)* — institution review record ID + verifiable document reference; **a Markdown protocol is not an approval**
- access permissions: *(REQUIRED-BEFORE-RATING)* — school/data-trust agreement reference
- guardian consent basis (minors): *(REQUIRED-BEFORE-RATING)* — consent register excerpt reference (IDs only, no PII in Git)
- codebook version: 1.0.0 (this pack's CODEBOOK.md)
- task-specific item prompts: *(REQUIRED-BEFORE-RATING)* — pinned prompt set version
- preregistered exclusion rules: responses with incomplete declared structure (unparseable), units with ABSTAIN on any criterion go to adjudication, duplicate submissions excluded by idempotency key
- rater_A pseudonym: *(REQUIRED-BEFORE-RATING)*
- rater_B pseudonym: *(REQUIRED-BEFORE-RATING)*
- (optional rater_C/D): *(REQUIRED-BEFORE-RATING)*
- blind assignment verified: *(REQUIRED-BEFORE-RATING)* — randomization seed + who verified
- timestamp of rating session: *(REQUIRED-BEFORE-RATING)*
- actual scoring records: *(REQUIRED-BEFORE-RATING)* — path to filled ratings CSV outside templates
- confusion matrix: *(REQUIRED-AFTER-RATING)*
- weighted kappa / Krippendorff alpha as fit: *(REQUIRED-AFTER-RATING)* — with CI and n; computed only by research_v3/methods/p11/reliability.py with is_synthetic_toy=False
- sample sizes (units, raters, complete pairs): *(REQUIRED-AFTER-RATING)*
- disagreements and adjudication evidence: *(REQUIRED-AFTER-RATING)* — first-round ratings preserved verbatim, never erased
- release decision: **BLOCKED until authentic annotation + approval available**
