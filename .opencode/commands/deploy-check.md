---
description: Pre-deploy verification checklist — everything CI runs plus what it misses
agent: build
---

Run the full pre-deploy verification checklist. This covers everything GitHub Actions CI runs, plus the manual checks it skips.

Execute in order and stop on first failure:

1. **Python tests** (what CI `backend` job runs):
```
DATABASE_URL="postgresql+psycopg://postgres:postgres@localhost:5432/luuniensuki_test" pytest tests/backend/ -v --tb=short
```

2. **Frontend lint** (what CI `frontend` job runs):
```
cd frontend && npm run lint:ci
```

3. **Frontend build** (what CI `frontend` job runs):
```
cd frontend && npm run build
```

4. **Frontend type-check** (CI SKIPS this — run locally):
```
cd frontend && npm run type-check
```

5. **Rust checks** (CI SKIPS these — no Rust CI job exists):
```
cd backend-rust && cargo fmt --check && cargo test
```

6. **Manual CI lint scripts** (CI SKIPS — all manual):
```
./scripts/ci/lint-pinned-deps.sh
./scripts/ci/lint-build-budget.sh
./scripts/ci/lint-inventory-drift.sh
./scripts/ci/lint-ai-tutor-pinning.sh
./scripts/ci/lint-migration-safety.sh
./scripts/ci/lint-ledger-sync.sh
```

7. **OpenAPI snapshot check**:
```
DATABASE_URL="postgresql+psycopg://postgres:postgres@localhost:5432/luuniensuki_test" pytest tests/backend/test_openapi_snapshot.py -v
```

Report a summary table: step name, pass/fail, duration. For any failures, show the relevant error output.

$ARGUMENTS
