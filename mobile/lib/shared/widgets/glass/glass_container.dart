import 'package:flutter/material.dart';

import '../../../core/theme/app_colors.dart';

/// A container with glassmorphism styling
/// Uses semi-transparent background without BackdropFilter to avoid layout issues
class GlassContainer extends StatelessWidget {
  final Widget child;
  final double opacity;
  final BorderRadius? borderRadius;
  final EdgeInsets? padding;
  final Border? border;
  final Gradient? gradient;
  final List<BoxShadow>? boxShadow;

  const GlassContainer({
    super.key,
    required this.child,
    this.opacity = 0.1,
    this.borderRadius,
    this.padding,
    this.border,
    this.gradient,
    this.boxShadow,
  });

  @override
  Widget build(BuildContext context) {
    final effectiveBorderRadius = borderRadius ?? BorderRadius.circular(20);

    return Container(
      padding: padding ?? const EdgeInsets.all(20),
      decoration: BoxDecoration(
        gradient: gradient,
        color:
            gradient == null ? AppColors.glassWhite.withOpacity(opacity) : null,
        borderRadius: effectiveBorderRadius,
        border: border ??
            Border.all(
              color: AppColors.glassBorder,
              width: 1.5,
            ),
        boxShadow: boxShadow ??
            [
              BoxShadow(
                color: AppColors.black.withOpacity(0.25),
                blurRadius: 24,
                offset: const Offset(0, 12),
              ),
            ],
      ),
      child: child,
    );
  }
}

/// A card variant of GlassContainer with preset styling
class GlassCard extends StatelessWidget {
  final Widget child;
  final EdgeInsets? padding;
  final VoidCallback? onTap;

  const GlassCard({
    super.key,
    required this.child,
    this.padding,
    this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    final container = GlassContainer(
      opacity: 0.08,
      padding: padding ?? const EdgeInsets.all(20),
      child: child,
    );

    if (onTap != null) {
      return Material(
        color: Colors.transparent,
        child: InkWell(
          onTap: onTap,
          borderRadius: BorderRadius.circular(16),
          child: container,
        ),
      );
    }

    return container;
  }
}
