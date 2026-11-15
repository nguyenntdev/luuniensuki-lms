# Task tracker usage
**Generated tasks:** 318 = 24 global + 14×21 per-paper; all start as TODO because the new V3 was not implemented during this audit. Existing V2 evidence is separately recorded as inherited, never treated as V3 completion.

## State transitions
`TODO` → `IN_PROGRESS` → `CODE_READY` → `EVIDENCE_VERIFIED` → `HUMAN_SIGNOFF` → `DONE`.
`BLOCKED` is not DONE. For P04/P08 add `MERGE_REQUIRED` and `DEFERRED` as legitimate project outcomes. Each change includes reviewer, date, commit, output hash, and verification command; no bulk mark-as-DONE by document assertion.

## Dependency and tests
- Global G00–G09 before any V3 primary external run. Data/rights gate before materialization.
- Paper T01–T05 before model fitting; T07/T08 before claiming superiority; T10 before sealing test.
- T19–T21 require human action and signed evidence; code agent can generate checklists but cannot fabricate completion.
- When a task fails, create a concrete failing test and a minimal repair PR. Preserve failure history and any null result.

- G21–G23 are newly confirmed critical CLI/tier claim integrity tickets.
