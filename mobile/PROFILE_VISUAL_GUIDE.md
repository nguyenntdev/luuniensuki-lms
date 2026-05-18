# 📸 Profile Screen Visual Guide

## Screen Layout (Top to Bottom)

```
┌─────────────────────────────────────┐
│  🌅 GRADIENT HEADER SECTION         │
│  ┌─────────────────────────────┐   │
│  │   ✨ Hero Avatar (120x120)  │   │
│  │   with golden glow          │   │
│  └─────────────────────────────┘   │
│                                     │
│       John Doe                      │
│       📧 john@example.com           │
│                                     │
│    🏅 [Scholar] Rank Badge          │
│                                     │
├─────────────────────────────────────┤
│                                     │
│  💎 XP Progress Card                │
│  ┌─────────────────────────────┐   │
│  │ ⭐ 1,250 XP    🏅 Scholar   │   │
│  │                → Expert      │   │
│  │                              │   │
│  │ ▓▓▓▓▓▓▓░░░░░ 60%           │   │
│  │ 500 XP to next level        │   │
│  └─────────────────────────────┘   │
│                                     │
│  📊 Stats Grid                      │
│  ┌──────┐ ┌──────┐ ┌──────┐       │
│  │ 👁️ 12 │ │ 📚 16 │ │ 🏆 0  │      │
│  │Discov│ │Lesson│ │Badge │      │
│  └──────┘ └──────┘ └──────┘       │
│                                     │
│  🔥 Streak Card                     │
│  ┌─────────────────────────────┐   │
│  │ 🔥  7 days 🔥               │   │
│  │     Current Streak          │   │
│  │                    🏆 10     │   │
│  │                    ❄️ 2      │   │
│  └─────────────────────────────┘   │
│                                     │
│  ⚙️ Settings & Account              │
│                                     │
│  ┌─────────────────────────────┐   │
│  │ 👤  Personal Info           │   │
│  │     Edit profile & avatar  ❯│   │
│  └─────────────────────────────┘   │
│                                     │
│  ┌─────────────────────────────┐   │
│  │ 🔔  Notifications           │   │
│  │     Manage reminders       ❯│   │
│  └─────────────────────────────┘   │
│                                     │
│  ┌─────────────────────────────┐   │
│  │ ⚙️  Settings                │   │
│  │     Customize app          ❯│   │
│  └─────────────────────────────┘   │
│                                     │
│  ┌─────────────────────────────┐   │
│  │ ❓  Help & Support          │   │
│  │     FAQ and contact        ❯│   │
│  └─────────────────────────────┘   │
│                                     │
│  ┌─────────────────────────────┐   │
│  │   🚪  Logout (Red Theme)    │   │
│  └─────────────────────────────┘   │
│                                     │
└─────────────────────────────────────┘
```

---

## Color Legend

```
🟡 Gold Gradient    - Header background, avatar, XP star
🔵 Blue            - Discovered stat
🟢 Green           - Lessons stat
🟣 Purple          - Badges stat
🟠 Orange          - Streak (when active)
🔴 Red             - Logout button
⚪ White/Glass     - Container backgrounds
```

---

## Component Details

### 1. Avatar (Top)
```
╔═════════════════╗
║                 ║
║    ✨ Avatar    ║
║   120 x 120    ║
║                 ║
║  Golden Glow   ║
║   Effect 🌟    ║
╚═════════════════╝
```
- Circular with 4px white border
- Dual shadow layers (gold)
- Hero animation ready
- Fallback to initials

### 2. XP Card
```
┌─────────────────────────────┐
│ ┌──┐ Kinh nghiệm    Scholar │
│ │⭐│ 1,250 XP      → Expert │
│ └──┘                        │
│                             │
│ 500 XP to level up    60%   │
│ ▓▓▓▓▓▓▓▓░░░░░░░░░░░        │
└─────────────────────────────┘
```
- Glass container with gold gradient
- Star icon in gradient box
- Progress bar with glow
- Percentage badge

### 3. Stats Grid
```
┌──────┐  ┌──────┐  ┌──────┐
│ ┌──┐ │  │ ┌──┐ │  │ ┌──┐ │
│ │👁️│ │  │ │📚│ │  │ │🏆│ │
│ └──┘ │  │ └──┘ │  │ └──┘ │
│  12  │  │  16  │  │   0  │
│ Disc │  │Lesn  │  │Badge │
└──────┘  └──────┘  └──────┘
  Blue      Green     Purple
```
- Each card has themed gradient
- Icon in colored container
- Equal width columns

### 4. Streak Card
```
┌───────────────────────────┐
│ ┌────┐                    │
│ │ 🔥 │  7 days 🔥         │
│ │    │  Current Streak    │
│ └────┘             ┌────┐ │
│                    │🏆10│ │
│                    │❄️ 2│ │
│                    └────┘ │
└───────────────────────────┘
```
- Orange glow when active
- 64x64 fire icon container
- Stat badges on right

### 5. Menu Cards
```
┌─────────────────────────────┐
│ ┌────┐                      │
│ │ 👤 │  Title               │
│ │    │  Description       ❯ │
│ └────┘                      │
└─────────────────────────────┘
```
- Icon: 48x48 with gradient bg
- Title: 16px bold white
- Subtitle: 12px white 60%
- Chevron: right indicator

### 6. Logout Button
```
┌─────────────────────────────┐
│     🚪  Logout (Red)        │
└─────────────────────────────┘
```
- Full width, centered
- Red gradient background
- Icon + text layout

---

## Animation Sequence

### Screen Load (800ms total)

```
0ms        200ms       480ms      800ms
│           │           │          │
▼           ▼           ▼          ▼
Start    Fade       Fade      Animation
         Begins     Done       Complete
         ├──────────┤
         Fade: 0→1 (60%)
         
         └──────────────────────┘
         Slide: Offset(0,0.3)→(0,0)
                 (20-100%)
```

**Result**: Content fades in while sliding up smoothly

---

## Interaction Map

```
Tap Zones:
═══════════

[Avatar]        → (No action - visual only)
[Rank Badge]    → (No action - visual only)
[XP Card]       → (No action - could add tap)
[Stats Cards]   → (No action - could add tap)
[Streak Card]   → (No action - could add tap)
[Menu Cards]    → Shows "Coming soon" snackbar
[Logout]        → Shows confirmation dialog
```

---

## Logout Dialog

```
┌─────────────────────────────┐
│  🚪  Logout                 │
├─────────────────────────────┤
│                             │
│  Are you sure you want to   │
│  logout from your account?  │
│                             │
├─────────────────────────────┤
│        Cancel    [Logout]   │
└─────────────────────────────┘
```
- Icon in title with gradient
- White text on dark surface
- Cancel (text) + Logout (red button)

---

## Responsive Behavior

### Small Screen (< 360px width)
- Stats grid remains in row
- Text truncates with ellipsis
- Scroll enabled throughout
- All touch targets >= 44x44

### Medium Screen (360-600px)
- Optimal layout
- All content visible
- Comfortable spacing

### Large Screen (> 600px)
- Content stays centered
- Max width could be applied
- More whitespace

---

## Glass Effect Details

```
Container Stack:
┌─────────────────┐
│ Content         │ ← Your widgets
├─────────────────┤
│ Border (1.5px)  │ ← white 20% opacity
├─────────────────┤
│ Background      │ ← white 8-15% + gradient
├─────────────────┤
│ Shadow          │ ← black 20%, blur 20px
└─────────────────┘
     ↓
Animated gradient
background below
```

---

## Theme Integration

All colors derived from `AppColors`:
- `primary` → Gold base color
- `primaryDark` → Darker gold
- `primaryLight` → Lighter gold
- `info` → Blue for discovered
- `success` → Green for lessons
- `badgePurple` → Purple for badges
- `streakOrange` → Orange for streak
- `error` → Red for logout

All spacing from `AppSpacing`:
- `xs, sm, md, lg, xl, xxl` → Base scale
- `radiusXS, SM, MD, LG, XL` → Border radius

---

## Accessibility Features

✅ Color contrast ratios meet WCAG AA
✅ Touch targets >= 44x44 points  
✅ Text hierarchy with size/weight
✅ Icon + text labels for clarity
✅ Error states clearly indicated
✅ Loading states (from provider)

---

This visual guide shows the complete layout and design system integration!

