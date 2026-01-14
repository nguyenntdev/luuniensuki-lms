# Hearts/Energy System Implementation

## Overview

The Hearts/Energy system is a gamification feature similar to Duolingo's hearts system. Users lose hearts when they answer questions incorrectly in quizzes, creating a risk-reward dynamic that encourages careful learning.

## Features

### 1. **Hearts State Management**
- **Max Hearts**: 5 hearts maximum
- **Auto Refill**: 1 heart every 30 minutes
- **Persistent Storage**: Hearts state saved in Hive storage
- **Real-time Updates**: Auto-refill timer updates every minute

### 2. **Quiz Integration**
- **Heart Deduction**: Lose 1 heart per wrong answer
- **Heart Display**: Show hearts count in quiz header
- **Lost Animation**: Animated feedback when losing a heart
- **Blocking**: Cannot continue quiz when hearts reach 0

### 3. **Hearts Refill Options**
When users run out of hearts, they can:
- **Wait**: Hearts auto-refill (30 min per heart)
- **Spend Gems**: Refill all hearts for 50 gems
- **Practice Mode**: Earn hearts back through practice (TODO)
- **Watch Ad**: Get 1 heart by watching an ad (TODO)

## File Structure

```
mobile/lib/features/hearts/
├── domain/
│   └── entities/
│       ├── heart_state.dart          # Hearts state entity
│       ├── heart_state.freezed.dart  # Generated
│       └── heart_state.g.dart        # Generated
├── presentation/
│   ├── providers/
│   │   ├── hearts_provider.dart      # Hearts state provider
│   │   └── hearts_provider.g.dart    # Generated
│   ├── screens/
│   │   └── hearts_refill_screen.dart # Refill options screen
│   └── widgets/
│       ├── hearts_display.dart       # Hearts UI widget
│       └── heart_lost_animation.dart # Lost heart animation
```

## Implementation Details

### HeartState Entity

```dart
class HeartState {
  final int maxHearts;           // 5
  final int currentHearts;       // 0-5
  final DateTime lastRefillTime; // Last refill timestamp
  final int refillIntervalMinutes; // 30
  final bool isUnlimited;        // Premium feature
}
```

**Key Methods:**
- `calculateRefillableHearts()` - Calculate hearts to add based on time
- `getTimeUntilNextRefill()` - Get time until next heart
- `loseHeart()` - Deduct one heart
- `refillAll()` - Restore all hearts
- `autoRefill()` - Auto-refill based on time passed

### HeartsNotifier Provider

**Responsibilities:**
- Load/save hearts state from/to Hive
- Auto-refill timer (checks every minute)
- Provide methods for heart manipulation

**Key Methods:**
- `loseHeart()` - Called when user answers incorrectly
- `canContinue()` - Check if user has hearts
- `refillWithGems(gemCost, currentGems)` - Refill using gems
- `addHeart()` - Add single heart (for rewards)
- `refresh()` - Force check for auto-refill

### Quiz Integration

**Modified Quiz Screen:**
1. Added hearts display in AppBar
2. Track incorrect answers to avoid duplicate penalties
3. Deduct heart on wrong answer
4. Show heart lost animation
5. Navigate to refill screen when out of hearts

```dart
onAnswerSelected: (answer) async {
  final isCorrect = currentQuestion.correctAnswer == answer;
  
  if (!isCorrect && !_incorrectAnswers.containsKey(questionId)) {
    _incorrectAnswers[questionId] = true;
    await ref.read(heartsNotifierProvider.notifier).loseHeart();
    showHeartLostAnimation(context);
    
    if (!ref.read(heartsNotifierProvider).hasHearts) {
      // Navigate to refill screen
      context.push('/hearts-refill?returnPath=/quiz/$motifId');
    }
  }
}
```

### UI Components

**HeartsDisplay Widget:**
- Shows 5 heart icons (filled/empty)
- Countdown timer for next refill
- Tap to show info dialog

**CompactHeartsDisplay Widget:**
- Compact version for headers
- Shows heart icon + count
- Infinity symbol for unlimited hearts

**HeartLostAnimation:**
- Animated overlay when losing a heart
- Scale + fade + slide animation
- Auto-dismisses after animation

**HeartsRefillScreen:**
- Shows refill options when out of hearts
- 4 options: Wait, Gems, Practice, Ad
- Can navigate back or to home

## Storage

Hearts state is stored in Hive's `userBox` with key `'hearts_state'`:

```dart
{
  "maxHearts": 5,
  "currentHearts": 3,
  "lastRefillTime": "2024-01-15T10:30:00.000Z",
  "refillIntervalMinutes": 30,
  "isUnlimited": false
}
```

## Auto-Refill Logic

1. **Timer**: Runs every 1 minute
2. **Calculate**: Minutes passed since `lastRefillTime`
3. **Refill**: Add hearts based on full 30-minute intervals
4. **Update**: Set `lastRefillTime` to last full interval
5. **Cap**: Never exceed `maxHearts`

Example:
- Last refill: 10:00 AM
- Current time: 11:15 AM (75 minutes)
- Full intervals: 2 (60 minutes)
- Hearts to add: 2
- New lastRefillTime: 11:00 AM

## Routes

```dart
'/hearts-refill' => HeartsRefillScreen
  Query params:
    - returnPath: Path to return to after refill
```

## Future Enhancements

### TODO Items

1. **Practice Mode**
   - Special quiz mode that doesn't cost hearts
   - Earn 1 heart per perfect score
   - Limited to once per day

2. **Ad Integration**
   - Integrate ad SDK (e.g., AdMob)
   - Watch rewarded video ad for 1 heart
   - Cooldown timer (e.g., 1 ad per hour)

3. **Gems System Integration**
   - Currently uses XP as placeholder
   - Add actual gems currency
   - Deduct gems when refilling

4. **Premium Features**
   - Unlimited hearts for premium users
   - Set `isUnlimited: true` for subscribers
   - Show premium badge in UI

5. **Analytics**
   - Track heart loss rate
   - Monitor refill method usage
   - A/B test refill costs

6. **Notifications**
   - Notify when hearts are full
   - Remind users to return when hearts refilled
   - Schedule local notifications

## Usage Examples

### Check if user has hearts before starting quiz:

```dart
final hasHearts = ref.watch(hasHeartsProvider);

if (!hasHearts) {
  context.push('/hearts-refill?returnPath=/quiz/$motifId');
  return;
}
```

### Show hearts in any screen:

```dart
// Full display with timer
HeartsDisplay(showTimer: true)

// Compact display
CompactHeartsDisplay(
  onTap: () => showHeartsInfoDialog(context),
)
```

### Reward hearts for achievements:

```dart
await ref.read(heartsNotifierProvider.notifier).addHeart();
```

### Test/Debug:

```dart
// Reset to full hearts
await ref.read(heartsNotifierProvider.notifier).reset();

// Set unlimited (premium)
await ref.read(heartsNotifierProvider.notifier).setUnlimited(true);
```

## Testing

### Unit Tests Needed

1. **HeartState:**
   - `calculateRefillableHearts()` logic
   - `getTimeUntilNextRefill()` edge cases
   - `loseHeart()` when at 0
   - `autoRefill()` calculations

2. **HeartsNotifier:**
   - Storage load/save
   - Timer behavior
   - State updates

3. **Quiz Integration:**
   - Heart deduction on wrong answer
   - No duplicate penalties
   - Navigation to refill screen

### Manual Testing Checklist

- [ ] Hearts display correctly in quiz header
- [ ] Wrong answer deducts 1 heart
- [ ] Animation plays when losing heart
- [ ] Can't answer when at 0 hearts
- [ ] Navigates to refill screen when at 0
- [ ] Timer counts down correctly
- [ ] Auto-refill works after 30 minutes
- [ ] Gems refill option works
- [ ] State persists across app restarts
- [ ] Multiple wrong answers on same question only costs 1 heart

## Performance Considerations

1. **Timer Efficiency**: Timer runs every minute, not every second
2. **Storage**: Only saves on state change, not on every read
3. **Animations**: Uses hardware-accelerated transforms
4. **Provider**: Uses Riverpod for efficient rebuilds

## Accessibility

- Clear visual feedback for heart count
- Timer displays time in readable format
- Large touch targets for buttons
- High contrast colors for hearts
- Info dialog explains system clearly

## Localization

All text is in Vietnamese (vi):
- "Tim" (Hearts)
- "Hết Tim" (Out of Hearts)
- "Đợi Tim Hồi" (Wait for Refill)
- "Nạp Đầy Tim" (Refill Hearts)

Ready for i18n extraction when multi-language support is added.

