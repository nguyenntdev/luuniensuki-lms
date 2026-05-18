# 07_DB_Migrations_Alembic.md

## Goal

Replace ad-hoc `Base.metadata.create_all()` schema creation with **Alembic migrations**, so production deployments are safe, repeatable, and auditable.

## Current State

- Schema is created in `backend/seed.py` using `Base.metadata.create_all(engine)`.
- No migration history exists.

## Target State

- `alembic` is configured and committed.
- Schema changes are applied via:
  - `alembic revision --autogenerate`
  - `alembic upgrade head`
- Production deploy runs migrations before serving traffic.

## Proposed Layout

```
alembic.ini
migrations/
  env.py
  script.py.mako
  versions/
    0001_initial_schema.py
    0002_add_indexes_or_constraints.py
    ...
```

## Key Decisions

1. **Where to run migrations**
   - Recommended: a one-off job during deploy:
     - `docker compose run --rm api alembic upgrade head`
2. **Seed script behavior**
   - Dev: allow `create_all()` if no migrations yet (temporary)
   - Prod: do **not** create schema; assume migrations ran

## Tasks (Ticket-Sized)

- [ ] **DB-MIG-01**: Add Alembic dependency to `backend/requirements.txt`
- [ ] **DB-MIG-02**: Initialize Alembic (`alembic init migrations`)
- [ ] **DB-MIG-03**: Configure `migrations/env.py`:
  - import `Base` from `backend.models`
  - set `target_metadata = Base.metadata`
  - read `DATABASE_URL` env var
- [ ] **DB-MIG-04**: Generate initial migration:
  - `alembic revision --autogenerate -m "initial schema"`
  - review enums/constraints/indexes carefully
- [ ] **DB-MIG-05**: Update deployment flow:
  - add a step in `setup.sh` and `docs/implementation/07_Deployment_Guide.md`:
    - run `alembic upgrade head` before API start or right after containers are up
- [ ] **DB-MIG-06**: Update seed:
  - remove `create_all()` for production path
  - keep seed idempotent (upserts)

## Definition of Done

- Fresh DB + `alembic upgrade head` produces full schema.
- Upgrading from previous version works without data loss for additive changes.
- Production deploy script runs migrations automatically.

