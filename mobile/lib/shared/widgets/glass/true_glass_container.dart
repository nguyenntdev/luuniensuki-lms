import 'dart:ui';
import 'package:flutter/material.dart';
import '../../theme/glass_theme.dart';

/// A true glassmorphism container with BackdropFilter for blur effects.
/// Creates authentic glass effect by blurring content behind the container.
class TrueGlassContainer extends StatelessWidget {
  final Widget child;
  final double blurSigma;
  final double opacity;
  final BorderRadius? borderRadius;
  final EdgeInsets? padding;
  final Color? borderColor;
  final double? borderWidth;
  final List<BoxShadow>? boxShadow;
  final Color? backgroundColor;
  final Gradient? gradient;

  const TrueGlassContainer({
    super.key,
    required this.child,
    this.blurSigma = 10.0,
    this.opacity = 0.1,
    this.borderRadius,
    this.padding,
    this.borderColor,
    this.borderWidth,
    this.boxShadow,
    this.backgroundColor,
    this.gradient,
  });

  @override
  Widget build(BuildContext context) {
    final effectiveBorderRadius =
        borderRadius ?? BorderRadius.circular(GlassTheme.borderRadius);
    final effectiveBorderColor = borderColor ?? GlassTheme.glassBorder;
    final effectiveBorderWidth = borderWidth ?? GlassTheme.borderWidth;

    return ClipRRect(
      borderRadius: effectiveBorderRadius,
      child: BackdropFilter(
        filter: ImageFilter.blur(
          sigmaX: blurSigma,
          sigmaY: blurSigma,
        ),
        child: Container(
          padding: padding ?? const EdgeInsets.all(GlassTheme.spaceL),
          decoration: BoxDecoration(
            gradient: gradient,
            color: gradient == null
                ? (backgroundColor ?? Colors.white.withOpacity(opacity))
                : null,
            borderRadius: effectiveBorderRadius,
            border: Border.all(
              color: effectiveBorderColor,
              width: effectiveBorderWidth,
            ),
            boxShadow: boxShadow ?? GlassTheme.glassShadow,
          ),
          child: child,
        ),
      ),
    );
  }
}

/// Preset variations for common use cases
class TrueGlassCard extends StatelessWidget {
  final Widget child;
  final EdgeInsets? padding;
  final VoidCallback? onTap;

  const TrueGlassCard({
    super.key,
    required this.child,
    this.padding,
    this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    final container = TrueGlassContainer(
      blurSigma: GlassTheme.blurSigma,
      opacity: 0.08,
      padding: padding ?? const EdgeInsets.all(GlassTheme.spaceL),
      child: child,
    );

    if (onTap != null) {
      return Material(
        color: Colors.transparent,
        child: InkWell(
          onTap: onTap,
          borderRadius: BorderRadius.circular(GlassTheme.borderRadius),
          child: container,
        ),
      );
    }

    return container;
  }
}

/// Strong glass variant with more blur and opacity
class TrueGlassContainerStrong extends StatelessWidget {
  final Widget child;
  final EdgeInsets? padding;

  const TrueGlassContainerStrong({
    super.key,
    required this.child,
    this.padding,
  });

  @override
  Widget build(BuildContext context) {
    return TrueGlassContainer(
      blurSigma: GlassTheme.blurSigmaStrong,
      opacity: 0.15,
      borderColor: GlassTheme.glassBorderActive,
      borderWidth: GlassTheme.borderWidthActive,
      boxShadow: GlassTheme.glassShadowStrong,
      padding: padding ?? const EdgeInsets.all(GlassTheme.spaceL),
      child: child,
    );
  }
}

/// Light glass variant with subtle blur
class TrueGlassContainerLight extends StatelessWidget {
  final Widget child;
  final EdgeInsets? padding;

  const TrueGlassContainerLight({
    super.key,
    required this.child,
    this.padding,
  });

  @override
  Widget build(BuildContext context) {
    return TrueGlassContainer(
      blurSigma: GlassTheme.blurSigmaLight,
      opacity: 0.05,
      boxShadow: GlassTheme.glassShadowLight,
      padding: padding ?? const EdgeInsets.all(GlassTheme.spaceL),
      child: child,
    );
  }
}

