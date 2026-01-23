#!/bin/bash

# Test script to verify the complete-lesson endpoint works

API_BASE="${API_BASE:-https://lms.histolab.icu}"

echo "=== Test Complete Lesson Endpoint ==="
echo "API Base: $API_BASE"
echo ""

# Check if TOKEN is set
if [ -z "$TOKEN" ]; then
    echo "ERROR: TOKEN environment variable not set"
    echo "Usage: TOKEN=your_jwt_token bash test_complete_lesson.sh"
    echo ""
    echo "To get a token:"
    echo "1. Login via the app or web"
    echo "2. Copy the JWT token from localStorage or app storage"
    echo "3. Set it as: export TOKEN='your_token_here'"
    exit 1
fi

# Check if MOTIF_ID is set
if [ -z "$MOTIF_ID" ]; then
    echo "ERROR: MOTIF_ID environment variable not set"
    echo "Usage: TOKEN=your_jwt MOTIF_ID=motif_uuid bash test_complete_lesson.sh"
    echo ""
    echo "To get a motif ID:"
    echo "1. Open the app and view a lesson"
    echo "2. Copy the motif UUID from the URL or logs"
    echo "3. Set it as: export MOTIF_ID='uuid_here'"
    exit 1
fi

echo "Testing endpoint: POST $API_BASE/api/v1/motifs/$MOTIF_ID/complete-lesson"
echo ""

# Make the API call
RESPONSE=$(curl -s -X POST "$API_BASE/api/v1/motifs/$MOTIF_ID/complete-lesson" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -w "\n%{http_code}")

# Extract HTTP status code (last line)
HTTP_CODE=$(echo "$RESPONSE" | tail -n 1)
BODY=$(echo "$RESPONSE" | sed '$d')

echo "HTTP Status: $HTTP_CODE"
echo ""
echo "Response Body:"
echo "$BODY" | python3 -m json.tool 2>/dev/null || echo "$BODY"
echo ""

if [ "$HTTP_CODE" = "200" ]; then
    echo "✅ SUCCESS! Lesson completed successfully"
    echo ""
    echo "Expected fields in response:"
    echo "- user_id: UUID"
    echo "- motif_id: UUID"
    echo "- status: string (e.g., 'learned')"
    echo "- lesson_viewed_at: timestamp"
    echo "- learned_at: timestamp"
    echo "- xp_awarded: number"
    echo "- total_xp: number"
else
    echo "❌ FAILED with status $HTTP_CODE"
    echo ""
    echo "Common issues:"
    echo "- 401: Token is invalid or expired"
    echo "- 403: Lesson not published or access denied"
    echo "- 404: Motif not found"
fi

