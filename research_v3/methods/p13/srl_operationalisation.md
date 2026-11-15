# P13 — SRL proxy operationalisation table (construct_validity: proxy_only)

**Status: CONSTRUCT_VALIDATION_REQUIRED.** OULAD has no SRL instrument. Each
row below maps an observable OULAD clickstream quantity to a Zimmerman SRL
phase as a **behavioural proxy**, with the citation that motivates the mapping
and the explicit threat to its validity. Nothing here amounts to construct-
level SRL evidence — by design.

Zimmerman (2000) phases: **forethought** (task analysis, strategic planning),
**performance** (self-control, self-observation), **self-reflection**
(self-judgement, self-reaction). Winne & Hadwin (1998) model studying as
SRL with equivalent phases (conditions → operations → products → evaluations).
Learning-analytics precedent for click-based proxies: Jovanović et al. (2017);
for low-inference-metric critique: Gašević et al. (2016); for temporal
engagement profiles: Kizilcec et al. (2013, LAK) — "exploring/solidifying/
auditing" engagement patterns derived from video-watching regularity.

| # | Proxy feature | OULAD operationalisation (day 0..60 window) | Zimmerman phase | Citation | construct_validity | Main validity threat |
|---|---------------|----------------------------------------------|-----------------|----------|--------------------|----------------------|
| 1 | `plan_regularity` | CV of daily active-session gaps; regular spacing of study sessions → planning-like regularity | forethought | Kizilcec et al. (2013); Zimmerman (2000) | proxy_only | regularity may reflect course deadlines, not planning |
| 2 | `plan_early_start` | first active day within window (earlier start = forethought-style task analysis) | forethought | Zimmerman (2000) | proxy_only | early clicks can be mandatory orientation, not planning |
| 3 | `plan_consistency_weekend_weekday` | ratio weekend vs weekday activity dispersion (stable routine) | forethought | Winne & Hadwin (1998) | proxy_only | routine ≠ intent; no diary data |
| 4 | `effort_mean_daily_clicks` | mean clicks per active day in window | performance | Gašević et al. (2016) (low-inference caveat) | proxy_only | click volume confounded by content type |
| 5 | `effort_dispersion` | Gini coefficient of clicks across active days (effort distribution over time) | performance | Kizilcec et al. (2013) | proxy_only | cramming vs pacing is also course-structure driven |
| 6 | `effort_diversity` | Shannon entropy over clicks by activity_type (range of learning activities) | performance | Jovanović et al. (2017) | proxy_only | heterogeneity of clicking ≠ strategic variety |
| 7 | `help_seeking_forum_clicks` | forumng clicks (viewing/posting pages not distinguished in OULAD VLE log) | performance (help-seeking) | Zimmerman & Martinez-Pons (1988) help-seeking strategy; Jovanović et al. (2017) forum indicator | proxy_only | OULAD records forum *page loads*, not posts; reading ≠ asking for help |
| 8 | `help_seeking_forum_share` | forumng clicks / total clicks | performance (help-seeking) | Jovanović et al. (2017) | proxy_only | same as #7 |
| 9 | `self_observation_revisits` | share of sites visited on >1 distinct day (returning to same material = monitoring-like) | performance (self-observation) | Winne & Hadwin (1998) | proxy_only | re-reading may reflect difficulty, not monitoring |
| 10 | `reflect_late_activity` | clicks in days 45..60 relative to 0..44 (late-window self-evaluation surge before first TMA deadlines) | self_reflection | Zimmerman (2000); assessment calendar of OULAD TMAs (day 19/54 per assessments.csv) | proxy_only | deadline-driven workload, not reflection |
| 11 | `session_consistency` | std of daily click counts (low = consistent sessions) | performance | Kizilcec et al. (2013) | proxy_only | consistency partially enforced by course pacing |
| 12 | `temporal_order_integrity` | pipeline-invariant: flags rows whose features used shuffled dates (mutation test hook, expected 0 in real data) | (none — audit) | spec A2 ablation | audit_only | n/a |

**What is deliberately NOT claimed:**
- No proxy measures the SRL *construct*; at best each is a low-inference
  behavioural correlate of one phase, with the threats listed.
- No proxy may be renamed, aggregated into an "SRL score", or reported as an
  SRL *level* of a student.
- Forum clicks ≠ help-seeking messages (OULAD studentVle has no post content).
- Nothing here establishes construct-level SRL evidence; the mapping is an
  operational analogy only.

**References:**
- Zimmerman, B. J. (2000). Attaining self-regulation: A social cognitive
  perspective. In *Handbook of Self-Regulation* (pp. 13–39). Academic Press.
- Zimmerman, B. J., & Martinez-Pons, M. (1988). Construct validation of a
  strategy model of student self-regulated learning. *Journal of Educational
  Psychology*, 80(3), 284–290.
- Winne, P. H., & Hadwin, A. F. (1998). Studying as self-regulated learning.
  In *Metacognition in Educational Theory and Practice* (pp. 277–304). Erlbaum.
- Jovanović, J., Gašević, D., Dawson, S., Pardo, A., & Mirriahi, N. (2017).
  Learning analytics to unveil learning strategies: A case study.
  *Journal of Learning Analytics*, 4(1), 42–64.
- Gašević, D., Dawson, S., Rogers, T., & Gasevic, D. (2016). Learning analytics
  should not promote one size fits all. *LAK '16*, 68–78.
- Kizilcec, R. F., Piech, C., & Schneider, E. (2013). Deconstructing
  disengagement: analyzing learner subpopulations in massive open online
  courses. *LAK '13*, 170–179.
- Kuzilek, J., Hlosta, M., & Zdrahal, Z. (2017). Open University Learning
  Analytics Dataset. *Scientific Data*, 4, 170171. doi:10.1038/sdata.2017.171
