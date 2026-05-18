# Profile Menu Navigation Flow - Visual Reference

## 🗺️ Navigation Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Profile Screen                           │
│  (mobile/lib/features/profile/presentation/screens/             │
│   profile_screen.dart)                                          │
│                                                                 │
│  ┌─────────────────────────────────────────────────────┐      │
│  │         "Cài đặt & Tài khoản" Section               │      │
│  │                                                      │      │
│  │  ┌────────────────────────────────────────┐         │      │
│  │  │  📱 Thông tin cá nhân                  │ ────────┼──────┼──┐
│  │  │  Chỉnh sửa hồ sơ và ảnh đại diện      │         │      │  │
│  │  └────────────────────────────────────────┘         │      │  │
│  │                                                      │      │  │
│  │  ┌────────────────────────────────────────┐         │      │  │
│  │  │  🔔 Thông báo                          │ ────────┼──────┼──┼──┐
│  │  │  Quản lý nhắc nhở và thông báo        │         │      │  │  │
│  │  └────────────────────────────────────────┘         │      │  │  │
│  │                                                      │      │  │  │
│  │  ┌────────────────────────────────────────┐         │      │  │  │
│  │  │  ⚙️ Cài đặt                            │ ────────┼──────┼──┼──┼──┐
│  │  │  Tùy chỉnh ứng dụng                   │         │      │  │  │  │
│  │  └────────────────────────────────────────┘         │      │  │  │  │
│  │                                                      │      │  │  │  │
│  │  ┌────────────────────────────────────────┐         │      │  │  │  │
│  │  │  ❓ Trợ giúp & Hỗ trợ                  │ ────────┼──────┼──┼──┼──┼──┐
│  │  │  Câu hỏi thường gặp và liên hệ        │         │      │  │  │  │  │
│  │  └────────────────────────────────────────┘         │      │  │  │  │  │
│  └─────────────────────────────────────────────────────┘      │  │  │  │  │
└─────────────────────────────────────────────────────────────────┘  │  │  │  │
                                                                     │  │  │  │
                                                                     │  │  │  │
┌────────────────────────────────────────────────────────────────────┘  │  │  │
│                    Personal Info Screen                                │  │  │
│  (mobile/lib/features/profile/presentation/screens/                    │  │  │
│   personal_info_screen.dart)                                           │  │  │
│                                                                         │  │  │
│  Navigation: Navigator.push()                                          │  │  │
│  Route: None (direct navigation)                                       │  │  │
│                                                                         │  │  │
│  Features:                                                              │  │  │
│  • Edit display name                                                   │  │  │
│  • Edit username                                                       │  │  │
│  • Profile visibility toggle                                           │  │  │
│  • Avatar upload                                                       │  │  │
└─────────────────────────────────────────────────────────────────────────┘  │  │
                                                                             │  │
┌────────────────────────────────────────────────────────────────────────────┘  │
│                    Notifications Screen                                       │
│  (mobile/lib/features/notifications/presentation/screens/                    │
│   notifications_screen.dart)                                                 │
│                                                                               │
│  Navigation: context.push('/notifications')                                  │
│  Route: /notifications (line 234-238 in app_router.dart)                    │
│                                                                               │
│  Features:                                                                    │
│  • List of notifications                                                     │
│  • Mark as read/unread                                                       │
│  • Filter by type (All, Lessons, Achievements, System)                      │
│  • Delete notifications                                                      │
│  • Pull to refresh                                                           │
└───────────────────────────────────────────────────────────────────────────────┘
                                                                                │
┌───────────────────────────────────────────────────────────────────────────────┘
│                    Settings Screen
│  (mobile/lib/features/settings/presentation/screens/
│   settings_screen.dart)
│
│  Navigation: context.push('/settings')
│  Route: /settings (line 216-220 in app_router.dart)
│
│  Features:
│  • Notification preferences
│  • Language selection (Tiếng Việt, English)
│  • Sound effects toggle
│  • Background music toggle
│  • Cache management
│  • App version info
│  • Legal documents (Privacy, Terms)
└───────────────────────────────────────────────────────────────────────────────┐
                                                                                │
┌───────────────────────────────────────────────────────────────────────────────┘
│                    Help & Support Screen
│  (mobile/lib/features/help/presentation/screens/
│   help_support_screen.dart)
│
│  Navigation: context.push('/help')
│  Route: /help (line 225-229 in app_router.dart)
│
│  Features:
│  • FAQ section (10+ questions)
│  • Contact support button
│  • Email support (support@luuniensuki.com)
│  • Social media links
│  • Expandable FAQ items
└───────────────────────────────────────────────────────────────────────────────┘
```

## 🎨 Color Scheme

```
Personal Info    → Blue   (AppColors.info)      💙
Notifications    → Amber  (AppColors.warning)   🟡
Settings         → Gray   (AppColors.textSecondary) ⚪
Help & Support   → Green  (AppColors.success)   💚
```

## 📂 File Structure

```
mobile/
├── lib/
│   ├── routing/
│   │   └── app_router.dart           ← Router configuration
│   └── features/
│       ├── profile/
│       │   └── presentation/
│       │       └── screens/
│       │           ├── profile_screen.dart        ← Main profile screen
│       │           └── personal_info_screen.dart  ← Personal info editor
│       ├── notifications/
│       │   └── presentation/
│       │       └── screens/
│       │           └── notifications_screen.dart  ← Notifications list
│       ├── settings/
│       │   └── presentation/
│       │       └── screens/
│       │           └── settings_screen.dart       ← App settings
│       └── help/
│           └── presentation/
│               └── screens/
│                   └── help_support_screen.dart   ← FAQ & support
```


