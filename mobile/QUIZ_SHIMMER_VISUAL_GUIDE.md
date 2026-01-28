# Quiz Screen Shimmer Loading - Visual Guide

## Before & After Comparison

### Before: CircularProgressIndicator
```
┌─────────────────────────────────┐
│         Quiz Screen             │
│                                 │
│                                 │
│             ⟳                   │
│        [Spinner]                │
│                                 │
│                                 │
│                                 │
└─────────────────────────────────┘
```

**Issues:**
- Generic loading indicator
- No context about what's loading
- Doesn't match the actual content layout
- Higher perceived loading time

---

### After: Shimmer Skeleton Loading
```
┌─────────────────────────────────┐
│         Quiz Screen             │
├─────────────────────────────────┤
│ ▓▓▓▓▓▓▓▓▒▒▒▒▒▒▒▒░░░░░░░░░░      │ ← Progress bar shimmer
│                                 │
│ ▓▓▓▓▓▒▒▒░░                      │ ← Question number (Câu 1/10)
│                                 │
│ ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▒▒▒░░    │ ← Question text line 1
│ ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▒▒▒░░            │ ← Question text line 2
│                                 │
│ ┌─────────────────────────────┐ │
│ │ ▓▓▓▓▓▓▓▓▓▓▓▒▒▒▒▒░░░         │ │ ← Answer option 1
│ └─────────────────────────────┘ │
│                                 │
│ ┌─────────────────────────────┐ │
│ │ ▓▓▓▓▓▓▓▓▓▓▓▒▒▒▒▒░░░         │ │ ← Answer option 2
│ └─────────────────────────────┘ │
│                                 │
│ ┌─────────────────────────────┐ │
│ │ ▓▓▓▓▓▓▓▓▓▓▓▒▒▒▒▒░░░         │ │ ← Answer option 3
│ └─────────────────────────────┘ │
│                                 │
│ ┌─────────────────────────────┐ │
│ │ ▓▓▓▓▓▓▓▓▓▓▓▒▒▒▒▒░░░         │ │ ← Answer option 4
│ └─────────────────────────────┘ │
│                                 │
│ ┌──────────┐   ┌──────────────┐ │
│ │ ▓▓▓▓▓▒▒░ │   │ ▓▓▓▓▓▓▒▒▒░░ │ │ ← Navigation buttons
│ └──────────┘   └──────────────┘ │
└─────────────────────────────────┘

Legend: ▓ = Dark shimmer, ▒ = Medium shimmer, ░ = Light shimmer
```

**Benefits:**
- Content-aware loading
- Shows exact layout of upcoming content
- Smooth animated shimmer effect
- Reduced perceived loading time
- Professional, modern appearance

---

## Shimmer Components Breakdown

### 1. Progress Bar (Top)
- **Width**: Full width
- **Height**: 8px
- **Border Radius**: 4px
- **Purpose**: Shows quiz progress indicator placeholder

### 2. Question Number
- **Width**: 120px
- **Height**: 20px
- **Border Radius**: 4px
- **Purpose**: Placeholder for "Câu 1/10" text

### 3. Question Text (Multi-line)
- **Line 1**: Full width, 24px height
- **Line 2**: 70% width, 24px height
- **Border Radius**: 4px
- **Purpose**: Shows question text placeholder

### 4. Answer Options (4 cards)
- **Width**: Full width
- **Height**: 60px each
- **Border Radius**: 12px
- **Spacing**: 12px bottom margin
- **Purpose**: Placeholder for answer choices

### 5. Navigation Buttons (Row)
- **Layout**: 2 buttons in a row
- **Height**: 48px each
- **Border Radius**: 12px
- **Spacing**: 12px between buttons
- **Purpose**: Placeholder for Previous/Next buttons

---

## Animation Flow

```
State 1: Loading starts
    ↓
    Quiz data is fetched
    ↓
    Shimmer skeleton appears
    ▓▓▓▓▓▓▓▓▒▒▒▒▒▒▒▒░░░░░░░░
    ↓
    Shimmer animation continues
    ░░▓▓▓▓▓▓▒▒▒▒▒▒▒▒░░░░░░░░
    ↓
    Data arrives
    ↓
    Fade transition to actual content
    ↓
State 2: Quiz content displayed
```

---

## Code Structure

```dart
Widget _buildQuizShimmer() {
  return SafeArea(
    child: Padding(
      padding: const EdgeInsets.all(16),
      child: Column(
        children: [
          // 1. Progress bar shimmer
          ShimmerSkeleton(...),
          
          // 2. Question number shimmer
          ShimmerSkeleton(...),
          
          // 3. Question text shimmer (2 lines)
          ShimmerSkeleton(...),
          ShimmerSkeleton(...),
          
          // 4. Answer options (ListView)
          Expanded(
            child: ListView.builder(
              itemCount: 4,
              itemBuilder: (context, index) => ShimmerSkeleton(...),
            ),
          ),
          
          // 5. Navigation buttons (Row)
          Row(
            children: [
              Expanded(child: ShimmerSkeleton(...)),
              Expanded(child: ShimmerSkeleton(...)),
            ],
          ),
        ],
      ),
    ),
  );
}
```

---

## User Experience Impact

### Loading Time Perception
- **Before**: Users see blank screen with spinner → feels slow
- **After**: Users see content structure immediately → feels faster

### Visual Continuity
- **Before**: Jarring transition from spinner to content
- **After**: Smooth fade from shimmer to actual quiz

### Professional Appearance
- **Before**: Basic, generic loading state
- **After**: Modern, polished loading experience

---

## Related Implementations

This shimmer pattern is consistent with:
- `explore_screen.dart` - ShimmerUrnCard for URN cards
- `collection_screen.dart` - ShimmerMotifCard for motif cards
- Other screens using shimmer loading states

All use the same `ShimmerSkeleton` component from:
`lib/shared/widgets/shimmer/shimmer_skeleton.dart`

