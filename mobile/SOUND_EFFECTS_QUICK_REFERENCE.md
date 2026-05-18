# Sound Effects System - Quick Reference

## 🎵 Import and Setup

```dart
import 'package:your_app/core/services/sound_service.dart';

// In your widget
final soundService = ref.read(soundServiceProvider);
```

## 🎮 Playing Sounds

### Basic Usage
```dart
// Play specific sound
await soundService.playCorrect();
await soundService.playWrong();
await soundService.playTap();
await soundService.playXpGain();
await soundService.playLevelUp();
await soundService.playStreakComplete();
await soundService.playLessonComplete();

// Or use generic method
await soundService.play(SoundEffect.correct);
```

### Haptic Only
```dart
// Just vibration, no sound
await soundService.playHaptic();
```

## 🎯 Integration Examples

### Quiz Answer Feedback
```dart
onAnswerSelected: (answer) async {
  final soundService = ref.read(soundServiceProvider);
  final isCorrect = checkAnswer(answer);
  
  if (isCorrect) {
    await soundService.playCorrect();
  } else {
    await soundService.playWrong();
  }
}
```

### Button Tap Sound
```dart
// Method 1: Manual
ElevatedButton(
  onPressed: () async {
    await ref.read(soundServiceProvider).playTap();
    // Your logic here
  },
  child: Text('Click Me'),
)

// Method 2: Using SoundButton widget
SoundButton(
  onPressed: () {
    // Your logic here
  },
  child: Text('Click Me'),
)

// Method 3: Extension method
ElevatedButton(
  onPressed: () => print('Clicked'),
  child: Text('Click Me'),
).withTapSound(ref)
```

### XP Celebration
```dart
// Automatic - already integrated in XpCelebrationService
context.showXpCelebration(
  xpGained: 50,
  oldTotalXp: 100,
  newTotalXp: 150,
);
// Plays appropriate sound automatically
```

### Lesson Complete
```dart
// In quiz result screen
if (quizPassed) {
  ref.read(soundServiceProvider).playLessonComplete();
}
```

### Level Up
```dart
// Automatic - integrated in XpCelebrationService
// Or manual trigger:
if (didLevelUp) {
  ref.read(soundServiceProvider).playLevelUp();
}
```

### Streak Complete
```dart
// When user completes daily streak
if (streakAchieved) {
  ref.read(soundServiceProvider).playStreakComplete();
}
```

## 🔧 Advanced Usage

### Check Settings
```dart
// Sound service automatically checks settings
// But you can check manually:
final settings = ref.read(settingsNotifierProvider);
if (settings.soundEffectsEnabled) {
  // Sound will play
} else {
  // Haptic will play instead
}
```

### Custom Sound Sequence
```dart
// Play multiple sounds in sequence
await soundService.playCorrect();
await Future.delayed(Duration(milliseconds: 500));
await soundService.playXpGain();
```

### Conditional Sounds
```dart
if (isPerfectScore) {
  await soundService.playLevelUp(); // More dramatic
} else if (isPassing) {
  await soundService.playLessonComplete(); // Normal celebration
} else {
  await soundService.playWrong(); // Failed
}
```

## 📱 Sound Button Widgets

### Pre-built Button Widgets
```dart
// Elevated button with sound
SoundButton(
  onPressed: () => print('Clicked'),
  child: Text('Submit'),
)

// Text button with sound
SoundTextButton(
  onPressed: () => print('Clicked'),
  child: Text('Cancel'),
)

// Outlined button with sound
SoundOutlinedButton(
  onPressed: () => print('Clicked'),
  child: Text('Learn More'),
)

// Icon button with sound
SoundIconButton(
  onPressed: () => print('Clicked'),
  icon: Icon(Icons.favorite),
)

// Disable sound for specific button
SoundButton(
  onPressed: () => print('Clicked'),
  playSound: false, // No sound on this button
  child: Text('Silent'),
)
```

## 🎨 Haptic Patterns Reference

| Sound Effect | Duration | Intensity | Pattern |
|--------------|----------|-----------|---------|
| Correct | 50ms | Medium | Single pulse |
| Wrong | 100ms×2 | Strong | Double tap |
| Tap | 30ms | Light | Quick tap |
| XP Gain | 80ms | Medium+ | Celebration |
| Level Up | 3-burst | Maximum | Fanfare |
| Streak | 3-rising | Crescendo | Ascending |
| Lesson | 2-pulse | Strong | Success |

## ⚙️ Settings Integration

### Enable/Disable Sounds
```dart
// In Settings screen (already implemented)
ref.read(settingsNotifierProvider.notifier).setSoundEffects(true);

// Get current setting
final isEnabled = ref.watch(settingsNotifierProvider).soundEffectsEnabled;
```

## 🔊 Sound Files

### Required Files
Place in `mobile/assets/sounds/`:
- `correct.mp3`
- `wrong.mp3`
- `tap.mp3`
- `xp_gain.mp3`
- `level_up.mp3`
- `streak_complete.mp3`
- `lesson_complete.mp3`

### Generate Placeholder Sounds
```bash
cd mobile/assets/sounds
python3 generate_sounds.py
```

## 🐛 Troubleshooting

### Sound Not Playing
```dart
// Check initialization
final soundService = ref.read(soundServiceProvider);
await soundService.initialize(); // Manual init if needed

// Check settings
print(ref.read(settingsNotifierProvider).soundEffectsEnabled);

// Check file exists
// If file missing, haptic feedback plays automatically
```

### Delay on First Play
```dart
// Pre-initialize in app startup
// Already handled in soundServiceProvider, but you can force:
void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await HiveStorage.init();
  
  runApp(
    ProviderScope(
      child: MyApp(),
    ),
  );
}
```

## 📝 Best Practices

### Do's ✅
- Use appropriate sound for the action
- Play sounds on immediate feedback events
- Respect user's sound settings
- Pre-load sounds (automatic)
- Use haptic feedback for subtle interactions

### Don'ts ❌
- Don't play multiple sounds simultaneously (confusing)
- Don't play sound on every tiny action (annoying)
- Don't ignore sound settings
- Don't block UI while playing sound (always async)

## 🎯 Common Use Cases

### Form Submission
```dart
onPressed: () async {
  await ref.read(soundServiceProvider).playTap();
  final success = await submitForm();
  
  if (success) {
    await ref.read(soundServiceProvider).playCorrect();
  } else {
    await ref.read(soundServiceProvider).playWrong();
  }
}
```

### Achievement Unlock
```dart
if (achievementUnlocked) {
  await ref.read(soundServiceProvider).playLevelUp();
  showAchievementDialog();
}
```

### Navigation
```dart
onTap: () async {
  await ref.read(soundServiceProvider).playTap();
  context.push('/next-screen');
}
```

### Toggle Switch
```dart
Switch(
  value: value,
  onChanged: (newValue) async {
    await ref.read(soundServiceProvider).playTap();
    setState(() => value = newValue);
  },
)
```

---

**Need more help?** Check `SOUND_EFFECTS_IMPLEMENTATION.md` for detailed documentation.

