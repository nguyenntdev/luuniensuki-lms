# P14 Accessibility Test Plan (human-evaluation protocol; NOT executed)

Status: **BLOCKED_pending_ethics** — requires P14-T19 (ethics/human annotation approvals, human-only). This document is the exact protocol a human lead must approve before any participant contact. No recruitment, no simulated ratings, no fabricated annotator IDs.

## Participants
- Expert audit arm: N >= 3 accessibility/HCD experts (independent, no coauthor overlap), compensated, pseudonymised IDs.
- Learner arm (optional extension): school-age learners require guardian consent + age-appropriate assent + institutional review BEFORE contact; accommodations documented per participant.

## Design
- Within-objects factorial: each participant audits the same frozen manifest (or a stratified sample) under (a) C1 checklist-only guidance and (b) full UDL+WCAG rubric, order counterbalanced.
- Outcome measures (preregistered): task completion (binary per object task), time-to-complete, SUS, critical-affordance coverage, inter-rater agreement (Krippendorff alpha; weighted kappa where ordinal). Denominators and unit of analysis fixed in preregistration.yaml.

## Procedure
1. Ethics approvals (P14-T19) signed and archived with artifact hashes.
2. Pilot on 2 excluded objects; codebook frozen.
3. Blinded audit sessions; disagreement adjudicated by a third rater with logs preserved.
4. Analysis per research_v3/eval/statistics.py standards (cluster-aware uncertainty on rater groups).

## Fail-closed rules
- No participant data may be collected before approvals exist on file.
- Absence of human data keeps H0 untested; the manuscript must then publish H0 as not rejected and carry no UDL-benefit wording (enforced by claims_guard).
