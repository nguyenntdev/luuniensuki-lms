# 00_Index.md — Implementation Plans & Backlog

This folder turns the high-level specs into **actionable, ticket-sized tasks**.

## Source of Truth (Specs)

- Requirements: `docs/specs/PHASE1_Requirements_Analysis.md`
- Technical spec: `docs/specs/PHASE2_Technical_Specifications.md`
- Architecture: `docs/architecture/01_Architecture_Spec.md`
- Seed data: `docs/architecture/02_Content_Seed.md`
- Current implementation notes:
  - `docs/implementation/03_Backend_Implementation.md`
  - `docs/implementation/04_Frontend_3D_Logic.md`
  - `docs/implementation/06_Auth_System.md`
  - `docs/implementation/07_Deployment_Guide.md`

## Plans (Start Here)

0. Roadmap: `docs/plan/00_Roadmap.md`
1. Backend API backlog: `docs/plan/01_Backend_API_Backlog.md`
2. Quiz system: `docs/plan/02_Quiz_System.md`
3. Gamification (badges/streak/leaderboard): `docs/plan/03_Gamification.md`
4. Frontend pages/components roadmap: `docs/plan/04_Frontend_Roadmap.md`
5. 3D assets + integration pipeline: `docs/plan/05_3D_Assets_Integration.md`
6. Seed/data quality upgrades: `docs/plan/06_Data_and_Seeding.md`
7. Alembic migrations: `docs/plan/07_DB_Migrations_Alembic.md`
8. Testing strategy: `docs/plan/08_Testing_and_QA.md`
9. CI/CD: `docs/plan/09_CICD.md`
10. Observability: `docs/plan/10_Observability.md`
11. Admin panel & admin APIs: `docs/plan/11_Admin_Panel.md`
12. API docs + dev setup: `docs/plan/12_API_Docs_and_Dev_Setup.md`
13. Detailed execution plan: `docs/plan/13_Execution_Plan_Detailed.md`
14. Phase 1 checklist (core loop + certificates): `docs/plan/20_Phase1_Checklist.md`
15. Phase 2 checklist (curriculum + quests): `docs/plan/21_Phase2_Checklist.md`
16. Phase 3 checklist (admin/teacher + classes): `docs/plan/22_Phase3_Checklist.md`
17. Phase 4 checklist (AI recommendations): `docs/plan/23_Phase4_Checklist.md`

## Definitions

### Ticket Size

One task should be finishable in **0.5–1 day** (or split again).

### “Done” for a Backend Ticket

- Endpoint implemented + OpenAPI visible
- DB transactions safe + idempotent where needed
- Auth protected when needed
- Unit tests added (happy + 2–3 negative cases)
- Production docker build works

### “Done” for a Frontend Ticket

- Page/component implemented
- Loading + error states handled
- Works in production build (`next build`)
- Basic e2e smoke checks (manual + script)
