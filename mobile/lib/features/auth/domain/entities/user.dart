import 'package:equatable/equatable.dart';

/// User entity representing the authenticated user.
/// This is a domain entity that is independent of the data layer.
class User extends Equatable {
  final String id;
  final String email;
  final String displayName;
  final String? avatarUrl;
  final String? username;
  final String role;
  final int totalXp;
  final bool isProfilePublic;
  final int currentStreak;
  final int longestStreak;
  final int streakFreezes;
  final DateTime? lastActiveAt;
  final Rank rank;
  final int xpToNextRank;
  final Rank? nextRank;

  const User({
    required this.id,
    required this.email,
    required this.displayName,
    this.avatarUrl,
    this.username,
    required this.role,
    required this.totalXp,
    required this.isProfilePublic,
    this.currentStreak = 0,
    this.longestStreak = 0,
    this.streakFreezes = 0,
    this.lastActiveAt,
    required this.rank,
    required this.xpToNextRank,
    this.nextRank,
  });

  // ==========================================================================
  // ROLE HELPERS
  // ==========================================================================

  /// Check if user is a guest (limited access)
  bool get isGuest => role == 'guest';

  /// Check if user is a learner (standard user)
  bool get isLearner => role == 'learner';

  /// Check if user is a teacher
  bool get isTeacher => role == 'teacher';

  /// Check if user is an admin
  bool get isAdmin => role == 'admin' || role == 'super_admin';

  /// Check if user is a super admin
  bool get isSuperAdmin => role == 'super_admin';

  /// Check if user has elevated privileges (teacher or admin)
  bool get hasElevatedPrivileges => isTeacher || isAdmin;

  // ==========================================================================
  // DISPLAY HELPERS
  // ==========================================================================

  /// Get user initials for avatar fallback
  String get initials {
    final parts = displayName.trim().split(' ');
    if (parts.isEmpty) return '?';
    if (parts.length == 1) {
      return parts[0].isNotEmpty ? parts[0][0].toUpperCase() : '?';
    }
    return '${parts[0][0]}${parts[parts.length - 1][0]}'.toUpperCase();
  }

  /// Get display name or email as fallback
  String get displayNameOrEmail {
    if (displayName.isNotEmpty) return displayName;
    return email.split('@').first;
  }

  /// Check if user has an avatar
  bool get hasAvatar => avatarUrl != null && avatarUrl!.isNotEmpty;

  // ==========================================================================
  // STREAK HELPERS
  // ==========================================================================

  /// Check if user has an active streak
  bool get hasActiveStreak => currentStreak > 0;

  /// Check if user has streak freezes available
  bool get canFreezeStreak => streakFreezes > 0;

  // ==========================================================================
  // XP & RANK HELPERS
  // ==========================================================================

  /// Calculate progress to next rank (0.0 - 1.0)
  double get progressToNextRank {
    if (nextRank == null || xpToNextRank <= 0) return 1.0;

    final xpInCurrentRank = totalXp - rank.xp;
    final xpNeededForNext = nextRank!.xp - rank.xp;

    if (xpNeededForNext <= 0) return 1.0;
    return (xpInCurrentRank / xpNeededForNext).clamp(0.0, 1.0);
  }

  /// Check if user is at max rank
  bool get isMaxRank => nextRank == null;

  // ==========================================================================
  // COPY WITH
  // ==========================================================================

  /// Create a copy of this user with updated fields
  User copyWith({
    String? id,
    String? email,
    String? displayName,
    String? avatarUrl,
    String? username,
    String? role,
    int? totalXp,
    bool? isProfilePublic,
    int? currentStreak,
    int? longestStreak,
    int? streakFreezes,
    DateTime? lastActiveAt,
    Rank? rank,
    int? xpToNextRank,
    Rank? nextRank,
  }) {
    return User(
      id: id ?? this.id,
      email: email ?? this.email,
      displayName: displayName ?? this.displayName,
      avatarUrl: avatarUrl ?? this.avatarUrl,
      username: username ?? this.username,
      role: role ?? this.role,
      totalXp: totalXp ?? this.totalXp,
      isProfilePublic: isProfilePublic ?? this.isProfilePublic,
      currentStreak: currentStreak ?? this.currentStreak,
      longestStreak: longestStreak ?? this.longestStreak,
      streakFreezes: streakFreezes ?? this.streakFreezes,
      lastActiveAt: lastActiveAt ?? this.lastActiveAt,
      rank: rank ?? this.rank,
      xpToNextRank: xpToNextRank ?? this.xpToNextRank,
      nextRank: nextRank ?? this.nextRank,
    );
  }

  @override
  List<Object?> get props => [
        id,
        email,
        displayName,
        avatarUrl,
        username,
        role,
        totalXp,
        isProfilePublic,
        currentStreak,
        longestStreak,
        streakFreezes,
        lastActiveAt,
        rank,
        xpToNextRank,
        nextRank,
      ];

  @override
  String toString() {
    return 'User(id: $id, email: $email, displayName: $displayName, role: $role, totalXp: $totalXp)';
  }
}

/// Rank entity representing a user's XP rank level.
class Rank extends Equatable {
  final int level;
  final String name;
  final int xp;

  const Rank({
    required this.level,
    required this.name,
    required this.xp,
  });

  /// Default ranks based on the backend XP_RANKS
  static const List<Rank> defaultRanks = [
    Rank(level: 1, name: 'Lính Mới', xp: 0),
    Rank(level: 2, name: 'Học Viên', xp: 100),
    Rank(level: 3, name: 'Thư Sinh', xp: 300),
    Rank(level: 4, name: 'Tri Huyện', xp: 600),
    Rank(level: 5, name: 'Tiến Sĩ', xp: 1000),
    Rank(level: 6, name: 'Thượng Thư', xp: 1500),
    Rank(level: 7, name: 'Thái Tử', xp: 2100),
    Rank(level: 8, name: 'Hoàng Đế', xp: 2800),
    Rank(level: 9, name: 'Sử Quan', xp: 3600),
  ];

  /// Get rank for a given XP value
  static Rank forXp(int xp) {
    Rank current = defaultRanks.first;
    for (final rank in defaultRanks) {
      if (xp >= rank.xp) {
        current = rank;
      } else {
        break;
      }
    }
    return current;
  }

  /// Get next rank after this one, or null if max
  Rank? get next {
    final index = defaultRanks.indexWhere((r) => r.level == level);
    if (index == -1 || index >= defaultRanks.length - 1) return null;
    return defaultRanks[index + 1];
  }

  /// Check if this is the highest rank
  bool get isMax => level == defaultRanks.last.level;

  /// Create a copy with updated fields
  Rank copyWith({
    int? level,
    String? name,
    int? xp,
  }) {
    return Rank(
      level: level ?? this.level,
      name: name ?? this.name,
      xp: xp ?? this.xp,
    );
  }

  @override
  List<Object?> get props => [level, name, xp];

  @override
  String toString() => 'Rank(level: $level, name: $name, xp: $xp)';
}
