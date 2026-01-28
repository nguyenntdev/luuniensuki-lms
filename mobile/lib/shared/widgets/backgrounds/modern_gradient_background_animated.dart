import 'dart:math';
import 'dart:ui';
import 'package:flutter/material.dart';

/// Premium animated background with aurora-like gradient and floating particles
/// Features smooth color transitions, glowing orbs, and subtle noise texture
class ModernGradientBackgroundAnimated extends StatefulWidget {
  final Widget child;
  final int particleCount;
  final bool showNoise;
  final List<Color>? gradientColors;
  final Duration animationDuration;

  const ModernGradientBackgroundAnimated({
    super.key,
    required this.child,
    this.particleCount = 8,
    this.showNoise = true,
    this.gradientColors,
    this.animationDuration = const Duration(seconds: 15),
  });

  @override
  State<ModernGradientBackgroundAnimated> createState() =>
      _ModernGradientBackgroundAnimatedState();
}

class _ModernGradientBackgroundAnimatedState
    extends State<ModernGradientBackgroundAnimated>
    with TickerProviderStateMixin {
  late AnimationController _gradientController;
  late List<_FloatingParticle> _particles;

  @override
  void initState() {
    super.initState();
    
    _gradientController = AnimationController(
      duration: widget.animationDuration,
      vsync: this,
    )..repeat(reverse: true);

    _initializeParticles();
  }

  void _initializeParticles() {
    final random = Random();
    _particles = List.generate(
      widget.particleCount,
      (index) => _FloatingParticle(
        controller: AnimationController(
          duration: Duration(seconds: 12 + random.nextInt(8)),
          vsync: this,
        )..repeat(reverse: true),
        startX: random.nextDouble(),
        startY: random.nextDouble(),
        size: 60.0 + random.nextDouble() * 80,
        opacity: 0.08 + random.nextDouble() * 0.12,
        velocityX: (random.nextDouble() - 0.5) * 0.25,
        velocityY: (random.nextDouble() - 0.5) * 0.25,
        color: _getParticleColor(index, random),
      ),
    );
  }

  Color _getParticleColor(int index, Random random) {
    final colors = widget.gradientColors ??
        [
          const Color(0xFF1A0A2E), // Imperial purple
          const Color(0xFF16213E), // Deep blue
          const Color(0xFFE8B44C), // Gold accent
        ];
    return colors[index % colors.length].withOpacity(0.15);
  }

  @override
  void dispose() {
    _gradientController.dispose();
    for (var particle in _particles) {
      particle.controller.dispose();
    }
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return RepaintBoundary(
      child: Stack(
        children: [
          // Aurora-like animated gradient base
          AnimatedBuilder(
            animation: _gradientController,
            builder: (context, _) => _buildAnimatedGradient(),
          ),

          // Floating particles
          ..._particles.map((particle) => AnimatedBuilder(
                animation: particle.controller,
                builder: (context, _) => _buildParticle(particle),
              )),

          // Subtle noise texture overlay
          if (widget.showNoise)
            Positioned.fill(
              child: _NoiseOverlay(),
            ),

          // Content
          widget.child,
        ],
      ),
    );
  }

  Widget _buildAnimatedGradient() {
    final progress = _gradientController.value;
    final colors = widget.gradientColors ??
        [
          const Color(0xFF1A0A2E),
          const Color(0xFF16213E),
          const Color(0xFF0F1419),
        ];

    return Container(
      decoration: BoxDecoration(
        gradient: RadialGradient(
          center: Alignment(
            -0.8 + (progress * 0.4),
            -0.6 + (progress * 0.3),
          ),
          radius: 1.5,
          colors: [
            Color.lerp(colors[0], colors[1], progress)!,
            Color.lerp(colors[1], colors[2 % colors.length], progress)!,
            colors[2 % colors.length],
          ],
          stops: const [0.0, 0.5, 1.0],
        ),
      ),
      child: Container(
        decoration: BoxDecoration(
          gradient: RadialGradient(
            center: Alignment(
              0.8 - (progress * 0.4),
              0.6 - (progress * 0.3),
            ),
            radius: 1.2,
            colors: [
              const Color(0xFFE8B44C).withOpacity(0.1 * (1 - progress)),
              Colors.transparent,
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildParticle(_FloatingParticle particle) {
    return LayoutBuilder(
      builder: (context, constraints) {
        final progress = particle.controller.value;
        final curve = Curves.easeInOut.transform(progress);

        final x = constraints.maxWidth *
            (particle.startX + particle.velocityX * curve);
        final y = constraints.maxHeight *
            (particle.startY + particle.velocityY * curve);

        return Positioned(
          left: x - particle.size / 2,
          top: y - particle.size / 2,
          child: BackdropFilter(
            filter: ImageFilter.blur(sigmaX: 40, sigmaY: 40),
            child: Container(
              width: particle.size,
              height: particle.size,
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                gradient: RadialGradient(
                  colors: [
                    particle.color.withOpacity(particle.opacity),
                    particle.color.withOpacity(0),
                  ],
                ),
              ),
            ),
          ),
        );
      },
    );
  }
}

/// Data class for floating particle animations
class _FloatingParticle {
  final AnimationController controller;
  final double startX;
  final double startY;
  final double size;
  final double opacity;
  final double velocityX;
  final double velocityY;
  final Color color;

  _FloatingParticle({
    required this.controller,
    required this.startX,
    required this.startY,
    required this.size,
    required this.opacity,
    required this.velocityX,
    required this.velocityY,
    required this.color,
  });
}

/// Subtle noise texture overlay for premium feel
class _NoiseOverlay extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return RepaintBoundary(
      child: CustomPaint(
        painter: _NoisePainter(),
        child: Container(),
      ),
    );
  }
}

class _NoisePainter extends CustomPainter {
  @override
  void paint(Canvas canvas, Size size) {
    final paint = Paint()
      ..color = Colors.white.withOpacity(0.015)
      ..strokeWidth = 1;

    final random = Random(42);

    for (var i = 0; i < 600; i++) {
      final x = random.nextDouble() * size.width;
      final y = random.nextDouble() * size.height;
      final radius = random.nextDouble() * 0.8 + 0.2;
      canvas.drawCircle(Offset(x, y), radius, paint);
    }
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => false;
}

