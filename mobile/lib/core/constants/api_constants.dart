/// API constants for the Luuniensuki LMS mobile app.
/// Contains base URL, timeouts, and all API endpoint definitions.
class ApiConstants {
  ApiConstants._();

  // Base Configuration
  static const String baseUrl = 'https://lms.histolab.icu';
  static const String apiVersion = 'v1';
  static const String apiPath = '/api/$apiVersion';

  // Timeouts
  static const Duration connectTimeout = Duration(seconds: 30);
  static const Duration receiveTimeout = Duration(seconds: 30);
  static const Duration sendTimeout = Duration(seconds: 30);

  // Auth Endpoints
  static const String login = '$apiPath/auth/login';
  static const String register = '$apiPath/auth/register';
  static const String logout = '$apiPath/auth/logout';
  static const String refreshToken = '$apiPath/auth/refresh';
  static const String me = '$apiPath/auth/me';

  // Content Endpoints
  static const String urns = '$apiPath/urns';
  static String urn(String slug) => '$apiPath/urns/$slug';
  static String motif(String id) => '$apiPath/motifs/$id';
  static String motifLesson(String id) => '$apiPath/motifs/$id/lesson';
  static String motifQuiz(String id) => '$apiPath/motifs/$id/quiz';
  static String motifQuizSubmit(String id) => '$apiPath/motifs/$id/quiz/submit';

  // Progress Endpoints
  static const String progressUnlock = '$apiPath/progress/unlock';
  static const String progressCompleteLesson = '$apiPath/progress/complete-lesson';

  // Gamification Endpoints
  static const String badges = '$apiPath/badges';
  static const String leaderboard = '$apiPath/leaderboard';
  static const String quests = '$apiPath/quests';
  static const String userBadges = '$apiPath/users/me/badges';
  static const String userQuests = '$apiPath/users/me/quests';

  // User Endpoints
  static const String userDashboard = '$apiPath/users/me/dashboard';
  static const String userStats = '$apiPath/users/me/stats';
  static const String userProgress = '$apiPath/users/me/progress';
  static const String userProfile = '$apiPath/users/me';
  static const String userCollection = '$apiPath/users/me/collection';

  // Dashboard Endpoints
  static const String dashboardSummary = '$apiPath/dashboard/summary';

  // Streak Endpoints
  static const String streak = '$apiPath/users/me/streak';
  static const String useStreakFreeze = '$apiPath/users/me/streak/freeze';

  // Health Check
  static const String health = '/health';

  // Public endpoints that don't require authentication
  static const List<String> publicEndpoints = [
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
