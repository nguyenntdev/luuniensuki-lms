import 'package:flutter/material.dart';
import '../../../core/theme/app_colors.dart';
import '../../../core/theme/app_spacing.dart';
import '../../../core/theme/app_typography.dart';
import '../glass/glass_button.dart';

/// A widget that displays an error state with an icon, message, and optional retry button.
///
/// This widget is used to show error states throughout the app with a consistent
/// design. It can optionally include a retry button when an [onRetry] callback is provided.
///
/// Example:
/// ```dart
/// AppErrorState(
///   message: 'Không thể tải dữ liệu',
///   onRetry: () => _loadData(),
/// )
/// ```
class AppErrorState extends StatelessWidget {
  /// The error message to display
  final String message;

  /// Optional callback when the retry button is tapped
  final VoidCallback? onRetry;

  /// The icon to display (defaults to Icons.error_outline)
  final IconData icon;

  /// The label for the retry button (defaults to 'Thử lại')
  final String retryLabel;

  const AppErrorState({
    super.key,
    required this.message,
    this.onRetry,
    this.icon = Icons.error_outline,
    this.retryLabel = 'Thử lại',
  });

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(AppSpacing.lg),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(
              icon,
              size: 64,
              color: AppColors.error,
            ),
            const SizedBox(height: AppSpacing.md),
            Text(
              message,
              style: AppTypography.bodyLarge.copyWith(
                color: AppColors.textPrimary,
              ),
              textAlign: TextAlign.center,
            ),
            if (onRetry != null) ...[
              const SizedBox(height: AppSpacing.lg),
              GlassButton(
                onPressed: onRetry!,
                icon: Icons.refresh,
                text: retryLabel,
              ),
            ],
          ],
        ),
      ),
    );
  }
}

