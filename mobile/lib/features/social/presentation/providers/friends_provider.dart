import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:riverpod_annotation/riverpod_annotation.dart';

import '../../../../core/storage/hive_storage.dart';
import '../../../auth/presentation/providers/auth_provider.dart';
import '../../domain/entities/friend.dart';
import '../../domain/entities/friend_request.dart';

part 'friends_provider.g.dart';

/// Friends state holding friends and requests
class FriendsState {
  final List<Friend> friends;
  final List<FriendRequest> incomingRequests;
  final List<FriendRequest> outgoingRequests;
  final bool isLoading;
  final String? error;

  const FriendsState({
    this.friends = const [],
    this.incomingRequests = const [],
    this.outgoingRequests = const [],
    this.isLoading = false,
    this.error,
  });

  FriendsState copyWith({
    List<Friend>? friends,
    List<FriendRequest>? incomingRequests,
    List<FriendRequest>? outgoingRequests,
    bool? isLoading,
    String? error,
  }) {
    return FriendsState(
      friends: friends ?? this.friends,
      incomingRequests: incomingRequests ?? this.incomingRequests,
      outgoingRequests: outgoingRequests ?? this.outgoingRequests,
      isLoading: isLoading ?? this.isLoading,
      error: error,
    );
  }

  /// Get accepted friends sorted by XP
  List<Friend> get acceptedFriends {
    return friends
        .where((f) => f.status == FriendStatus.accepted)
        .toList()
      ..sort((a, b) => b.xp.compareTo(a.xp));
  }

  /// Get pending friend requests count
  int get pendingRequestsCount => incomingRequests.length;
}

/// Friends provider managing friend relationships
@Riverpod(keepAlive: true)
class FriendsNotifier extends _$FriendsNotifier {
  static const String _friendsKey = 'friends';
  static const String _incomingRequestsKey = 'incoming_friend_requests';
  static const String _outgoingRequestsKey = 'outgoing_friend_requests';

  HiveStorage get _storage => ref.read(hiveStorageProvider);

  @override
  FriendsState build() {
    _loadFromStorage();
    return const FriendsState();
  }

  /// Load friends data from storage
  void _loadFromStorage() {
    try {
      final friendsData = _storage.getSetting<List>(_friendsKey, defaultValue: []);
      final incomingData = _storage.getSetting<List>(_incomingRequestsKey, defaultValue: []);
      final outgoingData = _storage.getSetting<List>(_outgoingRequestsKey, defaultValue: []);

      final friends = friendsData!
          .map((json) => Friend.fromJson(Map<String, dynamic>.from(json)))
          .toList();

      final incomingRequests = incomingData!
          .map((json) => FriendRequest.fromJson(Map<String, dynamic>.from(json)))
          .toList();

      final outgoingRequests = outgoingData!
          .map((json) => FriendRequest.fromJson(Map<String, dynamic>.from(json)))
          .toList();

      state = FriendsState(
        friends: friends,
        incomingRequests: incomingRequests,
        outgoingRequests: outgoingRequests,
      );
    } catch (e) {
      // If there's an error, keep initial state
      state = const FriendsState();
    }
  }

  /// Save to storage
  Future<void> _saveToStorage() async {
    await _storage.setSetting(
      _friendsKey,
      state.friends.map((f) => f.toJson()).toList(),
    );
    await _storage.setSetting(
      _incomingRequestsKey,
      state.incomingRequests.map((r) => r.toJson()).toList(),
    );
    await _storage.setSetting(
      _outgoingRequestsKey,
      state.outgoingRequests.map((r) => r.toJson()).toList(),
    );
  }

  /// Send a friend request
  Future<void> sendFriendRequest(String userId, String userName, String? avatarUrl) async {
    try {
      state = state.copyWith(isLoading: true);

      final currentUser = ref.read(authNotifierProvider).user;
      if (currentUser == null) {
        throw Exception('Bạn cần đăng nhập để gửi lời mời kết bạn');
      }

      // Create new friend request
      final request = FriendRequest(
        id: DateTime.now().millisecondsSinceEpoch.toString(),
        fromUserId: currentUser.id,
        fromUserName: currentUser.displayName,
        fromUserAvatar: currentUser.avatarUrl,
        toUserId: userId,
        toUserName: userName,
        toUserAvatar: avatarUrl,
        createdAt: DateTime.now(),
      );

      final updatedOutgoing = [...state.outgoingRequests, request];
      state = state.copyWith(
        outgoingRequests: updatedOutgoing,
        isLoading: false,
      );

      await _saveToStorage();
    } catch (e) {
      state = state.copyWith(
        isLoading: false,
        error: e.toString(),
      );
      rethrow;
    }
  }

  /// Accept a friend request
  Future<void> acceptFriendRequest(FriendRequest request) async {
    try {
      state = state.copyWith(isLoading: true);

      final currentUser = ref.read(authNotifierProvider).user;
      if (currentUser == null) {
        throw Exception('Bạn cần đăng nhập');
      }

      // Create new friend from the request
      final friend = Friend(
        id: request.id,
        userId: request.fromUserId,
        displayName: request.fromUserName,
        avatarUrl: request.fromUserAvatar,
        status: FriendStatus.accepted,
        becameFriendsAt: DateTime.now(),
      );

      // Update lists
      final updatedFriends = [...state.friends, friend];
      final updatedIncoming = state.incomingRequests
          .where((r) => r.id != request.id)
          .toList();

      state = state.copyWith(
        friends: updatedFriends,
        incomingRequests: updatedIncoming,
        isLoading: false,
      );

      await _saveToStorage();
    } catch (e) {
      state = state.copyWith(
        isLoading: false,
        error: e.toString(),
      );
      rethrow;
    }
  }

  /// Reject a friend request
  Future<void> rejectFriendRequest(FriendRequest request) async {
    try {
      state = state.copyWith(isLoading: true);

      final updatedIncoming = state.incomingRequests
          .where((r) => r.id != request.id)
          .toList();

      state = state.copyWith(
        incomingRequests: updatedIncoming,
        isLoading: false,
      );

      await _saveToStorage();
    } catch (e) {
      state = state.copyWith(
        isLoading: false,
        error: e.toString(),
      );
      rethrow;
    }
  }

  /// Remove a friend
  Future<void> removeFriend(Friend friend) async {
    try {
      state = state.copyWith(isLoading: true);

      final updatedFriends = state.friends
          .where((f) => f.id != friend.id)
          .toList();

      state = state.copyWith(
        friends: updatedFriends,
        isLoading: false,
      );

      await _saveToStorage();
    } catch (e) {
      state = state.copyWith(
        isLoading: false,
        error: e.toString(),
      );
      rethrow;
    }
  }

  /// Add mock friends for demo (will be replaced with real API calls)
  Future<void> addMockFriends() async {
    final mockFriends = [
      Friend(
        id: '1',
        userId: 'user1',
        displayName: 'Nguyễn Văn A',
        xp: 1250,
        level: 5,
        currentStreak: 7,
        status: FriendStatus.accepted,
        becameFriendsAt: DateTime.now().subtract(const Duration(days: 30)),
      ),
      Friend(
        id: '2',
        userId: 'user2',
        displayName: 'Trần Thị B',
        xp: 980,
        level: 4,
        currentStreak: 3,
        status: FriendStatus.accepted,
        becameFriendsAt: DateTime.now().subtract(const Duration(days: 15)),
      ),
      Friend(
        id: '3',
        userId: 'user3',
        displayName: 'Lê Văn C',
        xp: 1500,
        level: 6,
        currentStreak: 12,
        status: FriendStatus.accepted,
        becameFriendsAt: DateTime.now().subtract(const Duration(days: 45)),
      ),
    ];

    final mockIncomingRequests = [
      FriendRequest(
        id: 'req1',
        fromUserId: 'user4',
        fromUserName: 'Phạm Thị D',
        toUserId: 'current_user',
        toUserName: 'Bạn',
        createdAt: DateTime.now().subtract(const Duration(hours: 2)),
      ),
    ];

    state = state.copyWith(
      friends: mockFriends,
      incomingRequests: mockIncomingRequests,
    );

    await _saveToStorage();
  }
}

