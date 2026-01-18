#!/bin/bash

# P1-NOTIFY-02: Push Notification API Testing Script

BASE_URL="${BASE_URL:-http://localhost:8000}"

echo "==================================================================="
echo "P1-NOTIFY-02: Push Notification Backend Testing"
echo "==================================================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test counter
TESTS_PASSED=0
TESTS_FAILED=0

# Helper function to test endpoint
test_endpoint() {
    local name="$1"
    local method="$2"
    local endpoint="$3"
    local data="$4"
    local expected_status="${5:-200}"

    echo -n "Testing: $name... "

    if [ "$method" = "GET" ]; then
        response=$(curl -s -w "\n%{http_code}" -X GET "$BASE_URL$endpoint" \
            -H "Authorization: Bearer $TOKEN" 2>&1)
    else
        response=$(curl -s -w "\n%{http_code}" -X "$method" "$BASE_URL$endpoint" \
            -H "Authorization: Bearer $TOKEN" \
            -H "Content-Type: application/json" \
            -d "$data" 2>&1)
    fi

    status_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | head -n -1)

    if [ "$status_code" = "$expected_status" ]; then
        echo -e "${GREEN}✓ PASSED${NC} (HTTP $status_code)"
        ((TESTS_PASSED++))
        if [ -n "$VERBOSE" ]; then
            echo "$body" | jq '.' 2>/dev/null || echo "$body"
        fi
    else
        echo -e "${RED}✗ FAILED${NC} (Expected $expected_status, got $status_code)"
        echo "$body" | jq '.' 2>/dev/null || echo "$body"
        ((TESTS_FAILED++))
    fi
    echo ""
}

# Step 1: Login as admin
echo "Step 1: Authenticating as admin..."
LOGIN_RESPONSE=$(curl -s -X POST "$BASE_URL/api/v1/auth/login" \
    -H "Content-Type: application/json" \
    -d '{
        "email": "admin@example.com",
        "password": "admin123"
    }')

TOKEN=$(echo "$LOGIN_RESPONSE" | jq -r '.access_token')

if [ "$TOKEN" = "null" ] || [ -z "$TOKEN" ]; then
    echo -e "${RED}Failed to authenticate. Please ensure the server is running and admin user exists.${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Authenticated successfully${NC}"
echo ""

# Get a test user ID
echo "Step 2: Getting test user ID..."
USERS_RESPONSE=$(curl -s -X GET "$BASE_URL/api/v1/admin/users?limit=1" \
    -H "Authorization: Bearer $TOKEN")
USER_ID=$(echo "$USERS_RESPONSE" | jq -r '.users[0].id // empty')

if [ -z "$USER_ID" ]; then
    echo -e "${YELLOW}Warning: No users found. Some tests may be skipped.${NC}"
else
    echo -e "${GREEN}✓ Found test user: $USER_ID${NC}"
fi
echo ""

# Test 1: Send notification to specific user
if [ -n "$USER_ID" ]; then
    test_endpoint \
        "Send notification to specific user" \
        "POST" \
        "/api/v1/admin/push-notifications/send" \
        '{
            "user_ids": ["'"$USER_ID"'"],
            "title": "Test Notification",
            "body": "This is a test push notification",
            "notification_type": "system",
            "data_payload": {"screen": "home"}
        }' \
        200
else
    echo -e "${YELLOW}Skipping: Send notification (no test user)${NC}"
    echo ""
fi

# Test 2: Broadcast notification
test_endpoint \
    "Broadcast notification to all users" \
    "POST" \
    "/api/v1/admin/push-notifications/broadcast" \
    '{
        "title": "System Announcement",
        "body": "Testing broadcast functionality",
        "notification_type": "system"
    }' \
    200

# Test 3: Broadcast with role filter
test_endpoint \


# Test 4: Schedule notification
if [ -n "$USER_ID" ]; then
    FUTURE_TIME=$(date -u -v+1H +"%Y-%m-%dT%H:%M:%SZ" 2>/dev/null || date -u -d "+1 hour" +"%Y-%m-%dT%H:%M:%SZ")
    test_endpoint \
        "Schedule notification for later" \
        "POST" \
        "/api/v1/admin/push-notifications/send" \
        '{
            "user_ids": ["'"$USER_ID"'"],
            "title": "Scheduled Notification",
            "body": "This notification is scheduled",
            "notification_type": "streak_reminder",
            "scheduled_for": "'"$FUTURE_TIME"'"
        }' \
        200
else
    echo -e "${YELLOW}Skipping: Schedule notification (no test user)${NC}"
    echo ""
fi

# Test 5: List all notifications
test_endpoint \
    "List all notifications" \
    "GET" \
    "/api/v1/admin/push-notifications?limit=10&offset=0" \
    "" \
    200

# Test 6: Filter by user
if [ -n "$USER_ID" ]; then
    test_endpoint \
        "Filter notifications by user" \
        "GET" \
        "/api/v1/admin/push-notifications?user_id=$USER_ID&limit=5" \
        "" \
        200
else
    echo -e "${YELLOW}Skipping: Filter by user (no test user)${NC}"
    echo ""
fi

# Test 7: Filter by status
test_endpoint \
    "Filter notifications by status" \
    "GET" \
    "/api/v1/admin/push-notifications?status=pending&limit=5" \
    "" \
    200

# Test 8: Filter by type
test_endpoint \
    "Filter notifications by type" \
    "GET" \
    "/api/v1/admin/push-notifications?notification_type=system&limit=5" \
    "" \
    200

# Test 9: Get user notification history (as user)
echo -n "Testing: Get user notification history... "
if [ -n "$USER_ID" ]; then
    # Login as regular user (you may need to adjust credentials)
    USER_LOGIN=$(curl -s -X POST "$BASE_URL/api/v1/auth/login" \
        -H "Content-Type: application/json" \
        -d '{
            "email": "user@example.com",
            "password": "user123"
        }')

    USER_TOKEN=$(echo "$USER_LOGIN" | jq -r '.access_token')

    if [ "$USER_TOKEN" != "null" ] && [ -n "$USER_TOKEN" ]; then
        response=$(curl -s -w "\n%{http_code}" \
            -X GET "$BASE_URL/api/v1/notifications/history?limit=10" \
            -H "Authorization: Bearer $USER_TOKEN")

        status_code=$(echo "$response" | tail -n1)

        if [ "$status_code" = "200" ]; then
            echo -e "${GREEN}✓ PASSED${NC} (HTTP $status_code)"
            ((TESTS_PASSED++))
        else
            echo -e "${RED}✗ FAILED${NC} (Expected 200, got $status_code)"
            ((TESTS_FAILED++))
        fi
    else
        echo -e "${YELLOW}SKIPPED (user login failed)${NC}"
    fi
else
    echo -e "${YELLOW}SKIPPED (no test user)${NC}"
fi
echo ""

# Test 10: Invalid notification type (should fail validation)
test_endpoint \
    "Invalid notification type (expect 422)" \
    "POST" \
    "/api/v1/admin/push-notifications/broadcast" \
    '{
        "title": "Test",
        "body": "Test",
        "notification_type": "invalid_type"
    }' \
    422

# Summary
echo "==================================================================="
echo "Test Summary"
echo "==================================================================="
echo -e "Tests Passed: ${GREEN}$TESTS_PASSED${NC}"
echo -e "Tests Failed: ${RED}$TESTS_FAILED${NC}"
echo "Total Tests: $((TESTS_PASSED + TESTS_FAILED))"
echo ""

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "${GREEN}All tests passed! ✓${NC}"
    exit 0
else
    echo -e "${RED}Some tests failed. Please review the output above.${NC}"
    exit 1
fi
