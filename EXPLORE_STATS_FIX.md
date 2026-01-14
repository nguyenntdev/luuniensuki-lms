# Fix for Explore Screen Statistics

## Problem
The Explore screen was showing incorrect statistics (all zeros for discovered/learned/mastered counts) because:
- The `/api/v1/urns` endpoint does NOT return `discovered_count`, `learned_count`, `mastered_count` fields
- The mobile app was defaulting these values to 0 in the `Urn.fromJson()` method

## Solution
Use the `/api/v1/dashboard/summary` endpoint which DOES return correct progress statistics in its `collection_stats` field.

## Changes Made

### 1. Updated API Constants
**File**: `mobile/lib/core/constants/api_constants.dart`
- Added `dashboardSummary` constant pointing to `/api/v1/dashboard/summary`

### 2. Updated Explore Provider
**File**: `mobile/lib/features/explore/presentation/providers/explore_provider.dart`

#### Added CollectionStats class
```dart
class CollectionStats {
  final int total;
  final int discovered;
  final int learned;
  final int mastered;
  
  factory CollectionStats.fromJson(Map<String, dynamic> json) { ... }
}
```

#### Updated ExploreState
- Added `collectionStats` field to store the statistics from dashboard summary
- Updated `copyWith` method to include the new field

#### Updated loadUrns() method
- After loading urns, also fetches dashboard summary
- Extracts `collection_stats` from the response
- Stores it in the state
- Gracefully handles errors (continues even if stats fail to load)

#### Updated refreshUrns() method
- Also refreshes collection stats when pulling to refresh
- Keeps existing stats if refresh fails

#### Updated exploreProgress provider
- **Primary source**: Uses `collectionStats` from dashboard summary if available
- **Fallback**: Falls back to summing from urns (which will show 0s but prevents crashes)

## How It Works

1. When the Explore screen loads, it calls `loadUrns()`
2. This fetches both:
   - Urns list from `/api/v1/urns`
   - Collection stats from `/api/v1/dashboard/summary`
3. The `exploreProgress` provider checks for `collectionStats` first
4. If available, it uses those values (which are correct)
5. Otherwise, it falls back to the old method (summing from urns)

## API Response Structure

The dashboard summary endpoint returns:
```json
{
  "urns": [...],
  "collection_stats": {
    "total": 162,
    "discovered": 5,
    "learned": 2,
    "mastered": 1
  },
  "streak": {...},
  "quest_summary": {...},
  ...
}
```

## Testing

To verify the fix:
1. Launch the app
2. Navigate to Explore screen
3. Check the statistics header shows correct values for:
   - Discovered count
   - Learned count
   - Mastered count
4. Pull to refresh and verify stats update correctly
5. Check debug logs for messages like:
   - `[EXPLORE] Fetching collection stats from dashboard summary...`
   - `[EXPLORE] Collection stats loaded: discovered=X, learned=Y, mastered=Z`

## Backward Compatibility

The implementation maintains backward compatibility:
- If dashboard summary fails to load, the app continues to work
- Falls back to calculating from urns (will show 0s as before)
- No breaking changes to existing code

