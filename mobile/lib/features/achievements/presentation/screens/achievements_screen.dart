import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../../shared/widgets/glass/animated_background.dart';
import '../../../../shared/widgets/glass/glass_container.dart';
import '../../../auth/presentation/providers/auth_provider.dart';
import '../providers/leaderboard_provider.dart';

/// Achievements screen with tabs for badges and leaderboard
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
    _tabController = TabController(length: 2, vsync: this);

    // Add listener to load leaderboard when the tab is selected
    _tabController.addListener(() {
      if (_tabController.index == 1) {
        // Leaderboard tab selected
        // Load leaderboard data on first visit
        Future.microtask(() {
          final provider = ref.read(leaderboardNotifierProvider);
          if (provider is AsyncLoading || provider is AsyncData) {
            // Already loading or loaded
            return;
          }
          ref.read(leaderboardNotifierProvider.notifier).loadLeaderboard();
        });
      }
    });
  }

  @override
  void dispose() {
    _tabController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return AnimatedGradientBackground(
      child: SafeArea(
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
      ),
    );
  }

  Widget _buildHeader() {
    return Padding(
      padding: const EdgeInsets.fromLTRB(20, 16, 20, 8),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          const Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                'Thành Tích',
                style: TextStyle(
                  color: Colors.white,
                  fontSize: 28,
                  fontWeight: FontWeight.bold,
                ),
              ),
              Text(
                'Huy hiệu và bảng xếp hạng',
                style: TextStyle(
                  color: Colors.white70,
                  fontSize: 14,
                ),
              ),
            ],
          ),
          // Trophy icon
          Container(
            width: 50,
            height: 50,
            decoration: BoxDecoration(
              gradient: const LinearGradient(
                colors: [Color(0xFFD4A84B), Color(0xFFE8C87E)],
              ),
              borderRadius: BorderRadius.circular(16),
              boxShadow: [
                BoxShadow(
                  color: const Color(0xFFD4A84B).withOpacity(0.3),
                  blurRadius: 12,
                  spreadRadius: 2,
                ),
              ],
            ),
            child: const Icon(
              Icons.emoji_events,
              color: Color(0xFF1A1A2E),
              size: 28,
            ),
          ),
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
            colors: [Color(0xFFD4A84B), Color(0xFFE8C87E)],
          ),
          borderRadius: BorderRadius.circular(12),
        ),
        indicatorSize: TabBarIndicatorSize.tab,
        labelColor: const Color(0xFF1A1A2E),
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
    // Sample badges data - will integrate with API
    final badges = [
      {'name': 'Người Khám Phá', 'icon': Icons.visibility, 'earned': true, 'xp': 50},
      {'name': 'Học Sinh Chăm Chỉ', 'icon': Icons.school, 'earned': true, 'xp': 100},
      {'name': 'Bậc Thầy', 'icon': Icons.star, 'earned': false, 'xp': 200},
      {'name': 'Chuỗi 7 Ngày', 'icon': Icons.local_fire_department, 'earned': false, 'xp': 150},
      {'name': 'Nhà Sưu Tập', 'icon': Icons.collections, 'earned': false, 'xp': 300},
      {'name': 'Hoàn Hảo', 'icon': Icons.workspace_premium, 'earned': false, 'xp': 500},
    ];

    return GridView.builder(
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
        return _buildBadgeCard(badge);
      },
    );
  }

  Widget _buildBadgeCard(Map<String, dynamic> badge) {
    final isEarned = badge['earned'] as bool;

    return GlassContainer(
      opacity: isEarned ? 0.12 : 0.06,
      padding: const EdgeInsets.all(16),
      border: Border.all(
        color: isEarned
            ? const Color(0xFFD4A84B).withOpacity(0.5)
            : Colors.white.withOpacity(0.1),
        width: 1.5,
      ),
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          // Badge icon
          Container(
            width: 64,
            height: 64,
            decoration: BoxDecoration(
              shape: BoxShape.circle,
              gradient: isEarned
                  ? const LinearGradient(
                      colors: [Color(0xFFD4A84B), Color(0xFFE8C87E)],
                    )
                  : null,
              color: isEarned ? null : Colors.white.withOpacity(0.1),
              boxShadow: isEarned
                  ? [
                      BoxShadow(
                        color: const Color(0xFFD4A84B).withOpacity(0.3),
                        blurRadius: 12,
                        spreadRadius: 2,
                      ),
                    ]
                  : null,
            ),
            child: Icon(
              badge['icon'] as IconData,
              color: isEarned
                  ? const Color(0xFF1A1A2E)
                  : Colors.white.withOpacity(0.3),
              size: 32,
            ),
          ),

          const SizedBox(height: 12),

          // Badge name
          Text(
            badge['name'] as String,
            style: TextStyle(
              color: isEarned ? Colors.white : Colors.white.withOpacity(0.5),
              fontSize: 14,
              fontWeight: FontWeight.bold,
            ),
            textAlign: TextAlign.center,
            maxLines: 2,
            overflow: TextOverflow.ellipsis,
          ),

          const SizedBox(height: 8),

          // XP reward or status
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
            decoration: BoxDecoration(
              color: isEarned
                  ? const Color(0xFF4CAF50).withOpacity(0.2)
                  : Colors.white.withOpacity(0.05),
              borderRadius: BorderRadius.circular(12),
            ),
            child: Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                Icon(
                  isEarned ? Icons.check_circle : Icons.lock,
                  size: 12,
                  color: isEarned
                      ? const Color(0xFF4CAF50)
                      : Colors.white.withOpacity(0.3),
                ),
                const SizedBox(width: 4),
                Text(
                  isEarned ? 'Đã nhận' : '+${badge['xp']} XP',
                  style: TextStyle(
                    color: isEarned
                        ? const Color(0xFF4CAF50)
                        : Colors.white.withOpacity(0.5),
                    fontSize: 11,
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ],
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
      loading: () => const Center(
        child: CircularProgressIndicator(
          valueColor: AlwaysStoppedAnimation<Color>(Color(0xFFD4A84B)),
        ),
      ),
      error: (error, stackTrace) => _buildErrorState(error),
      data: (entries) {
        if (entries.isEmpty) {
          return _buildEmptyState();
        }
        return _buildLeaderboardList(entries, currentUser?.id);
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
                backgroundColor: const Color(0xFFD4A84B),
                foregroundColor: const Color(0xFF1A1A2E),
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
          return const Color(0xFFFFD700); // Gold
        case 2:
          return const Color(0xFFC0C0C0); // Silver
        case 3:
          return const Color(0xFFCD7F32); // Bronze
        default:
          return Colors.white.withOpacity(0.5);
      }
    }

    return Container(
      margin: const EdgeInsets.only(bottom: 10),
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: isCurrentUser
            ? const Color(0xFFD4A84B).withOpacity(0.15)
            : Colors.white.withOpacity(0.08),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(
          color: isCurrentUser
              ? const Color(0xFFD4A84B).withOpacity(0.5)
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
                      colors: [Color(0xFFD4A84B), Color(0xFFE8C87E)],
                    )
                  : null,
              color: isCurrentUser ? null : Colors.white.withOpacity(0.1),
            ),
            child: Center(
              child: Text(
                displayName[0].toUpperCase(),
                style: TextStyle(
                  color: isCurrentUser
                      ? const Color(0xFF1A1A2E)
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
                              ? const Color(0xFFD4A84B)
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
                          color: const Color(0xFFD4A84B).withOpacity(0.2),
                          borderRadius: BorderRadius.circular(6),
                        ),
                        child: const Text(
                          'Bạn',
                          style: TextStyle(
                            color: Color(0xFFD4A84B),
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

          // XP
          Column(
            crossAxisAlignment: CrossAxisAlignment.end,
            children: [
              Row(
                children: [
                  Icon(
                    Icons.star,
                    color: const Color(0xFFD4A84B).withOpacity(0.8),
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
