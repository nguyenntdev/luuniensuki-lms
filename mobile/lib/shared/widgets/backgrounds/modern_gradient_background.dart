import 'dart:math' as math;
import 'dart:ui';
import 'package:flutter/material.dart';

/// Modern gradient background with mesh effect
/// Optimized for performance with RepaintBoundary
/// Color palette: Deep purple (#1a0a2e), Rich blue (#16213e), Warm gold accent (#e8b44c)
class ModernGradientBackground extends StatelessWidget {
  final Widget child;
  final List<Color>? colors;
  final bool showNoise;

  const ModernGradientBackground({
    super.key,
    required this.child,
    this.colors,
    this.showNoise = true,
  });

  static const defaultColors = [
    Color(0xFF1A0A2E), // Deep purple
    Color(0xFF16213E), // Rich blue
    Color(0xFF0F1419), // Dark variant
    Color(0xFF1A0A2E), // Deep purple (loop)
  ];

  @override
  Widget build(BuildContext context) {
    return RepaintBoundary(
      child: Stack(
        children: [
          // Base gradient
          Container(
            decoration: BoxDecoration(
              gradient: RadialGradient(
                center: Alignment.topLeft,
                radius: 1.5,
                colors: colors ?? defaultColors,
                stops: const [0.0, 0.4, 0.7, 1.0],
              ),
            ),
          ),

          // Secondary gradient overlay
          Container(
            decoration: BoxDecoration(
              gradient: RadialGradient(
                center: Alignment.bottomRight,
                radius: 1.2,
                colors: [
                  const Color(0xFF16213E).withOpacity(0.6),
                  Colors.transparent,
                ],
              ),
            ),
          ),

          // Gold accent glow
          Positioned(
            top: -100,
            right: -100,
            child: Container(
              width: 300,
              height: 300,
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                gradient: RadialGradient(
                  colors: [
                    const Color(0xFFE8B44C).withOpacity(0.08),
                    Colors.transparent,
                  ],
                ),
              ),
            ),
          ),

          // Noise texture overlay
          if (showNoise)
            Positioned.fill(
              child: _NoiseOverlay(),
            ),

          // Content
          child,
        ],
      ),
    );
  }
}

/// Subtle noise texture overlay for depth
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
      ..color = Colors.white.withOpacity(0.02)
      ..strokeWidth = 1;

    final random = math.Random(42); // Fixed seed for consistent pattern

    for (var i = 0; i < 500; i++) {
      final x = random.nextDouble() * size.width;
      final y = random.nextDouble() * size.height;
      canvas.drawCircle(Offset(x, y), 0.5, paint);
    }
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => false;
}

/// Animated mesh gradient background
/// Smooth color transitions with performance optimization
class ModernGradientBackgroundMesh extends StatefulWidget {
  final Widget child;
  final Duration duration;
  final bool showNoise;

  const ModernGradientBackgroundMesh({
    super.key,
    required this.child,
    this.duration = const Duration(seconds: 8),
    this.showNoise = true,
  });

  @override
  State<ModernGradientBackgroundMesh> createState() =>
      _ModernGradientBackgroundMeshState();
}

class _ModernGradientBackgroundMeshState
    extends State<ModernGradientBackgroundMesh>
    with SingleTickerProviderStateMixin {
  late AnimationController _controller;

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
    return RepaintBoundary(
      child: AnimatedBuilder(
        animation: _controller,
        builder: (context, _) {
          return Stack(
            children: [
              // Animated mesh gradient
              CustomPaint(
                painter: _MeshGradientPainter(
                  progress: _controller.value,
                ),
                size: Size.infinite,
              ),

              // Gold accent glow - animated
              AnimatedPositioned(
                duration: widget.duration,
                top: -100 + (_controller.value * 50),
                right: -100 + (_controller.value * 30),
                child: Container(
                  width: 300,
                  height: 300,
                  decoration: BoxDecoration(
                    shape: BoxShape.circle,
                    gradient: RadialGradient(
                      colors: [
                        Color.lerp(
                          const Color(0xFFE8B44C),
                          const Color(0xFF16213E),
                          _controller.value,
                        )!.withOpacity(0.1),
                        Colors.transparent,
                      ],
                    ),
                  ),
                ),
              ),

              // Noise overlay
              if (widget.showNoise)
                Positioned.fill(
                  child: _NoiseOverlay(),
                ),

              // Content
              widget.child,
            ],
          );
        },
      ),
    );
  }
}

/// Custom painter for mesh gradient effect
class _MeshGradientPainter extends CustomPainter {
  final double progress;

  _MeshGradientPainter({required this.progress});

  @override
  void paint(Canvas canvas, Size size) {
    // Create mesh gradient with multiple color stops
    final rect = Offset.zero & size;

    // Top-left gradient
    final gradient1 = RadialGradient(
      center: Alignment(
        -0.8 + (progress * 0.2),
        -0.8 + (progress * 0.1),
      ),
      radius: 1.2,
      colors: [
        Color.lerp(
          const Color(0xFF1A0A2E),
          const Color(0xFF16213E),
          progress,
        )!,
        Colors.transparent,
      ],
    );

    // Bottom-right gradient
    final gradient2 = RadialGradient(
      center: Alignment(
        0.8 - (progress * 0.2),
        0.8 - (progress * 0.1),
      ),
      radius: 1.0,
      colors: [
        Color.lerp(
          const Color(0xFF16213E),
          const Color(0xFF0F1419),
          progress,
        )!,
        Colors.transparent,
      ],
    );

    // Center gradient
    final gradient3 = RadialGradient(
      center: Alignment(
        0.0,
        progress * 0.5 - 0.25,
      ),
      radius: 0.8,
      colors: [
        const Color(0xFF0F1419),
        Colors.transparent,
      ],
    );

    // Paint gradients
    canvas.drawRect(rect, Paint()..shader = gradient1.createShader(rect));
    canvas.drawRect(rect, Paint()
      ..shader = gradient2.createShader(rect)
      ..blendMode = BlendMode.screen);
    canvas.drawRect(rect, Paint()
      ..shader = gradient3.createShader(rect)
      ..blendMode = BlendMode.overlay);
  }

  @override
  bool shouldRepaint(_MeshGradientPainter oldDelegate) =>
      oldDelegate.progress != progress;
}


/// Modern background with animated floating particles/orbs
/// Includes blur effects and smooth animations
class ModernGradientBackgroundAnimated extends StatefulWidget {
  final Widget child;
  final int particleCount;
  final Duration duration;
  final bool showNoise;

  const ModernGradientBackgroundAnimated({
    super.key,
    required this.child,
    this.particleCount = 12,
    this.duration = const Duration(seconds: 15),
    this.showNoise = true,
  });

  @override
  State<ModernGradientBackgroundAnimated> createState() =>
      _ModernGradientBackgroundAnimatedState();
}

class _ModernGradientBackgroundAnimatedState
    extends State<ModernGradientBackgroundAnimated>
    with TickerProviderStateMixin {
  late List<AnimationController> _controllers;
  late List<_ParticleAnimation> _particles;

  @override
  void initState() {
    super.initState();
    _initializeParticles();
  }

  void _initializeParticles() {
    final random = math.Random();

    _controllers = List.generate(
      widget.particleCount,
      (index) => AnimationController(
        duration: Duration(
          seconds: 12 + random.nextInt(8),
        ),
        vsync: this,
      )..repeat(reverse: true),
    );

    _particles = List.generate(
      widget.particleCount,
      (index) {
        return _ParticleAnimation(
          controller: _controllers[index],
          startX: random.nextDouble(),
          startY: random.nextDouble(),
          size: 40.0 + random.nextDouble() * 80,
          color: _getParticleColor(index),
          offsetX: (random.nextDouble() - 0.5) * 0.3,
          offsetY: (random.nextDouble() - 0.5) * 0.3,
        );
      },
    );
  }

  Color _getParticleColor(int index) {
    final colors = [
      const Color(0xFF1A0A2E).withOpacity(0.15), // Deep purple
      const Color(0xFF16213E).withOpacity(0.12), // Rich blue
      const Color(0xFFE8B44C).withOpacity(0.08), // Gold accent
    ];
    return colors[index % colors.length];
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
    return RepaintBoundary(
      child: Stack(
        children: [
          // Base gradient
          const ModernGradientBackground(
            child: SizedBox.expand(),
            showNoise: false,
          ),

          // Animated particles with blur
          ..._particles.map((particle) {
            return AnimatedBuilder(
              animation: particle.controller,
              builder: (context, child) {
                return _buildParticle(particle);
              },
            );
          }),

          // Noise overlay
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

  Widget _buildParticle(_ParticleAnimation particle) {
    return LayoutBuilder(
      builder: (context, constraints) {
        final progress = particle.controller.value;
        final curve = Curves.easeInOut.transform(progress);

        final x = constraints.maxWidth *
            (particle.startX + particle.offsetX * curve);
        final y = constraints.maxHeight *
            (particle.startY + particle.offsetY * curve);

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
                    particle.color,
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

/// Data class for particle animations
class _ParticleAnimation {
  final AnimationController controller;
  final double startX;
  final double startY;
  final double size;
  final Color color;
  final double offsetX;
  final double offsetY;

  _ParticleAnimation({
    required this.controller,
    required this.startX,
    required this.startY,
    required this.size,
    required this.color,
    required this.offsetX,
    required this.offsetY,
  });
}

