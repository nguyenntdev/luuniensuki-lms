# Gems System Implementation Summary

## Overview
Implemented a complete Virtual Currency (Gems) system similar to Duolingo's Lingots/Gems for the Lưu Niên Sử Kí LMS mobile app.

## Features Implemented

### 1. Domain Layer

**File: `mobile/lib/features/gems/domain/entities/gem_transaction.dart`**
- `GemTransaction` entity with id, amount, type, description, createdAt
- `GemTransactionType` enum with transaction categories:
  - **Earned**: `earnedLesson`, `earnedStreak`, `earnedPerfect`, `earnedBonus`
  - **Spent**: `spentStreakFreeze`, `spentDoubleXp`, `spentHint`
- Custom ID generator using timestamps (no external dependencies)

### 2. State Management

**File: `mobile/lib/features/gems/presentation/providers/gems_provider.dart`**
- `GemsState` class with balance, transactions, isLoading, error
- `GemsNotifier` (Riverpod with keepAlive: true)
- Local storage using HiveStorage with keys:
  - `gems_balance` - Current gem count
  - `gems_transactions` - Transaction history
- Initial gems: 100 for new users
- Methods:
  - `addGems()` - Award gems with transaction logging
  - `spendGems()` - Deduct gems with validation
  - `getBalance()` - Get current balance
  - `canAfford()` - Check if user can afford an item

### 3. UI Components

**File: `mobile/lib/features/gems/presentation/widgets/gems_display.dart`**

Two display widgets:

1. **GemsDisplay** - Full animated display
   - Scale animation on balance change
   - Optional label
   - Customizable icon size and text style
   - Tap callback support

2. **CompactGemsDisplay** - Compact version for app bars
   - Shows gem icon and count
   - Glass morphism styling
   - Tap to navigate to shop

### 4. Gems Shop Screen

**File: `mobile/lib/features/gems/presentation/screens/gems_shop_screen.dart`**

Shop items available for purchase:
- **Streak Freeze** (50 gems) - Protects streak for 1 day
- **Double XP** (100 gems) - x2 XP for 30 minutes
- **Hint** (25 gems) - Hint for answer

Features:
- Transaction history modal
- "How to Earn Gems" information section
- Purchase validation with balance checking
- Glass morphism card design
- Animated backgrounds

### 5. Earning Gems Integration

Gems are automatically awarded for:

1. **Complete a Lesson: +10 gems**
   - Integrated in `lesson_tab.dart`
   - Awards on lesson completion

2. **Complete Daily Goal: +20 gems**
   - Integrated in `daily_goal_provider.dart`
   - Awards when daily XP goal is reached

3. **7-Day Streak Milestone: +50 gems**
   - Integrated in `lesson_tab.dart`
   - Awards on multiples of 7 days (7, 14, 21, etc.)

4. **Perfect Quiz Score: +5 bonus**
   - Integrated in `quiz_result_screen.dart`
   - Awards when achieving 100% on quiz

### 6. Navigation & Integration

**Route Registration:**
- Path: `/gems-shop`
- Name: `gemsShop`
- Added to `app_router.dart`

**Profile Screen Integration:**
- Gems display added to profile header (after rank badge)
- Shop link added to settings menu
- Tappable to navigate to shop

### 7. Theme Integration

**File: `mobile/lib/core/theme/app_colors.dart`**
- Added `gemYellow = Color(0xFFFFD700)` constant

## Files Created

1. `mobile/lib/features/gems/domain/entities/gem_transaction.dart`
2. `mobile/lib/features/gems/presentation/providers/gems_provider.dart`
3. `mobile/lib/features/gems/presentation/providers/gems_provider.g.dart`
4. `mobile/lib/features/gems/presentation/widgets/gems_display.dart`
5. `mobile/lib/features/gems/presentation/screens/gems_shop_screen.dart`

## Files Modified

1. `mobile/lib/core/theme/app_colors.dart` - Added gemYellow color
2. `mobile/lib/routing/app_router.dart` - Added gems shop route
3. `mobile/lib/features/profile/presentation/screens/profile_screen.dart` - Added gems display and shop link
4. `mobile/lib/features/lesson/presentation/widgets/lesson_tab.dart` - Added gem earning on lesson completion
5. `mobile/lib/features/quiz/presentation/screens/quiz_result_screen.dart` - Added gem earning for perfect scores
6. `mobile/lib/features/daily_goals/presentation/providers/daily_goal_provider.dart` - Added gem earning on goal completion

## Usage Examples

### Award Gems
```dart
await ref.read(gemsNotifierProvider.notifier).addGems(
  amount: 10,
  type: GemTransactionType.earnedLesson,
  description: 'Hoàn thành bài học',
);
```

### Spend Gems
```dart
final success = await ref.read(gemsNotifierProvider.notifier).spendGems(
  amount: 50,
  type: GemTransactionType.spentStreakFreeze,
  description: 'Mua Đóng Băng Chuỗi',
);
```

### Check Balance
```dart
final balance = ref.read(gemsNotifierProvider).balance;
final canBuy = ref.read(gemsNotifierProvider.notifier).canAfford(50);
```

### Display Gems
```dart
// Full display
GemsDisplay(
  showLabel: true,
  onTap: () => context.push('/gems-shop'),
)

// Compact display
CompactGemsDisplay(
  onTap: () => context.push('/gems-shop'),
)
```

## Technical Notes

1. **Local Storage**: All gem data persists locally using HiveStorage
2. **Transaction History**: Every gem addition/deduction is logged with metadata
3. **No Backend Integration**: Currently local-only (ready for backend sync)
4. **Animation**: Gems display animates when balance changes
5. **Vietnamese UI**: All text in Vietnamese language

## Future Enhancements

- Backend API integration for gem persistence
- Premium shop items (extra lives, XP boosts, etc.)
- Gem purchase with real money (IAP)
- Gem gifting between users
- Limited-time offers and discounts
- Achievement-based gem rewards

