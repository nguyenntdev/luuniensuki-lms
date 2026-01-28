import 'package:flutter/material.dart';

class AnimatedPathConnector extends StatefulWidget {
  final bool isLocked;
  final bool isCompleted;
  final bool isActive;
  final double height;
  final Color? activeColor;

  const AnimatedPathConnector({
    super.key,
    this.isLocked = false,
    this.isCompleted = false,
    this.isActive = false,
    this.height = 36,
    this.activeColor,
  });

  @override
  State<AnimatedPathConnector> createState() => _AnimatedPathConnectorState();
}

class _AnimatedPathConnectorState extends State<AnimatedPathConnector>
    with SingleTickerProviderStateMixin {
  late AnimationController _controller;
  late Animation<double> _animation;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      duration: const Duration(seconds: 2),
      vsync: this,
    )..repeat();
    _animation = Tween<double>(begin: 0, end: 1).animate(_controller);
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      width: 6,
      height: widget.height,
      margin: const EdgeInsets.only(bottom: 8),
      child: AnimatedBuilder(
        animation: _animation,
        builder: (context, child) {
          return CustomPaint(
            painter: _PathConnectorPainter(
              progress: _animation.value,
              isLocked: widget.isLocked,
              isCompleted: widget.isCompleted,
              isActive: widget.isActive,
              activeColor: widget.activeColor,
            ),
          );
        },
      ),
    );
  }
}

class _PathConnectorPainter extends CustomPainter {
  final double progress;
  final bool isLocked;
  final bool isCompleted;
  final bool isActive;
  final Color? activeColor;

  _PathConnectorPainter({
    required this.progress,
    required this.isLocked,
    required this.isCompleted,
    required this.isActive,
    this.activeColor,
  });

  @override
  void paint(Canvas canvas, Size size) {
    final colors = _getColors();
    final gradient = LinearGradient(
      begin: Alignment.topCenter,
      end: Alignment.bottomCenter,
      colors: colors,
    );

    final rect = Rect.fromLTWH(0, 0, size.width, size.height);
    final rrect = RRect.fromRectAndRadius(rect, const Radius.circular(3));

    final backgroundPaint = Paint()
      ..shader = gradient.createShader(rect)
      ..style = PaintingStyle.fill;

    canvas.drawRRect(rrect, backgroundPaint);

    if (!isLocked) {
      _drawAnimatedDots(canvas, size, colors.first);
    }

    if (isCompleted) {
      _drawGlow(canvas, size, colors.first);
    }
  }

  void _drawAnimatedDots(Canvas canvas, Size size, Color dotColor) {
    final dotPaint = Paint()
      ..color = dotColor.withOpacity(0.8)
      ..style = PaintingStyle.fill;

    const dotCount = 5;
    const dotSize = 2.0;
    final spacing = size.height / (dotCount - 1);

    for (int i = 0; i < dotCount; i++) {
      final baseY = i * spacing;
      final animatedY = (baseY + progress * size.height) % size.height;
      final opacity = 1.0 - (animatedY / size.height) * 0.5;

      dotPaint.color = dotColor.withOpacity(opacity * 0.8);
      canvas.drawCircle(
        Offset(size.width / 2, animatedY),
        dotSize,
        dotPaint,
      );
    }
  }

  void _drawGlow(Canvas canvas, Size size, Color glowColor) {
    final glowPaint = Paint()
      ..color = glowColor.withOpacity(0.3)
      ..maskFilter = const MaskFilter.blur(BlurStyle.normal, 4)
      ..style = PaintingStyle.fill;

    final rect = Rect.fromLTWH(-2, -2, size.width + 4, size.height + 4);
    final rrect = RRect.fromRectAndRadius(rect, const Radius.circular(5));

    canvas.drawRRect(rrect, glowPaint);
  }

  List<Color> _getColors() {
    if (isCompleted) {
      return [
        const Color(0xFF34D399),
        const Color(0xFF34D399).withOpacity(0.5),
      ];
    } else if (isActive) {
      final color = activeColor ?? const Color(0xFFE8B44C);
      return [color.withOpacity(0.6), color.withOpacity(0.3)];
    } else if (isLocked) {
      return [
        Colors.white.withOpacity(0.2),
        Colors.white.withOpacity(0.1),
      ];
    }
    return [
      Colors.white.withOpacity(0.2),
      Colors.white.withOpacity(0.1),
    ];
  }

  @override
  bool shouldRepaint(_PathConnectorPainter oldDelegate) {
    return oldDelegate.progress != progress ||
        oldDelegate.isLocked != isLocked ||
        oldDelegate.isCompleted != isCompleted ||
        oldDelegate.isActive != isActive;
  }
}

