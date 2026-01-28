import 'package:flutter/material.dart';

import '../../../core/theme/app_colors.dart';

/// A widget that displays text with a gradient effect.
///
/// This widget uses [ShaderMask] to apply a gradient shader to the text,
/// creating a smooth color transition effect.
///
/// Example usage:
/// ```dart
/// GradientText(
///   '1,250 XP',
///   style: TextStyle(fontSize: 24, fontWeight: FontWeight.bold),
///   gradient: AppColors.primaryGradient,
/// )
/// ```
class GradientText extends StatelessWidget {
  /// The text to display
  final String text;

  /// The text style to apply
  final TextStyle? style;

  /// The gradient to use for the text color
  final Gradient gradient;

  /// The text alignment
  final TextAlign? textAlign;

  /// Maximum number of lines
  final int? maxLines;

  /// How to handle text overflow
  final TextOverflow? overflow;

  const GradientText(
    this.text, {
    super.key,
    this.style,
    this.gradient = AppColors.primaryGradient,
    this.textAlign,
    this.maxLines,
    this.overflow,
  });

  /// Creates a gradient text with the gold accent gradient
  factory GradientText.gold(
    String text, {
    TextStyle? style,
    TextAlign? textAlign,
    int? maxLines,
    TextOverflow? overflow,
  }) {
    return GradientText(
      text,
      style: style,
      gradient: AppColors.primaryGradient,
      textAlign: textAlign,
      maxLines: maxLines,
      overflow: overflow,
    );
  }

  /// Creates a gradient text with the XP gold gradient
  factory GradientText.xp(
    String text, {
    TextStyle? style,
    TextAlign? textAlign,
    int? maxLines,
    TextOverflow? overflow,
  }) {
    return GradientText(
      text,
      style: style,
      gradient: AppColors.xpGradient,
      textAlign: textAlign,
      maxLines: maxLines,
      overflow: overflow,
    );
  }

  @override
  Widget build(BuildContext context) {
    return ShaderMask(
      blendMode: BlendMode.srcIn,
      shaderCallback: (bounds) => gradient.createShader(
        Rect.fromLTWH(0, 0, bounds.width, bounds.height),
      ),
      child: Text(
        text,
        style: style,
        textAlign: textAlign,
        maxLines: maxLines,
        overflow: overflow,
      ),
    );
  }
}

