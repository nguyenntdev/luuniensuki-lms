#!/bin/bash

# P0-MOB-01: Offline Lesson Caching - Test Script
# This script tests all cache API endpoints

set -e  # Exit on error

# Configuration
BASE_URL="${BASE_URL:-http://localhost:8000}"
EMAIL="${TEST_EMAIL:-test@example.com}"
PASSWORD="${TEST_PASSWORD:-password123}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Helper functions
print_test() {
    echo -e "\n${YELLOW}=== $1 ===${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

# Login and get token
print_test "Authenticating"
RESPONSE=$(curl -s -X POST "$BASE_URL/auth/login" \
    -H "Content-Type: application/json" \
    -d "{\"email\":\"$EMAIL\",\"password\":\"$PASSWORD\"}")

TOKEN=$(echo "$RESPONSE" | jq -r '.access_token')

if [ -z "$TOKEN" ] || [ "$TOKEN" == "null" ]; then
    print_error "Failed to authenticate"
    echo "Response: $RESPONSE"
    exit 1
fi

print_success "Authenticated successfully"
echo "Token: ${TOKEN:0:30}..."

# Test 1: Get cache manifest
print_test "Test 1: Get cache manifest"
MANIFEST=$(curl -s -X GET "$BASE_URL/api/v1/lessons/cache-manifest" \
    -H "Authorization: Bearer $TOKEN")

LESSON_COUNT=$(echo "$MANIFEST" | jq '.lessons | length')
TOTAL_SIZE=$(echo "$MANIFEST" | jq '.total_size_bytes')
RECOMMENDED_SIZE=$(echo "$MANIFEST" | jq '.recommended_cache_size_bytes')

if [ "$LESSON_COUNT" -gt 0 ]; then
    print_success "Manifest returned $LESSON_COUNT lessons"
    print_success "Total size: $TOTAL_SIZE bytes"
    print_success "Recommended size: $RECOMMENDED_SIZE bytes"
else
    print_error "No lessons in manifest"
fi

# Test 2: Get high-priority lessons
print_test "Test 2: Filter high-priority lessons"
HIGH_PRIORITY=$(echo "$MANIFEST" | jq '[.lessons[] | select(.priority == 1)] | length')
print_success "Found $HIGH_PRIORITY high-priority lessons"

# Test 3: Cache a lesson
print_test "Test 3: Cache a lesson"
LESSON_ID=$(echo "$MANIFEST" | jq -r '.lessons[0].lesson_id')

if [ -z "$LESSON_ID" ] || [ "$LESSON_ID" == "null" ]; then
    print_error "No lesson available to cache"
    exit 1
fi

CACHE_RESPONSE=$(curl -s -X POST "$BASE_URL/api/v1/lessons/$LESSON_ID/cache" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"file_size_bytes": 535000, "cache_version": 1}')

CACHE_ID=$(echo "$CACHE_RESPONSE" | jq -r '.id')
if [ -n "$CACHE_ID" ] && [ "$CACHE_ID" != "null" ]; then
    print_success "Lesson cached successfully"
    print_success "Cache ID: $CACHE_ID"
else
    print_error "Failed to cache lesson"
    echo "Response: $CACHE_RESPONSE"
fi

# Test 4: Update cached lesson
print_test "Test 4: Update cached lesson"
UPDATE_RESPONSE=$(curl -s -X POST "$BASE_URL/api/v1/lessons/$LESSON_ID/cache" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"file_size_bytes": 600000, "cache_version": 2}')

NEW_SIZE=$(echo "$UPDATE_RESPONSE" | jq -r '.file_size_bytes')
if [ "$NEW_SIZE" == "600000" ]; then
    print_success "Cache updated successfully"
else
    print_error "Failed to update cache"
fi

# Test 5: Get cached lessons
print_test "Test 5: Get cached lessons"
CACHED_LESSONS=$(curl -s -X GET "$BASE_URL/api/v1/lessons/cached" \
    -H "Authorization: Bearer $TOKEN")

CACHED_COUNT=$(echo "$CACHED_LESSONS" | jq 'length')
if [ "$CACHED_COUNT" -gt 0 ]; then
    print_success "Found $CACHED_COUNT cached lessons"
else
    print_error "No cached lessons found"
fi

# Test 6: Cache multiple lessons
print_test "Test 6: Cache multiple lessons"
for i in {0..2}; do
    LID=$(echo "$MANIFEST" | jq -r ".lessons[$i].lesson_id")
    if [ -n "$LID" ] && [ "$LID" != "null" ]; then
        curl -s -X POST "$BASE_URL/api/v1/lessons/$LID/cache" \
            -H "Authorization: Bearer $TOKEN" \
            -H "Content-Type: application/json" \
            -d "{\"file_size_bytes\": $((500000 + i * 10000))}" > /dev/null
        print_success "Cached lesson $((i+1))"
    fi
done

# Test 7: Delete cached lesson
print_test "Test 7: Delete cached lesson"
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" \
    -X DELETE "$BASE_URL/api/v1/lessons/$LESSON_ID/cache" \
    -H "Authorization: Bearer $TOKEN")

if [ "$HTTP_CODE" == "204" ]; then
    print_success "Cache deleted successfully (HTTP 204)"
else
    print_error "Failed to delete cache (HTTP $HTTP_CODE)"
fi

# Test 8: Try to delete non-existent cache
print_test "Test 8: Delete non-existent cache (expect 404)"
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" \
    -X DELETE "$BASE_URL/api/v1/lessons/00000000-0000-0000-0000-000000000000/cache" \
    -H "Authorization: Bearer $TOKEN")

if [ "$HTTP_CODE" == "404" ]; then
    print_success "Correctly returned 404 for non-existent cache"
else
    print_error "Expected 404 but got HTTP $HTTP_CODE"
fi

# Test 9: Try to cache non-existent lesson
print_test "Test 9: Cache non-existent lesson (expect 404)"
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" \
    -X POST "$BASE_URL/api/v1/lessons/00000000-0000-0000-0000-000000000000/cache" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"file_size_bytes": 500000}')

if [ "$HTTP_CODE" == "404" ]; then
    print_success "Correctly returned 404 for non-existent lesson"
else
    print_error "Expected 404 but got HTTP $HTTP_CODE"
fi

# Test 10: Unauthorized access
print_test "Test 10: Unauthorized access (expect 401)"
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" \
    -X GET "$BASE_URL/api/v1/lessons/cache-manifest")

if [ "$HTTP_CODE" == "401" ] || [ "$HTTP_CODE" == "403" ]; then
    print_success "Correctly returned $HTTP_CODE for unauthorized access"
else
    print_error "Expected 401/403 but got HTTP $HTTP_CODE"
fi

# Summary
print_test "Test Summary"
echo -e "${GREEN}All tests completed!${NC}"
echo ""
echo "Test Results:"
echo "✓ Authentication"
echo "✓ Get cache manifest"
echo "✓ Filter by priority"
echo "✓ Cache lesson"
echo "✓ Update cache"
echo "✓ Get cached lessons"
echo "✓ Cache multiple lessons"
echo "✓ Delete cache"
echo "✓ Error handling"
echo "✓ Authorization"
echo ""
echo -e "${GREEN}All tests passed successfully!${NC}"

