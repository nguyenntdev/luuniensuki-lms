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
/// Uses emoji owl 🦉 as placeholder (can be replaced with custom assets)
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

  String _getEmoji() {
    switch (widget.expression) {
      case MascotExpression.happy:
        return '🦉';
      case MascotExpression.sad:
        return '😢';
      case MascotExpression.encouraging:
        return '💪';
      case MascotExpression.celebrating:
        return '🎉';
      case MascotExpression.worried:
        return '😟';
      case MascotExpression.excited:
        return '🤩';
      case MascotExpression.neutral:
        return '🦉';
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
      child: Text(
        _getEmoji(),
        style: TextStyle(fontSize: widget.size),
      ),
    );
  }
}

