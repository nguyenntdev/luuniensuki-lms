# Ten-agent execution plan, resource/branch ownership and waves

| Agent | Exclusive ownership | Main responsibilities |
|---|---|---|
| A01 | `research_v3/contracts/`, `governance/` | Source audit, immutable schema and claim ledger |
| A02 | `research_v3/datasets/`, `datasets/` | Official external data acquisition, licensing, ingestion and split registry |
| A03 | `research_v3/methods/p01/`, `p04/` | KT selective transfer + independent benchmark protocol |
| A04 | `research_v3/methods/p02/`, `p10/` | Path optimization and curriculum mapping support |
| A05 | `research_v3/methods/p03/`, `p09/` | Tutor source calibration and heritage provenance interface |
| A06 | `research_v3/methods/p05/`, `p13/` | Temporal KT and SRL construct features |
| A07 | `research_v3/methods/p06/`, `p11/` | Risk ranking, rubric and annotator reliability |
| A08 | `research_v3/methods/p07/`, `p14/` | Multimodal retrieval and UDL accessibility |
| A09 | `research_v3/methods/p08/`, `p12/` | Mastery/replay and scholarly source curation |
| A10 | `research_v3/eval/`, `scripts/`, `manuscripts/`, CI | Statistics/release engineering and independent reproducibility |

## Ownership collisions
Each agent works in a distinct short-lived branch `research-v3/aXX/WY-...`; PRs target integration branch `research-v3/integration`. Changes to shared contract owned by A01 use schema-proposal issue and a signed PR. Dataset interfaces owned by A02; evaluation protocols by A10. **Never run simultaneous writes to the same file.** Cross-agent consumers use pinned artifact version and hash.

## Wave schedule: do not run all 14 independent primary analyses at once
**W0 — Source lock/read-first:** A01/02/10 verify baseline and gold protections; A03–09 review literature and submit study prereg/novelty challenges. Required: G00/01, baseline environment, 14 signed RQs and overlap matrix.

**W1 — External data & shared contracts:** A02 licenses sources and safe adapters; A01 schemas/ethics; A10 split/metrics/CI. Remaining agents write unit tests, not headline performance results.

**W2 — Strong baselines:** A03/A04/A05/A06/A07/A08/A09 each reproduce at least one serious comparable baseline; A10 verifies each source. Stop if method has no honest comparator.

**W3 — Proposed models / algorithms:** prioritized P01/P02/P03/P05 and pedagogical P10/P11 first. P04/P08 remain conditional. A10 runs gate tests; other P projects begin only when external data fields confirmed.

**W4 — Stress/robustness:** LN-06/07/09 partial mechanisms, cross-platform shifts, counterpart errors, annotation agreement, fair budgets, pseudoreplication guard.

**W5 — Evidence and manuscripts:** manuscript writing builds only after run manifests and primary table IDs exist; literature, discussion and protocol writing can occur earlier. Human raters and ethics reviews are never auto-approved.

**W6 — Independent review:** rotate validation A03↔A07, A04↔A08, A05↔A09, A06↔A10, A01↔A02; owners cannot self-sign own primary metrics. Re-run from clean branch; preserve negative reports and decide merge/drop on conditional papers.

**W7 — Release:** freeze V3 provenance, assemble artifact pack, verify venue conditions for 2027, coauthor/ethics signoff; open PR to main only after all required software tests pass.

## Parallel performance
Parallelize independent paper engines only AFTER W1 contracts freeze. Use resource semaphore (GPU slots, memory and API budget) rather than assuming ten simultaneous model trainings are affordable. Ensure outputs are isolated by SHA and job ID.
