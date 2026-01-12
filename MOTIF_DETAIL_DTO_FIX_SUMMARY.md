# Motif Detail DTO Fix Summary

## Problem
The mobile app was crashing with "type null is not a subtype of type String" error when fetching motif details. This was due to a mismatch between the backend API response structure and the mobile DTO expectations.

## Root Causes

### Issue 1: urn_id vs urn object mismatch
- **Backend**: Returns `urn` as a nested object (UrnOut) containing id, slug, name, model_url, etc.
- **Mobile (old)**: Expected `urn_id` as a simple string field
- **Location**: `/api/v1/motifs/{motif_id}` endpoint (backend/main.py line 1633)

### Issue 2: Missing fields in LessonContentDto
- **Backend**: LessonContentOut does not include `id` and `motif_id` fields
- **Mobile (old)**: Required these fields as mandatory
- **Location**: backend/schemas.py line 175-183

## Changes Made

### 1. Added UrnInfoDto Class
Created a new DTO class to match the backend's nested urn object structure:

```dart
// File: mobile/lib/features/urn_viewer/data/models/urn_dtos.dart
@freezed
class UrnInfoDto with _$UrnInfoDto {
  const factory UrnInfoDto({
    required String id,
    required String slug,
    required String name,
    @JsonKey(name: 'model_url') String? modelUrl,
    @JsonKey(name: 'thumbnail_url') String? thumbnailUrl,
    String? description,
    @JsonKey(name: 'display_order') @Default(0) int displayOrder,
  }) = _UrnInfoDto;

  factory UrnInfoDto.fromJson(Map<String, dynamic> json) =>
      _$UrnInfoDtoFromJson(json);
}
```

### 2. Updated MotifDetailDto
Changed from `urn_id` string to `urn` object:

**Before:**
```dart
@JsonKey(name: 'urn_id') required String urnId,
```

**After:**
```dart
required UrnInfoDto urn,
```

### 3. Made LessonContentDto Fields Optional
Changed `id` and `motif_id` from required to optional:

**Before:**
```dart
required String id,
@JsonKey(name: 'motif_id') required String motifId,
```

**After:**
```dart
String? id,
@JsonKey(name: 'motif_id') String? motifId,
```

### 4. Updated Mapper
Changed the mapper to extract urn ID from the nested object:

**File**: `mobile/lib/features/urn_viewer/data/models/urn_mappers.dart`

**Before:**
```dart
urnId: urnId,
```

**After:**
```dart
urnId: urn.id,
```

## Files Modified

1. ✅ `mobile/lib/features/urn_viewer/data/models/urn_dtos.dart`
   - Added UrnInfoDto class (lines 86-101)
   - Updated MotifDetailDto to use UrnInfoDto instead of String urnId (line 108)
   - Made LessonContentDto id and motif_id optional (lines 133-134)

2. ✅ `mobile/lib/features/urn_viewer/data/models/urn_mappers.dart`
   - Updated MotifDetailDtoMapper to use urn.id instead of urnId (line 140)

## Next Steps - YOU MUST RUN THIS

### Run build_runner to regenerate code
The Freezed and JSON serialization code needs to be regenerated:

```bash
cd mobile
flutter pub run build_runner build --delete-conflicting-outputs
```

Or use the provided script:
```bash
cd mobile
./run_build_runner.sh
```

### Verify the fix
After running build_runner, the following should happen:
1. `urn_dtos.freezed.dart` will be regenerated with the new UrnInfoDto class
2. `urn_dtos.g.dart` will be regenerated with updated JSON serialization
3. The app should compile without errors
4. Fetching motif details should work without crashes

## Testing
Once the build is complete, test the fix:
1. Launch the app
2. Navigate to an urn viewer screen
3. Tap on a motif to view its details
4. Verify that the lesson content loads without crashes
5. Check that the urn information is properly displayed

## Backend Response Structure (for reference)
The API returns this structure for `/api/v1/motifs/{motif_id}`:

```json
{
  "id": "uuid",
  "urn": {
    "id": "uuid",
    "slug": "cao-dinh",
    "name": "Cao Đỉnh",
    "model_url": "https://...",
    "thumbnail_url": "https://...",
    "description": "...",
    "display_order": 0
  },
  "mesh_name": "mesh_name",
  "name": "Motif name",
  "category": "nature",
  "rarity": "common",
  "lesson": {
    "intro_text": "...",
    "description": "...",
    "historical_context": "...",
    "symbolism": "...",
    "fun_fact": "..."
  },
  "progress": {
    "status": "discovered",
    "xp_earned": 100
  }
}
```

## Impact
- ✅ Fixes the "type null is not a subtype of type String" crash
- ✅ Aligns mobile DTOs with backend response structure
- ✅ Makes the app compatible with the current backend API
- ✅ Provides access to full urn information (slug, name, model_url) not just ID

