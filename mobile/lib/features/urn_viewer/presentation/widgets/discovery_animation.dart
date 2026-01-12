import 'package:flutter/material.dart';

import '../../../../core/theme/app_colors.dart';
import '../../domain/entities/urn.dart';

/// Animated overlay shown when a motif is discovered.
/// Displays XP earned and any badges unlocked.
class DiscoveryAnimation extends StatefulWidget {
  final Motif motif;
  final int xpEarned;
  final List<String> badgesEarned;
  final VoidCallback onComplete;

  const DiscoveryAnimation({
    super.key,
    required this.motif,
    required this.xpEarned,
    this.badgesEarned = const [],
    required this.onComplete,
  });

  @override
  State<DiscoveryAnimation> createState() => _DiscoveryAnimationState();
}

class _DiscoveryAnimationState extends State<DiscoveryAnimation>
    with TickerProviderStateMixin {
  late AnimationController _mainController;
  late AnimationController _xpController;
  late Animation<double> _scaleAnimation;
  late Animation<double> _fadeInAnimation;
  late Animation<double> _fadeOutAnimation;
  late Animation<double> _xpCountAnimation;

  @override
  void initState() {
    super.initState();

    // Main animation controller
    _mainController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 2500),
    );

    // XP counter animation
    _xpController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 1000),
    );

    // Scale animation - bounce in
    _scaleAnimation = TweenSequence<double>([
      TweenSequenceItem(
        tween: Tween(begin: 0.0, end: 1.2)
            .chain(CurveTween(curve: Curves.easeOut)),
        weight: 25,
      ),
      TweenSequenceItem(
        tween: Tween(begin: 1.2, end: 0.9)
            .chain(CurveTween(curve: Curves.easeInOut)),
        weight: 15,
      ),
      TweenSequenceItem(
        tween: Tween(begin: 0.9, end: 1.0)
            .chain(CurveTween(curve: Curves.easeOut)),
        weight: 10,
      ),
      TweenSequenceItem(
        tween: ConstantTween(1.0),
        weight: 35,
      ),
      TweenSequenceItem(
        tween: Tween(begin: 1.0, end: 0.0)
            .chain(CurveTween(curve: Curves.easeIn)),
        weight: 15,
      ),
    ]).animate(_mainController);

    // Fade in animation
    _fadeInAnimation = Tween<double>(begin: 0.0, end: 1.0).animate(
      CurvedAnimation(
        parent: _mainController,
        curve: const Interval(0.0, 0.3, curve: Curves.easeOut),
      ),
    );

    // Fade out animation
    _fadeOutAnimation = Tween<double>(begin: 1.0, end: 0.0).animate(
      CurvedAnimation(
        parent: _mainController,
        curve: const Interval(0.85, 1.0, curve: Curves.easeIn),
      ),
    );

    // XP count animation
    _xpCountAnimation = Tween<double>(
      begin: 0.0,
      end: widget.xpEarned.toDouble(),
    ).animate(CurvedAnimation(
      parent: _xpController,
      curve: Curves.easeOut,
    ));

    // Start animations
    _mainController.forward();
    Future.delayed(const Duration(milliseconds: 500), () {
      if (mounted) {
        _xpController.forward();
      }
    });

    // Call onComplete when animation finishes
    _mainController.addStatusListener((status) {
      if (status == AnimationStatus.completed) {
        widget.onComplete();
      }
    });
  }

  @override
  void dispose() {
    _mainController.dispose();
    _xpController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: _mainController,
      builder: (context, child) {
        final opacity = _fadeInAnimation.value * _fadeOutAnimation.value;

        return Container(
          color: Colors.black.withOpacity(0.7 * opacity),
          child: Center(
            child: Transform.scale(
              scale: _scaleAnimation.value,
              child: Opacity(
                opacity: opacity,
                child: _buildContent(),
              ),
            ),
          ),
        );
      },
    );
  }

  Widget _buildContent() {
    return Container(
      margin: const EdgeInsets.all(32),
      padding: const EdgeInsets.all(32),
      decoration: BoxDecoration(
        color: Colors.grey[900],
        borderRadius: BorderRadius.circular(24),
        border: Border.all(
          color: AppColors.primary,
          width: 3,
        ),
        boxShadow: [
          BoxShadow(
            color: AppColors.primary.withOpacity(0.4),
            blurRadius: 30,
            spreadRadius: 5,
          ),
        ],
      ),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          // Discovery icon
          Container(
            width: 80,
            height: 80,
            decoration: BoxDecoration(
              color: AppColors.primary.withOpacity(0.2),
              shape: BoxShape.circle,
              border: Border.all(color: AppColors.primary, width: 3),
            ),
            child: const Icon(
              Icons.celebration,
              color: AppColors.xpGold,
              size: 40,
            ),
          ),
          const SizedBox(height: 24),

          // Title
          const Text(
            'ĐÃ KHÁM PHÁ!',
            style: TextStyle(
              color: AppColors.xpGold,
              fontSize: 24,
              fontWeight: FontWeight.bold,
              letterSpacing: 2,
            ),
          ),
          const SizedBox(height: 16),

          // Motif name
          Text(
            widget.motif.name,
            style: const TextStyle(
              color: Colors.white,
              fontSize: 28,
              fontWeight: FontWeight.bold,
            ),
            textAlign: TextAlign.center,
          ),
          const SizedBox(height: 8),

          // Category chip
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
            decoration: BoxDecoration(
              color: AppColors.primary.withOpacity(0.2),
              borderRadius: BorderRadius.circular(16),
            ),
            child: Text(
              widget.motif.category.nameVi,
              style: const TextStyle(
                color: AppColors.primary,
                fontSize: 14,
                fontWeight: FontWeight.w500,
              ),
            ),
          ),
          const SizedBox(height: 24),

          // XP earned
          if (widget.xpEarned > 0) ...[
            AnimatedBuilder(
              animation: _xpCountAnimation,
              builder: (context, child) {
                return Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    const Icon(
                      Icons.star,
                      color: AppColors.xpGold,
                      size: 32,
                    ),
                    const SizedBox(width: 8),
                    Text(
                      '+${_xpCountAnimation.value.toInt()} XP',
                      style: const TextStyle(
                        color: AppColors.xpGold,
                        fontSize: 32,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                  ],
                );
              },
            ),
            const SizedBox(height: 16),
          ],

          // Badges earned
          if (widget.badgesEarned.isNotEmpty) ...[
            const Divider(color: Colors.white24),
            const SizedBox(height: 16),
            const Text(
              'Huy hiệu mới!',
              style: TextStyle(
                color: AppColors.badgePurple,
                fontSize: 16,
                fontWeight: FontWeight.w600,
              ),
            ),
            const SizedBox(height: 8),
            Wrap(
              spacing: 8,
              children: widget.badgesEarned.map((badge) {
                return Chip(
                  backgroundColor: AppColors.badgePurple.withOpacity(0.2),
                  label: Text(
                    badge,
                    style: const TextStyle(color: AppColors.badgePurple),
                  ),
                  avatar: const Icon(
                    Icons.emoji_events,
                    color: AppColors.badgePurple,
                    size: 18,
                  ),
                );
              }).toList(),
            ),
          ],

          const SizedBox(height: 24),

          // Tap to continue hint
          Text(
            'Chạm để tiếp tục',
            style: TextStyle(
              color: Colors.white.withOpacity(0.5),
              fontSize: 14,
            ),
          ),
        ],
      ),
    );
  }
}

/// Animated XP badge widget
class XpBadge extends StatelessWidget {
  final int amount;
  final XpBadgeSize size;

  const XpBadge({
    super.key,
    required this.amount,
    this.size = XpBadgeSize.medium,
  });

  @override
  Widget build(BuildContext context) {
    final (iconSize, fontSize, padding) = switch (size) {
      XpBadgeSize.small => (16.0, 14.0, 6.0),
      XpBadgeSize.medium => (20.0, 18.0, 8.0),
      XpBadgeSize.large => (28.0, 24.0, 12.0),
    };

    return Container(
      padding: EdgeInsets.symmetric(horizontal: padding * 1.5, vertical: padding),
      decoration: BoxDecoration(
        gradient: const LinearGradient(
          colors: [AppColors.xpGold, AppColors.xpGoldDark],
          begin: Alignment.topCenter,
          end: Alignment.bottomCenter,
        ),
        borderRadius: BorderRadius.circular(padding * 3),
        boxShadow: [
          BoxShadow(
            color: AppColors.xpGold.withOpacity(0.4),
            blurRadius: 8,
            offset: const Offset(0, 2),
          ),
        ],
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(Icons.star, color: Colors.white, size: iconSize),
          SizedBox(width: padding / 2),
          Text(
            '+$amount XP',
            style: TextStyle(
              color: Colors.white,
              fontSize: fontSize,
              fontWeight: FontWeight.bold,
            ),
          ),
        ],
      ),
    );
  }
}

enum XpBadgeSize { small, medium, large }
