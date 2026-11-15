# Submission gates: green software != publishable science

## G0 Source and identity
[ ] Repo head pinned; CI and release all reference same SHA. [ ] Prior V2 artifacts hashed read-only. [ ] V3 conflict-free source snapshot.

## G1 Data
[ ] Official URL, version, license file snapshot and SHA for every external source. [ ] Raw stored safely. [ ] Schema and dedup tests. [ ] Group/time split hash. [ ] No leakage. [ ] Real annotations only if verified.

## G2 Method
[ ] Source to RQ mapping. [ ] Mathematically stated objective. [ ] CPU/GPU budget. [ ] Baseline parity. [ ] C2 original published comparators if valid. [ ] Ablations and counterexamples.

## G3 Scientific results
[ ] No empty/extra/duplicate scored IDs. [ ] Primary effect and CI with proper unit. [ ] Negative cases included. [ ] Calibration, robustness, cost. [ ] Cross-seed interpretation correct. [ ] External-domain generalization appropriately bounded.

## G4 Distinct manuscripts
[ ] No duplicated primary outcome graph/table from another paper. [ ] Novelty prior-art review signed. [ ] Single evidence owner for key result. [ ] HCMUS/Q2/LN manuscripts disclosure in overlap register.

## G5 Ethics and historical accuracy
[ ] Human subjects clearance/consent actually verified if used. [ ] Teacher raters real and blind where claimed. [ ] Rights-cleared media. [ ] Archival quotation/translation reviewed and cited. [ ] Appropriate withdrawal/privacy.

## G6 Publication artifacts
[ ] Run manifest, data card, model card, reproducible tables/plots, paper, supplementary appendix, reference list, authorship/affiliation, transparency statement. [ ] Venue policy, rank and deadline independently reconfirmed for intended 2027 submission. [ ] Coauthor signoff.

## Fail-closed outcomes
If G1 or G5 fails: BLOCKED. If benchmark proves no improvement: preserve negative result and revise hypothesis; do not replace test. If novelty duplicates another P paper: MERGE_REQUIRED. If only synthetic evidence: SOFTWARE_EXPERIMENT_ONLY, never SUBMISSION_READY.
