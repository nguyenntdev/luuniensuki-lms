import 'package:flutter/material.dart';
import 'package:confetti/confetti.dart';
import 'dart:math' as math;

import '../../../../core/theme/app_colors.dart';
import '../../../../core/theme/app_spacing.dart';
import '../../../../shared/widgets/icons/index.dart';
import '../../domain/entities/streak_milestone.dart';

/// Enhanced streak milestone celebration with rich animations
/// Shows when user reaches a milestone (7, 30, 100, 365 days)
class StreakMilestoneAnimation extends StatefulWidget {
  final StreakMilestone milestone;
  final VoidCallback onDismiss;
  final int currentStreak;

  const StreakMilestoneAnimation({
    super.key,
    required this.milestone,
    required this.onDismiss,
    required this.currentStreak,
  });

  /// Show the milestone celebration overlay
  static Future<void> show(
    BuildContext context, {
    required StreakMilestone milestone,
    required int currentStreak,
  }) {
    return showGeneralDialog(
      context: context,
      barrierDismissible: false,
      barrierColor: Colors.black87,
      transitionDuration: const Duration(milliseconds: 300),
      pageBuilder: (context, animation, secondaryAnimation) {
        return StreakMilestoneAnimation(
          milestone: milestone,
          currentStreak: currentStreak,
          onDismiss: () => Navigator.of(context).pop(),
        );
      },
    );
  }

  @override
  State<StreakMilestoneAnimation> createState() =>
      _StreakMilestoneAnimationState();
}

class _StreakMilestoneAnimationState extends State<StreakMilestoneAnimation>
    with TickerProviderStateMixin {
  late AnimationController _scaleController;
  late AnimationController _pulseController;
  late AnimationController _fireController;
  late Animation<double> _scaleAnimation;
  late Animation<double> _pulseAnimation;
  late Animation<double> _fireAnimation;
  late ConfettiController _confettiController;

  @override
  void initState() {
    super.initState();

    // Scale animation for card
    _scaleController = AnimationController(
      duration: const Duration(milliseconds: 600),
      vsync: this,
    );
    _scaleAnimation = CurvedAnimation(
      parent: _scaleController,
      curve: Curves.elasticOut,
    );

    // Pulse animation for glow
    _pulseController = AnimationController(
      duration: const Duration(milliseconds: 1500),
      vsync: this,
    );
    _pulseAnimation = Tween<double>(begin: 0.8, end: 1.2).animate(
      CurvedAnimation(parent: _pulseController, curve: Curves.easeInOut),
    );

    // Fire/flame animation
    _fireController = AnimationController(
      duration: const Duration(milliseconds: 800),
      vsync: this,
    );
    _fireAnimation = Tween<double>(begin: 0.9, end: 1.1).animate(
      CurvedAnimation(parent: _fireController, curve: Curves.easeInOut),
    );

    // Confetti controller
    _confettiController = ConfettiController(
      duration: const Duration(seconds: 5),
    );

    // Start animations
    _scaleController.forward();
    _pulseController.repeat(reverse: true);
    _fireController.repeat(reverse: true);
    _confettiController.play();

    // Auto dismiss after 8 seconds
    Future.delayed(const Duration(seconds: 8), () {
      if (mounted) {
        widget.onDismiss();
      }
    });
  }

  @override
  void dispose() {
    _scaleController.dispose();
    _pulseController.dispose();
    _fireController.dispose();
    _confettiController.dispose();
    super.dispose();
  }

  Color _getMilestoneColor() {
    switch (widget.milestone.days) {
      case 7:
        return Colors.green;
      case 30:
        return Colors.blue;
      case 100:
        return Colors.purple;
      case 365:
        return AppColors.xpGold;
      default:
        return AppColors.streakOrange;
    }
  }

  @override
  Widget build(BuildContext context) {
    final milestoneColor = _getMilestoneColor();

    return Material(
      color: Colors.transparent,
      child: Stack(
        children: [
          // Top confetti
          Align(
            alignment: Alignment.topCenter,
            child: ConfettiWidget(
              confettiController: _confettiController,
              blastDirection: math.pi / 2,
              emissionFrequency: 0.03,
              numberOfParticles: 30,
              maxBlastForce: 30,
              minBlastForce: 10,
              gravity: 0.2,
              colors: [
                AppColors.streakOrange,
                milestoneColor,
                AppColors.xpGold,
                Colors.white,
                AppColors.primary,
              ],
            ),
          ),

          // Main celebration card
          Center(
            child: ScaleTransition(
              scale: _scaleAnimation,
              child: Container(
                margin: const EdgeInsets.all(AppSpacing.xl),
                padding: const EdgeInsets.all(AppSpacing.xl),
                constraints: const BoxConstraints(maxWidth: 340),
                decoration: BoxDecoration(
                  gradient: LinearGradient(
                    begin: Alignment.topLeft,
                    end: Alignment.bottomRight,
                    colors: [
                      milestoneColor.withOpacity(0.3),
                      AppColors.surface,
                      AppColors.surfaceVariant,
                    ],
                  ),
                  borderRadius: BorderRadius.circular(28),
                  border: Border.all(
                    color: milestoneColor.withOpacity(0.5),
                    width: 3,
                  ),
                  boxShadow: [
                    BoxShadow(
                      color: milestoneColor.withOpacity(0.4),
                      blurRadius: 40,
                      spreadRadius: 10,
                    ),
                  ],
                ),
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    // Animated milestone icon
                    AnimatedBuilder(
                      animation: _fireAnimation,
                      builder: (context, child) {
                        return Transform.scale(
                          scale: _fireAnimation.value,
                          child: Container(
                            width: 100,
                            height: 100,
                            decoration: BoxDecoration(
                              gradient: RadialGradient(
                                colors: [
                                  milestoneColor.withOpacity(0.4),
                                  milestoneColor.withOpacity(0.1),
                                ],
                              ),
                              shape: BoxShape.circle,
                              boxShadow: [
                                BoxShadow(
                                  color: milestoneColor.withOpacity(
                                    0.3 * _pulseAnimation.value,
                                  ),
                                  blurRadius: 30 * _pulseAnimation.value,
                                  spreadRadius: 10 * _pulseAnimation.value,
                                ),
                              ],
                            ),
                            child: Center(
                              child: MilestoneIcon(
                                days: widget.milestone.days,
                                size: 56,
                                showGlow: false,
                              ),
                            ),
                          ),
                        );
                      },
                    ),

                    AppSpacing.verticalSpaceLG,

                    // Streak count with fire
                    Row(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        const StreakIcon(
                          type: StreakIconType.fire,
                          size: 32,
                        ),
                        const SizedBox(width: 8),
                        Text(
                          '${widget.currentStreak}',
                          style: TextStyle(
                            color: AppColors.streakOrange,
                            fontSize: 48,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                        const SizedBox(width: 8),
                        Text(
                          'ngày',
                          style: TextStyle(
                            color: Colors.white.withOpacity(0.8),
                            fontSize: 24,
                            fontWeight: FontWeight.w500,
                          ),
                        ),
                      ],
                    ),

                    AppSpacing.verticalSpaceMD,

                    // Milestone title
                    Text(
                      widget.milestone.name,
                      style: TextStyle(
                        color: milestoneColor,
                        fontSize: 28,
                        fontWeight: FontWeight.bold,
                        letterSpacing: 1,
                      ),
                      textAlign: TextAlign.center,
                    ),

                    AppSpacing.verticalSpaceSM,

                    // Description
                    Text(
                      widget.milestone.description,
                      style: TextStyle(
                        color: Colors.white.withOpacity(0.8),
                        fontSize: 16,
                      ),
                      textAlign: TextAlign.center,
                    ),

                    AppSpacing.verticalSpaceLG,

                    // Gem reward with animation
                    AnimatedBuilder(
                      animation: _pulseAnimation,
                      builder: (context, child) {
                        return Transform.scale(
                          scale: 0.9 + (_pulseAnimation.value - 0.8) * 0.5,
                          child: Container(
                            padding: const EdgeInsets.symmetric(
                              horizontal: AppSpacing.lg,
                              vertical: AppSpacing.md,
                            ),
                            decoration: BoxDecoration(
                              gradient: LinearGradient(
                                colors: [
                                  AppColors.gemYellow.withOpacity(0.3),
                                  AppColors.xpGoldDark.withOpacity(0.2),
                                ],
                              ),
                              borderRadius: BorderRadius.circular(16),
                              border: Border.all(
                                color: AppColors.gemYellow,
                                width: 2,
                              ),
                              boxShadow: [
                                BoxShadow(
                                  color: AppColors.gemYellow.withOpacity(0.3),
                                  blurRadius: 15,
                                  spreadRadius: 2,
                                ),
                              ],
                            ),
                            child: Row(
                              mainAxisSize: MainAxisSize.min,
                              children: [
                                const GemIcon(size: 28),
                                const SizedBox(width: 10),
                                Text(
                                  '+${widget.milestone.gemReward}',
                                  style: const TextStyle(
                                    color: AppColors.gemYellow,
                                    fontSize: 28,
                                    fontWeight: FontWeight.bold,
                                  ),
                                ),
                              ],
                            ),
                          ),
                        );
                      },
                    ),

                    AppSpacing.verticalSpaceLG,

                    // Continue button
                    SizedBox(
                      width: double.infinity,
                      child: ElevatedButton(
                        onPressed: widget.onDismiss,
                        style: ElevatedButton.styleFrom(
                          backgroundColor: milestoneColor,
                          padding: const EdgeInsets.symmetric(vertical: 16),
                          shape: RoundedRectangleBorder(
                            borderRadius: BorderRadius.circular(14),
                          ),
                          elevation: 8,
                          shadowColor: milestoneColor.withOpacity(0.5),
                        ),
                        child: Row(
                          children: [
                            const Icon(
                              Icons.celebration_rounded,
                              color: Colors.white,
                              size: 18,
                            ),
                            const SizedBox(width: 8),
                            const Text(
                              'Tuyệt vời!',
                              style: TextStyle(
                                color: Colors.white,
                                fontSize: 18,
                                fontWeight: FontWeight.bold,
                              ),
                            ),
                          ],
                        ),
                      ),
                    ),
                  ],
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }
}

