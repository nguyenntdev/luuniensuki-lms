import 'package:flutter/material.dart';

import '../../../../core/theme/app_colors.dart';
import '../../../../shared/widgets/icons/index.dart';

/// Small streak badge for display in leaderboard entries
/// Shows fire icon with streak count
class StreakBadge extends StatelessWidget {
  final int streakDays;
  final bool compact;
  final bool showLabel;

  const StreakBadge({
    super.key,
    required this.streakDays,
    this.compact = false,
    this.showLabel = true,
  });

  Color _getStreakColor() {
    if (streakDays >= 365) return AppColors.xpGold;
    if (streakDays >= 100) return Colors.purple;
    if (streakDays >= 30) return Colors.blue;
    if (streakDays >= 7) return Colors.green;
    return AppColors.streakOrange;
  }

  @override
  Widget build(BuildContext context) {
    if (streakDays <= 0) {
      return const SizedBox.shrink();
    }

    final color = _getStreakColor();

    if (compact) {
      return Container(
        padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
        decoration: BoxDecoration(
          color: color.withOpacity(0.2),
          borderRadius: BorderRadius.circular(10),
          border: Border.all(
            color: color.withOpacity(0.4),
            width: 1,
          ),
        ),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            StreakIcon(
              type: StreakIconType.fire,
              size: compact ? 10 : 12,
            ),
            const SizedBox(width: 2),
            Text(
              '$streakDays',
              style: TextStyle(
                color: color,
                fontSize: compact ? 10 : 12,
                fontWeight: FontWeight.bold,
              ),
            ),
          ],
        ),
      );
    }

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
      decoration: BoxDecoration(
        gradient: LinearGradient(
          colors: [
            color.withOpacity(0.25),
            color.withOpacity(0.1),
          ],
        ),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(
          color: color.withOpacity(0.4),
          width: 1.5,
        ),
        boxShadow: [
          BoxShadow(
            color: color.withOpacity(0.2),
            blurRadius: 6,
            spreadRadius: 0,
          ),
        ],
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          const StreakIcon(type: StreakIconType.fire, size: 14),
          const SizedBox(width: 4),
          Text(
            '$streakDays',
            style: TextStyle(
              color: color,
              fontSize: 14,
              fontWeight: FontWeight.bold,
            ),
          ),
          if (showLabel) ...[
            const SizedBox(width: 2),
            Text(
              'ngày',
              style: TextStyle(
                color: Colors.white.withOpacity(0.6),
                fontSize: 11,
              ),
            ),
          ],
        ],
      ),
    );
  }
}

/// Animated streak badge with glow effect for top players
class AnimatedStreakBadge extends StatefulWidget {
  final int streakDays;

  const AnimatedStreakBadge({
    super.key,
    required this.streakDays,
  });

  @override
  State<AnimatedStreakBadge> createState() => _AnimatedStreakBadgeState();
}

class _AnimatedStreakBadgeState extends State<AnimatedStreakBadge>
    with SingleTickerProviderStateMixin {
  late AnimationController _controller;
  late Animation<double> _glowAnimation;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      duration: const Duration(milliseconds: 1500),
      vsync: this,
    );
    _glowAnimation = Tween<double>(begin: 0.3, end: 0.7).animate(
      CurvedAnimation(parent: _controller, curve: Curves.easeInOut),
    );
    _controller.repeat(reverse: true);
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  Color _getStreakColor() {
    if (widget.streakDays >= 365) return AppColors.xpGold;
    if (widget.streakDays >= 100) return Colors.purple;
    if (widget.streakDays >= 30) return Colors.blue;
    if (widget.streakDays >= 7) return Colors.green;
    return AppColors.streakOrange;
  }

  @override
  Widget build(BuildContext context) {
    if (widget.streakDays <= 0) {
      return const SizedBox.shrink();
    }

    final color = _getStreakColor();

    return AnimatedBuilder(
      animation: _glowAnimation,
      builder: (context, child) {
        return Container(
          padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
          decoration: BoxDecoration(
            gradient: LinearGradient(
              colors: [
                color.withOpacity(0.3),
                color.withOpacity(0.15),
              ],
            ),
            borderRadius: BorderRadius.circular(14),
            border: Border.all(
              color: color.withOpacity(0.5),
              width: 2,
            ),
            boxShadow: [
              BoxShadow(
                color: color.withOpacity(_glowAnimation.value),
                blurRadius: 12,
                spreadRadius: 2,
              ),
            ],
          ),
          child: Row(
            mainAxisSize: MainAxisSize.min,
            children: [
              const StreakIcon(type: StreakIconType.fire, size: 18),
              const SizedBox(width: 6),
              Text(
                '${widget.streakDays}',
                style: TextStyle(
                  color: color,
                  fontSize: 18,
                  fontWeight: FontWeight.bold,
                ),
              ),
              const SizedBox(width: 4),
              Text(
                'ngày',
                style: TextStyle(
                  color: Colors.white.withOpacity(0.7),
                  fontSize: 12,
                ),
              ),
            ],
          ),
        );
      },
    );
  }
}

