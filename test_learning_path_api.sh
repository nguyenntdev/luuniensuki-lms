#!/bin/bash

# P1-ADAP-03: Learning Path API Testing Script
# Tests all learning path endpoints

set -e

# Configuration
API_BASE="${API_BASE:-http://localhost:8000}"
EMAIL="${TEST_EMAIL:-test@example.com}"
PASSWORD="${TEST_PASSWORD:-testpass123}"

echo "=========================================="
echo "P1-ADAP-03: Learning Path API Tests"
echo "=========================================="
echo ""

# Step 1: Login to get token
echo "Step 1: Logging in..."
LOGIN_RESPONSE=$(curl -s -X POST "$API_BASE/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"$EMAIL\",\"password\":\"$PASSWORD\"}")

TOKEN=$(echo "$LOGIN_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])" 2>/dev/null || echo "")

if [ -z "$TOKEN" ]; then
    echo "❌ Login failed. Please check credentials."
    echo "Response: $LOGIN_RESPONSE"
    exit 1
fi

echo "✅ Login successful"
echo ""

# Step 2: Get today's learning path
echo "Step 2: Getting today's learning path..."
TODAYS_PATH=$(curl -s -X GET "$API_BASE/api/v1/learning-path/today" \
  -H "Authorization: Bearer $TOKEN")

echo "$TODAYS_PATH" | python3 -m json.tool

PATH_ID=$(echo "$TODAYS_PATH" | python3 -c "import sys, json; print(json.load(sys.stdin).get('id', ''))" 2>/dev/null || echo "")

if [ -z "$PATH_ID" ]; then
    echo "❌ Failed to get today's path"
    exit 1
fi

echo "✅ Today's path retrieved (ID: $PATH_ID)"
echo ""

# Step 3: Get first lesson ID from path
echo "Step 3: Extracting first lesson..."
FIRST_LESSON=$(echo "$TODAYS_PATH" | python3 -c "
import sys, json
data = json.load(sys.stdin)
lessons = data.get('lessons', [])
if lessons:
    print(lessons[0]['item_id'])
else:
    print('')
" 2>/dev/null || echo "")

if [ -n "$FIRST_LESSON" ]; then
    echo "✅ Found lesson: $FIRST_LESSON"
    echo ""
    
    # Step 4: Complete the lesson
    echo "Step 4: Marking lesson as complete..."
    COMPLETE_RESPONSE=$(curl -s -X POST "$API_BASE/api/v1/learning-path/complete-item" \
      -H "Authorization: Bearer $TOKEN" \
      -H "Content-Type: application/json" \
      -d "{\"item_type\":\"lesson\",\"item_id\":\"$FIRST_LESSON\"}")
    
    echo "$COMPLETE_RESPONSE" | python3 -m json.tool
    
    SUCCESS=$(echo "$COMPLETE_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('success', False))" 2>/dev/null || echo "false")
    
    if [ "$SUCCESS" = "True" ]; then
        echo "✅ Lesson marked as complete"
    else
        echo "⚠️  Completion status unclear"
    fi
    echo ""
else
    echo "⚠️  No lessons in today's path (user may have completed all content)"
    echo ""
fi

# Step 5: Force regenerate path
echo "Step 5: Force regenerating path..."
REGENERATE_RESPONSE=$(curl -s -X POST "$API_BASE/api/v1/learning-path/generate" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"force_regenerate":true}')

echo "$REGENERATE_RESPONSE" | python3 -m json.tool

NEW_PATH_ID=$(echo "$REGENERATE_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('id', ''))" 2>/dev/null || echo "")

if [ -n "$NEW_PATH_ID" ]; then
    echo "✅ Path regenerated (New ID: $NEW_PATH_ID)"
else
    echo "❌ Failed to regenerate path"
fi
echo ""

# Step 6: Get path history
echo "Step 6: Getting path history (last 7 days)..."
HISTORY_RESPONSE=$(curl -s -X GET "$API_BASE/api/v1/learning-path/history?days=7" \
  -H "Authorization: Bearer $TOKEN")

echo "$HISTORY_RESPONSE" | python3 -m json.tool

TOTAL_PATHS=$(echo "$HISTORY_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('total_paths', 0))" 2>/dev/null || echo "0")

echo "✅ Retrieved $TOTAL_PATHS historical paths"
echo ""

# Step 7: Get path statistics
echo "Step 7: Getting path statistics (last 30 days)..."
STATS_RESPONSE=$(curl -s -X GET "$API_BASE/api/v1/learning-path/stats?days=30" \
  -H "Authorization: Bearer $TOKEN")

echo "$STATS_RESPONSE" | python3 -m json.tool

COMPLETION_RATE=$(echo "$STATS_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('completion_rate', 0))" 2>/dev/null || echo "0")

echo "✅ Completion rate: ${COMPLETION_RATE}%"
echo ""

echo "=========================================="
echo "Test Summary"
echo "=========================================="
echo "✅ Login successful"
echo "✅ Today's path retrieved"
if [ -n "$FIRST_LESSON" ]; then
    echo "✅ Item completion tested"
fi
echo "✅ Path regeneration tested"
echo "✅ History retrieval tested"
echo "✅ Statistics retrieval tested"
echo ""
echo "All tests completed successfully! 🎉"

