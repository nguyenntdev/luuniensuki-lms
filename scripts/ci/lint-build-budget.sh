#!/usr/bin/env bash
# CI lint: Build-budget lint
#
# Task 1.21: Checks that every direct dependency in Cargo.toml has a
# corresponding row in backend-rust/docs/build-budget.md, and vice versa.
#
# Validates: Req 11.2; Property 20

set -euo pipefail

CARGO_TOML="${1:-backend-rust/Cargo.toml}"
BUILD_BUDGET="${2:-backend-rust/docs/build-budget.md}"

if [ ! -f "$CARGO_TOML" ]; then
    echo "ERROR: $CARGO_TOML not found"
    exit 1
fi

if [ ! -f "$BUILD_BUDGET" ]; then
    echo "ERROR: $BUILD_BUDGET not found"
    exit 1
fi

echo "Checking build-budget parity..."

# Extract dependency names from [dependencies] section of Cargo.toml
# Handles both: dep = "version" and dep = { version = "..." }
CARGO_DEPS=$(sed -n '/^\[dependencies\]/,/^\[/p' "$CARGO_TOML" \
    | grep -E '^\s*\w' \
    | grep -v '^\[' \
    | sed -E 's/^\s*([a-zA-Z0-9_-]+)\s*=.*/\1/' \
    | sort -u)

# Extract dependency names from the build-budget.md table
# Table rows start with | dep_name |
BUDGET_DEPS=$(grep -E '^\|\s*[a-z]' "$BUILD_BUDGET" \
    | sed -E 's/^\|\s*([a-zA-Z0-9_-]+)\s*\|.*/\1/' \
    | sort -u)

ERRORS=0

# Check: every Cargo.toml dep has a row in build-budget.md
for dep in $CARGO_DEPS; do
    if ! echo "$BUDGET_DEPS" | grep -qx "$dep"; then
        echo "ERROR: Dependency '$dep' in Cargo.toml has no row in $BUILD_BUDGET"
        ERRORS=$((ERRORS + 1))
    fi
done

# Check: every build-budget.md row has a dep in Cargo.toml
for dep in $BUDGET_DEPS; do
    if ! echo "$CARGO_DEPS" | grep -qx "$dep"; then
        echo "WARNING: '$dep' in $BUILD_BUDGET has no matching dependency in Cargo.toml"
    fi
done

if [ $ERRORS -gt 0 ]; then
    echo ""
    echo "FAILED: $ERRORS dependencies missing from build-budget.md"
    echo "Add a row for each new dependency with its peak RSS measurement."
    exit 1
fi

echo "OK: All Cargo.toml dependencies have build-budget entries."
