/// API constants for the Luuniensuki LMS mobile app.
/// Contains base URL, timeouts, and all API endpoint definitions.
class ApiConstants {
  ApiConstants._();

  // Base Configuration
  // Override with --dart-define=API_BASE_URL=https://your-domain
  static const String rawBaseUrl = String.fromEnvironment(
    'API_BASE_URL',
    defaultValue: 'https://lms.histolab.icu',
  );
  static const String apiVersion = 'v1';
  static String get baseUrl => _normalizeBaseUrl(rawBaseUrl);
  static String get apiPath => '/api/$apiVersion';

  static String _normalizeBaseUrl(String url) {
    var normalized = url.trim();
    if (normalized.endsWith('/')) {
      normalized = normalized.substring(0, normalized.length - 1);
    }
    if (normalized.endsWith('/api')) {
      normalized = normalized.substring(0, normalized.length - 4);
    }
    return normalized;
  }

  // Asset URLs
  static String get assetsUrl => '$baseUrl/assets';
  static String get motifsAssetsUrl => '$assetsUrl/motifs';
  static String get modelsAssetsUrl => '$assetsUrl/models';

  // Timeouts
  static const Duration connectTimeout = Duration(seconds: 30);
  static const Duration receiveTimeout = Duration(seconds: 90);
  static const Duration sendTimeout = Duration(seconds: 30);

  // Auth Endpoints
  static String get login => '$apiPath/auth/login';
  static String get register => '$apiPath/auth/register';
  static String get logout => '$apiPath/auth/logout';
  static String get refreshToken => '$apiPath/auth/refresh';
  static String get me => '$apiPath/auth/me';

  // Content Endpoints
  static String get urns => '$apiPath/urns';
  static String urn(String slug) => '$apiPath/urns/$slug';
  static String motif(String id) => '$apiPath/motifs/$id';
  static String motifLesson(String id) => '$apiPath/motifs/$id/lesson';
  static String motifQuiz(String id) => '$apiPath/motifs/$id/quiz';
  static String motifQuizSubmit(String id) => '$apiPath/motifs/$id/quiz/submit';

  // Progress Endpoints
  static String get progressUnlock => '/progress/unlock';
  static String get progressCompleteLesson => '/progress/complete-lesson';

  // Gamification Endpoints
  static String get badges => '$apiPath/badges';
  static String get leaderboard => '$apiPath/leaderboard';
  static String get quests => '$apiPath/quests';
  static String get userBadges => '$apiPath/users/me/badges';
  static String get userQuests => '$apiPath/users/me/quests';

  // User Endpoints
  static String get userDashboard => '$apiPath/users/me/dashboard';
  static String get userStats => '$apiPath/users/me/stats';
  static String get userProgress => '$apiPath/users/me/progress';
  static String get userProfile => '$apiPath/users/me';
  static String get userCollection => '$apiPath/users/me/collection';

  // Dashboard Endpoints
  static String get dashboardSummary => '$apiPath/dashboard/summary';

  // Streak Endpoints
  static String get streak => '$apiPath/users/me/streak';
  static String get useStreakFreeze => '$apiPath/users/me/streak/freeze';

  // Health Check
  static const String health = '/health';

  // Public endpoints that don't require authentication
  static List<String> get publicEndpoints => [
        login,
        register,
        refreshToken,
        health,
      ];

  /// Check if a path is a public endpoint that doesn't require auth
  static bool isPublicEndpoint(String path) {
    return publicEndpoints.any((endpoint) => path.contains(endpoint));
  }
}
