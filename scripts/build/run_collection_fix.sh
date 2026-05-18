#!/bin/bash

# Collection Screen DTO Fix - Build Runner Script
# This script will regenerate the freezed and json_serializable code

echo "================================================"
echo "Collection Screen DTO Fix - Running build_runner"
echo "================================================"
echo ""

# Navigate to mobile directory
cd "$(dirname "$0")/mobile"

echo "Current directory: $(pwd)"
echo ""

echo "Step 1: Cleaning previous build artifacts..."
flutter pub run build_runner clean
echo ""

echo "Step 2: Running build_runner to regenerate code..."
flutter pub run build_runner build --delete-conflicting-outputs
echo ""

echo "================================================"
echo "Build complete!"
echo "================================================"
echo ""
echo "Next steps:"
echo "1. Run: cd mobile && flutter run"
echo "2. Navigate to the Collection tab"
echo "3. Verify the screen loads without errors"
echo ""

