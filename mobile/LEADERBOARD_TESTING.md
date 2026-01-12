# Testing the Leaderboard Implementation

## Prerequisites
1. Ensure backend API is running and accessible
2. Have at least one user account with some XP
3. Mobile app is authenticated

## Quick Test Steps

### 1. Basic Functionality Test
```bash
# Run the mobile app
cd mobile
flutter run
```

1. Login to the app
2. Navigate to the Achievements screen (bottom navigation)
3. Switch to the "Xếp Hạng" (Leaderboard) tab
4. Verify:
   - Loading indicator appears
   - Leaderboard data loads from API
   - Current user is highlighted with gold accent
   - User's title displays correctly (not "Hạng {rank}")

### 2. Error Handling Test

#### Offline Test:
1. Disconnect from network
2. Switch to Leaderboard tab
3. Verify error message appears
4. Tap "Thử lại" (Retry) button
5. Reconnect network
6. Verify data loads successfully

#### API Error Test:
1. Stop backend server
2. Switch to Leaderboard tab
3. Verify error message with details
4. Restart backend
5. Use retry button to reload

### 3. Edge Cases

#### Empty Leaderboard:
1. Use a fresh database with no users
2. Verify empty state message appears

#### Current User Detection:
1. Check that your user has gold highlighting
2. Verify "Bạn" badge appears next to your name
3. Try with different users to confirm correct matching

### 4. Performance Test
1. Create 50+ users with varying XP
2. Verify all users load correctly
3. Check smooth scrolling
4. Verify top 3 users have proper rank badges

## Expected Behavior

### Loading State
- Golden CircularProgressIndicator
- Centered on screen

### Error State
- Error icon (outlined)
- Vietnamese error message
- Error details shown
- "Thử lại" button with golden styling

### Empty State
- Leaderboard icon
- "Chưa có dữ liệu" message
- Helpful description

### Data Display
- Rank badge (trophy icon for top 3, number for others)
- User avatar (first letter of name for now)
- Display name
- User title (from API, not hardcoded "Hạng X")
- Total XP with star icon
- Current user highlighted with golden accent

## API Endpoint Details

**Endpoint:** `GET /api/v1/leaderboard`
**Parameters:** `?limit=50`

**Sample cURL:**
```bash
curl -X GET "https://lms.histolab.icu/api/v1/leaderboard?limit=50" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Expected Response:**
```json
[
  {
    "rank": 1,
    "user_id": "some-uuid",
    "display_name": "Top User",
    "avatar_url": null,
    "total_xp": 5000,
    "title": "Grand Master"
  }
]
```

## Common Issues

### Issue: "command not found: flutter"
**Solution:** Install Flutter SDK or use proper environment

### Issue: Build errors about missing .g.dart files
**Solution:** These files are not needed - the implementation uses plain classes

### Issue: Leaderboard always shows loading
**Solution:** 
- Check network connectivity
- Verify backend API is running
- Check authentication token is valid

### Issue: Current user not highlighted
**Solution:**
- Verify user is logged in
- Check user_id matching logic
- Ensure API returns correct user_id

## Debugging

### Enable detailed logging:
```dart
// In leaderboard_provider.dart, add print statements:
print('Loading leaderboard...');
print('Response: $data');
print('Entries: ${entries.length}');
```

### Check Dio logs:
The app already has LoggingInterceptor in debug mode.
Check console for HTTP request/response details.

## Next Steps

After successful testing, consider:
1. Adding pull-to-refresh
2. Implementing pagination
3. Adding user avatar images
4. Adding search functionality
5. Adding time-based filters (weekly/monthly)

