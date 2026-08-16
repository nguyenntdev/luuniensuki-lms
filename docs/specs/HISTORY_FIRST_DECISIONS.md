# HISTORY-FIRST DECISION LOG

Material deviations / architectural decisions for the History-First Rebuild. Master spec: `docs/specs/HISTORY_FIRST_MASTER_SPEC.md`.

| ID | Date | Context | Options considered | Decision | Reason | Consequences | Revisit trigger |
|----|------|---------|--------------------|----------|--------|--------------|-----------------|
| DEC-0001 | 2026-08-17 | Local working copy was a stale non-git snapshot | (a) keep snapshot; (b) replace with git clone of nguyenntdev/luuniensuki-lms | Replaced working dir with `git clone` of the canonical repo, restored AGENTS.md + master spec | Spec requires git-based execution; snapshot lacked history/remotes | Working tree now tracks origin/main; spec committed at docs/specs/ | — |