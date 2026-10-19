---
description: Run all lint and type checks across the entire monorepo
agent: build
---

Run all lint and type checks for this project. Execute each and report results:

**Python**: no dedicated linter configured (rely on test suite for validation).

**Rust** (from backend-rust/):
```
cd backend-rust && cargo fmt --check
```

**Frontend** (from frontend/):
```
cd frontend && npm run lint:ci && npm run type-check
```

**CI lint scripts** (from repo root — manual, not in CI):
```
./scripts/ci/lint-pinned-deps.sh
./scripts/ci/lint-build-budget.sh
./scripts/ci/lint-inventory-drift.sh
./scripts/ci/lint-ai-tutor-pinning.sh
./scripts/ci/lint-migration-safety.sh
./scripts/ci/lint-ledger-sync.sh
```

Report: which checks passed, which failed, with error details for failures.

$ARGUMENTS
