import 'package:flutter/material.dart';
import '../../../core/theme/app_colors.dart';

/// Milestone icons to replace emoji usage
/// Provides Material Design icons for streak milestones
class MilestoneIcon extends StatelessWidget {
  final int days;
  final double size;
  final bool showGlow;

  const MilestoneIcon({
    super.key,
    required this.days,
    this.size = 56,
    this.showGlow = true,
  });

  @override
  Widget build(BuildContext context) {
    final config = _getMilestoneConfig(days);

    return Container(
      width: size,
      height: size,
      decoration: showGlow
          ? BoxDecoration(
              gradient: RadialGradient(
                colors: [
                  config.color.withOpacity(0.4),
                  config.color.withOpacity(0.1),
                ],
              ),
              shape: BoxShape.circle,
            )
          : null,
      child: Icon(
        config.icon,
        size: size * 0.65,
        color: config.color,
      ),
    );
  }

  _MilestoneIconConfig _getMilestoneConfig(int days) {
    if (days >= 365) {
      return const _MilestoneIconConfig(
        icon: Icons.emoji_events_rounded, // 👑 Crown/Trophy
        color: AppColors.xpGold,
      );
    } else if (days >= 100) {
      return const _MilestoneIconConfig(
        icon: Icons.emoji_events_rounded, // 🏆 Trophy
        color: Colors.amber,
      );
    } else if (days >= 30) {
      return const _MilestoneIconConfig(
        icon: Icons.track_changes_rounded, // 🎯 Target
        color: Colors.purple,
      );
    } else if (days >= 7) {
      return const _MilestoneIconConfig(
        icon: Icons.star_rounded, // ⭐ Star
        color: AppColors.primary,
      );
    }
    return const _MilestoneIconConfig(
      icon: Icons.flag_rounded,
      color: Colors.grey,
    );
  }
}

class _MilestoneIconConfig {
  final IconData icon;
  final Color color;

  const _MilestoneIconConfig({
    required this.icon,
    required this.color,
  });
}

/// Simple milestone icon without background for inline usage
class SimpleMilestoneIcon extends StatelessWidget {
  final int days;
  final double size;

  const SimpleMilestoneIcon({
    super.key,
    required this.days,
    this.size = 16,
  });

  @override
  Widget build(BuildContext context) {
    final config = _getMilestoneIconConfig(days);

    return Icon(
      config.icon,
      size: size,
      color: config.color,
    );
  }

  _MilestoneIconConfig _getMilestoneIconConfig(int days) {
    if (days >= 365) {
      return const _MilestoneIconConfig(
        icon: Icons.emoji_events_rounded,
        color: AppColors.xpGold,
      );
    } else if (days >= 100) {
      return const _MilestoneIconConfig(
        icon: Icons.emoji_events_rounded,
        color: Colors.amber,
      );
    } else if (days >= 30) {
      return const _MilestoneIconConfig(
        icon: Icons.track_changes_rounded,
        color: Colors.purple,
      );
    } else if (days >= 7) {
      return const _MilestoneIconConfig(
        icon: Icons.star_rounded,
        color: AppColors.primary,
      );
    }
    return const _MilestoneIconConfig(
      icon: Icons.flag_rounded,
      color: Colors.grey,
    );
  }
}

