import 'package:flutter/material.dart';
import '../../../core/theme/app_colors.dart';
import '../../../core/theme/app_spacing.dart';
import '../../../core/theme/app_typography.dart';
import '../glass/glass_button.dart';

/// A reusable widget for displaying empty state screens.
///
/// Displays an icon, title, optional message, and optional action button
/// in a centered, vertically aligned layout.
///
/// Example usage:
/// ```dart
/// AppEmptyState(
///   icon: Icons.search_off,
///   title: 'Không tìm thấy kết quả',
///   message: 'Thử tìm kiếm với từ khóa khác',
/// )
/// ```
///
/// Example with action:
/// ```dart
/// AppEmptyState(
///   icon: Icons.folder_open,
///   title: 'Chưa có khóa học nào',
///   message: 'Bắt đầu khám phá các khóa học ngay',
///   actionLabel: 'Khám phá',
///   onAction: () => Navigator.pushNamed(context, '/explore'),
/// )
/// ```
class AppEmptyState extends StatelessWidget {
  final IconData icon;
  final String title;
  final String? message;
  final String? actionLabel;
  final VoidCallback? onAction;

  const AppEmptyState({
    super.key,
    this.icon = Icons.inbox_outlined,
    required this.title,
    this.message,
    this.actionLabel,
    this.onAction,
  });

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(AppSpacing.xl),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(
              icon,
              size: 64,
              color: AppColors.textHint,
            ),
            const SizedBox(height: AppSpacing.md),
            Text(
              title,
              style: AppTypography.textTheme.titleMedium?.copyWith(
                color: AppColors.textPrimary,
              ),
              textAlign: TextAlign.center,
            ),
            if (message != null) ...[
              const SizedBox(height: AppSpacing.sm),
              Text(
                message!,
                style: AppTypography.textTheme.bodyMedium?.copyWith(
                  color: AppColors.textSecondary,
                ),
                textAlign: TextAlign.center,
              ),
            ],
            if (actionLabel != null && onAction != null) ...[
              const SizedBox(height: AppSpacing.lg),
              GlassButton(
                onPressed: onAction!,
                child: Text(actionLabel!),
              ),
            ],
          ],
        ),
      ),
    );
  }
}

