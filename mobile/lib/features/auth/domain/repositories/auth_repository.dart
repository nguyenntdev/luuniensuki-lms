import 'package:dartz/dartz.dart';

import '../../../../core/errors/failures.dart';
import '../entities/user.dart';

/// Abstract interface for authentication operations.
/// This is the domain layer contract that data layer must implement.
abstract class AuthRepository {
  /// Login with email and password.
  /// Returns [User] on success or [Failure] on error.
  Future<Either<Failure, User>> login({
    required String email,
    required String password,
  });

  /// Register a new user account.
  /// Returns [User] on success or [Failure] on error.
  Future<Either<Failure, User>> register({
    required String email,
    required String password,
    required String displayName,
  });

  /// Get the currently authenticated user.
  /// Returns [User] on success or [Failure] if not authenticated or error.
  Future<Either<Failure, User>> getCurrentUser();

  /// Logout the current user.
  /// Clears local tokens and session data.
  /// Returns void on success or [Failure] on error.
  Future<Either<Failure, void>> logout();

  /// Refresh the access token using the refresh token.
  /// Returns true if refresh was successful.
  Future<Either<Failure, bool>> refreshToken();

  /// Check if user is currently logged in.
  /// This is a quick local check, not a server validation.
  Future<bool> isLoggedIn();

  /// Update user profile information.
  /// Returns updated [User] on success or [Failure] on error.
  Future<Either<Failure, User>> updateProfile({
    String? displayName,
    String? username,
    String? avatarUrl,
    bool? isProfilePublic,
  });

  /// Change user password.
  /// Returns void on success or [Failure] on error.
  Future<Either<Failure, void>> changePassword({
    required String currentPassword,
    required String newPassword,
  });

  /// Delete user account.
  /// This is a destructive operation.
  Future<Either<Failure, void>> deleteAccount();

  /// Request password reset email.
  Future<Either<Failure, void>> requestPasswordReset({
    required String email,
  });

  /// Use a streak freeze to protect the current streak.
  Future<Either<Failure, User>> useStreakFreeze();

  /// Get user statistics.
  Future<Either<Failure, UserStats>> getUserStats();
}

/// User statistics data class
class UserStats {
  final int totalXp;
  final int motifsDiscovered;
  final int motifsLearned;
  final int motifsMastered;
  final int badgesEarned;
  final int quizzesCompleted;
  final int currentStreak;
  final int longestStreak;
  final Rank rank;
  final int xpToNextRank;
  final Rank? nextRank;

  const UserStats({
    required this.totalXp,
    required this.motifsDiscovered,
    required this.motifsLearned,
    required this.motifsMastered,
    required this.badgesEarned,
    required this.quizzesCompleted,
    required this.currentStreak,
    required this.longestStreak,
    required this.rank,
    required this.xpToNextRank,
    this.nextRank,
  });

  /// Total motifs count
  int get totalMotifs => motifsDiscovered + motifsLearned + motifsMastered;

  /// Check if user has any activity
  bool get hasActivity => totalXp > 0 || totalMotifs > 0;

  /// Calculate overall progress percentage (assuming ~100 total motifs)
  double get overallProgress {
    const estimatedTotalMotifs = 100;
    return (motifsMastered / estimatedTotalMotifs).clamp(0.0, 1.0);
  }

  /// Create a copy with updated fields
  UserStats copyWith({
    int? totalXp,
    int? motifsDiscovered,
    int? motifsLearned,
    int? motifsMastered,
    int? badgesEarned,
    int? quizzesCompleted,
    int? currentStreak,
    int? longestStreak,
    Rank? rank,
    int? xpToNextRank,
    Rank? nextRank,
  }) {
    return UserStats(
      totalXp: totalXp ?? this.totalXp,
      motifsDiscovered: motifsDiscovered ?? this.motifsDiscovered,
      motifsLearned: motifsLearned ?? this.motifsLearned,
      motifsMastered: motifsMastered ?? this.motifsMastered,
      badgesEarned: badgesEarned ?? this.badgesEarned,
      quizzesCompleted: quizzesCompleted ?? this.quizzesCompleted,
      currentStreak: currentStreak ?? this.currentStreak,
      longestStreak: longestStreak ?? this.longestStreak,
      rank: rank ?? this.rank,
      xpToNextRank: xpToNextRank ?? this.xpToNextRank,
      nextRank: nextRank ?? this.nextRank,
    );
  }
}
