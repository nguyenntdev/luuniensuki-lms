# 11_Phase2_Core_Screens.md — Core Screens & Navigation

## Overview

Phase 2 implements the main app shell with bottom navigation and core screens: Home, Explore, Collection, Achievements, and Profile.

**Duration:** 2 weeks  
**Priority:** P0 (Critical Path)  
**Prerequisites:** Phase 1 (Auth) completed

---

## Week 1: Navigation Shell & Home Screen

### Task 2.1: Implement GoRouter Configuration

**Estimated Time:** 3 hours

**File: `lib/routing/route_names.dart`**

```dart
class RouteNames {
  // Main tabs
  static const home = 'home';
  static const explore = 'explore';
  static const collection = 'collection';
  static const achievements = 'achievements';
  static const profile = 'profile';
  
  // Auth routes
  static const login = 'login';
  static const register = 'register';
  
  // Detail routes
  static const urnViewer = 'urn-viewer';
  static const motifDetail = 'motif-detail';
  static const motifQuiz = 'motif-quiz';
  static const questDetail = 'quest-detail';
  
  // Other routes
  static const leaderboard = 'leaderboard';
  static const certificateVerify = 'certificate-verify';
  static const userPublicProfile = 'user-public-profile';
}
```

**File: `lib/routing/app_router.dart`**

```dart
import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:riverpod_annotation/riverpod_annotation.dart';

part 'app_router.g.dart';

@riverpod
GoRouter appRouter(AppRouterRef ref) {
  final authState = ref.watch(authNotifierProvider);
  
  return GoRouter(
    initialLocation: '/',
    debugLogDiagnostics: true,
    redirect: (context, state) {
      final isLoggedIn = authState.isAuthenticated;
      final isAuthRoute = state.matchedLocation.startsWith('/auth');
      
      // Redirect to login if not authenticated
      if (!isLoggedIn && !isAuthRoute) {
        return '/auth/login?returnUrl=${Uri.encodeComponent(state.matchedLocation)}';
      }
      
      // Redirect to home if already authenticated
      if (isLoggedIn && isAuthRoute) {
        final returnUrl = state.uri.queryParameters['returnUrl'];
        return returnUrl ?? '/';
      }
      
      return null;
    },
    routes: [
      // Auth routes (no shell)
      GoRoute(
        path: '/auth/login',
        name: RouteNames.login,
        builder: (context, state) => const LoginScreen(),
      ),
      GoRoute(
        path: '/auth/register',
        name: RouteNames.register,
        builder: (context, state) => const RegisterScreen(),
      ),
      
      // Main shell with bottom navigation
      ShellRoute(
        builder: (context, state, child) => MainShell(child: child),
        routes: [
          GoRoute(
            path: '/',
            name: RouteNames.home,
            pageBuilder: (context, state) => NoTransitionPage(
              child: const HomeScreen(),
            ),
          ),
          GoRoute(
            path: '/explore',
            name: RouteNames.explore,
            pageBuilder: (context, state) => NoTransitionPage(
              child: const ExploreScreen(),
            ),
          ),
          GoRoute(
            path: '/collection',
            name: RouteNames.collection,
            pageBuilder: (context, state) => NoTransitionPage(
              child: const CollectionScreen(),
            ),
          ),
          GoRoute(
            path: '/achievements',
            name: RouteNames.achievements,
            pageBuilder: (context, state) => NoTransitionPage(
              child: const AchievementsScreen(),
            ),
          ),
          GoRoute(
            path: '/profile',
            name: RouteNames.profile,
            pageBuilder: (context, state) => NoTransitionPage(
              child: const ProfileScreen(),
            ),
          ),
        ],
      ),
      
      // Detail routes (full screen, no shell)
      GoRoute(
        path: '/urns/:urnSlug',
        name: RouteNames.urnViewer,
        builder: (context, state) => UrnViewerScreen(
          urnSlug: state.pathParameters['urnSlug']!,
        ),
      ),
      GoRoute(
        path: '/motif/:motifId',
        name: RouteNames.motifDetail,
        builder: (context, state) => MotifDetailScreen(
          motifId: state.pathParameters['motifId']!,
        ),
        routes: [
          GoRoute(
            path: 'quiz',
            name: RouteNames.motifQuiz,
            builder: (context, state) => QuizScreen(
              motifId: state.pathParameters['motifId']!,
            ),
          ),
        ],
      ),
      GoRoute(
        path: '/quests/:questSlug',
        name: RouteNames.questDetail,
        builder: (context, state) => QuestDetailScreen(
          questSlug: state.pathParameters['questSlug']!,
        ),
      ),
      GoRoute(
        path: '/leaderboard',
        name: RouteNames.leaderboard,
        builder: (context, state) => const LeaderboardScreen(),
      ),
    ],
    errorBuilder: (context, state) => ErrorScreen(error: state.error),
  );
}
```

**Acceptance Criteria:**
- [ ] Router configured with all routes
- [ ] Auth redirect works correctly
- [ ] Deep linking supported
- [ ] No transition animation for tab switches

---

### Task 2.2: Implement Main Shell with Bottom Navigation

**Estimated Time:** 3 hours

**File: `lib/shared/widgets/main_shell.dart`**

```dart
import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

class MainShell extends StatelessWidget {
  final Widget child;
  
  const MainShell({super.key, required this.child});
  
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: child,
      bottomNavigationBar: const MainBottomNavBar(),
    );
  }
}

class MainBottomNavBar extends StatelessWidget {
  const MainBottomNavBar({super.key});
  
  static const _tabs = [
    _TabItem(
      path: '/',
      label: 'Khám Phá',
      labelEn: 'Explore',
      icon: Icons.explore_outlined,
      activeIcon: Icons.explore,
    ),
    _TabItem(
      path: '/explore',
      label: 'Đỉnh',
      labelEn: 'Urns',
      icon: Icons.view_in_ar_outlined,
      activeIcon: Icons.view_in_ar,
    ),
    _TabItem(
      path: '/collection',
      label: 'Bộ Sưu Tập',
      labelEn: 'Collection',
      icon: Icons.collections_outlined,
      activeIcon: Icons.collections,
    ),
    _TabItem(
      path: '/achievements',
      label: 'Thành Tích',
      labelEn: 'Achievements',
      icon: Icons.emoji_events_outlined,
      activeIcon: Icons.emoji_events,
    ),
    _TabItem(
      path: '/profile',
      label: 'Hồ Sơ',
      labelEn: 'Profile',
      icon: Icons.person_outline,
      activeIcon: Icons.person,
    ),
  ];
  
  int _getCurrentIndex(BuildContext context) {
    final location = GoRouterState.of(context).matchedLocation;
    for (int i = 0; i < _tabs.length; i++) {
      if (location == _tabs[i].path) return i;
    }
    return 0;
  }
  
  @override
  Widget build(BuildContext context) {
    final currentIndex = _getCurrentIndex(context);
    
    return Container(
      decoration: BoxDecoration(
        color: Theme.of(context).colorScheme.surface,
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.1),
            blurRadius: 8,
            offset: const Offset(0, -2),
          ),
        ],
      ),
      child: SafeArea(
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 8),
          child: Row(
            mainAxisAlignment: MainAxisAlignment.spaceAround,
            children: List.generate(_tabs.length, (index) {
              final tab = _tabs[index];
              final isSelected = index == currentIndex;
              
              return _NavBarItem(
                tab: tab,
                isSelected: isSelected,
                onTap: () => context.go(tab.path),
              );
            }),
          ),
        ),
      ),
    );
  }
}

class _TabItem {
  final String path;
  final String label;
  final String labelEn;
  final IconData icon;
  final IconData activeIcon;
  
  const _TabItem({
    required this.path,
    required this.label,
    required this.labelEn,
    required this.icon,
    required this.activeIcon,
  });
}

class _NavBarItem extends StatelessWidget {
  final _TabItem tab;
  final bool isSelected;
  final VoidCallback onTap;
  
  const _NavBarItem({
    required this.tab,
    required this.isSelected,
    required this.onTap,
  });
  
  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final color = isSelected
        ? theme.colorScheme.primary
        : theme.colorScheme.onSurface.withOpacity(0.6);
    
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(12),
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(
              isSelected ? tab.activeIcon : tab.icon,
              color: color,
              size: 24,
            ),
            const SizedBox(height: 4),
            Text(
              tab.label,
              style: theme.textTheme.labelSmall?.copyWith(
                color: color,
                fontWeight: isSelected ? FontWeight.w600 : FontWeight.normal,
              ),
            ),
          ],
        ),
      ),
    );
  }
}
```

**Acceptance Criteria:**
- [ ] Bottom navigation with 5 tabs
- [ ] Current tab highlighted
- [ ] Vietnamese labels displayed
- [ ] Smooth transitions between tabs

---

### Task 2.3: Implement Home Screen

**Estimated Time:** 4 hours

**File: `lib/features/home/presentation/screens/home_screen.dart`**

```dart
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

class HomeScreen extends ConsumerWidget {
  const HomeScreen({super.key});
  
  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final dashboardAsync = ref.watch(dashboardProvider);
    
    return Scaffold(
      body: SafeArea(
        child: dashboardAsync.when(
          loading: () => const HomeScreenSkeleton(),
          error: (error, stack) => ErrorWidget(
            message: error.toString(),
            onRetry: () => ref.invalidate(dashboardProvider),
          ),
          data: (dashboard) => RefreshIndicator(
            onRefresh: () async => ref.invalidate(dashboardProvider),
            child: CustomScrollView(
              slivers: [
                // Welcome header
                SliverToBoxAdapter(
                  child: HomeHeader(user: dashboard.user),
                ),
                
                // Stats cards
                SliverToBoxAdapter(
                  child: StatsSection(stats: dashboard.stats),
                ),
                
                // Continue learning section
                if (dashboard.inProgressMotifs.isNotEmpty)
                  SliverToBoxAdapter(
                    child: ContinueLearningSection(
                      motifs: dashboard.inProgressMotifs,
                    ),
                  ),
                
                // Active quests
                if (dashboard.activeQuests.isNotEmpty)
                  SliverToBoxAdapter(
                    child: ActiveQuestsSection(
                      quests: dashboard.activeQuests,
                    ),
                  ),
                
                // Quick explore urns
                SliverToBoxAdapter(
                  child: QuickExploreSection(urns: dashboard.urns),
                ),
                
                // Recent achievements
                if (dashboard.recentBadges.isNotEmpty)
                  SliverToBoxAdapter(
                    child: RecentAchievementsSection(
                      badges: dashboard.recentBadges,
                    ),
                  ),
                
                // Bottom padding
                const SliverPadding(padding: EdgeInsets.only(bottom: 24)),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
```

**Home Screen Sections:**

1. **HomeHeader** - Welcome message, user name, streak indicator
2. **StatsSection** - XP progress, rank, daily goal
3. **ContinueLearningSection** - Motifs in progress (horizontal scroll)
4. **ActiveQuestsSection** - Current quests with progress
5. **QuickExploreSection** - Urn cards to start exploring
6. **RecentAchievementsSection** - Recently earned badges

**Acceptance Criteria:**
- [ ] Dashboard data loaded from API
- [ ] Pull-to-refresh implemented
- [ ] Loading skeleton shown
- [ ] Error state with retry
- [ ] All sections render correctly

---

### Task 2.4: Implement Dashboard Provider

**Estimated Time:** 2 hours

**File: `lib/features/home/presentation/providers/dashboard_provider.dart`**

```dart
import 'package:riverpod_annotation/riverpod_annotation.dart';
import '../../domain/entities/dashboard.dart';

part 'dashboard_provider.g.dart';

@riverpod
Future<Dashboard> dashboard(DashboardRef ref) async {
  final repository = ref.watch(userRepositoryProvider);
  final result = await repository.getDashboard();
  
  return result.fold(
    (failure) => throw failure,
    (dashboard) => dashboard,
  );
}

// Dashboard entity
class Dashboard {
  final User user;
  final UserStats stats;
  final List<Urn> urns;
  final List<MotifProgress> inProgressMotifs;
  final List<Quest> activeQuests;
  final List<Badge> recentBadges;
  
  const Dashboard({
    required this.user,
    required this.stats,
    required this.urns,
    required this.inProgressMotifs,
    required this.activeQuests,
    required this.recentBadges,
  });
}
```

**Acceptance Criteria:**
- [ ] Dashboard data fetched from API
- [ ] Data cached for offline access
- [ ] Auto-refresh on pull

---

## Week 2: Explore, Collection, Achievements, Profile Screens

### Task 2.5: Implement Explore Screen (Urn List)

**Estimated Time:** 4 hours

**File: `lib/features/explore/presentation/screens/explore_screen.dart`**

```dart
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

class ExploreScreen extends ConsumerWidget {
  const ExploreScreen({super.key});
  
  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final urnsAsync = ref.watch(urnsProvider);
    
    return Scaffold(
      appBar: AppBar(
        title: const Text('Cửu Đỉnh'),
        actions: [
          IconButton(
            icon: const Icon(Icons.search),
            onPressed: () => _showSearch(context),
          ),
        ],
      ),
      body: urnsAsync.when(
        loading: () => const UrnGridSkeleton(),
        error: (error, stack) => ErrorWidget(
          message: error.toString(),
          onRetry: () => ref.invalidate(urnsProvider),
        ),
        data: (urns) => RefreshIndicator(
          onRefresh: () async => ref.invalidate(urnsProvider),
          child: GridView.builder(
            padding: const EdgeInsets.all(16),
            gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
              crossAxisCount: 2,
              mainAxisSpacing: 16,
              crossAxisSpacing: 16,
              childAspectRatio: 0.8,
            ),
            itemCount: urns.length,
            itemBuilder: (context, index) => UrnCard(
              urn: urns[index],
              onTap: () => context.goNamed(
                RouteNames.urnViewer,
                pathParameters: {'urnSlug': urns[index].slug},
              ),
            ),
          ),
        ),
      ),
    );
  }
}
```

**File: `lib/features/explore/presentation/widgets/urn_card.dart`**

```dart
class UrnCard extends StatelessWidget {
  final Urn urn;
  final VoidCallback onTap;
  
  const UrnCard({
    super.key,
    required this.urn,
    required this.onTap,
  });
  
  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final progress = urn.discoveredCount / urn.motifCount;
    
    return Card(
      clipBehavior: Clip.antiAlias,
      child: InkWell(
        onTap: onTap,
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            // Thumbnail
            Expanded(
              flex: 3,
              child: CachedNetworkImage(
                imageUrl: urn.thumbnailUrl ?? '',
                fit: BoxFit.cover,
                placeholder: (_, __) => const ShimmerBox(),
                errorWidget: (_, __, ___) => Container(
                  color: theme.colorScheme.surfaceVariant,
                  child: const Icon(Icons.view_in_ar, size: 48),
                ),
              ),
            ),
            
            // Info
            Expanded(
              flex: 2,
              child: Padding(
                padding: const EdgeInsets.all(12),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      urn.name,
                      style: theme.textTheme.titleMedium?.copyWith(
                        fontWeight: FontWeight.bold,
                      ),
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                    ),
                    const SizedBox(height: 4),
                    Text(
                      '${urn.discoveredCount}/${urn.motifCount} họa tiết',
                      style: theme.textTheme.bodySmall?.copyWith(
                        color: theme.colorScheme.onSurface.withOpacity(0.6),
                      ),
                    ),
                    const Spacer(),
                    // Progress bar
                    ClipRRect(
                      borderRadius: BorderRadius.circular(4),
                      child: LinearProgressIndicator(
                        value: progress,
                        minHeight: 4,
                        backgroundColor: theme.colorScheme.surfaceVariant,
                      ),
                    ),
                  ],
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
```

**Acceptance Criteria:**
- [ ] 3x3 grid of urn cards
- [ ] Thumbnail images loaded
- [ ] Progress indicator per urn
- [ ] Navigation to 3D viewer on tap

---

### Task 2.6: Implement Collection Screen

**Estimated Time:** 4 hours

**File: `lib/features/collection/presentation/screens/collection_screen.dart`**

```dart
class CollectionScreen extends ConsumerStatefulWidget {
  const CollectionScreen({super.key});
  
  @override
  ConsumerState<CollectionScreen> createState() => _CollectionScreenState();
}

class _CollectionScreenState extends ConsumerState<CollectionScreen>
    with SingleTickerProviderStateMixin {
  late TabController _tabController;
  
  final _filters = [
    CollectionFilter.all,
    CollectionFilter.discovered,
    CollectionFilter.learned,
    CollectionFilter.mastered,
  ];
  
  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: _filters.length, vsync: this);
  }
  
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Bộ Sưu Tập'),
        bottom: TabBar(
          controller: _tabController,
          tabs: _filters.map((f) => Tab(text: f.label)).toList(),
        ),
      ),
      body: TabBarView(
        controller: _tabController,
        children: _filters.map((filter) {
          return CollectionGrid(filter: filter);
        }).toList(),
      ),
    );
  }
}

class CollectionGrid extends ConsumerWidget {
  final CollectionFilter filter;
  
  const CollectionGrid({super.key, required this.filter});
  
  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final collectionAsync = ref.watch(collectionProvider(filter));
    
    return collectionAsync.when(
      loading: () => const MotifGridSkeleton(),
      error: (e, s) => ErrorWidget(message: e.toString()),
      data: (motifs) {
        if (motifs.isEmpty) {
          return EmptyState(
            icon: Icons.collections_outlined,
            title: 'Chưa có họa tiết',
            message: 'Khám phá Cửu Đỉnh để thu thập họa tiết!',
            actionLabel: 'Khám phá ngay',
            onAction: () => context.go('/explore'),
          );
        }
        
        return GridView.builder(
          padding: const EdgeInsets.all(16),
          gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
            crossAxisCount: 3,
            mainAxisSpacing: 12,
            crossAxisSpacing: 12,
          ),
          itemCount: motifs.length,
          itemBuilder: (context, index) => MotifCollectionCard(
            motif: motifs[index],
          ),
        );
      },
    );
  }
}
```

**Acceptance Criteria:**
- [ ] Tab filters (All, Discovered, Learned, Mastered)
- [ ] Grid of collected motifs
- [ ] Empty state when no motifs
- [ ] Tap to view motif detail

---

### Task 2.7: Implement Achievements Screen

**Estimated Time:** 4 hours

**File: `lib/features/gamification/presentation/screens/achievements_screen.dart`**

```dart
class AchievementsScreen extends ConsumerStatefulWidget {
  const AchievementsScreen({super.key});
  
  @override
  ConsumerState<AchievementsScreen> createState() => _AchievementsScreenState();
}

class _AchievementsScreenState extends ConsumerState<AchievementsScreen>
    with SingleTickerProviderStateMixin {
  late TabController _tabController;
  
  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 3, vsync: this);
  }
  
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Thành Tích'),
        bottom: TabBar(
          controller: _tabController,
          tabs: const [
            Tab(text: 'Huy Hiệu'),
            Tab(text: 'Nhiệm Vụ'),
            Tab(text: 'Bảng Xếp Hạng'),
          ],
        ),
      ),
      body: TabBarView(
        controller: _tabController,
        children: const [
          BadgesTab(),
          QuestsTab(),
          LeaderboardTab(),
        ],
      ),
    );
  }
}
```

**Sub-components:**

1. **BadgesTab** - Grid of all badges (earned/unearned)
2. **QuestsTab** - List of quests with progress
3. **LeaderboardTab** - Top users by XP

**Acceptance Criteria:**
- [ ] 3 tabs working
- [ ] Badges show earned status
- [ ] Quests show progress
- [ ] Leaderboard with user ranking

---

### Task 2.8: Implement Profile Screen

**Estimated Time:** 4 hours

**File: `lib/features/profile/presentation/screens/profile_screen.dart`**

```dart
class ProfileScreen extends ConsumerWidget {
  const ProfileScreen({super.key});
  
  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final authState = ref.watch(authNotifierProvider);
    final user = authState.user;
    
    if (user == null) {
      return const Center(child: CircularProgressIndicator());
    }
    
    return Scaffold(
      appBar: AppBar(
        title: const Text('Hồ Sơ'),
        actions: [
          IconButton(
            icon: const Icon(Icons.settings_outlined),
            onPressed: () => _showSettings(context),
          ),
        ],
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Column(
          children: [
            // Avatar and name
            ProfileHeader(user: user),
            
            const SizedBox(height: 24),
            
            // XP and rank
            XpRankCard(
              totalXp: user.totalXp,
              rank: user.rank,
              xpToNext: user.xpToNextRank,
            ),
            
            const SizedBox(height: 16),
            
            // Stats grid
            StatsGrid(userId: user.id),
            
            const SizedBox(height: 16),
            
            // Streak card
            StreakCard(userId: user.id),
            
            const SizedBox(height: 24),
            
            // Action buttons
            ProfileActions(
              onEditProfile: () => _editProfile(context),
              onViewPublicProfile: () => context.goNamed(
                RouteNames.userPublicProfile,
                pathParameters: {'userId': user.id},
              ),
              onLogout: () => _confirmLogout(context, ref),
            ),
          ],
        ),
      ),
    );
  }
  
  void _confirmLogout(BuildContext context, WidgetRef ref) {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Đăng xuất'),
        content: const Text('Bạn có chắc muốn đăng xuất?'),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('Hủy'),
          ),
          TextButton(
            onPressed: () {
              ref.read(authNotifierProvider.notifier).logout();
              Navigator.pop(context);
            },
            child: const Text('Đăng xuất'),
          ),
        ],
      ),
    );
  }
}
```

**Acceptance Criteria:**
- [ ] User info displayed
- [ ] XP progress bar
- [ ] Stats grid (discoveries, lessons, quizzes)
- [ ] Streak display
- [ ] Logout functionality

---

## Shared Widgets

### Task 2.9: Implement Common Widgets

**Estimated Time:** 4 hours

**Widgets to implement:**

1. **LoadingSkeleton** - Shimmer loading placeholders
2. **ErrorWidget** - Error state with retry button
3. **EmptyState** - Empty state with icon, message, action
4. **XpBadge** - Small XP amount display
5. **ProgressBar** - Customized progress indicator
6. **CachedImage** - Image with loading/error states
7. **StreakBadge** - Streak count display
8. **RankBadge** - User rank display

**File: `lib/shared/widgets/loading_skeleton.dart`**

```dart
class ShimmerBox extends StatelessWidget {
  final double? width;
  final double? height;
  final BorderRadius? borderRadius;
  
  const ShimmerBox({
    super.key,
    this.width,
    this.height,
    this.borderRadius,
  });
  
  @override
  Widget build(BuildContext context) {
    return Shimmer.fromColors(
      baseColor: Colors.grey[300]!,
      highlightColor: Colors.grey[100]!,
      child: Container(
        width: width,
        height: height,
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: borderRadius ?? BorderRadius.circular(8),
        ),
      ),
    );
  }
}
```

**File: `lib/shared/widgets/empty_state.dart`**

```dart
class EmptyState extends StatelessWidget {
  final IconData icon;
  final String title;
  final String message;
  final String? actionLabel;
  final VoidCallback? onAction;
  
  const EmptyState({
    super.key,
    required this.icon,
    required this.title,
    required this.message,
    this.actionLabel,
    this.onAction,
  });
  
  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(32),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(
              icon,
              size: 64,
              color: theme.colorScheme.onSurface.withOpacity(0.3),
            ),
            const SizedBox(height: 16),
            Text(
              title,
              style: theme.textTheme.titleLarge,
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 8),
            Text(
              message,
              style: theme.textTheme.bodyMedium?.copyWith(
                color: theme.colorScheme.onSurface.withOpacity(0.6),
              ),
              textAlign: TextAlign.center,
            ),
            if (actionLabel != null && onAction != null) ...[
              const SizedBox(height: 24),
              ElevatedButton(
                onPressed: onAction,
                child: Text(actionLabel!),
              ),
            ],
          ],
        ),
      ),
    );
  }
}
```

**Acceptance Criteria:**
- [ ] All common widgets implemented
- [ ] Consistent styling across app
- [ ] Reusable components

---

## Phase 2 Checklist

### Backend Integration
- [ ] P2-B1: Implement urns provider with API call
- [ ] P2-B2: Implement collection provider with filters
- [ ] P2-B3: Implement badges provider
- [ ] P2-B4: Implement quests provider
- [ ]