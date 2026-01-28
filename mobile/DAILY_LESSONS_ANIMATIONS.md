# Daily Lessons Widget - Animation Specifications

## Overview
Enhanced animations for the Daily Lessons horizontal scrollable cards in the Learning Hub screen.

## Animation Breakdown

### 1. Staggered Entry Animation
**Purpose**: Create a professional cascading effect when cards first appear

```dart
Duration: 400ms per card
Delay: 100ms between each card (index * 100ms)
Curve: Curves.easeOutCubic

Entry Effects (combined):
- Fade: opacity 0.0 → 1.0
- Slide: translateY from +30% → 0%

Implementation: _StaggeredAnimationWrapper
```

**Visual Timeline**:
```
Card 0: starts at 0ms    → completes at 400ms
Card 1: starts at 100ms  → completes at 500ms
Card 2: starts at 200ms  → completes at 600ms
Card 3: starts at 300ms  → completes at 700ms
Card 4: starts at 400ms  → completes at 800ms
Card 5: starts at 500ms  → completes at 900ms
```

### 2. Floating Animation (Idle State)
**Purpose**: Create subtle "breathing" effect for living UI

```dart
Duration: 3000ms (3 seconds)
Range: -2px to +2px (vertical)
Curve: Curves.easeInOut
Mode: repeat(reverse: true) - infinite loop

Implementation: _floatController with AnimatedBuilder
```

**Motion Pattern**:
```
0s    → y = 0px
0.75s → y = -2px (up)
1.5s  → y = 0px (center)
2.25s → y = +2px (down)
3s    → y = 0px (back to start, then repeat)
```

### 3. XP Badge Glow
**Purpose**: Draw attention to XP rewards

```dart
Effect: BoxShadow on XP badge background
Color: AppColors.xpGold.withOpacity(0.3)
Blur: 8px
Spread: 0px (soft edge)

Applied to: ALL XP badges
```

### 4. XP Badge Pulse (High Value)
**Purpose**: Extra emphasis for valuable lessons (>50 XP)

```dart
Duration: 1500ms
Scale: 1.0 → 1.15 → 1.0
Curve: Curves.easeInOut
Mode: repeat(reverse: true)

Trigger: widget.lesson.xpReward > 50

Implementation: ScaleTransition with _pulseController
```

### 5. Progress Ring (Review Lessons)
**Purpose**: Show review progress visually

```dart
Position: Top-left corner
Size: 28x28px
Stroke: 2.5px
Progress: 0.7 (70% - mock value)
Color: AppColors.warning (amber)
Background: Colors.white.withOpacity(0.2)

Visibility: Only for status == _LessonStatus.review
```

## Animation Hierarchy

```
ListView.builder
└── _StaggeredAnimationWrapper (per card)
    └── FadeTransition
        └── SlideTransition
            └── _DailyLessonCard
                └── AnimatedBuilder (float)
                    └── Transform.translate
                        └── GestureDetector
                            └── AnimatedScale (on press)
                                └── Card Container
                                    ├── Progress Ring (conditional)
                                    ├── Status Badge
                                    └── XP Badge
                                        └── ScaleTransition (pulse, conditional)
```

## Performance Notes

- All animations use hardware acceleration (Transform, Scale)
- Controllers properly disposed on unmount
- Staggered start prevents simultaneous animation overhead
- RepaintBoundary not needed (each card is separate widget)
- No expensive rebuilds in hot path

## Color Constants Used

```dart
AppColors.info        // Blue for "Mới" (New) lessons
AppColors.warning     // Amber for "Ôn tập" (Review) lessons
AppColors.xpGold      // Gold for XP badge
```

## Interaction States

1. **Idle**: Floating animation active
2. **Pressed**: Scale to 0.96 (150ms, Curves.easeOut)
3. **Released**: Scale back to 1.0 + navigate

## Testing Checklist

- [ ] Cards appear with stagger on screen load
- [ ] Floating animation visible during idle
- [ ] XP glow visible on all badges
- [ ] Pulse animation on lessons with >50 XP
- [ ] Progress ring shows on review lessons
- [ ] Tap interaction still works smoothly
- [ ] No animation jank or dropped frames
- [ ] Controllers disposed (no memory leaks)

