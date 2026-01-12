# Motif Detail DTO Fix - Before & After Comparison

## Change 1: New UrnInfoDto Class

### ADDED (NEW)
```dart
/// URN info DTO (nested in motif detail response)
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

## Change 2: MotifDetailDto Field

### BEFORE
```dart
@freezed
class MotifDetailDto with _$MotifDetailDto {
  const factory MotifDetailDto({
    required String id,
    @JsonKey(name: 'urn_id') required String urnId,  // ❌ OLD: String
    @JsonKey(name: 'mesh_name') required String meshName,
    // ... rest of fields
  }) = _MotifDetailDto;
}
```

### AFTER
```dart
@freezed
class MotifDetailDto with _$MotifDetailDto {
  const factory MotifDetailDto({
    required String id,
    required UrnInfoDto urn,  // ✅ NEW: Object
    @JsonKey(name: 'mesh_name') required String meshName,
    // ... rest of fields
  }) = _MotifDetailDto;
}
```

## Change 3: LessonContentDto Fields

### BEFORE
```dart
@freezed
class LessonContentDto with _$LessonContentDto {
  const factory LessonContentDto({
    required String id,                          // ❌ OLD: Required
    @JsonKey(name: 'motif_id') required String motifId,  // ❌ OLD: Required
    @JsonKey(name: 'intro_text') String? introText,
    // ... rest of fields
  }) = _LessonContentDto;
}
```

### AFTER
```dart
@freezed
class LessonContentDto with _$LessonContentDto {
  const factory LessonContentDto({
    String? id,                                  // ✅ NEW: Optional
    @JsonKey(name: 'motif_id') String? motifId,  // ✅ NEW: Optional
    @JsonKey(name: 'intro_text') String? introText,
    // ... rest of fields
  }) = _LessonContentDto;
}
```

## Change 4: Mapper Update

### BEFORE (urn_mappers.dart)
```dart
extension MotifDetailDtoMapper on MotifDetailDto {
  Motif toEntity() {
    return Motif(
      id: id,
      urnId: urnId,  // ❌ OLD: Direct field access
      meshName: meshName,
      // ... rest of fields
    );
  }
}
```

### AFTER (urn_mappers.dart)
```dart
extension MotifDetailDtoMapper on MotifDetailDto {
  Motif toEntity() {
    return Motif(
      id: id,
      urnId: urn.id,  // ✅ NEW: Access through object
      meshName: meshName,
      // ... rest of fields
    );
  }
}
```

## Backend API Response Structure

What the backend actually sends at `/api/v1/motifs/{id}`:

```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "urn": {                           // ✅ Nested object
    "id": "456e7890-e89b-12d3-a456-426614174001",
    "slug": "cao-dinh",
    "name": "Cao Đỉnh",
    "model_url": "https://lms.histolab.icu/assets/models/CAO-DINH-v1.glb",
    "thumbnail_url": "https://lms.histolab.icu/assets/thumbnails/cao-dinh.jpg",
    "description": "...",
    "display_order": 1
  },
  "mesh_name": "Dragon_Head",
  "name": "Đầu rồng",
  "category": "animal",
  "rarity": "legendary",
  "lesson": {                        // ✅ No id/motif_id fields
    "intro_text": "...",
    "description": "...",
    "historical_context": "...",
    "symbolism": "...",
    "fun_fact": "..."
  }
}
```

## Summary

| Aspect | Before | After | Reason |
|--------|--------|-------|--------|
| MotifDetailDto.urn | `String urnId` | `UrnInfoDto urn` | Backend sends object, not string |
| LessonContentDto.id | `required` | `optional` | Backend doesn't include this field |
| LessonContentDto.motifId | `required` | `optional` | Backend doesn't include this field |
| Mapper access | `urnId` | `urn.id` | Changed to access nested object |

## Benefits

1. ✅ **Prevents crash**: No more "type null is not a subtype of type String"
2. ✅ **More data**: Access to urn slug, name, model_url, not just ID
3. ✅ **API alignment**: Mobile DTOs now match backend response structure
4. ✅ **Future-proof**: Can access additional urn fields if needed

