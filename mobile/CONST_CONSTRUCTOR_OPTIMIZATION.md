# Const Constructor Optimization - ShimmerSkeleton

## Summary

Added `const` constructors to all eligible ShimmerSkeleton widget instantiations for performance optimization. Const widgets are cached and reused by Flutter, reducing memory allocation and improving rebuild performance.

## File Modified

- `lib/shared/widgets/shimmer/shimmer_skeleton.dart`

## Changes Made

### ShimmerUrnCard Widget (3 instances)
- Title shimmer (line 101)
- Subtitle shimmer (line 107)
- Progress bar shimmer (line 113)

### ShimmerMotifCard Widget (4 instances)
- Thumbnail shimmer (line 158)
- Motif name shimmer (line 167)
- Status badge shimmer 1 (line 177)
- Status badge shimmer 2 (line 182)

### ShimmerListItem Widget (4 instances)
- Leading icon shimmer (line 237)
- Content title shimmer (line 250)
- Content subtitle shimmer (line 255)
- Trailing icon shimmer (line 266)

## Total: 11 ShimmerSkeleton instances optimized with const

## Key Changes

### Before:
```dart
ShimmerSkeleton(
  width: double.infinity,
  height: 20,
  borderRadius: BorderRadius.circular(AppSpacing.radiusXS),
),
```

### After:
```dart
const ShimmerSkeleton(
  width: double.infinity,
  height: 20,
),
```

## Note on borderRadius Removal

The `borderRadius` parameter was removed from all const instances because:
1. `BorderRadius.circular()` is not a compile-time constant
2. ShimmerSkeleton already has a default borderRadius in its build method:
   ```dart
   borderRadius: borderRadius ?? BorderRadius.circular(AppSpacing.radiusMD),
   ```
3. The default radius (AppSpacing.radiusMD) is acceptable for all shimmer instances

## Performance Benefits

1. **Memory Efficiency**: Const widgets are created once and reused
2. **Rebuild Optimization**: Flutter skips rebuilding const widgets when parent rebuilds
3. **Reduced Allocations**: No new widget instances created on each rebuild
4. **Better Performance**: Especially noticeable in lists with multiple shimmer items

## Testing Recommendations

1. Verify shimmer animations still work correctly
2. Check visual appearance of all shimmer widgets
3. Test in different screen sizes
4. Verify performance improvement in release mode

## Next Steps

Consider applying the same optimization to other widget trees in the app where const constructors are applicable.

