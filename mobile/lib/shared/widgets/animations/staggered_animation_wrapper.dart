import 'package:flutter/material.dart';

/// Reusable staggered animation wrapper for list items.
/// Provides fade + slide-up animation with configurable delay per index.
class StaggeredAnimationWrapper extends StatefulWidget {
  final int index;
  final Widget child;
  final Duration animationDuration;
  final Duration staggerDelay;
  final Offset slideOffset;
  final Curve curve;

  const StaggeredAnimationWrapper({
    super.key,
    required this.index,
    required this.child,
    this.animationDuration = const Duration(milliseconds: 400),
    this.staggerDelay = const Duration(milliseconds: 100),
    this.slideOffset = const Offset(0, 0.3),
    this.curve = Curves.easeOutCubic,
  });

  @override
  State<StaggeredAnimationWrapper> createState() =>
      _StaggeredAnimationWrapperState();
}

class _StaggeredAnimationWrapperState extends State<StaggeredAnimationWrapper>
    with SingleTickerProviderStateMixin {
  late AnimationController _controller;
  late Animation<double> _fadeAnimation;
  late Animation<Offset> _slideAnimation;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      duration: widget.animationDuration,
      vsync: this,
    );

    _fadeAnimation = Tween<double>(begin: 0.0, end: 1.0).animate(
      CurvedAnimation(parent: _controller, curve: widget.curve),
    );

    _slideAnimation = Tween<Offset>(
      begin: widget.slideOffset,
      end: Offset.zero,
    ).animate(
      CurvedAnimation(parent: _controller, curve: widget.curve),
    );

    Future.delayed(
      Duration(milliseconds: widget.staggerDelay.inMilliseconds * widget.index),
      () {
        if (mounted) _controller.forward();
      },
    );
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return FadeTransition(
      opacity: _fadeAnimation,
      child: SlideTransition(
        position: _slideAnimation,
        child: widget.child,
      ),
    );
  }
}

