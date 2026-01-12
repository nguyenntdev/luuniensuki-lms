import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../../shared/widgets/glass/animated_background.dart';
import '../../../../shared/widgets/glass/glass_container.dart';
import '../../../auth/domain/entities/user.dart';
import '../../../auth/presentation/providers/auth_provider.dart';
import '../../../auth/presentation/providers/auth_state.dart';
import '../../../collection/presentation/providers/collection_provider.dart';

/// Profile screen showing user info, stats, and settings
class ProfileScreen extends ConsumerWidget {
  const ProfileScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final authState = ref.watch(authNotifierProvider);
    final user = authState.user;

    return AnimatedGradientBackground(
      child: SafeArea(
        child: user == null
            ? _buildNotLoggedIn(context)
            : _buildProfile(context, ref, user),
      ),
    );
  }

  Widget _buildNotLoggedIn(BuildContext context) {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(
            Icons.person_outline,
            size: 80,
            color: Colors.white.withOpacity(0.5),
          ),
          const SizedBox(height: 16),
          Text(
            'Chưa đăng nhập',
            style: TextStyle(
              color: Colors.white.withOpacity(0.7),
              fontSize: 18,
            ),
          ),
          const SizedBox(height: 24),
          ElevatedButton(
            onPressed: () => context.go('/login'),
            style: ElevatedButton.styleFrom(
              backgroundColor: const Color(0xFFD4A84B),
              foregroundColor: const Color(0xFF1A1A2E),
              padding: const EdgeInsets.symmetric(horizontal: 32, vertical: 12),
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(12),
              ),
            ),
            child: const Text('Đăng nhập'),
          ),
        ],
      ),
    );
  }

  Widget _buildProfile(BuildContext context, WidgetRef ref, User user) {
    return SingleChildScrollView(
      padding: const EdgeInsets.all(20),
      child: Column(
        children: [
          // Header with avatar and name
          _buildProfileHeader(user),

          const SizedBox(height: 24),

          // XP Progress Card
          _buildXpCard(user),

          const SizedBox(height: 16),

          // Stats Grid
          _buildStatsGrid(ref, user),

          const SizedBox(height: 16),

          // Streak Card
          _buildStreakCard(user),

          const SizedBox(height: 24),

          // Action Buttons
          _buildActionButtons(context, ref),

          const SizedBox(height: 100), // Bottom padding for nav bar
        ],
      ),
    );
  }

  Widget _buildProfileHeader(User user) {
    return Column(
      children: [
        // Avatar
        Container(
          width: 100,
          height: 100,
          decoration: BoxDecoration(
            shape: BoxShape.circle,
            gradient: const LinearGradient(
              colors: [Color(0xFFD4A84B), Color(0xFFE8C87E)],
            ),
            border: Border.all(
              color: Colors.white.withOpacity(0.3),
              width: 3,
            ),
            boxShadow: [
              BoxShadow(
                color: const Color(0xFFD4A84B).withOpacity(0.3),
                blurRadius: 20,
                spreadRadius: 2,
              ),
            ],
          ),
          child: user.avatarUrl != null && user.avatarUrl!.isNotEmpty
              ? ClipOval(
                  child: Image.network(
                    user.avatarUrl!,
                    fit: BoxFit.cover,
                    errorBuilder: (_, __, ___) => _buildAvatarPlaceholder(user),
                  ),
                )
              : _buildAvatarPlaceholder(user),
        ),

        const SizedBox(height: 16),

        // Display Name
        Text(
          user.displayName,
          style: const TextStyle(
            color: Colors.white,
            fontSize: 24,
            fontWeight: FontWeight.bold,
          ),
        ),

        // Email
        Text(
          user.email,
          style: TextStyle(
            color: Colors.white.withOpacity(0.6),
            fontSize: 14,
          ),
        ),

        // Rank badge
        const SizedBox(height: 8),
        Container(
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 6),
          decoration: BoxDecoration(
            color: const Color(0xFFD4A84B).withOpacity(0.2),
            borderRadius: BorderRadius.circular(20),
            border: Border.all(
              color: const Color(0xFFD4A84B).withOpacity(0.5),
            ),
          ),
          child: Text(
            user.rank.name,
            style: const TextStyle(
              color: Color(0xFFD4A84B),
              fontSize: 12,
              fontWeight: FontWeight.bold,
            ),
          ),
        ),
      ],
    );
  }

  Widget _buildAvatarPlaceholder(User user) {
    final initial = user.displayName.isNotEmpty
        ? user.displayName[0].toUpperCase()
        : user.email[0].toUpperCase();
    return Center(
      child: Text(
        initial,
        style: const TextStyle(
          color: Color(0xFF1A1A2E),
          fontSize: 40,
          fontWeight: FontWeight.bold,
        ),
      ),
    );
  }

  Widget _buildXpCard(User user) {
    final totalXp = user.totalXp;
    final xpToNext = user.xpToNextRank;
    final currentRank = user.rank.name;
    final nextRank = user.nextRank?.name;
    final progress = xpToNext > 0 ? (totalXp % xpToNext) / xpToNext : 1.0;

    return GlassContainer(
      padding: const EdgeInsets.all(20),
      child: Column(
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text(
                    'Kinh nghiệm',
                    style: TextStyle(
                      color: Colors.white70,
                      fontSize: 14,
                    ),
                  ),
                  const SizedBox(height: 4),
                  Row(
                    children: [
                      const Icon(
                        Icons.star,
                        color: Color(0xFFD4A84B),
                        size: 24,
                      ),
                      const SizedBox(width: 8),
                      Text(
                        '$totalXp XP',
                        style: const TextStyle(
                          color: Colors.white,
                          fontSize: 28,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                    ],
                  ),
                ],
              ),
              Column(
                crossAxisAlignment: CrossAxisAlignment.end,
                children: [
                  Text(
                    currentRank,
                    style: const TextStyle(
                      color: Color(0xFFD4A84B),
                      fontSize: 16,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                  if (nextRank != null)
                    Text(
                      '→ $nextRank',
                      style: TextStyle(
                        color: Colors.white.withOpacity(0.5),
                        fontSize: 12,
                      ),
                    ),
                ],
              ),
            ],
          ),

          const SizedBox(height: 16),

          // XP Progress bar
          Column(
            children: [
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Text(
                    'Còn $xpToNext XP để lên cấp',
                    style: TextStyle(
                      color: Colors.white.withOpacity(0.6),
                      fontSize: 12,
                    ),
                  ),
                  Text(
                    '${(progress * 100).round()}%',
                    style: TextStyle(
                      color: Colors.white.withOpacity(0.6),
                      fontSize: 12,
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 8),
              Container(
                height: 8,
                decoration: BoxDecoration(
                  color: Colors.white.withOpacity(0.1),
                  borderRadius: BorderRadius.circular(4),
                ),
                child: FractionallySizedBox(
                  alignment: Alignment.centerLeft,
                  widthFactor: progress.clamp(0.0, 1.0),
                  child: Container(
                    decoration: BoxDecoration(
                      gradient: const LinearGradient(
                        colors: [Color(0xFFD4A84B), Color(0xFFE8C87E)],
                      ),
                      borderRadius: BorderRadius.circular(4),
                    ),
                  ),
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildStatsGrid(WidgetRef ref, User user) {
    final collectionState = ref.watch(collectionNotifierProvider);
    final discoveredCount = collectionState.collection?.stats.discovered ?? 0;

    return Row(
      children: [
        Expanded(
          child: _buildStatCard(
            icon: Icons.visibility,
            label: 'Đã khám phá',
            value: '$discoveredCount',
            color: const Color(0xFF64B5F6),
          ),
        ),
        const SizedBox(width: 12),
        Expanded(
          child: _buildStatCard(
            icon: Icons.school,
            label: 'Đã học',
            value: '${user.totalXp ~/ 75}', // Approximate
            color: const Color(0xFF81C784),
          ),
        ),
        const SizedBox(width: 12),
        Expanded(
          child: _buildStatCard(
            icon: Icons.emoji_events,
            label: 'Huy hiệu',
            value: '0', // Would need badges count
            color: const Color(0xFFD4A84B),
          ),
        ),
      ],
    );
  }

  Widget _buildStatCard({
    required IconData icon,
    required String label,
    required String value,
    required Color color,
  }) {
    return GlassContainer(
      padding: const EdgeInsets.symmetric(vertical: 16, horizontal: 12),
      child: Column(
        children: [
          Icon(icon, color: color, size: 28),
          const SizedBox(height: 8),
          Text(
            value,
            style: const TextStyle(
              color: Colors.white,
              fontSize: 20,
              fontWeight: FontWeight.bold,
            ),
          ),
          const SizedBox(height: 4),
          Text(
            label,
            style: TextStyle(
              color: Colors.white.withOpacity(0.6),
              fontSize: 11,
            ),
            textAlign: TextAlign.center,
          ),
        ],
      ),
    );
  }

  Widget _buildStreakCard(User user) {
    final currentStreak = user.currentStreak;
    final longestStreak = user.longestStreak;
    final streakFreezes = user.streakFreezes;

    return GlassContainer(
      padding: const EdgeInsets.all(20),
      child: Row(
        children: [
          // Streak fire icon
          Container(
            width: 56,
            height: 56,
            decoration: BoxDecoration(
              color: currentStreak > 0
                  ? const Color(0xFFFF6B35).withOpacity(0.2)
                  : Colors.white.withOpacity(0.1),
              borderRadius: BorderRadius.circular(16),
            ),
            child: Icon(
              Icons.local_fire_department,
              color: currentStreak > 0
                  ? const Color(0xFFFF6B35)
                  : Colors.white.withOpacity(0.3),
              size: 32,
            ),
          ),

          const SizedBox(width: 16),

          // Streak info
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    Text(
                      '$currentStreak ngày',
                      style: const TextStyle(
                        color: Colors.white,
                        fontSize: 24,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                    if (currentStreak > 0)
                      const Padding(
                        padding: EdgeInsets.only(left: 8),
                        child: Text('🔥', style: TextStyle(fontSize: 20)),
                      ),
                  ],
                ),
                Text(
                  'Chuỗi học tập hiện tại',
                  style: TextStyle(
                    color: Colors.white.withOpacity(0.6),
                    fontSize: 14,
                  ),
                ),
              ],
            ),
          ),

          // Stats column
          Column(
            crossAxisAlignment: CrossAxisAlignment.end,
            children: [
              Text(
                'Kỷ lục: $longestStreak',
                style: TextStyle(
                  color: Colors.white.withOpacity(0.6),
                  fontSize: 12,
                ),
              ),
              const SizedBox(height: 4),
              Row(
                children: [
                  Icon(
                    Icons.ac_unit,
                    color: Colors.white.withOpacity(0.5),
                    size: 14,
                  ),
                  const SizedBox(width: 4),
                  Text(
                    '$streakFreezes',
                    style: TextStyle(
                      color: Colors.white.withOpacity(0.6),
                      fontSize: 12,
                    ),
                  ),
                ],
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildActionButtons(BuildContext context, WidgetRef ref) {
    return Column(
      children: [
        // Settings button
        _buildActionButton(
          icon: Icons.settings_outlined,
          label: 'Cài đặt',
          onTap: () {
            // Navigate to settings
            ScaffoldMessenger.of(context).showSnackBar(
              const SnackBar(content: Text('Cài đặt - Coming soon')),
            );
          },
        ),

        const SizedBox(height: 12),

        // Logout button
        _buildActionButton(
          icon: Icons.logout,
          label: 'Đăng xuất',
          isDestructive: true,
          onTap: () => _showLogoutDialog(context, ref),
        ),
      ],
    );
  }

  Widget _buildActionButton({
    required IconData icon,
    required String label,
    required VoidCallback onTap,
    bool isDestructive = false,
  }) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 16),
        decoration: BoxDecoration(
          color: Colors.white.withOpacity(0.08),
          borderRadius: BorderRadius.circular(16),
          border: Border.all(
            color: isDestructive
                ? Colors.red.withOpacity(0.3)
                : Colors.white.withOpacity(0.1),
          ),
        ),
        child: Row(
          children: [
            Icon(
              icon,
              color: isDestructive ? Colors.red[300] : Colors.white70,
              size: 24,
            ),
            const SizedBox(width: 16),
            Text(
              label,
              style: TextStyle(
                color: isDestructive ? Colors.red[300] : Colors.white,
                fontSize: 16,
              ),
            ),
            const Spacer(),
            Icon(
              Icons.chevron_right,
              color: isDestructive
                  ? Colors.red.withOpacity(0.5)
                  : Colors.white.withOpacity(0.3),
            ),
          ],
        ),
      ),
    );
  }

  void _showLogoutDialog(BuildContext context, WidgetRef ref) {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        backgroundColor: const Color(0xFF1A1A2E),
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(20),
          side: BorderSide(color: Colors.white.withOpacity(0.1)),
        ),
        title: const Text(
          'Đăng xuất',
          style: TextStyle(color: Colors.white),
        ),
        content: Text(
          'Bạn có chắc chắn muốn đăng xuất?',
          style: TextStyle(color: Colors.white.withOpacity(0.7)),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: Text(
              'Hủy',
              style: TextStyle(color: Colors.white.withOpacity(0.7)),
            ),
          ),
          TextButton(
            onPressed: () {
              Navigator.pop(context);
              ref.read(authNotifierProvider.notifier).logout();
              context.go('/login');
            },
            child: const Text(
              'Đăng xuất',
              style: TextStyle(color: Colors.red),
            ),
          ),
        ],
      ),
    );
  }
}
