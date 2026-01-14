# 🦉 Mascot Visual Guide

## Mascot Expressions & Use Cases

### 1. Happy Expression 🦉
**When to use:**
- Default state
- General progress
- Explore screen header
- Positive interactions

**Example:**
```
     🦉
    /   \
  "Bạn làm tốt lắm!"
```

---

### 2. Celebrating Expression 🎉
**When to use:**
- Quiz completion (passing)
- Perfect scores (100%)
- Lesson completion
- Achievement unlocked
- Streak milestones

**Example:**
```
     🎉
    /   \
  "Tuyệt vời! Bạn đã hoàn thành!"
```

---

### 3. Encouraging Expression 💪
**When to use:**
- Quiz failed (motivation)
- Low scores
- Struggling with content
- After multiple wrong answers
- Daily goal progress

**Example:**
```
     💪
    /   \
  "Đừng nản! Cố lên nhé!"
```

---

### 4. Sad Expression 😢
**When to use:**
- Streak about to break
- No activity for days
- Failed attempts

**Example:**
```
     😢
    /   \
  "Đừng để streak bị mất!"
```

---

### 5. Worried Expression 😟
**When to use:**
- Streak warning (24h remaining)
- Hearts running low
- Quiz time running out

**Example:**
```
     😟
    /   \
  "Streak của bạn sắp mất rồi!"
```

---

### 6. Excited Expression 🤩
**When to use:**
- New feature unlocked
- Special events
- Bonus gems earned
- New achievements

**Example:**
```
     🤩
    /   \
  "Wow! Thật tuyệt vời!"
```

---

## Mascot Bubble Layout

```
┌─────────────────────────────────┐
│  🦉                             │
│   ╭─────────────────────────╮   │
│   │ Bạn làm tốt lắm! 🎉     │   │
│   │                         │   │
│   │ Nhấn để đóng            │   │
│   ╰─────────────────────────╯   │
└─────────────────────────────────┘
```

### Components:
1. **Mascot Avatar** (left): Animated emoji, 50x50
2. **Speech Bubble** (right): White container with message
3. **Dismiss Hint**: "Nhấn để đóng" in gray
4. **Auto-dismiss**: 3 seconds (customizable)

---

## Integration Examples

### Explore Screen Header
```
┌──────────────────────────────────┐
│ 🦉  Cửu Đỉnh          [Progress] │
│     Khám phá 9 chiếc đỉnh...     │
└──────────────────────────────────┘
```

### Quiz Result - Perfect Score
```
┌──────────────────────────────────┐
│          🎉 100% 🎉              │
│      Hoàn hảo! Tuyệt vời!        │
│                                  │
│  ┌────────────────────────────┐  │
│  │ 🎉                         │  │
│  │  ╭──────────────────────╮  │  │
│  │  │ Hoàn hảo 100%!       │  │  │
│  │  │ Bạn quá tuyệt! 🌟    │  │  │
│  │  ╰──────────────────────╯  │  │
│  └────────────────────────────┘  │
└──────────────────────────────────┘
```

### Login Screen
```
┌──────────────────────────────────┐
│                                  │
│          🦉 (animated)           │
│      Lưu Niên Sử Kí             │
│   Đăng nhập để tiếp tục          │
│                                  │
│   ┌────────────────────┐         │
│   │ Email              │         │
│   └────────────────────┘         │
│   ┌────────────────────┐         │
│   │ Password           │         │
│   └────────────────────┘         │
│   ┌────────────────────┐         │
│   │   ĐĂNG NHẬP        │         │
│   └────────────────────┘         │
└──────────────────────────────────┘
```

### Lesson Completion
```
┌──────────────────────────────────┐
│  ✅ Bài học hoàn thành!          │
│                                  │
│  +50 XP earned!                  │
│                                  │
│  ┌────────────────────────────┐  │
│  │ 🎉                         │  │
│  │  ╭──────────────────────╮  │  │
│  │  │ Bài học hoàn thành! │  │  │
│  │  │ Tuyệt lắm! 📚       │  │  │
│  │  ╰──────────────────────╯  │  │
│  └────────────────────────────┘  │
│                                  │
│  [TIẾP TỤC]   [LÀM BÀI QUIZ]    │
└──────────────────────────────────┘
```

---

## Animation Behavior

### Bounce Animation
```
Position over time (1.5s cycle):

   🦉     Start
    ↑
   🦉     Move up (-10px)
    ↓
   🦉     Bounce down
    ↓
   🦉     Return to start
```

### Rotation Animation
```
Rotation over time (1.5s cycle):

   🦉     0°    (Start)
   🦉     +18°  (Tilt right)
   🦉     -18°  (Tilt left)
   🦉     +18°  (Tilt right)
   🦉     0°    (Return)
```

### Bubble Appearance
```
Frame 1: Scale 0.0, Opacity 0.0
Frame 2: Scale 0.5, Opacity 0.5
Frame 3: Scale 1.0, Opacity 1.0 (300ms)
```

---

## Color Palette

### Mascot
- **Emoji-based**: Platform-dependent rendering
- **Background**: Transparent
- **Size**: 32-80px depending on context

### Speech Bubble
- **Background**: `#FFFFFF` (white)
- **Text**: `AppColors.textPrimary` (dark gray/black)
- **Shadow**: `rgba(0,0,0,0.1)` with 10px blur
- **Border Radius**: 20px
- **Padding**: 16px

### Hint Text
- **Color**: `rgba(0,0,0,0.6)` (60% gray)
- **Font Size**: 12px
- **Style**: Italic

---

## Responsive Behavior

### Mobile (< 600px)
- Bubble max width: `screen width - 32px`
- Mascot size: 50px
- Font size: 15px

### Tablet (600-900px)
- Bubble max width: `500px`
- Mascot size: 60px
- Font size: 16px

### Desktop (> 900px)
- Bubble max width: `500px`
- Mascot size: 60px
- Font size: 16px

---

## Accessibility

1. **Semantic Labels**: All mascot widgets should have semantic labels
2. **Screen Reader**: Messages should be announced
3. **High Contrast**: Ensure text contrast ratio > 4.5:1
4. **Reduced Motion**: Respect `prefers-reduced-motion` setting
5. **Tap Targets**: Minimum 44x44 for interactive elements

---

## Best Practices

✅ **DO:**
- Show mascot at meaningful moments
- Use appropriate expressions for context
- Keep messages short and encouraging
- Allow users to dismiss quickly
- Time appearance after other animations

❌ **DON'T:**
- Show mascot too frequently
- Block critical UI elements
- Use mismatched expressions
- Make messages too long
- Force users to wait for mascot

---

## Implementation Checklist

- [x] Mascot widget with expressions
- [x] Speech bubble component
- [x] Message library
- [x] Explore screen integration
- [x] Quiz result integration
- [x] Lesson completion integration
- [x] Login screen integration
- [ ] Empty state integration (optional)
- [ ] Streak warning system (future)
- [ ] Push notification integration (future)


