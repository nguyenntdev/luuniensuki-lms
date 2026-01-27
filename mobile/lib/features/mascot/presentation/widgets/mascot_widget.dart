import 'package:flutter/material.dart';

/// Mascot expressions
enum MascotExpression {
  happy,
  sad,
  encouraging,
  celebrating,
  worried,
  excited,
  neutral,
}

/// Mascot widget similar to Duolingo's Duo owl
/// Uses Material Icons for expressions
class MascotWidget extends StatefulWidget {
  final MascotExpression expression;
  final double size;
  final bool animate;

  const MascotWidget({
    super.key,
    this.expression = MascotExpression.happy,
    this.size = 80,
    this.animate = true,
  });

  @override
  State<MascotWidget> createState() => _MascotWidgetState();
}

class _MascotWidgetState extends State<MascotWidget>
    with SingleTickerProviderStateMixin {
  late AnimationController _controller;
  late Animation<double> _bounceAnimation;
  late Animation<double> _rotationAnimation;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      duration: const Duration(milliseconds: 1500),
      vsync: this,
    );

    _bounceAnimation = TweenSequence<double>([
      TweenSequenceItem(
        tween: Tween(begin: 0.0, end: -10.0)
            .chain(CurveTween(curve: Curves.easeOut)),
        weight: 25,
      ),
      TweenSequenceItem(
        tween: Tween(begin: -10.0, end: 0.0)
            .chain(CurveTween(curve: Curves.bounceOut)),
        weight: 75,
      ),
    ]).animate(_controller);

    _rotationAnimation = TweenSequence<double>([
      TweenSequenceItem(
        tween: Tween(begin: 0.0, end: 0.1),
        weight: 25,
      ),
      TweenSequenceItem(
        tween: Tween(begin: 0.1, end: -0.1),
        weight: 25,
      ),
      TweenSequenceItem(
        tween: Tween(begin: -0.1, end: 0.1),
        weight: 25,
      ),
      TweenSequenceItem(
        tween: Tween(begin: 0.1, end: 0.0),
        weight: 25,
      ),
    ]).animate(_controller);

    if (widget.animate) {
      _controller.repeat(period: const Duration(seconds: 3));
    }
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  void didUpdateWidget(MascotWidget oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (widget.animate != oldWidget.animate) {
      if (widget.animate) {
        _controller.repeat(period: const Duration(seconds: 3));
      } else {
        _controller.stop();
      }
    }
  }

  IconData _getIcon() {
    switch (widget.expression) {
      case MascotExpression.happy:
        return Icons.sentiment_very_satisfied_rounded;
      case MascotExpression.sad:
        return Icons.sentiment_dissatisfied_rounded;
      case MascotExpression.encouraging:
        return Icons.fitness_center_rounded;
      case MascotExpression.celebrating:
        return Icons.celebration_rounded;
      case MascotExpression.worried:
        return Icons.sentiment_dissatisfied_rounded;
      case MascotExpression.excited:
        return Icons.sentiment_very_satisfied_rounded;
      case MascotExpression.neutral:
        return Icons.sentiment_satisfied_rounded;
    }
  }

  Color _getIconColor() {
    switch (widget.expression) {
      case MascotExpression.happy:
        return const Color(0xFFFFD700); // Gold
      case MascotExpression.sad:
        return const Color(0xFF6E9AC4); // Blue
      case MascotExpression.encouraging:
        return const Color(0xFFFF6B6B); // Red
      case MascotExpression.celebrating:
        return const Color(0xFFFF8C00); // Orange
      case MascotExpression.worried:
        return const Color(0xFF9B9B9B); // Gray
      case MascotExpression.excited:
        return const Color(0xFFFFD700); // Gold
      case MascotExpression.neutral:
        return const Color(0xFFB8B8B8); // Light Gray
    }
  }

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: _controller,
      builder: (context, child) {
        return Transform.translate(
          offset: widget.animate
              ? Offset(0, _bounceAnimation.value)
              : Offset.zero,
          child: Transform.rotate(
            angle: widget.animate ? _rotationAnimation.value : 0,
            child: child,
          ),
        );
      },
      child: Icon(
        _getIcon(),
        size: widget.size,
        color: _getIconColor(),
      ),
    );
  }
}

