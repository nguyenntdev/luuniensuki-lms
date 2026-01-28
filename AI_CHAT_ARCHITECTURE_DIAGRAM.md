# AI Chat Streaming & Recommendations - Architecture Diagram

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      MOBILE APP (Flutter)                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌────────────────────┐         ┌─────────────────────┐        │
│  │  Explore Screen    │         │   AI Chat Screen    │        │
│  │                    │         │                     │        │
│  │  ┌──────────────┐  │         │  ┌──────────────┐  │        │
│  │  │Recommendations│◄─┼─────────┼──┤ Chat Messages│  │        │
│  │  │Card Widget   │  │         │  │ (Streaming)  │  │        │
│  │  └──────┬───────┘  │         │  └──────┬───────┘  │        │
│  └─────────┼──────────┘         └─────────┼──────────┘        │
│            │                               │                    │
│            ▼                               ▼                    │
│  ┌─────────────────┐         ┌────────────────────┐           │
│  │Recommendations  │         │ AiChatRemoteData   │           │
│  │Provider         │         │ Source              │           │
│  │(Riverpod)       │         │ (SSE Streaming)     │           │
│  └─────────┬───────┘         └─────────┬──────────┘           │
│            │                            │                       │
│            │                            │                       │
│  ┌─────────▼────────────────────────────▼──────────┐          │
│  │         API Client (Dio + Auth)                 │          │
│  └─────────────────────┬───────────────────────────┘          │
└────────────────────────┼──────────────────────────────────────┘
                         │
                         │ HTTPS
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                    BACKEND SERVER (FastAPI)                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────────────┐      ┌───────────────────────┐       │
│  │ GET /api/v1/         │      │ POST /api/v1/ai/      │       │
│  │ recommendations      │      │ tutor/stream          │       │
│  │                      │      │ (NEW)                 │       │
│  │ Returns:             │      │                       │       │
│  │ {                    │      │ Returns SSE:          │       │
│  │   continue_learning, │      │ data: {type,content}  │       │
│  │   discover_new,      │      │ data: {type,citations}│       │
│  │   review_needed,     │      │ data: {type,done}     │       │
│  │   popular            │      │                       │       │
│  │ }                    │      │                       │       │
│  └──────────┬───────────┘      └──────────┬────────────┘       │
│             │                             │                     │
│             ▼                             ▼                     │
│  ┌─────────────────┐         ┌────────────────────────┐       │
│  │ Recommendations │         │ _call_deepseek_chat_   │       │
│  │ Service         │         │ stream()               │       │
│  │ (Existing)      │         │ (NEW)                  │       │
│  └─────────┬───────┘         └────────────┬───────────┘       │
│            │                              │                     │
│            ▼                              ▼                     │
│  ┌─────────────────────────────────────────────────────┐      │
│  │              PostgreSQL Database                     │      │
│  │  - User progress                                     │      │
│  │  - Content metadata                                  │      │
│  │  - Learning analytics                                │      │
│  └──────────────────────────────────────────────────────┘      │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          │ HTTPS
                          ▼
                 ┌─────────────────┐
                 │  DeepSeek API   │
                 │  (AI Service)   │
                 └─────────────────┘
```

## Data Flow Diagrams

### 1. Recommendations Flow
```
User opens Explore Screen
        │
        ▼
RecommendationsProvider fetches
        │
        ▼
GET /api/v1/recommendations?limit=5
        │
        ▼
Backend queries user progress
        │
        ▼
Recommendations Service calculates
- Continue learning (incomplete)
- Discover new (similar content)
- Review needed (due for review)
- Popular (trending)
        │
        ▼
Returns JSON response
        │
        ▼
Mobile parses RecommendationsResponseDto
        │
        ▼
RecommendationsCard renders
- Shows up to 2 continue_learning
- Shows up to 2 discover_new
- Color-coded icons
- Tap to navigate
```

### 2. AI Chat Streaming Flow
```
User sends message
        │
        ▼
_sendMessageStreaming() called
        │
        ▼
Add placeholder message (isStreaming: true)
        │
        ▼
POST /api/v1/ai/tutor/stream
        │
        ▼
Backend creates async generator
        │
        ▼
_call_deepseek_chat_stream()
calls DeepSeek API with stream=True
        │
        ▼
╔════════════════════════════════════╗
║   Real-time SSE Streaming Loop     ║
╠════════════════════════════════════╣
║  Backend yields:                   ║
║  data: {type:"chunk", content:"C"} ║
║  data: {type:"chunk", content:"a"} ║
║  data: {type:"chunk", content:"o"} ║
║  ...                               ║
║  data: {type:"done", citations:[]} ║
╚═══════════┬════════════════════════╝
            │
            ▼
Mobile receives each chunk
            │
            ▼
Parse AiChatStreamEvent
            │
            ▼
┌───────────▼──────────────┐
│  Event Type Handling:    │
├──────────────────────────┤
│  chunk → Append text     │
│  citations → Store refs  │
│  done → Mark complete    │
│  error → Show error      │
└───────────┬──────────────┘
            │
            ▼
Update UI with setState()
            │
            ▼
User sees text appear in real-time! ✨
```

## Component Relationships

### Recommendations Feature
```
explore_screen.dart
    │
    ├─► recommendations_card.dart (Widget)
    │       │
    │       ├─► recommendations_provider.dart (Data fetching)
    │       │       │
    │       │       └─► recommendation_dto.dart (Models)
    │       │               │
    │       │               ├─► recommendation_dto.freezed.dart
    │       │               └─► recommendation_dto.g.dart
    │       │
    │       └─► api_client.dart (Network)
    │
    └─► auth_provider.dart (Check if user logged in)
```

### AI Chat Streaming
```
ai_chat_screen.dart
    │
    ├─► _sendMessageStreaming() (New method)
    │       │
    │       └─► ai_chat_remote_data_source.dart
    │               │
    │               ├─► streamTutorResponse() → Stream<AiChatStreamEvent>
    │               │       │
    │               │       └─► Dio (HTTP client with SSE support)
    │               │
    │               └─► sendTutorMessage() (Fallback)
    │
    └─► _sendMessageNonStreaming() (Original method)
```

## State Management

### Recommendations
```
AsyncValue<RecommendationsResponseDto>
    ├─► Loading: Show spinner
    ├─► Data: Display recommendations
    └─► Error: Hide card silently
```

### AI Chat Messages
```
List<_ChatMessage>
    └─► _ChatMessage
            ├─► role: user | assistant
            ├─► content: String
            ├─► sources: List<_ChatCitation>
            └─► isStreaming: bool (NEW)
                    ├─► true → Show typing indicator
                    └─► false → Show complete message
```

## Security & Auth

```
┌──────────────────────────────┐
│   All API calls include:     │
├──────────────────────────────┤
│  Authorization: Bearer TOKEN │
└──────────────┬───────────────┘
               │
               ▼
    ┌──────────────────────┐
    │  Backend validates:   │
    ├───────────────────────┤
    │  - JWT token          │
    │  - User existence     │
    │  - Token expiration   │
    └──────────┬────────────┘
               │
               ▼
        ┌──────────────┐
        │ Returns 401  │
        │ if invalid   │
        └──────────────┘
```

## Performance Optimizations

### Backend
- Uses async/await for non-blocking I/O
- Streams responses (low memory)
- Connection pooling for database
- Caching for recommendations (optional)

### Mobile
- Riverpod auto-dispose (memory efficient)
- Widget rebuilds only affected parts
- Dio connection reuse
- Freezed immutable models (fast equality checks)

## Error Handling Flow

```
Error occurs
    │
    ├─► Backend
    │   ├─► Log error
    │   ├─► Return appropriate status code
    │   └─► For streaming: yield error event
    │
    └─► Mobile
        ├─► Catch exception
        ├─► Show user-friendly message
        ├─► Log to console (debug)
        └─► Graceful degradation:
            ├─► Recommendations: Hide card
            └─► Streaming: Fall back to non-streaming
```

## Key Design Decisions

1. **Streaming is opt-in**: `_useStreaming` toggle allows easy fallback
2. **Recommendations are silent**: Don't disturb UX if service fails
3. **SSE over WebSocket**: Simpler, HTTP-compatible, one-way is sufficient
4. **Freezed for models**: Type safety + JSON serialization
5. **Provider auto-dispose**: Prevents memory leaks
6. **In-place message updates**: Better UX than adding new messages


