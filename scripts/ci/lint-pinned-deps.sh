#!/usr/bin/env bash
# CI lint: Pinned-deps lint (Property 20 enforcement)
#
# Task 1.21: Scans backend-rust/Cargo.toml for unpinned dependency versions.
# Every direct dependency MUST use an exact version pin (= prefix) for the
# duration of the strangler-fig migration (Requirement 11.4).
#
# Validates: Req 11.4; Property 20

set -euo pipefail

CARGO_TOML="${1:-backend-rust/Cargo.toml}"

if [ ! -f "$CARGO_TOML" ]; then
    echo "ERROR: $CARGO_TOML not found"
    exit 1
fi

echo "Checking pinned dependencies in $CARGO_TOML..."

# Extract only [dependencies] and [dev-dependencies] sections, then check for unpinned versions.
# We use awk to extract the relevant sections and grep for unpinned version strings.

UNPINNED=$(awk '
    /^\[(dependencies|dev-dependencies)\]/ { in_deps=1; next }
    /^\[/ { in_deps=0 }
    in_deps && /version\s*=\s*"[^=]/ { print NR": "$0 }
' "$CARGO_TOML" | grep -v '^\s*#' || true)

if [ -n "$UNPINNED" ]; then
    echo "ERROR: Found unpinned dependency versions in $CARGO_TOML:"
    echo "$UNPINNED"
    echo ""
    echo "All direct dependencies must use exact version pins (e.g., version = \"=1.0.0\")"
    echo "for the duration of the migration (Requirement 11.4)."
    exit 1
fi

# Also check shorthand form in dependency sections: dep = "x.y.z" (without = prefix)
UNPINNED_SHORT=$(awk '
    /^\[(dependencies|dev-dependencies)\]/ { in_deps=1; next }
    /^\[/ { in_deps=0 }
    in_deps && /^[[:space:]]*[a-zA-Z][a-zA-Z0-9_-]*[[:space:]]*=[[:space:]]*"[^={]/ { print NR": "$0 }
' "$CARGO_TOML" | grep -v '^\s*#' || true)

if [ -n "$UNPINNED_SHORT" ]; then
    echo "ERROR: Found unpinned shorthand dependency versions in $CARGO_TOML:"
    echo "$UNPINNED_SHORT"
    echo ""
    echo "All direct dependencies must use exact version pins (e.g., dep = \"=1.0.0\")"
    exit 1
fi

echo "OK: All dependencies are pinned to exact versions."
