# 🔔 Notifications Screen - Visual Reference

## Screen Anatomy

```
┌─────────────────────────────────────────┐
│ ← Thông báo              [✓✓]  [⋮]     │ ← App Bar
│   5 chưa đọc                            │ ← Unread Badge
├─────────────────────────────────────────┤
│                                         │
│ ┌─────────────────────────────────────┐ │
│ │ ● [🏆] Huy hiệu mới!               │ │ ← Unread
│ │        Bạn đã mở khóa huy hiệu...  │ │   Achievement
│ │        30 phút trước                │ │   (Purple)
│ └─────────────────────────────────────┘ │
│                                         │
│ ┌─────────────────────────────────────┐ │
│ │ ● [🔥] Chuỗi học tập 7 ngày!       │ │ ← Unread
│ │        Tuyệt vời! Bạn đã duy trì... │ │   Streak
│ │        2 giờ trước                  │ │   (Orange)
│ └─────────────────────────────────────┘ │
│                                         │
│ ┌─────────────────────────────────────┐ │
│ │   [🎓] Bài học mới                 │ │ ← Read
│ │        Bài học về "Hoa văn rồng"... │ │   Lesson
│ │        5 giờ trước                  │ │   (Blue)
│ └─────────────────────────────────────┘ │
│                                         │
│ ┌─────────────────────────────────────┐ │
│ │   [ℹ️] Cập nhật ứng dụng            │ │ ← Read
│ │        Phiên bản mới với nhiều...   │ │   System
│ │        1 ngày trước                 │ │   (Gold)
│ └─────────────────────────────────────┘ │
└─────────────────────────────────────────┘
```

## Notification Card States

### 🟣 Unread Notification
```
┌───────────────────────────────────────────┐
│ ● [Icon]  Title (Bold)                    │
│           Message text (2 lines max)       │
│           Time ago                         │
└───────────────────────────────────────────┘
↑
Glowing dot with shadow
```

**Visual Indicators:**
- Glowing colored dot (●)
- Bold title text
- Icon with gradient background + shadow
- Card has subtle glow

### ⚪ Read Notification
```
┌───────────────────────────────────────────┐
│   [Icon]  Title (Semi-bold)               │
│           Message text (2 lines max)       │
│           Time ago                         │
└───────────────────────────────────────────┘
```

**Visual Indicators:**
- No dot
- Semi-bold title
- Icon without extra glow
- Standard card appearance

## Notification Types & Colors

### 🏆 Achievement (Purple #9C27B0)
```
[Icon: trophy emoji_events]
Examples:
- Badge unlocked
- Level up
- Milestone reached
```

### 🔥 Streak (Orange #FF6B35)
```
[Icon: fire local_fire_department]
Examples:
- 7-day streak
- 30-day streak
- Streak milestone
```

### 🎓 Lesson (Blue #60A5FA)
```
[Icon: school]
Examples:
- New lesson available
- Lesson completed
- Content update
```

### 👥 Social (Green #34D399)
```
[Icon: people]
Examples:
- New follower
- Comment received
- Mention
```

### ℹ️ System (Gold #E8B44C)
```
[Icon: info_outline]
Examples:
- App update
- Maintenance notice
- System announcement
```

## Interactive States

### 🔄 Swipe to Delete
```
Before:
┌───────────────────────────────────────────┐
│ [Notification Card]                       │
└───────────────────────────────────────────┘

Swiping Left:
┌───────────────────────────────────────────┐
│ [Notification Card]          [🗑️]        │
│                              Delete        │
└───────────────────────────────────────────┘
             ← Red gradient background

After Delete:
[Snackbar: "Đã xóa thông báo"]
```

### 👆 Tap Interaction
```
Tap on unread → Mark as read + Navigate (if actionUrl exists)
Tap on read   → Navigate only (if actionUrl exists)
```

## App Bar Components

### Left Side
```
[←] Thông báo
    5 chưa đọc
    ↑ Unread count (gold color)
```

### Right Side
```
[✓✓] Mark all read (only if unread > 0)
[⋮]  Menu
     ├─ Xóa tất cả (red, with icon)
```

## Empty State

```
                ┌─────────┐
                │         │
                │   🔔    │  ← Large icon in circle
                │         │     with gradient
                └─────────┘
                
         Chưa có thông báo
         
   Bạn sẽ nhận được thông báo về
   các hoạt động và thành tích của mình
```

**Styling:**
- Circle: 120x120px
- Icon: 60px, white 50% opacity
- Border: white 20% opacity, 2px
- Background: gold gradient (20% → 10% opacity)
- Text: centered, white with varying opacity

## Animation Timeline

### Entrance Animation (600ms)
```
0ms                     600ms
│                         │
├─ Screen Fade In ────────┤
   0% → 100% opacity
   Curve: easeOut
```

### List Item Animation (Staggered)
```
Item 0: 0ms     → 600ms
Item 1: 100ms   → 700ms
Item 2: 200ms   → 800ms
Item 3: 300ms   → 900ms
...
│                         │
├─ Fade In (60%) ─────────┤
│  0% → 100% opacity
│
├─ Slide In (80%) ────────┤
   Offset(0.3, 0) → Offset.zero
   Curve: easeOutCubic
```

### Swipe Delete Animation
```
Swipe:
│                         │
├─ Red Background ────────┤
│  Fade in gradually
│
├─ Delete Icon ───────────┤
   Slide in from right
```

## Pull to Refresh

```
Pull Down:
┌───────────────────────────┐
│         ⟳                 │ ← Spinner
│    [Refreshing...]        │
├───────────────────────────┤
│ [Notification Cards]      │
└───────────────────────────┘

Colors:
- Spinner: AppColors.primary (gold)
- Background: AppColors.surface
```

## Dialog - Clear All

```
┌─────────────────────────────────────┐
│ [🗑️]  Xóa tất cả                   │
├─────────────────────────────────────┤
│                                     │
│ Bạn có chắc chắn muốn xóa tất cả    │
│ thông báo?                          │
│                                     │
├─────────────────────────────────────┤
│              [Hủy]  [Xóa tất cả]   │
└─────────────────────────────────────┘

Styling:
- Background: AppColors.surface
- Border: white 15% opacity
- Icon bg: red gradient
- Delete button: red background
- Cancel button: text only
```

## Spacing & Dimensions

### Card
```
Padding: 16px all around
Gap between items: 16px
Border radius: 16px (AppSpacing.radiusLG)
Icon container: 48x48px
Icon: 24px
```

### Screen
```
App bar height: ~56px
Content padding: 16px
List item height: ~100px (dynamic)
Empty state icon: 120x120px
```

### Typography
```
Title: 16px, weight 700/600
Message: 14px, weight 400
Time: 12px, weight 400
App bar title: 20px, weight 700
Unread badge: 12px, weight 500
```

## Color Opacity Guide

```
Text Primary:     white 100%
Text Secondary:   white 70%
Text Tertiary:    white 60%
Text Hint:        white 50%
Border:           white 20%
Glass Container:  white 8-10%
Icon Background:  type-color 30% → 10%
Glow Shadow:      type-color 20-40%
```

## Responsive Behavior

### Portrait
- Standard layout as shown
- Cards full width with padding

### Landscape
- Same layout (no special handling needed)
- Scrollable content

### Small Screens
- Text may wrap to 2 lines
- All spacing maintained
- Scrollable as needed

## Accessibility

### Tap Targets
- All cards: ≥ 48x48px
- App bar buttons: 48x48px
- Menu items: 48px height

### Contrast
- Title: 16.6:1 (white on dark)
- Message: 11.6:1 (70% white)
- Icons: High contrast on gradient

### Semantic Labels
- Icons: Meaningful type indicators
- Actions: Clear button labels
- States: Visual + textual indicators

---

**Legend:**
- ● = Unread indicator dot
- [Icon] = Type-specific icon
- ← → ↑ ↓ = Direction indicators
- [Button] = Interactive element
- ... = Truncated text

