import 'package:flutter/material.dart';

import '../../../../core/theme/app_colors.dart';
import '../../../../core/theme/app_spacing.dart';

/// Banner showing pending reviews that need attention with pulsing animation
class DueReviewsBanner extends StatefulWidget {
  final int dueCount;
  final DateTime? nextReviewTime;
  final VoidCallback onTap;

  const DueReviewsBanner({
    super.key,
    required this.dueCount,
    this.nextReviewTime,
    required this.onTap,
  });

  @override
  State<DueReviewsBanner> createState() => _DueReviewsBannerState();
}

class _DueReviewsBannerState extends State<DueReviewsBanner>
    with SingleTickerProviderStateMixin {
  late AnimationController _controller;
  late Animation<double> _pulseAnimation;
  late Animation<double> _borderOpacityAnimation;
  late Animation<double> _shadowBlurAnimation;
  late Animation<double> _iconRotationAnimation;

  @override
  void initState() {
    super.initState();

    _controller = AnimationController(
      duration: const Duration(milliseconds: 2000),
      vsync: this,
    );

    _pulseAnimation = Tween<double>(
      begin: 1.0,
      end: 1.02,
    ).animate(
      CurvedAnimation(
        parent: _controller,
        curve: Curves.easeInOut,
      ),
    );

    _borderOpacityAnimation = Tween<double>(
      begin: 0.3,
      end: 0.7,
    ).animate(
      CurvedAnimation(
        parent: _controller,
        curve: Curves.easeInOut,
      ),
    );

    _shadowBlurAnimation = Tween<double>(
      begin: 8.0,
      end: 15.0,
    ).animate(
      CurvedAnimation(
        parent: _controller,
        curve: Curves.easeInOut,
      ),
    );

    _iconRotationAnimation = TweenSequence<double>([
      TweenSequenceItem(
        tween: Tween<double>(begin: 0.0, end: 0.1)
            .chain(CurveTween(curve: Curves.easeInOut)),
        weight: 25,
      ),
      TweenSequenceItem(
        tween: Tween<double>(begin: 0.1, end: -0.1)
            .chain(CurveTween(curve: Curves.easeInOut)),
        weight: 50,
      ),
      TweenSequenceItem(
        tween: Tween<double>(begin: -0.1, end: 0.0)
            .chain(CurveTween(curve: Curves.easeInOut)),
        weight: 25,
      ),
    ]).animate(_controller);

    _controller.repeat(reverse: true);
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  String _getReviewText() {
    if (widget.dueCount == 0) {
      return 'Không có họa tiết cần ôn tập';
    }
    return 'CẦN ÔN TẬP: ${widget.dueCount} họa tiết';
  }

  String? _getNextReviewText() {
    if (widget.nextReviewTime == null) return null;

    final now = DateTime.now();
    final difference = widget.nextReviewTime!.difference(now);

    if (difference.isNegative) return 'Đến giờ ôn tập';

    if (difference.inHours > 24) {
      final days = difference.inDays;
      return 'Kế tiếp trong $days ngày';
    } else if (difference.inHours > 0) {
      return 'Kế tiếp trong ${difference.inHours} giờ';
    } else {
      return 'Kế tiếp trong ${difference.inMinutes} phút';
    }
  }

  @override
  Widget build(BuildContext context) {
    if (widget.dueCount == 0) return const SizedBox.shrink();

    return AnimatedBuilder(
      animation: _controller,
      builder: (context, child) {
        return Transform.scale(
          scale: _pulseAnimation.value,
          child: InkWell(
            onTap: widget.onTap,
            borderRadius: BorderRadius.circular(16),
            child: Container(
              padding: const EdgeInsets.all(AppSpacing.md),
              decoration: BoxDecoration(
                gradient: LinearGradient(
                  begin: Alignment.topLeft,
                  end: Alignment.bottomRight,
                  colors: [
                    AppColors.warning.withOpacity(0.2),
                    AppColors.warning.withOpacity(0.1),
                  ],
                ),
                borderRadius: BorderRadius.circular(16),
                border: Border.all(
                  color: AppColors.warning
                      .withOpacity(_borderOpacityAnimation.value),
                  width: 1.5,
                ),
                boxShadow: [
                  BoxShadow(
                    color: AppColors.warning.withOpacity(0.3),
                    blurRadius: _shadowBlurAnimation.value,
                    offset: const Offset(0, 4),
                  ),
                ],
              ),
              child: LayoutBuilder(
                builder: (context, constraints) {
                  final isCompact = constraints.maxWidth < 340;
                  final content = Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        '📋 ${_getReviewText()}',
                        style:
                            Theme.of(context).textTheme.titleMedium?.copyWith(
                                  color: Colors.white,
                                  fontWeight: FontWeight.bold,
                                ),
                      ),
                      if (_getNextReviewText() != null) ...[
                        const SizedBox(height: 4),
                        Text(
                          _getNextReviewText()!,
                          style:
                              Theme.of(context).textTheme.bodySmall?.copyWith(
                                    color: Colors.white70,
                                  ),
                        ),
                      ],
                    ],
                  );

                  if (isCompact) {
                    return Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Transform.rotate(
                          angle: _iconRotationAnimation.value,
                          child: Container(
                            padding: const EdgeInsets.all(AppSpacing.sm),
                            decoration: BoxDecoration(
                              color: AppColors.warning.withOpacity(0.3),
                              borderRadius: BorderRadius.circular(12),
                            ),
                            child: const Icon(
                              Icons.notifications_active,
                              color: AppColors.warning,
                              size: 24,
                            ),
                          ),
                        ),
                        const SizedBox(height: AppSpacing.sm),
                        content,
                      ],
                    );
                  }

                  return Row(
                    children: [
                      // Animated icon with wobble effect
                      Transform.rotate(
                        angle: _iconRotationAnimation.value,
                        child: Container(
                          padding: const EdgeInsets.all(AppSpacing.sm),
                          decoration: BoxDecoration(
                            color: AppColors.warning.withOpacity(0.3),
                            borderRadius: BorderRadius.circular(12),
                          ),
                          child: const Icon(
                            Icons.notifications_active,
                            color: AppColors.warning,
                            size: 28,
                          ),
                        ),
                      ),
                      const SizedBox(width: AppSpacing.md),

                      // Text content
                      Expanded(child: content),

                      // Arrow icon
                      Icon(
                        Icons.arrow_forward_ios,
                        color: Colors.white.withOpacity(0.5),
                        size: 20,
                      ),
                    ],
                  );
                },
              ),
            ),
          ),
        );
      },
    );
  }
}
