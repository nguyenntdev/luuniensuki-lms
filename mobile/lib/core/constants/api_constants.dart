/// API constants for the Luuniensuki LMS mobile app.
/// Contains base URL, timeouts, and all API endpoint definitions.
class ApiConstants {
  ApiConstants._();

  // Base Configuration
  static const String baseUrl = 'https://lms.histolab.icu';
  static const String apiVersion = 'v1';
  static const String apiPath = '/api/$apiVersion';

  // Asset URLs
  static const String assetsUrl = '$baseUrl/assets';
  static const String motifsAssetsUrl = '$assetsUrl/motifs';
  static const String modelsAssetsUrl = '$assetsUrl/models';
  static const String manifestsAssetsUrl = '$modelsAssetsUrl/manifests';
  static String urnManifest(String slug) => '$manifestsAssetsUrl/$slug.json';
  static const String urnManifestIndex = '$manifestsAssetsUrl/index.json';

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

  // Practice & Assessment Endpoints (V5-T057)
  static const String practiceSync = '$apiPath/history/practice/sync';
  static const String practiceSubmit = '$apiPath/history/practice/submit';
  static const String practiceVerifyBadge = '$apiPath/history/practice/verify-badge';
  static String lessonQuizSync(String lessonId) => '$apiPath/history/lessons/$lessonId/quiz-sync';

  // Progress Endpoints
  static const String progressUnlock = '$apiPath/progress/unlock';
  static const String progressCompleteLesson =
      '$apiPath/progress/complete-lesson';

  // Gamification Endpoints
  static const String badges = '$apiPath/badges';
  static const String leaderboard = '$apiPath/leaderboard';
  static const String quests = '$apiPath/quests';
  static String questDetail(String slug) => '$apiPath/quests/$slug';
  static String questStart(String slug) => '$apiPath/quests/$slug/start';
  static String questClaim(String slug) => '$apiPath/quests/$slug/claim';
  static const String questSummary = '$apiPath/users/me/quest-summary';
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

  // AI Endpoints
  static const String aiTutor = '$apiPath/ai/tutor';
  static const String aiQa = '$apiPath/ai/qa';
  static const String aiSummary = '$apiPath/ai/summary';
  static const String aiFlashcards = '$apiPath/ai/flashcards';
  static const String aiExplain = '$apiPath/ai/explain';
  static const String aiCoach = '$apiPath/ai/coach';
  static const String aiFeedback = '$apiPath/ai/feedback';
  static const String aiReviewPlan = '$apiPath/ai/review-plan';
  static const String aiDiagnostic = '$apiPath/ai/diagnostic';

  // Streak Endpoints
  static const String streak = '$apiPath/users/me/streak';
  static const String useStreakFreeze = '$apiPath/users/me/streak/freeze';

  // Health Check
  static const String health = '/health';

  // Heritage Knowledge Catalogue Endpoints (V5-T053)
  static const String heritageCatalog = '$apiPath/heritage/catalog';
  static String heritageCatalogUrn(String slug) => '$apiPath/heritage/catalog/$slug';
  static String heritageCatalogMotif(String id) => '$apiPath/heritage/catalog/motifs/$id';

  // Public endpoints that don't require authentication
  static const List<String> publicEndpoints = [
    login,
    register,
    refreshToken,
    health,
    heritageCatalog,
  ];

  /// Check if a path is a public endpoint that doesn't require auth
  static bool isPublicEndpoint(String path) {
    return publicEndpoints.any((endpoint) => path.contains(endpoint));
  }
}
