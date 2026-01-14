# Profile Menu Code Reference

## 🔍 Navigation Code Snippets

### 1. Personal Info Navigation

**Location**: `mobile/lib/features/profile/presentation/screens/profile_screen.dart` (lines 873-885)

```dart
_buildMenuCard(
  icon: Icons.person_outline,
  title: 'Thông tin cá nhân',
  subtitle: 'Chỉnh sửa hồ sơ và ảnh đại diện',
  color: AppColors.info,
  onTap: () {
    Navigator.of(context).push(
      MaterialPageRoute(
        builder: (context) => const PersonalInfoScreen(),
      ),
    );
  },
),
```

**Why Navigator.push()?**
- Direct screen-to-screen navigation
- Simpler for modal-like screens
- Doesn't require route registration

---

### 2. Notifications Navigation

**Location**: `mobile/lib/features/profile/presentation/screens/profile_screen.dart` (lines 889-896)

```dart
_buildMenuCard(
  icon: Icons.notifications_outlined,
  title: 'Thông báo',
  subtitle: 'Quản lý nhắc nhở và thông báo',
  color: AppColors.warning,
  onTap: () => context.push('/notifications'),
),
```

**Route Registration**: `mobile/lib/routing/app_router.dart` (lines 234-238)

```dart
GoRoute(
  path: _Paths.notifications,  // '/notifications'
  name: 'notifications',
  builder: (context, state) => const NotificationsScreen(),
),
```

---

### 3. Settings Navigation

**Location**: `mobile/lib/features/profile/presentation/screens/profile_screen.dart` (lines 900-907)

```dart
_buildMenuCard(
  icon: Icons.settings_outlined,
  title: 'Cài đặt',
  subtitle: 'Tùy chỉnh ứng dụng',
  color: AppColors.textSecondary,
  onTap: () => context.push('/settings'),
),
```

**Route Registration**: `mobile/lib/routing/app_router.dart` (lines 216-220)

```dart
GoRoute(
  path: _Paths.settings,  // '/settings'
  name: 'settings',
  builder: (context, state) => const SettingsScreen(),
),
```

---

### 4. Help & Support Navigation

**Location**: `mobile/lib/features/profile/presentation/screens/profile_screen.dart` (lines 911-920)

```dart
_buildMenuCard(
  icon: Icons.help_outline,
  title: 'Trợ giúp & Hỗ trợ',
  subtitle: 'Câu hỏi thường gặp và liên hệ',
  color: AppColors.success,
  onTap: () {
    context.push('/help');
  },
),
```

**Route Registration**: `mobile/lib/routing/app_router.dart` (lines 225-229)

```dart
GoRoute(
  path: _Paths.help,  // '/help'
  name: 'help',
  builder: (context, state) => const HelpSupportScreen(),
),
```

---

## 🎨 Menu Card Widget

**Location**: `mobile/lib/features/profile/presentation/screens/profile_screen.dart` (lines 930-1001)

```dart
Widget _buildMenuCard({
  required IconData icon,
  required String title,
  required String subtitle,
  required Color color,
  required VoidCallback onTap,
}) {
  return GlassCard(
    padding: const EdgeInsets.all(AppSpacing.md),
    onTap: onTap,
    child: Row(
      children: [
        // Icon with gradient background
        Container(
          width: 48,
          height: 48,
          decoration: BoxDecoration(
            gradient: LinearGradient(
              colors: [
                color.withOpacity(0.3),
                color.withOpacity(0.1),
              ],
            ),
            borderRadius: BorderRadius.circular(AppSpacing.radiusMD),
            border: Border.all(
              color: color.withOpacity(0.3),
            ),
          ),
          child: Icon(
            icon,
            color: color,
            size: 24,
          ),
        ),

        AppSpacing.horizontalSpaceMD,

        // Text content
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                title,
                style: const TextStyle(
                  color: Colors.white,
                  fontSize: 16,
                  fontWeight: FontWeight.w600,
                ),
              ),
              AppSpacing.verticalSpaceXS,
              Text(
                subtitle,
                style: TextStyle(
                  color: Colors.white.withOpacity(0.6),
                  fontSize: 12,
                ),
              ),
            ],
          ),
        ),

        // Arrow icon
        Icon(
          Icons.chevron_right,
          color: Colors.white.withOpacity(0.3),
          size: 24,
        ),
      ],
    ),
  );
}
```

---

## 📋 Import Statements

### Profile Screen Imports
```dart
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../../core/theme/app_colors.dart';
import '../../../../core/theme/app_spacing.dart';
import '../../../../shared/widgets/glass/animated_background.dart';
import '../../../../shared/widgets/glass/glass_container.dart';
import '../../../auth/domain/entities/user.dart';
import '../../../auth/presentation/providers/auth_provider.dart';
import 'personal_info_screen.dart';
```

### Router Imports
```dart
import '../features/profile/presentation/screens/profile_screen.dart';
import '../features/settings/presentation/screens/settings_screen.dart';
import '../features/help/presentation/screens/help_support_screen.dart';
import '../features/notifications/presentation/screens/notifications_screen.dart';
```

---

## 🔄 Navigation Flow

```
User taps menu card
      ↓
onTap callback triggered
      ↓
Navigation method called
      ↓
Screen transition begins
      ↓
New screen appears
      ↓
User can tap back button
      ↓
Returns to Profile screen
```

---

## 💡 Key Concepts

1. **GoRouter**: Used for app-wide navigation with route management
2. **Navigator**: Used for simple push navigation
3. **context.push()**: GoRouter method for pushing new routes
4. **GlassCard**: Reusable card component with glassmorphism
5. **AppColors**: Centralized color constants
6. **AppSpacing**: Consistent spacing values


