---
description: Run the full test suite across Python backend, Rust, and frontend
agent: build
---

Run the tests for this project. Execute each suite and report results:

**Python backend** (requires running PostgreSQL):
```
DATABASE_URL="postgresql+psycopg://postgres:postgres@localhost:5432/luuniensuki_test" pytest tests/backend/ -v --tb=short
```

**Rust backend** (from backend-rust/):
```
cd backend-rust && cargo test
```

**Frontend** (from frontend/):
```
cd frontend && npm run test
```

Report: which suites passed, which failed, total pass/fail counts. For failures, show the failing test name and error summary.

$ARGUMENTS
