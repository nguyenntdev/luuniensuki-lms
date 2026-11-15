# Target architecture, interfaces and source boundaries

## New isolated tree (create during implementation)
```
research_v3/
  README.md
  config/{papers,compute,split_protocols}/
  contracts/{dataset_v3,experiment_v3,model_card,evidence_card}.py
  datasets/{registry.yaml,fetchers/,adapters/,sanitized/,datasheets/}
  annotations/{tasks/,schemas/,agreements/,adjudication/}
  methods/{p01,...,p14}/
  baselines/{registry.yaml,upstream/,adapters/,verification/}
  eval/{splitters,metrics,statistics,calibration,robustness,privacy}/
  experiments/{P01,...,P14}/{pre_registration.yaml,run_matrix.yaml,splits.yaml}/
  scripts/{audit_repo,fetch_data,verify_licenses,materialize,train,evaluate,aggregate,freeze,render}.py
  manuscripts/{P01,...,P14}/{main.tex,figures/,tables/,supplement.tex}/
  governance/{consent_index,ethics,claims,overlap,audit_log}/
tests/research_v3/{contracts,data,method,baseline,evaluation,integration,scientific,privacy}/
research_artifacts_v3/{runs,release,figures,manifests}/  # never checked in if privacy restricted
```

## Immutable contract for all external data
```
DatasetCard { dataset_id, provider, source_url, doi, version, retrieved_at,
  license_text_sha256, allowed_uses, redistribution_policy, original_sha256,
  transformed_sha256, sample_count, schema_version, consent_basis,
  units, group_keys, time_key, leakage_audit, source_attribution,
  status: APPROVED|BLOCKED|RESTRICTED }
ExperimentCard { paper_id, rq_id, train_dataset_ids, holdout_dataset_ids,
  method_commit_sha, method_hash, baseline_version, split_hash,
  feature_cutoff, prereg_sha256, hyperparameter_budget,
  seed, hardware, wall_time, dependency_lock_sha256, output_path,
  protocol_deviations, status }
EvidenceCard { paper_id, claim_id, source_type, source_sha256, code_sha,
  experiment_ids, analysis_script, table_cell_ids, denominator, CI,
  comparison_family, reviewer_signoffs, allowed_wording, limitations }
```
Add canonical-json validation and schema-migration tests. Each record is append-only after freeze; no silent overwrite.

## Mandatory runner lifecycle
1. `audit_repo` reads V1/V2 read-only and enumerates real source paths.
2. `fetch_data --manifest ...` verifies source/terms, writes immutable raw hashes, never redistributes restricted files.
3. `materialize --paper` creates cleaned external-ready inputs and separate sealed labels with stable IDs.
4. `validate_splits --paper` checks learner/course/skill/time separation, duplicates, label leak, train/test contamination.
5. `train --method` enforces matched optimization/hardware budgets; stores full config and checkpoint provenance.
6. `evaluate --frozen` runs all baselines/ablations, logs negatives, sign-off; independent statistician script aggregates.
7. `render --paper` builds tables/figures from numeric artifacts ONLY; no pasted constants.
8. `claim_audit` parses manuscript claims against evidence IDs, disallows unmatched adjectives like 'best', 'causally improves'.
9. `freeze --all` records SHA-256s and legal/ethics approvals; staged artifacts uploaded separately if necessary.

## Production separation
- Reuse verified `research_v2/contracts/` patterns, not raw production learning logs.
- Adapters are pure functions, side-effect-free for original LMS data. Feature flags when integrating any new experiment into `backend/`, `backend-rust/`, `frontend/`.
- Privacy: deidentify, encrypt, restrict source access; no private child data in Git history, PR, ML model artifacts or remote logging.
- Service tests and research outcomes stay separate; software correctness never automatically establishes pedagogy.
- Data access boundaries: training code cannot import gold/evaluator/annotations/test targets, including indirect hashed or nested keys.

## Reliability rules
- Optimizer fallback state must report bound/error (optimal, bound-proven, heuristic, timeout), no invented global optimum.
- Deterministic policies run one scored seed + byte-for-byte reproducibility check; stochastic methods need independent model fits at e.g. seeds 11/23/37/53/71, not metadata relabeling.
- Any nonzero failure propagates to run failure and cannot be converted to SKIP with success status.
- Benchmark leaderboard is experimental; never score the same freeze set during hyperparameter search.
