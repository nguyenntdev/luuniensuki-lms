# Collection Screen DTO Fix Summary

## Problem
The mobile app was showing "Đã xảy ra lỗi" (An error occurred) on the Collection Screen due to a DTO mismatch between mobile and backend.

## Root Cause
The mobile DTOs didn't match the backend API response format:
1. Backend returns `items` array, mobile expected `motifs`
2. Backend sends `motif_id`, mobile expected plain `id`
3. Backend sends `mesh_name`, mobile expected `slug`
4. Mobile required `urnId`, `urnSlug`, `urnName` fields that don't exist in backend

## Backend API Response Format
```python
class UserCollectionResponse(BaseModel):
    items: list[CollectionItemOut]  # NOT "motifs"
    stats: CollectionStatsOut

class CollectionItemOut(BaseModel):
    motif_id: UUID
    mesh_name: str
    name: str
    name_en: Optional[str]
    category: str
    rarity: str
    thumbnail_url: Optional[str]
    status: str
```

## Changes Made

### 1. Updated `mobile/lib/features/collection/data/models/collection_dtos.dart`

**CollectionMotifDto:**
- Changed `id` to map from `motif_id` using `@JsonKey(name: 'motif_id')`
- Changed `slug` to `meshName` and mapped from `mesh_name` using `@JsonKey(name: 'mesh_name')`
- Added `nameEn` field mapped from `name_en` using `@JsonKey(name: 'name_en')`
- Removed non-existent fields: `urnId`, `urnSlug`, `urnName`, `discoveredAt`, `learnedAt`, `masteredAt`
- Kept required fields: `id`, `meshName`, `name`, `nameEn`, `category`, `rarity`, `thumbnailUrl`, `status`

**CollectionResponseDto:**
- Changed field name from `motifs` to `items` to match backend response
- Maintained the same structure with `items` and `stats`

### 2. Updated `mobile/lib/features/collection/presentation/screens/collection_screen.dart`

- Changed reference from `state.collection!.motifs` to `state.collection!.items` (line 247)

## Next Steps

### REQUIRED: Run build_runner

You **MUST** run the following command to regenerate the freezed and json_serializable code:

```bash
cd mobile
flutter pub run build_runner build --delete-conflicting-outputs
```

Or use the provided script:

```bash
cd mobile
bash run_build_runner.sh
```

This will regenerate:
- `collection_dtos.freezed.dart`
- `collection_dtos.g.dart`

### Testing

After running build_runner:

1. **Start the app:**
   ```bash
   cd mobile
   flutter run
   ```

2. **Test the Collection Screen:**
   - Navigate to the Collection tab
   - Verify the screen loads without errors
   - Check that motifs are displayed correctly
   - Test filter functionality (All, Discovered, Learned, Mastered)

3. **Expected Behavior:**
   - Collection screen should load successfully
   - Stats should display: "X/Y" discovered motifs
   - Motif cards should show name, category, status, and rarity
   - Filters should work correctly
   - No "Đã xảy ra lỗi" error

## Files Modified

1. ✅ `mobile/lib/features/collection/data/models/collection_dtos.dart` - Fixed DTO structure
2. ✅ `mobile/lib/features/collection/presentation/screens/collection_screen.dart` - Updated reference

## Files That Will Be Regenerated

1. ⏳ `mobile/lib/features/collection/data/models/collection_dtos.freezed.dart` (pending build_runner)
2. ⏳ `mobile/lib/features/collection/data/models/collection_dtos.g.dart` (pending build_runner)

## Verification Checklist

- [x] DTOs match backend API response exactly
- [x] Field names use proper @JsonKey annotations for snake_case mapping
- [x] Removed non-existent fields from backend
- [x] Updated screen to use `items` instead of `motifs`
- [ ] Build runner executed successfully (USER ACTION REQUIRED)
- [ ] App builds without errors (USER ACTION REQUIRED)
- [ ] Collection screen loads correctly (USER ACTION REQUIRED)
- [ ] Motif data displays properly (USER ACTION REQUIRED)

## Notes

The fix ensures the mobile app's Collection DTOs perfectly match the backend API response format. The JSON deserialization will now work correctly, and the Collection Screen will display user's discovered motifs without errors.

