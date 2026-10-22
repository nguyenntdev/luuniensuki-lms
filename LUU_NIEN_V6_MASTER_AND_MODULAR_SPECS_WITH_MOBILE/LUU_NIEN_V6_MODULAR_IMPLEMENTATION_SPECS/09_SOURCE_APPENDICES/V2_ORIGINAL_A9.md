# V2 original archival technical chapter — A9

> Extracted without rewriting from V2 snapshot documentation, **not verified current code**.

## A9. Điều tra cần thực hiện trên môi trường đầy đủ (copy-paste command runbook)

```bash
# Use a trusted branch checkout with .git and pinned dependencies.
git rev-parse HEAD
git status --short
python -m pip install -r backend/requirements.txt -r backend/requirements-dev.txt
python -m pytest tests/backend tests/unit -q
cd frontend && npm ci && npm run type-check && npm run lint:ci && npm run test && npm run build && npx playwright test
cd ../backend-rust && cargo fmt --check && cargo test && cargo clippy --all-targets -- -D warnings
cd ../mobile && flutter pub get && flutter analyze && flutter test
cd .. && alembic heads --verbose && alembic history --verbose
```

**End of verification inventory.**



---

