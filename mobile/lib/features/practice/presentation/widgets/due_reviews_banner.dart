import 'package:flutter/material.dart';

import '../../../../core/theme/app_colors.dart';
import '../../../../core/theme/app_spacing.dart';

/// Banner showing pending reviews that need attention
class DueReviewsBanner extends StatelessWidget {
  final int dueCount;
  final DateTime? nextReviewTime;
  final VoidCallback onTap;

  const DueReviewsBanner({
    super.key,
    required this.dueCount,
    this.nextReviewTime,
    required this.onTap,
  });

  String _getReviewText() {
    if (dueCount == 0) {
      return 'Không có họa tiết cần ôn tập';
    }
    return 'CẦN ÔN TẬP: $dueCount họa tiết';
  }

  String? _getNextReviewText() {
    if (nextReviewTime == null) return null;

    final now = DateTime.now();
    final difference = nextReviewTime!.difference(now);

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
    if (dueCount == 0) return const SizedBox.shrink();

    return InkWell(
      onTap: onTap,
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
            color: AppColors.warning.withOpacity(0.4),
            width: 1.5,
          ),
          boxShadow: [
            BoxShadow(
              color: AppColors.warning.withOpacity(0.2),
              blurRadius: 12,
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
                  style: Theme.of(context).textTheme.titleMedium?.copyWith(
                        color: Colors.white,
                        fontWeight: FontWeight.bold,
                      ),
                ),
                if (_getNextReviewText() != null) ...[
                  const SizedBox(height: 4),
                  Text(
                    _getNextReviewText()!,
                    style: Theme.of(context).textTheme.bodySmall?.copyWith(
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
                  Container(
                    padding: const EdgeInsets.all(AppSpacing.sm),
                    decoration: BoxDecoration(
                      color: AppColors.warning.withOpacity(0.3),
                      borderRadius: BorderRadius.circular(12),
                    ),
                    child: const Icon(
                      Icons.assignment,
                      color: AppColors.warning,
                      size: 24,
                    ),
                  ),
                  const SizedBox(height: AppSpacing.sm),
                  content,
                ],
              );
            }

            return Row(
              children: [
                // Icon
                Container(
                  padding: const EdgeInsets.all(AppSpacing.sm),
                  decoration: BoxDecoration(
                    color: AppColors.warning.withOpacity(0.3),
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: const Icon(
                    Icons.assignment,
                    color: AppColors.warning,
                    size: 28,
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
    );
  }
}
