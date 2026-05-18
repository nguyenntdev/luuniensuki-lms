import 'package:flutter/material.dart';

import '../../../core/theme/app_colors.dart';

/// An animated gradient background with smooth color transitions
/// Creates a dynamic glassmorphism backdrop
class AnimatedGradientBackground extends StatefulWidget {
  final Widget child;
  final Duration duration;
  final List<Color>? colors;

  const AnimatedGradientBackground({
    super.key,
    required this.child,
    this.duration = const Duration(seconds: 10),
    this.colors,
  });

  @override
  State<AnimatedGradientBackground> createState() =>
      _AnimatedGradientBackgroundState();
}

class _AnimatedGradientBackgroundState
    extends State<AnimatedGradientBackground>
    with SingleTickerProviderStateMixin {
  late AnimationController _controller;

  // Default gradient colors - Imperial dark core with warm neutral depth
  static const _defaultColors = [
    AppColors.background,
    AppColors.surface,
    AppColors.surfaceElevated,
    AppColors.surfaceVariant,
  ];

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      duration: widget.duration,
      vsync: this,
    )..repeat(reverse: true);
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final colors = widget.colors ?? _defaultColors;

    return AnimatedBuilder(
      animation: _controller,
      builder: (context, child) {
        return Container(
          decoration: BoxDecoration(
            gradient: LinearGradient(
              begin: Alignment.topLeft,
              end: Alignment.bottomRight,
              colors: [
                Color.lerp(
                  colors[0],
                  colors[2],
                  _controller.value,
                )!,
                Color.lerp(
                  colors[1],
                  colors[0],
                  _controller.value,
                )!,
                Color.lerp(
                  colors[2],
                  colors[1],
                  _controller.value,
                )!,
                Color.lerp(
                  colors[3 % colors.length],
                  colors[2],
                  _controller.value,
                )!,
              ],
            ),
          ),
          child: widget.child,
        );
      },
    );
  }
}

/// A static gradient background (no animation)
/// Useful for better performance when animation is not needed
class GradientBackground extends StatelessWidget {
  final Widget child;
  final List<Color>? colors;
  final AlignmentGeometry? begin;
  final AlignmentGeometry? end;

  const GradientBackground({
    super.key,
    required this.child,
    this.colors,
    this.begin,
    this.end,
  });

  static const defaultColors = [
    AppColors.background,
    AppColors.surface,
    AppColors.surfaceElevated,
    AppColors.surfaceVariant,
  ];

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: BoxDecoration(
        gradient: LinearGradient(
          begin: begin ?? Alignment.topLeft,
          end: end ?? Alignment.bottomRight,
          colors: colors ?? defaultColors,
        ),
      ),
      child: child,
    );
  }
}

/// Background with floating particles/orbs for extra depth
class ParticleBackground extends StatefulWidget {
  final Widget child;
  final int particleCount;
  final Color particleColor;

  const ParticleBackground({
    super.key,
    required this.child,
    this.particleCount = 20,
    this.particleColor = const Color(0x1AFFFFFF),
  });

  @override
  State<ParticleBackground> createState() => _ParticleBackgroundState();
}

class _ParticleBackgroundState extends State<ParticleBackground>
    with TickerProviderStateMixin {
  late List<AnimationController> _controllers;
  late List<Animation<Offset>> _animations;

  @override
  void initState() {
    super.initState();
    _controllers = List.generate(
      widget.particleCount,
      (index) => AnimationController(
        duration: Duration(seconds: 10 + (index % 5)),
        vsync: this,
      )..repeat(reverse: true),
    );

    _animations = _controllers.map((controller) {
      return Tween<Offset>(
        begin: Offset.zero,
        end: Offset(0.2, 0.2),
      ).animate(CurvedAnimation(
        parent: controller,
        curve: Curves.easeInOut,
      ));
    }).toList();
  }

  @override
  void dispose() {
    for (var controller in _controllers) {
      controller.dispose();
    }
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Stack(
      children: [
        // Background gradient
        const GradientBackground(child: SizedBox.expand()),

        // Floating particles
        ...List.generate(widget.particleCount, (index) {
          return AnimatedBuilder(
            animation: _animations[index],
            builder: (context, child) {
              return Positioned(
                left: (index * 50.0) % MediaQuery.of(context).size.width,
                top: (index * 80.0) % MediaQuery.of(context).size.height,
                child: Transform.translate(
                  offset: _animations[index].value * 100,
                  child: Container(
                    width: 60 + (index % 3) * 20,
                    height: 60 + (index % 3) * 20,
                    decoration: BoxDecoration(
                      shape: BoxShape.circle,
                      color: widget.particleColor,
                      boxShadow: [
                        BoxShadow(
                          color: widget.particleColor,
                          blurRadius: 20,
                          spreadRadius: 10,
                        ),
                      ],
                    ),
                  ),
                ),
              );
            },
          );
        }),

        // Content on top
        widget.child,
      ],
    );
  }
}
