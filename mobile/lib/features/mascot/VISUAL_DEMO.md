# 📸 Mascot Feature - Visual Demo Guide

## What You'll See in the App

### 🏠 Explore Screen

```
╔══════════════════════════════════════════╗
║  [≡]  🦉  Cửu Đỉnh      [📊 Progress]  ║
║       Khám phá 9 chiếc đỉnh triều Nguyễn ║
║                                          ║
║  ┌────────────────────────────────────┐  ║
║  │ 🔍 Tìm kiếm...                     │  ║
║  └────────────────────────────────────┘  ║
║                                          ║
║  [Daily Goal Widget]                     ║
╚══════════════════════════════════════════╝
```

**What to look for:**
- Animated owl (🦉) in top left
- Bounces up and down every 3 seconds
- Tap it to see encouragement message

---

### 💬 Mascot Bubble (When Tapped)

```
╔══════════════════════════════════════════╗
║                                          ║
║  🦉  ╭─────────────────────────────╮    ║
║      │ Bạn làm tốt lắm! 🎉         │    ║
║      │                             │    ║
║      │ Nhấn để đóng                │    ║
║      ╰─────────────────────────────╯    ║
║                                          ║
╚══════════════════════════════════════════╝
```

**What to look for:**
- White speech bubble appears
- Message inside
- Auto-dismisses after 3 seconds
- Can tap to dismiss early

---

### 🎯 Quiz Result - Perfect Score

```
╔══════════════════════════════════════════╗
║            ✨ 100% ✨                    ║
║                                          ║
║  ┌────────────────────────────────────┐  ║
║  │     Hoàn hảo!                      │  ║
║  │     10/10 câu đúng                 │  ║
║  │                                    │  ║
║  │     +50 XP                         │  ║
║  └────────────────────────────────────┘  ║
║                                          ║
║  🎉  ╭─────────────────────────────╮    ║
║      │ Hoàn hảo 100%!              │    ║
║      │ Bạn quá tuyệt! 🌟           │    ║
║      ╰─────────────────────────────╯    ║
║                                          ║
║  [TRỞ VỀ]         [TIẾP TỤC]           ║
╚══════════════════════════════════════════╝
```

**What to look for:**
- Confetti animation
- Celebrating emoji (🎉)
- Perfect score message
- Appears ~500ms after score shown

---

### 😢 Quiz Result - Failed

```
╔══════════════════════════════════════════╗
║            40%                           ║
║                                          ║
║  ┌────────────────────────────────────┐  ║
║  │     Chưa đạt yêu cầu               │  ║
║  │     4/10 câu đúng                  │  ║
║  │                                    │  ║
║  │     +20 XP                         │  ║
║  └────────────────────────────────────┘  ║
║                                          ║
║  💪  ╭─────────────────────────────╮    ║
║      │ Đừng nản!                   │    ║
║      │ Cố lên nhé! 💪              │    ║
║      ╰─────────────────────────────╯    ║
║                                          ║
║  [THỬ LẠI]         [HỌC LẠI]           ║
╚══════════════════════════════════════════╝
```

**What to look for:**
- No confetti
- Encouraging emoji (💪)
- Motivation message
- Supportive tone

---

### 📚 Lesson Completion

```
╔══════════════════════════════════════════╗
║  ╭────────────────────────────────────╮  ║
║  │  ✅ Bài học hoàn thành!           │  ║
║  │                                    │  ║
║  │  +50 XP earned                     │  ║
║  │  🏆 Badge earned: Người học tập    │  ║
║  │                                    │  ║
║  │  [ĐÓNG]    [LÀM BÀI QUIZ]         │  ║
║  ╰────────────────────────────────────╯  ║
║                                          ║
║  🎉  ╭─────────────────────────────╮    ║
║      │ Bài học hoàn thành!         │    ║
║      │ Tuyệt lắm! 📚               │    ║
║      ╰─────────────────────────────╯    ║
╚══════════════════════════════════════════╝
```

**What to look for:**
- Completion dialog first
- Then mascot bubble appears
- Celebrating expression
- Lesson complete message

---

### 🔐 Login Screen

```
╔══════════════════════════════════════════╗
║                                          ║
║                                          ║
║              🦉                          ║
║         (bouncing)                       ║
║                                          ║
║        Lưu Niên Sử Kí                   ║
║     Đăng nhập để tiếp tục               ║
║                                          ║
║  ┌────────────────────────────────────┐  ║
║  │ 📧 Email                           │  ║
║  └────────────────────────────────────┘  ║
║                                          ║
║  ┌────────────────────────────────────┐  ║
║  │ 🔒 Mật khẩu                        │  ║
║  └────────────────────────────────────┘  ║
║                                          ║
║  ┌────────────────────────────────────┐  ║
║  │        ĐĂNG NHẬP                   │  ║
║  └────────────────────────────────────┘  ║
║                                          ║
║     Chưa có tài khoản? Đăng ký          ║
╚══════════════════════════════════════════╝
```

**What to look for:**
- Large animated owl at top
- Replaces the traditional logo
- Continuous bounce + rotation
- Welcoming presence

---

## Animation Behavior

### Bounce Effect
```
Frame 0:    🦉     (baseline)
Frame 1:    🦉↑    (move up)
Frame 2:    🦉↓    (move down)
Frame 3:    🦉     (bounce back)
Frame 4:    🦉     (baseline)

Duration: 1.5 seconds per cycle
Repeat: Infinite
```

### Rotation Effect
```
Frame 0:    🦉     (0°)
Frame 1:    🦉⤴    (+18°)
Frame 2:    🦉⤵    (-18°)
Frame 3:    🦉⤴    (+18°)
Frame 4:    🦉     (0°)

Duration: 1.5 seconds per cycle
Synchronized with bounce
```

### Bubble Appear Animation
```
Frame 0:  ·        (scale: 0, opacity: 0)
Frame 1:  •        (scale: 0.5, opacity: 0.5)
Frame 2:  ○        (scale: 0.8, opacity: 0.8)
Frame 3:  ⭕       (scale: 1, opacity: 1)

Duration: 300ms
Curve: easeOutBack (slight overshoot)
```

---

## Interaction Flow

### Tap Mascot on Explore Screen
```
1. User taps 🦉
   ↓
2. Speech bubble scales in
   ↓
3. Random encouragement message shown
   ↓
4. Auto-dismiss after 3 seconds
   OR
   User taps bubble to dismiss early
   ↓
5. Bubble scales out and fades
```

### Complete Quiz with Perfect Score
```
1. Submit quiz answers
   ↓
2. Navigate to result screen
   ↓
3. Show score (100%)
   ↓
4. Play confetti animation
   ↓
5. Wait 500ms
   ↓
6. Show mascot bubble with perfect score message
   ↓
7. Auto-dismiss after 4 seconds
```

---

## Color & Styling

### Speech Bubble
- **Background**: White (#FFFFFF)
- **Text**: Dark gray/black
- **Shadow**: rgba(0,0,0,0.1), 10px blur
- **Border Radius**: 20px
- **Padding**: 16px all sides

### Message Text
- **Font Size**: 15px
- **Font Weight**: 500 (medium)
- **Line Height**: 1.4
- **Color**: AppColors.textPrimary

### Hint Text ("Nhấn để đóng")
- **Font Size**: 12px
- **Color**: rgba(0,0,0,0.6)
- **Style**: Italic

---

## Responsive Behavior

### Mobile Portrait
```
┌─────────────┐
│ 🦉  Title   │
│   Message   │
│   [Bubble]  │
└─────────────┘

Bubble width: 90% of screen
Mascot size: 50px
```

### Tablet Landscape
```
┌──────────────────────────────┐
│ 🦉  Title         [Content]  │
│       [Bubble]               │
└──────────────────────────────┘

Bubble width: Max 500px
Mascot size: 60px
```

---

## Testing Checklist

When testing, verify:

- [ ] Mascot appears on explore screen
- [ ] Mascot animates smoothly
- [ ] Tap shows bubble
- [ ] Bubble auto-dismisses
- [ ] Quiz results show appropriate mascot
- [ ] Lesson completion shows mascot
- [ ] Login screen has animated mascot
- [ ] Animations are smooth (60fps)
- [ ] No memory leaks after repeated use
- [ ] Works on different screen sizes

---

## Troubleshooting

### Mascot not appearing?
- Check imports: `import 'package:mobile/features/mascot/mascot.dart';`
- Verify context is valid
- Check console for errors

### Animation not smooth?
- Check device performance
- Ensure no heavy operations during animation
- Verify vsync is properly configured

### Bubble not dismissing?
- Check timer is created
- Verify context.mounted before showing
- Ensure overlay entry is properly removed

---

## 🎬 Demo Video Script

If recording a demo:

1. **Start**: Open app to login screen
   - Show animated mascot bouncing

2. **Navigate**: Go to explore screen
   - Point out mascot in header
   - Tap mascot to show bubble

3. **Take Quiz**: Complete a quiz
   - Show different scores (perfect, pass, fail)
   - Highlight mascot messages for each

4. **Complete Lesson**: Finish a lesson
   - Show completion dialog + mascot

5. **Wrap Up**: Return to explore
   - Show mascot one more time

Duration: ~2 minutes

---

## Summary

The mascot feature is fully integrated and ready to use! Look for the animated owl emoji throughout the app providing encouragement, celebration, and support at key moments in the learning journey.

**Enjoy the added personality! 🦉✨**

