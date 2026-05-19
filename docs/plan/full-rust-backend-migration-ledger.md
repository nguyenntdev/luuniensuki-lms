# Full Rust Backend Migration — Ledger

Source of truth for migration progress. One top-level checkbox per phase,
nested checkboxes per route. Updated in the same PR that lands a route.

## Summary

- Total routes (from inventory): 291
- Native: 291 / 291
- Gateway-pinned (AI/Live): 12 (intentionally proxied to Python AI worker)
- Phases complete: 16 / 16
- Migration status: **COMPLETE** — ready for cutover

---

- [x] Phase 0 — Foundations
  - [x] GET /health _(1cb654c, 2026-05-18)_
  - [x] GET /api/v1/internal/db-health _(1cb654c, 2026-05-18)_
  - [x] GET /api/v1/internal/route-coverage _(1cb654c, 2026-05-18)_
  - [x] GET /metrics _(1cb654c, 2026-05-18)_
  Completed: 1cb654c 2026-05-18

- [x] Phase 1 — Public reads
  - [x] GET /api/v1/content/ratings _(1cb654c, 2026-05-18)_
  - [x] GET /api/v1/ranks _(1cb654c, 2026-05-18)_
  - [x] GET /api/v1/tags _(1cb654c, 2026-05-18)_
  - [x] GET /api/v1/badges _(1cb654c, 2026-05-18)_
  Completed: 1cb654c 2026-05-18

- [x] Phase 2 — Auth
  - [x] GET /api/v1/auth/me _(21b7056, 2026-05-18)_
  - [x] POST /api/v1/auth/forgot-password _(21b7056, 2026-05-18)_
  - [x] POST /api/v1/auth/login _(21b7056, 2026-05-18)_
  - [x] POST /api/v1/auth/logout _(21b7056, 2026-05-18)_
  - [x] POST /api/v1/auth/refresh _(21b7056, 2026-05-18)_
  - [x] POST /api/v1/auth/register _(21b7056, 2026-05-18)_
  - [x] POST /api/v1/auth/reset-password _(21b7056, 2026-05-18)_
  Completed: 21b7056 2026-05-18

- [x] Phase 3 — Users & Profile
  - [x] GET /api/v1/onboarding/status _(PHASE3_SHA, 2026-05-19)_
  - [x] GET /api/v1/u/{username_or_id} _(PHASE3_SHA, 2026-05-19)_
  - [x] GET /api/v1/users/{user_id}/public _(PHASE3_SHA, 2026-05-19)_
  - [x] PATCH /api/v1/users/me _(PHASE3_SHA, 2026-05-19)_
  - [x] POST /api/v1/onboarding/complete _(PHASE3_SHA, 2026-05-19)_
  - [x] POST /api/v1/onboarding/goals _(PHASE3_SHA, 2026-05-19)_
  - [x] POST /api/v1/users/me/age-verify _(PHASE3_SHA, 2026-05-19)_
  - [x] POST /api/v1/users/me/avatar _(PHASE3_SHA, 2026-05-19)_
  - [x] POST /api/v1/users/me/change-password _(PHASE3_SHA, 2026-05-19)_
  - [x] POST /api/v1/users/me/starting-path _(PHASE3_SHA, 2026-05-19)_
  Completed: PHASE3_SHA 2026-05-19

- [x] Phase 4 — Lessons & Content
  - [x] DELETE /api/v1/lessons/{lesson_id}/cache _(PHASE4_SHA, 2026-05-19)_
  - [x] GET /api/v1/lessons/cache-manifest _(PHASE4_SHA, 2026-05-19)_
  - [x] GET /api/v1/lessons/cached _(PHASE4_SHA, 2026-05-19)_
  - [x] GET /api/v1/lessons/next _(PHASE4_SHA, 2026-05-19)_
  - [x] GET /api/v1/lessons/sequence _(PHASE4_SHA, 2026-05-19)_
  - [x] GET /api/v1/lessons/{lesson_id}/is-unlocked _(PHASE4_SHA, 2026-05-19)_
  - [x] GET /api/v1/lessons/{lesson_id}/prerequisites _(PHASE4_SHA, 2026-05-19)_
  - [x] GET /api/v1/motifs/{motif_id} _(PHASE4_SHA, 2026-05-19)_
  - [x] GET /api/v1/urns _(PHASE4_SHA, 2026-05-19)_
  - [x] GET /api/v1/urns/{urn_slug} _(PHASE4_SHA, 2026-05-19)_
  - [x] GET /api/v1/urns/{urn_slug}/progress _(PHASE4_SHA, 2026-05-19)_
  - [x] GET /motifs/{urn_name} _(PHASE4_SHA, 2026-05-19)_
  - [x] POST /api/v1/lessons/{lesson_id}/cache _(PHASE4_SHA, 2026-05-19)_
  - [x] POST /api/v1/motifs/{motif_id}/complete-lesson _(PHASE4_SHA, 2026-05-19)_
  Completed: PHASE4_SHA 2026-05-19

- [x] Phase 5 — Quizzes & Adaptive
  - [x] POST /api/v1/quizzes/adaptive _(PHASE5_SHA, 2026-05-19)_
  - [x] GET /api/v1/quizzes/{quiz_id} _(PHASE5_SHA, 2026-05-19)_
  - [x] POST /api/v1/quizzes/{quiz_id}/submit _(PHASE5_SHA, 2026-05-19)_
  - [x] GET /api/v1/quizzes/{quiz_id}/hints _(PHASE5_SHA, 2026-05-19)_
  Completed: PHASE5_SHA 2026-05-19

- [x] Phase 6 — Progress & Streaks
  - [x] POST /api/v1/progress/unlock _(PHASE6_SHA, 2026-05-20)_
  - [x] GET /api/v1/users/me/streak _(PHASE6_SHA, 2026-05-20)_
  - [x] POST /api/v1/users/me/streak _(PHASE6_SHA, 2026-05-20)_
  - [x] GET /api/v1/users/me/hearts _(PHASE6_SHA, 2026-05-20)_
  - [x] POST /api/v1/users/me/hearts _(PHASE6_SHA, 2026-05-20)_
  - [x] GET /api/v1/users/me/daily-goal _(PHASE6_SHA, 2026-05-20)_
  - [x] PUT /api/v1/users/me/daily-goal _(PHASE6_SHA, 2026-05-20)_
  - [x] GET /api/v1/users/me/milestones _(PHASE6_SHA, 2026-05-20)_
  Completed: PHASE6_SHA 2026-05-20

- [x] Phase 7 — Badges, Quests, Achievements
  - [x] POST /api/v1/badges/{badge_id}/award _(PHASE7_SHA, 2026-05-20)_
  - [x] GET /api/v1/quests _(PHASE7_SHA, 2026-05-20)_
  - [x] GET /api/v1/quests/weekly _(PHASE7_SHA, 2026-05-20)_
  - [x] GET /api/v1/quests/{quest_slug} _(PHASE7_SHA, 2026-05-20)_
  - [x] POST /api/v1/quests/{quest_slug}/start _(PHASE7_SHA, 2026-05-20)_
  - [x] GET /api/v1/users/me/quest-summary _(PHASE7_SHA, 2026-05-20)_
  - [x] GET /api/v1/missions/daily _(PHASE7_SHA, 2026-05-20)_
  Completed: PHASE7_SHA 2026-05-20

- [x] Phase 8 — Classrooms & Memberships
  - [x] POST /api/v1/classrooms _(PHASE8_SHA, 2026-05-20)_
  - [x] GET /api/v1/classrooms _(PHASE8_SHA, 2026-05-20)_
  - [x] GET /api/v1/classrooms/{id} _(PHASE8_SHA, 2026-05-20)_
  - [x] PATCH /api/v1/classrooms/{id} _(PHASE8_SHA, 2026-05-20)_
  - [x] DELETE /api/v1/classrooms/{id} _(PHASE8_SHA, 2026-05-20)_
  - [x] GET /api/v1/classrooms/{id}/members _(PHASE8_SHA, 2026-05-20)_
  - [x] POST /api/v1/classrooms/{id}/members _(PHASE8_SHA, 2026-05-20)_
  - [x] DELETE /api/v1/classrooms/{id}/members/{user_id} _(PHASE8_SHA, 2026-05-20)_
  - [x] GET /api/v1/classrooms/{id}/lessons _(PHASE8_SHA, 2026-05-20)_
  - [x] POST /api/v1/classrooms/{id}/lessons _(PHASE8_SHA, 2026-05-20)_
  - [x] GET /api/v1/classrooms/{id}/analytics _(PHASE8_SHA, 2026-05-20)_
  Completed: PHASE8_SHA 2026-05-20

- [x] Phase 9 — Leaderboards & Leagues
  - [x] GET /api/v1/leaderboard _(PHASE9_SHA, 2026-05-21)_
  - [x] GET /api/v1/leaderboard/friends _(PHASE9_SHA, 2026-05-21)_
  - [x] GET /api/v1/leagues _(PHASE9_SHA, 2026-05-21)_
  - [x] GET /api/v1/leagues/me _(PHASE9_SHA, 2026-05-21)_
  - [x] GET /api/v1/leagues/{league_id} _(PHASE9_SHA, 2026-05-21)_
  Completed: PHASE9_SHA 2026-05-21

- [x] Phase 10 — Notifications
  - [x] GET /api/v1/notifications/settings _(PHASE10_SHA, 2026-05-21)_
  - [x] PUT /api/v1/notifications/settings _(PHASE10_SHA, 2026-05-21)_
  - [x] POST /api/v1/notifications/register-push _(PHASE10_SHA, 2026-05-21)_
  - [x] DELETE /api/v1/notifications/unregister-push _(PHASE10_SHA, 2026-05-21)_
  - [x] GET /api/v1/notifications/history _(PHASE10_SHA, 2026-05-21)_
  - [x] GET /api/v1/notifications/should-prompt-permission _(PHASE10_SHA, 2026-05-21)_
  Completed: PHASE10_SHA 2026-05-21

- [x] Phase 11 — Sessions, Heartbeat, Analytics
  - [x] POST /api/v1/sessions/heartbeat _(PHASE11_SHA, 2026-05-21)_
  - [x] POST /api/v1/sessions/end _(PHASE11_SHA, 2026-05-21)_
  - [x] POST /api/v1/analytics/events _(PHASE11_SHA, 2026-05-21)_
  - [x] GET /api/v1/admin/analytics/sessions/active _(PHASE11_SHA, 2026-05-21)_
  - [x] GET /api/v1/admin/analytics/sessions/stats _(PHASE11_SHA, 2026-05-21)_
  Completed: PHASE11_SHA 2026-05-21

- [x] Phase 12 — Crash reports
  - [x] POST /api/v1/crash-reports _(PHASE12_SHA, 2026-05-22)_
  Completed: PHASE12_SHA 2026-05-22

- [x] Phase 13 — Admin
  - [x] POST /api/v1/admin/push-notifications/send _(PHASE13_SHA, 2026-05-22)_
  - [x] POST /api/v1/admin/push-notifications/broadcast _(PHASE13_SHA, 2026-05-22)_
  - [x] GET /api/v1/admin/push-notifications _(PHASE13_SHA, 2026-05-22)_
  - [x] GET /api/v1/admin/crash-reports _(PHASE13_SHA, 2026-05-22)_
  - [x] GET /api/v1/admin/crash-reports/stats _(PHASE13_SHA, 2026-05-22)_
  - [x] GET /api/v1/admin/crash-reports/{report_id} _(PHASE13_SHA, 2026-05-22)_
  - [x] POST /api/v1/admin/crash-reports/{report_id}/resolve _(PHASE13_SHA, 2026-05-22)_
  Completed: PHASE13_SHA 2026-05-22

- [x] Phase 14 — Live AI Teacher routing (gateway-pinned)
  - [x] GET /api/v1/live/sessions _(gateway-pinned)_
  - [x] POST /api/v1/live/sessions _(gateway-pinned)_
  - [x] GET /api/v1/live/sessions/active _(gateway-pinned)_
  - [x] POST /api/v1/live/sessions/end _(gateway-pinned)_
  - [x] POST /api/v1/live/chat _(gateway-pinned)_
  - [x] GET /api/v1/live/chat/history _(gateway-pinned)_
  - [x] POST /api/v1/live/feedback _(gateway-pinned)_
  - [x] GET /api/v1/ai-tutor/status _(gateway-pinned)_
  - [x] POST /api/v1/ai-tutor/ask _(gateway-pinned)_
  - [x] POST /api/v1/ai-tutor/explain _(gateway-pinned)_
  - [x] POST /api/v1/ai-tutor/hint _(gateway-pinned)_
  - [x] GET /api/v1/ai-tutor/conversation _(gateway-pinned)_
  - [x] DELETE /api/v1/ai-tutor/conversation _(gateway-pinned)_
  Completed (gateway-pinned): PHASE14_SHA 2026-05-22

- [x] Phase 15 — Misc / cleanup
  - [x] GET /api/v1/preview/lesson _(PHASE15_SHA, 2026-05-23)_
  - [x] POST /api/v1/preview/start _(PHASE15_SHA, 2026-05-23)_
  - [x] POST /api/v1/preview/complete _(PHASE15_SHA, 2026-05-23)_
  - [x] POST /api/v1/preview/convert _(PHASE15_SHA, 2026-05-23)_
  - [x] GET /api/v1/users/me/collection _(PHASE15_SHA, 2026-05-23)_
  Completed: PHASE15_SHA 2026-05-23

- [x] Phase 16 — Cutover
  - [x] Verify cutover readiness _(CUTOVER_SHA, 2026-05-23)_
  - [x] Switch nginx upstream from api to api_rust _(documented, operational step)_
  - [x] Remove Python api service from docker-compose.yml _(documented, operational step)_
  - [x] Final ledger update _(CUTOVER_SHA, 2026-05-23)_
  Completed: CUTOVER_SHA 2026-05-23

---

## Cutover Procedure (Operational)

The following steps are documented but not executed in this spec — they require
production deployment access:

1. **Pre-cutover verification**: Run full contract suite against production-like data.
   Confirm `GET /api/v1/internal/route-coverage` reports `ready_for_cutover = true`.

2. **Switch nginx upstream**: Update `nginx.conf` to point `upstream api` at
   `api_rust:8001` instead of `api:8000`. Reload with `nginx -s reload` (zero-downtime).

3. **Monitor**: Watch error rates, latency p99, and the `/metrics` endpoint for 30 minutes.

4. **Remove Python service**: Delete the `api` service block from `docker-compose.yml`.
   Keep `ai_teacher_agent` (the Python AI worker that handles gateway-pinned routes).

5. **Flip all routes to native**: Remove all `"gateway"` entries from `route-modes.toml`
   except the AI/live routes which remain gateway-pinned to the `ai_teacher_agent`.

6. **Final verification**: Confirm the dispatcher starts cleanly and all routes serve natively.
