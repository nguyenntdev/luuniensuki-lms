/// App-wide constants for Luuniensuki LMS
class AppConstants {
  // Private constructor to prevent instantiation
  AppConstants._();

  // App Info
  static const String appName = 'Lưu Niên Sử Kí';
  static const String appNameEn = 'Luuniensuki LMS';
  static const String appVersion = '1.0.0';

  // XP System
  static const int discoveryXp = 25;
  static const int lessonXp = 50;
  static const int masteredXp = 75;
  static const int urnExamXp = 300;
  static const int quizPassPercent = 80;

  // XP Celebration Thresholds
  static const int smallXpThreshold = 25; // Quick badge popup
  static const int mediumXpThreshold = 50; // Badge + subtle particles
  static const int largeXpThreshold = 300; // Full confetti blast

  // XP Ranks (Vietnamese titles)
  static const List<Map<String, dynamic>> xpRanks = [
    {'level': 1, 'name': 'Lính Mới', 'xp': 0},
    {'level': 2, 'name': 'Học Viên', 'xp': 100},
    {'level': 3, 'name': 'Thư Sinh', 'xp': 300},
    {'level': 4, 'name': 'Tri Huyện', 'xp': 600},
    {'level': 5, 'name': 'Tiến Sĩ', 'xp': 1000},
    {'level': 6, 'name': 'Thượng Thư', 'xp': 1500},
    {'level': 7, 'name': 'Thái Tử', 'xp': 2100},
    {'level': 8, 'name': 'Hoàng Đế', 'xp': 2800},
    {'level': 9, 'name': 'Sử Quan', 'xp': 3600},
  ];

  /// Get rank information for a given XP amount
  static Map<String, dynamic> getRankForXp(int xp) {
    Map<String, dynamic> currentRank = xpRanks.first;
    for (final rank in xpRanks) {
      if (xp >= rank['xp']) {
        currentRank = rank;
      } else {
        break;
      }
    }
    return currentRank;
  }

  /// Get next rank information
  static Map<String, dynamic>? getNextRank(int currentXp) {
    for (final rank in xpRanks) {
      if (currentXp < rank['xp']) {
        return rank;
      }
    }
    return null; // Already at max rank
  }

  /// Check if XP gain causes level up
  static bool didLevelUp(int oldXp, int newXp) {
    final oldRank = getRankForXp(oldXp);
    final newRank = getRankForXp(newXp);
    return oldRank['level'] != newRank['level'];
  }

  // Number of urns (Cửu Đỉnh = 9 urns)
  static const int totalUrns = 9;

  // Cache Durations
  static const Duration urnsCacheDuration = Duration(hours: 24);
  static const Duration motifsCacheDuration = Duration(hours: 12);
  static const Duration progressCacheDuration = Duration(minutes: 5);
  static const Duration leaderboardCacheDuration = Duration(minutes: 10);
  static const Duration badgesCacheDuration = Duration(hours: 6);

  // Animation Durations
  static const Duration shortAnimationDuration = Duration(milliseconds: 200);
  static const Duration mediumAnimationDuration = Duration(milliseconds: 350);
  static const Duration longAnimationDuration = Duration(milliseconds: 500);

  // UI Constants
  static const double defaultPadding = 16.0;
  static const double smallPadding = 8.0;
  static const double largePadding = 24.0;
  static const double borderRadius = 12.0;
  static const double cardElevation = 2.0;

  // 3D Viewer
  static const double defaultCameraDistance = 5.0;
  static const double minZoom = 2.0;
  static const double maxZoom = 10.0;
  static const double hotspotRadius = 0.12;

  // Pagination
  static const int defaultPageSize = 20;
  static const int leaderboardPageSize = 50;

  // Storage Keys
  static const String hasSeenOnboardingKey = 'hasSeenOnboarding';
  static const String hasSeenViewerTipsKey = 'hasSeenViewerTips';
  static const String selectedLanguageKey = 'selectedLanguage';

  // Supported Languages
  static const String vietnameseLocale = 'vi';
  static const String englishLocale = 'en';
  static const String defaultLocale = vietnameseLocale;
}
