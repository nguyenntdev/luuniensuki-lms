import 'package:flutter/material.dart';

import '../../../core/theme/app_colors.dart';
import 'glass_container.dart';

/// Reusable floating app bar with Liquid Glass styling.
class LiquidGlassAppBar extends StatelessWidget {
  final String title;
  final String? subtitle;
  final Widget? leading;
  final List<Widget> actions;
  final EdgeInsetsGeometry? margin;
  final bool compact;

  const LiquidGlassAppBar({
    super.key,
    required this.title,
    this.subtitle,
    this.leading,
    this.actions = const [],
    this.margin,
    this.compact = false,
  });

  @override
  Widget build(BuildContext context) {
    final horizontal = compact ? 14.0 : 16.0;
    final vertical = compact ? 10.0 : 12.0;

    return Padding(
      padding: margin ?? EdgeInsets.zero,
      child: GlassContainer(
        opacity: 0.14,
        blurSigma: 18,
        borderRadius: BorderRadius.circular(20),
        padding:
            EdgeInsets.symmetric(horizontal: horizontal, vertical: vertical),
        child: Row(
          children: [
            if (leading != null) ...[
              leading!,
              const SizedBox(width: 10),
            ],
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                mainAxisSize: MainAxisSize.min,
                children: [
                  Text(
                    title,
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                    style: const TextStyle(
                      color: AppColors.textPrimary,
                      fontSize: 20,
                      fontWeight: FontWeight.w700,
                      letterSpacing: 0.2,
                    ),
                  ),
                  if (subtitle != null && subtitle!.isNotEmpty) ...[
                    const SizedBox(height: 2),
                    Text(
                      subtitle!,
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                      style: TextStyle(
                        color: AppColors.textSecondary.withOpacity(0.92),
                        fontSize: 12,
                        fontWeight: FontWeight.w500,
                      ),
                    ),
                  ],
                ],
              ),
            ),
            if (actions.isNotEmpty) ...[
              const SizedBox(width: 8),
              ...actions,
            ],
          ],
        ),
      ),
    );
  }
}

/// Small icon action tuned for LiquidGlassAppBar.
class LiquidGlassAppBarAction extends StatelessWidget {
  final IconData icon;
  final VoidCallback onTap;
  final String? tooltip;

  const LiquidGlassAppBarAction({
    super.key,
    required this.icon,
    required this.onTap,
    this.tooltip,
  });

  @override
  Widget build(BuildContext context) {
    final actionChild = Material(
      color: Colors.transparent,
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(12),
        child: Container(
          width: 40,
          height: 40,
          decoration: BoxDecoration(
            color: AppColors.glassWhite.withOpacity(0.65),
            borderRadius: BorderRadius.circular(12),
            border: Border.all(
              color: AppColors.glassBorder.withOpacity(0.9),
            ),
          ),
          child: Icon(
            icon,
            color: AppColors.textPrimary,
            size: 20,
          ),
        ),
      ),
    );

    if (tooltip == null || tooltip!.isEmpty) {
      return actionChild;
    }

    return Tooltip(
      message: tooltip!,
      child: actionChild,
    );
  }
}
