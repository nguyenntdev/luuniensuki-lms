import 'package:flutter/material.dart';

/// Centralized spacing constants for consistent UI
class AppSpacing {
  // Base spacing scale
  static const double xs = 4.0;
  static const double sm = 8.0;
  static const double md = 16.0;
  static const double lg = 24.0;
  static const double xl = 32.0;
  static const double xxl = 48.0;

  // Common padding values
  static const EdgeInsets screenPadding = EdgeInsets.all(md);
  static const EdgeInsets cardPadding = EdgeInsets.all(md);
  static const EdgeInsets buttonPadding = EdgeInsets.symmetric(horizontal: lg, vertical: md);

  // Vertical spacing
  static const SizedBox verticalSpaceXS = SizedBox(height: xs);
  static const SizedBox verticalSpaceSM = SizedBox(height: sm);
  static const SizedBox verticalSpaceMD = SizedBox(height: md);
  static const SizedBox verticalSpaceLG = SizedBox(height: lg);
  static const SizedBox verticalSpaceXL = SizedBox(height: xl);
  static const SizedBox verticalSpaceXXL = SizedBox(height: xxl);

  // Horizontal spacing
  static const SizedBox horizontalSpaceXS = SizedBox(width: xs);
  static const SizedBox horizontalSpaceSM = SizedBox(width: sm);
  static const SizedBox horizontalSpaceMD = SizedBox(width: md);
  static const SizedBox horizontalSpaceLG = SizedBox(width: lg);
  static const SizedBox horizontalSpaceXL = SizedBox(width: xl);
  static const SizedBox horizontalSpaceXXL = SizedBox(width: xxl);

  // Border radius
  static const double radiusXS = 4.0;
  static const double radiusSM = 8.0;
  static const double radiusMD = 12.0;
  static const double radiusLG = 16.0;
  static const double radiusXL = 24.0;
  static const double radiusRound = 999.0;

  // Icon sizes
  static const double iconXS = 16.0;
  static const double iconSM = 20.0;
  static const double iconMD = 24.0;
  static const double iconLG = 32.0;
  static const double iconXL = 48.0;
}

