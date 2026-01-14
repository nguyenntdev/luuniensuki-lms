import 'package:equatable/equatable.dart';

/// Friend request entity representing a pending friend connection
class FriendRequest extends Equatable {
  final String id;
  final String fromUserId;
  final String fromUserName;
  final String? fromUserAvatar;
  final String toUserId;
  final String toUserName;
  final String? toUserAvatar;
  final DateTime createdAt;
  final DateTime? respondedAt;
  final String status; // 'pending', 'accepted', 'rejected'

  const FriendRequest({
    required this.id,
    required this.fromUserId,
    required this.fromUserName,
    this.fromUserAvatar,
    required this.toUserId,
    required this.toUserName,
    this.toUserAvatar,
    required this.createdAt,
    this.respondedAt,
    this.status = 'pending',
  });

  /// Create from JSON
  factory FriendRequest.fromJson(Map<String, dynamic> json) {
    return FriendRequest(
      id: json['id'] as String,
      fromUserId: json['fromUserId'] as String,
      fromUserName: json['fromUserName'] as String,
      fromUserAvatar: json['fromUserAvatar'] as String?,
      toUserId: json['toUserId'] as String,
      toUserName: json['toUserName'] as String,
      toUserAvatar: json['toUserAvatar'] as String?,
      createdAt: DateTime.parse(json['createdAt'] as String),
      respondedAt: json['respondedAt'] != null
          ? DateTime.parse(json['respondedAt'] as String)
          : null,
      status: json['status'] as String? ?? 'pending',
    );
  }

  /// Convert to JSON
  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'fromUserId': fromUserId,
      'fromUserName': fromUserName,
      'fromUserAvatar': fromUserAvatar,
      'toUserId': toUserId,
      'toUserName': toUserName,
      'toUserAvatar': toUserAvatar,
      'createdAt': createdAt.toIso8601String(),
      'respondedAt': respondedAt?.toIso8601String(),
      'status': status,
    };
  }

  /// Copy with updated fields
  FriendRequest copyWith({
    String? id,
    String? fromUserId,
    String? fromUserName,
    String? fromUserAvatar,
    String? toUserId,
    String? toUserName,
    String? toUserAvatar,
    DateTime? createdAt,
    DateTime? respondedAt,
    String? status,
  }) {
    return FriendRequest(
      id: id ?? this.id,
      fromUserId: fromUserId ?? this.fromUserId,
      fromUserName: fromUserName ?? this.fromUserName,
      fromUserAvatar: fromUserAvatar ?? this.fromUserAvatar,
      toUserId: toUserId ?? this.toUserId,
      toUserName: toUserName ?? this.toUserName,
      toUserAvatar: toUserAvatar ?? this.toUserAvatar,
      createdAt: createdAt ?? this.createdAt,
      respondedAt: respondedAt ?? this.respondedAt,
      status: status ?? this.status,
    );
  }

  bool get isPending => status == 'pending';
  bool get isAccepted => status == 'accepted';
  bool get isRejected => status == 'rejected';

  @override
  List<Object?> get props => [
        id,
        fromUserId,
        fromUserName,
        fromUserAvatar,
        toUserId,
        toUserName,
        toUserAvatar,
        createdAt,
        respondedAt,
        status,
      ];

  @override
  String toString() {
    return 'FriendRequest(from: $fromUserName, to: $toUserName, status: $status)';
  }
}

