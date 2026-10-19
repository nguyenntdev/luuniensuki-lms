---
name: api-contract
description: Use when modifying API endpoints, schemas, or routes. Covers OpenAPI snapshot pinning, route inventory updates, cross-backend contract tests, and the error envelope standard.
---

# API Contract Management

## OpenAPI Snapshot

`tests/backend/test_openapi_snapshot.py` locks the FastAPI contract byte-for-byte against `tests/backend/fixtures/openapi_snapshot.json`.

- Any endpoint, schema, or response change will break this test.
- To deliberately update after a reviewed contract change:
  ```bash
  REGENERATE_OPENAPI_SNAPSHOT=1 pytest tests/backend/test_openapi_snapshot.py
  ```
- **Never** regenerate as a side effect of a refactor. The snapshot update must be an explicit, reviewed decision.

## Route Inventory

When adding, removing, or modifying endpoints:

```bash
python scripts/dev/generate_route_inventory.py
./scripts/ci/lint-inventory-drift.sh   # verify freshness
```

## Cross-Backend Contract

`tests/backend/test_cross_backend_contract.py` validates JWT acceptance and token compatibility between the Python (FastAPI) and Rust (Axum) backends.

Run after any auth-related changes:
```bash
pytest tests/backend/test_cross_backend_contract.py -v
```

## Error Envelope Standard

Every API error response **must** follow this shape:
```json
{"error": {"code": "ERROR_CODE", "message": "Human readable message", "details": {}}}
```

Validated by `tests/backend/test_validation_error_envelope.py`.

## Frontend API Types

After any contract change, regenerate the frontend TypeScript types:
```bash
cd frontend
npm run gen:api   # regenerates src/types/api.ts from OpenAPI schema
```

## Checklist for endpoint changes

1. Make your changes in `backend/routers/` and `backend/apischemas/`
2. Run `pytest tests/backend/ -v` to catch snapshot/contract breaks
3. If intentional contract change: regenerate snapshot (see above)
4. Update route inventory: `python scripts/dev/generate_route_inventory.py`
5. Regenerate frontend types: `cd frontend && npm run gen:api`
6. If touching Rust routes too: run the full rust-preflight checklist
