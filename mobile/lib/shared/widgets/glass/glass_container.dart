import 'dart:ui';

import 'package:flutter/material.dart';

import '../../../core/theme/app_colors.dart';

/// A container with glassmorphism styling
/// Uses semi-transparent background without BackdropFilter to avoid layout issues
class GlassContainer extends StatelessWidget {
  final Widget child;
  final double opacity;
  final double blurSigma;
  final bool enableBackdropBlur;
  final BorderRadius? borderRadius;
  final EdgeInsets? padding;
  final Border? border;
  final Gradient? gradient;
  final List<BoxShadow>? boxShadow;

  const GlassContainer({
    super.key,
    required this.child,
    this.opacity = 0.1,
    this.blurSigma = 16,
    this.enableBackdropBlur = true,
    this.borderRadius,
    this.padding,
    this.border,
    this.gradient,
    this.boxShadow,
  });

  @override
  Widget build(BuildContext context) {
    final effectiveBorderRadius = borderRadius ?? BorderRadius.circular(20);
    final effectiveBorder = border ??
        Border.all(
          color: AppColors.glassBorder,
          width: 1.5,
        );
    final effectiveShadow = boxShadow ??
        [
          BoxShadow(
            color: AppColors.black.withOpacity(0.25),
            blurRadius: 24,
            offset: const Offset(0, 12),
          ),
        ];

    return Container(
      decoration: BoxDecoration(
        borderRadius: effectiveBorderRadius,
        boxShadow: effectiveShadow,
      ),
      child: ClipRRect(
        borderRadius: effectiveBorderRadius,
        child: Stack(
          children: [
            if (enableBackdropBlur)
              Positioned.fill(
                child: BackdropFilter(
                  filter: ImageFilter.blur(
                    sigmaX: blurSigma,
                    sigmaY: blurSigma,
                  ),
                  child: const SizedBox.expand(),
                ),
              ),
            Positioned.fill(
              child: DecoratedBox(
                decoration: BoxDecoration(
                  gradient: gradient,
                  color: gradient == null
                      ? AppColors.glassWhite.withOpacity(opacity)
                      : null,
                  borderRadius: effectiveBorderRadius,
                  border: effectiveBorder,
                ),
              ),
            ),
            Positioned.fill(
              child: IgnorePointer(
                child: DecoratedBox(
                  decoration: BoxDecoration(
                    gradient: LinearGradient(
                      begin: Alignment.topLeft,
                      end: Alignment.bottomRight,
                      colors: [
                        Colors.white.withOpacity(opacity * 0.95),
                        Colors.white.withOpacity(opacity * 0.45),
                        Colors.transparent,
                      ],
                      stops: const [0.0, 0.22, 0.7],
                    ),
                  ),
                ),
              ),
            ),
            Padding(
              padding: padding ?? const EdgeInsets.all(20),
              child: child,
            ),
          ],
        ),
      ),
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
      opacity: 0.11,
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
