# V3-G20 — Human venue / license / authorship clearance: **BLOCKED**

> **Status: BLOCKED (human-only). This artifact is intentionally NOT done and
> must never be marked DONE by automation.**

- **Task owner**: corresponding author (human only — per
  `V3_TASK_REGISTER.csv` `V3-G20, ..., human_only=true`).
- **Blocked reason**: no signed documentary evidence exists for any of the
  following, and the automation stack (this repository) cannot generate it:
  1. **Venue clearance** — official CFP/policy verification and any required
     venue approvals for the intended 2027 submissions (independently
     reconfirmed rank/deadline/fit; a doc assertion is not proof).
  2. **License clearance** — signed license captures for the datasets that
     remain BLOCKED in `research_v3/datasets/registry.yaml`
     (assistments, ednet, europeana, hue-heritage-corpus, junyi,
     mathtutorbench, smithsonian-open-access, wikidata-hue-heritage-mini).
  3. **Authorship clearance** — coauthor signoff, authorship/affiliation
     agreement, and overlap-register disclosure signoffs.

## Exit criteria (all human, all documentary)

- A signed venue-policy confirmation filed under `research_v3/governance/`
  (with document SHA-256) for each target venue.
- Signed license records equivalent to the `approval_*.json` schema used by
  `research_v3/scripts/ethics.py`, with hash-matching document files.
- A coauthor signoff sheet listing every paper, its author list, and each
  author's explicit approval.

## Non-negotiable rule

No code agent, CI job, or script may fabricate, simulate, or pre-fill any of
the above. `verify_licenses.py`, `ethics.py` and the release gates will keep
every affected claim BLOCKED until real signed records exist. Any future
status change must cite the signed document paths and their hashes here.
