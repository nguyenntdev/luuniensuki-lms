# Version 1.4.0 Commit Summary

## Commit Hash
`d789ffd279a102be14c02c2c675a0dbb3884500c`

## Commit Message
```
fix(mobile): Fix motif images, detail DTO, explore race condition, navbar width (v1.4.0)
```

## Summary
Successfully committed all changes for version 1.4.0 with 74 files changed, 34,823 insertions(+), and 73 deletions(-).

---

## Bug Fixes Included

### 1. Collection Screen - Motif Images
- **Problem**: Hardcoded placeholder icon instead of actual motif thumbnails
- **Solution**: Replace placeholder with CachedNetworkImage to load from API
- **File**: `mobile/lib/features/collection/presentation/screens/collection_screen.dart`

### 2. Motif Detail Error
- **Problem**: "type null is not a subtype of type String" error
- **Root Cause**: Backend sends nested `urn` object, not `urn_id` string
- **Solutions**:
  - Created new `UrnInfoDto` class to match backend structure
  - Changed `MotifDetailDto.urn_id: String` → `urn: UrnInfoDto`
  - Made `LessonContentDto.id` and `motif_id` optional (backend doesn't send them)
- **Files**:
  - `mobile/lib/features/urn_viewer/data/models/urn_dtos.dart`
  - `mobile/lib/features/urn_viewer/data/mappers/urn_mappers.dart`
  - Generated files: `.freezed.dart`, `.g.dart`

### 3. Explore Screen Blank
- **Problem**: Race condition with auth state causing blank screen
- **Solutions**:
  - Added `fireImmediately: true` to `ref.listenManual`
  - Properly storing and disposing `ProviderSubscription`
  - Ensures `loadUrns()` is called regardless of auth timing
- **File**: `mobile/lib/features/explore/presentation/screens/explore_screen.dart`

### 4. Navbar Indicator Width
- **Problem**: Gold indicator pill too narrow
- **Solution**: Widened from 50% to 70% of item width
- **File**: `mobile/lib/shared/widgets/glass/glass_bottom_nav.dart`

---

## Version Update
- **pubspec.yaml**: Version bumped to `1.4.0+5`

---

## Documentation Added
Comprehensive documentation and testing guides:
- `COLLECTION_DTO_FIX_SUMMARY.md`
- `EXPLORE_SCREEN_FIX_*` (multiple files)
- `MOTIF_DETAIL_DTO_FIX_SUMMARY.md`
- `MOTIF_DTO_FIX_*.md`
- Various mobile UI/UX and implementation guides

---

## Builds Included
- `builds/luuniensuki-lms-v1.4.0-build5.apk`
- Historical builds: v1.1.0, v1.2.0, v1.3.0

---

## Statistics
- **74 files changed**
- **34,823 insertions(+)**
- **73 deletions(-)**

---

## How to Push
```bash
git push origin android-app
```

## Previous Version
- v1.3.0+4: Collection DTO, leaderboard, navbar alignment, auth improvements

