import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:cached_network_image/cached_network_image.dart';

import '../../../../core/theme/app_colors.dart';
import '../../../../core/theme/app_spacing.dart';
import '../../../../core/theme/app_typography.dart';
import '../../../../core/utils/url_utils.dart';
import '../../../../routing/route_names.dart';
import '../../../urn_viewer/data/models/urn_dtos.dart';
import '../../../gems/presentation/providers/gems_provider.dart';
import '../../../gems/domain/entities/gem_transaction.dart';
import '../../../auth/presentation/providers/auth_provider.dart';
import '../../../mascot/presentation/widgets/mascot_bubble.dart';
import '../../../mascot/presentation/widgets/mascot_widget.dart';
import '../../../mascot/domain/mascot_messages.dart';
import '../providers/motif_detail_provider.dart';

/// Lesson tab showing lesson content and action buttons.
class LessonTab extends ConsumerWidget {
  final MotifDetailDto motif;
  final LessonContentDto? lesson;
  final UserProgressDto? progress;

  const LessonTab({
    super.key,
    required this.motif,
    this.lesson,
    this.progress,
  });

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    if (lesson == null) {
      return _buildEmptyState();
    }

    final isCompact = MediaQuery.of(context).size.width < 360;
    final contentPadding = EdgeInsets.all(
      isCompact ? AppSpacing.md : AppSpacing.lg,
    );

    return SingleChildScrollView(
      padding: contentPadding,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Introduction
          if (lesson!.introText != null && lesson!.introText!.isNotEmpty) ...[
            _LessonSection(
              title: 'Giới thiệu',
              icon: Icons.info_outline,
              content: lesson!.introText!,
            ),
            const SizedBox(height: 20),
          ],

          // Description
          if (lesson!.description != null &&
              lesson!.description!.isNotEmpty) ...[
            _LessonSection(
              title: 'Mô tả chi tiết',
              icon: Icons.description_outlined,
              content: lesson!.description!,
            ),
            const SizedBox(height: 20),
          ],

          // Symbolism
          if (lesson!.symbolism != null && lesson!.symbolism!.isNotEmpty) ...[
            _LessonSection(
              title: 'Ý nghĩa biểu tượng',
              icon: Icons.auto_awesome_outlined,
              content: lesson!.symbolism!,
              accentColor: AppColors.primary,
            ),
            const SizedBox(height: 20),
          ],

          // Historical context
          if (lesson!.historicalContext != null &&
              lesson!.historicalContext!.isNotEmpty) ...[
            _LessonSection(
              title: 'Bối cảnh lịch sử',
              icon: Icons.history_edu_outlined,
              content: lesson!.historicalContext!,
            ),
            const SizedBox(height: 20),
          ],

          // Fun fact
          if (lesson!.funFact != null && lesson!.funFact!.isNotEmpty) ...[
            _FunFactCard(fact: lesson!.funFact!),
            const SizedBox(height: 20),
          ],

          // Image gallery placeholder
          if (lesson!.images.isNotEmpty) ...[
            _ImageGalleryPreview(images: lesson!.images),
            const SizedBox(height: 20),
          ],

          const SizedBox(height: 16),

          // Action buttons
          _buildActionButtons(context, ref),

          const SizedBox(height: 32),
        ],
      ),
    );
  }

  Widget _buildEmptyState() {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(32),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(
              Icons.school_outlined,
              size: 64,
              color: AppColors.textHint,
            ),
            const SizedBox(height: 16),
            Text(
              'Chưa có bài học',
              style: AppTypography.textTheme.titleMedium?.copyWith(
                color: AppColors.textPrimary,
              ),
            ),
            const SizedBox(height: 8),
            Text(
              'Nội dung bài học đang được cập nhật.',
              style: AppTypography.textTheme.bodyMedium?.copyWith(
                color: AppColors.textSecondary,
              ),
              textAlign: TextAlign.center,
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildActionButtons(BuildContext context, WidgetRef ref) {
    final status = progress?.status ?? 'hidden';
    final lessonCompletion = ref.watch(lessonCompletionProvider);
    final isLoading = lessonCompletion is AsyncLoading;

    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        _ActionButton(
          label: 'Hỏi AI về họa tiết',
          icon: Icons.auto_awesome_outlined,
          isPrimary: false,
          onPressed: () => context.push(
            '/motifs/${motif.id}/ai-chat',
          ),
        ),
        const SizedBox(height: 12),
        // Complete lesson button (for discovered status)
        if (status == 'discovered')
          _ActionButton(
            label: 'Hoàn thành bài học',
            icon: Icons.check_circle_outline,
            isLoading: isLoading,
            onPressed: isLoading ? null : () => _completeLesson(context, ref),
          ),

        // Quiz button (for learned or mastered status)
        if (status == 'learned' || status == 'mastered') ...[
          _ActionButton(
            label: status == 'mastered'
                ? 'Làm lại trắc nghiệm'
                : 'Làm trắc nghiệm',
            icon: Icons.quiz_outlined,
            isPrimary: status == 'learned',
            onPressed: () => context.push(
              RoutePaths.quiz(motif.id),
            ),
          ),
          if (status == 'mastered' && progress?.quizBestScore != null)
            Padding(
              padding: const EdgeInsets.only(top: 12),
              child: Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Icon(
                    Icons.emoji_events,
                    size: 16,
                    color: AppColors.xpGold,
                  ),
                  const SizedBox(width: 6),
                  Text(
                    'Điểm cao nhất: ${progress!.quizBestScore}%',
                    style: AppTypography.textTheme.bodySmall?.copyWith(
                      color: AppColors.textSecondary,
                    ),
                  ),
                ],
              ),
            ),
        ],

        // Hidden status message
        if (status == 'hidden')
          Container(
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(
              color: AppColors.surfaceElevated,
              borderRadius: BorderRadius.circular(12),
              border: Border.all(color: AppColors.border),
            ),
            child: Row(
              children: [
                Icon(
                  Icons.explore_outlined,
                  color: AppColors.textHint,
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: Text(
                    'Hãy khám phá họa tiết này trên mô hình 3D để mở khóa bài học.',
                    style: AppTypography.textTheme.bodyMedium?.copyWith(
                      color: AppColors.textSecondary,
                    ),
                  ),
                ),
              ],
            ),
          ),
      ],
    );
  }

  Future<void> _completeLesson(BuildContext context, WidgetRef ref) async {
    final result = await ref
        .read(lessonCompletionProvider.notifier)
        .completeLesson(motif.id);

    if (!context.mounted) return;

    if (result == null) {
      // Show error message
      final lessonState = ref.read(lessonCompletionProvider);
      final errorMessage = lessonState.hasError
          ? lessonState.error.toString()
          : 'Có lỗi xảy ra khi hoàn thành bài học';

      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(errorMessage),
          backgroundColor: AppColors.error,
          behavior: SnackBarBehavior.floating,
        ),
      );
      return;
    }

    // Award gems for completing lesson
    await ref.read(gemsNotifierProvider.notifier).addGems(
          amount: 10,
          type: GemTransactionType.earnedLesson,
          description: 'Hoàn thành bài học: ${motif.name}',
        );

    // Check for 7-day streak milestone and award bonus gems
    final user = ref.read(currentUserProvider);
    if (user != null &&
        user.currentStreak >= 7 &&
        user.currentStreak % 7 == 0) {
      await ref.read(gemsNotifierProvider.notifier).addGems(
            amount: 50,
            type: GemTransactionType.earnedStreak,
            description: 'Chuỗi học tập ${user.currentStreak} ngày!',
          );
    }

    // Show completion dialog
    showDialog(
      context: context,
      barrierDismissible: false,
      builder: (context) => _LessonCompletionDialog(
        xpEarned: result.xpEarned,
        onDismiss: () {
          Navigator.pop(context);
        },
        onTakeQuiz: () {
          Navigator.pop(context);
          context.push(
            RoutePaths.quiz(motif.id),
          );
        },
      ),
    );

    // Show mascot message after dialog
    Future.delayed(const Duration(milliseconds: 500), () {
      if (context.mounted) {
        showMascotBubble(
          context: context,
          message: MascotMessages.random(MascotMessages.lessonComplete),
          expression: MascotExpression.celebrating,
          duration: const Duration(seconds: 4),
        );
      }
    });
  }
}

/// Lesson section widget
class _LessonSection extends StatelessWidget {
  final String title;
  final IconData icon;
  final String content;
  final Color? accentColor;

  const _LessonSection({
    required this.title,
    required this.icon,
    required this.content,
    this.accentColor,
  });

  @override
  Widget build(BuildContext context) {
    final color = accentColor ?? AppColors.textSecondary;

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        // Header
        Row(
          children: [
            Icon(icon, size: 18, color: color),
            const SizedBox(width: 8),
            Text(
              title,
              style: AppTypography.textTheme.titleSmall?.copyWith(
                color: color,
                fontWeight: FontWeight.w600,
              ),
            ),
          ],
        ),
        const SizedBox(height: 12),

        // Content
        Container(
          width: double.infinity,
          padding: const EdgeInsets.all(16),
          decoration: BoxDecoration(
            color: AppColors.surface,
            borderRadius: BorderRadius.circular(12),
            border: Border.all(color: AppColors.border),
          ),
          child: Text(
            content,
            style: AppTypography.vietnameseText.copyWith(
              color: AppColors.textPrimary,
              height: 1.7,
            ),
          ),
        ),
      ],
    );
  }
}

/// Fun fact card widget
class _FunFactCard extends StatelessWidget {
  final String fact;

  const _FunFactCard({required this.fact});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        gradient: LinearGradient(
          colors: [
            AppColors.primary.withOpacity(0.1),
            AppColors.primary.withOpacity(0.05),
          ],
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
        ),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(
          color: AppColors.primary.withOpacity(0.3),
        ),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              const Icon(
                Icons.lightbulb_rounded,
                color: AppColors.warning,
                size: 20,
              ),
              const SizedBox(width: 8),
              Text(
                'Điều thú vị',
                style: AppTypography.textTheme.titleSmall?.copyWith(
                  color: AppColors.primary,
                  fontWeight: FontWeight.w600,
                ),
              ),
            ],
          ),
          const SizedBox(height: 12),
          Text(
            fact,
            style: AppTypography.vietnameseText.copyWith(
              color: AppColors.textPrimary,
              height: 1.6,
            ),
          ),
        ],
      ),
    );
  }
}

/// Image gallery preview widget
class _ImageGalleryPreview extends StatelessWidget {
  final List<String> images;

  const _ImageGalleryPreview({required this.images});

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          children: [
            Icon(
              Icons.photo_library_outlined,
              size: 18,
              color: AppColors.textSecondary,
            ),
            const SizedBox(width: 8),
            Text(
              'Hình ảnh (${images.length})',
              style: AppTypography.textTheme.titleSmall?.copyWith(
                color: AppColors.textSecondary,
                fontWeight: FontWeight.w600,
              ),
            ),
          ],
        ),
        const SizedBox(height: 12),
        LayoutBuilder(
          builder: (context, constraints) {
            final isCompact = constraints.maxWidth < 360;
            final size = isCompact ? 84.0 : 100.0;

            return SizedBox(
              height: size,
              child: ListView.separated(
                scrollDirection: Axis.horizontal,
                itemCount: images.length > 4 ? 4 : images.length,
                separatorBuilder: (_, __) => const SizedBox(width: 8),
                itemBuilder: (context, index) {
                  if (index == 3 && images.length > 4) {
                    return _buildMoreIndicator(size);
                  }
                  return _buildImageThumbnail(images[index], size);
                },
              ),
            );
          },
        ),
      ],
    );
  }

  Widget _buildImageThumbnail(String imageUrl, double size) {
    // Convert relative URL to full URL
    final fullImageUrl = UrlUtils.getImageUrl(imageUrl);

    return ClipRRect(
      borderRadius: BorderRadius.circular(8),
      child: Container(
        width: size,
        height: size,
        color: AppColors.surfaceVariant,
        child: fullImageUrl.isNotEmpty
            ? CachedNetworkImage(
                imageUrl: fullImageUrl,
                fit: BoxFit.cover,
                placeholder: (context, url) => const Center(
                  child: CircularProgressIndicator(
                    strokeWidth: 2,
                    color: AppColors.primary,
                  ),
                ),
                errorWidget: (context, url, error) {
                  debugPrint(
                      '[MOTIF_IMAGE] Failed to load lesson image: $fullImageUrl - Error: $error');
                  return Icon(
                    Icons.broken_image,
                    color: AppColors.textHint,
                  );
                },
              )
            : Icon(
                Icons.image,
                color: AppColors.textHint,
              ),
      ),
    );
  }

  Widget _buildMoreIndicator(double size) {
    return Container(
      width: size,
      height: size,
      decoration: BoxDecoration(
        color: AppColors.surfaceVariant,
        borderRadius: BorderRadius.circular(8),
      ),
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Text(
            '+${images.length - 3}',
            style: AppTypography.textTheme.titleLarge?.copyWith(
              color: AppColors.primary,
              fontWeight: FontWeight.bold,
            ),
          ),
          Text(
            'ảnh',
            style: AppTypography.textTheme.bodySmall?.copyWith(
              color: AppColors.textSecondary,
            ),
          ),
        ],
      ),
    );
  }
}

/// Action button widget
class _ActionButton extends StatelessWidget {
  final String label;
  final IconData icon;
  final VoidCallback? onPressed;
  final bool isPrimary;
  final bool isLoading;

  const _ActionButton({
    required this.label,
    required this.icon,
    this.onPressed,
    this.isPrimary = true,
    this.isLoading = false,
  });

  @override
  Widget build(BuildContext context) {
    if (isPrimary) {
      return SizedBox(
        height: 52,
        child: ElevatedButton.icon(
          onPressed: onPressed,
          icon: isLoading
              ? const SizedBox(
                  width: 20,
                  height: 20,
                  child: CircularProgressIndicator(
                    strokeWidth: 2,
                    color: AppColors.onPrimary,
                  ),
                )
              : Icon(icon),
          label: Text(label),
          style: ElevatedButton.styleFrom(
            backgroundColor: AppColors.primary,
            foregroundColor: AppColors.onPrimary,
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(12),
            ),
            textStyle: const TextStyle(
              fontSize: 16,
              fontWeight: FontWeight.w600,
            ),
          ),
        ),
      );
    }

    return SizedBox(
      height: 52,
      child: OutlinedButton.icon(
        onPressed: onPressed,
        icon: Icon(icon),
        label: Text(label),
        style: OutlinedButton.styleFrom(
          foregroundColor: AppColors.primary,
          side: BorderSide(color: AppColors.primary),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(12),
          ),
          textStyle: const TextStyle(
            fontSize: 16,
            fontWeight: FontWeight.w600,
          ),
        ),
      ),
    );
  }
}

/// Lesson completion dialog
class _LessonCompletionDialog extends StatelessWidget {
  final int xpEarned;
  final VoidCallback onDismiss;
  final VoidCallback onTakeQuiz;

  const _LessonCompletionDialog({
    required this.xpEarned,
    required this.onDismiss,
    required this.onTakeQuiz,
  });

  @override
  Widget build(BuildContext context) {
    return Dialog(
      backgroundColor: AppColors.surface,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(20),
      ),
      child: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            // Success icon
            Container(
              width: 80,
              height: 80,
              decoration: BoxDecoration(
                color: AppColors.success.withOpacity(0.15),
                shape: BoxShape.circle,
              ),
              child: const Icon(
                Icons.check_circle,
                size: 48,
                color: AppColors.success,
              ),
            ),

            const SizedBox(height: 20),

            // Title
            Text(
              'Hoàn thành bài học!',
              style: AppTypography.textTheme.headlineSmall?.copyWith(
                color: AppColors.textPrimary,
                fontWeight: FontWeight.bold,
              ),
            ),

            const SizedBox(height: 12),

            // XP earned
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
              decoration: BoxDecoration(
                color: AppColors.xpGold.withOpacity(0.15),
                borderRadius: BorderRadius.circular(20),
              ),
              child: Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  const Icon(
                    Icons.star,
                    size: 20,
                    color: AppColors.xpGold,
                  ),
                  const SizedBox(width: 6),
                  Text(
                    '+$xpEarned XP',
                    style: AppTypography.xpCounter,
                  ),
                ],
              ),
            ),

            const SizedBox(height: 24),

            // Buttons
            Row(
              children: [
                Expanded(
                  child: OutlinedButton(
                    onPressed: onDismiss,
                    style: OutlinedButton.styleFrom(
                      foregroundColor: AppColors.textSecondary,
                      side: BorderSide(color: AppColors.border),
                      padding: const EdgeInsets.symmetric(vertical: 12),
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(10),
                      ),
                    ),
                    child: const Text('Đóng'),
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: ElevatedButton(
                    onPressed: onTakeQuiz,
                    style: ElevatedButton.styleFrom(
                      backgroundColor: AppColors.primary,
                      foregroundColor: AppColors.onPrimary,
                      padding: const EdgeInsets.symmetric(vertical: 12),
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(10),
                      ),
                    ),
                    child: const Text('Làm trắc nghiệm'),
                  ),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}
