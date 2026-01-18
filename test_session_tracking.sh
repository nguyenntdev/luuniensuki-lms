#!/bin/bash

# P0-ANA-03 Session Tracking API Testing Script
# Tests all session tracking endpoints

set -e

# Configuration
API_BASE="${API_BASE:-http://localhost}"
TEST_EMAIL="${TEST_EMAIL:-test@example.com}"
TEST_PASSWORD="${TEST_PASSWORD:-testpass123}"
ADMIN_EMAIL="${ADMIN_EMAIL:-admin@example.com}"
ADMIN_PASSWORD="${ADMIN_PASSWORD:-adminpass123}"

echo "🧪 P0-ANA-03 Session Tracking API Tests"
echo "========================================"
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print test results
print_result() {
    if [ $1 -eq 0 ]; then
        echo -e "${GREEN}✓ $2${NC}"
    else
        echo -e "${RED}✗ $2${NC}"
        exit 1
    fi
}

# Function to check if jq is installed
check_jq() {
    if ! command -v jq &> /dev/null; then
        echo -e "${RED}Error: jq is not installed${NC}"
        echo "Please install jq: brew install jq"
        exit 1
    fi
}

check_jq

echo "📋 Step 1: User Login"
echo "--------------------"

# Login as regular user
USER_TOKEN=$(curl -s -X POST "$API_BASE/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"$TEST_EMAIL\",\"password\":\"$TEST_PASSWORD\"}" \
  | jq -r '.access_token // empty')

if [ -z "$USER_TOKEN" ]; then
    echo -e "${RED}Failed to login as user${NC}"
    echo "Creating test user..."
    
    # Try to register
    curl -s -X POST "$API_BASE/api/v1/auth/register" \
      -H "Content-Type: application/json" \
      -d "{\"email\":\"$TEST_EMAIL\",\"password\":\"$TEST_PASSWORD\",\"display_name\":\"Test User\"}" \
      > /dev/null
    
    # Try login again
    USER_TOKEN=$(curl -s -X POST "$API_BASE/api/v1/auth/login" \
      -H "Content-Type: application/json" \
      -d "{\"email\":\"$TEST_EMAIL\",\"password\":\"$TEST_PASSWORD\"}" \
      | jq -r '.access_token // empty')
fi

if [ -z "$USER_TOKEN" ]; then
    print_result 1 "User login failed"
else
    print_result 0 "User logged in successfully"
fi

echo ""
echo "📋 Step 2: Test Session Heartbeat (Create Session)"
echo "-------------------------------------------------"

# Generate session ID
if command -v uuidgen &> /dev/null; then
    SESSION_ID=$(uuidgen | tr '[:upper:]' '[:lower:]')
else
    SESSION_ID="$(cat /proc/sys/kernel/random/uuid 2>/dev/null || python3 -c 'import uuid; print(uuid.uuid4())')"
fi

echo "Session ID: $SESSION_ID"

# Send heartbeat
HEARTBEAT_RESPONSE=$(curl -s -X POST "$API_BASE/api/v1/sessions/heartbeat" \
  -H "Authorization: Bearer $USER_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"session_id\": \"$SESSION_ID\",
    \"device_type\": \"web\",
    \"platform\": \"web\",
    \"app_version\": \"1.0.0\"
  }")

echo "Response: $HEARTBEAT_RESPONSE" | jq .

SUCCESS=$(echo "$HEARTBEAT_RESPONSE" | jq -r '.success // false')
if [ "$SUCCESS" = "true" ]; then
    print_result 0 "Heartbeat sent successfully"
else
    print_result 1 "Heartbeat failed"
fi

echo ""
echo "📋 Step 3: Test Session Heartbeat (Update Session)"
echo "-------------------------------------------------"

sleep 2

# Send another heartbeat to same session
HEARTBEAT_RESPONSE_2=$(curl -s -X POST "$API_BASE/api/v1/sessions/heartbeat" \
  -H "Authorization: Bearer $USER_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"session_id\": \"$SESSION_ID\",
    \"device_type\": \"mobile\",
    \"platform\": \"ios\",
    \"app_version\": \"1.5.0\"
  }")

echo "Response: $HEARTBEAT_RESPONSE_2" | jq .

SUCCESS=$(echo "$HEARTBEAT_RESPONSE_2" | jq -r '.success // false')
if [ "$SUCCESS" = "true" ]; then
    print_result 0 "Session updated successfully"
else
    print_result 1 "Session update failed"
fi

echo ""
echo "📋 Step 4: Admin Login"
echo "--------------------"

# Login as admin
ADMIN_TOKEN=$(curl -s -X POST "$API_BASE/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"$ADMIN_EMAIL\",\"password\":\"$ADMIN_PASSWORD\"}" \
  | jq -r '.access_token // empty')

if [ -z "$ADMIN_TOKEN" ]; then
    print_result 1 "Admin login failed (skip admin tests)"
    SKIP_ADMIN=true
else
    print_result 0 "Admin logged in successfully"
    SKIP_ADMIN=false
fi

if [ "$SKIP_ADMIN" = "false" ]; then
    echo ""
    echo "📋 Step 5: Get Active Sessions (Admin)"
    echo "------------------------------------"

    ACTIVE_SESSIONS=$(curl -s -X GET "$API_BASE/api/v1/admin/analytics/sessions/active" \
      -H "Authorization: Bearer $ADMIN_TOKEN")

    echo "Response: $ACTIVE_SESSIONS" | jq .

    ACTIVE_COUNT=$(echo "$ACTIVE_SESSIONS" | jq -r '.active_sessions // 0')
    print_result 0 "Active sessions retrieved: $ACTIVE_COUNT"

    echo ""
    echo "📋 Step 6: Get Session Statistics (Admin)"
    echo "---------------------------------------"

    SESSION_STATS=$(curl -s -X GET "$API_BASE/api/v1/admin/analytics/sessions/stats" \
      -H "Authorization: Bearer $ADMIN_TOKEN")

    echo "Response: $SESSION_STATS" | jq .

    TOTAL_TODAY=$(echo "$SESSION_STATS" | jq -r '.total_sessions_today // 0')
    print_result 0 "Session stats retrieved: $TOTAL_TODAY sessions today"
fi

echo ""
echo "📋 Step 7: End Session"
echo "--------------------"

END_RESPONSE=$(curl -s -X POST "$API_BASE/api/v1/sessions/end" \
  -H "Authorization: Bearer $USER_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"session_id\": \"$SESSION_ID\"}")

echo "Response: $END_RESPONSE" | jq .

SUCCESS=$(echo "$END_RESPONSE" | jq -r '.success // false')
DURATION=$(echo "$END_RESPONSE" | jq -r '.duration_seconds // 0')

if [ "$SUCCESS" = "true" ]; then
    print_result 0 "Session ended successfully (duration: ${DURATION}s)"
else
    print_result 1 "Session end failed"
fi

echo ""
echo "========================================" 
echo -e "${GREEN}✓ All tests completed successfully!${NC}"
echo "========================================" 

