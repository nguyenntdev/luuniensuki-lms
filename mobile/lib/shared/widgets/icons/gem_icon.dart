import 'package:flutter/material.dart';
import '../../../core/theme/app_colors.dart';

/// Gem icon widget to replace 💎 emoji usage
/// Provides Material Design diamond icon with proper styling
class GemIcon extends StatelessWidget {
  final double size;
  final Color? color;
  final bool showGlow;

  const GemIcon({
    super.key,
    this.size = 24,
    this.color,
    this.showGlow = false,
  });

  @override
  Widget build(BuildContext context) {
    final iconColor = color ?? AppColors.gemYellow;

    return Container(
      width: size,
      height: size,
      decoration: showGlow
          ? BoxDecoration(
              shape: BoxShape.circle,
              boxShadow: [
                BoxShadow(
                  color: iconColor.withOpacity(0.3),
                  blurRadius: 8,
                  spreadRadius: 1,
                ),
              ],
            )
          : null,
      child: Icon(
        Icons.diamond_rounded,
        size: size,
        color: iconColor,
      ),
    );
  }
}

