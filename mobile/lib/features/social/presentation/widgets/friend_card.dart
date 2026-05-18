import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../../core/theme/app_colors.dart';
import '../../../../core/theme/app_spacing.dart';
import '../../../../shared/widgets/glass/glass_container.dart';
import '../../../auth/presentation/providers/auth_provider.dart';
import '../../domain/entities/friend.dart';

/// Friend profile card widget
class FriendCard extends ConsumerWidget {
  final Friend friend;
  final VoidCallback? onTap;
  final VoidCallback? onRemove;

  const FriendCard({
    super.key,
    required this.friend,
    this.onTap,
    this.onRemove,
  });

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final currentUser = ref.watch(authNotifierProvider).user;
    final myXp = currentUser?.totalXp ?? 0;
    final xpDifference = (friend.xp - myXp).toInt();

    return GlassContainer(
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(16),
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Row(
            children: [
              // Avatar
              _buildAvatar(),

              AppSpacing.horizontalSpaceMD,

              // Friend info
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    // Name
                    Text(
                      friend.displayName,
                      style: const TextStyle(
                        fontSize: 16,
                        fontWeight: FontWeight.bold,
                        color: Colors.white,
                      ),
                    ),

                    AppSpacing.verticalSpaceXS,

                    // Stats row
                    Row(
                      children: [
                        // XP
                        _buildStatChip(
                          icon: Icons.stars,
                          value: friend.xp.toString(),
                          color: AppColors.xpGold,
                        ),

                        AppSpacing.horizontalSpaceSM,

                        // Streak
                        _buildStatChip(
                          icon: Icons.local_fire_department,
                          value: '${friend.currentStreak}',
                          color: AppColors.streakOrange,
                        ),

                        AppSpacing.horizontalSpaceSM,

                        // Level
                        _buildStatChip(
                          icon: Icons.shield,
                          value: 'Cấp ${friend.level}',
                          color: AppColors.info,
                        ),
                      ],
                    ),

                    // XP comparison
                    if (xpDifference != 0) ...[
                      AppSpacing.verticalSpaceXS,
                      _buildXpComparison(xpDifference),
                    ],
                  ],
                ),
              ),

              // Actions
              if (onRemove != null)
                IconButton(
                  icon: const Icon(
                    Icons.more_vert,
                    color: Colors.white70,
                  ),
                  onPressed: () => _showOptions(context),
                ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildAvatar() {
    return Container(
      width: 56,
      height: 56,
      decoration: BoxDecoration(
        shape: BoxShape.circle,
        gradient: LinearGradient(
          colors: [
            AppColors.primary,
            AppColors.primaryDark,
          ],
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
        ),
        border: Border.all(
          color: Colors.white.withOpacity(0.3),
          width: 2,
        ),
      ),
      child: friend.avatarUrl != null
          ? ClipOval(
              child: Image.network(
                friend.avatarUrl!,
                fit: BoxFit.cover,
                errorBuilder: (context, error, stackTrace) => _buildDefaultAvatar(),
              ),
            )
          : _buildDefaultAvatar(),
    );
  }

  Widget _buildDefaultAvatar() {
    return Center(
      child: Text(
        friend.displayName.isNotEmpty ? friend.displayName[0].toUpperCase() : '?',
        style: const TextStyle(
          fontSize: 24,
          fontWeight: FontWeight.bold,
          color: Colors.white,
        ),
      ),
    );
  }

  Widget _buildStatChip({
    required IconData icon,
    required String value,
    required Color color,
  }) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
      decoration: BoxDecoration(
        color: color.withOpacity(0.2),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(
          color: color.withOpacity(0.3),
          width: 1,
        ),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(icon, size: 14, color: color),
          const SizedBox(width: 4),
          Text(
            value,
            style: TextStyle(
              fontSize: 12,
              fontWeight: FontWeight.bold,
              color: color,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildXpComparison(int difference) {
    final isAhead = difference > 0;
    final absValue = difference.abs();

    return Row(
      children: [
        Icon(
          isAhead ? Icons.arrow_upward : Icons.arrow_downward,
          size: 12,
          color: isAhead ? AppColors.success : AppColors.warning,
        ),
        const SizedBox(width: 4),
        Text(
          isAhead
              ? 'Hơn bạn $absValue XP'
              : 'Kém bạn $absValue XP',
          style: TextStyle(
            fontSize: 11,
            color: isAhead ? AppColors.success : AppColors.warning,
          ),
        ),
      ],
    );
  }

  void _showOptions(BuildContext context) {
    showModalBottomSheet(
      context: context,
      backgroundColor: Colors.transparent,
      builder: (context) => GlassContainer(
        borderRadius: const BorderRadius.vertical(top: Radius.circular(24)),
        child: SafeArea(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              ListTile(
                leading: const Icon(Icons.person_remove, color: Colors.red),
                title: const Text(
                  'Hủy kết bạn',
                  style: TextStyle(color: Colors.red),
                ),
                onTap: () {
                  Navigator.pop(context);
                  if (onRemove != null) {
                    onRemove!();
                  }
                },
              ),
              ListTile(
                leading: const Icon(Icons.close, color: Colors.white70),
                title: const Text(
                  'Hủy',
                  style: TextStyle(color: Colors.white70),
                ),
                onTap: () => Navigator.pop(context),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

