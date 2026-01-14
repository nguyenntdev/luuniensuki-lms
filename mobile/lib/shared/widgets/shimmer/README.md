# Shimmer Loading Skeletons

Shimmer loading skeletons để hiển thị loading states với trải nghiệm người dùng tốt hơn.

## Components

### 1. ShimmerSkeleton (Base Component)

Base component cho tất cả shimmer effects. Sử dụng `AppColors.surface` và `AppColors.surfaceElevated` để match với dark theme.

```dart
ShimmerSkeleton(
  width: 100,
  height: 20,
  borderRadius: BorderRadius.circular(8),
)
```

**Props:**
- `width`: Chiều rộng (optional)
- `height`: Chiều cao (optional)
- `borderRadius`: Bo góc (optional, default: `AppSpacing.radiusMD`)
- `margin`: Margin (optional)

### 2. ShimmerUrnCard

Shimmer skeleton cho UrnCard trong explore screen. Matches với thiết kế glass effect của UrnCard.

```dart
GridView.builder(
  itemCount: 9,
  itemBuilder: (context, index) {
    return const ShimmerUrnCard();
  },
)
```

**Use case:**
- Loading state trong explore screen
- Grid layout với aspect ratio 0.75
- Hiển thị 9 cards (số lượng urns)

### 3. ShimmerMotifCard

Shimmer skeleton cho MotifCard trong collection screen.

```dart
GridView.builder(
  itemCount: 8,
  itemBuilder: (context, index) {
    return const ShimmerMotifCard();
  },
)
```

**Use case:**
- Loading state trong collection screen
- Grid layout với aspect ratio 0.85
- Hiển thị placeholder cho motif cards

### 4. ShimmerListItem

Generic shimmer skeleton cho list items.

```dart
ShimmerListItem(
  showLeading: true,
  showTrailing: true,
  height: 70,
)
```

**Props:**
- `showLeading`: Hiển thị leading icon/image (default: true)
- `showTrailing`: Hiển thị trailing icon (default: true)
- `height`: Chiều cao của item (default: 70)

**Use case:**
- Loading state cho lists
- Settings screens
- Search results

## Usage Examples

### Explore Screen Loading State

```dart
Widget _buildLoadingState() {
  return LayoutBuilder(
    builder: (context, constraints) {
      int crossAxisCount = 2;
      if (constraints.maxWidth > 600) crossAxisCount = 3;
      if (constraints.maxWidth > 900) crossAxisCount = 4;

      return GridView.builder(
        gridDelegate: SliverGridDelegateWithFixedCrossAxisCount(
          crossAxisCount: crossAxisCount,
          childAspectRatio: 0.75,
          crossAxisSpacing: AppSpacing.md,
          mainAxisSpacing: AppSpacing.md,
        ),
        itemCount: 9,
        itemBuilder: (context, index) => const ShimmerUrnCard(),
      );
    },
  );
}
```

### Collection Screen Loading State

```dart
Widget _buildLoadingState() {
  return GridView.builder(
    gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
      crossAxisCount: 2,
      childAspectRatio: 0.85,
      crossAxisSpacing: 12,
      mainAxisSpacing: 12,
    ),
    itemCount: 8,
    itemBuilder: (context, index) => const ShimmerMotifCard(),
  );
}
```

### Image Placeholder

```dart
CachedNetworkImage(
  imageUrl: imageUrl,
  placeholder: (context, url) => const ShimmerSkeleton(
    width: double.infinity,
    height: double.infinity,
  ),
)
```

## Design Principles

1. **Color Matching**: Sử dụng `AppColors.surface` và `AppColors.surfaceElevated` để match với dark theme
2. **Structure Matching**: Shimmer skeleton phải match với structure thực tế của component
3. **Glass Effect**: UrnCard và MotifCard có glass effect giống như component thực
4. **Responsive**: Shimmer skeletons responsive giống như component thực

## Migration from CircularProgressIndicator

### Before
```dart
if (state.isLoading) {
  return const Center(
    child: CircularProgressIndicator(
      color: AppColors.primary,
    ),
  );
}
```

### After
```dart
if (state.isLoading) {
  return GridView.builder(
    itemCount: 9,
    itemBuilder: (context, index) => const ShimmerUrnCard(),
  );
}
```

## Files Changed

1. ✅ `mobile/lib/shared/widgets/shimmer/shimmer_skeleton.dart` - Created
2. ✅ `mobile/lib/shared/widgets/shimmer/index.dart` - Created
3. ✅ `mobile/lib/features/explore/presentation/screens/explore_screen.dart` - Updated
4. ✅ `mobile/lib/features/collection/presentation/screens/collection_screen.dart` - Updated

