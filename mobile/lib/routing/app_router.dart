import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:riverpod_annotation/riverpod_annotation.dart';

import '../features/auth/presentation/providers/auth_provider.dart';
import '../features/auth/presentation/screens/login_screen.dart';
import '../features/auth/presentation/screens/register_screen.dart';
import '../features/explore/presentation/screens/explore_screen.dart';
import '../features/collection/presentation/screens/collection_screen.dart';
import '../features/achievements/presentation/screens/achievements_screen.dart';
import '../features/profile/presentation/screens/profile_screen.dart';
import '../features/urn_viewer/presentation/screens/urn_viewer_screen.dart';
import '../features/lesson/presentation/screens/motif_detail_screen.dart';
import '../features/quiz/presentation/screens/quiz_screen.dart';
import '../shared/widgets/glass/animated_background.dart';
import '../shared/widgets/glass/glass_bottom_nav.dart';

part 'app_router.g.dart';

// Route path constants
class _Paths {
  static const String login = '/login';
  static const String register = '/register';
  static const String explore = '/explore';
  static const String collection = '/collection';
  static const String achievements = '/achievements';
  static const String profile = '/profile';
  static const String urns = '/urns';
  static const String motifs = '/motifs';
  static const String quests = '/quests';
  static const String settings = '/settings';
}

/// Provides the GoRouter instance configured with all app routes.
/// Handles authentication-based redirects and navigation.
/// Using keepAlive to maintain router instance and prevent unnecessary rebuilds
@Riverpod(keepAlive: true)
GoRouter appRouter(AppRouterRef ref) {
  // Watch auth state to rebuild router only when auth changes
  final authNotifier = ref.read(authNotifierProvider.notifier);

  return GoRouter(
    initialLocation: _Paths.explore,
    debugLogDiagnostics: true,

    // Redirect logic based on auth state
    redirect: (context, state) {
      // Use ref.read here - only called during navigation, not on every auth change
      final authState = ref.read(authNotifierProvider);

      final isLoggedIn = authState.maybeMap(
        authenticated: (_) => true,
        orElse: () => false,
      );
      final isLoggingIn = state.matchedLocation == _Paths.login;
      final isRegistering = state.matchedLocation == _Paths.register;
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

      // Not logged in and not on auth route -> redirect to login
      if (!isLoggedIn && !isAuthRoute) {
        final returnUrl = Uri.encodeComponent(state.matchedLocation);
        return '${_Paths.login}?returnUrl=$returnUrl';
      }

      // Logged in and on auth route -> redirect to explore
      if (isLoggedIn && isAuthRoute) {
        final returnUrl = state.uri.queryParameters['returnUrl'];
        if (returnUrl != null && returnUrl.isNotEmpty) {
          return Uri.decodeComponent(returnUrl);
        }
        return _Paths.explore;
      }

      // Allow navigation if logged in
      return null;
    },

    routes: [
      // =======================================================================
      // AUTH ROUTES
      // =======================================================================
      GoRoute(
        path: _Paths.login,
        name: 'login',
        builder: (context, state) => const LoginScreen(),
      ),
      GoRoute(
        path: _Paths.register,
        name: 'register',
        builder: (context, state) => const RegisterScreen(),
      ),

      // =======================================================================
      // MAIN SHELL WITH BOTTOM NAVIGATION
      // =======================================================================
      ShellRoute(
        builder: (context, state, child) {
          return MainShell(child: child);
        },
        routes: [
          // Explore (Home) - Urn grid
          GoRoute(
            path: _Paths.explore,
            name: 'explore',
            pageBuilder: (context, state) => const NoTransitionPage(
              child: ExploreScreen(),
            ),
          ),

          // Collection - User's discovered motifs
          GoRoute(
            path: _Paths.collection,
            name: 'collection',
            pageBuilder: (context, state) => const NoTransitionPage(
              child: CollectionScreen(),
            ),
          ),

          // Achievements - Badges and leaderboard
          GoRoute(
            path: _Paths.achievements,
            name: 'achievements',
            pageBuilder: (context, state) => const NoTransitionPage(
              child: AchievementsScreen(),
            ),
          ),

          // Profile - User profile and settings
          GoRoute(
            path: _Paths.profile,
            name: 'profile',
            pageBuilder: (context, state) => const NoTransitionPage(
              child: ProfileScreen(),
            ),
          ),
        ],
      ),

      // =======================================================================
      // URN & MOTIF ROUTES (Full screen, outside shell)
      // =======================================================================
      GoRoute(
        path: '${_Paths.urns}/:urnSlug',
        name: 'urn',
        builder: (context, state) {
          final urnSlug = state.pathParameters['urnSlug'] ?? '';
          return UrnViewerScreen(urnSlug: urnSlug);
        },
      ),

      GoRoute(
        path: '${_Paths.motifs}/:motifId',
        name: 'motif',
        builder: (context, state) {
          final motifId = state.pathParameters['motifId'] ?? '';
          return MotifDetailScreen(motifId: motifId);
        },
        routes: [
          // Lesson route under motif (same as motif detail, different tab)
          GoRoute(
            path: 'lesson',
            name: 'motifLesson',
            builder: (context, state) {
              final motifId = state.pathParameters['motifId'] ?? '';
              return MotifDetailScreen(motifId: motifId);
            },
          ),
          // Quiz route under motif
          GoRoute(
            path: 'quiz',
            name: 'motifQuiz',
            builder: (context, state) {
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
        path: _Paths.quests,
        name: 'quests',
        builder: (context, state) => const QuestsPlaceholder(),
      ),
      GoRoute(
        path: '${_Paths.quests}/:questId',
        name: 'quest',
        builder: (context, state) {
          final questId = state.pathParameters['questId'] ?? '';
          return QuestDetailPlaceholder(questId: questId);
        },
      ),

      // =======================================================================
      // SETTINGS ROUTES
      // =======================================================================
      GoRoute(
        path: _Paths.settings,
        name: 'settings',
        builder: (context, state) => const SettingsPlaceholder(),
      ),
    ],

    // Error page
    errorBuilder: (context, state) => ErrorScreen(error: state.error),
  );
}



// =============================================================================
// MAIN SHELL WITH BOTTOM NAVIGATION
// =============================================================================

class MainShell extends StatelessWidget {
  final Widget child;

  const MainShell({super.key, required this.child});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Stack(
        children: [
          // Content
          child,

          // Glass Bottom Navigation
          Positioned(
            left: 0,
            right: 0,
            bottom: 0,
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
                  icon: Icons.collections_outlined,
                  activeIcon: Icons.collections,
                  label: 'Bộ Sưu Tập',
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
        ],
      ),
    );
  }

  int _calculateSelectedIndex(BuildContext context) {
    final location = GoRouterState.of(context).matchedLocation;
    if (location.startsWith(_Paths.explore)) return 0;
    if (location.startsWith(_Paths.collection)) return 1;
    if (location.startsWith(_Paths.achievements)) return 2;
    if (location.startsWith(_Paths.profile)) return 3;
    return 0;
  }

  void _onItemTapped(int index, BuildContext context) {
    switch (index) {
      case 0:
        context.go(_Paths.explore);
        break;
      case 1:
        context.go(_Paths.collection);
        break;
      case 2:
        context.go(_Paths.achievements);
        break;
      case 3:
        context.go(_Paths.profile);
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
              onPressed: () => context.go(_Paths.explore),
              child: const Text('Về trang chủ'),
            ),
          ],
        ),
      ),
    );
  }
}
