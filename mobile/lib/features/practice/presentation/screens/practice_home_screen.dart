import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../../core/theme/app_colors.dart';
import '../../../../core/theme/app_spacing.dart';
import '../../../../shared/widgets/backgrounds/modern_gradient_background_animated.dart';
import '../../../../shared/widgets/glass/index.dart';
import '../widgets/due_reviews_banner.dart';
import '../widgets/practice_mode_card.dart';

/// Main practice home screen showing available practice modes
class PracticeHomeScreen extends ConsumerWidget {
  const PracticeHomeScreen({super.key});

  // Mock data for demo purposes
  static const int _mockDueReviews = 8;
  static final DateTime _mockNextReviewTime = DateTime.now().add(const Duration(hours: 2));
  static const int _mockCurrentRank = 42;

  List<PracticeModeData> _getPracticeModes(BuildContext context) {
    return [
      // Quick Review
      PracticeModeData(
        id: 'quick_review',
        emoji: 'bolt',
        title: 'Ôn Tập Nhanh',
        description: '5-10 câu hỏi về những họa tiết bạn đã học',
        duration: '2-3 phút',
        rewards: const [
          Reward(icon: 'favorite', value: '+1'),
          Reward(icon: 'star', value: '+10 XP'),
        ],
        color: AppColors.info,
      ),

      // Category Deep Dive
      PracticeModeData(
        id: 'category_dive',
        emoji: 'menu_book',
        title: 'Ôn Sâu Theo Danh Mục',
        description: 'Chọn danh mục và ôn tập kỹ hơn',
        duration: '5-7 phút',
        rewards: const [
          Reward(icon: 'star', value: '+30 XP'),
          Reward(icon: 'diamond', value: '+5'),
        ],
        color: AppColors.primary,
        additionalInfo: 'Thảo Mộc | Linh Thú | Kiến Trúc',
      ),

      // Timed Challenge
      PracticeModeData(
        id: 'timed_challenge',
        emoji: 'timer',
        title: 'Thách Thức Tốc Độ',
        description: '10 câu hỏi trong 3 phút - Đua top bảng xếp hạng',
        duration: '3 phút',
        rewards: const [
          Reward(icon: 'star', value: '+50 XP'),
          Reward(icon: 'emoji_events', value: 'Top 10% bonus'),
        ],
        color: AppColors.warning,
        additionalInfo: 'Hạng hiện tại: #$_mockCurrentRank',
      ),

      // Boss Battle
      PracticeModeData(
        id: 'boss_battle',
        emoji: 'school',
        title: 'Đỉnh Exam',
        description: '25 câu hỏi, cần 80% để vượt qua và nhận chứng chỉ',
        duration: '10-15 phút',
        rewards: const [
          Reward(icon: 'school', value: 'Chứng chỉ'),
          Reward(icon: 'star', value: '+100 XP'),
          Reward(icon: 'diamond', value: '+20'),
        ],
        color: AppColors.error,
        isLocked: true,
        lockReason: 'Đạt 80% thành thạo để mở khóa',
      ),
    ];
  }

  void _handleQuickReview(BuildContext context) {
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(
        content: Text('Bắt đầu ôn tập nhanh...'),
        duration: Duration(seconds: 2),
      ),
    );
  }

  void _handlePracticeModeSelect(BuildContext context, String modeId) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text('Bắt đầu chế độ: $modeId'),
        duration: const Duration(seconds: 2),
      ),
    );
  }

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final practiceModes = _getPracticeModes(context);

    return ModernGradientBackgroundAnimated(
      child: Scaffold(
        backgroundColor: Colors.transparent,
        appBar: AppBar(
          backgroundColor: Colors.transparent,
          elevation: 0,
          title: const Text(
            'Luyện Tập',
            style: TextStyle(
              fontSize: 24,
              fontWeight: FontWeight.bold,
              color: Colors.white,
            ),
          ),
          leading: IconButton(
            icon: const Icon(Icons.arrow_back, color: Colors.white),
            onPressed: () => context.pop(),
          ),
          actions: [
            // Stats button
            IconButton(
              icon: const Icon(Icons.bar_chart, color: Colors.white),
              onPressed: () {
                ScaffoldMessenger.of(context).showSnackBar(
                  const SnackBar(
                    content: Text('Xem thống kê luyện tập'),
                    duration: Duration(seconds: 2),
                  ),
                );
              },
            ),
          ],
        ),
        body: SafeArea(
          child: LayoutBuilder(
            builder: (context, constraints) {
              final isCompact = constraints.maxWidth < 360;
              final horizontalPadding =
                  isCompact ? AppSpacing.md : AppSpacing.lg;
              return SingleChildScrollView(
                padding: EdgeInsets.symmetric(
                  horizontal: horizontalPadding,
                  vertical: AppSpacing.md,
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    // Compact header
                    Row(
                      children: [
                        const Icon(
                          Icons.fitness_center,
                          color: AppColors.primary,
                          size: 22,
                        ),
                        const SizedBox(width: AppSpacing.sm),
                        Text(
                          'Chế độ luyện tập',
                          style: Theme.of(context).textTheme.titleLarge?.copyWith(
                                color: Colors.white,
                                fontWeight: FontWeight.bold,
                              ),
                        ),
                      ],
                    ),
                    const SizedBox(height: AppSpacing.sm),

                    // Due Reviews Banner
                    DueReviewsBanner(
                      dueCount: _mockDueReviews,
                      nextReviewTime: _mockNextReviewTime,
                      onTap: () => _handleQuickReview(context),
                    ),
                    const SizedBox(height: AppSpacing.md),

                    // Practice mode cards
                    ...practiceModes.map((mode) {
                      return Padding(
                        padding: const EdgeInsets.only(bottom: AppSpacing.md),
                        child: PracticeModeCard(
                          mode: mode,
                          onTap: () =>
                              _handlePracticeModeSelect(context, mode.id),
                        ),
                      );
                    }).toList(),

                    const SizedBox(height: AppSpacing.sm),

                    // Info card with 3D press effect
                    PressableGlassCard(
                      onTap: () {
                        ScaffoldMessenger.of(context).showSnackBar(
                          const SnackBar(
                            content: Text('💡 Tip acknowledged!'),
                            duration: Duration(seconds: 1),
                          ),
                        );
                      },
                      padding: const EdgeInsets.all(AppSpacing.md),
                      borderRadius: BorderRadius.circular(12),
                      backgroundColor: Colors.white,
                      opacity: 0.05,
                      border: Border.all(
                        color: Colors.white.withOpacity(0.1),
                        width: 1,
                      ),
                      child: Row(
                        children: [
                          Icon(
                            Icons.lightbulb_outline,
                            color: AppColors.info,
                            size: 24,
                          ),
                          const SizedBox(width: AppSpacing.md),
                          Expanded(
                            child: Text(
                              'Mẹo: Luyện tập đều đặn mỗi ngày giúp ghi nhớ tốt hơn học dồn một lúc',
                              style: Theme.of(context)
                                  .textTheme
                                  .bodyMedium
                                  ?.copyWith(
                                    color: Colors.white70,
                                  ),
                            ),
                          ),
                        ],
                      ),
                    ),

                    const SizedBox(height: AppSpacing.xl),

                    // Progress stats card
                    _buildProgressStatsCard(context),

                    const SizedBox(height: AppSpacing.xl),
                  ],
                ),
              );
            },
          ),
        ),
      ),
    );
  }

  Widget _buildProgressStatsCard(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(AppSpacing.lg),
      decoration: BoxDecoration(
        gradient: LinearGradient(
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
          colors: [
            AppColors.primary.withOpacity(0.1),
            AppColors.primary.withOpacity(0.05),
          ],
        ),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(
          color: AppColors.primary.withOpacity(0.2),
          width: 1,
        ),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              const Icon(
                Icons.show_chart,
                color: AppColors.primary,
                size: 24,
              ),
              const SizedBox(width: AppSpacing.sm),
              Text(
                'Thống Kê Luyện Tập',
                style: Theme.of(context).textTheme.titleMedium?.copyWith(
                      color: Colors.white,
                      fontWeight: FontWeight.bold,
                    ),
              ),
            ],
          ),
          const SizedBox(height: AppSpacing.md),
          _buildStatRow(context, 'Ngày luyện tập liên tiếp', '5 ngày', icon: Icons.calendar_today_rounded),
          const SizedBox(height: AppSpacing.sm),
          _buildStatRow(context, 'Tổng câu hỏi đã làm', '247 câu', icon: Icons.check_circle_rounded),
          const SizedBox(height: AppSpacing.sm),
          _buildStatRow(context, 'Tỷ lệ chính xác', '85%', icon: Icons.track_changes_rounded),
          const SizedBox(height: AppSpacing.sm),
          _buildStatRow(context, 'Họa tiết thành thạo', '12/45', icon: Icons.emoji_events_rounded),
        ],
      ),
    );
  }

  Widget _buildStatRow(BuildContext context, String label, String value, {IconData? icon}) {
    return Row(
      children: [
        if (icon != null) ...[
          Icon(
            icon,
            size: 18,
            color: AppColors.xpGold,
          ),
          const SizedBox(width: AppSpacing.xs),
        ],
        Expanded(
          child: Text(
            label,
            style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                  color: Colors.white70,
                ),
            maxLines: 2,
            overflow: TextOverflow.ellipsis,
          ),
        ),
        const SizedBox(width: AppSpacing.sm),
        Text(
          value,
          style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                color: Colors.white,
                fontWeight: FontWeight.bold,
              ),
        ),
      ],
    );
  }
}
