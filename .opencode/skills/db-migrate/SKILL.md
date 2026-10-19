---
name: db-migrate
description: Use when creating or modifying Alembic database migrations. Covers migration safety rules, the correct migration directory, additive-only constraints, and how to test migrations locally.
---

# Database Migration Workflow

## Key facts

- Alembic config: `alembic.ini` at repo root, `script_location = migrations`.
- Real migrations directory: `migrations/versions/`. The root-level `versions/` is stale — never use it.
- Models are defined in `backend/models.py`.

## Creating a migration

```bash
alembic revision --autogenerate -m "short_description_of_change"
alembic upgrade head   # apply locally
```

## Safety rules (enforced by `scripts/ci/lint-migration-safety.sh`)

Migrations **must be purely additive**. Allowed operations:
- `CREATE TABLE`
- `CREATE INDEX`
- `ADD COLUMN`

Blocked operations (will fail the lint):
- `DROP TABLE`, `DROP COLUMN`
- `ALTER TYPE`, `RENAME`
- Any destructive schema change

If you need a destructive change, discuss with the team first — it requires a multi-step migration plan (add new -> migrate data -> drop old).

## Testing migrations

```bash
# Against local test DB
DATABASE_URL="postgresql+psycopg://postgres:postgres@localhost:5432/luuniensuki_test" alembic upgrade head

# In Docker
docker compose exec api alembic upgrade head
```

## After creating a migration

1. Run `alembic upgrade head` to verify it applies cleanly
2. Run `./scripts/ci/lint-migration-safety.sh` to verify no destructive ops
3. Run `./scripts/ci/lint-ledger-sync.sh` to verify route-modes.toml parity
4. Run the test suite to verify nothing broke: `pytest tests/backend/ -v`
