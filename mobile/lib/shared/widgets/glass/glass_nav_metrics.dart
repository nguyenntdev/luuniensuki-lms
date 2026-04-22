import 'package:flutter/widgets.dart';

/// Shared geometry for the floating glass bottom navigation.
abstract class GlassNavMetrics {
  GlassNavMetrics._();

  static const double barHeight = 64;
  static const double horizontalMargin = 16;
  static const double floatingBottomGap = 8;
  static const double contentClearance = 16;

  static double safeBottom(BuildContext context) =>
      MediaQuery.viewPaddingOf(context).bottom;

  static bool isKeyboardVisible(BuildContext context) =>
      MediaQuery.viewInsetsOf(context).bottom > 0;

  static double barBottomOffset(BuildContext context) =>
      safeBottom(context) + floatingBottomGap;

  static double contentInset(BuildContext context, {double extra = 0}) {
    if (isKeyboardVisible(context)) {
      return extra;
    }
    return barHeight + contentClearance + barBottomOffset(context) + extra;
  }
}
