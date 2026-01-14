# Gems System - Quick Start Guide

## 🎯 What is the Gems System?

The Gems system is a virtual currency feature (like Duolingo's Lingots/Gems) that rewards users for their learning activities and allows them to purchase helpful power-ups in the app.

## 💎 How to Earn Gems

| Activity | Gems Earned | When |
|----------|-------------|------|
| Complete any lesson | +10 gems | After lesson completion |
| Complete daily goal | +20 gems | When reaching daily XP target |
| Perfect quiz score | +5 gems | When scoring 100% on a quiz |
| 7-day streak milestone | +50 gems | Every 7 days of streak (7, 14, 21...) |

## 🛍️ Gems Shop Items

| Item | Cost | Description |
|------|------|-------------|
| 🛡️ Streak Freeze | 50 gems | Protects your streak for 1 day |
| ⚡ Double XP | 100 gems | Earn 2x XP for 30 minutes |
| 💡 Hint | 25 gems | Get a hint for an answer |

## 📱 Where to Find Gems

### 1. Profile Screen
- Gems display appears in your profile header (below your rank)
- Tap to open the Gems Shop
- Shows current balance with animated gem icon

### 2. Settings Menu
- Look for "Cửa Hàng Gems" (Gems Shop) card
- Diamond icon with yellow color
- Located in the profile settings section

## 🔧 For Developers

### Quick Integration

#### Award Gems
```dart
import '../gems/presentation/providers/gems_provider.dart';
import '../gems/domain/entities/gem_transaction.dart';

// In your completion handler
await ref.read(gemsNotifierProvider.notifier).addGems(
  amount: 10,
  type: GemTransactionType.earnedLesson,
  description: 'Hoàn thành bài học',
);
```

#### Check Balance
```dart
final gemsState = ref.watch(gemsNotifierProvider);
final currentBalance = gemsState.balance;
final canAfford = gemsState.balance >= 50;
```

#### Display Gems
```dart
import '../gems/presentation/widgets/gems_display.dart';

// Full display with label
GemsDisplay(
  showLabel: true,
  onTap: () => context.push('/gems-shop'),
)

// Compact display
CompactGemsDisplay(
  onTap: () => context.push('/gems-shop'),
)
```

### File Structure
```
mobile/lib/features/gems/
├── domain/
│   └── entities/
│       └── gem_transaction.dart      # Transaction entity
├── presentation/
    ├── providers/
    │   ├── gems_provider.dart        # State management
    │   └── gems_provider.g.dart      # Generated code
    ├── screens/
    │   └── gems_shop_screen.dart     # Shop UI
    └── widgets/
        └── gems_display.dart         # Display widgets
```

### Integration Points

**Lesson Completion** (`lesson_tab.dart`)
- Awards +10 gems on lesson complete
- Checks for 7-day streak milestone

**Quiz Results** (`quiz_result_screen.dart`)
- Awards +5 gems for 100% score

**Daily Goals** (`daily_goal_provider.dart`)
- Awards +20 gems when goal is completed

## 🎨 UI Components

### GemsDisplay Widget
Full display with animation
- Scale animation on balance change
- Customizable icon size and text style
- Optional label "Gems"

### CompactGemsDisplay Widget
Compact version for app bars
- Glass morphism container
- Gem icon + count
- Tap to navigate to shop

### GemsShopScreen
Full shop experience
- List of purchasable items
- Transaction history modal
- How to earn gems info section
- Glass card design

## 📊 Tracking

All gem transactions are logged with:
- Unique ID
- Amount (positive or negative)
- Transaction type
- Description
- Timestamp

View transaction history in:
- Gems Shop → "Transaction History" button
- Shows all earning and spending activities

## 🔄 Persistence

- Stored locally using HiveStorage
- Keys: `gems_balance`, `gems_transactions`
- Persists across app restarts
- Automatic midnight reset for daily goals
- Initial balance: 100 gems for new users

## 🚀 Testing

See `GEMS_TESTING_CHECKLIST.md` for complete testing guide

Quick smoke test:
1. Launch app → Check initial 100 gems
2. Complete a lesson → Verify +10 gems
3. Open gems shop → Check UI
4. Purchase item → Verify deduction

## 📚 Documentation

- `GEMS_IMPLEMENTATION_SUMMARY.md` - Full implementation details
- `GEMS_ARCHITECTURE.md` - System architecture diagrams
- `GEMS_TESTING_CHECKLIST.md` - Complete testing guide

## 🎯 Future Enhancements

- [ ] Backend API integration
- [ ] Premium shop items
- [ ] In-app purchases
- [ ] Gem gifting
- [ ] Limited-time offers
- [ ] Achievement-based rewards

