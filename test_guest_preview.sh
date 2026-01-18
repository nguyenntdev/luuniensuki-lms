#!/bin/bash

# P0-ACT-02 Guest Preview - API Testing Script
# Tests all preview endpoints

set -e

BASE_URL="${API_URL:-http://localhost:8000}"
SESSION_ID="test-session-$(date +%s)"

echo "=========================================="
echo "P0-ACT-02 Guest Preview API Testing"
echo "=========================================="
echo "Base URL: $BASE_URL"
echo "Session ID: $SESSION_ID"
echo ""

# Test 1: Get preview lesson (no auth)
echo "Test 1: GET /api/v1/preview/lesson"
echo "→ Getting demo lesson for guests..."
LESSON_RESPONSE=$(curl -s -X GET "$BASE_URL/api/v1/preview/lesson")
echo "$LESSON_RESPONSE" | jq '.'

if echo "$LESSON_RESPONSE" | jq -e '.lesson_id' > /dev/null 2>&1; then
  echo "✅ Successfully retrieved preview lesson"
  LESSON_ID=$(echo "$LESSON_RESPONSE" | jq -r '.lesson_id')
else
  echo "❌ Failed to get preview lesson"
  echo "   Make sure at least one lesson has preview_eligible=true"
  exit 1
fi
echo ""

# Test 2: Start preview session (no auth)
echo "Test 2: POST /api/v1/preview/start"
echo "→ Starting preview session..."
START_RESPONSE=$(curl -s -X POST "$BASE_URL/api/v1/preview/start" \
  -H "Content-Type: application/json" \
  -d "{
    \"session_id\": \"$SESSION_ID\",
    \"device_info\": {
      \"platform\": \"web\",
      \"browser\": \"test-script\",
      \"os\": \"linux\"
    }
  }")
echo "$START_RESPONSE" | jq '.'

if echo "$START_RESPONSE" | jq -e '.preview_id' > /dev/null 2>&1; then
  echo "✅ Successfully started preview session"
  PREVIEW_ID=$(echo "$START_RESPONSE" | jq -r '.preview_id')
else
  echo "❌ Failed to start preview session"
  exit 1
fi
echo ""

# Test 3: Complete preview session (no auth)
echo "Test 3: POST /api/v1/preview/complete"
echo "→ Marking preview session as complete..."
COMPLETE_RESPONSE=$(curl -s -X POST "$BASE_URL/api/v1/preview/complete" \
  -H "Content-Type: application/json" \
  -d "{
    \"session_id\": \"$SESSION_ID\"
  }")
echo "$COMPLETE_RESPONSE" | jq '.'

if echo "$COMPLETE_RESPONSE" | jq -e '.success' > /dev/null 2>&1; then
  echo "✅ Successfully completed preview session"
else
  echo "❌ Failed to complete preview session"
  exit 1
fi
echo ""

# Test 4: Register a new user
echo "Test 4: Register new user"
echo "→ Creating test user account..."
REGISTER_EMAIL="preview-test-$(date +%s)@example.com"
REGISTER_RESPONSE=$(curl -s -X POST "$BASE_URL/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d "{
    \"email\": \"$REGISTER_EMAIL\",
    \"password\": \"testpassword123\",
    \"display_name\": \"Preview Test User\"
  }")
echo "$REGISTER_RESPONSE" | jq '.'

if echo "$REGISTER_RESPONSE" | jq -e '.access_token' > /dev/null 2>&1; then
  echo "✅ Successfully registered new user"
  ACCESS_TOKEN=$(echo "$REGISTER_RESPONSE" | jq -r '.access_token')
else
  echo "❌ Failed to register user"
  exit 1
fi
echo ""

# Test 5: Convert preview session (auth required)
echo "Test 5: POST /api/v1/preview/convert"
echo "→ Linking preview session to user account..."
CONVERT_RESPONSE=$(curl -s -X POST "$BASE_URL/api/v1/preview/convert" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -d "{
    \"session_id\": \"$SESSION_ID\"
  }")
echo "$CONVERT_RESPONSE" | jq '.'

if echo "$CONVERT_RESPONSE" | jq -e '.success' > /dev/null 2>&1; then
  SESSIONS_CONVERTED=$(echo "$CONVERT_RESPONSE" | jq -r '.preview_sessions_converted')
  echo "✅ Successfully converted preview session(s): $SESSIONS_CONVERTED"
else
  echo "❌ Failed to convert preview session"
  exit 1
fi
echo ""

echo "=========================================="
echo "✅ All tests passed!"
echo "=========================================="
echo ""
echo "Summary:"
echo "  - Preview ID: $PREVIEW_ID"
echo "  - Session ID: $SESSION_ID"
echo "  - User Email: $REGISTER_EMAIL"
echo "  - Converted Sessions: $SESSIONS_CONVERTED"
echo ""

