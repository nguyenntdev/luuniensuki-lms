# DTO Fix - Action Required Checklist

## ✅ Completed Changes

- [x] Created new `UrnInfoDto` class to match backend's nested urn object
- [x] Updated `MotifDetailDto` to use `UrnInfoDto urn` instead of `String urnId`
- [x] Made `LessonContentDto` fields (`id`, `motif_id`) optional
- [x] Updated `MotifDetailDtoMapper` to use `urn.id` instead of `urnId`

## ⚠️ ACTION REQUIRED - Run Build Runner

You **MUST** run the build runner to regenerate the Freezed and JSON serialization code:

```bash
cd mobile
flutter pub run build_runner build --delete-conflicting-outputs
```

Or use the script:
```bash
cd mobile
./run_build_runner.sh
```

## Expected Output

When you run build_runner, you should see:
```
[INFO] Generating build script...
[INFO] Generating build script completed, took 293ms
[INFO] Creating build script snapshot......
[INFO] Creating build script snapshot... completed, took 10.4s
[INFO] Building new asset graph...
[INFO] Building new asset graph completed, took 1.1s
[INFO] Checking for unexpected pre-existing outputs.
[INFO] Deleting 2 declared outputs which already existed on disk.
[INFO] Running build...
[INFO] 1.2s elapsed, 0/3 actions completed.
[INFO] 4.5s elapsed, 2/3 actions completed.
[INFO] Running build completed, took 4.7s
[INFO] Caching finalized dependency graph...
[INFO] Caching finalized dependency graph completed, took 45ms
[INFO] Succeeded after 4.8s with 2 outputs
```

## Files That Will Be Regenerated

1. `mobile/lib/features/urn_viewer/data/models/urn_dtos.freezed.dart`
   - Will include the new `_$UrnInfoDto` class
   - Will update `_$MotifDetailDto` to use UrnInfoDto

2. `mobile/lib/features/urn_viewer/data/models/urn_dtos.g.dart`
   - Will add `_$UrnInfoDtoFromJson` function
   - Will update `_$MotifDetailDtoFromJson` to handle the urn object
   - Will update `_$LessonContentDtoFromJson` for optional fields

## Verification Steps

After running build_runner:

1. **Check compilation**:
   ```bash
   cd mobile
   flutter analyze
   ```
   Should show no errors related to urn_dtos

2. **Run the app**:
   ```bash
   flutter run
   ```

3. **Test the fix**:
   - Navigate to an urn viewer
   - Tap on a motif
   - Verify the lesson screen loads without crashing
   - Check console for any errors

## If You Get Errors

If build_runner fails with conflicts:
```bash
cd mobile
flutter clean
flutter pub get
flutter pub run build_runner build --delete-conflicting-outputs
```

## Summary

**What was fixed**: 
- Motif Detail DTO now matches backend API response structure
- Backend sends `urn` as object, not `urn_id` as string
- LessonContent doesn't require `id` and `motif_id` fields

**Why it's needed**:
- Prevents "type null is not a subtype of type String" crash
- Allows proper JSON deserialization of motif details

**Next step**: 
- Run build_runner (command above)
- Test the app

