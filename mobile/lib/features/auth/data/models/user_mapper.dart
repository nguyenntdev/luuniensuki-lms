import '../../../../core/utils/url_utils.dart';
import '../../domain/entities/user.dart';
import 'auth_dtos.dart';

/// Extension methods for converting DTOs to domain entities
extension UserDtoMapper on UserDto {
  /// Convert UserDto to User entity
  /// Requires StatsDto for rank information
  User toEntity(StatsDto? stats) {
    final rankDto = stats?.rank;
    final nextRankDto = stats?.nextRank;

    return User(
      id: id,
      email: email,
      displayName: displayName,
      avatarUrl: UrlUtils.toFullUrl(avatarUrl),
      username: username,
      role: role,
      totalXp: stats?.totalXp ?? totalXp,
      isProfilePublic: isProfilePublic,
      currentStreak: stats?.currentStreak ?? currentStreak,
      longestStreak: longestStreak,
      streakFreezes: streakFreezes,
      lastActiveAt: lastActiveAt != null ? DateTime.tryParse(lastActiveAt!) : null,
      rank: rankDto?.toEntity() ?? Rank.forXp(totalXp),
      xpToNextRank: stats?.xpToNextRank ?? 0,
      nextRank: nextRankDto?.toEntity(),
    );
  }

  /// Convert UserDto to User entity without stats
  /// Uses default rank calculation based on XP
  User toEntitySimple() {
    final rank = Rank.forXp(totalXp);
    final nextRank = rank.next;
    final xpToNext = nextRank != null ? nextRank.xp - totalXp : 0;

    return User(
      id: id,
      email: email,
      displayName: displayName,
      avatarUrl: UrlUtils.toFullUrl(avatarUrl),
      username: username,
      role: role,
      totalXp: totalXp,
      isProfilePublic: isProfilePublic,
      currentStreak: currentStreak,
      longestStreak: longestStreak,
      streakFreezes: streakFreezes,
      lastActiveAt: lastActiveAt != null ? DateTime.tryParse(lastActiveAt!) : null,
      rank: rank,
      xpToNextRank: xpToNext,
      nextRank: nextRank,
    );
  }
}

/// Extension methods for converting RankDto to Rank entity
extension RankDtoMapper on RankDto {
  /// Convert RankDto to Rank entity
  Rank toEntity() {
    return Rank(
      level: level,
      name: name,
      xp: xp,
    );
  }
}

/// Extension methods for converting AuthResponseDto
extension AuthResponseDtoMapper on AuthResponseDto {
  /// Extract User entity from auth response
  User toUserEntity() {
    return user.toEntity(stats);
  }
}

/// Extension methods for converting LoginResponseDto
extension LoginResponseDtoMapper on LoginResponseDto {
  /// Extract User entity from login response
  User toUserEntity() {
    return user.toEntity(stats);
  }
}

/// Extension methods for converting User entity back to DTO (for caching)
extension UserToDto on User {
  /// Convert User entity to UserDto for caching
  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'email': email,
      'display_name': displayName,
      'avatar_url': avatarUrl,
      'username': username,
      'role': role,
      'total_xp': totalXp,
      'is_profile_public': isProfilePublic,
      'current_streak': currentStreak,
      'longest_streak': longestStreak,
      'streak_freezes': streakFreezes,
      'last_active_at': lastActiveAt?.toIso8601String(),
    };
  }

  /// Create User from cached JSON
  static User fromJson(Map<String, dynamic> json) {
    final totalXp = json['total_xp'] as int? ?? 0;
    final rank = Rank.forXp(totalXp);
    final nextRank = rank.next;

    return User(
      id: json['id'] as String,
      email: json['email'] as String,
      displayName: json['display_name'] as String,
      avatarUrl: json['avatar_url'] as String?,
      username: json['username'] as String?,
      role: json['role'] as String,
      totalXp: totalXp,
      isProfilePublic: json['is_profile_public'] as bool? ?? false,
      currentStreak: json['current_streak'] as int? ?? 0,
      longestStreak: json['longest_streak'] as int? ?? 0,
      streakFreezes: json['streak_freezes'] as int? ?? 0,
      lastActiveAt: json['last_active_at'] != null
          ? DateTime.tryParse(json['last_active_at'] as String)
          : null,
      rank: rank,
      xpToNextRank: nextRank != null ? nextRank.xp - totalXp : 0,
      nextRank: nextRank,
    );
  }
}
