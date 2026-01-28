import 'dart:math' as math;

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../../core/theme/app_colors.dart';
import '../../../../shared/widgets/effects/shimmer_widget.dart';
import '../../../../shared/widgets/glass/glass_container.dart';
import '../../../../shared/widgets/glass/pressable_glass_card.dart';
import '../../../../shared/widgets/text/gradient_text.dart';
import '../../../auth/presentation/providers/auth_provider.dart';
import '../../../streak/presentation/widgets/streak_badge.dart';
import '../../utils/badge_category_utils.dart';
import '../providers/badge_provider.dart';
import '../providers/leaderboard_provider.dart';
import '../widgets/badge_detail_sheet.dart';

/// Achievements screen with tabs for badges and leaderboard
class AchievementsScreen extends ConsumerStatefulWidget {
  const AchievementsScreen({super.key});

  @override
  ConsumerState<AchievementsScreen> createState() => _AchievementsScreenState();
}

class _AchievementsScreenState extends ConsumerState<AchievementsScreen>
    with TickerProviderStateMixin {
  late TabController _tabController;
  late AnimationController _animationController;

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 2, vsync: this);

    // Initialize animation controller
    _animationController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 800),
    );
    _animationController.forward();

    // Add listener to load leaderboard when the tab is selected
    _tabController.addListener(() {
      if (_tabController.index == 1) {
        // Leaderboard tab selected
        // Load leaderboard data on first visit
        Future.microtask(() {
          final provider = ref.read(leaderboardNotifierProvider);
          // Only skip if we already have valid data
          if (provider.hasValue && provider.value!.isNotEmpty) {
            return;
          }
          ref.read(leaderboardNotifierProvider.notifier).loadLeaderboard();
        });
      }
    });

    // Initial load of badge and leaderboard data
    WidgetsBinding.instance.addPostFrameCallback((_) {
      ref.read(badgeNotifierProvider.notifier).loadBadges();
      ref.read(leaderboardNotifierProvider.notifier).loadLeaderboard();
    });
  }

  @override
  void dispose() {
    _tabController.dispose();
    _animationController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return SafeArea(
      bottom: false, // Allow content to extend behind navbar
      child: Column(
        children: [
          // Header
          _buildHeader(),

          // Tab bar
          _buildTabBar(),

          // Tab content
          Expanded(
            child: TabBarView(
              controller: _tabController,
              children: [
                _buildBadgesTab(),
                _buildLeaderboardTab(),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildHeader() {
    return Padding(
      padding: const EdgeInsets.fromLTRB(20, 16, 20, 8),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              GradientText(
                'Thành Tích',
                style: const TextStyle(
                  fontSize: 28,
                  fontWeight: FontWeight.bold,
                ),
                gradient: AppColors.primaryGradient,
              ),
              const Text(
                'Huy hiệu và bảng xếp hạng',
                style: TextStyle(
                  color: Colors.white70,
                  fontSize: 14,
                ),
              ),
            ],
          ),
          // Trophy icon with pulsing glow
          _PulsingTrophyIcon(),
        ],
      ),
    );
  }

  Widget _buildTabBar() {
    return Container(
      margin: const EdgeInsets.symmetric(horizontal: 20, vertical: 12),
      padding: const EdgeInsets.all(4),
      decoration: BoxDecoration(
        color: Colors.white.withOpacity(0.1),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(
          color: Colors.white.withOpacity(0.1),
        ),
      ),
      child: TabBar(
        controller: _tabController,
        indicator: BoxDecoration(
          gradient: const LinearGradient(
            colors: [AppColors.primaryDark, AppColors.primaryLight],
          ),
          borderRadius: BorderRadius.circular(12),
        ),
        indicatorSize: TabBarIndicatorSize.tab,
        labelColor: AppColors.onPrimary,
        unselectedLabelColor: Colors.white70,
        labelStyle: const TextStyle(
          fontWeight: FontWeight.bold,
          fontSize: 14,
        ),
        dividerColor: Colors.transparent,
        tabs: const [
          Tab(
            child: Row(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Icon(Icons.military_tech, size: 18),
                SizedBox(width: 8),
                Text('Huy Hiệu'),
              ],
            ),
          ),
          Tab(
            child: Row(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Icon(Icons.leaderboard, size: 18),
                SizedBox(width: 8),
                Text('Xếp Hạng'),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildBadgesTab() {
    final badgesAsync = ref.watch(badgeNotifierProvider);

    return badgesAsync.when(
      loading: () => _buildBadgeLoadingState(),
      error: (error, stackTrace) => _buildBadgeErrorState(error),
      data: (badges) {
        if (badges.isEmpty) {
          return RefreshIndicator(
            onRefresh: () async {
              await ref.read(badgeNotifierProvider.notifier).loadBadges();
            },
            color: AppColors.primary,
            backgroundColor: AppColors.surface,
            child: SingleChildScrollView(
              physics: const AlwaysScrollableScrollPhysics(),
              child: SizedBox(
                height: MediaQuery.of(context).size.height * 0.7,
                child: _buildBadgeEmptyState(),
              ),
            ),
          );
        }
        return RefreshIndicator(
          onRefresh: () async {
            await ref.read(badgeNotifierProvider.notifier).loadBadges();
          },
          color: AppColors.primary,
          backgroundColor: AppColors.surface,
          child: _buildBadgeGrid(badges),
        );
      },
    );
  }

  Widget _buildBadgeLoadingState() {
    return GridView.builder(
      padding: const EdgeInsets.fromLTRB(16, 8, 16, 100),
      gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
        crossAxisCount: 2,
        childAspectRatio: 0.9,
        crossAxisSpacing: 12,
        mainAxisSpacing: 12,
      ),
      itemCount: 6,
      itemBuilder: (context, index) {
        return ShimmerWidget(
          duration: const Duration(milliseconds: 1500),
          gradient: LinearGradient(
            colors: [
              Colors.white.withOpacity(0.0),
              Colors.white.withOpacity(0.1),
              Colors.white.withOpacity(0.15),
              Colors.white.withOpacity(0.1),
              Colors.white.withOpacity(0.0),
            ],
            stops: const [0.0, 0.35, 0.5, 0.65, 1.0],
            begin: Alignment.topLeft,
            end: Alignment.bottomRight,
          ),
          enabled: true,
          child: Container(
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(
              color: Colors.white.withOpacity(0.05),
              borderRadius: BorderRadius.circular(20),
              border: Border.all(
                color: Colors.white.withOpacity(0.1),
                width: 1.5,
              ),
            ),
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Container(
                  width: 64,
                  height: 64,
                  decoration: BoxDecoration(
                    shape: BoxShape.circle,
                    color: Colors.white.withOpacity(0.08),
                  ),
                ),
                const SizedBox(height: 12),
                Container(
                  width: 80,
                  height: 14,
                  decoration: BoxDecoration(
                    color: Colors.white.withOpacity(0.08),
                    borderRadius: BorderRadius.circular(7),
                  ),
                ),
                const SizedBox(height: 8),
                Container(
                  width: 60,
                  height: 20,
                  decoration: BoxDecoration(
                    color: Colors.white.withOpacity(0.08),
                    borderRadius: BorderRadius.circular(12),
                  ),
                ),
              ],
            ),
          ),
        );
      },
    );
  }

  Widget _buildBadgeErrorState(Object error) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(24.0),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Icon(
              Icons.error_outline,
              color: Colors.white70,
              size: 64,
            ),
            const SizedBox(height: 16),
            const Text(
              'Không thể tải huy hiệu',
              style: TextStyle(
                color: Colors.white,
                fontSize: 18,
                fontWeight: FontWeight.bold,
              ),
            ),
            const SizedBox(height: 8),
            Text(
              error.toString(),
              style: TextStyle(
                color: Colors.white.withOpacity(0.7),
                fontSize: 14,
              ),
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 24),
            ElevatedButton.icon(
              onPressed: () {
                ref.read(badgeNotifierProvider.notifier).loadBadges();
              },
              icon: const Icon(Icons.refresh),
              label: const Text('Thử lại'),
              style: ElevatedButton.styleFrom(
                backgroundColor: AppColors.primary,
                foregroundColor: AppColors.onPrimary,
                padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 12),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildBadgeEmptyState() {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(24.0),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Icon(
              Icons.military_tech,
              color: Colors.white70,
              size: 64,
            ),
            const SizedBox(height: 16),
            const Text(
              'Chưa có huy hiệu',
              style: TextStyle(
                color: Colors.white,
                fontSize: 18,
                fontWeight: FontWeight.bold,
              ),
            ),
            const SizedBox(height: 8),
            Text(
              'Huy hiệu sẽ xuất hiện khi bạn hoàn thành các thành tích',
              style: TextStyle(
                color: Colors.white.withOpacity(0.7),
                fontSize: 14,
              ),
              textAlign: TextAlign.center,
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildBadgeGrid(List badges) {
    return GridView.builder(
      physics: const AlwaysScrollableScrollPhysics(),
      padding: const EdgeInsets.fromLTRB(16, 8, 16, 100),
      gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
        crossAxisCount: 2,
        childAspectRatio: 0.9,
        crossAxisSpacing: 12,
        mainAxisSpacing: 12,
      ),
      itemCount: badges.length,
      itemBuilder: (context, index) {
        final badge = badges[index];
        return _buildAnimatedBadgeCard(badge, index);
      },
    );
  }

  Widget _buildAnimatedBadgeCard(dynamic badge, int index) {
    return AnimatedBuilder(
      animation: _animationController,
      builder: (context, child) {
        final delay = index * 0.1;
        final animation = CurvedAnimation(
          parent: _animationController,
          curve: Interval(
            delay.clamp(0.0, 1.0),
            (delay + 0.4).clamp(0.0, 1.0),
            curve: Curves.easeOutCubic,
          ),
        );

        final rotationAngle = (1 - animation.value) * math.pi / 2;

        return FadeTransition(
          opacity: animation,
          child: Transform(
            alignment: Alignment.center,
            transform: Matrix4.identity()
              ..setEntry(3, 2, 0.001)
              ..rotateY(rotationAngle),
            child: child,
          ),
        );
      },
      child: _buildBadgeCard(badge),
    );
  }

  Widget _buildBadgeCard(dynamic badge) {
    final isEarned = badge.earnedAt != null;

    Widget badgeContent = PressableGlassCard(
      onTap: () => BadgeDetailSheet.show(context, badge),
      padding: const EdgeInsets.all(16),
      opacity: isEarned ? 0.15 : 0.06,
      border: Border.all(
        color: isEarned
            ? AppColors.primary.withOpacity(0.6)
            : Colors.white.withOpacity(0.1),
        width: isEarned ? 2.0 : 1.5,
      ),
      gradient: isEarned
          ? LinearGradient(
              begin: Alignment.topLeft,
              end: Alignment.bottomRight,
              colors: [
                AppColors.primaryDark.withOpacity(0.08),
                AppColors.primaryLight.withOpacity(0.04),
              ],
            )
          : null,
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          _buildBadgeIcon(badge, isEarned),
          const SizedBox(height: 12),
          _buildBadgeName(badge, isEarned),
          const SizedBox(height: 8),
          _buildBadgeStatus(badge, isEarned),
        ],
      ),
    );

    if (isEarned) {
      return PulsingGlowWidget(
        glowColor: AppColors.primary,
        maxBlurRadius: 12.0,
        minBlurRadius: 4.0,
        duration: const Duration(milliseconds: 2500),
        enabled: true,
        child: badgeContent,
      );
    } else {
      return badgeContent;
    }
  }

  Widget _buildBadgeIcon(dynamic badge, bool isEarned) {
    Widget iconWidget = Container(
      width: 64,
      height: 64,
      decoration: BoxDecoration(
        shape: BoxShape.circle,
        gradient: isEarned
            ? const LinearGradient(
                colors: [AppColors.primaryDark, AppColors.primaryLight],
                begin: Alignment.topLeft,
                end: Alignment.bottomRight,
              )
            : null,
        color: isEarned ? null : Colors.white.withOpacity(0.08),
        boxShadow: isEarned
            ? [
                BoxShadow(
                  color: AppColors.primary.withOpacity(0.4),
                  blurRadius: 16,
                  spreadRadius: 2,
                ),
                BoxShadow(
                  color: AppColors.primaryLight.withOpacity(0.3),
                  blurRadius: 24,
                  spreadRadius: -4,
                ),
              ]
            : null,
      ),
      child: Icon(
        BadgeCategoryUtils.getIcon(badge.category),
        color: isEarned ? AppColors.onPrimary : Colors.white.withOpacity(0.3),
        size: 32,
      ),
    );

    if (!isEarned) {
      iconWidget = Opacity(
        opacity: 0.4,
        child: iconWidget,
      );
    }

    return iconWidget;
  }

  Widget _buildBadgeName(dynamic badge, bool isEarned) {
    if (isEarned) {
      return GradientText(
        badge.name,
        style: const TextStyle(
          fontSize: 14,
          fontWeight: FontWeight.bold,
        ),
        gradient: AppColors.primaryGradient,
        textAlign: TextAlign.center,
        maxLines: 2,
        overflow: TextOverflow.ellipsis,
      );
    }

    return Text(
      badge.name,
      style: TextStyle(
        color: Colors.white.withOpacity(0.4),
        fontSize: 14,
        fontWeight: FontWeight.w600,
      ),
      textAlign: TextAlign.center,
      maxLines: 2,
      overflow: TextOverflow.ellipsis,
    );
  }

  Widget _buildBadgeStatus(dynamic badge, bool isEarned) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
      decoration: BoxDecoration(
        color: isEarned
            ? AppColors.success.withOpacity(0.2)
            : Colors.white.withOpacity(0.05),
        borderRadius: BorderRadius.circular(12),
        border: isEarned
            ? Border.all(
                color: AppColors.success.withOpacity(0.3),
                width: 1,
              )
            : null,
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(
            isEarned ? Icons.check_circle : Icons.lock,
            size: 12,
            color: isEarned ? AppColors.success : Colors.white.withOpacity(0.3),
          ),
          const SizedBox(width: 4),
          Text(
            isEarned ? 'Đã nhận' : '+${badge.xpBonus} XP',
            style: TextStyle(
              color:
                  isEarned ? AppColors.success : Colors.white.withOpacity(0.4),
              fontSize: 11,
              fontWeight: FontWeight.bold,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildLeaderboardTab() {
    final leaderboardAsync = ref.watch(leaderboardNotifierProvider);
    final currentUser = ref.watch(currentUserProvider);

    return leaderboardAsync.when(
      loading: () => _buildLeaderboardLoadingState(),
      error: (error, stackTrace) => _buildErrorState(error),
      data: (entries) {
        if (entries.isEmpty) {
          return RefreshIndicator(
            onRefresh: () async {
              await ref.read(leaderboardNotifierProvider.notifier).loadLeaderboard();
            },
            color: AppColors.primary,
            backgroundColor: AppColors.surface,
            child: SingleChildScrollView(
              physics: const AlwaysScrollableScrollPhysics(),
              child: SizedBox(
                height: MediaQuery.of(context).size.height * 0.7,
                child: _buildEmptyState(),
              ),
            ),
          );
        }
        return RefreshIndicator(
          onRefresh: () async {
            await ref.read(leaderboardNotifierProvider.notifier).loadLeaderboard();
          },
          color: AppColors.primary,
          backgroundColor: AppColors.surface,
          child: _buildLeaderboardList(entries, currentUser?.id),
        );
      },
    );
  }

  Widget _buildLeaderboardLoadingState() {
    return ListView.builder(
      padding: const EdgeInsets.fromLTRB(16, 8, 16, 100),
      itemCount: 8,
      itemBuilder: (context, index) {
        return Container(
          margin: const EdgeInsets.only(bottom: 10),
          child: ShimmerWidget(
            duration: const Duration(milliseconds: 1500),
            gradient: LinearGradient(
              colors: [
                Colors.white.withOpacity(0.0),
                Colors.white.withOpacity(0.1),
                Colors.white.withOpacity(0.15),
                Colors.white.withOpacity(0.1),
                Colors.white.withOpacity(0.0),
              ],
              stops: const [0.0, 0.35, 0.5, 0.65, 1.0],
              begin: Alignment.topLeft,
              end: Alignment.bottomRight,
            ),
            enabled: true,
            child: Container(
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: Colors.white.withOpacity(0.08),
                borderRadius: BorderRadius.circular(16),
                border: Border.all(
                  color: Colors.white.withOpacity(0.1),
                  width: 1,
                ),
              ),
              child: Row(
                children: [
                  Container(
                    width: 40,
                    height: 40,
                    decoration: BoxDecoration(
                      shape: BoxShape.circle,
                      color: Colors.white.withOpacity(0.1),
                    ),
                  ),
                  const SizedBox(width: 16),
                  Container(
                    width: 44,
                    height: 44,
                    decoration: BoxDecoration(
                      shape: BoxShape.circle,
                      color: Colors.white.withOpacity(0.1),
                    ),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Container(
                          width: 100,
                          height: 16,
                          decoration: BoxDecoration(
                            color: Colors.white.withOpacity(0.1),
                            borderRadius: BorderRadius.circular(8),
                          ),
                        ),
                        const SizedBox(height: 4),
                        Container(
                          width: 60,
                          height: 12,
                          decoration: BoxDecoration(
                            color: Colors.white.withOpacity(0.08),
                            borderRadius: BorderRadius.circular(6),
                          ),
                        ),
                      ],
                    ),
                  ),
                  Container(
                    width: 50,
                    height: 24,
                    decoration: BoxDecoration(
                      color: Colors.white.withOpacity(0.1),
                      borderRadius: BorderRadius.circular(12),
                    ),
                  ),
                ],
              ),
            ),
          ),
        );
      },
    );
  }

  Widget _buildErrorState(Object error) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(24.0),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Icon(
              Icons.error_outline,
              color: Colors.white70,
              size: 64,
            ),
            const SizedBox(height: 16),
            const Text(
              'Không thể tải bảng xếp hạng',
              style: TextStyle(
                color: Colors.white,
                fontSize: 18,
                fontWeight: FontWeight.bold,
              ),
            ),
            const SizedBox(height: 8),
            Text(
              error.toString(),
              style: TextStyle(
                color: Colors.white.withOpacity(0.7),
                fontSize: 14,
              ),
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 24),
            ElevatedButton.icon(
              onPressed: () {
                ref.read(leaderboardNotifierProvider.notifier).loadLeaderboard();
              },
              icon: const Icon(Icons.refresh),
              label: const Text('Thử lại'),
              style: ElevatedButton.styleFrom(
                backgroundColor: AppColors.primary,
                foregroundColor: AppColors.onPrimary,
                padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 12),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildEmptyState() {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(24.0),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Icon(
              Icons.leaderboard,
              color: Colors.white70,
              size: 64,
            ),
            const SizedBox(height: 16),
            const Text(
              'Chưa có dữ liệu',
              style: TextStyle(
                color: Colors.white,
                fontSize: 18,
                fontWeight: FontWeight.bold,
              ),
            ),
            const SizedBox(height: 8),
            Text(
              'Bảng xếp hạng sẽ xuất hiện khi có người dùng tham gia',
              style: TextStyle(
                color: Colors.white.withOpacity(0.7),
                fontSize: 14,
              ),
              textAlign: TextAlign.center,
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildLeaderboardList(List<dynamic> entries, String? currentUserId) {
    return ListView.builder(
      physics: const AlwaysScrollableScrollPhysics(),
      padding: const EdgeInsets.fromLTRB(16, 8, 16, 100),
      itemCount: entries.length,
      itemBuilder: (context, index) {
        final entry = entries[index];
        final isCurrentUser = entry.userId == currentUserId;
        return _buildLeaderboardEntry(entry, isCurrentUser);
      },
    );
  }

  Widget _buildLeaderboardEntry(dynamic entry, bool isCurrentUser) {
    final rank = entry.rank as int;
    final displayName = entry.displayName as String;
    final totalXp = entry.totalXp as int;
    final avatarUrl = entry.avatarUrl as String?;
    final title = entry.title as String;
    final isTopThree = rank <= 3;

    Color getRankColor() {
      switch (rank) {
        case 1:
          return AppColors.rankGold;
        case 2:
          return AppColors.rankSilver;
        case 3:
          return AppColors.rankBronze;
        default:
          return Colors.white.withOpacity(0.5);
      }
    }

    return Container(
      margin: const EdgeInsets.only(bottom: 10),
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: isCurrentUser
            ? AppColors.primary.withOpacity(0.15)
            : Colors.white.withOpacity(0.08),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(
          color: isCurrentUser
              ? AppColors.primary.withOpacity(0.5)
              : Colors.white.withOpacity(0.1),
          width: 1,
        ),
      ),
      child: Row(
        children: [
          // Rank
          Container(
            width: 40,
            height: 40,
            decoration: BoxDecoration(
              shape: BoxShape.circle,
              color: isTopThree
                  ? getRankColor().withOpacity(0.2)
                  : Colors.white.withOpacity(0.1),
              border: isTopThree
                  ? Border.all(color: getRankColor(), width: 2)
                  : null,
            ),
            child: Center(
              child: isTopThree
                  ? Icon(
                      Icons.emoji_events,
                      color: getRankColor(),
                      size: 20,
                    )
                  : Text(
                      '$rank',
                      style: TextStyle(
                        color: Colors.white.withOpacity(0.7),
                        fontSize: 16,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
            ),
          ),

          const SizedBox(width: 16),

          // Avatar placeholder
          Container(
            width: 44,
            height: 44,
            decoration: BoxDecoration(
              shape: BoxShape.circle,
              gradient: isCurrentUser
                  ? const LinearGradient(
                      colors: [AppColors.primaryDark, AppColors.primaryLight],
                    )
                  : null,
              color: isCurrentUser ? null : Colors.white.withOpacity(0.1),
            ),
            child: Center(
              child: Text(
                displayName[0].toUpperCase(),
                style: TextStyle(
                  color: isCurrentUser
                      ? AppColors.onPrimary
                      : Colors.white.withOpacity(0.7),
                  fontSize: 18,
                  fontWeight: FontWeight.bold,
                ),
              ),
            ),
          ),

          const SizedBox(width: 12),

          // Name and title
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    Flexible(
                      child: Text(
                        displayName,
                        style: TextStyle(
                          color: isCurrentUser
                              ? AppColors.primary
                              : Colors.white,
                          fontSize: 16,
                          fontWeight:
                              isCurrentUser ? FontWeight.bold : FontWeight.normal,
                        ),
                        overflow: TextOverflow.ellipsis,
                      ),
                    ),
                    if (isCurrentUser) ...[
                      const SizedBox(width: 8),
                      Container(
                        padding: const EdgeInsets.symmetric(
                            horizontal: 6, vertical: 2),
                        decoration: BoxDecoration(
                          color: AppColors.primary.withOpacity(0.2),
                          borderRadius: BorderRadius.circular(6),
                        ),
                        child: const Text(
                          'Bạn',
                          style: TextStyle(
                            color: AppColors.primary,
                            fontSize: 10,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                      ),
                    ],
                  ],
                ),
                Text(
                  title,
                  style: TextStyle(
                    color: Colors.white.withOpacity(0.5),
                    fontSize: 12,
                  ),
                ),
              ],
            ),
          ),

          // Streak badge (show placeholder - will be populated when API supports it)
          // TODO: Add streak field to leaderboard API and LeaderboardEntryDto
          // For now, show streak badge for top 3 players as demo
          if (isTopThree)
            Padding(
              padding: const EdgeInsets.only(right: 12),
              child: StreakBadge(
                streakDays: rank == 1 ? 42 : (rank == 2 ? 28 : 14),
                compact: true,
              ),
            ),

          // XP
          Column(
            crossAxisAlignment: CrossAxisAlignment.end,
            children: [
              Row(
                children: [
                  Icon(
                    Icons.star,
                    color: AppColors.primary.withOpacity(0.8),
                    size: 16,
                  ),
                  const SizedBox(width: 4),
                  Text(
                    '$totalXp',
                    style: const TextStyle(
                      color: Colors.white,
                      fontSize: 16,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                ],
              ),
              Text(
                'XP',
                style: TextStyle(
                  color: Colors.white.withOpacity(0.5),
                  fontSize: 11,
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }
}

/// Pulsing trophy icon widget with continuous animation
class _PulsingTrophyIcon extends StatefulWidget {
  @override
  State<_PulsingTrophyIcon> createState() => _PulsingTrophyIconState();
}

class _PulsingTrophyIconState extends State<_PulsingTrophyIcon>
    with SingleTickerProviderStateMixin {
  late AnimationController _controller;
  late Animation<double> _pulseAnimation;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 2000),
    );

    _pulseAnimation = Tween<double>(begin: 0.8, end: 1.2).animate(
      CurvedAnimation(parent: _controller, curve: Curves.easeInOut),
    );

    _controller.repeat(reverse: true);
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: _pulseAnimation,
      builder: (context, child) {
        return Container(
          width: 50,
          height: 50,
          decoration: BoxDecoration(
            gradient: const LinearGradient(
              colors: [AppColors.primaryDark, AppColors.primaryLight],
            ),
            borderRadius: BorderRadius.circular(16),
            boxShadow: [
              BoxShadow(
                color: AppColors.primary.withOpacity(0.25 * _pulseAnimation.value),
                blurRadius: 10 + (4 * _pulseAnimation.value),
                spreadRadius: 1.5 * _pulseAnimation.value,
              ),
            ],
          ),
          child: const Icon(
            Icons.emoji_events,
            color: AppColors.onPrimary,
            size: 28,
          ),
        );
      },
    );
  }
}
