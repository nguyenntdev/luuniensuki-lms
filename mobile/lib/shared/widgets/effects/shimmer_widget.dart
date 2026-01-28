import 'dart:math' as math;

import 'package:flutter/material.dart';

class ShimmerWidget extends StatefulWidget {
  final Widget child;
  final Duration duration;
  final LinearGradient? gradient;
  final bool enabled;

  const ShimmerWidget({
    super.key,
    required this.child,
    this.duration = const Duration(seconds: 2),
    this.gradient,
    this.enabled = true,
  });

  @override
  State<ShimmerWidget> createState() => _ShimmerWidgetState();
}

class _ShimmerWidgetState extends State<ShimmerWidget>
    with SingleTickerProviderStateMixin {
  late AnimationController _controller;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      vsync: this,
      duration: widget.duration,
    );

    if (widget.enabled) {
      _controller.repeat();
    }
  }

  @override
  void didUpdateWidget(ShimmerWidget oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (widget.enabled != oldWidget.enabled) {
      if (widget.enabled) {
        _controller.repeat();
      } else {
        _controller.stop();
      }
    }
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    if (!widget.enabled) {
      return widget.child;
    }

    return AnimatedBuilder(
      animation: _controller,
      builder: (context, child) {
        return ShaderMask(
          shaderCallback: (bounds) {
            final gradient = widget.gradient ??
                LinearGradient(
                  colors: [
                    Colors.white.withOpacity(0.0),
                    Colors.white.withOpacity(0.3),
                    Colors.white.withOpacity(0.5),
                    Colors.white.withOpacity(0.3),
                    Colors.white.withOpacity(0.0),
                  ],
                  stops: const [0.0, 0.35, 0.5, 0.65, 1.0],
                  begin: Alignment.topLeft,
                  end: Alignment.bottomRight,
                );

            final translateX = bounds.width * 2 * _controller.value;
            final translateY = bounds.height * 2 * _controller.value;

            return gradient.createShader(
              Rect.fromLTWH(
                -bounds.width + translateX,
                -bounds.height + translateY,
                bounds.width * 3,
                bounds.height * 3,
              ),
            );
          },
          blendMode: BlendMode.srcATop,
          child: child,
        );
      },
      child: widget.child,
    );
  }
}

class PulsingGlowWidget extends StatefulWidget {
  final Widget child;
  final Color glowColor;
  final double maxBlurRadius;
  final double minBlurRadius;
  final Duration duration;
  final bool enabled;

  const PulsingGlowWidget({
    super.key,
    required this.child,
    this.glowColor = Colors.amber,
    this.maxBlurRadius = 16.0,
    this.minBlurRadius = 4.0,
    this.duration = const Duration(seconds: 2),
    this.enabled = true,
  });

  @override
  State<PulsingGlowWidget> createState() => _PulsingGlowWidgetState();
}

class _PulsingGlowWidgetState extends State<PulsingGlowWidget>
    with SingleTickerProviderStateMixin {
  late AnimationController _controller;
  late Animation<double> _animation;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      vsync: this,
      duration: widget.duration,
    );

    _animation = Tween<double>(
      begin: widget.minBlurRadius,
      end: widget.maxBlurRadius,
    ).animate(CurvedAnimation(
      parent: _controller,
      curve: Curves.easeInOut,
    ));

    if (widget.enabled) {
      _controller.repeat(reverse: true);
    }
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    if (!widget.enabled) {
      return widget.child;
    }

    return AnimatedBuilder(
      animation: _animation,
      builder: (context, child) {
        return Container(
          decoration: BoxDecoration(
            boxShadow: [
              BoxShadow(
                color: widget.glowColor.withOpacity(0.5),
                blurRadius: _animation.value,
                spreadRadius: _animation.value / 4,
              ),
            ],
          ),
          child: child,
        );
      },
      child: widget.child,
    );
  }
}

