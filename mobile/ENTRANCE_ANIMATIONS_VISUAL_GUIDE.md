# Entrance Animations - Visual Reference Guide

## Animation Timeline

```
Time: 0ms                 400ms               800ms              1200ms
      |---------------------|-------------------|-------------------|
Item 0: [====FADE+SLIDE====]
Item 1:    [====FADE+SLIDE====]
Item 2:       [====FADE+SLIDE====]
Item 3:          [====FADE+SLIDE====]
Item 4:             [====FADE+SLIDE====]
Item 5:                [====FADE+SLIDE====]
```

## Animation Flow Diagram

```
Collection/Achievements Screen Loads
        ↓
AnimationController Initialized (800ms duration)
        ↓
Animation Starts (.forward())
        ↓
Grid Items Render with Stagger
        ↓
┌─────────────────────────────────────────┐
│ Item 0: Delay 0ms   → Animate 0-400ms   │
│ Item 1: Delay 100ms → Animate 100-500ms │
│ Item 2: Delay 200ms → Animate 200-600ms │
│ Item 3: Delay 300ms → Animate 300-700ms │
│ Item 4: Delay 400ms → Animate 400-800ms │
│ ...                                      │
└─────────────────────────────────────────┘
        ↓
All Items Fully Visible
```

## Visual States

### Before Animation (t=0ms for each item)
```
┌───────────────┐
│               │
│               │  ← Item at Y offset +30%
│               │  ← Opacity: 0 (invisible)
│               │
└───────────────┘
```

### During Animation (t=200ms for each item)
```
┌───────────────┐
│               │
│   ▓▓▓▓▓▓▓     │  ← Item sliding up
│               │  ← Opacity: ~0.5 (semi-transparent)
│               │
└───────────────┘
```

### After Animation (t=400ms for each item)
```
┌───────────────┐
│   ████████    │  ← Item at final position
│   ████████    │  ← Opacity: 1.0 (fully visible)
│               │
└───────────────┘
```

## Code Structure

### Collection Screen Animation Flow
```
_CollectionScreenState
    ↓
initState()
    ├─ Create AnimationController (800ms)
    ├─ Start animation (.forward())
    └─ Load collection data
    ↓
build() → _buildContent() → _buildMotifGrid()
    ↓
GridView.builder
    ↓
_buildAnimatedMotifCard(motif, index)
    ├─ AnimatedBuilder
    │   ├─ Calculate delay (index * 0.1)
    │   ├─ Create CurvedAnimation with Interval
    │   └─ Apply FadeTransition + SlideTransition
    └─ _buildMotifCard(motif)
```

### Achievements Screen Animation Flow
```
_AchievementsScreenState
    ↓
initState()
    ├─ Create TabController
    ├─ Create AnimationController (800ms)
    ├─ Start animation (.forward())
    └─ Load leaderboard data
    ↓
build() → TabBarView → _buildBadgesTab()
    ↓
GridView.builder
    ↓
_buildAnimatedBadgeCard(badge, index)
    ├─ AnimatedBuilder
    │   ├─ Calculate delay (index * 0.1)
    │   ├─ Create CurvedAnimation with Interval
    │   └─ Apply FadeTransition + SlideTransition
    └─ _buildBadgeCard(badge)
```

## Animation Parameters Reference

| Parameter | Value | Purpose |
|-----------|-------|---------|
| Duration | 800ms | Total animation controller duration |
| Stagger Delay | 100ms per item | Time between each item starting |
| Item Duration | 400ms | How long each item takes to animate |
| Start Offset | (0, 0.3) | Vertical offset (30% down) |
| End Offset | (0, 0) | Final position |
| Curve | easeOutCubic | Smooth deceleration |
| Opacity Range | 0.0 → 1.0 | Fade from invisible to visible |

## Grid Layout Reference

### 2-Column Grid (Both Screens)
```
┌─────────┬─────────┐
│ Item 0  │ Item 1  │  ← Row 1 (delay: 0ms, 100ms)
├─────────┼─────────┤
│ Item 2  │ Item 3  │  ← Row 2 (delay: 200ms, 300ms)
├─────────┼─────────┤
│ Item 4  │ Item 5  │  ← Row 3 (delay: 400ms, 500ms)
└─────────┴─────────┘
```

## Performance Considerations

### Memory Usage
```
Per Screen:
├─ 1 AnimationController (~1-2 KB)
├─ N AnimatedBuilders (where N = number of items)
└─ N CurvedAnimations (lightweight, created on-demand)
```

### Frame Rate Impact
- Target: 60 FPS
- Expected: 60 FPS (animations use GPU acceleration)
- Curve complexity: Low (easeOutCubic is simple)

## Testing Checklist

- [ ] Collection screen items fade in smoothly
- [ ] Collection screen items slide from below
- [ ] Stagger effect is visible in Collection
- [ ] Achievement badges fade in smoothly
- [ ] Achievement badges slide from below
- [ ] Stagger effect is visible in Achievements
- [ ] No performance degradation
- [ ] No memory leaks (controllers disposed)
- [ ] Tab switching doesn't restart animations
- [ ] Filter changes don't interfere with animations
- [ ] Animations work on different screen sizes
- [ ] Animations work on slow devices

## Integration Points

### Collection Screen
- Integrates with: `CollectionNotifierProvider`
- Triggers on: Screen load
- Grid type: Motif cards (2 columns)
- Filter impact: No re-animation on filter change

### Achievements Screen
- Integrates with: Badges tab data
- Triggers on: Tab view
- Grid type: Badge cards (2 columns)
- Tab switching: No re-animation (controller lives with state)

