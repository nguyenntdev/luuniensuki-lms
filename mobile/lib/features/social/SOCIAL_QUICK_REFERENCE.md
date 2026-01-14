# 👥 Social Features - Quick Reference

## ⚡ Quick Commands

### Navigate to Friends Screen
```dart
context.push('/friends');
```

### Add Mock Data
```dart
ref.read(friendsNotifierProvider.notifier).addMockFriends();
```

### Watch Friends State
```dart
final friendsState = ref.watch(friendsNotifierProvider);
```

## 📁 File Locations

```
Domain Entities:
  mobile/lib/features/social/domain/entities/friend.dart
  mobile/lib/features/social/domain/entities/friend_request.dart

Provider:
  mobile/lib/features/social/presentation/providers/friends_provider.dart
  mobile/lib/features/social/presentation/providers/friends_provider.g.dart

Screen:
  mobile/lib/features/social/presentation/screens/friends_screen.dart

Widgets:
  mobile/lib/features/social/presentation/widgets/friend_card.dart
  mobile/lib/features/social/presentation/widgets/friend_request_card.dart

Docs:
  mobile/lib/features/social/SOCIAL_FEATURES_README.md
  mobile/lib/features/social/SOCIAL_VISUAL_GUIDE.md
  mobile/lib/features/social/SOCIAL_QUICK_REFERENCE.md
```

## 🔧 Common Operations

### Get Friend List
```dart
final friends = ref.watch(friendsNotifierProvider).acceptedFriends;
```

### Get Pending Requests Count
```dart
final count = ref.watch(friendsNotifierProvider).pendingRequestsCount;
```

### Send Friend Request
```dart
await ref.read(friendsNotifierProvider.notifier).sendFriendRequest(
  'userId',
  'Display Name',
  'https://avatar.url',
);
```

### Accept Request
```dart
await ref.read(friendsNotifierProvider.notifier).acceptFriendRequest(request);
```

### Reject Request
```dart
await ref.read(friendsNotifierProvider.notifier).rejectFriendRequest(request);
```

### Remove Friend
```dart
await ref.read(friendsNotifierProvider.notifier).removeFriend(friend);
```

## 🗂️ Storage Keys

```dart
'friends'                    // Friends list
'incoming_friend_requests'   // Incoming requests
'outgoing_friend_requests'   // Outgoing requests
```

## 🎨 UI Constants

### Colors
```dart
Primary:       AppColors.primary
Success:       AppColors.success
Error:         AppColors.error
XP Gold:       AppColors.xpGold
Streak Orange: AppColors.streakOrange
Info Blue:     AppColors.info
```

### Icons
```dart
Friends:       Icons.people_outline
Add Friend:    Icons.person_add
Remove:        Icons.person_remove
Accept:        Icons.check
Reject:        Icons.close
XP:           Icons.stars
Streak:       Icons.local_fire_department
Level:        Icons.shield
```

### Spacing
```dart
Card Padding:  16px
Card Gap:      12px (AppSpacing.verticalSpaceMD)
Horizontal:    16px (AppSpacing.horizontalSpaceMD)
```

## 🧪 Mock Data

### Mock Friends
```dart
Friend(
  id: '1',
  userId: 'user1',
  displayName: 'Nguyễn Văn A',
  xp: 1250,
  level: 5,
  currentStreak: 7,
),
Friend(
  id: '2',
  userId: 'user2',
  displayName: 'Trần Thị B',
  xp: 980,
  level: 4,
  currentStreak: 3,
),
Friend(
  id: '3',
  userId: 'user3',
  displayName: 'Lê Văn C',
  xp: 1500,
  level: 6,
  currentStreak: 12,
),
```

### Mock Request
```dart
FriendRequest(
  id: 'req1',
  fromUserId: 'user4',
  fromUserName: 'Phạm Thị D',
  createdAt: 2 hours ago,
),
```

## 🔄 State Management Flow

```
1. Provider loads data from HiveStorage on init
2. User performs action (accept/reject/remove)
3. Provider updates state
4. Provider saves to HiveStorage
5. UI rebuilds automatically
```

## 📱 Screen Features

### Friends Tab
- Shows accepted friends
- Sorted by XP (highest first)
- XP comparison with current user
- Remove friend option

### Requests Tab
- Shows incoming requests
- Badge with count
- Accept/Reject actions
- Time ago display

### AppBar Actions
- Add friend button (👤)
- Refresh mock data (🔄)

## 🎯 Integration Points

### Profile Screen
```dart
// In _buildSettingsCards()
_buildMenuCard(
  icon: Icons.people_outline,
  title: 'Bạn bè',
  subtitle: 'Kết nối và thi đua với bạn bè',
  color: AppColors.primary,
  onTap: () => context.push('/friends'),
),
```

### App Router
```dart
GoRoute(
  path: '/friends',
  name: 'friends',
  builder: (context, state) => const FriendsScreen(),
),
```

## 🐛 Debugging

### Check Provider State
```dart
print(ref.read(friendsNotifierProvider).friends);
print(ref.read(friendsNotifierProvider).incomingRequests);
```

### Check Storage
```dart
final storage = ref.read(hiveStorageProvider);
print(storage.getSetting('friends'));
```

### Clear Data
```dart
final storage = ref.read(hiveStorageProvider);
await storage.setSetting('friends', []);
await storage.setSetting('incoming_friend_requests', []);
```

## 📝 Vietnamese Translations

```
Bạn Bè              = Friends
Lời Mời             = Requests
Thêm bạn bè         = Add Friend
Chấp nhận           = Accept
Từ chối             = Reject
Hủy kết bạn         = Unfriend
Chưa có bạn bè      = No Friends Yet
Không có lời mời    = No Requests
Gửi lời mời         = Send Request
Hơn bạn X XP        = X XP ahead of you
Kém bạn X XP        = X XP behind you
```

## ✅ Checklist

- [x] Friend entity with stats
- [x] Friend request entity
- [x] Friends provider
- [x] Friends screen with tabs
- [x] Friend card widget
- [x] Friend request card widget
- [x] Profile menu integration
- [x] Router configuration
- [x] Mock data support
- [x] Vietnamese localization
- [ ] Backend API integration
- [ ] Real-time updates
- [ ] User search
- [ ] Push notifications

