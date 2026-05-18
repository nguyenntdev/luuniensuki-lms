import 'package:flutter/material.dart';
import '../../../core/theme/app_colors.dart';

/// Status icons for motif progress states
/// Replaces emoji usage with Material icons
enum MotifStatus {
  discovered,
  learned,
  mastered,
}

class StatusIcon extends StatelessWidget {
  final MotifStatus status;
  final double size;
  final bool showBackground;

  const StatusIcon({
    super.key,
    required this.status,
    this.size = 16,
    this.showBackground = false,
  });

  @override
  Widget build(BuildContext context) {
    final config = _getStatusConfig(status);

    if (showBackground) {
      return Container(
        width: size * 1.5,
        height: size * 1.5,
        decoration: BoxDecoration(
          color: config.color.withOpacity(0.15),
          borderRadius: BorderRadius.circular(size * 0.25),
        ),
        child: Icon(
          config.icon,
          size: size,
          color: config.color.withOpacity(0.9),
        ),
      );
    }

    return Icon(
      config.icon,
      size: size,
      color: config.color,
    );
  }

  _StatusConfig _getStatusConfig(MotifStatus status) {
    switch (status) {
      case MotifStatus.discovered:
        return const _StatusConfig(
          icon: Icons.visibility_rounded,
          color: AppColors.info,
        );
      case MotifStatus.learned:
        return const _StatusConfig(
          icon: Icons.menu_book_rounded,
          color: AppColors.success,
        );
      case MotifStatus.mastered:
        return const _StatusConfig(
          icon: Icons.star_rounded,
          color: AppColors.primary,
        );
    }
  }
}

class _StatusConfig {
  final IconData icon;
  final Color color;

  const _StatusConfig({
    required this.icon,
    required this.color,
  });
}

