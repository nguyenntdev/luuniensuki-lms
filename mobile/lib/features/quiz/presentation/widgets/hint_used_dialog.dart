import 'package:flutter/material.dart';
import 'dart:ui';

import '../../../../core/theme/app_colors.dart';
import '../../../../core/theme/app_typography.dart';
import '../../../../shared/widgets/glass/glass_container.dart';

/// Dialog shown when a hint is used
/// Shows gems deducted and provides visual feedback
class HintUsedDialog extends StatefulWidget {
  final int gemsDeducted;
  final VoidCallback onDismiss;

  const HintUsedDialog({
    super.key,
    required this.gemsDeducted,
    required this.onDismiss,
  });

  @override
  State<HintUsedDialog> createState() => _HintUsedDialogState();
}

class _HintUsedDialogState extends State<HintUsedDialog>
    with SingleTickerProviderStateMixin {
  late AnimationController _controller;
  late Animation<double> _scaleAnimation;
  late Animation<double> _fadeAnimation;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      duration: const Duration(milliseconds: 600),
      vsync: this,
    );

    _scaleAnimation = CurvedAnimation(
      parent: _controller,
      curve: Curves.elasticOut,
    );

    _fadeAnimation = CurvedAnimation(
      parent: _controller,
      curve: Curves.easeIn,
    );

    _controller.forward();

    // Auto dismiss after 2 seconds
    Future.delayed(const Duration(seconds: 2), () {
      if (mounted) {
        _controller.reverse().then((_) {
          if (mounted) {
            widget.onDismiss();
          }
        });
      }
    });
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
      child: BackdropFilter(
        filter: ImageFilter.blur(sigmaX: 5, sigmaY: 5),
        child: Container(
          color: Colors.black.withOpacity(0.3),
          child: Center(
            child: ScaleTransition(
              scale: _scaleAnimation,
              child: GlassContainer(
                padding: const EdgeInsets.all(32),
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    // Lightbulb icon with glow
                    Container(
                      width: 80,
                      height: 80,
                      decoration: BoxDecoration(
                        shape: BoxShape.circle,
                        color: AppColors.warning.withOpacity(0.2),
                        boxShadow: [
                          BoxShadow(
                            color: AppColors.warning.withOpacity(0.5),
                            blurRadius: 30,
                            spreadRadius: 5,
                          ),
                        ],
                      ),
                      child: const Icon(
                        Icons.lightbulb,
                        size: 48,
                        color: AppColors.warning,
                      ),
                    ),

                    const SizedBox(height: 24),

                    // Title
                    Text(
                      'Gợi ý đã sử dụng!',
                      style: AppTypography.textTheme.titleLarge?.copyWith(
                        color: AppColors.textPrimary,
                        fontWeight: FontWeight.bold,
                      ),
                      textAlign: TextAlign.center,
                    ),

                    const SizedBox(height: 12),

                    // Gems deducted
                    Container(
                      padding: const EdgeInsets.symmetric(
                        horizontal: 20,
                        vertical: 10,
                      ),
                      decoration: BoxDecoration(
                        color: AppColors.error.withOpacity(0.15),
                        borderRadius: BorderRadius.circular(20),
                        border: Border.all(
                          color: AppColors.error.withOpacity(0.3),
                          width: 1,
                        ),
                      ),
                      child: Row(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          Icon(
                            Icons.diamond_rounded,
                            color: AppColors.gemYellow,
                            size: 20,
                          ),
                          const SizedBox(width: 8),
                          Text(
                            '-${widget.gemsDeducted} Gems',
                            style: AppTypography.textTheme.titleMedium?.copyWith(
                              color: AppColors.error,
                              fontWeight: FontWeight.bold,
                            ),
                          ),
                        ],
                      ),
                    ),
                  ],
                ),
              ),
            ),
          ),
        ),
      ),
    );
  }
}

