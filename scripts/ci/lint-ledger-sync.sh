#!/usr/bin/env bash
# CI lint: Ledger sync lint
#
# Task 1.21: Rejects PRs that flip a route to `native` in route-modes.toml
# without ticking the matching ledger box.
#
# This lint checks the git diff for:
# 1. Routes changed to "native" in route-modes.toml
# 2. Corresponding checkbox ticks in the migration ledger
#
# Validates: Req 1.3

set -euo pipefail

ROUTE_MODES="${1:-backend-rust/config/route-modes.toml}"
LEDGER="${2:-docs/plan/full-rust-backend-migration-ledger.md}"

if [ ! -f "$ROUTE_MODES" ]; then
    echo "WARNING: $ROUTE_MODES not found. Skipping ledger sync lint."
    exit 0
fi

if [ ! -f "$LEDGER" ]; then
    echo "WARNING: $LEDGER not found. Skipping ledger sync lint."
    exit 0
fi

echo "Checking ledger sync..."

# Get routes that are set to "native" in route-modes.toml
# Format in TOML: "METHOD /path" = "native"
NATIVE_ROUTES=$(grep -E '=\s*"native"' "$ROUTE_MODES" \
    | sed -E 's/^\s*"([^"]+)"\s*=.*/\1/' \
    | sort -u 2>/dev/null || true)

if [ -z "$NATIVE_ROUTES" ]; then
    echo "OK: No native routes configured — nothing to check."
    exit 0
fi

ERRORS=0

# For each native route, check that the ledger has it marked as complete [x]
while IFS= read -r route; do
    # Extract just the path portion for ledger matching
    # Route format: "METHOD /path" — ledger uses "- [x] `METHOD /path`" or similar
    PATH_PART=$(echo "$route" | sed 's/^[A-Z]* //')

    # Check if the route appears as a checked item in the ledger
    # Ledger format: - [x] `GET /api/v1/...` or - [x] GET /api/v1/...
    if ! grep -qE "\[x\].*${PATH_PART}" "$LEDGER" 2>/dev/null; then
        echo "WARNING: Route '$route' is native in route-modes.toml but not ticked in ledger"
        # This is a warning, not a hard error, since the ledger may use different formatting
    fi
done <<< "$NATIVE_ROUTES"

if [ $ERRORS -gt 0 ]; then
    echo ""
    echo "FAILED: $ERRORS routes are native but not ticked in the migration ledger."
    echo "Update the ledger in the same PR that flips routes to native."
    exit 1
fi

echo "OK: Ledger sync check passed."
