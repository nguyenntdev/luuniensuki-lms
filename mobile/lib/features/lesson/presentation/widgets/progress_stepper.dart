import 'package:flutter/material.dart';

import '../../../../core/theme/app_colors.dart';
import '../../../../core/theme/app_typography.dart';

/// Progress stepper showing the learning flow steps.
/// Steps: Khám Phá (25 XP) → Bài Học (50 XP) → Trắc Nghiệm (75 XP)
class ProgressStepper extends StatelessWidget {
  final String status;

  const ProgressStepper({super.key, required this.status});

  @override
  Widget build(BuildContext context) {
    final currentStep = _getStepIndex(status);

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 20),
      color: AppColors.background,
      child: Row(
        children: [
          _buildStep(
            index: 0,
            label: 'Khám Phá',
            xp: 25,
            isCompleted: currentStep > 0,
            isCurrent: currentStep == 0,
            isLocked: currentStep < 0,
          ),
          _buildConnector(isCompleted: currentStep > 0),
          _buildStep(
            index: 1,
            label: 'Bài Học',
            xp: 50,
            isCompleted: currentStep > 1,
            isCurrent: currentStep == 1,
            isLocked: currentStep < 1,
          ),
          _buildConnector(isCompleted: currentStep > 1),
          _buildStep(
            index: 2,
            label: 'Trắc Nghiệm',
            xp: 75,
            isCompleted: currentStep > 2,
            isCurrent: currentStep == 2,
            isLocked: currentStep < 2,
          ),
        ],
      ),
    );
  }

  int _getStepIndex(String status) {
    switch (status.toLowerCase()) {
      case 'discovered':
        return 1; // Discovered, ready for lesson
      case 'learned':
        return 2; // Learned, ready for quiz
      case 'mastered':
        return 3; // All completed
      case 'hidden':
      default:
        return 0; // Not yet discovered
    }
  }

  Widget _buildStep({
    required int index,
    required String label,
    required int xp,
    required bool isCompleted,
    required bool isCurrent,
    required bool isLocked,
  }) {
    final Color circleColor;
    final Color textColor;
    final Widget circleContent;

    if (isCompleted) {
      circleColor = AppColors.success;
      textColor = AppColors.success;
      circleContent = const Icon(
        Icons.check,
        color: Colors.white,
        size: 16,
      );
    } else if (isCurrent) {
      circleColor = AppColors.primary;
      textColor = AppColors.primary;
      circleContent = Text(
        '${index + 1}',
        style: const TextStyle(
          color: AppColors.onPrimary,
          fontWeight: FontWeight.bold,
          fontSize: 12,
        ),
      );
    } else {
      circleColor = AppColors.surfaceElevated;
      textColor = AppColors.textHint;
      circleContent = Icon(
        Icons.lock,
        color: AppColors.textHint,
        size: 14,
      );
    }

    return Expanded(
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          // Circle indicator
          AnimatedContainer(
            duration: const Duration(milliseconds: 300),
            width: 32,
            height: 32,
            decoration: BoxDecoration(
              color: circleColor,
              shape: BoxShape.circle,
              boxShadow: isCurrent
                  ? [
                      BoxShadow(
                        color: AppColors.primary.withOpacity(0.4),
                        blurRadius: 12,
                        offset: const Offset(0, 4),
                      ),
                    ]
                  : null,
            ),
            child: Center(child: circleContent),
          ),

          const SizedBox(height: 8),

          // Label
          Text(
            label,
            style: AppTypography.textTheme.labelSmall?.copyWith(
              color: textColor,
              fontWeight: isCurrent ? FontWeight.w600 : FontWeight.normal,
            ),
            textAlign: TextAlign.center,
          ),

          const SizedBox(height: 2),

          // XP value
          Row(
            mainAxisSize: MainAxisSize.min,
            children: [
              Icon(
                Icons.star,
                size: 10,
                color: isCompleted || isCurrent
                    ? AppColors.xpGold
                    : AppColors.textHint,
              ),
              const SizedBox(width: 2),
              Text(
                '+$xp XP',
                style: AppTypography.textTheme.labelSmall?.copyWith(
                  color: isCompleted || isCurrent
                      ? AppColors.xpGold
                      : AppColors.textHint,
                  fontSize: 10,
                  fontWeight: FontWeight.w500,
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildConnector({required bool isCompleted}) {
    return Expanded(
      child: Container(
        height: 2,
        margin: const EdgeInsets.only(bottom: 32),
        decoration: BoxDecoration(
          color: isCompleted ? AppColors.success : AppColors.border,
          borderRadius: BorderRadius.circular(1),
        ),
      ),
    );
  }
}
