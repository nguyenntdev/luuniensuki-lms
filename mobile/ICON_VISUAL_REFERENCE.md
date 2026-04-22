# Material Icons - Visual Reference

This document provides a visual reference for all icon replacements in the Explore page.

## 🎯 Status Icons (Stats Display)

### Before & After

#### Discovered Motifs
```
BEFORE: 👁️ 5/10
AFTER:  👁  5/10  (Icons.visibility_rounded, blue)
```

#### Learned Motifs
```
BEFORE: 📚 3
AFTER:  📖 3   (Icons.menu_book_rounded, green)
```

#### Mastered Motifs
```
BEFORE: ⭐ 1
AFTER:  ⭐ 1   (Icons.star_rounded, gold)
```

### Icon Details
| Old Emoji | New Icon | Material Icon Name | Color | Size |
|-----------|----------|-------------------|-------|------|
| 👁️ | 👁 | `Icons.visibility_rounded` | `AppColors.info` (#60A5FA) | 16px |
| 📚 | 📖 | `Icons.menu_book_rounded` | `AppColors.success` (#34D399) | 16px |
| ⭐ | ⭐ | `Icons.star_rounded` | `AppColors.primary` (#E8B44C) | 16px |

---

## 🔥 Streak Icons

### Before & After

#### Active Streak
```
BEFORE: 🔥 15 ngày
AFTER:  🔥 15 ngày  (Icons.local_fire_department_rounded, orange)
```

#### No Streak
```
BEFORE: ❄️ 0 ngày
AFTER:  ❄  0 ngày  (Icons.ac_unit_rounded, light blue)
```

#### At Risk
```
BEFORE: ⚠️ 7 ngày - Sắp mất chuỗi!
AFTER:  ⚠  7 ngày - Sắp mất chuỗi!  (Icons.warning_rounded, red)
```

#### Freeze Count
```
BEFORE: ❄️ 3
AFTER:  ❄  3   (Icons.ac_unit_rounded, light blue)
```

### Icon Details
| Old Emoji | New Icon | Material Icon Name | Color | Size | Glow |
|-----------|----------|-------------------|-------|------|------|
| 🔥 | 🔥 | `Icons.local_fire_department_rounded` | `AppColors.streakOrange` (#FF6B35) | 18px | Yes |
| ❄️ | ❄ | `Icons.ac_unit_rounded` | `Colors.lightBlue` | 14-18px | No |
| ⚠️ | ⚠ | `Icons.warning_rounded` | `Colors.red` | 18px | Yes |

---

## 🏆 Milestone Icons

### Before & After

#### 7 Days (Week Perfect)
```
BEFORE: Còn 2 ngày đến ⭐
AFTER:  Còn 2 ngày đến ⭐  (Icons.star_rounded, gold)

CELEBRATION:
BEFORE: ⭐ (80px emoji)
        Tuần Hoàn Hảo
AFTER:  ⭐ (56px icon with glow)
        Tuần Hoàn Hảo
```

#### 30 Days (Diligent Learner)
```
BEFORE: Còn 5 ngày đến 🎯
AFTER:  Còn 5 ngày đến 🎯  (Icons.track_changes_rounded, purple)

CELEBRATION:
BEFORE: 🎯 (80px emoji)
        Người Học Chăm Chỉ
AFTER:  🎯 (56px icon with glow)
        Người Học Chăm Chỉ
```

#### 100 Days (Master of Persistence)
```
BEFORE: Còn 15 ngày đến 🏆
AFTER:  Còn 15 ngày đến 🏆  (Icons.emoji_events_rounded, amber)

CELEBRATION:
BEFORE: 🏆 (80px emoji)
        Bậc Thầy Kiên Trì
AFTER:  🏆 (56px icon with glow)
        Bậc Thầy Kiên Trì
```

#### 365 Days (Invincible Warrior)
```
BEFORE: Còn 50 ngày đến 👑
AFTER:  Còn 50 ngày đến 🏆  (Icons.emoji_events_rounded, gold)

CELEBRATION:
BEFORE: 👑 (80px emoji)
        Chiến Binh Bất Bại
AFTER:  🏆 (56px icon with glow)
        Chiến Binh Bất Bại
```

### Icon Details
| Milestone | Old Emoji | New Icon | Material Icon Name | Color | Inline Size | Celebration Size |
|-----------|-----------|----------|-------------------|-------|-------------|-----------------|
| 7 days | ⭐ | ⭐ | `Icons.star_rounded` | `AppColors.primary` | 12px | 56px |
| 30 days | 🎯 | 🎯 | `Icons.track_changes_rounded` | `Colors.purple` | 12px | 56px |
| 100 days | 🏆 | 🏆 | `Icons.emoji_events_rounded` | `Colors.amber` | 12px | 56px |
| 365 days | 👑 | 🏆 | `Icons.emoji_events_rounded` | `AppColors.xpGold` | 12px | 56px |

---

## 📊 Component Breakdown

### Explore Screen Header

```
┌─────────────────────────────────────────────────┐
│ Khám Phá                  [🔥 15]  [@Avatar]    │
│                                                  │
│ ┌──────────────────────────────────────────┐   │
│ │  👁 5/10  │  📖 3  │  ⭐ 1              │   │
│ └──────────────────────────────────────────┘   │
└─────────────────────────────────────────────────┘
```

### Streak Widget (Expanded)

```
┌──────────────────────────────────┐
│  ┌──┐                            │
│  │🔥│  15 ngày                   │
│  └──┘  Còn 2 ngày đến ⭐    [❄ 3]│
└──────────────────────────────────┘
```

### Urn Card Stats

```
┌────────────────────┐
│                    │
│   [URN IMAGE]      │
│                    │
├────────────────────┤
│  Bình Đông Sơn     │
│                    │
│ [Progress Bar]     │
│ 👁 2/5 📖 1/5 ⭐ 0/5│
└────────────────────┘
```

---

## 🎨 Color Palette

### Status Colors
```
Discovered:  #60A5FA ████ (Info Blue)
Learned:     #34D399 ████ (Success Green)
Mastered:    #E8B44C ████ (Primary Gold)
```

### Streak Colors
```
Fire:        #FF6B35 ████ (Streak Orange)
Freeze:      #ADD8E6 ████ (Light Blue)
Warning:     #FF0000 ████ (Red)
```

### Milestone Colors
```
7 days:      #E8B44C ████ (Primary Gold)
30 days:     #9C27B0 ████ (Purple)
100 days:    #FFC107 ████ (Amber)
365 days:    #FFD700 ████ (XP Gold)
```

---

## 🔍 Implementation Details

### Sizing Guidelines
- **Inline stats icons**: 14-16px
- **Streak widget icons**: 18px
- **Milestone inline icons**: 12px
- **Milestone celebration icons**: 56px
- **Urn card stats icons**: 14px

### Spacing Guidelines
- **Icon to text**: 4-6px gap
- **Between stats**: 8-12px with divider
- **Icon padding**: 2-4px

### Effects
- **Glow shadows**: Active streaks and warnings
- **Colored backgrounds**: Optional for status icons
- **Radial gradients**: Milestone celebration backgrounds

---

## ✅ Testing Checklist

Visual verification:
- [ ] All stats icons display correctly in header
- [ ] Streak icon changes based on state (fire/freeze/warning)
- [ ] Milestone icons appear in progress text
- [ ] Celebration overlays show large milestone icons
- [ ] Colors match design system
- [ ] Icons scale properly on different screen sizes
- [ ] Vietnamese text remains intact
- [ ] Animations work smoothly
- [ ] No emoji artifacts or rendering issues

