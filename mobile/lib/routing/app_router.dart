import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:riverpod_annotation/riverpod_annotation.dart';

import '../core/storage/hive_storage.dart';
import '../features/auth/presentation/providers/auth_provider.dart';
import '../features/auth/presentation/screens/login_screen.dart';
import '../features/auth/presentation/screens/register_screen.dart';
import '../features/explore/presentation/screens/explore_screen.dart';
import '../features/collection/presentation/screens/collection_screen.dart';
import '../features/learning_path/presentation/screens/learning_path_screen.dart';
import '../features/learning_path/presentation/screens/learn_practice_hub_screen.dart';
import '../features/practice/presentation/screens/practice_screen.dart';
import '../features/practice/presentation/screens/practice_session_screen.dart';
import '../features/ai_chat/presentation/screens/ai_hub_screen.dart';
import '../features/achievements/presentation/screens/achievements_screen.dart';
import '../features/profile/presentation/screens/profile_screen.dart';
import '../features/settings/presentation/screens/settings_screen.dart';
import '../features/urn_viewer/presentation/screens/urn_viewer_screen.dart';
import '../features/lesson/presentation/screens/motif_detail_screen.dart';
import '../features/quiz/presentation/screens/quiz_screen.dart';
import '../features/help/presentation/screens/help_support_screen.dart';
import '../features/history/presentation/history_atlas_screen.dart';
import '../features/notifications/presentation/screens/notifications_screen.dart';
import '../features/daily_goals/presentation/screens/daily_goal_screen.dart';
import '../features/gems/presentation/screens/gems_shop_screen.dart';
import '../features/hearts/presentation/screens/hearts_refill_screen.dart';
import '../features/social/presentation/screens/friends_screen.dart';
import '../features/quests/presentation/screens/quests_screen.dart';
import '../features/quests/presentation/screens/quest_detail_screen.dart';
import '../features/profile/presentation/screens/personal_info_screen.dart';
import '../features/onboarding/presentation/screens/onboarding_screen.dart';
import '../features/offline_kit/presentation/screens/low_bandwidth_kit_screen.dart';
import '../features/streak/services/streak_event_service.dart';
import 'route_names.dart';
import '../shared/widgets/glass/glass_bottom_nav.dart';
import '../shared/widgets/glass/glass_nav_metrics.dart';

part 'app_router.g.dart';

/// Notifier that bridges Riverpod AuthNotifier changes with GoRouter refresh.
class RouterNotifier extends ChangeNotifier {
  final Ref _ref;

  RouterNotifier(this._ref) {
    _ref.listen(authNotifierProvider, (_, __) => notifyListeners());
  }
}

/// Helper to check if a route requires standard learner or higher privileges.
bool _isLearnerOnlyRoute(String location) {
  const learnerOnlyPrefixes = [
    RoutePaths.collection,
    RoutePaths.learnPractice,
    RoutePaths.learningPath,
    RoutePaths.practice,
    RoutePaths.aiHub,
    RoutePaths.achievements,
    RoutePaths.dailyGoal,
    RoutePaths.gemsShop,
    RoutePaths.heartsRefill,
    RoutePaths.friends,
    RoutePaths.editProfile,
    RoutePaths.changePassword,
    RoutePaths.notifications,
  ];
  return learnerOnlyPrefixes.any(
    (prefix) => location == prefix || location.startsWith('$prefix/'),
  );
}

/// Provides the GoRouter instance configured with all app routes.
/// Handles authentication-based redirects and navigation.
/// Using keepAlive to maintain router instance and prevent unnecessary rebuilds
@Riverpod(keepAlive: true)
GoRouter appRouter(Ref ref) {
  final storage = ref.read(hiveStorageProvider);
  final routerNotifier = RouterNotifier(ref);

  return GoRouter(
    initialLocation: RoutePaths.explore,
    debugLogDiagnostics: true,
    refreshListenable: routerNotifier,

    // Redirect logic based on auth state, roles, and onboarding
    redirect: (_, state) {
      // Use ref.read here - refreshListenable triggers re-evaluation on auth changes
      final authState = ref.read(authNotifierProvider);

      final isLoggedIn = authState.maybeMap(
        authenticated: (_) => true,
        orElse: () => false,
      );
      final currentUser = authState.user;

      final isOnboarding = state.matchedLocation == RoutePaths.onboarding;
      final isLoggingIn = state.matchedLocation == RoutePaths.login;
      final isRegistering = state.matchedLocation == RoutePaths.register;
      final isAuthRoute = isLoggingIn || isRegistering;
      final isPublicRoute = state.matchedLocation == RoutePaths.historyAtlas ||
          state.matchedLocation == RoutePaths.help ||
          state.matchedLocation == RoutePaths.about;

      // Still checking auth status - allow navigation to proceed
      final isInitial = authState.maybeMap(
        initial: (_) => true,
        loading: (_) => true,
        orElse: () => false,
      );
      if (isInitial) {
        return null;
      }

      // Check if user has seen onboarding
      final hasSeenOnboarding = storage.hasSeenOnboarding();

      // Not seen onboarding and not currently on onboarding -> redirect to onboarding
      if (isLoggedIn && !hasSeenOnboarding && !isOnboarding) {
        return RoutePaths.onboarding;
      }

      // On onboarding but already seen it -> go to explore
      if (isOnboarding && hasSeenOnboarding) {
        return RoutePaths.explore;
      }

      // Not logged in and not on auth route / onboarding / public route -> redirect to login
      if (!isLoggedIn && !isAuthRoute && !isOnboarding && !isPublicRoute) {
        final returnUrl = Uri.encodeComponent(state.matchedLocation);
        return '${RoutePaths.login}?returnUrl=$returnUrl';
      }

      // Logged in and on auth route -> redirect to explore or returnUrl
      if (isLoggedIn && isAuthRoute) {
        final returnUrl = state.uri.queryParameters['returnUrl'];
        if (returnUrl != null && returnUrl.isNotEmpty) {
          return Uri.decodeComponent(returnUrl);
        }
        return RoutePaths.explore;
      }

      // Role-aware guard: Guest users have restricted access
      if (isLoggedIn && (currentUser?.isGuest ?? false)) {
        if (_isLearnerOnlyRoute(state.matchedLocation)) {
          final returnUrl = Uri.encodeComponent(state.matchedLocation);
          return '${RoutePaths.login}?returnUrl=$returnUrl';
        }
      }

      // Role-aware guard: Administrative and Teacher routes
      final isAdminRoute = state.matchedLocation.startsWith('/admin');
      final isTeacherRoute = state.matchedLocation.startsWith('/teacher');
      if (isAdminRoute && !(currentUser?.isAdmin ?? false)) {
        return RoutePaths.explore;
      }
      if (isTeacherRoute && !(currentUser?.hasElevatedPrivileges ?? false)) {
        return RoutePaths.explore;
      }

      // Allow navigation
      return null;
    },

    routes: [
      // =======================================================================
      // ALIAS & REDIRECT ROUTES (Safe fallback to live production screens)
      // =======================================================================
      GoRoute(
        path: RoutePaths.splash,
        redirect: (_, __) => RoutePaths.explore,
      ),
      GoRoute(
        path: RoutePaths.home,
        redirect: (_, __) => RoutePaths.explore,
      ),
      GoRoute(
        path: RoutePaths.badges,
        redirect: (_, __) => RoutePaths.achievements,
      ),
      GoRoute(
        path: RoutePaths.leaderboard,
        redirect: (_, __) => RoutePaths.achievements,
      ),
      GoRoute(
        path: RoutePaths.about,
        redirect: (_, __) => RoutePaths.settings,
      ),

      // =======================================================================
      // ONBOARDING
      // =======================================================================
      GoRoute(
        path: RoutePaths.onboarding,
        name: 'onboarding',
        builder: (_, __) => const OnboardingScreen(),
      ),

      // =======================================================================
      // AUTH ROUTES
      // =======================================================================
      GoRoute(
        path: RoutePaths.login,
        name: 'login',
        builder: (_, __) => const LoginScreen(),
      ),
      GoRoute(
        path: RoutePaths.register,
        name: 'register',
        builder: (_, __) => const RegisterScreen(),
      ),

      // =======================================================================
      // MAIN SHELL WITH BOTTOM NAVIGATION
      // =======================================================================
      ShellRoute(
        builder: (_, __, child) {
          return MainShell(child: child);
        },
        routes: [
          // Explore (Home) - Urn grid
          GoRoute(
            path: RoutePaths.explore,
            name: 'explore',
            pageBuilder: (_, __) => const NoTransitionPage(
              child: ExploreScreen(),
            ),
          ),

          // Collection - User's discovered motifs
          GoRoute(
            path: RoutePaths.collection,
            name: 'collection',
            pageBuilder: (_, __) => const NoTransitionPage(
              child: CollectionScreen(),
            ),
          ),

          // Learning Path - Structured learning progression
          GoRoute(
            path: RoutePaths.learnPractice,
            name: 'learnPractice',
            pageBuilder: (_, __) => const NoTransitionPage(
              child: LearnPracticeHubScreen(),
            ),
          ),

          // AI Hub - Chat and AI features
          GoRoute(
            path: RoutePaths.aiHub,
            name: RouteNames.aiHub,
            pageBuilder: (_, __) => const NoTransitionPage(
              child: AiHubScreen(),
            ),
          ),

          // Learning Path - kept for deep links/backward compatibility
          GoRoute(
            path: RoutePaths.learningPath,
            name: 'learningPath',
            pageBuilder: (_, __) => const NoTransitionPage(
              child: LearningPathScreen(),
            ),
          ),

          // Practice - Spaced repetition and review modes
          GoRoute(
            path: RoutePaths.practice,
            name: 'practice',
            pageBuilder: (_, __) => const NoTransitionPage(
              child: PracticeScreen(),
            ),
            routes: [
              // Practice session route
              GoRoute(
                path: RoutePaths.practiceSessionSegment,
                name: RouteNames.practiceSession,
                builder: (_, __) => const PracticeSessionScreen(),
              ),
            ],
          ),

          // Achievements - Badges and leaderboard
          GoRoute(
            path: RoutePaths.achievements,
            name: 'achievements',
            pageBuilder: (_, __) => const NoTransitionPage(
              child: AchievementsScreen(),
            ),
          ),

          // Profile - User profile and settings
          GoRoute(
            path: RoutePaths.profile,
            name: 'profile',
            pageBuilder: (_, __) => const NoTransitionPage(
              child: ProfileScreen(),
            ),
          ),
        ],
      ),

      // =======================================================================
      // URN & MOTIF ROUTES (Full screen, outside shell)
      // =======================================================================
      GoRoute(
        path: RoutePaths.historyAtlas,
        name: RouteNames.historyAtlas,
        builder: (_, __) => const HistoryAtlasScreen(),
      ),
      GoRoute(
        path: RoutePaths.offlineKit,
        name: RouteNames.offlineKit,
        builder: (_, __) => const LowBandwidthKitScreen(),
      ),

      GoRoute(
        path: '${RoutePaths.urns}/:urnSlug',
        name: 'urn',
        builder: (_, state) {
          final urnSlug = state.pathParameters['urnSlug'] ?? '';
          return UrnViewerScreen(urnSlug: urnSlug);
        },
      ),

      GoRoute(
        path: '${RoutePaths.motifs}/:motifId',
        name: 'motif',
        builder: (_, state) {
          final motifId = state.pathParameters['motifId'] ?? '';
          return MotifDetailScreen(motifId: motifId);
        },
        routes: [
          // Lesson route under motif (same as motif detail, different tab)
          GoRoute(
            path: RoutePaths.lessonSegment,
            name: RouteNames.motifLesson,
            builder: (_, state) {
              final motifId = state.pathParameters['motifId'] ?? '';
              return MotifDetailScreen(motifId: motifId);
            },
          ),
          // Quiz route under motif
          GoRoute(
            path: RoutePaths.quizSegment,
            name: RouteNames.motifQuiz,
            builder: (_, state) {
              final motifId = state.pathParameters['motifId'] ?? '';
              return QuizScreen(motifId: motifId);
            },
          ),
        ],
      ),

      // =======================================================================
      // QUEST ROUTES (Live production screens)
      // =======================================================================
      GoRoute(
        path: RoutePaths.quests,
        name: RouteNames.quests,
        builder: (_, __) => const QuestsScreen(),
      ),
      GoRoute(
        path: '${RoutePaths.quests}/:questId',
        name: RouteNames.questDetail,
        builder: (_, state) {
          final questId = state.pathParameters['questId'] ?? '';
          return QuestDetailScreen(questId: questId);
        },
      ),

      // =======================================================================
      // SETTINGS ROUTES
      // =======================================================================
      GoRoute(
        path: RoutePaths.settings,
        name: 'settings',
        builder: (_, __) => const SettingsScreen(),
      ),
      GoRoute(
        path: RoutePaths.editProfile,
        name: RouteNames.editProfile,
        builder: (_, __) => const PersonalInfoScreen(),
      ),

      // =======================================================================
      // DAILY GOAL ROUTE
      // =======================================================================
      GoRoute(
        path: RoutePaths.dailyGoal,
        name: 'dailyGoal',
        builder: (_, __) => const DailyGoalScreen(),
      ),

      // =======================================================================
      // HELP & SUPPORT ROUTES
      // =======================================================================
      GoRoute(
        path: RoutePaths.help,
        name: 'help',
        builder: (_, __) => const HelpSupportScreen(),
      ),

      // =======================================================================
      // NOTIFICATIONS ROUTE
      // =======================================================================
      GoRoute(
        path: RoutePaths.notifications,
        name: 'notifications',
        builder: (_, __) => const NotificationsScreen(),
      ),

      // =======================================================================
      // GEMS SHOP ROUTE
      // =======================================================================
      GoRoute(
        path: RoutePaths.gemsShop,
        name: 'gemsShop',
        builder: (_, __) => const GemsShopScreen(),
      ),

      // =======================================================================
      // HEARTS REFILL ROUTE
      // =======================================================================
      GoRoute(
        path: RoutePaths.heartsRefill,
        name: 'heartsRefill',
        builder: (_, state) {
          final returnPath = state.uri.queryParameters['returnPath'];
          return HeartsRefillScreen(returnPath: returnPath);
        },
      ),

      // =======================================================================
      // FRIENDS ROUTE
      // =======================================================================
      GoRoute(
        path: RoutePaths.friends,
        name: 'friends',
        builder: (_, __) => const FriendsScreen(),
      ),
    ],

    // Error page
    errorBuilder: (_, state) => ErrorScreen(error: state.error),
  );
}

// =============================================================================
// MAIN SHELL WITH BOTTOM NAVIGATION
// =============================================================================

class MainShell extends ConsumerStatefulWidget {
  final Widget child;

  const MainShell({super.key, required this.child});

  @override
  ConsumerState<MainShell> createState() => _MainShellState();
}

class _MainShellState extends ConsumerState<MainShell> {
  bool _hasCheckedStreak = false;

  @override
  void initState() {
    super.initState();
    // Check streak reminder after the widget is built
    WidgetsBinding.instance.addPostFrameCallback((_) {
      _checkStreakReminder();
    });
  }

  Future<void> _checkStreakReminder() async {
    if (_hasCheckedStreak) return;
    _hasCheckedStreak = true;

    // Wait for authentication to complete
    final authState = ref.read(authNotifierProvider);
    if (!authState.isAuthenticated) return;

    // Check and show streak reminder if needed
    final streakService = ref.read(streakEventServiceProvider);
    if (mounted) {
      await streakService.checkAndShowStreakReminder(context);
    }
  }

  @override
  Widget build(BuildContext context) {
    final navInset = GlassNavMetrics.contentInset(context);
    final keyboardVisible = GlassNavMetrics.isKeyboardVisible(context);
    final barBottomOffset = GlassNavMetrics.barBottomOffset(context);

    return Scaffold(
      body: Stack(
        children: [
          // Content
          Padding(
            padding: EdgeInsets.only(bottom: navInset),
            child: MediaQuery.removePadding(
              context: context,
              removeBottom: true,
              child: widget.child,
            ),
          ),

          // Glass Bottom Navigation
          Positioned(
            left: GlassNavMetrics.horizontalMargin,
            right: GlassNavMetrics.horizontalMargin,
            bottom: barBottomOffset,
            child: IgnorePointer(
              ignoring: keyboardVisible,
              child: AnimatedSlide(
                duration: const Duration(milliseconds: 220),
                curve: Curves.easeOutCubic,
                offset: keyboardVisible ? const Offset(0, 1.2) : Offset.zero,
                child: AnimatedOpacity(
                  duration: const Duration(milliseconds: 180),
                  opacity: keyboardVisible ? 0 : 1,
                  child: GlassBottomNav(
                    currentIndex: _calculateSelectedIndex(context),
                    onTap: (index) => _onItemTapped(index, context),
                    items: const [
                      GlassBottomNavItem(
                        icon: Icons.explore_outlined,
                        activeIcon: Icons.explore,
                        label: 'Khám Phá',
                      ),
                      GlassBottomNavItem(
                        icon: Icons.school_outlined,
                        activeIcon: Icons.school,
                        label: 'Học & Luyện',
                      ),
                      GlassBottomNavItem(
                        icon: Icons.auto_awesome_outlined,
                        activeIcon: Icons.auto_awesome,
                        label: 'AI',
                        prominent: true,
                      ),
                      GlassBottomNavItem(
                        icon: Icons.emoji_events_outlined,
                        activeIcon: Icons.emoji_events,
                        label: 'Thành Tích',
                      ),
                      GlassBottomNavItem(
                        icon: Icons.person_outlined,
                        activeIcon: Icons.person,
                        label: 'Hồ Sơ',
                      ),
                    ],
                  ),
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }

  int _calculateSelectedIndex(BuildContext context) {
    final location = GoRouterState.of(context).matchedLocation;
    if (location.startsWith(RoutePaths.explore)) return 0;
    if (location.startsWith(RoutePaths.learnPractice) ||
        location.startsWith(RoutePaths.learningPath) ||
        location.startsWith(RoutePaths.practice)) {
      return 1;
    }
    if (location.startsWith(RoutePaths.aiHub)) return 2;
    if (location.startsWith(RoutePaths.achievements)) return 3;
    if (location.startsWith(RoutePaths.profile)) return 4;
    return 0;
  }

  void _onItemTapped(int index, BuildContext context) {
    switch (index) {
      case 0:
        context.go(RoutePaths.explore);
        break;
      case 1:
        context.go(RoutePaths.learnPractice);
        break;
      case 2:
        context.go(RoutePaths.aiHub);
        break;
      case 3:
        context.go(RoutePaths.achievements);
        break;
      case 4:
        context.go(RoutePaths.profile);
        break;
    }
  }
}

// =============================================================================
// ERROR SCREEN
// =============================================================================

class ErrorScreen extends StatelessWidget {
  final Exception? error;

  const ErrorScreen({super.key, this.error});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Lỗi')),
      body: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Icon(Icons.error_outline, size: 64, color: Colors.red),
            const SizedBox(height: 16),
            const Text(
              'Không tìm thấy trang',
              style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 8),
            if (error != null)
              Text(
                error.toString(),
                textAlign: TextAlign.center,
                style: const TextStyle(color: Colors.grey),
              ),
            const SizedBox(height: 24),
            ElevatedButton(
              onPressed: () => context.go(RoutePaths.explore),
              child: const Text('Về trang chủ'),
            ),
          ],
        ),
      ),
    );
  }
}
