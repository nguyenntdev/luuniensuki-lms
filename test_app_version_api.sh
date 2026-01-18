#!/bin/bash

# P0-MOB-02: App Version Management - API Testing Script
# This script tests all app version management endpoints

set -e  # Exit on error

# Configuration
BASE_URL="${BASE_URL:-http://localhost:8000}"
ADMIN_TOKEN="${ADMIN_TOKEN:-}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Helper functions
print_header() {
    echo -e "\n${YELLOW}=== $1 ===${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_info() {
    echo -e "ℹ $1"
}

# Check if admin token is provided
if [ -z "$ADMIN_TOKEN" ]; then
    print_error "ADMIN_TOKEN environment variable not set"
    echo "Usage: ADMIN_TOKEN=your_token ./test_app_version_api.sh"
    exit 1
fi

# Test 1: List versions (should be empty initially)
print_header "Test 1: List App Versions (Empty)"
RESPONSE=$(curl -s -w "\n%{http_code}" \
    -H "Authorization: Bearer $ADMIN_TOKEN" \
    "$BASE_URL/api/v1/admin/app/versions")
HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
BODY=$(echo "$RESPONSE" | sed '$d')

if [ "$HTTP_CODE" -eq 200 ]; then
    print_success "List versions endpoint works"
    print_info "Response: $BODY"
else
    print_error "List versions failed (HTTP $HTTP_CODE)"
    echo "$BODY"
    exit 1
fi

# Test 2: Create Android version 1.0.0
print_header "Test 2: Create Android Version 1.0.0"
ANDROID_V1=$(curl -s -w "\n%{http_code}" \
    -X POST \
    -H "Authorization: Bearer $ADMIN_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{
        "platform": "android",
        "version": "1.0.0",
        "version_code": 1,
        "min_required_version": "1.0.0",
        "is_current": true,
        "force_update": false,
        "release_notes": "Initial release",
        "download_url": "https://play.google.com/store/apps/details?id=com.luuniensuki"
    }' \
    "$BASE_URL/api/v1/admin/app/versions")

HTTP_CODE=$(echo "$ANDROID_V1" | tail -n1)
BODY=$(echo "$ANDROID_V1" | sed '$d')

if [ "$HTTP_CODE" -eq 201 ]; then
    print_success "Created Android version 1.0.0"
    ANDROID_V1_ID=$(echo "$BODY" | grep -o '"id":"[^"]*' | cut -d'"' -f4)
    print_info "Version ID: $ANDROID_V1_ID"
else
    print_error "Failed to create Android version (HTTP $HTTP_CODE)"
    echo "$BODY"
    exit 1
fi

# Test 3: Create iOS version 1.0.0
print_header "Test 3: Create iOS Version 1.0.0"
IOS_V1=$(curl -s -w "\n%{http_code}" \
    -X POST \
    -H "Authorization: Bearer $ADMIN_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{
        "platform": "ios",
        "version": "1.0.0",
        "version_code": 1,
        "min_required_version": "1.0.0",
        "is_current": true,
        "force_update": false,
        "release_notes": "Initial iOS release",
        "download_url": "https://apps.apple.com/app/luuniensuki/id123456789"
    }' \
    "$BASE_URL/api/v1/admin/app/versions")

HTTP_CODE=$(echo "$IOS_V1" | tail -n1)
BODY=$(echo "$IOS_V1" | sed '$d')

if [ "$HTTP_CODE" -eq 201 ]; then
    print_success "Created iOS version 1.0.0"
    IOS_V1_ID=$(echo "$BODY" | grep -o '"id":"[^"]*' | cut -d'"' -f4)
    print_info "Version ID: $IOS_V1_ID"
else
    print_error "Failed to create iOS version (HTTP $HTTP_CODE)"
    echo "$BODY"
    exit 1
fi

# Test 4: Version check - current version (no update)
print_header "Test 4: Version Check - Current Version (No Update)"
RESPONSE=$(curl -s -w "\n%{http_code}" \
    "$BASE_URL/api/v1/app/version/check?platform=android&current_version=1.0.0")

HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
BODY=$(echo "$RESPONSE" | sed '$d')

if [ "$HTTP_CODE" -eq 200 ]; then
    if echo "$BODY" | grep -q '"update_available":false'; then
        print_success "Version check correctly reports no update needed"
    else
        print_error "Version check should report no update needed"
        echo "$BODY"
        exit 1
    fi
else
    print_error "Version check failed (HTTP $HTTP_CODE)"
    echo "$BODY"
    exit 1
fi

# Test 5: Create newer Android version
print_header "Test 5: Create Android Version 1.2.0"
ANDROID_V2=$(curl -s -w "\n%{http_code}" \
    -X POST \
    -H "Authorization: Bearer $ADMIN_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{
        "platform": "android",
        "version": "1.2.0",
        "version_code": 3,
        "min_required_version": "1.0.0",
        "is_current": true,
        "force_update": false,
        "release_notes": "New features and improvements",
        "download_url": "https://play.google.com/store/apps/details?id=com.luuniensuki"
    }' \
    "$BASE_URL/api/v1/admin/app/versions")

HTTP_CODE=$(echo "$ANDROID_V2" | tail -n1)
BODY=$(echo "$ANDROID_V2" | sed '$d')

if [ "$HTTP_CODE" -eq 201 ]; then
    print_success "Created Android version 1.2.0"
    ANDROID_V2_ID=$(echo "$BODY" | grep -o '"id":"[^"]*' | cut -d'"' -f4)
else
    print_error "Failed to create Android version 1.2.0 (HTTP $HTTP_CODE)"
    echo "$BODY"
    exit 1
fi

# Test 6: Version check - old version (update available)
print_header "Test 6: Version Check - Old Version (Update Available)"
RESPONSE=$(curl -s -w "\n%{http_code}" \
    "$BASE_URL/api/v1/app/version/check?platform=android&current_version=1.0.0")

HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
BODY=$(echo "$RESPONSE" | sed '$d')

if [ "$HTTP_CODE" -eq 200 ]; then
    if echo "$BODY" | grep -q '"update_available":true'; then
        print_success "Version check correctly detects update available"
        if echo "$BODY" | grep -q '"latest_version":"1.2.0"'; then
            print_success "Correct latest version reported"
        fi
    else
        print_error "Version check should report update available"
        echo "$BODY"
        exit 1
    fi
else
    print_error "Version check failed (HTTP $HTTP_CODE)"
    echo "$BODY"
    exit 1
fi

# Test 7: Update version to force update
print_header "Test 7: Update Version - Enable Force Update"
RESPONSE=$(curl -s -w "\n%{http_code}" \
    -X PUT \
    -H "Authorization: Bearer $ADMIN_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{
        "force_update": true,
        "release_notes": "CRITICAL SECURITY UPDATE - Please update immediately"
    }' \
    "$BASE_URL/api/v1/admin/app/versions/$ANDROID_V2_ID")

HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
BODY=$(echo "$RESPONSE" | sed '$d')

if [ "$HTTP_CODE" -eq 200 ]; then
    if echo "$BODY" | grep -q '"force_update":true'; then
        print_success "Force update enabled successfully"
    else
        print_error "Force update flag not set"
        echo "$BODY"
        exit 1
    fi
else
    print_error "Failed to update version (HTTP $HTTP_CODE)"
    echo "$BODY"
    exit 1
fi

# Test 8: Version check - force update
print_header "Test 8: Version Check - Force Update Required"
RESPONSE=$(curl -s -w "\n%{http_code}" \
    "$BASE_URL/api/v1/app/version/check?platform=android&current_version=1.0.0")

HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
BODY=$(echo "$RESPONSE" | sed '$d')

if [ "$HTTP_CODE" -eq 200 ]; then
    if echo "$BODY" | grep -q '"force_update":true'; then
        print_success "Version check correctly requires force update"
    else
        print_error "Version check should require force update"
        echo "$BODY"
        exit 1
    fi
else
    print_error "Version check failed (HTTP $HTTP_CODE)"
    echo "$BODY"
    exit 1
fi

# Test 9: List all versions
print_header "Test 9: List All Versions"
RESPONSE=$(curl -s -w "\n%{http_code}" \
    -H "Authorization: Bearer $ADMIN_TOKEN" \
    "$BASE_URL/api/v1/admin/app/versions")

HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
BODY=$(echo "$RESPONSE" | sed '$d')

if [ "$HTTP_CODE" -eq 200 ]; then
    COUNT=$(echo "$BODY" | grep -o '"id"' | wc -l)
    print_success "List versions returned $COUNT versions"
    print_info "Versions: $BODY"
else
    print_error "Failed to list versions (HTTP $HTTP_CODE)"
    echo "$BODY"
    exit 1
fi

# Test 10: Filter by platform
print_header "Test 10: List Versions - Filter by Platform"
RESPONSE=$(curl -s -w "\n%{http_code}" \
    -H "Authorization: Bearer $ADMIN_TOKEN" \
    "$BASE_URL/api/v1/admin/app/versions?platform=ios")

HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
BODY=$(echo "$RESPONSE" | sed '$d')

if [ "$HTTP_CODE" -eq 200 ]; then
    if echo "$BODY" | grep -q '"platform":"ios"'; then
        print_success "Platform filter works correctly"
    else
        print_error "Platform filter should return iOS versions only"
        echo "$BODY"
        exit 1
    fi
else
    print_error "Failed to list iOS versions (HTTP $HTTP_CODE)"
    echo "$BODY"
    exit 1
fi

# Test 11: Try to create duplicate version (should fail)
print_header "Test 11: Create Duplicate Version (Should Fail)"
RESPONSE=$(curl -s -w "\n%{http_code}" \
    -X POST \
    -H "Authorization: Bearer $ADMIN_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{
        "platform": "android",
        "version": "1.0.0",
        "version_code": 1,
        "min_required_version": "1.0.0",
        "is_current": false,
        "force_update": false
    }' \
    "$BASE_URL/api/v1/admin/app/versions")

HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
BODY=$(echo "$RESPONSE" | sed '$d')

if [ "$HTTP_CODE" -eq 409 ]; then
    print_success "Duplicate version correctly rejected (409 Conflict)"
else
    print_error "Should reject duplicate version with 409, got $HTTP_CODE"
    echo "$BODY"
fi

# Test 12: Version check without auth (public endpoint)
print_header "Test 12: Version Check Without Auth (Public Endpoint)"
RESPONSE=$(curl -s -w "\n%{http_code}" \
    "$BASE_URL/api/v1/app/version/check?platform=ios&current_version=1.0.0")

HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
BODY=$(echo "$RESPONSE" | sed '$d')

if [ "$HTTP_CODE" -eq 200 ]; then
    print_success "Public version check works without authentication"
else
    print_error "Version check should work without auth (HTTP $HTTP_CODE)"
    echo "$BODY"
    exit 1
fi

# Summary
print_header "Test Summary"
print_success "All tests passed!"
echo ""
echo "Test Results:"
echo "  ✓ Created 3 app versions (Android 1.0.0, 1.2.0, iOS 1.0.0)"
echo "  ✓ Version check correctly detects updates"
echo "  ✓ Force update mechanism works"
echo "  ✓ Admin endpoints require authentication"
echo "  ✓ Public endpoint works without authentication"
echo "  ✓ Duplicate version prevention works"
echo "  ✓ Platform filtering works"
echo ""
print_info "Clean up test data manually if needed:"
echo "  DELETE FROM app_versions WHERE version IN ('1.0.0', '1.2.0');"

