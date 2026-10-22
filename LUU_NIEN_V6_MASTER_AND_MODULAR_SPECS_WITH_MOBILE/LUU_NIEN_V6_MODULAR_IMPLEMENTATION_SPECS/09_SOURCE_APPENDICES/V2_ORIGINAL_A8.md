# V2 original archival technical chapter — A8

> Extracted without rewriting from V2 snapshot documentation, **not verified current code**.

## A8. Kết quả các lệnh audit thực tế

```text
Python: 390 files parsed/compiled with `compile(..., mode="exec")` -> 0 syntax errors.
JSON: 83 .json files parsed -> 0 syntax errors.
Data: 9 urn JSON files × 18 = 162 records, unique IDs = 162; all 162 flagged is_ai_generated=true.
Data: directly linked source fields (`sources`, `source_url`, `source_ids`, `bibliography`) found in 0/162 listed seed records.
Data: 162 JPGs under `ban-duc-noi`.
pytest tests/backend/test_rbpc_endpoints.py tests/unit/test_rbpc_ai.py -> import blocked, missing psycopg; exit 4.
Rust/Flutter/front-end full builds NOT run (toolchain/dependency availability limits).
```

