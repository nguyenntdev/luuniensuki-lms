# Badge Unlock Notifications - Visual Reference

## Component Hierarchy

```
RootLayout (layout.jsx)
└── XpCelebrationProvider
    └── BadgeUnlockProvider ⭐ (NEW)
        └── App Content
            └── BadgeUnlockToast (when badge unlocked)
```

## Toast Appearance

### Desktop View
```
                                    ┌──────────────────────────────────┐
                                    │  ┌────┐  Huy hiệu mới!      [×] │
                                    │  │ 🏅 │  Người Mới Bắt Đầu       │
                                    │  └────┘  Hoàn thành quiz đầu... │
                                    └──────────────────────────────────┘
                                                    ↑
                                            (bottom-right corner)
```

### Mobile View
```
┌─────────────────────────────┐
│  ┌──┐  Huy hiệu mới!    [×] │
│  │🏅│  Người Mới Bắt Đầu     │
│  └──┘  Hoàn thành quiz...   │
└─────────────────────────────┘
        ↑
(bottom-right corner)
```

## Animation Timeline

```
Time: 0s           0.5s                    5s          5.3s
      │             │                      │            │
      ▼             ▼                      ▼            ▼
   [Hidden]  [Fully Visible]        [Auto-dismiss]  [Hidden]
      │             │                      │            │
      └─────────────┴──────────────────────┴────────────┘
           Slide Up              Display          Slide Down
         (translate-y)         (5 seconds)      (translate-y)
         (opacity 0→1)                          (opacity 1→0)
```

## Multiple Badges Sequence

```
Badge 1: ████████████░░░░░░░░░░░░░░░░░░░░░░  (0s - 5.3s)
Badge 2:             ░░░░░░████████████░░░░░  (6s - 11.3s)
Badge 3:                           ░░░░░░████ (12s - 17.3s)
         ↑           ↑              ↑
       Start      6s gap        12s gap
```

## Color Scheme

### Background Gradient
```
from-yellow-500 ──────► to-amber-600
   #F59E0B                #D97706
     ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓
```

### Text Colors
- Header: `text-yellow-100` (#FEF3C7)
- Title: `text-white` (#FFFFFF)
- Description: `text-yellow-100` (#FEF3C7)
- Close button: `text-white/70` (70% opacity)

## Layout Structure

```
┌───────────────────────────────────────────────────────┐
│ [Container: fixed bottom-4 right-4]                   │
│  ┌─────────────────────────────────────────────────┐  │
│  │ [Inner: gradient bg, rounded-lg, p-4]           │  │
│  │  ┌────────┐  ┌──────────────────┐  ┌─────┐     │  │
│  │  │ Icon   │  │  Text Content    │  │  X  │     │  │
│  │  │ 64×64  │  │  - Header        │  │ Btn │     │  │
│  │  │ Circle │  │  - Badge Name    │  │     │     │  │
│  │  │        │  │  - Description   │  │     │     │  │
│  │  └────────┘  └──────────────────┘  └─────┘     │  │
│  │  flex gap-4                                     │  │
│  └─────────────────────────────────────────────────┘  │
│  max-w-sm                                             │
└───────────────────────────────────────────────────────┘
```

## State Flow Diagram

```
┌─────────────────┐
│  Quiz/Lesson    │
│   Completed     │
└────────┬────────┘
         │ API returns badges_awarded
         ▼
┌─────────────────┐
│ showUnlockBadge │
│    (action)     │
└────────┬────────┘
         │ Updates store
         ▼
┌─────────────────┐
│  badgeStore     │
│  unlockedBadge  │
└────────┬────────┘
         │ Provider listens
         ▼
┌─────────────────┐
│ BadgeUnlockToast│
│   Rendered      │
└────────┬────────┘
         │ After 5s
         ▼
┌─────────────────┐
│ clearUnlockBadge│
│    (action)     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Toast Hidden   │
└─────────────────┘
```

## Icon Rendering Logic

```
badge.icon_url exists?
    │
    ├─ YES → <img src={badge.icon_url} />
    │         (w-12 h-12, object-contain)
    │
    └─ NO → <Award className="w-8 h-8" />
            (lucide-react icon)
```

## Responsive Behavior

### Desktop (>768px)
- Position: bottom-4 right-4
- Max width: 24rem (384px)
- Full description visible (2 lines max)

### Tablet (768px - 1024px)
- Same as desktop
- Toast adjusts to viewport width
- Description may wrap

### Mobile (<768px)
- Position: bottom-4 right-4 (adapts to screen)
- Max width: calc(100vw - 2rem)
- Description truncates with ellipsis
- Icon size maintained for visibility

## Z-Index Hierarchy

```
Layer 5 (z-50):  BadgeUnlockToast    ← Badge notifications
Layer 4 (z-50):  XpCelebrationOverlay ← XP celebrations
Layer 3 (z-40):  Modal overlays
Layer 2 (z-30):  Toasts (react-hot-toast)
Layer 1 (z-20):  Floating elements
Layer 0 (z-10):  Navigation
```

## Interaction States

### Default
- Opacity: 100%
- Transform: translateY(0)

### Hover (close button)
- Color: white/70 → white
- Transition: 150ms

### Click (close button)
- Immediately triggers exit animation
- Calls onClose after 300ms

## Accessibility

```html
<div role="region" aria-live="polite">
  <button aria-label="Đóng thông báo">
    <X />
  </button>
</div>
```

- Implicit ARIA role via semantic HTML
- Close button has descriptive label
- Non-intrusive auto-dismiss behavior

## File Dependencies

```
BadgeUnlockToast.jsx
├── react (useEffect, useState)
├── lucide-react (X, Award icons)
└── Tailwind CSS (styling)

BadgeUnlockProvider.jsx
├── react (default export)
├── badgeStore (Zustand)
└── BadgeUnlockToast

badgeStore.js
└── zustand (create)
```

