#!/bin/bash
# P0-CMS-03 Content Versioning Test Script
# This script demonstrates testing the content versioning endpoints

# Configuration
API_URL="http://localhost:8000"
TOKEN="your_jwt_token_here"  # Replace with actual JWT token

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}═══════════════════════════════════════════════════${NC}"
echo -e "${BLUE}  P0-CMS-03 Content Versioning Test Suite${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════${NC}"
echo ""

# Step 1: Create a new lesson
echo -e "${YELLOW}Step 1: Creating a new lesson...${NC}"
LESSON_ID=$(curl -s -X POST "${API_URL}/api/v1/admin/lessons" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "motif_id": "your-motif-id-here",
    "description": "Initial lesson content",
    "intro_text": "Welcome to this lesson",
    "historical_context": "This motif dates back to...",
    "is_published": false
  }' | jq -r '.id')

echo -e "${GREEN}✓ Lesson created with ID: ${LESSON_ID}${NC}"
echo ""

# Step 2: List versions (should be empty since we haven't updated yet)
echo -e "${YELLOW}Step 2: Listing versions (should be empty)...${NC}"
curl -s -X GET "${API_URL}/api/v1/admin/content/lesson/${LESSON_ID}/versions" \
  -H "Authorization: Bearer ${TOKEN}" | jq '.'
echo ""

# Step 3: First update - creates version 1 snapshot
echo -e "${YELLOW}Step 3: Updating lesson (creates version 1 snapshot)...${NC}"
curl -s -X PATCH "${API_URL}/api/v1/admin/lessons/${LESSON_ID}" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "description": "Updated lesson content - First edit",
    "historical_context": "More detailed historical context..."
  }' | jq '.'
echo ""

# Step 4: List versions again (should show version 1)
echo -e "${YELLOW}Step 4: Listing versions (should show version 1)...${NC}"
curl -s -X GET "${API_URL}/api/v1/admin/content/lesson/${LESSON_ID}/versions" \
  -H "Authorization: Bearer ${TOKEN}" | jq '.'
echo ""

# Step 5: Second update - creates version 2 snapshot
echo -e "${YELLOW}Step 5: Making another update (creates version 2 snapshot)...${NC}"
curl -s -X PATCH "${API_URL}/api/v1/admin/lessons/${LESSON_ID}" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "description": "Updated lesson content - Second edit",
    "symbolism": "This motif symbolizes prosperity and good fortune"
  }' | jq '.'
echo ""

# Step 6: List all versions (should show versions 1 and 2)
echo -e "${YELLOW}Step 6: Listing all versions (should show v1 and v2)...${NC}"
curl -s -X GET "${API_URL}/api/v1/admin/content/lesson/${LESSON_ID}/versions" \
  -H "Authorization: Bearer ${TOKEN}" | jq '.'
echo ""

# Step 7: Get specific version (version 1)
echo -e "${YELLOW}Step 7: Getting version 1 details with full data...${NC}"
curl -s -X GET "${API_URL}/api/v1/admin/content/lesson/${LESSON_ID}/versions/1" \
  -H "Authorization: Bearer ${TOKEN}" | jq '.'
echo ""

# Step 8: Third update with publish
echo -e "${YELLOW}Step 8: Publishing the lesson (creates version 3)...${NC}"
curl -s -X PATCH "${API_URL}/api/v1/admin/lessons/${LESSON_ID}" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "is_published": true,
    "publish_note": "Ready for production - v1.0"
  }' | jq '.'
echo ""

# Step 9: Revert to version 1
echo -e "${YELLOW}Step 9: Reverting to version 1...${NC}"
curl -s -X POST "${API_URL}/api/v1/admin/content/lesson/${LESSON_ID}/revert/1" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "change_note": "Reverting to original content due to errors in later versions"
  }' | jq '.'
echo ""

# Step 10: List all versions (should now show v1, v2, v3, and v4 after revert)
echo -e "${YELLOW}Step 10: Listing all versions after revert...${NC}"
curl -s -X GET "${API_URL}/api/v1/admin/content/lesson/${LESSON_ID}/versions" \
  -H "Authorization: Bearer ${TOKEN}" | jq '.'
echo ""

# Step 11: Get current lesson state
echo -e "${YELLOW}Step 11: Getting current lesson state...${NC}"
curl -s -X GET "${API_URL}/api/v1/admin/lessons/${LESSON_ID}" \
  -H "Authorization: Bearer ${TOKEN}" | jq '.'
echo ""

echo -e "${GREEN}═══════════════════════════════════════════════════${NC}"
echo -e "${GREEN}  Test suite completed!${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════${NC}"
echo ""
echo -e "Summary of operations:"
echo -e "  • Created lesson (version 1)"
echo -e "  • Updated lesson (version 2, created v1 snapshot)"
echo -e "  • Updated again (version 3, created v2 snapshot)"
echo -e "  • Published lesson (version 4, created v3 snapshot)"
echo -e "  • Reverted to v1 (version 5, created v4 snapshot then v5 with v1 data)"
echo ""
echo -e "Expected result: Lesson should have content from version 1"
echo -e "                 but version number should be 5"
echo ""

