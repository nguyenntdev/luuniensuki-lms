# Quiz Screen Shimmer Loading Implementation

## Overview
Replaced CircularProgressIndicator with shimmer loading skeleton in quiz_screen.dart for a better user experience with content-aware loading states.

## Changes Made

### 1. Import Added
**File**: `lib/features/quiz/presentation/screens/quiz_screen.dart`
**Line**: 9

```dart
import '../../../../shared/widgets/shimmer/shimmer_skeleton.dart';
```

### 2. Loading State Replaced
**File**: `lib/features/quiz/presentation/screens/quiz_screen.dart`
**Lines**: 335-339

**Before**:
```dart
loading: () => const Center(
  child: CircularProgressIndicator(
    color: AppColors.primary,
  ),
),
```

**After**:
```dart
loading: () => _buildQuizShimmer(),
```

### 3. Shimmer Method Added
**File**: `lib/features/quiz/presentation/screens/quiz_screen.dart`
**Lines**: 425-498

Added `_buildQuizShimmer()` method that creates a shimmer skeleton matching the actual quiz layout:

```dart
Widget _buildQuizShimmer() {
  return SafeArea(
    child: Padding(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Progress bar shimmer
          ShimmerSkeleton(
            width: double.infinity,
            height: 8,
            borderRadius: BorderRadius.circular(4),
          ),
          const SizedBox(height: 16),
          // Question number shimmer
          ShimmerSkeleton(
            width: 120,
            height: 20,
            borderRadius: BorderRadius.circular(4),
          ),
          const SizedBox(height: 24),
          // Question text shimmer (2 lines)
          ShimmerSkeleton(
            width: double.infinity,
            height: 24,
            borderRadius: BorderRadius.circular(4),
          ),
          const SizedBox(height: 8),
          ShimmerSkeleton(
            width: MediaQuery.of(context).size.width * 0.7,
            height: 24,
            borderRadius: BorderRadius.circular(4),
          ),
          const SizedBox(height: 32),
          // Answer options shimmer (4 cards)
          Expanded(
            child: ListView.builder(
              itemCount: 4,
              itemBuilder: (context, index) => Padding(
                padding: const EdgeInsets.only(bottom: 12),
                child: ShimmerSkeleton(
                  width: double.infinity,
                  height: 60,
                  borderRadius: BorderRadius.circular(12),
                ),
              ),
            ),
          ),
          const SizedBox(height: 16),
          // Navigation buttons shimmer
          Row(
            children: [
              Expanded(
                child: ShimmerSkeleton(
                  width: double.infinity,
                  height: 48,
                  borderRadius: BorderRadius.circular(12),
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: ShimmerSkeleton(
                  width: double.infinity,
                  height: 48,
                  borderRadius: BorderRadius.circular(12),
                ),
              ),
            ],
          ),
        ],
      ),
    ),
  );
}
```

## Shimmer Components

The shimmer skeleton includes:

1. **Progress Bar** - 8px height shimmer at the top
2. **Question Number** - 120px width shimmer for "Câu 1/10" text
3. **Question Text** - 2 lines of shimmer (full width + 70% width)
4. **Answer Options** - 4 shimmer cards (60px height each)
5. **Navigation Buttons** - 2 shimmer buttons (48px height)

## Design Decisions

- Used `ShimmerSkeleton` widget from `shared/widgets/shimmer/shimmer_skeleton.dart`
- Layout matches actual quiz screen structure for seamless transition
- Border radius values match actual UI components (4px for text, 12px for buttons/cards)
- Consistent with other shimmer implementations in the app (explore_screen, collection_screen)

## Benefits

1. **Better UX** - Users see content-aware loading instead of generic spinner
2. **Reduced perceived loading time** - Shimmer gives visual feedback of upcoming content
3. **Consistency** - Matches shimmer pattern used in other screens
4. **Professional appearance** - Modern loading pattern seen in apps like Facebook, LinkedIn

## Testing Checklist

- [ ] Navigate to quiz screen from a motif
- [ ] Verify shimmer appears during quiz loading
- [ ] Confirm shimmer layout matches actual quiz layout
- [ ] Check shimmer animation is smooth
- [ ] Test on different screen sizes
- [ ] Verify no console errors or warnings

## File Changed

- `/mobile/lib/features/quiz/presentation/screens/quiz_screen.dart`

## Related Files

- `/mobile/lib/shared/widgets/shimmer/shimmer_skeleton.dart` - Shimmer component used
- `/mobile/lib/features/explore/presentation/screens/explore_screen.dart` - Similar shimmer implementation
- `/mobile/lib/features/collection/presentation/screens/collection_screen.dart` - Similar shimmer implementation

