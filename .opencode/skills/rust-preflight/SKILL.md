---
name: rust-preflight
description: Use before committing Rust backend changes. Covers the full pre-commit checklist for backend-rust/ including cargo test, fmt, and all 6 manual CI lint scripts that are NOT wired into GitHub Actions.
---

# Rust Backend Pre-Commit Checklist

The Rust gateway (`backend-rust/`) has **no automated CI job**. All verification is manual. Run these before committing any Rust changes.

## Step 1: Format and test

```bash
cd backend-rust
cargo fmt --check
cargo test
```

## Step 2: Run all 6 lint scripts (from repo root)

```bash
./scripts/ci/lint-pinned-deps.sh       # Exact (=) version pins in Cargo.toml
./scripts/ci/lint-build-budget.sh      # Cargo.toml <-> build-budget.md parity
./scripts/ci/lint-inventory-drift.sh   # route-inventory.json freshness
./scripts/ci/lint-ai-tutor-pinning.sh  # AI tutor routes stay pinned to gateway
./scripts/ci/lint-migration-safety.sh  # No destructive SQL ops
./scripts/ci/lint-ledger-sync.sh       # route-modes.toml matches migration ledger
```

## Dependency rules

- Every direct dep in `Cargo.toml` must use exact pin: `=x.y.z`
- Each dep must have peak RSS recorded in `backend-rust/docs/build-budget.md`
- Build is memory-constrained (~3.9 GiB RAM). Dockerfile uses `CARGO_BUILD_JOBS=2`, `CODEGEN_UNITS=1`, `LTO=thin`.

## If you added or changed routes

1. Regenerate route inventory: `python scripts/dev/generate_route_inventory.py`
2. Run `./scripts/ci/lint-inventory-drift.sh` to verify
3. If routes involve `/api/v1/live/*` or `/api/v1/ai-tutor/*`, verify they stay pinned to `"gateway"` mode in `backend-rust/config/route-modes.toml`

## Key files

- Entry point: `backend-rust/src/main.rs`
- Route dispatch: `backend-rust/src/dispatcher.rs` (hot-reloadable route modes)
- Python proxy fallback: `backend-rust/src/gateway.rs`
- Route modes config: `backend-rust/config/route-modes.toml`
- Build budget: `backend-rust/docs/build-budget.md`
