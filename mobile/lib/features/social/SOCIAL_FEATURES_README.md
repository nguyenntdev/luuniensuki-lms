# 👥 Social Features - Friend System

## 📋 Overview

Duolingo-style friend system implementation for the LMS app, enabling users to connect with friends, compare progress, and compete on leaderboards.

## 🏗️ Architecture

### Directory Structure
```
mobile/lib/features/social/
├── domain/
│   └── entities/
│       ├── friend.dart              # Friend entity with stats
│       └── friend_request.dart      # Friend request entity
├── presentation/
│   ├── providers/
│   │   ├── friends_provider.dart    # Friends state management
│   │   └── friends_provider.g.dart  # Generated provider code
│   ├── screens/
│   │   └── friends_screen.dart      # Main friends screen with tabs
│   └── widgets/
│       ├── friend_card.dart         # Friend profile card widget
│       └── friend_request_card.dart # Friend request card widget
```

## 🎯 Features Implemented

### 1. Friend Entity
**File:** `mobile/lib/features/social/domain/entities/friend.dart`

```dart
class Friend {
  final String id;
  final String userId;
  final String displayName;
  final String? avatarUrl;
  final int currentStreak;
  final int xp;
  final int level;
  final FriendStatus status;
  final DateTime? becameFriendsAt;
}
```

**Features:**
- ✅ Friend profile information
- ✅ XP and level tracking
- ✅ Streak tracking
- ✅ Status management (pending, accepted, rejected, blocked)
- ✅ JSON serialization
- ✅ Equatable for comparison

### 2. Friend Request Entity
**File:** `mobile/lib/features/social/domain/entities/friend_request.dart`

```dart
class FriendRequest {
  final String id;
  final String fromUserId;
  final String fromUserName;
  final String toUserId;
  final String toUserName;
  final DateTime createdAt;
  final String status;
}
```

### 3. Friends Provider
**File:** `mobile/lib/features/social/presentation/providers/friends_provider.dart`

**State Management:**
```dart
class FriendsState {
  final List<Friend> friends;
  final List<FriendRequest> incomingRequests;
  final List<FriendRequest> outgoingRequests;
  final bool isLoading;
  final String? error;
}
```

**Methods:**
- ✅ `sendFriendRequest()` - Send friend request to user
- ✅ `acceptFriendRequest()` - Accept incoming request
- ✅ `rejectFriendRequest()` - Reject incoming request
- ✅ `removeFriend()` - Remove friend from list
- ✅ `addMockFriends()` - Add demo data for testing

**Storage:**
- Uses HiveStorage for local persistence
- Keys: `'friends'`, `'incoming_friend_requests'`, `'outgoing_friend_requests'`

### 4. Friends Screen
**File:** `mobile/lib/features/social/presentation/screens/friends_screen.dart`

**Features:**
- ✅ Tabbed interface (Friends List / Friend Requests)
- ✅ Friend count badges
- ✅ Add friend button
- ✅ Mock data refresh button (for demo)
- ✅ Empty state messages
- ✅ Glass morphism design
- ✅ Animated background

**UI Components:**
- Friends list sorted by XP
- Pending requests with count badge
- Search/add friend dialog
- Confirmation dialogs
- Success/error messages

### 5. Friend Card Widget
**File:** `mobile/lib/features/social/presentation/widgets/friend_card.dart`

**Features:**
- ✅ Avatar display (with fallback to initials)
- ✅ User stats (XP, Streak, Level)
- ✅ XP comparison with current user
- ✅ Remove friend action
- ✅ Glass container styling

**Stats Display:**
```dart
- 🌟 XP: Shows total experience points
- 🔥 Streak: Shows current learning streak
- 🛡️ Level: Shows user level
- ⬆️⬇️ Comparison: Shows XP difference with you
```

### 6. Friend Request Card Widget
**File:** `mobile/lib/features/social/presentation/widgets/friend_request_card.dart`

**Features:**
- ✅ Request sender information
- ✅ Time ago display
- ✅ Accept/Reject buttons
- ✅ Color-coded actions (green/red)

## 🔌 Integration

### 1. Route Registration
**File:** `mobile/lib/routing/app_router.dart`

```dart
// Added import
import '../features/social/presentation/screens/friends_screen.dart';

// Added route path
static const String friends = '/friends';

// Added route
GoRoute(
  path: _Paths.friends,
  name: 'friends',
  builder: (context, state) => const FriendsScreen(),
),
```

### 2. Profile Menu Integration
**File:** `mobile/lib/features/profile/presentation/screens/profile_screen.dart`

Added menu item:
```dart
_buildMenuCard(
  icon: Icons.people_outline,
  title: 'Bạn bè',
  subtitle: 'Kết nối và thi đua với bạn bè',
  color: AppColors.primary,
  onTap: () => context.push('/friends'),
),
```

## 📱 Usage

### Navigation
```dart
// Navigate to friends screen
context.push('/friends');

// Or using named route
context.pushNamed('friends');
```

### Add Mock Data (for testing)
```dart
ref.read(friendsNotifierProvider.notifier).addMockFriends();
```

### Watch Friends State
```dart
final friendsState = ref.watch(friendsNotifierProvider);
final acceptedFriends = friendsState.acceptedFriends;
final pendingCount = friendsState.pendingRequestsCount;
```

### Send Friend Request
```dart
await ref.read(friendsNotifierProvider.notifier).sendFriendRequest(
  userId: 'user123',
  userName: 'John Doe',
  avatarUrl: 'https://...',
);
```

## 🎨 UI/UX Design

### Color Scheme
- **Primary**: Friend card backgrounds, accept button
- **Success**: Accept action, ahead in XP
- **Error**: Reject action, remove friend
- **Warning**: Behind in XP
- **XP Gold**: XP stat chip
- **Streak Orange**: Streak stat chip
- **Info**: Level stat chip

### Animations
- ✅ Tab transitions
- ✅ Card entrance animations (via GlassContainer)
- ✅ Background gradient animation
- ✅ Button press feedback

### Empty States
```
Friends Tab:
- Icon: people_outline
- Message: "Chưa có bạn bè"
- Subtitle: "Thêm bạn bè để cùng học tập và thi đua!"

Requests Tab:
- Icon: inbox_outlined
- Message: "Không có lời mời"
- Subtitle: "Lời mời kết bạn sẽ hiển thị ở đây"
```

## 🧪 Testing

### Test Mock Data
The system includes mock friends for testing:

```dart
// Mock Friends (automatically added with refresh button)
1. Nguyễn Văn A - 1250 XP, Level 5, 7-day streak
2. Trần Thị B - 980 XP, Level 4, 3-day streak
3. Lê Văn C - 1500 XP, Level 6, 12-day streak

// Mock Incoming Request
1. Phạm Thị D - Sent 2 hours ago
```

### Manual Testing Steps
1. ✅ Navigate to Profile → Bạn bè
2. ✅ Click refresh icon to add mock data
3. ✅ View friends sorted by XP
4. ✅ Accept/Reject friend requests
5. ✅ Remove friends using options menu
6. ✅ Check XP comparison display
7. ✅ Verify empty states
8. ✅ Test add friend dialog (UI only)

## 🔮 Future Enhancements

### Backend Integration (TODO)
- [ ] Connect to real API endpoints
- [ ] Real-time friend status updates
- [ ] User search functionality
- [ ] Friend recommendations
- [ ] Activity feed

### Features to Add
- [ ] Friend challenges/competitions
- [ ] Private messaging
- [ ] Friend leaderboards
- [ ] Activity sharing
- [ ] Achievements comparison
- [ ] Study groups
- [ ] Friend referral rewards

### API Endpoints Needed
```dart
// Friends API (to be implemented)
GET    /api/friends              // List friends
POST   /api/friends/request      // Send friend request
POST   /api/friends/accept/:id   // Accept request
POST   /api/friends/reject/:id   // Reject request
DELETE /api/friends/:id          // Remove friend
GET    /api/friends/search?q=    // Search users
GET    /api/friends/requests     // Get pending requests
GET    /api/friends/suggestions  // Friend suggestions
```

## 🐛 Known Limitations

1. **Mock Data Only**: Currently uses local storage only
2. **No User Search**: Add friend dialog is UI placeholder
3. **No Real-time Updates**: Friend status changes aren't synced
4. **No Notifications**: No push notifications for friend requests
5. **Limited Profile**: Friend profiles don't show detailed stats

## 📝 Code Generation

After making changes to providers, run:

```bash
cd mobile
flutter pub run build_runner build --delete-conflicting-outputs

# Or use the provided script
./run_build_runner.sh
```

## 🎯 Duolingo-Inspired Features

This implementation mirrors Duolingo's friend system:

✅ **Implemented:**
- Friend connections
- XP comparison
- Streak tracking
- Friend requests
- Leaderboard-style sorting

⏳ **Coming Soon:**
- Weekly XP competitions
- Friend challenges
- Activity notifications
- Follow/Following system
- Public profiles

## 💾 Data Persistence

### HiveStorage Keys
```dart
'friends'                    // List<Friend>
'incoming_friend_requests'   // List<FriendRequest>
'outgoing_friend_requests'   // List<FriendRequest>
```

### Storage Format
```json
{
  "friends": [
    {
      "id": "1",
      "userId": "user1",
      "displayName": "Nguyễn Văn A",
      "xp": 1250,
      "level": 5,
      "currentStreak": 7,
      "status": "accepted",
      "becameFriendsAt": "2024-01-01T00:00:00.000Z"
    }
  ],
  "incoming_friend_requests": [],
  "outgoing_friend_requests": []
}
```

## 🚀 Quick Start

### 1. Import the provider
```dart
import 'package:your_app/features/social/presentation/providers/friends_provider.dart';
```

### 2. Watch the state
```dart
final friendsState = ref.watch(friendsNotifierProvider);
```

### 3. Perform actions
```dart
// Add mock data
ref.read(friendsNotifierProvider.notifier).addMockFriends();

// Accept request
await ref.read(friendsNotifierProvider.notifier).acceptFriendRequest(request);

// Remove friend
await ref.read(friendsNotifierProvider.notifier).removeFriend(friend);
```

## 📚 Related Features

- **Profile Screen**: Displays friend count and stats
- **Achievements**: Can compare badges with friends
- **Leaderboard**: Shows friend rankings
- **Daily Goals**: Can see friend daily progress

## ✨ Summary

The friend system is now fully integrated with:
- ✅ 2 domain entities (Friend, FriendRequest)
- ✅ 1 state provider with full CRUD operations
- ✅ 1 main screen with tabs
- ✅ 2 reusable widget components
- ✅ Profile menu integration
- ✅ App router configuration
- ✅ Mock data for testing
- ✅ Glass morphism design
- ✅ Vietnamese localization

Ready for backend integration! 🚀

