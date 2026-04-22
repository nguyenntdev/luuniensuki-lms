import 'package:equatable/equatable.dart';

/// Friend status enum
enum FriendStatus {
  pending,
  accepted,
  rejected,
  blocked;

  String get displayName {
    switch (this) {
      case FriendStatus.pending:
        return 'Đang chờ';
      case FriendStatus.accepted:
        return 'Đã kết bạn';
      case FriendStatus.rejected:
        return 'Từ chối';
      case FriendStatus.blocked:
        return 'Đã chặn';
    }
  }
}

/// Friend entity representing a user's friend
class Friend extends Equatable {
  final String id;
  final String userId;
  final String displayName;
  final String? avatarUrl;
  final int currentStreak;
  final int xp;
  final int level;
  final FriendStatus status;
  final DateTime? becameFriendsAt;

  const Friend({
    required this.id,
    required this.userId,
    required this.displayName,
    this.avatarUrl,
    this.currentStreak = 0,
    this.xp = 0,
    this.level = 1,
    this.status = FriendStatus.pending,
    this.becameFriendsAt,
  });

  /// Create from JSON
  factory Friend.fromJson(Map<String, dynamic> json) {
    return Friend(
      id: json['id'] as String,
      userId: json['userId'] as String,
      displayName: json['displayName'] as String,
      avatarUrl: json['avatarUrl'] as String?,
      currentStreak: json['currentStreak'] as int? ?? 0,
      xp: json['xp'] as int? ?? 0,
      level: json['level'] as int? ?? 1,
      status: FriendStatus.values.firstWhere(
        (s) => s.toString().split('.').last == json['status'],
        orElse: () => FriendStatus.pending,
      ),
      becameFriendsAt: json['becameFriendsAt'] != null
          ? DateTime.parse(json['becameFriendsAt'] as String)
          : null,
    );
  }

  /// Convert to JSON
  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'userId': userId,
      'displayName': displayName,
      'avatarUrl': avatarUrl,
      'currentStreak': currentStreak,
      'xp': xp,
      'level': level,
      'status': status.toString().split('.').last,
      'becameFriendsAt': becameFriendsAt?.toIso8601String(),
    };
  }

  /// Copy with updated fields
  Friend copyWith({
    String? id,
    String? userId,
    String? displayName,
    String? avatarUrl,
    int? currentStreak,
    int? xp,
    int? level,
    FriendStatus? status,
    DateTime? becameFriendsAt,
  }) {
    return Friend(
      id: id ?? this.id,
      userId: userId ?? this.userId,
      displayName: displayName ?? this.displayName,
      avatarUrl: avatarUrl ?? this.avatarUrl,
      currentStreak: currentStreak ?? this.currentStreak,
      xp: xp ?? this.xp,
      level: level ?? this.level,
      status: status ?? this.status,
      becameFriendsAt: becameFriendsAt ?? this.becameFriendsAt,
    );
  }

  @override
  List<Object?> get props => [
        id,
        userId,
        displayName,
        avatarUrl,
        currentStreak,
        xp,
        level,
        status,
        becameFriendsAt,
      ];

  @override
  String toString() {
    return 'Friend(id: $id, displayName: $displayName, xp: $xp, level: $level, status: $status)';
  }
}

