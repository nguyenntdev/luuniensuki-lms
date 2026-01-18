# AI Conversation API Quick Reference

## Authentication
All endpoints require a valid JWT token in the Authorization header:
```
Authorization: Bearer <your_jwt_token>
```

## Endpoints

### 1. List Conversations
```
GET /api/v1/ai/conversations
```

**Query Parameters:**
- `page` (int, default=1): Page number
- `page_size` (int, default=20, max=100): Items per page
- `active_only` (bool, default=true): Show only active conversations

**Example:**
```bash
curl -X GET "http://localhost:8000/api/v1/ai/conversations?page=1&page_size=10" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Response:**
```json
{
  "conversations": [
    {
      "id": "uuid",
      "title": "Conversation about Cửu Đỉnh",
      "context_type": "motif",
      "context_id": "uuid",
      "is_active": true,
      "message_count": 5,
      "created_at": "2025-01-20T10:00:00Z",
      "updated_at": "2025-01-20T11:00:00Z",
      "last_message": "AI response preview...",
      "last_message_at": "2025-01-20T11:00:00Z"
    }
  ],
  "total": 15,
  "page": 1,
  "page_size": 10,
  "has_more": true
}
```

---

### 2. Create Conversation
```
POST /api/v1/ai/conversations
```

**Request Body:**
```json
{
  "title": "My conversation about Vietnamese history",
  "context_type": "motif",
  "context_id": "uuid-of-motif",
  "initial_message": "Tell me about this motif"
}
```

**Note:** All fields are optional. If `initial_message` is provided, the AI will respond immediately.

**Example:**
```bash
curl -X POST "http://localhost:8000/api/v1/ai/conversations" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "context_type": "general",
    "initial_message": "Xin chào! Hãy giới thiệu về Cửu Đỉnh?"
  }'
```

**Response (201 Created):**
```json
{
  "id": "uuid",
  "title": "Conversation about Cửu Đỉnh",
  "context_type": "general",
  "context_id": null,
  "created_at": "2025-01-20T10:00:00Z",
  "message": "Conversation created successfully"
}
```

---

### 3. Get Conversation Details
```
GET /api/v1/ai/conversations/{conversation_id}
```

**Example:**
```bash
curl -X GET "http://localhost:8000/api/v1/ai/conversations/your-uuid-here" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Response:**
```json
{
  "id": "uuid",
  "title": "Conversation about Cửu Đỉnh",
  "context_type": "general",
  "context_id": null,
  "is_active": true,
  "message_count": 4,
  "created_at": "2025-01-20T10:00:00Z",
  "updated_at": "2025-01-20T10:05:00Z",
  "messages": [
    {
      "id": "msg-uuid-1",
      "conversation_id": "uuid",
      "role": "user",
      "content": "Xin chào! Hãy giới thiệu về Cửu Đỉnh?",
      "tokens_used": null,
      "created_at": "2025-01-20T10:00:00Z"
    },
    {
      "id": "msg-uuid-2",
      "conversation_id": "uuid",
      "role": "assistant",
      "content": "Cửu Đỉnh là...",
      "tokens_used": 250,
      "created_at": "2025-01-20T10:00:05Z"
    }
  ]
}
```

---

### 4. Send Message
```
POST /api/v1/ai/conversations/{conversation_id}/messages
```

**Request Body:**
```json
{
  "message": "Tell me more about Đỉnh Thần Công"
}
```

**Example:**
```bash
curl -X POST "http://localhost:8000/api/v1/ai/conversations/your-uuid-here/messages" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Tôi muốn biết thêm về Đỉnh Thần Công"
  }'
```

**Response:**
```json
{
  "message": {
    "id": "msg-uuid-3",
    "conversation_id": "uuid",
    "role": "user",
    "content": "Tôi muốn biết thêm về Đỉnh Thần Công",
    "tokens_used": null,
    "created_at": "2025-01-20T10:02:00Z"
  },
  "response": {
    "id": "msg-uuid-4",
    "conversation_id": "uuid",
    "role": "assistant",
    "content": "Đỉnh Thần Công...",
    "tokens_used": 300,
    "created_at": "2025-01-20T10:02:05Z"
  },
  "conversation_id": "uuid",
  "tokens_used": 300
}
```

---

### 5. Delete Conversation
```
DELETE /api/v1/ai/conversations/{conversation_id}
```

**Example:**
```bash
curl -X DELETE "http://localhost:8000/api/v1/ai/conversations/your-uuid-here" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Response:** `204 No Content` (success)

---

## Error Responses

### 401 Unauthorized
```json
{
  "detail": "Not authenticated"
}
```

### 404 Not Found
```json
{
  "detail": "Conversation not found"
}
```

### 400 Bad Request
```json
{
  "detail": "Conversation is not active"
}
```

### 503 Service Unavailable
```json
{
  "detail": "AI service not configured"
}
```

---

## Context Types

Valid values for `context_type`:
- `"general"` - General conversation, no specific context
- `"lesson"` - Related to a specific lesson
- `"motif"` - Related to a specific motif
- `"quest"` - Related to a specific quest

When using a context type other than "general", provide the related `context_id`.

---

## Notes

1. **Message Length**: Messages must be between 1 and 5000 characters
2. **Pagination**: Maximum page_size is 100
3. **History**: AI responses include context from last 10 messages
4. **Auto-Titles**: If no title provided, it's generated from the first message
5. **RAG**: AI responses automatically include relevant source material
6. **Token Tracking**: Token counts are stored when available from API

---

**API Version:** v1
**Base URL:** http://localhost:8000/api/v1
**Documentation:** http://localhost:8000/docs (when server running)

