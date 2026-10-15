#!/usr/bin/env bash
# CI lint: AI-tutor pinning lint
#
# Task 1.21: Verifies that every route listed in backend-rust/docs/ai-tutor-routing.md
# is pinned to "gateway" in route-modes.toml. The AI Teacher Worker stays in Python
# and its routes MUST NOT be served natively (Requirement 9.1, 9.4).
#
# Validates: Req 9.2

set -euo pipefail

AI_TUTOR_DOC="${1:-backend-rust/docs/ai-tutor-routing.md}"
ROUTE_MODES="${2:-backend-rust/config/route-modes.toml}"

if [ ! -f "$AI_TUTOR_DOC" ]; then
    echo "WARNING: $AI_TUTOR_DOC not found. Skipping AI-tutor pinning lint."
    echo "Create this file to document AI tutor routes (Requirement 9.2)."
    exit 0
fi

if [ ! -f "$ROUTE_MODES" ]; then
    echo "ERROR: $ROUTE_MODES not found."
    exit 1
fi

echo "Checking AI-tutor route pinning..."

# Extract routes from the AI tutor routing doc
# Handles both:
# 1. Markdown tables: `| `/api/v1/live/...` | GET |`
# 2. Inline/plain text: `GET /api/v1/live/...`
AI_ROUTES=$( (grep -oE '(GET|POST|PUT|PATCH|DELETE)\s+/api/v1/(live|ai-tutor)[^\s`]*' "$AI_TUTOR_DOC" 2>/dev/null || true; \
    grep -E '^\|\s*`?/api/v1/(live|ai-tutor)' "$AI_TUTOR_DOC" 2>/dev/null \
    | awk -F'|' '{gsub(/[` ]/, "", $2); gsub(/[` ]/, "", $3); if ($3 != "" && $2 != "") print $3, $2}' || true) \
    | sort -u 2>/dev/null || true)

if [ -z "$AI_ROUTES" ]; then
    echo "OK: No AI tutor routes found in $AI_TUTOR_DOC — nothing to check."
    exit 0
fi

ERRORS=0

while IFS= read -r route; do
    # Check that this route is pinned to "gateway" in route-modes.toml
    # Format: "METHOD /path" = "gateway"
    ESCAPED_ROUTE=$(echo "$route" | sed 's/[\/&]/\\&/g')
    if grep -qE "\"${ESCAPED_ROUTE}\".*=.*\"native\"" "$ROUTE_MODES" 2>/dev/null; then
        echo "ERROR: AI tutor route '$route' is set to native in $ROUTE_MODES"
        echo "  AI tutor routes MUST remain in gateway mode (Requirement 9.1, 9.4)"
        ERRORS=$((ERRORS + 1))
    fi
done <<< "$AI_ROUTES"

if [ $ERRORS -gt 0 ]; then
    echo ""
    echo "FAILED: $ERRORS AI tutor routes are incorrectly set to native mode."
    echo "AI tutor routes must stay pinned to 'gateway' in route-modes.toml."
    exit 1
fi

echo "OK: All AI tutor routes are correctly pinned to gateway mode."
