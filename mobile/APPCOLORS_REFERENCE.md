# AppColors Quick Reference Guide

## 🎨 Primary Colors

### Gold Palette (Main Brand)
```dart
AppColors.primary           // #E8B44C - Warmer, luminous gold
AppColors.primaryDark       // #D49B38 - Rich deep gold
AppColors.primaryLight      // #F5D078 - Champagne gold
AppColors.primarySurface    // #2A2520 - Gold surface background
```

**Use Cases:**
- Primary actions & buttons
- Progress indicators
- Highlights & emphasis
- Brand elements

---

## 🌑 Background Colors

```dart
AppColors.background        // #0A0E14 - Deep midnight (main bg)
AppColors.surface           // #141921 - Elevated dark (cards)
AppColors.surfaceElevated   // #1C232D - Card surface (raised)
AppColors.surfaceVariant    // #1C2128 - Alternating backgrounds
```

**Use Cases:**
- Main screen backgrounds
- Card containers
- Elevated surfaces
- Modal backgrounds

---

## 📝 Text Colors

```dart
AppColors.textPrimary       // #F5F5F5 - Near white (main text)
AppColors.textSecondary     // #B8BCC5 - Clearer secondary
AppColors.textHint          // #6B7280 - Muted hints
AppColors.textDisabled      // #6E6A64 - Disabled state
AppColors.onPrimary         // #1A1A1A - Text on gold
AppColors.onSurface         // #F5F5F5 - Text on surface
AppColors.mutedForeground   // #BFB8A8 - Muted text
```

**Use Cases:**
- Headings: `textPrimary`
- Body text: `textPrimary`
- Labels: `textSecondary`
- Placeholders: `textHint`
- Text on buttons: `onPrimary`

---

## ✅ Semantic Colors

### Success (Green)
```dart
AppColors.success           // #34D399 - Soft teal-green
AppColors.successSurface    // #1A3D1C - Success background
```
**Use:** Completed items, learned status

### Error (Red)
```dart
AppColors.error             // #EF6B6B - Warm coral
AppColors.errorSurface      // #3D1A1A - Error background
AppColors.errorLight        // #FFEBEE - Light error bg
```
**Use:** Error messages, validation

### Warning (Amber)
```dart
AppColors.warning           // #F59E0B - Amber
AppColors.warningSurface    // #3D3018 - Warning background
```
**Use:** Warnings, cautions

### Info (Blue)
```dart
AppColors.info              // #60A5FA - Soft blue
AppColors.infoSurface       // #1A2D3D - Info background
```
**Use:** Discovery status, info messages

---

## 🎮 Gamification Colors

```dart
AppColors.xpGold            // #FFD700 - Bright XP gold
AppColors.xpGoldDark        // #D4A200 - Dark XP gold
AppColors.streakOrange      // #FF6B35 - Streak fire
AppColors.badgePurple       // #9C27B0 - Badge purple
AppColors.questBlue         // #3F51B5 - Quest blue
AppColors.levelUpGreen      // #00C853 - Level up
```

---

## 🏛️ Imperial Colors

```dart
AppColors.secondary         // #C41E3A - Imperial red
AppColors.secondaryLight    // #E8415A - Light imperial
AppColors.accent            // #C41E3A - Accent red
AppColors.accentLight       // #E8415A - Light accent
```

---

## 📊 Status Colors

```dart
AppColors.statusHidden      // #6E6A64 - Undiscovered
AppColors.statusDiscovered  // #4CAF50 - Discovered (green)
AppColors.statusLearned     // #2196F3 - Learned (blue)
AppColors.statusMastered    // #9C27B0 - Mastered (purple)
```

**Helper Method:**
```dart
Color color = AppColors.forStatus('discovered');
```

---

## ✨ Glass Effects

```dart
AppColors.glassWhite        // #1AFFFFFF - 10% white
AppColors.glassBorder       // #33FFFFFF - 20% white
```

**Use:** Glassmorphism effects

---

## 🎨 Gradients

```dart
AppColors.primaryGradient   // Gold gradient
AppColors.backgroundGradient // Background gradient
AppColors.xpGradient        // XP gradient
AppColors.cardGradient      // Card gradient overlay
```

**Example:**
```dart
Container(
  decoration: BoxDecoration(
    gradient: AppColors.primaryGradient,
  ),
)
```

---

## 💫 Shadows

```dart
AppColors.goldGlow          // Gold glow shadow
AppColors.elegantShadow     // Elegant deep shadow
AppColors.cardShadow        // Standard card shadow
```

**Example:**
```dart
Container(
  decoration: BoxDecoration(
    boxShadow: AppColors.goldGlow,
  ),
)
```

---

## 🔧 Common Usage Patterns

### Button Styles
```dart
// Primary button
ElevatedButton(
  style: ElevatedButton.styleFrom(
    backgroundColor: AppColors.primary,
    foregroundColor: AppColors.onPrimary,
  ),
)

// Secondary button
OutlinedButton(
  style: OutlinedButton.styleFrom(
    foregroundColor: AppColors.primary,
    side: BorderSide(color: AppColors.primary),
  ),
)
```

### Card Containers
```dart
Container(
  decoration: BoxDecoration(
    color: AppColors.surface,
    borderRadius: BorderRadius.circular(12),
    border: Border.all(color: AppColors.glassBorder),
    boxShadow: AppColors.cardShadow,
  ),
)
```

### Text Styles
```dart
Text(
  'Heading',
  style: TextStyle(
    color: AppColors.textPrimary,
    fontSize: 24,
    fontWeight: FontWeight.bold,
  ),
)

Text(
  'Body text',
  style: TextStyle(
    color: AppColors.textSecondary,
    fontSize: 16,
  ),
)
```

### Progress Indicators
```dart
CircularProgressIndicator(
  valueColor: AlwaysStoppedAnimation(AppColors.primary),
  backgroundColor: AppColors.surface,
)
```

---

## ⚠️ Don't Use
- ❌ Hardcoded hex values: `Color(0xFFE8B44C)`
- ❌ Direct color constructors without constants
- ❌ Colors.amber, Colors.blue (use semantic AppColors)

## ✅ Do Use
- ✅ AppColors constants: `AppColors.primary`
- ✅ Semantic color names
- ✅ Helper methods when available

