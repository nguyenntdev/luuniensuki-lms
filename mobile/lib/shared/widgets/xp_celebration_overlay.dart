import 'dart:math' as math;
import 'package:flutter/material.dart';
import 'package:confetti/confetti.dart';

import '../../core/theme/app_colors.dart';
import '../services/xp_celebration_service.dart';

/// Animated XP celebration overlay
class XpCelebrationOverlay extends StatefulWidget {
  final int xpGained;
  final CelebrationLevel celebrationLevel;
  final bool didLevelUp;
  final Map<String, dynamic>? newRank;
  final List<String> badges;
  final VoidCallback onComplete;

  const XpCelebrationOverlay({
    super.key,
    required this.xpGained,
    required this.celebrationLevel,
    required this.didLevelUp,
    this.newRank,
    this.badges = const [],
    required this.onComplete,
  });

  @override
  State<XpCelebrationOverlay> createState() => _XpCelebrationOverlayState();
}

class _XpCelebrationOverlayState extends State<XpCelebrationOverlay>
    with TickerProviderStateMixin {
  late AnimationController _mainController;
  late AnimationController _particlesController;
  late ConfettiController _confettiController;
  
  late Animation<double> _slideUpAnimation;
  late Animation<double> _scaleAnimation;
  late Animation<double> _fadeAnimation;
  late Animation<double> _bannerSlideAnimation;

  @override
  void initState() {
    super.initState();

    // Main animation controller
    _mainController = AnimationController(
      vsync: this,
      duration: _getAnimationDuration(),
    );

    // Particles controller (for medium level)
    _particlesController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 1500),
    );

    // Confetti controller (for large level)
    _confettiController = ConfettiController(
      duration: const Duration(seconds: 3),
    );

    // Slide up animation
    _slideUpAnimation = Tween<double>(
      begin: 100.0,
      end: -200.0,
    ).animate(CurvedAnimation(
      parent: _mainController,
      curve: Curves.easeOutCubic,
    ));

    // Scale animation with bounce
    _scaleAnimation = TweenSequence<double>([
      TweenSequenceItem(
        tween: Tween(begin: 0.0, end: 1.3)
            .chain(CurveTween(curve: Curves.easeOut)),
        weight: 30,
      ),
      TweenSequenceItem(
        tween: Tween(begin: 1.3, end: 1.0)
            .chain(CurveTween(curve: Curves.elasticOut)),
        weight: 40,
      ),
      TweenSequenceItem(
        tween: ConstantTween(1.0),
        weight: 30,
      ),
    ]).animate(_mainController);

    // Fade out animation
    _fadeAnimation = Tween<double>(begin: 1.0, end: 0.0).animate(
      CurvedAnimation(
        parent: _mainController,
        curve: const Interval(0.7, 1.0, curve: Curves.easeIn),
      ),
    );

    // Banner slide animation (for level up)
    _bannerSlideAnimation = Tween<double>(begin: -100.0, end: 0.0).animate(
      CurvedAnimation(
        parent: _mainController,
        curve: const Interval(0.2, 0.5, curve: Curves.easeOutBack),
      ),
    );

    // Start animations
    _mainController.forward();
    
    if (widget.celebrationLevel == CelebrationLevel.medium) {
      _particlesController.forward();
    } else if (widget.celebrationLevel == CelebrationLevel.large ||
        widget.didLevelUp) {
      _confettiController.play();
    }

    // Complete callback
    _mainController.addStatusListener((status) {
      if (status == AnimationStatus.completed) {
        Future.delayed(const Duration(milliseconds: 300), () {
          if (mounted) {
            widget.onComplete();
          }
        });
      }
    });
  }

  Duration _getAnimationDuration() {
    switch (widget.celebrationLevel) {
      case CelebrationLevel.small:
        return const Duration(milliseconds: 1500);
      case CelebrationLevel.medium:
        return const Duration(milliseconds: 2000);
      case CelebrationLevel.large:
        return const Duration(milliseconds: 2500);
    }
  }

  @override
  void dispose() {
    _mainController.dispose();
    _particlesController.dispose();
    _confettiController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Material(
      color: Colors.transparent,
      child: Stack(
        children: [
          // Confetti overlay (for large celebrations)
          if (widget.celebrationLevel == CelebrationLevel.large ||
              widget.didLevelUp)
            _buildConfettiOverlay(),

          // Main XP badge animation
          _buildXpBadge(),

          // Level up banner (if leveled up)
          if (widget.didLevelUp) _buildLevelUpBanner(),

          // Particles (for medium celebrations)
          if (widget.celebrationLevel == CelebrationLevel.medium)
            _buildParticles(),
        ],
      ),
    );
  }

  Widget _buildConfettiOverlay() {
    return Align(
      alignment: Alignment.topCenter,
      child: ConfettiWidget(
        confettiController: _confettiController,
        blastDirectionality: BlastDirectionality.explosive,
        shouldLoop: false,
        colors: const [
          AppColors.xpGold,
          AppColors.primary,
          AppColors.success,
          AppColors.badgePurple,
          AppColors.levelUpGreen,
          Colors.orange,
        ],
        numberOfParticles: widget.didLevelUp ? 50 : 30,
        gravity: 0.3,
        emissionFrequency: 0.05,
        maxBlastForce: 20,
        minBlastForce: 8,
      ),
    );
  }

  Widget _buildXpBadge() {
    return AnimatedBuilder(
      animation: _mainController,
      builder: (context, child) {
        return Positioned(
          top: MediaQuery.of(context).size.height / 2 + _slideUpAnimation.value,
          left: 0,
          right: 0,
          child: Center(
            child: Opacity(
              opacity: _fadeAnimation.value,
              child: Transform.scale(
                scale: _scaleAnimation.value,
                child: Container(
                  padding: const EdgeInsets.symmetric(
                    horizontal: 24,
                    vertical: 16,
                  ),
                  decoration: BoxDecoration(
                    gradient: const LinearGradient(
                      colors: [AppColors.xpGold, AppColors.xpGoldDark],
                      begin: Alignment.topCenter,
                      end: Alignment.bottomCenter,
                    ),
                    borderRadius: BorderRadius.circular(24),
                    boxShadow: [
                      BoxShadow(
                        color: AppColors.xpGold.withOpacity(0.6),
                        blurRadius: 30,
                        spreadRadius: 5,
                      ),
                    ],
                  ),
                  child: Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      const Icon(
                        Icons.star,
                        color: Colors.white,
                        size: 32,
                      ),
                      const SizedBox(width: 12),
                      Text(
                        '+${widget.xpGained} XP',
                        style: const TextStyle(
                          color: Colors.white,
                          fontSize: 28,
                          fontWeight: FontWeight.bold,
                          letterSpacing: 1.2,
                        ),
                      ),
                    ],
                  ),
                ),
              ),
            ),
          ),
        );
      },
    );
  }

  Widget _buildLevelUpBanner() {
    return AnimatedBuilder(
      animation: _mainController,
      builder: (context, child) {
        return Positioned(
          top: 100 + _bannerSlideAnimation.value,
          left: 0,
          right: 0,
          child: Center(
            child: Opacity(
              opacity: _fadeAnimation.value.clamp(0.0, 1.0),
              child: Container(
                margin: const EdgeInsets.symmetric(horizontal: 32),
                padding: const EdgeInsets.symmetric(
                  horizontal: 32,
                  vertical: 20,
                ),
                decoration: BoxDecoration(
                  gradient: const LinearGradient(
                    colors: [
                      AppColors.levelUpGreen,
                      Color(0xFF00A844),
                    ],
                    begin: Alignment.topLeft,
                    end: Alignment.bottomRight,
                  ),
                  borderRadius: BorderRadius.circular(16),
                  border: Border.all(
                    color: Colors.white.withOpacity(0.3),
                    width: 2,
                  ),
                  boxShadow: [
                    BoxShadow(
                      color: AppColors.levelUpGreen.withOpacity(0.5),
                      blurRadius: 25,
                      spreadRadius: 3,
                    ),
                  ],
                ),
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    const Row(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        Icon(
                          Icons.military_tech,
                          color: Colors.white,
                          size: 28,
                        ),
                        SizedBox(width: 8),
                        Text(
                          'THĂNG CẤP!',
                          style: TextStyle(
                            color: Colors.white,
                            fontSize: 24,
                            fontWeight: FontWeight.bold,
                            letterSpacing: 2,
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 8),
                    Text(
                      widget.newRank?['name'] ?? '',
                      style: const TextStyle(
                        color: Colors.white,
                        fontSize: 32,
                        fontWeight: FontWeight.bold,
                        letterSpacing: 1,
                      ),
                    ),
                    Text(
                      'Cấp độ ${widget.newRank?['level'] ?? ''}',
                      style: TextStyle(
                        color: Colors.white.withOpacity(0.9),
                        fontSize: 16,
                        fontWeight: FontWeight.w500,
                      ),
                    ),
                  ],
                ),
              ),
            ),
          ),
        );
      },
    );
  }

  Widget _buildParticles() {
    return AnimatedBuilder(
      animation: _particlesController,
      builder: (context, child) {
        return Positioned.fill(
          child: IgnorePointer(
            child: CustomPaint(
              painter: _ParticlesPainter(
                animation: _particlesController,
                opacity: _fadeAnimation.value,
              ),
            ),
          ),
        );
      },
    );
  }
}

/// Custom painter for particle effects
class _ParticlesPainter extends CustomPainter {
  final Animation<double> animation;
  final double opacity;
  final List<_Particle> particles;

  _ParticlesPainter({
    required this.animation,
    required this.opacity,
  }) : particles = List.generate(
          15,
          (index) => _Particle(
            angle: (index / 15) * 2 * math.pi,
            speed: 100 + math.Random().nextDouble() * 50,
            size: 4 + math.Random().nextDouble() * 4,
            color: _getRandomColor(index),
          ),
        ),
        super(repaint: animation);

  static Color _getRandomColor(int seed) {
    final colors = [
      AppColors.xpGold,
      AppColors.primary,
      AppColors.success,
      AppColors.warning,
    ];
    return colors[seed % colors.length];
  }

  @override
  void paint(Canvas canvas, Size size) {
    final progress = animation.value;
    final centerX = size.width / 2;
    final centerY = size.height / 2;

    for (final particle in particles) {
      final distance = progress * particle.speed;
      final x = centerX + math.cos(particle.angle) * distance;
      final y = centerY + math.sin(particle.angle) * distance;

      // Fade out particles as they move away
      final particleOpacity = (1 - progress) * opacity;

      final paint = Paint()
        ..color = particle.color.withOpacity(particleOpacity)
        ..style = PaintingStyle.fill;

      canvas.drawCircle(
        Offset(x, y),
        particle.size * (1 - progress * 0.5),
        paint,
      );
    }
  }

  @override
  bool shouldRepaint(_ParticlesPainter oldDelegate) => true;
}

/// Particle data class
class _Particle {
  final double angle;
  final double speed;
  final double size;
  final Color color;

  _Particle({
    required this.angle,
    required this.speed,
    required this.size,
    required this.color,
  });
}
