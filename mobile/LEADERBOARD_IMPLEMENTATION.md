# Real Leaderboard Data Implementation

## Overview
Replaced hardcoded demo data in the Achievements screen with real API data fetching from the backend leaderboard endpoint.

## Changes Made

### 1. Created Data Model
**File:** `mobile/lib/features/achievements/data/models/leaderboard_dto.dart`

Simple DTO class without Freezed to avoid build_runner dependency:
- Maps API response fields to Dart properties
- Handles JSON serialization/deserialization
- Fields:
  - `rank`: User's position in leaderboard
  - `userId`: Unique user identifier
  - `displayName`: User's display name
  - `avatarUrl`: Optional profile picture URL
  - `totalXp`: Total experience points
  - `title`: User's rank title (e.g., "Beginner", "Expert")

### 2. Created Provider
**File:** `mobile/lib/features/achievements/presentation/providers/leaderboard_provider.dart`

StateNotifier-based provider for managing leaderboard state:
- Uses `AsyncValue<List<LeaderboardEntryDto>>` for loading/error/data states
- `loadLeaderboard()`: Fetches data from API endpoint
- `refresh()`: Convenience method to reload data
- Integrates with Dio provider for HTTP requests
- Supports pagination via `limit` parameter (default: 50)

### 3. Updated Achievements Screen
**File:** `mobile/lib/features/achievements/presentation/screens/achievements_screen.dart`

#### Key Updates:
1. **Imports**: Added auth and leaderboard provider imports
2. **Tab Listener**: Added logic to load leaderboard when tab is selected
3. **Replaced Demo Data**: Removed hardcoded array with provider watch
4. **Added UI States**:
   - **Loading**: Shows golden CircularProgressIndicator
   - **Error**: Displays error message with retry button
   - **Empty**: Shows message when no data available
   - **Data**: Renders leaderboard list

#### UI Enhancements:
- **Current User Highlighting**: Compares `userId` with authenticated user
- **Real Data Display**: Shows `displayName`, `totalXp`, and `title` from API
- **Title Display**: Changed from "Hạng {rank}" to user's actual title
- **Error Handling**: User-friendly error messages with retry functionality
- **Responsive Layout**: Added `Flexible` wrapper for text overflow

### 4. API Integration Details

**Endpoint:** `GET /api/v1/leaderboard`
**Query Parameters:**
- `limit` (optional): Maximum entries to return (default: 50)

**Response Format:**
```json
[
  {
    "rank": 1,
    "user_id": "uuid-string",
    "display_name": "User Name",
    "avatar_url": "https://...",
    "total_xp": 5420,
    "title": "Grand Master"
  },
  ...
]
```

## Testing Checklist

- [ ] Verify leaderboard loads when switching to tab
- [ ] Test loading state appears initially
- [ ] Test error state with network disconnected
- [ ] Test retry button in error state
- [ ] Verify current user is highlighted correctly
- [ ] Test with empty leaderboard (no users)
- [ ] Verify proper display of user titles
- [ ] Test XP values display correctly
- [ ] Check rank badges (gold/silver/bronze for top 3)
- [ ] Test scrolling with 50+ entries

## Future Enhancements

1. **Add Pull-to-Refresh**: Allow users to manually refresh leaderboard
2. **Add Pagination**: Load more entries as user scrolls
3. **Add Filtering**: Filter by time period (weekly, monthly, all-time)
4. **Add Avatar Support**: Display user avatars from `avatarUrl` field
5. **Add Caching**: Cache leaderboard data to reduce API calls
6. **Add Animations**: Smooth transitions when data loads
7. **Add Search**: Search for specific users in leaderboard

## Dependencies

No new dependencies were added. Uses existing:
- `flutter_riverpod`: State management
- `dio`: HTTP client (via existing provider)
- Standard Flutter widgets

## Notes

- Implementation avoids Freezed/build_runner to simplify setup
- Can be migrated to Freezed later if desired by running:
  ```bash
  cd mobile && flutter pub run build_runner build --delete-conflicting-outputs
  ```
- Provider uses `StateNotifier` instead of `@riverpod` annotation for simplicity
- Current implementation loads on tab selection; could be optimized to preload

