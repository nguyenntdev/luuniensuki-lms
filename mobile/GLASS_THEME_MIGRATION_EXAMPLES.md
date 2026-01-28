# GlassTheme Helper Methods - Migration Examples

## 🔄 How to Migrate Existing Code

### Example 1: Practice Mode Cards

**Before:**
```dart
Container(
  padding: const EdgeInsets.all(16),
  decoration: BoxDecoration(
    gradient: LinearGradient(
      begin: Alignment.topLeft,
      end: Alignment.bottomRight,
      colors: [
        mode.color.withOpacity(0.15),
        mode.color.withOpacity(0.05),
      ],
    ),
    borderRadius: BorderRadius.circular(20),
    border: Border.all(
      color: mode.isLocked
          ? Colors.white.withOpacity(0.1)
          : mode.color.withOpacity(0.3),
      width: 1.5,
    ),
  ),
  child: ModeContent(),
)
```

**After:**
```dart
Container(
  padding: const EdgeInsets.all(16),
  decoration: GlassTheme.coloredCardDecoration(
    color: mode.color,
    isDisabled: mode.isLocked,
  ),
  child: ModeContent(),
)
```

**Savings:** -15 lines, clearer intent

---

### Example 2: Feature Cards with Different Colors

**Before:**
```dart
// Discovery Card
Container(
  decoration: BoxDecoration(
    gradient: LinearGradient(
      begin: Alignment.topLeft,
      end: Alignment.bottomRight,
      colors: [
        GlassTheme.accentBlue.withOpacity(0.15),
        GlassTheme.accentBlue.withOpacity(0.05),
      ],
    ),
    borderRadius: BorderRadius.circular(20),
    border: Border.all(
      color: GlassTheme.accentBlue.withOpacity(0.3),
      width: 1.5,
    ),
  ),
)

// Learned Card
Container(
  decoration: BoxDecoration(
    gradient: LinearGradient(
      begin: Alignment.topLeft,
      end: Alignment.bottomRight,
      colors: [
        GlassTheme.accentGreen.withOpacity(0.15),
        GlassTheme.accentGreen.withOpacity(0.05),
      ],
    ),
    borderRadius: BorderRadius.circular(20),
    border: Border.all(
      color: GlassTheme.accentGreen.withOpacity(0.3),
      width: 1.5,
    ),
  ),
)
```

**After:**
```dart
// Discovery Card
Container(
  decoration: GlassTheme.coloredCardDecoration(
    color: GlassTheme.accentBlue,
  ),
)

// Learned Card
Container(
  decoration: GlassTheme.coloredCardDecoration(
    color: GlassTheme.accentGreen,
  ),
)
```

**Savings:** -26 lines for 2 cards

---

### Example 3: Status Badges

**Before:**
```dart
// Completed Badge
Container(
  decoration: BoxDecoration(
    gradient: LinearGradient(
      colors: [
        GlassTheme.accentGreen,
        GlassTheme.accentGreen.withOpacity(0.8),
      ],
    ),
    borderRadius: BorderRadius.circular(12),
    border: Border.all(
      color: GlassTheme.accentGreen,
      width: 1.5,
    ),
    boxShadow: [
      BoxShadow(
        color: GlassTheme.accentGreen.withOpacity(0.3),
        blurRadius: 8,
        offset: const Offset(0, 2),
      ),
    ],
  ),
)

// Pending Badge
Container(
  decoration: BoxDecoration(
    gradient: LinearGradient(
      colors: [
        AppColors.surface.withOpacity(0.9),
        AppColors.surface.withOpacity(0.85),
      ],
    ),
    borderRadius: BorderRadius.circular(12),
    border: Border.all(
      color: Colors.white.withOpacity(0.25),
      width: 1.5,
    ),
    boxShadow: [
      BoxShadow(
        color: Colors.black.withOpacity(0.3),
        blurRadius: 8,
        offset: const Offset(0, 2),
      ),
    ],
  ),
)
```

**After:**
```dart
// Completed Badge
Container(
  decoration: GlassTheme.statusBadgeDecoration(
    isActive: true,
    activeColor: GlassTheme.accentGreen,
  ),
)

// Pending Badge
Container(
  decoration: GlassTheme.statusBadgeDecoration(
    isActive: false,
    activeColor: GlassTheme.accentGreen,
  ),
)
```

**Savings:** -36 lines for 2 badges

---

## 🎯 Quick Reference

| Use Case | Method | Key Parameters |
|----------|--------|----------------|
| Colored glass card | `coloredCardDecoration()` | `color`, `isDisabled` |
| Disabled/locked card | `coloredCardDecoration(isDisabled: true)` | `color`, `isDisabled: true` |
| Active status badge | `statusBadgeDecoration(isActive: true)` | `isActive: true`, `activeColor` |
| Inactive status badge | `statusBadgeDecoration(isActive: false)` | `isActive: false`, `activeColor` |

---

## 📊 Impact Summary

For a typical screen with 3 mode cards and 2 status badges:

- **Before:** ~100 lines of BoxDecoration code
- **After:** ~25 lines using helper methods
- **Reduction:** 75% less boilerplate code
- **Benefit:** Easier to maintain, more consistent styling

