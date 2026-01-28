import 'dart:math';
import 'package:flutter/material.dart';
import '../../../core/theme/app_colors.dart';

/// Circular progress badge with animated progress arc and icon in center.
class CircularProgressBadge extends StatefulWidget {
  final double progress;
  final Color? progressColor;
  final Color? backgroundColor;
  final IconData icon;
  final double size;
  final double strokeWidth;
  final bool animated;
  final Duration animationDuration;

  const CircularProgressBadge({
    super.key,
    required this.progress,
    this.progressColor,
    this.backgroundColor,
    required this.icon,
    this.size = 48,
    this.strokeWidth = 4,
    this.animated = true,
    this.animationDuration = const Duration(milliseconds: 800),
  });

  @override
  State<CircularProgressBadge> createState() => _CircularProgressBadgeState();
}

class _CircularProgressBadgeState extends State<CircularProgressBadge>
    with SingleTickerProviderStateMixin {
  late AnimationController _animationController;
  late Animation<double> _progressAnimation;

  @override
  void initState() {
    super.initState();
    _animationController = AnimationController(
      duration: widget.animationDuration,
      vsync: this,
    );

    _progressAnimation = Tween<double>(
      begin: 0.0,
      end: widget.progress.clamp(0.0, 1.0),
    ).animate(
      CurvedAnimation(
        parent: _animationController,
        curve: Curves.easeOutCubic,
      ),
    );

    if (widget.animated) {
      _animationController.forward();
    } else {
      _animationController.value = 1.0;
    }
  }

  @override
  void didUpdateWidget(CircularProgressBadge oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.progress != widget.progress) {
      _progressAnimation = Tween<double>(
        begin: _progressAnimation.value,
        end: widget.progress.clamp(0.0, 1.0),
      ).animate(
        CurvedAnimation(
          parent: _animationController,
          curve: Curves.easeOutCubic,
        ),
      );
      _animationController.forward(from: 0.0);
    }
  }

  @override
  void dispose() {
    _animationController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final progressColor = widget.progressColor ?? AppColors.primary;
    final backgroundColor = widget.backgroundColor ?? Colors.white.withOpacity(0.12);
    final isCompleted = widget.progress >= 1.0;

    return SizedBox(
      width: widget.size,
      height: widget.size,
      child: Stack(
        alignment: Alignment.center,
        children: [
          if (isCompleted)
            Container(
              width: widget.size,
              height: widget.size,
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                boxShadow: [
                  BoxShadow(
                    color: progressColor.withOpacity(0.4),
                    blurRadius: 16,
                    spreadRadius: 2,
                  ),
                ],
              ),
            ),
          AnimatedBuilder(
            animation: _progressAnimation,
            builder: (context, child) {
              return CustomPaint(
                size: Size(widget.size, widget.size),
                painter: _CircularProgressPainter(
                  progress: _progressAnimation.value,
                  color: progressColor,
                  backgroundColor: backgroundColor,
                  strokeWidth: widget.strokeWidth,
                ),
              );
            },
          ),
          Icon(
            widget.icon,
            color: isCompleted ? Colors.white : progressColor,
            size: widget.size * 0.45,
          ),
        ],
      ),
    );
  }
}

class _CircularProgressPainter extends CustomPainter {
  final double progress;
  final Color color;
  final Color backgroundColor;
  final double strokeWidth;

  _CircularProgressPainter({
    required this.progress,
    required this.color,
    required this.backgroundColor,
    required this.strokeWidth,
  });

  @override
  void paint(Canvas canvas, Size size) {
    final center = Offset(size.width / 2, size.height / 2);
    final radius = (size.width - strokeWidth) / 2;

    final backgroundPaint = Paint()
      ..color = backgroundColor
      ..strokeWidth = strokeWidth
      ..style = PaintingStyle.stroke
      ..strokeCap = StrokeCap.round;

    canvas.drawCircle(center, radius, backgroundPaint);

    if (progress > 0) {
      final rect = Rect.fromCircle(center: center, radius: radius);

      final gradient = SweepGradient(
        colors: [
          AppColors.primary,
          AppColors.primaryLight,
          AppColors.primary,
        ],
        stops: const [0.0, 0.5, 1.0],
        startAngle: -pi / 2,
        endAngle: -pi / 2 + (2 * pi * progress),
      );

      final progressPaint = Paint()
        ..shader = gradient.createShader(rect)
        ..strokeWidth = strokeWidth
        ..style = PaintingStyle.stroke
        ..strokeCap = StrokeCap.round;

      final startAngle = -pi / 2;
      final sweepAngle = 2 * pi * progress;

      canvas.drawArc(
        rect,
        startAngle,
        sweepAngle,
        false,
        progressPaint,
      );
    }
  }

  @override
  bool shouldRepaint(_CircularProgressPainter oldDelegate) {
    return oldDelegate.progress != progress ||
        oldDelegate.color != color ||
        oldDelegate.backgroundColor != backgroundColor ||
        oldDelegate.strokeWidth != strokeWidth;
  }
}
  
