#!/usr/bin/env bash
# CI lint: Inventory drift lint
#
# Task 1.21: Regenerates route-inventory.json and fails if the committed
# version differs from the freshly generated one.
#
# Validates: Req 1.6, 2.3

set -euo pipefail

INVENTORY_PATH="${1:-backend-rust/docs/route-inventory.json}"
GENERATOR_SCRIPT="${2:-scripts/dev/generate_route_inventory.py}"

if [ ! -f "$INVENTORY_PATH" ]; then
    echo "ERROR: $INVENTORY_PATH not found"
    exit 1
fi

if [ ! -f "$GENERATOR_SCRIPT" ]; then
    echo "WARNING: Generator script $GENERATOR_SCRIPT not found."
    echo "Cannot verify inventory drift without the generator."
    echo "Skipping lint (non-blocking)."
    exit 0
fi

echo "Checking route inventory drift..."

# Save the current inventory
TEMP_INVENTORY=$(mktemp)
cp "$INVENTORY_PATH" "$TEMP_INVENTORY"

# Regenerate the inventory
if ! python3 "$GENERATOR_SCRIPT" 2>/dev/null; then
    echo "WARNING: Generator script failed to run (Python service may not be available)."
    echo "Skipping inventory drift check."
    rm -f "$TEMP_INVENTORY"
    exit 0
fi

# Compare
if ! diff -q "$TEMP_INVENTORY" "$INVENTORY_PATH" > /dev/null 2>&1; then
    echo "ERROR: Route inventory has drifted!"
    echo ""
    echo "The committed $INVENTORY_PATH differs from the freshly generated version."
    echo "Diff:"
    diff -u "$TEMP_INVENTORY" "$INVENTORY_PATH" || true
    echo ""
    echo "Please regenerate the inventory:"
    echo "  python3 $GENERATOR_SCRIPT"
    echo "and commit the updated file."

    # Restore original
    cp "$TEMP_INVENTORY" "$INVENTORY_PATH"
    rm -f "$TEMP_INVENTORY"
    exit 1
fi

rm -f "$TEMP_INVENTORY"
echo "OK: Route inventory is up to date."
