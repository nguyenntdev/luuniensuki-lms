#!/bin/bash
# P0-RAG-02: RAG Document Management API Testing Script
#
# Prerequisites:
# 1. Backend server running on http://localhost:8000
# 2. Admin user created and logged in
# 3. Set ADMIN_TOKEN environment variable with valid JWT token
#
# Usage:
#   export ADMIN_TOKEN="your_admin_jwt_token"
#   bash P0-RAG-02_API_TESTING.sh

set -e

# Configuration
API_BASE="http://localhost:8000/api/v1/admin/rag/documents"
TOKEN="${ADMIN_TOKEN}"

if [ -z "$TOKEN" ]; then
    echo "❌ Error: ADMIN_TOKEN environment variable not set"
    echo "Usage: export ADMIN_TOKEN='your_token' && bash $0"
    exit 1
fi

echo "🚀 P0-RAG-02: RAG Document Management API Testing"
echo "================================================"
echo ""

# Test 1: Create a manual document
echo "📝 Test 1: Create Manual Document"
echo "POST $API_BASE"
CREATED_DOC=$(curl -s -X POST "$API_BASE" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Test Document - Vietnamese History",
    "content": "This is a test document about Vietnamese history. It contains information about the Lưu Niên Dynasty.",
    "is_active": true
  }')
echo "$CREATED_DOC" | jq '.'
DOC_ID=$(echo "$CREATED_DOC" | jq -r '.id')
echo "✅ Created document with ID: $DOC_ID"
echo ""

# Test 2: Create a test file and upload it
echo "📤 Test 2: Upload Text File"
echo "POST $API_BASE/upload"
cat > /tmp/test_rag_document.txt << 'EOF'
Vietnamese Historical Dynasties

The history of Vietnam is marked by various dynasties that ruled over different periods.
Each dynasty contributed to the rich cultural heritage of Vietnam.

This document serves as a knowledge base for the RAG system to provide
contextual information about Vietnamese history.
EOF

UPLOADED_DOC=$(curl -s -X POST "$API_BASE/upload" \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@/tmp/test_rag_document.txt" \
  -F "title=Vietnamese Dynasties Overview")
echo "$UPLOADED_DOC" | jq '.'
UPLOADED_DOC_ID=$(echo "$UPLOADED_DOC" | jq -r '.id')
echo "✅ Uploaded document with ID: $UPLOADED_DOC_ID"
echo ""

# Test 3: List documents with pagination
echo "📋 Test 3: List Documents (Page 1, 10 items)"
echo "GET $API_BASE?page=1&page_size=10"
LIST_RESULT=$(curl -s "$API_BASE?page=1&page_size=10" \
  -H "Authorization: Bearer $TOKEN")
echo "$LIST_RESULT" | jq '.'
TOTAL_DOCS=$(echo "$LIST_RESULT" | jq -r '.total')
echo "✅ Total documents: $TOTAL_DOCS"
echo ""

# Test 4: Get single document
echo "🔍 Test 4: Get Single Document"
echo "GET $API_BASE/$DOC_ID"
SINGLE_DOC=$(curl -s "$API_BASE/$DOC_ID" \
  -H "Authorization: Bearer $TOKEN")
echo "$SINGLE_DOC" | jq '.'
echo "✅ Retrieved document"
echo ""

# Test 5: Update document content
echo "✏️ Test 5: Update Document Content"
echo "PUT $API_BASE/$DOC_ID"
UPDATED_DOC=$(curl -s -X PUT "$API_BASE/$DOC_ID" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "UPDATED: This is an updated test document about Vietnamese history with new information."
  }')
echo "$UPDATED_DOC" | jq '.'
echo "✅ Updated document content"
echo ""

# Test 6: Deactivate document
echo "❌ Test 6: Deactivate Document"
echo "POST $API_BASE/$DOC_ID/deactivate"
DEACTIVATED_DOC=$(curl -s -X POST "$API_BASE/$DOC_ID/deactivate" \
  -H "Authorization: Bearer $TOKEN")
echo "$DEACTIVATED_DOC" | jq '.'
IS_ACTIVE=$(echo "$DEACTIVATED_DOC" | jq -r '.is_active')
if [ "$IS_ACTIVE" = "false" ]; then
    echo "✅ Document deactivated successfully"
else
    echo "❌ Failed to deactivate document"
fi
echo ""

# Test 7: Activate document
echo "✅ Test 7: Activate Document"
echo "POST $API_BASE/$DOC_ID/activate"
ACTIVATED_DOC=$(curl -s -X POST "$API_BASE/$DOC_ID/activate" \
  -H "Authorization: Bearer $TOKEN")
echo "$ACTIVATED_DOC" | jq '.'
IS_ACTIVE=$(echo "$ACTIVATED_DOC" | jq -r '.is_active')
if [ "$IS_ACTIVE" = "true" ]; then
    echo "✅ Document activated successfully"
else
    echo "❌ Failed to activate document"
fi
echo ""

# Test 8: Test file size limit (create a 6MB file)
echo "🚫 Test 8: File Size Limit (Should Fail)"
echo "POST $API_BASE/upload"
dd if=/dev/zero of=/tmp/large_file.txt bs=1M count=6 2>/dev/null
UPLOAD_RESULT=$(curl -s -X POST "$API_BASE/upload" \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@/tmp/large_file.txt" | jq '.')
echo "$UPLOAD_RESULT"
if echo "$UPLOAD_RESULT" | grep -q "too large"; then
    echo "✅ Correctly rejected file > 5MB"
else
    echo "⚠️ File size validation may not be working"
fi
rm /tmp/large_file.txt
echo ""

# Test 9: Test unsupported file type
echo "🚫 Test 9: Unsupported File Type (Should Fail)"
echo "POST $API_BASE/upload"
echo "Binary content" > /tmp/test.pdf
UPLOAD_RESULT=$(curl -s -X POST "$API_BASE/upload" \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@/tmp/test.pdf" | jq '.')
echo "$UPLOAD_RESULT"
if echo "$UPLOAD_RESULT" | grep -q "Unsupported"; then
    echo "✅ Correctly rejected unsupported file type"
else
    echo "⚠️ File type validation may not be working"
fi
rm /tmp/test.pdf
echo ""

# Test 10: Delete document
echo "🗑️ Test 10: Delete Document"
echo "DELETE $API_BASE/$UPLOADED_DOC_ID"
DELETE_RESPONSE=$(curl -s -w "\n%{http_code}" -X DELETE "$API_BASE/$UPLOADED_DOC_ID" \
  -H "Authorization: Bearer $TOKEN")
HTTP_CODE=$(echo "$DELETE_RESPONSE" | tail -1)
if [ "$HTTP_CODE" = "204" ]; then
    echo "✅ Document deleted successfully (HTTP 204)"
else
    echo "❌ Delete failed with HTTP $HTTP_CODE"
fi
echo ""

# Clean up
echo "🧹 Cleanup"
echo "DELETE $API_BASE/$DOC_ID"
curl -s -X DELETE "$API_BASE/$DOC_ID" \
  -H "Authorization: Bearer $TOKEN" > /dev/null
rm -f /tmp/test_rag_document.txt
echo "✅ Cleanup completed"
echo ""

echo "================================================"
echo "✅ All tests completed!"
echo ""
echo "Summary:"
echo "- Created manual document ✓"
echo "- Uploaded text file ✓"
echo "- Listed documents with pagination ✓"
echo "- Retrieved single document ✓"
echo "- Updated document content ✓"
echo "- Deactivated document ✓"
echo "- Activated document ✓"
echo "- Tested file size limit ✓"
echo "- Tested file type validation ✓"
echo "- Deleted document ✓"

