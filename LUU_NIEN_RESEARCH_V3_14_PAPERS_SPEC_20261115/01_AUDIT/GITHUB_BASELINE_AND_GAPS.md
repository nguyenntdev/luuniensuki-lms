# GitHub audit at fixed SHA (read-only connector review)
Source of truth: `https://github.com/nguyenntdev/luuniensuki-lms/tree/6debec211f240375f5b967fe2eac7f6450c3e53c`. **This is a source/CI/artifact audit, not an independent environment rerun of every experiment.**

## Observed evidence
| Evidence | Location | What can be concluded |
|---|---|---|
| Last visible main head | `6debec211f240375f5b967fe2eac7f6450c3e53c` | Main latest in queried 10-branch list; dated 2026-11-15 05:49:57Z |
| V2 research stack | `research_v2/` | 10 task schemas, methods, evaluation runner, sealed-gold, manifests and scripts exist |
| V2 release | `research_artifacts_v2/release/SCIENTIFIC_READINESS.md` | 7 PASS, 3 PARTIAL (LN-06/07/09) on synthetic T3 and T3S |
| Reproduction | `research_v2/REPRODUCE.md` | commands for tests, audit, integrity, full matrix, aggregate, release freeze |
| Dataset manifest | `research_v2/data/manifest.json` | 10 T1 external entries BLOCKED; 10 T2 heritage expert entries BLOCKED; 10 T3 synthetic + LN10 T3S populated |
| Synthetic matrix | `research_artifacts_v2/release/BENCHMARK_APPENDIX.md` | 198 experiment cells; C0/C1 and ablations run; C2 published implementations blocked |
| Tests | `.github/workflows/research-v2.yml` | GitHub Research V2 workflow concluded success at head SHA; commit reports 769 research-v2 and 206 legacy research tests |
| Legacy task register | `research/task_register_executed.csv` | 720 rows, 72 for each LN-01..LN-10; all 720 recorded as DONE. This denotes legacy technical task status, not external scientific validation. |
| Legacy reports | `research_artifacts/release_validation.json` | 50 conditions/36,000 synthetic policy executions described as technically complete, scientific submission explicitly false |
| Manuscripts | `manuscripts_v5/` | 10 LN manuscripts, each with alias file, not P01..P14 portfolio manuscripts |
| Older spec | `LUU_NIEN_V6_MASTER_AND_MODULAR_SPECS_WITH_MOBILE/.../06_RESEARCH/PAPER_TO_CODE_TRACEABILITY.md` | prior product/research crosswalk covers prior manuscripts and product verification |
| G0 audit | `research_v2/reports/G0_repo_audit.json` | observed SHA is previous commit; pinned SHA is much older; dirty worktree snapshot. Regenerate after changes; not proof latest SHA is intrinsically dirty |

## Scientific status by original study
| Study | Existing synthetic-policy result | Major missing evidence |
|---|---|---|
| LN-01 | PASS | external curriculum/activity datasets; expert pedagogy |
| LN-02 | PASS | learner-level predictive KT and cross-platform transfer |
| LN-03 | PASS | real longitudinal temporal KT + independent scheduling evaluation |
| LN-04 | PASS | real LLM baseline, teacher-rated tutoring, real sources |
| LN-05 | PASS | human gamification outcomes, reward attack external scenarios |
| LN-06 | PARTIAL (ties a2/a3) | out-of-template alternatives, meaningful solver comparison |
| LN-07 | PARTIAL (ties a1/a3) | transcript-failure stratum in scored matrix, rights-cleared media annotation |
| LN-08 | PASS | independent rubric/teacher annotation, historical source review |
| LN-09 | PARTIAL (ties a3) | small cohorts n<5 in scored matrix; actual teacher capacity/risk data |
| LN-10 | PASS incl. T3S | observational SRL construct validation and real learner evidence |

## High-priority audit findings
1. V2 synthetic 100% decision accuracy in multiple studies is not evidence of SOTA. Many labels are programmatic rule oracles; C1 is a reimplementation and C2 = BLOCKED.
2. Fixed seeds 11/23/37 yield identical prediction hashes for deterministic methods; not multiple independent stochastic training replicates.
3. P01/P04/P05 need new external KT engines; LN-02/LN-03 only offer decision-policy scaffolding.
4. Some prereg fields differ from `task_registry.py` or native label vocabularies (notably LN-01/LN-09); reconcile endpoint/label mapping BEFORE continuing, without silently relabeling frozen gold.
5. `G0_repo_audit.json` references earlier checkout and old pin. Mark output as historic; create new pinned snapshot on V3 release.
6. Older product docs use assertions like approved IRB/survey; existence of Markdown assertion is not external proof of approval, consent or record-level data. Verify documentary evidence before empirical claims.
7. CI success confirms workflow run, not accuracy of external research or novelty.
8. DO NOT modify historic V2 metrics to manufacture experimental improvement. All V3 results are new artifacts under V3.

## Honest progress conclusion
**Legacy task register: 720/720 marked DONE. Engineering research framework: substantial. Scientific submission readiness for the NEW 14-paper portfolio: not yet demonstrated.** Do not compute a fabricated 'percentage completed' across different study definitions. Progress is tracked per acceptance gate below.
