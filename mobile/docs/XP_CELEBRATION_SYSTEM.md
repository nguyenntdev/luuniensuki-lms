# XP Celebration System

Enhanced XP gain celebration animations for the Luuniensuki LMS mobile app.

## Overview

The XP Celebration System provides visually appealing animations when users gain XP, with different celebration levels based on the amount of XP earned and automatic level-up detection.

## Features

- **Three Celebration Levels:**
  - **Small (25 XP)**: Quick badge popup with slide-up animation
  - **Medium (50-75 XP)**: Badge popup with subtle particle effects
  - **Large (300+ XP)**: Full confetti blast with banner
  
- **Level-Up Detection**: Automatically detects rank changes and displays a special golden banner
- **Confetti Effects**: Uses the `confetti` package for celebration particles
- **Global Overlay System**: Works from anywhere in the app via context extension

## Components

### 1. XP Celebration Service
`mobile/lib/shared/services/xp_celebration_service.dart`

Global singleton service that manages celebration overlays.

```dart
// Show celebration programmatically
XpCelebrationService.instance.showCelebration(
  context: context,
  xpGained: 50,
  oldTotalXp: 100,
  newTotalXp: 150,
  badges: ['first_discovery'],
  onComplete: () => print('Celebration complete'),
);
```

### 2. XP Celebration Overlay Widget
`mobile/lib/shared/widgets/xp_celebration_overlay.dart`

The animated overlay widget with:
- Animated XP badge with bounce and slide effects
- Particle system for medium celebrations
- Confetti system for large celebrations and level-ups
- Level-up banner with rank name display

### 3. Context Extension
Easy-to-use context extension for showing celebrations:

```dart
context.showXpCelebration(
  xpGained: 25,
  oldTotalXp: userOldXp,
  newTotalXp: userNewXp,
);
```

### 4. XP Gain Handler Widget
`mobile/lib/shared/widgets/xp_gain_handler.dart`

Wrapper widget that automatically detects XP changes:

```dart
XpGainHandler(
  child: YourWidget(),
)
```

## Usage Examples

### Example 1: Discovery Animation (Enhanced Mode)

Update the discovery animation to use enhanced celebrations:

```dart
DiscoveryAnimation(
  motif: motif,
  xpEarned: result.xpEarned,
  oldTotalXp: oldXp,  // Pass old XP
  newTotalXp: result.totalXp,  // Pass new XP
  badgesEarned: result.badgesEarned,
  onComplete: _onComplete,
  useEnhancedCelebration: true,  // Enable enhanced mode
)
```

### Example 2: Quiz Completion

```dart
// In quiz_result_screen.dart
@override
void initState() {
  super.initState();
  
  if (widget.result.passed && widget.result.xpEarned > 0) {
    WidgetsBinding.instance.addPostFrameCallback((_) {
      // Get old XP from user state before submission
      final oldXp = widget.oldUserXp;
      
      context.showXpCelebration(
        xpGained: widget.result.xpEarned,
        oldTotalXp: oldXp,
        newTotalXp: widget.result.totalXp,
        badges: widget.result.newBadges.map((b) => b.slug).toList(),
      );
    });
  }
}
```

### Example 3: Lesson Completion

```dart
final result = await ref
    .read(discoveryNotifierProvider.notifier)
    .completeLesson(motifId);

if (result != null && mounted) {
  context.celebrateXpGain(
    xpGained: result.xpEarned,
    oldTotalXp: oldXp,
    newTotalXp: result.totalXp,
    badges: result.badgesEarned,
  );
}
```

## Constants

Updated `app_constants.dart` with:

```dart
// XP Values
static const int discoveryXp = 25;
static const int lessonXp = 50;
static const int masteredXp = 75;
static const int urnExamXp = 300;  // NEW

// Celebration Thresholds
static const int smallXpThreshold = 25;
static const int mediumXpThreshold = 50;
static const int largeXpThreshold = 300;

// Helper methods
AppConstants.getRankForXp(int xp)
AppConstants.getNextRank(int currentXp)
AppConstants.didLevelUp(int oldXp, int newXp)
```

## Animation Specifications

### Small XP Gain (25 XP)
- Duration: 1500ms
- Badge scales from 0 → 1.3 → 1.0 with elastic bounce
- Slides up from center by 200px
- Fades out at 70% progress

### Medium XP Gain (50-75 XP)
- Duration: 2000ms
- Badge animation + 15 particles radiating outward
- Particles fade as they travel
- Random colors from theme palette

### Large XP Gain (300+ XP)
- Duration: 2500ms
- Full confetti blast with 30 particles
- Explosive directional blast
- Multiple colors from theme

### Level Up
- Automatically triggered when rank changes
- Golden banner slides down from top
- Shows new rank name and level
- Confetti blast with 50 particles
- Level-up specific green gradient

## Integration Checklist

- [x] Create XP Celebration Service
- [x] Create XP Celebration Overlay Widget
- [x] Update App Constants with thresholds
- [x] Add helper methods for rank calculation
- [x] Create XP Gain Handler widget
- [x] Update DiscoveryAnimation with enhanced mode
- [ ] Integrate into quiz_result_screen.dart
- [ ] Integrate into lesson completion flow
- [ ] Integrate into urn exam completion
- [ ] Add sound effects (optional)
- [ ] Add haptic feedback (optional)

## Future Enhancements

1. **Sound Effects**: Add celebration sounds
2. **Haptic Feedback**: Vibration on XP gain
3. **Customization**: User preferences for animation intensity
4. **Achievements**: Special animations for rare achievements
5. **Streaks**: Special celebration for maintaining streaks

## Testing

Test different XP amounts to verify celebration levels:

```dart
// Small
context.showXpCelebration(xpGained: 25, oldTotalXp: 0, newTotalXp: 25);

// Medium
context.showXpCelebration(xpGained: 50, oldTotalXp: 25, newTotalXp: 75);

// Large
context.showXpCelebration(xpGained: 300, oldTotalXp: 0, newTotalXp: 300);

// Level up (from rank 1 to rank 2)
context.showXpCelebration(xpGained: 50, oldTotalXp: 75, newTotalXp: 125);
```

## Dependencies

- `confetti: ^0.7.0` - Already in pubspec.yaml
- `flutter_riverpod` - For service provider
- Standard Flutter animation framework

## Notes

- The celebration overlay is dismissible but has auto-dismiss after animation
- Only one celebration can be shown at a time (new ones dismiss previous)
- Enhanced mode is opt-in for backward compatibility
- Old XP values must be tracked in calling code for level-up detection

