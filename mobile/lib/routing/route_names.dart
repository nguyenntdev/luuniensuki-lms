/// Route names for the app navigation.
/// Using constants ensures type safety and prevents typos.
abstract class RouteNames {
  RouteNames._();

  // ==========================================================================
  // AUTH ROUTES
  // ==========================================================================

  /// Splash screen shown on app launch
  static const String splash = 'splash';

  /// Login screen
  static const String login = 'login';

  /// Registration screen
  static const String register = 'register';

  /// Forgot password screen
  static const String forgotPassword = 'forgot-password';

  // ==========================================================================
  // MAIN ROUTES (Bottom Navigation)
  // ==========================================================================

  /// Home/Dashboard screen
  static const String home = 'home';

  /// Explore screen (urn grid)
  static const String explore = 'explore';

  /// Collection screen (discovered motifs)
  static const String collection = 'collection';

  /// Achievements screen (badges + leaderboard)
  static const String achievements = 'achievements';

  /// AI chat screen
  static const String aiChat = 'ai-chat';

  /// Profile screen
  static const String profile = 'profile';

  // ==========================================================================
  // URN ROUTES
  // ==========================================================================

  /// Urn detail/viewer screen
  static const String urnDetail = 'urn-detail';

  /// Urn 3D viewer
  static const String urnViewer = 'urn-viewer';

  // ==========================================================================
  // MOTIF ROUTES
  // ==========================================================================

  /// Motif detail screen
  static const String motifDetail = 'motif-detail';

  /// Motif lesson screen
  static const String motifLesson = 'motif-lesson';

  /// Motif quiz screen
  static const String motifQuiz = 'motif-quiz';

  /// Quiz result screen
  static const String quizResult = 'quiz-result';

  // ==========================================================================
  // GAMIFICATION ROUTES
  // ==========================================================================

  /// Badges screen (all badges)
  static const String badges = 'badges';

  /// Badge detail screen
  static const String badgeDetail = 'badge-detail';

  /// Leaderboard screen
  static const String leaderboard = 'leaderboard';

  /// Quests screen
  static const String quests = 'quests';

  /// Quest detail screen
  static const String questDetail = 'quest-detail';

  // ==========================================================================
  // PROFILE ROUTES
  // ==========================================================================

  /// Edit profile screen
  static const String editProfile = 'edit-profile';

  /// Change password screen
  static const String changePassword = 'change-password';

  /// Settings screen
  static const String settings = 'settings';

  /// About screen
  static const String about = 'about';

  // ==========================================================================
  // ONBOARDING
  // ==========================================================================

  /// Onboarding flow
  static const String onboarding = 'onboarding';

  // ==========================================================================
  // ERROR ROUTES
  // ==========================================================================

  /// 404 Not found screen
  static const String notFound = 'not-found';

  /// Error screen
  static const String error = 'error';
}

/// Route paths for navigation.
/// These are the actual URL paths used by GoRouter.
abstract class RoutePaths {
  RoutePaths._();

  // Auth
  static const String splash = '/';
  static const String login = '/login';
  static const String register = '/register';
  static const String forgotPassword = '/forgot-password';

  // Main tabs
  static const String home = '/home';
  static const String explore = '/explore';
  static const String collection = '/collection';
  static const String achievements = '/achievements';
  static const String profile = '/profile';
  static const String aiChat = '/ai-chat';

  // Urns (base path for building)
  static const String urns = '/urns';

  // Motifs (base path for building)
  static const String motifs = '/motifs';

  // Gamification
  static const String badges = '/badges';
  static const String leaderboard = '/leaderboard';
  static const String quests = '/quests';

  // Profile
  static const String editProfile = '/profile/edit';
  static const String changePassword = '/profile/change-password';
  static const String settings = '/settings';
  static const String about = '/about';

  // Onboarding
  static const String onboarding = '/onboarding';

  // Error
  static const String notFound = '/404';
  static const String error = '/error';

  // ==========================================================================
  // PATH BUILDERS
  // ==========================================================================

  /// Build urn detail path
  static String urn(String urnSlug) => '/urns/$urnSlug';

  /// Build urn viewer path
  static String urnViewerPath(String urnSlug) => '/urns/$urnSlug/viewer';

  /// Build motif detail path
  static String motif(String motifId) => '/motifs/$motifId';

  /// Build motif lesson path
  static String lesson(String motifId) => '/motifs/$motifId/lesson';

  /// Build motif quiz path
  static String quiz(String motifId) => '/motifs/$motifId/quiz';

  /// Build quiz result path
  static String quizResultPath(String motifId) => '/motifs/$motifId/quiz/result';

  /// Build badge detail path
  static String badge(String badgeId) => '/badges/$badgeId';

  /// Build quest detail path
  static String quest(String questId) => '/quests/$questId';
}
