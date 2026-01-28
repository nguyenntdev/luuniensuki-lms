# UrnCard Accessibility Implementation

## Summary
Added Semantics widget wrapper to UrnCard for screen reader accessibility support.

## Changes Made

### File Modified
- `lib/features/explore/presentation/widgets/urn_card.dart`

### Implementation Details

#### 1. Wrapped GestureDetector with Semantics Widget
**Location**: `build()` method (line 94-98)

```dart
return Semantics(
  button: true,
  enabled: widget.onTap != null,
  label: _buildSemanticLabel(),
  child: GestureDetector(
    // ... existing GestureDetector code
  ),
);
```

**Properties**:
- `button: true` - Identifies the widget as a button for screen readers
- `enabled: widget.onTap != null` - Sets enabled state based on tap handler availability
- `label: _buildSemanticLabel()` - Provides descriptive text for screen readers

#### 2. Added Semantic Label Builder Method
**Location**: New method in `_UrnCardState` class (line 195-205)

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

**Label Content** (Vietnamese):
- Urn name
- Discovery progress: "X trên Y họa tiết đã khám phá" (X out of Y motifs discovered)
- Progress percentage: "Tiến độ Z phần trăm" (Progress Z percent)
- Action hint: "Nhấn đúp để xem chi tiết" (Double tap to view details)

## Data Source

Uses properties from `Urn` entity:
- `name` - Urn display name
- `discoveredCount` - Number of discovered motifs
- `motifCount` - Total number of motifs
- `progressPercent` - Calculated progress (0.0 to 1.0)

## Accessibility Benefits

1. **Screen Reader Support**: Users with visual impairments can now understand:
   - What the card represents (urn name)
   - Current progress (discovered count and percentage)
   - Available action (tap to view details)

2. **Localization**: Labels are in Vietnamese to match the app's primary language

3. **Dynamic Content**: Progress information updates automatically as user makes progress

4. **Semantic Role**: Properly identified as a button widget for assistive technologies

## Testing Recommendations

### iOS (VoiceOver)
1. Enable VoiceOver: Settings > Accessibility > VoiceOver
2. Navigate to Explore screen
3. Swipe through urn cards
4. Verify VoiceOver reads: name, progress stats, and action hint
5. Double tap to activate card

### Android (TalkBack)
1. Enable TalkBack: Settings > Accessibility > TalkBack
2. Navigate to Explore screen
3. Swipe through urn cards
4. Verify TalkBack reads: name, progress stats, and action hint
5. Double tap to activate card

## Example Output

For an urn with:
- Name: "Đỉnh Cao"
- Discovered: 5 motifs
- Total: 10 motifs
- Progress: 50%

**Screen reader will announce**:
> "Đỉnh Cao. 5 trên 10 họa tiết đã khám phá. Tiến độ 50 phần trăm. Nhấn đúp để xem chi tiết."

## Code Quality

- ✅ No breaking changes to existing functionality
- ✅ Maintains existing widget structure
- ✅ Follows Flutter accessibility best practices
- ✅ Uses semantic properties correctly
- ✅ Vietnamese localization for labels
- ✅ Dynamic content based on urn state

## What's Next

Consider adding accessibility to:
1. Other card widgets (MotifCard, etc.)
2. Interactive buttons and controls
3. Form inputs and validation messages
4. Navigation elements
5. Status indicators and badges

## References

- [Flutter Semantics Documentation](https://api.flutter.dev/flutter/widgets/Semantics-class.html)
- [Flutter Accessibility Guide](https://docs.flutter.dev/development/accessibility-and-localization/accessibility)
- [Material Design Accessibility](https://m3.material.io/foundations/accessible-design/overview)

