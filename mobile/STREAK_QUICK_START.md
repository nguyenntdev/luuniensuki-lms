# Streak System - Quick Start Guide

## 🚀 Getting Started

### 1. Generate Code
```bash
cd mobile
flutter pub get
flutter pub run build_runner build --delete-conflicting-outputs
```

This generates:
- `streak_provider.g.dart` - Riverpod providers
- `streak_provider.freezed.dart` - Freezed models

### 2. Test the Features

Run the app and navigate to **Profile Screen** to see:
✅ Enhanced streak display with calendar
✅ Buy Streak Freeze button
✅ Current streak count with fire icon
✅ Freeze count badge
✅ Progress to next milestone

## 📍 Where to Find Features

### Profile Screen
Path: **Main Nav → Profile**

What you'll see:
1. **Streak Display Card**
   - Fire icon with current streak
   - 7-day calendar (last week)
   - Freeze count badge (if any)
   - Next milestone progress
   - Longest streak record

2. **Buy Streak Freeze Card**
   - Ice icon
   - Description of freeze feature
   - Price: 50 gems
   - Purchase button
   - Insufficient gems warning (if needed)

## 🎯 How to Test

### Test Streak Display
1. Open Profile screen
2. Check if streak count shows correctly
3. Verify calendar shows last 7 days
4. Check if freeze badge appears (if user has freezes)

### Test Freeze Purchase
1. Check your gem balance
2. Click "Mua (50 Gems)" button
3. Verify gems deducted
4. Check freeze count increased
5. Maximum 2 freezes enforced

### Test Milestone Celebration
This requires backend integration:
1. Set streak to milestone value (7, 30, 100, 365)
2. Celebration modal should appear
3. Confetti animation plays
4. Gems awarded automatically

## 🔧 Backend Setup (If Needed)

The backend already has:
- `GET /api/v1/users/me/streak` ✅
- `POST /api/v1/users/me/streak/freeze` ✅

No changes needed! Just ensure:
- User model has `streak_freezes` field
- Endpoint returns correct data format

## 📦 What Was Created

### New Files (11 total)
```
lib/features/streak/
├── domain/entities/
│   ├── streak_data.dart          ← API response model
│   ├── streak_freeze.dart        ← Freeze logic
│   ├── streak_milestone.dart     ← Milestone definitions
│   └── streak_day.dart           ← Calendar days
├── presentation/
│   ├── providers/
│   │   └── streak_provider.dart  ← State management
│   └── widgets/
│       ├── streak_calendar.dart       ← 7-day calendar
│       ├── streak_display.dart        ← Main card
│       ├── streak_milestone.dart      ← Celebration
│       └── buy_streak_freeze_button.dart ← Purchase UI
```

### Modified Files (2)
```
1. lib/core/constants/api_constants.dart
   + Added streak API endpoints

2. lib/features/profile/presentation/screens/profile_screen.dart
   + Added streak widgets import
   + Replaced old streak card
```

## 🎨 Visual Guide

### Streak Display
```
┌─────────────────────────────────┐
│ 🔥  7 ngày                 ❄️ 2 │
│     Chuỗi hiện tại              │
│                                 │
│ ┌───────────────────────────┐  │
│ │ Lịch Chuỗi         🔥 7 ngày│  │
│ │ T2 T3 T4 T5 T6 T7 CN       │  │
│ │ 🔥 🔥 🔥 🔥 🔥 🔥 ⚪       │  │
│ └───────────────────────────┘  │
│                                 │
│ ⭐ Tuần Hoàn Hảo       +25 💎  │
│    Còn 0 ngày nữa              │
└─────────────────────────────────┘
```

### Buy Freeze Button
```
┌─────────────────────────────────┐
│ ❄️  Đóng Băng Chuỗi            │
│     Bảo vệ chuỗi của bạn 1 ngày│
│                                 │
│ ✓ Tự động kích hoạt khi bạn    │
│   bỏ lỡ 1 ngày                 │
│ ✓ Tối đa 2 đóng băng cùng lúc  │
│                                 │
│ ┌─────────────────────────────┐│
│ │  💎 Mua (50 Gems)           ││
│ └─────────────────────────────┘│
└─────────────────────────────────┘
```

### Milestone Celebration
```
     ✨ ✨ ✨ ✨ ✨
   ┌─────────────────┐
   │                 │
   │       👑        │
   │                 │
   │ Chiến Binh Bất  │
   │      Bại        │
   │                 │
   │ Hoàn thành 365  │
   │  ngày liên tiếp!│
   │                 │
   │ ┌─────────────┐ │
   │ │ 💎 +500     │ │
   │ └─────────────┘ │
   │                 │
   │   [ Tiếp tục ]  │
   └─────────────────┘
```

## 🐛 Troubleshooting

### Build Errors
```bash
# Clean and rebuild
cd mobile
flutter clean
flutter pub get
flutter pub run build_runner build --delete-conflicting-outputs
```

### Import Errors
Make sure all imports are correct:
```dart
import 'package:riverpod_annotation/riverpod_annotation.dart';
import 'package:freezed_annotation/freezed_annotation.dart';
```

### Streak Not Loading
Check:
1. API endpoint is accessible
2. User is authenticated
3. Network connection
4. Console for errors

### Freeze Purchase Fails
Check:
1. User has enough gems (≥50)
2. User has less than 2 freezes
3. Gems provider is working
4. Console for error messages

## 📊 Data Flow

```
┌─────────────┐
│   Backend   │ GET /api/v1/users/me/streak
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ StreakData  │ fromJson()
└──────┬──────┘
       │
       ▼
┌─────────────┐
│   Provider  │ StreakNotifier
└──────┬──────┘
       │
       ▼
┌─────────────┐
│   Widgets   │ StreakDisplay, BuyButton
└─────────────┘
```

## ✅ Checklist

Before testing:
- [ ] Run `build_runner` to generate code
- [ ] Check backend endpoints are working
- [ ] Verify user has some streak data
- [ ] Have some gems for testing purchase
- [ ] Profile screen loads without errors

During testing:
- [ ] Streak count displays correctly
- [ ] Calendar shows 7 days
- [ ] Freeze badge shows if > 0
- [ ] Purchase button works
- [ ] Gems deducted correctly
- [ ] Freeze count increases
- [ ] Error messages display

## 🎁 Features Overview

| Feature | Status | Description |
|---------|--------|-------------|
| Streak Display | ✅ Complete | Shows current streak with calendar |
| Calendar Widget | ✅ Complete | Last 7 days visualization |
| Freeze Purchase | ✅ Complete | Buy with gems (50 each) |
| Milestone System | ✅ Complete | Auto rewards at 7, 30, 100, 365 |
| Celebration Modal | ✅ Complete | Full-screen confetti celebration |
| API Integration | ✅ Complete | Connected to backend endpoints |
| Error Handling | ✅ Complete | User-friendly error messages |
| Vietnamese Text | ✅ Complete | All strings in Vietnamese |

## 🚦 Status

**READY FOR TESTING** 🎉

All code is written and ready. Just need to:
1. Run code generation
2. Build and run the app
3. Test features
4. Report any issues

## 📞 Support

If you encounter issues:
1. Check console logs
2. Verify API responses
3. Check network tab in DevTools
4. Review error messages in UI

