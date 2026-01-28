# AI Chat Streaming & Recommendations - Quick Testing Guide

## 🎯 Quick Start

### Backend - Test Streaming Endpoint
```bash
# Start backend server
cd backend
python -m uvicorn main:app --reload

# Test streaming (replace TOKEN with actual JWT)
curl -N -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"message":"Tell me about Cao Dinh"}' \
  http://localhost:8000/api/v1/ai/tutor/stream

# Expected output (SSE format):
# data: {"type":"chunk","content":"Cao"}
# data: {"type":"chunk","content":" Đỉnh"}
# data: {"type":"done","citations":[...]}
```

### Mobile - Build & Run
```bash
cd mobile

# Generate code (if Flutter available)
flutter pub run build_runner build --delete-conflicting-outputs

# Run on device/emulator
flutter run
```

## ✅ Testing Checklist

### Backend SSE Streaming
- [ ] Server starts without errors
- [ ] Endpoint returns 401 without auth token
- [ ] Endpoint returns SSE stream with valid token
- [ ] Chunks arrive in real-time
- [ ] Citations included in response
- [ ] Error handling works (invalid input)

### Mobile Recommendations Widget
Login to app → Go to Explore screen → Should see:
- [ ] "Gợi ý cho bạn" card appears (logged in only)
- [ ] Shows "Tiếp tục học" section with continue_learning items
- [ ] Shows "Khám phá mới" section with discover_new items
- [ ] Icons are color-coded correctly
- [ ] Tapping item navigates to content
- [ ] Loading spinner shows while fetching
- [ ] Card hides gracefully on error

### Mobile AI Chat Streaming
Go to AI Chat screen (navigation drawer) → Start conversation:
- [ ] Send message to AI tutor
- [ ] Text appears character-by-character in real-time
- [ ] Message shows streaming indicator during generation
- [ ] Citations appear after message completes
- [ ] Multiple messages work correctly
- [ ] Error messages display if stream fails
- [ ] Q&A mode still uses non-streaming (instant response)

## 🐛 Common Issues & Fixes

### Backend Issues
**Problem**: `ImportError: cannot import name 'StreamingResponse'`
**Fix**: Update FastAPI: `pip install --upgrade fastapi`

**Problem**: Streaming endpoint returns 500
**Fix**: Check DeepSeek API key in `.env`, verify `DEEPSEEK_API_KEY` is set

**Problem**: Stream cuts off mid-response
**Fix**: Check timeout settings in nginx/proxy (should be > 60s for SSE)

### Mobile Issues
**Problem**: Recommendations card doesn't appear
**Fix**: 
1. Verify user is logged in
2. Check network tab - should call `/api/v1/recommendations`
3. Verify backend recommendations endpoint is working

**Problem**: Build errors with .g.dart files
**Fix**: Run `flutter pub run build_runner build --delete-conflicting-outputs`

**Problem**: Streaming not working in AI chat
**Fix**:
1. Check backend streaming endpoint is running
2. Verify `_useStreaming = true` in ai_chat_screen.dart
3. Check network inspector for SSE connection
4. Look for errors in Flutter logs

**Problem**: `aiChatRemoteDataSourceProvider not found`
**Fix**: Import is correct - check Dio provider exists in api_client.dart

## 📱 Visual Testing

### Recommendations Card Layout
```
┌─────────────────────────────────────┐
│ 💡 Gợi ý cho bạn                     │
├─────────────────────────────────────┤
│ Tiếp tục học                         │
│ ▶️  Lesson Title...                  │
│ 📝  Another Lesson...                │
│                                      │
│ Khám phá mới                         │
│ 🔍  New Content...                   │
│ 🌟  Trending Topic...                │
└─────────────────────────────────────┘
```

### AI Chat Streaming
```
User: Tell me about Cao Dinh

AI: [Streaming...] ▊
    Cao Đỉnh is one of the nine bronze urns...

AI: Cao Đỉnh is one of the nine bronze urns... ✓
    [Citations: 1, 2, 3]
```

## 🔍 Debug Commands

### Backend Logs
```bash
# Watch backend logs
tail -f backend.log

# Test with verbose curl
curl -v -N -H "Authorization: Bearer TOKEN" \
  http://localhost:8000/api/v1/ai/tutor/stream
```

### Mobile Logs
```bash
# Flutter logs
flutter logs

# Filter for recommendations
flutter logs | grep -i recommendation

# Filter for streaming
flutter logs | grep -i stream
```

## 📊 Performance Checks

### Backend
- SSE first chunk time: < 500ms
- Full response time: depends on DeepSeek (usually 2-5s)
- Memory usage: stable (no leaks)

### Mobile
- Recommendations load time: < 1s
- Streaming text updates: 60 FPS smooth
- Memory: no spikes during streaming

## 🚀 Next Steps After Testing

1. **All tests pass**: Deploy to production
2. **Some issues**: Check "Common Issues" section above
3. **Major problems**: Review implementation files
4. **Need features**: See "What's Next" in main summary doc

## 📞 Quick Help

**Backend endpoint not responding?**
→ Check `backend/main.py` line 11099

**Recommendations not showing?**
→ Check `mobile/lib/features/recommendations/presentation/widgets/recommendations_card.dart`

**Streaming not working?**
→ Check `mobile/lib/features/ai_chat/data/datasources/ai_chat_remote_data_source.dart`

**Need to regenerate code?**
→ `cd mobile && flutter pub run build_runner build --delete-conflicting-outputs`

