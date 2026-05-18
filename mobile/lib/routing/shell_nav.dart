import 'package:flutter/material.dart';
import '../shared/widgets/glass/glass_nav_metrics.dart';

abstract class ShellNavMetrics {
  ShellNavMetrics._();

  static const double navHeight = GlassNavMetrics.barHeight;
  static const double navMargin = GlassNavMetrics.horizontalMargin;

  static double inset(BuildContext context, {double extra = 0}) {
    return GlassNavMetrics.contentInset(context, extra: extra);
  }
}
