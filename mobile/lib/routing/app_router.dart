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
import '../features/history/presentation/history_atlas_screen.dart';import '../features/notifications/presentation/screens/notifications_screen.dart';
import '../features/daily_goals/presentation/screens/daily_goal_screen.dart';
import '../features/gems/presentation/screens/gems_shop_screen.dart';
import '../features/hearts/presentation/screens/hearts_refill_screen.dart';
import '../features/social/presentation/screens/friends_screen.dart';
import '../features/onboarding/presentation/screens/onboarding_screen.dart';
import '../features/streak/services/streak_event_service.dart';
import 'route_names.dart';
import '../shared/widgets/glass/glass_bottom_nav.dart';
import '../shared/widgets/glass/glass_nav_metrics.dart';

part 'app_router.g.dart';

/// Provides the GoRouter instance configured with all app routes.
/// Handles authentication-based redirects and navigation.
/// Using keepAlive to maintain router instance and prevent unnecessary rebuilds
@Riverpod(keepAlive: true)
GoRouter appRouter(Ref ref) {
  final storage = ref.read(hiveStorageProvider);

  return GoRouter(
    initialLocation: RoutePaths.explore,
    debugLogDiagnostics: true,

    // Redirect logic based on auth state and onboarding
    redirect: (_, state) {
      // Use ref.read here - only called during navigation, not on every auth change
      final authState = ref.read(authNotifierProvider);

      final isLoggedIn = authState.maybeMap(
        authenticated: (_) => true,
        orElse: () => false,
      );

      final isOnboarding = state.matchedLocation == RoutePaths.onboarding;
      final isLoggingIn = state.matchedLocation == RoutePaths.login;
      final isRegistering = state.matchedLocation == RoutePaths.register;
      final isAuthRoute = isLoggingIn || isRegistering;

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

      // Not logged in and not on auth route -> redirect to login
      if (!isLoggedIn && !isAuthRoute && !isOnboarding) {
        final returnUrl = Uri.encodeComponent(state.matchedLocation);
        return '${RoutePaths.login}?returnUrl=$returnUrl';
      }

      // Logged in and on auth route -> redirect to explore
      if (isLoggedIn && isAuthRoute) {
        final returnUrl = state.uri.queryParameters['returnUrl'];
        if (returnUrl != null && returnUrl.isNotEmpty) {
          return Uri.decodeComponent(returnUrl);
        }
        return RoutePaths.explore;
      }

      // Allow navigation if logged in
      return null;
    },

    routes: [
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
      // QUEST ROUTES
      // =======================================================================
      GoRoute(
        path: RoutePaths.quests,
        name: 'quests',
        builder: (_, __) => const QuestsPlaceholder(),
      ),
      GoRoute(
        path: '${RoutePaths.quests}/:questId',
        name: 'quest',
        builder: (_, state) {
          final questId = state.pathParameters['questId'] ?? '';
          return QuestDetailPlaceholder(questId: questId);
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
// PLACEHOLDER SCREENS (To be replaced with actual implementations)
// =============================================================================

class ExplorePlaceholder extends StatelessWidget {
  const ExplorePlaceholder({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Khám Phá')),
      body: const Center(child: Text('Explore Screen - Coming Soon')),
    );
  }
}

class CollectionPlaceholder extends StatelessWidget {
  const CollectionPlaceholder({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Bộ Sưu Tập')),
      body: const Center(child: Text('Collection Screen - Coming Soon')),
    );
  }
}

class AchievementsPlaceholder extends StatelessWidget {
  const AchievementsPlaceholder({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Thành Tích')),
      body: const Center(child: Text('Achievements Screen - Coming Soon')),
    );
  }
}

class ProfilePlaceholder extends StatelessWidget {
  const ProfilePlaceholder({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Hồ Sơ')),
      body: const Center(child: Text('Profile Screen - Coming Soon')),
    );
  }
}

class UrnViewerPlaceholder extends StatelessWidget {
  final String urnSlug;

  const UrnViewerPlaceholder({super.key, required this.urnSlug});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text('Urn: $urnSlug')),
      body: Center(child: Text('3D Urn Viewer for $urnSlug - Coming Soon')),
    );
  }
}

class MotifDetailPlaceholder extends StatelessWidget {
  final String motifId;

  const MotifDetailPlaceholder({super.key, required this.motifId});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text('Motif: $motifId')),
      body: Center(child: Text('Motif Detail for $motifId - Coming Soon')),
    );
  }
}

class LessonPlaceholder extends StatelessWidget {
  final String motifId;

  const LessonPlaceholder({super.key, required this.motifId});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text('Bài Học: $motifId')),
      body: Center(child: Text('Lesson for $motifId - Coming Soon')),
    );
  }
}

class QuizPlaceholder extends StatelessWidget {
  final String motifId;

  const QuizPlaceholder({super.key, required this.motifId});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text('Trắc Nghiệm: $motifId')),
      body: Center(child: Text('Quiz for $motifId - Coming Soon')),
    );
  }
}

class QuestsPlaceholder extends StatelessWidget {
  const QuestsPlaceholder({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Nhiệm Vụ')),
      body: const Center(child: Text('Quests Screen - Coming Soon')),
    );
  }
}

class QuestDetailPlaceholder extends StatelessWidget {
  final String questId;

  const QuestDetailPlaceholder({super.key, required this.questId});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text('Quest: $questId')),
      body: Center(child: Text('Quest Detail for $questId - Coming Soon')),
    );
  }
}

class SettingsPlaceholder extends StatelessWidget {
  const SettingsPlaceholder({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Cài Đặt')),
      body: const Center(child: Text('Settings Screen - Coming Soon')),
    );
  }
}

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
