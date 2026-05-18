import 'package:flutter/material.dart';
import '../../../core/theme/app_colors.dart';

/// Streak icon widget to replace emoji usage
/// Provides fire, freeze, and warning icons with proper styling
class StreakIcon extends StatelessWidget {
  final StreakIconType type;
  final double size;
  final bool showGlow;

  const StreakIcon({
    super.key,
    required this.type,
    this.size = 24,
    this.showGlow = false,
  });

  @override
  Widget build(BuildContext context) {
    final config = _getIconConfig(type);

    return Container(
      width: size,
      height: size,
      decoration: showGlow
          ? BoxDecoration(
              shape: BoxShape.circle,
              boxShadow: [
                BoxShadow(
                  color: config.color.withOpacity(0.3),
                  blurRadius: 8,
                  spreadRadius: 1,
                ),
              ],
            )
          : null,
      child: Icon(
        config.icon,
        size: size,
        color: config.color,
      ),
    );
  }

  _StreakIconConfig _getIconConfig(StreakIconType type) {
    switch (type) {
      case StreakIconType.fire:
        return const _StreakIconConfig(
          icon: Icons.local_fire_department_rounded,
          color: AppColors.streakOrange,
        );
      case StreakIconType.freeze:
        return const _StreakIconConfig(
          icon: Icons.ac_unit_rounded,
          color: Colors.lightBlue,
        );
      case StreakIconType.warning:
        return const _StreakIconConfig(
          icon: Icons.warning_rounded,
          color: Colors.red,
        );
    }
  }
}

enum StreakIconType {
  fire,
  freeze,
  warning,
}

class _StreakIconConfig {
  final IconData icon;
  final Color color;

  const _StreakIconConfig({
    required this.icon,
    required this.color,
  });
}

