#!/bin/bash

# P0-ACT-03: Push Notifications API Testing Script
# Tests all notification-related endpoints

set -e  # Exit on error

BASE_URL="${BASE_URL:-http://localhost:8000}"
TOKEN="${TOKEN:-}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "========================================="
echo "P0-ACT-03: Notification API Tests"
echo "========================================="
echo "Base URL: $BASE_URL"
echo ""

if [ -z "$TOKEN" ]; then
    echo -e "${RED}ERROR: TOKEN environment variable not set${NC}"
    echo "Usage: TOKEN=your-jwt-token ./test_notifications_api.sh"
    exit 1
fi

# Helper function to make API calls
api_call() {
    local method=$1
    local endpoint=$2
    local data=$3
    
    if [ -n "$data" ]; then
        curl -s -X "$method" "$BASE_URL$endpoint" \
            -H "Authorization: Bearer $TOKEN" \
            -H "Content-Type: application/json" \
            -d "$data"
    else
        curl -s -X "$method" "$BASE_URL$endpoint" \
            -H "Authorization: Bearer $TOKEN"
    fi
}

# Test 1: Check should prompt permission (before any lessons)
echo -e "${YELLOW}Test 1: Check should-prompt-permission${NC}"
RESPONSE=$(api_call GET "/api/v1/notifications/should-prompt-permission")
echo "$RESPONSE" | jq .
echo ""

# Test 2: Get notification settings (creates default if not exists)
echo -e "${YELLOW}Test 2: Get notification settings${NC}"
RESPONSE=$(api_call GET "/api/v1/notifications/settings")
echo "$RESPONSE" | jq .
SETTINGS_ID=$(echo "$RESPONSE" | jq -r '.id')
echo "Settings ID: $SETTINGS_ID"
echo ""

# Test 3: Update notification settings
echo -e "${YELLOW}Test 3: Update notification settings${NC}"
UPDATE_DATA='{
  "streak_reminders": true,
  "daily_mission_reminders": false,
  "weekly_digest": true,
  "marketing_enabled": false,
  "quiet_hours_start": 22,
  "quiet_hours_end": 8
}'
RESPONSE=$(api_call PUT "/api/v1/notifications/settings" "$UPDATE_DATA")
echo "$RESPONSE" | jq .
echo ""

# Test 4: Verify settings were updated
echo -e "${YELLOW}Test 4: Verify settings were updated${NC}"
RESPONSE=$(api_call GET "/api/v1/notifications/settings")
STREAK_REMINDERS=$(echo "$RESPONSE" | jq -r '.streak_reminders')
QUIET_START=$(echo "$RESPONSE" | jq -r '.quiet_hours_start')
QUIET_END=$(echo "$RESPONSE" | jq -r '.quiet_hours_end')

if [ "$STREAK_REMINDERS" == "true" ] && [ "$QUIET_START" == "22" ] && [ "$QUIET_END" == "8" ]; then
    echo -e "${GREEN}✓ Settings updated correctly${NC}"
else
    echo -e "${RED}✗ Settings update failed${NC}"
fi
echo ""

# Test 5: Register push token (iOS)
echo -e "${YELLOW}Test 5: Register push token (iOS)${NC}"
REGISTER_DATA='{
  "token": "test-fcm-token-ios-123456789",
  "platform": "ios"
}'
RESPONSE=$(api_call POST "/api/v1/notifications/register-push" "$REGISTER_DATA")
echo "$RESPONSE" | jq .
SUCCESS=$(echo "$RESPONSE" | jq -r '.success')
if [ "$SUCCESS" == "true" ]; then
    echo -e "${GREEN}✓ Token registered successfully${NC}"
else
    echo -e "${RED}✗ Token registration failed${NC}"
fi
echo ""

# Test 6: Verify token was saved
echo -e "${YELLOW}Test 6: Verify token was saved${NC}"
RESPONSE=$(api_call GET "/api/v1/notifications/settings")
PUSH_TOKEN=$(echo "$RESPONSE" | jq -r '.push_token')
PUSH_PLATFORM=$(echo "$RESPONSE" | jq -r '.push_platform')
PUSH_ENABLED=$(echo "$RESPONSE" | jq -r '.push_enabled')

if [ "$PUSH_TOKEN" == "test-fcm-token-ios-123456789" ] && [ "$PUSH_PLATFORM" == "ios" ] && [ "$PUSH_ENABLED" == "true" ]; then
    echo -e "${GREEN}✓ Token saved correctly${NC}"
else
    echo -e "${RED}✗ Token not saved correctly${NC}"
    echo "Token: $PUSH_TOKEN"
    echo "Platform: $PUSH_PLATFORM"
    echo "Enabled: $PUSH_ENABLED"
fi
echo ""

# Test 7: Check should prompt after token registration
echo -e "${YELLOW}Test 7: Check should-prompt after registration${NC}"
RESPONSE=$(api_call GET "/api/v1/notifications/should-prompt-permission")
SHOULD_PROMPT=$(echo "$RESPONSE" | jq -r '.should_prompt')
if [ "$SHOULD_PROMPT" == "false" ]; then
    echo -e "${GREEN}✓ Should not prompt after registration${NC}"
else
    echo -e "${RED}✗ Still prompting after registration${NC}"
fi
echo "$RESPONSE" | jq .
echo ""

# Test 8: Update token (Android)
echo -e "${YELLOW}Test 8: Update token (Android)${NC}"
UPDATE_TOKEN_DATA='{
  "token": "test-fcm-token-android-987654321",
  "platform": "android"
}'
RESPONSE=$(api_call POST "/api/v1/notifications/register-push" "$UPDATE_TOKEN_DATA")
echo "$RESPONSE" | jq .
echo ""

# Test 9: Verify token update
echo -e "${YELLOW}Test 9: Verify token was updated${NC}"
RESPONSE=$(api_call GET "/api/v1/notifications/settings")
PUSH_TOKEN=$(echo "$RESPONSE" | jq -r '.push_token')
PUSH_PLATFORM=$(echo "$RESPONSE" | jq -r '.push_platform')

if [ "$PUSH_TOKEN" == "test-fcm-token-android-987654321" ] && [ "$PUSH_PLATFORM" == "android" ]; then
    echo -e "${GREEN}✓ Token updated correctly${NC}"
else
    echo -e "${RED}✗ Token update failed${NC}"
fi
echo ""

# Test 10: Unregister push token
echo -e "${YELLOW}Test 10: Unregister push token${NC}"
RESPONSE=$(api_call DELETE "/api/v1/notifications/unregister-push")
echo "$RESPONSE" | jq .
echo ""

# Test 11: Verify token was removed
echo -e "${YELLOW}Test 11: Verify token was removed${NC}"
RESPONSE=$(api_call GET "/api/v1/notifications/settings")
PUSH_TOKEN=$(echo "$RESPONSE" | jq -r '.push_token')
PUSH_PLATFORM=$(echo "$RESPONSE" | jq -r '.push_platform')
PUSH_ENABLED=$(echo "$RESPONSE" | jq -r '.push_enabled')

if [ "$PUSH_TOKEN" == "null" ] && [ "$PUSH_PLATFORM" == "null" ] && [ "$PUSH_ENABLED" == "false" ]; then
    echo -e "${GREEN}✓ Token removed correctly${NC}"
else
    echo -e "${RED}✗ Token removal failed${NC}"
fi
echo ""

# Test 12: Test invalid platform
echo -e "${YELLOW}Test 12: Test invalid platform (should fail)${NC}"
INVALID_PLATFORM_DATA='{
  "token": "test-token",
  "platform": "invalid"
}'
RESPONSE=$(api_call POST "/api/v1/notifications/register-push" "$INVALID_PLATFORM_DATA")
echo "$RESPONSE" | jq .
echo ""

# Test 13: Test quiet hours validation
echo -e "${YELLOW}Test 13: Test quiet hours edge cases${NC}"
QUIET_HOURS_DATA='{
  "quiet_hours_start": 0,
  "quiet_hours_end": 23
}'
RESPONSE=$(api_call PUT "/api/v1/notifications/settings" "$QUIET_HOURS_DATA")
QUIET_START=$(echo "$RESPONSE" | jq -r '.quiet_hours_start')
QUIET_END=$(echo "$RESPONSE" | jq -r '.quiet_hours_end')

if [ "$QUIET_START" == "0" ] && [ "$QUIET_END" == "23" ]; then
    echo -e "${GREEN}✓ Quiet hours edge cases work${NC}"
else
    echo -e "${RED}✗ Quiet hours validation issue${NC}"
fi
echo ""

echo "========================================="
echo -e "${GREEN}All tests completed!${NC}"
echo "========================================="

