# Novelty screening and red-team procedure (NO claims of originality yet)

- Task+label+horizon+data equivalence first; an adjacent domain paper is conceptual prior art, not an automatic directly comparable metric baseline.
- Search 2015–2026 including latest, publisher official pages + cited works + forward citations; store queries, date, search engines, abstracts/fulltext, inclusion/exclusion, code/weight commits and licences.
- Read at least 3 closest prior methods per idea and ask: does an existing method already implement the exact mechanism? Is the claimed gap missing only because a strong baseline was omitted?
- Require `N1 exact prior-work overlap`, `N2 mathematically distinguishable mechanism`, `N3 residual failure after strongest baseline`, `N4 ablation differentiates mechanism`, `N5 disjoint scientific claim versus other Pxx`, `N6 same TASK/metric parity`, `N7 independent external evaluation`.
- If N1 indicates same mechanism => DISALLOW standalone method claim until re-formulated; if N3 absent => HALT NEW MODEL; if N5 collides => MERGE or split estimands BEFORE running.
- Novelty rating is provisional ordinal screening (NOT acceptance probability): **HIGH RISK** = closest works already describe nearly same mechanism; **MEDIUM** = potential novel target/constraint but unverified; **LOWER** = novel artifact/evaluation may be distinguishable, still requires expert review.
- No method is called a new SOTA just from a creative name or composite loss.
