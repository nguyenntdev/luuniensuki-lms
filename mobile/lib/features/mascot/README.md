# 🦉 App Mascot Feature - Implementation Guide

A Duolingo-inspired mascot system that provides encouragement, celebration, and engagement throughout the learning experience.

## 📁 File Structure

```
mobile/lib/features/mascot/
├── domain/
│   └── mascot_messages.dart      # Message library & context management
├── presentation/
│   └── widgets/
│       ├── mascot_widget.dart           # Animated mascot display
│       ├── mascot_bubble.dart           # Speech bubble with auto-dismiss
│       └── compact_mascot_display.dart  # Header-sized mascot
└── mascot.dart                    # Barrel file for exports
```

## 🎯 Features

### 1. **Mascot Widget** (`mascot_widget.dart`)
- Multiple expressions: happy, sad, encouraging, celebrating, worried, excited
- Smooth bounce and rotation animations
- Customizable size
- Uses emoji 🦉 as default (can be replaced with custom assets)

### 2. **Mascot Messages** (`mascot_messages.dart`)
- **Encouragement**: Motivational messages during progress
- **Celebration**: Achievement and completion messages
- **Streak Reminders**: Daily learning reminders
- **Streak Warnings**: When streak is about to break
- **Perfect Score**: Special messages for 100% quiz scores
- **Motivation**: Supportive messages for struggles
- **Welcome**: Greeting messages
- **Empty State**: Guidance for new users

### 3. **Mascot Bubble** (`mascot_bubble.dart`)
- Speech bubble overlay with mascot
- Auto-dismisses after 3 seconds (customizable)
- Tap to dismiss manually
- Fade and scale animations
- Context-aware positioning

### 4. **Compact Display** (`compact_mascot_display.dart`)
- Small animated mascot for headers
- Interactive - shows encouragement on tap
- Perfect for app bars and headers

## 🚀 Usage Examples

### Show Mascot Bubble
```dart
import 'package:mobile/features/mascot/mascot.dart';

// Show celebration message
showMascotBubble(
  context: context,
  message: MascotMessages.random(MascotMessages.celebration),
  expression: MascotExpression.celebrating,
  duration: const Duration(seconds: 4),
);

// Show perfect score message
showMascotBubble(
  context: context,
  message: MascotMessages.random(MascotMessages.perfectScore),
  expression: MascotExpression.celebrating,
);
```

### Use Mascot Widget Directly
```dart
// Large animated mascot
MascotWidget(
  expression: MascotExpression.happy,
  size: 80,
  animate: true,
)

// Small static mascot
MascotWidget(
  expression: MascotExpression.sad,
  size: 40,
  animate: false,
)
```

### Add Compact Mascot to Header
```dart
Row(
  children: [
    const CompactMascotDisplay(),
    // ... other header content
  ],
)
```

## 📍 Integration Points

### ✅ 1. Explore Screen Header
**File**: `mobile/lib/features/explore/presentation/screens/explore_screen.dart`
- Mascot appears in header next to title
- Tappable for encouragement messages

### ✅ 2. Quiz Result Screen
**File**: `mobile/lib/features/quiz/presentation/screens/quiz_result_screen.dart`
- **Perfect Score (100%)**: Celebrating expression with perfect score message
- **Pass**: Happy expression with celebration message
- **Fail**: Encouraging expression with motivation message

### ✅ 3. Lesson Completion
**File**: `mobile/lib/features/lesson/presentation/widgets/lesson_tab.dart`
- Shows celebration message when lesson is completed
- Celebrating expression

### ✅ 4. Login Screen
**File**: `mobile/lib/features/auth/presentation/screens/login_screen.dart`
- Animated mascot as app logo
- Welcomes users to the app

## 🎨 Mascot Expressions

```dart
enum MascotExpression {
  happy,       // 🦉 Default owl
  sad,         // 😢 When something goes wrong
  encouraging, // 💪 Motivation and encouragement
  celebrating, // 🎉 Achievements and perfect scores
  worried,     // 😟 Streak warnings
  excited,     // 🤩 Special events
  neutral,     // 🦉 Default state
}
```

## 💬 Message Categories

### Encouragement
```dart
MascotMessages.encouragement
// "Bạn làm tốt lắm! 🎉"
// "Tiếp tục phát huy nhé!"
// "Còn một chút nữa thôi!"
```

### Celebration
```dart
MascotMessages.celebration
// "Tuyệt vời! Bạn đã hoàn thành! 🎊"
// "Xuất sắc! Tiếp tục nào!"
```

### Perfect Score
```dart
MascotMessages.perfectScore
// "Hoàn hảo 100%! Bạn quá tuyệt! 🌟"
// "Điểm tuyệt đối! Mình tự hào về bạn! 💯"
```

### Motivation
```dart
MascotMessages.motivation
// "Đừng nản! Mọi người đều có lúc khó khăn!"
// "Học tập là quá trình, cứ cố gắng nhé!"
```

## 🔧 Customization

### Change Mascot Appearance
Edit `mascot_widget.dart` and replace emoji with:
- Custom image assets
- SVG graphics
- Lottie animations

### Add New Messages
Edit `mascot_messages.dart`:
```dart
static const newCategory = [
  "Your message 1",
  "Your message 2",
];
```

### Adjust Animation
Edit `mascot_widget.dart`:
```dart
_controller = AnimationController(
  duration: const Duration(milliseconds: 1500), // Change duration
  vsync: this,
);
```

## 🎯 Best Practices

1. **Context-Aware Messages**: Use `MascotMessages.getMessageForContext()` for appropriate messages
2. **Timing**: Show mascot messages after animations complete (500ms delay)
3. **Don't Overuse**: Show mascot at key moments, not for every action
4. **Keep It Light**: Messages should be short and encouraging
5. **Localization**: All messages in Vietnamese can be easily replaced for i18n

## 🚀 Future Enhancements

### Suggested Features:
1. **Persistent State**: Remember user's last interaction
2. **Custom Animations**: Different animations per expression
3. **Sound Effects**: Add audio feedback
4. **Push Notifications**: Use mascot in notifications
5. **Streak Reminders**: Daily notifications from mascot
6. **Level Up**: Special mascot reactions for level milestones
7. **Multiple Mascots**: Unlock different mascots
8. **Customization**: Let users choose mascot appearance

## 📊 Analytics Opportunities

Track mascot interactions:
- Message shown count
- Tap interactions
- Most shown contexts
- User engagement with mascot features

## 🐛 Known Limitations

1. Currently uses emojis - may not render consistently across platforms
2. No persistence - mascot state resets on app restart
3. Messages are hardcoded - need i18n for multi-language support

## 📝 Example: Adding Mascot to New Screen

```dart
import 'package:mobile/features/mascot/mascot.dart';

class NewScreen extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        actions: [
          CompactMascotDisplay(),
        ],
      ),
      body: Column(
        children: [
          // Your content
          ElevatedButton(
            onPressed: () {
              // Show mascot message on action
              showMascotBubble(
                context: context,
                message: "Great job!",
                expression: MascotExpression.celebrating,
              );
            },
            child: Text('Complete'),
          ),
        ],
      ),
    );
  }
}
```

## 🎉 Summary

The mascot feature adds personality and engagement to the app, similar to Duolingo's Duo owl. It provides:
- ✅ Visual feedback for user actions
- ✅ Encouragement and motivation
- ✅ Celebration of achievements
- ✅ Consistent brand personality
- ✅ Improved user engagement

The system is modular, easy to extend, and integrated at key touchpoints throughout the app.

