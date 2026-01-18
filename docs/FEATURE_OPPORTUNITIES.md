# Feature Opportunities and Improvements

## Executive Summary
The strongest product leverage is in activation (<60s to first lesson), habit loops (daily missions + streaks), and adaptive guidance (next lesson, remediation). These align with existing plan phases but should be tightened into production-ready experiences with clear UX feedback and measurable KPIs.

## High-Impact Opportunities (P0)
1) Activation and onboarding
- Goal selection and personalized "first task" flow.
- Immediate lesson start with a single-tap CTA.
- Early success: micro-quiz and XP reward within first 2 minutes.

2) Habit loops
- Daily missions + weekly quests with clear progress UI.
- Streak protection (freeze, reminders) and daily reward chest.
- Lightweight notification schedule tuned to local usage patterns.

3) Content workflow
- Enforce lesson templates (intro, context, symbolism, fun fact).
- Review workflow and content tagging for discoverability.
- Versioning metadata for audit and faster edits.

4) Analytics foundation
- Track activation funnel (visit -> start -> complete -> quiz -> pass).
- D1/D7 retention dashboards per cohort and user role.

## Mid-Term Opportunities (P1)
1) Adaptive learning
- Difficulty ramping based on quiz performance and lesson completion.
- Remediation suggestions when quiz fails.

2) Recommendations
- "Next best lesson" surfaced on dashboard and lesson completion.
- Reason tags like "continue last quest" or "practice missed motifs".

3) AI tutor with citations
- RAG-backed tutor responses with sources from content library.
- Safety guardrails and structured logging.

4) Teacher tools
- Assignment scheduling, gradebook, and class export.

## Differentiators (P2)
1) 3D interactive learning
- Hotspot-based tasks and progress tracking per interaction.
- Micro-challenges tied to motifs in the 3D model.

2) Community and UGC (moderated)
- User annotations per motif/lesson.
- Moderation queue to maintain quality and safety.

3) Growth loops
- Referral incentives tied to learning milestones.

## Suggested KPIs
- Activation: lesson start within 60s, quiz completion < 5 minutes.
- Retention: D1/D7/D30, weekly active streak rate.
- Learning: completion rate, pass rate, average retries per quiz.
- Content: time-to-publish, review turnaround time.

## Risks and Mitigations
- Over-gamification can reduce learning depth: balance rewards with mastery.
- Content bottleneck: invest early in review workflow and tagging.
- Complexity creep: ship in small slices with strict definition of done.
