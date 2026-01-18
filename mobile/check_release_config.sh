#!/bin/bash
# Release Configuration Verification Script
# Run this before building a release to ensure everything is configured correctly

echo "═══════════════════════════════════════════════════════════"
echo "  Luuniensuki LMS - Release Configuration Checker"
echo "═══════════════════════════════════════════════════════════"
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

ERRORS=0
WARNINGS=0

# Function to check file exists
check_file() {
    if [ -f "$1" ]; then
        echo -e "${GREEN}✓${NC} $2"
        return 0
    else
        echo -e "${RED}✗${NC} $2"
        ERRORS=$((ERRORS + 1))
        return 1
    fi
}

# Function to check directory exists
check_dir() {
    if [ -d "$1" ]; then
        echo -e "${GREEN}✓${NC} $2"
        return 0
    else
        echo -e "${RED}✗${NC} $2"
        ERRORS=$((ERRORS + 1))
        return 1
    fi
}

# Check project root
if [ ! -f "pubspec.yaml" ]; then
    echo -e "${RED}Error: This script must be run from the mobile app root directory${NC}"
    exit 1
fi

echo "1. Checking Keystore Configuration..."
echo "───────────────────────────────────────────────────────────"

check_file "android/key.properties" "Key properties file exists"

if [ -f "android/key.properties" ]; then
    KEYSTORE_PATH=$(grep "storeFile=" android/key.properties | cut -d'=' -f2)
    if [ -f "$KEYSTORE_PATH" ]; then
        echo -e "${GREEN}✓${NC} Release keystore exists at: $KEYSTORE_PATH"
    else
        echo -e "${RED}✗${NC} Release keystore NOT FOUND at: $KEYSTORE_PATH"
        ERRORS=$((ERRORS + 1))
    fi
fi

echo ""
echo "2. Checking Build Configuration..."
echo "───────────────────────────────────────────────────────────"

check_file "android/app/build.gradle" "Build.gradle exists"
check_file "android/app/proguard-rules.pro" "ProGuard rules exist"

# Check if minifyEnabled is set
if grep -q "minifyEnabled true" android/app/build.gradle; then
    echo -e "${GREEN}✓${NC} Minification enabled for release"
else
    echo -e "${YELLOW}⚠${NC} Minification not enabled"
    WARNINGS=$((WARNINGS + 1))
fi

# Check if shrinkResources is set
if grep -q "shrinkResources true" android/app/build.gradle; then
    echo -e "${GREEN}✓${NC} Resource shrinking enabled"
else
    echo -e "${YELLOW}⚠${NC} Resource shrinking not enabled"
    WARNINGS=$((WARNINGS + 1))
fi

echo ""
echo "3. Checking Version Configuration..."
echo "───────────────────────────────────────────────────────────"

VERSION=$(grep "^version:" pubspec.yaml | cut -d' ' -f2)
echo -e "${GREEN}✓${NC} App version: $VERSION"

echo ""
echo "4. Checking API Configuration..."
echo "───────────────────────────────────────────────────────────"

check_file "lib/core/constants/api_constants.dart" "API constants file exists"

if [ -f "lib/core/constants/api_constants.dart" ]; then
    API_URL=$(grep "defaultValue:" lib/core/constants/api_constants.dart | grep -o "'https://[^']*'")
    if [[ $API_URL == *"https://lms.histolab.icu"* ]]; then
        echo -e "${GREEN}✓${NC} Production API URL configured: $API_URL"
    else
        echo -e "${YELLOW}⚠${NC} API URL: $API_URL (verify this is correct)"
        WARNINGS=$((WARNINGS + 1))
    fi
fi

echo ""
echo "5. Checking Manifest Configuration..."
echo "───────────────────────────────────────────────────────────"

check_file "android/app/src/main/AndroidManifest.xml" "Main AndroidManifest exists"

# Check for cleartext traffic in main manifest (should NOT exist)
if grep -q "usesCleartextTraffic=\"true\"" android/app/src/main/AndroidManifest.xml; then
    echo -e "${YELLOW}⚠${NC} Cleartext traffic enabled in main manifest (security risk)"
    WARNINGS=$((WARNINGS + 1))
else
    echo -e "${GREEN}✓${NC} HTTPS enforced (no cleartext traffic in main manifest)"
fi

# Check debug manifest
if [ -f "android/app/src/debug/AndroidManifest.xml" ]; then
    if grep -q "usesCleartextTraffic=\"true\"" android/app/src/debug/AndroidManifest.xml; then
        echo -e "${GREEN}✓${NC} Cleartext traffic enabled in debug manifest (OK for development)"
    fi
fi

echo ""
echo "6. Checking for Debug Logs..."
echo "───────────────────────────────────────────────────────────"

PRINT_COUNT=$(grep -r "print(" lib/ --include="*.dart" 2>/dev/null | wc -l | tr -d ' ')
DEBUG_PRINT_COUNT=$(grep -r "debugPrint(" lib/ --include="*.dart" 2>/dev/null | wc -l | tr -d ' ')

if [ "$PRINT_COUNT" -gt 0 ]; then
    echo -e "${YELLOW}⚠${NC} Found $PRINT_COUNT print() statements (will appear in release builds)"
    WARNINGS=$((WARNINGS + 1))
else
    echo -e "${GREEN}✓${NC} No print() statements found"
fi

if [ "$DEBUG_PRINT_COUNT" -gt 0 ]; then
    echo -e "${GREEN}✓${NC} Found $DEBUG_PRINT_COUNT debugPrint() statements (auto-removed in release)"
fi

echo ""
echo "═══════════════════════════════════════════════════════════"
echo "  Summary"
echo "═══════════════════════════════════════════════════════════"

if [ $ERRORS -eq 0 ] && [ $WARNINGS -eq 0 ]; then
    echo -e "${GREEN}✓ All checks passed! Ready for release build.${NC}"
    echo ""
    echo "Build release APK with:"
    echo "  flutter build apk --release"
    echo ""
    echo "Build app bundle with:"
    echo "  flutter build appbundle --release"
    exit 0
elif [ $ERRORS -eq 0 ]; then
    echo -e "${YELLOW}⚠ Passed with $WARNINGS warning(s)${NC}"
    echo "  Review warnings above before releasing."
    exit 0
else
    echo -e "${RED}✗ Failed with $ERRORS error(s) and $WARNINGS warning(s)${NC}"
    echo "  Fix errors above before building release."
    exit 1
fi

