# UrnCard Accessibility - Quick Reference

## Quick Implementation Guide

### What Was Changed

**Before** (Lines 94-100):
```dart
return GestureDetector(
  onTapDown: (_) => setState(() => _isPressed = true),
  onTapUp: (_) {
    setState(() => _isPressed = false);
    widget.onTap?.call();
  },
  ...
```

**After** (Lines 94-105):
```dart
return Semantics(
  button: true,
  enabled: widget.onTap != null,
  label: _buildSemanticLabel(),
  child: GestureDetector(
    onTapDown: (_) => setState(() => _isPressed = true),
    onTapUp: (_) {
      setState(() => _isPressed = false);
      widget.onTap?.call();
    },
    ...
```

### New Helper Method (Lines 195-205)

```dart
String _buildSemanticLabel() {
  final urn = widget.urn;
  final discovered = urn.discoveredCount;
  final total = urn.motifCount;
  final progress = (urn.progressPercent * 100).round();
  
  return '${urn.name}. '
      '$discovered trên $total họa tiết đã khám phá. '
      'Tiến độ $progress phần trăm. '
      'Nhấn đúp để xem chi tiết.';
}
```

## Visual Flow

```
┌─────────────────────────────────────────┐
│ Semantics Widget (Accessibility Layer) │
│                                         │
│ button: true                            │
│ enabled: widget.onTap != null           │
│ label: "Đỉnh Cao. 5 trên 10 họa tiết..." │
│                                         │
│  ┌───────────────────────────────────┐  │
│  │ GestureDetector (Interaction)     │  │
│  │                                   │  │
│  │  ┌─────────────────────────────┐  │  │
│  │  │ AnimatedBuilder             │  │  │
│  │  │   (Visual Presentation)     │  │  │
│  │  │                             │  │  │
│  │  │   - Card UI                 │  │  │
│  │  │   - Progress Badge          │  │  │
│  │  │   - Stats Row               │  │  │
│  │  └─────────────────────────────┘  │  │
│  └───────────────────────────────────┘  │
└─────────────────────────────────────────┘
```

## Screen Reader Announcement Example

### Example 1: Fresh Urn (No Progress)
```
Urn: Đỉnh Cao
Discovered: 0/10
Progress: 0%

Screen Reader Says:
"Đỉnh Cao. 0 trên 10 họa tiết đã khám phá. Tiến độ 0 phần trăm. 
Nhấn đúp để xem chi tiết. Nút."
```

### Example 2: In Progress
```
Urn: Đỉnh Thịnh
Discovered: 7/15
Progress: 46%

Screen Reader Says:
"Đỉnh Thịnh. 7 trên 15 họa tiết đã khám phá. Tiến độ 46 phần trăm. 
Nhấn đúp để xem chi tiết. Nút."
```

### Example 3: Completed
```
Urn: Đỉnh Hưng
Discovered: 12/12
Progress: 100%

Screen Reader Says:
"Đỉnh Hưng. 12 trên 12 họa tiết đã khám phá. Tiến độ 100 phần trăm. 
Nhấn đúp để xem chi tiết. Nút."
```

## Testing Checklist

### VoiceOver (iOS)
- [ ] Enable VoiceOver
- [ ] Navigate to Explore screen
- [ ] Swipe through urn cards
- [ ] Verify announcement includes name
- [ ] Verify announcement includes progress stats
- [ ] Verify announcement includes action hint
- [ ] Double tap to activate

### TalkBack (Android)
- [ ] Enable TalkBack
- [ ] Navigate to Explore screen
- [ ] Swipe through urn cards
- [ ] Verify announcement includes name
- [ ] Verify announcement includes progress stats
- [ ] Verify announcement includes action hint
- [ ] Double tap to activate

## Key Points

✅ **Wrapped**: GestureDetector wrapped with Semantics
✅ **Button Role**: Identified as button for screen readers
✅ **Descriptive Label**: Includes name, progress, and action
✅ **Vietnamese**: Labels match app language
✅ **Dynamic**: Updates with urn progress
✅ **Non-Breaking**: No changes to existing functionality

## File Modified
`mobile/lib/features/explore/presentation/widgets/urn_card.dart`

- Lines 94-98: Added Semantics wrapper
- Lines 195-205: Added _buildSemanticLabel() method
- Total: +16 lines

