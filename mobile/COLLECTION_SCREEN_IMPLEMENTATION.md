# Collection Screen Implementation Summary

## Changes Made

### 1. Added API Endpoint Constant
**File:** `mobile/lib/core/constants/api_constants.dart`
- Added `userCollection = '$apiPath/users/me/collection'` constant

### 2. Created Collection Data Models
**File:** `mobile/lib/features/collection/data/models/collection_dtos.dart`
- Created `CollectionStatsDto` with total, discovered, learned, mastered counts
- Created `CollectionMotifDto` with all motif fields matching API response
- Created `CollectionResponseDto` combining stats and motifs list
- All models use Freezed for immutability and JSON serialization

### 3. Created Collection Provider
**File:** `mobile/lib/features/collection/presentation/providers/collection_provider.dart`
- Implemented `CollectionState` with collection data, loading, error states
- Created `CollectionNotifier` using riverpod_annotation
- Added `loadCollection()` method to fetch from API
- Added `refreshCollection()` for pull-to-refresh support
- Includes proper error handling with Vietnamese error messages

### 4. Updated Collection Screen
**File:** `mobile/lib/features/collection/presentation/screens/collection_screen.dart`
- Added imports for collection DTOs and provider
- Added `initState` to load collection on screen creation
- Updated `_buildContent()` to:
  - Show loading spinner when fetching data
  - Show error state with retry button on failure
  - Show empty state when no motifs discovered
  - Show motif grid when data is available
- Added `_filterMotifs()` to filter by status (all/discovered/learned/mastered)
- Updated `_buildMotifGrid()` to use `CollectionMotifDto` type
- Updated `_buildMotifCard()` to use typed motif data

### 5. Fixed Profile Screen Discovered Count
**File:** `mobile/lib/features/profile/presentation/screens/profile_screen.dart`
- Added import for `collectionNotifierProvider`
- Updated `_buildStatsGrid()` to accept `WidgetRef ref` parameter
- Changed discovered count from `totalXp ~/ 25` to actual `collection.stats.discovered`
- Now shows real collection data instead of estimated value

## API Integration

### Endpoint Used
```
GET /api/v1/users/me/collection
```

### Response Structure
```json
{
  "stats": {
    "total": 162,
    "discovered": 45,
    "learned": 23,
    "mastered": 12
  },
  "motifs": [
    {
      "id": "uuid",
      "slug": "motif-slug",
      "name": "Họa tiết name",
      "category": "geometric",
      "rarity": "common",
      "thumbnail_url": "url",
      "status": "discovered",
      "urn_id": "uuid",
      "urn_slug": "urn-slug",
      "urn_name": "Urn name",
      "discovered_at": "2024-01-01T00:00:00Z",
      "learned_at": null,
      "mastered_at": null
    }
  ]
}
```

## Features Implemented

1. **Loading State** - Shows spinner while fetching collection data
2. **Error Handling** - Shows error message with retry button
3. **Empty State** - Shows when user has no discovered motifs
4. **Filtering** - Can filter by all/discovered/learned/mastered status
5. **Real Data** - Profile screen now shows actual discovered count
6. **Type Safety** - All models are properly typed using Freezed

## Generated Files
- `mobile/lib/features/collection/data/models/collection_dtos.freezed.dart`
- `mobile/lib/features/collection/data/models/collection_dtos.g.dart`
- `mobile/lib/features/collection/presentation/providers/collection_provider.g.dart`

## Testing Checklist

- [ ] Collection screen loads and shows spinner initially
- [ ] Collection screen shows motifs after loading
- [ ] Empty state appears when no motifs discovered
- [ ] Filter chips work (all/discovered/learned/mastered)
- [ ] Error state shows with retry button on network failure
- [ ] Profile screen shows correct discovered count
- [ ] Tapping motif card navigates to motif detail
- [ ] Collection count in profile matches collection screen

## Notes

- The JsonKey annotation warnings from the analyzer are false positives and can be ignored
- They occur because Freezed generates the actual getters at build time
- The code compiles and runs correctly despite the warnings

