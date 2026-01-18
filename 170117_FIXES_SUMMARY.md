# v1.6.7 Bug Fixes Summary

**Date:** January 17, 2025
**Build:** app-release-v1.6.7.apk (69.4MB)

## Issues Fixed

### 1. Badges Not Showing ✅

**Root Causes Found:**
- Backend field name mismatch: `xp_reward` vs `xp_bonus`
- Silent error swallowing in badge provider
- Missing debug logging

**Fixes Applied:**

| File | Change |
|------|--------|
| `backend/schemas.py` (line 446) | Changed `xp_reward` to `xp_bonus` in BadgeOut schema |
| `mobile/.../badge_provider.dart` | Added comprehensive debug logging with `[BadgeProvider]` prefix |
| `mobile/.../badge_provider.dart` | Added try-catch with logging for user badges fetch |
| `mobile/.../badge_provider.dart` | Logs cache hits, API requests, and badge counts |

### 2. 3D Model Viewer Loading ✅

**Root Causes Found:**
- 3-second safety timeout was too aggressive for 60-80MB model files
- Loading indicator disappeared while model still downloading

**Fixes Applied:**

| File | Change |
|------|--------|
| `mobile/.../custom_model_viewer.dart` | Increased timeout from 3s to 120s (2 minutes) |
| `mobile/.../custom_model_viewer.dart` | Timeout now logs warning instead of hiding loading indicator |
| `mobile/.../custom_model_viewer.dart` | Added debug logging with emojis (🚀📊✅⚠️) |

### 3. Images Not Loading on Learn/Practice Pages ✅

**Root Causes Found:**
- Mock fallback data had no `thumbnailUrl` field
- Silent error catching prevented debugging
- Double mock fallback masking real API issues

**Fixes Applied:**

| File | Change |
|------|--------|
| `mobile/.../practice_urns_provider.dart` | Added debug logging for API calls |
| `mobile/.../practice_urns_provider.dart` | Fixed mock data with valid thumbnail URLs |
| `mobile/.../daily_lessons_widget.dart` | Added `thumbnailUrl` to all mock lessons |
| `mobile/.../daily_lessons_widget.dart` | Added debug logging for lesson parsing |
| `mobile/.../practice_screen.dart` | Added `thumbnailUrl` to mock fallback data |

## Mock Data URLs

**FIXED IN v1.6.7:** Mock URLs now use correct URL-encoded Vietnamese filenames from database:
```
https://lms.histolab.icu/assets/ban-duc-noi/CAO%20DINH/CAO%20DINH.jpg
https://lms.histolab.icu/assets/ban-duc-noi/NHAN%20DINH/NH%C3%82N%20%C4%90%E1%BB%88NH.jpg  (NHÂN ĐỈNH)
https://lms.histolab.icu/assets/ban-duc-noi/CHUONG%20DINH/CH%C6%AF%C6%A0NG%20%C4%90%E1%BB%88NH.jpg  (CHƯƠNG ĐỈNH)
https://lms.histolab.icu/assets/ban-duc-noi/ANH%20DINH/ANH%20%C4%90%E1%BB%88NH.jpg  (ANH ĐỈNH)
```

Previous URLs used ASCII filenames (e.g., `NHAN%20DINH.jpg`) which returned 404.

## Files Modified

### Backend
- `backend/schemas.py` - Fixed xp_bonus field name

### Mobile
- `mobile/lib/features/achievements/presentation/providers/badge_provider.dart`
- `mobile/lib/features/urn_viewer/presentation/widgets/custom_model_viewer.dart`
- `mobile/lib/features/practice/presentation/providers/practice_urns_provider.dart`
- `mobile/lib/features/practice/presentation/screens/practice_screen.dart`
- `mobile/lib/features/learning_path/presentation/widgets/daily_lessons_widget.dart`

## Debug Logging Added

Look for these log prefixes when debugging:
- `[BadgeProvider]` - Badge loading issues
- `[CUSTOM_MODEL_VIEWER]` - 3D model loading (with emojis)
- `🔍 [PracticeUrns]` - Practice screen image loading
- `📖 [DailyLessons]` - Learn screen lesson loading

## Testing Checklist

- [ ] Open Achievements screen - badges should load
- [ ] Check console for `[BadgeProvider]` logs
- [ ] Open Urn Viewer - 3D model should load with progress
- [ ] Wait for large models - loading should NOT disappear after 3s
- [ ] Open Practice screen - urn cards should have thumbnails
- [ ] Open Learn screen - daily lessons should have thumbnails
- [ ] Test in airplane mode - mock data should show with images

## Next Steps if Issues Persist

1. **Badges still not showing:**
   - Deploy backend changes
   - Check authentication is working
   - Verify `/api/v1/badges` returns data

2. **3D models still not loading:**
   - Check network connectivity
   - Verify model URLs are accessible
   - Consider implementing download progress UI

3. **Images still not loading:**
   - Check API response format in console logs
   - Verify `thumbnail_url` field exists in response
   - Test image URLs directly in browser

