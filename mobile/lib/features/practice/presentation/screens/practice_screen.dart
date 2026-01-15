import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../../../core/theme/app_colors.dart';
import '../../../../core/theme/app_spacing.dart';
import '../../../../core/theme/app_typography.dart';
import '../../../../shared/widgets/glass/animated_background.dart';
import '../../../hearts/presentation/widgets/hearts_display.dart';
import '../../../streak/presentation/providers/streak_provider.dart';
import '../providers/practice_provider.dart';
import '../providers/quiz_session_provider.dart';

/// Main practice screen with daily stats and practice modes
class PracticeScreen extends ConsumerWidget {
  const PracticeScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final stats = ref.watch(dailyPracticeStatsProvider);
    final streakState = ref.watch(streakNotifierProvider);
    final screenWidth = MediaQuery.of(context).size.width;
    final horizontalPadding =
        screenWidth < 360 ? AppSpacing.md : AppSpacing.lg;

    return AnimatedGradientBackground(
      child: Scaffold(
        backgroundColor: Colors.transparent,
        body: SafeArea(
          child: CustomScrollView(
            slivers: [
              // App Bar
              SliverToBoxAdapter(
                child: _buildHeader(context),
              ),

              // Daily Stats Card
              SliverToBoxAdapter(
                child: Padding(
                  padding: EdgeInsets.all(horizontalPadding),
                  child: _buildDailyStatsCard(
                      context, stats, streakState.data.currentStreak),
                ),
              ),

              // Quick Review Button
              SliverToBoxAdapter(
                child: Padding(
                  padding: EdgeInsets.symmetric(horizontal: horizontalPadding),
                  child: _buildQuickReviewButton(context, ref),
                ),
              ),

              // Section Headers and Categories
              SliverToBoxAdapter(
                child: Padding(
                  padding: EdgeInsets.all(horizontalPadding),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const SizedBox(height: AppSpacing.md),
                      _buildSectionHeader(
                          context, 'Cần Ôn Tập', Icons.schedule),
                      const SizedBox(height: AppSpacing.md),
                    ],
                  ),
                ),
              ),

              // Due for Review Items
              _buildUrnsList(context, 'Cần Ôn Tập', 8, AppColors.warning),

              SliverToBoxAdapter(
                child: Padding(
                  padding: EdgeInsets.all(horizontalPadding),
                  child: _buildSectionHeader(
                      context, 'Học Mới', Icons.new_releases),
                ),
              ),

              // New Items
              _buildUrnsList(context, 'Học Mới', 5, AppColors.info),

              SliverToBoxAdapter(
                child: Padding(
                  padding: EdgeInsets.all(horizontalPadding),
                  child: _buildSectionHeader(
                      context, 'Đã Thành Thạo', Icons.stars),
                ),
              ),

              // Mastered Items
              _buildUrnsList(context, 'Đã Thành Thạo', 12, AppColors.success),

              const SliverToBoxAdapter(
                child: SizedBox(height: AppSpacing.xl),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildHeader(BuildContext context) {
    final screenWidth = MediaQuery.of(context).size.width;
    final isCompact = screenWidth < 360;

    return Padding(
      padding: EdgeInsets.fromLTRB(
        AppSpacing.lg,
        isCompact ? AppSpacing.sm : AppSpacing.md,
        AppSpacing.lg,
        AppSpacing.sm,
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Wrap(
            alignment: WrapAlignment.spaceBetween,
            crossAxisAlignment: WrapCrossAlignment.center,
            runSpacing: AppSpacing.xs,
            children: [
              Text(
                'Luyện tập',
                style: AppTypography.textTheme.headlineSmall?.copyWith(
                  color: Colors.white,
                  fontSize: isCompact ? 20 : 24,
                  fontWeight: FontWeight.bold,
                ),
              ),
              const CompactHeartsDisplay(),
            ],
          ),
          SizedBox(height: isCompact ? AppSpacing.xs : AppSpacing.sm),
          Text(
            'Chọn chế độ để luyện tập nhanh',
            style: AppTypography.textTheme.bodySmall?.copyWith(
              color: Colors.white.withOpacity(0.7),
              letterSpacing: 0.2,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildDailyStatsCard(
      BuildContext context, Map<String, int> stats, int streak) {
    return LayoutBuilder(
      builder: (context, constraints) {
        final isCompact = constraints.maxWidth < 360;
        final padding = isCompact ? AppSpacing.md : AppSpacing.lg;
        return Container(
          padding: EdgeInsets.all(padding),
          decoration: BoxDecoration(
            gradient: LinearGradient(
              begin: Alignment.topLeft,
              end: Alignment.bottomRight,
              colors: [
                AppColors.primary.withOpacity(0.15),
                AppColors.primary.withOpacity(0.05),
              ],
            ),
            borderRadius: BorderRadius.circular(20),
            border: Border.all(
              color: AppColors.primary.withOpacity(0.3),
              width: 1.5,
            ),
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                'Thành Tích Hôm Nay',
                style: AppTypography.textTheme.titleLarge?.copyWith(
                      color: Colors.white,
                      fontWeight: FontWeight.bold,
                    ),
              ),
              const SizedBox(height: AppSpacing.md),
              Wrap(
                spacing: AppSpacing.lg,
                runSpacing: AppSpacing.md,
                children: [
                  _buildStatItem(
                    context,
                    '✨',
                    '${stats['xpEarned'] ?? 0}',
                    'XP',
                    isCompact,
                  ),
                  _buildStatItem(context, '🔥', '$streak', 'Ngày', isCompact),
                  _buildStatItem(
                    context,
                    '❤️',
                    '${stats['hearts'] ?? 5}',
                    'Tim',
                    isCompact,
                  ),
                  _buildStatItem(
                    context,
                    '✅',
                    '${stats['questionsAnswered'] ?? 0}',
                    'Câu',
                    isCompact,
                  ),
                ],
              ),
            ],
          ),
        );
      },
    );
  }

  Widget _buildStatItem(
    BuildContext context,
    String emoji,
    String value,
    String label,
    bool isCompact,
  ) {
    return Column(
      children: [
        Text(emoji, style: TextStyle(fontSize: isCompact ? 22 : 28)),
        const SizedBox(height: 4),
        Text(
          value,
          style: Theme.of(context).textTheme.titleLarge?.copyWith(
                color: AppColors.primary,
                fontWeight: FontWeight.bold,
              ),
        ),
        Text(
          label,
          style: Theme.of(context).textTheme.bodySmall?.copyWith(
                color: AppColors.textSecondary,
              ),
        ),
      ],
    );
  }

  Widget _buildQuickReviewButton(BuildContext context, WidgetRef ref) {
    return Material(
      color: Colors.transparent,
      child: InkWell(
        onTap: () {
          // Start quick review with mock questions
          ref.read(quizSessionProvider.notifier).startMixedQuiz();
          context.push('/practice/session');
        },
        borderRadius: BorderRadius.circular(16),
        child: Container(
          padding: const EdgeInsets.all(AppSpacing.lg),
          decoration: BoxDecoration(
            gradient: LinearGradient(
              begin: Alignment.topLeft,
              end: Alignment.bottomRight,
              colors: [
                AppColors.success,
                AppColors.success.withOpacity(0.7),
              ],
            ),
            borderRadius: BorderRadius.circular(16),
            boxShadow: [
              BoxShadow(
                color: AppColors.success.withOpacity(0.3),
                blurRadius: 20,
                offset: const Offset(0, 8),
              ),
            ],
          ),
          child: LayoutBuilder(
            builder: (context, constraints) {
              final isCompact = constraints.maxWidth < 360;
              return Row(
                children: [
                  Container(
                    padding: const EdgeInsets.all(12),
                    decoration: BoxDecoration(
                      color: Colors.white.withOpacity(0.2),
                      borderRadius: BorderRadius.circular(12),
                    ),
                    child: Icon(
                      Icons.play_arrow,
                      color: Colors.white,
                      size: isCompact ? 26 : 32,
                    ),
                  ),
                  const SizedBox(width: AppSpacing.md),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          'Ôn Tập Nhanh',
                          style: TextStyle(
                            color: Colors.white,
                            fontSize: isCompact ? 18 : 20,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                        const SizedBox(height: 4),
                        Text(
                          'Bắt đầu ôn tập ngay • 5-10 câu hỏi',
                          style: TextStyle(
                            color: Colors.white.withOpacity(0.9),
                            fontSize: isCompact ? 12 : 14,
                          ),
                        ),
                      ],
                    ),
                  ),
                  const Icon(
                    Icons.arrow_forward_ios,
                    color: Colors.white,
                    size: 18,
                  ),
                ],
              );
            },
          ),
        ),
      ),
    );
  }

  Widget _buildSectionHeader(
      BuildContext context, String title, IconData icon) {
    return Row(
      children: [
        Icon(icon, color: AppColors.primary, size: 24),
        const SizedBox(width: AppSpacing.sm),
        Expanded(
          child: Text(
            title,
            style: AppTypography.textTheme.titleLarge?.copyWith(
                  color: Colors.white,
                  fontWeight: FontWeight.bold,
                ),
            maxLines: 1,
            overflow: TextOverflow.ellipsis,
          ),
        ),
      ],
    );
  }

  Widget _buildUrnsList(
      BuildContext context, String category, int count, Color accentColor) {
    final screenWidth = MediaQuery.of(context).size.width;
    final horizontalPadding = screenWidth < 360 ? AppSpacing.md : AppSpacing.lg;
    return SliverPadding(
      padding: EdgeInsets.symmetric(horizontal: horizontalPadding),
      sliver: SliverList(
        delegate: SliverChildBuilderDelegate(
          (context, index) {
            return Padding(
              padding: const EdgeInsets.only(bottom: AppSpacing.md),
              child: _buildUrnCard(context, index, category, accentColor),
            );
          },
          childCount: count > 3 ? 3 : count, // Show max 3 items per category
        ),
      ),
    );
  }

  Widget _buildUrnCard(
      BuildContext context, int index, String category, Color accentColor) {
    final mockUrns = [
      {'name': 'Họa Tiết Rồng', 'progress': 0.8, 'items': 12},
      {'name': 'Họa Tiết Phượng', 'progress': 0.6, 'items': 8},
      {'name': 'Họa Tiết Sen', 'progress': 0.4, 'items': 5},
    ];

    final urn = mockUrns[index % mockUrns.length];
    final progressValue = urn['progress'] as double;

    return Material(
      color: Colors.transparent,
      child: InkWell(
        onTap: () {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(content: Text('Mở ${urn['name']}...')),
          );
        },
        borderRadius: BorderRadius.circular(12),
        child: LayoutBuilder(
          builder: (context, constraints) {
            final isCompact = constraints.maxWidth < 360;
            return Container(
              padding: EdgeInsets.all(isCompact ? 12 : AppSpacing.md),
              decoration: BoxDecoration(
                color: AppColors.surface.withOpacity(0.5),
                borderRadius: BorderRadius.circular(14),
                border: Border.all(
                  color: accentColor.withOpacity(0.3),
                  width: 1,
                ),
              ),
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Container(
                    width: isCompact ? 44 : 50,
                    height: isCompact ? 44 : 50,
                    decoration: BoxDecoration(
                      gradient: LinearGradient(
                        colors: [accentColor, accentColor.withOpacity(0.6)],
                      ),
                      borderRadius: BorderRadius.circular(12),
                    ),
                    child: const Icon(Icons.terrain,
                        color: Colors.white, size: 26),
                  ),
                  const SizedBox(width: AppSpacing.md),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          urn['name'] as String,
                          style: TextStyle(
                            color: Colors.white,
                            fontSize: isCompact ? 14 : 16,
                            fontWeight: FontWeight.bold,
                          ),
                          maxLines: 2,
                          overflow: TextOverflow.ellipsis,
                        ),
                        const SizedBox(height: 6),
                        _buildPeakProgress(
                            progressValue, accentColor, isCompact),
                        const SizedBox(height: 6),
                        Text(
                          '${(progressValue * 100).toInt()}% hoàn thành',
                          style: TextStyle(
                            color: AppColors.textSecondary,
                            fontSize: isCompact ? 11 : 12,
                          ),
                        ),
                      ],
                    ),
                  ),
                  const SizedBox(width: AppSpacing.sm),
                  Container(
                    padding:
                        const EdgeInsets.symmetric(horizontal: 8, vertical: 6),
                    decoration: BoxDecoration(
                      color: accentColor.withOpacity(0.2),
                      borderRadius: BorderRadius.circular(8),
                    ),
                    child: Text(
                      '${urn['items']} mục',
                      style: TextStyle(
                        color: accentColor,
                        fontSize: isCompact ? 11 : 12,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                  ),
                ],
              ),
            );
          },
        ),
      ),
    );
  }

  Widget _buildPeakProgress(
    double progress,
    Color accentColor,
    bool isCompact,
  ) {
    const totalPeaks = 5;
    final completed = (progress * totalPeaks).round().clamp(1, totalPeaks);

    return Row(
      children: List.generate(totalPeaks, (index) {
        final isActive = index < completed;
        return Padding(
          padding: EdgeInsets.only(right: index == totalPeaks - 1 ? 0 : 4),
          child: Icon(
            Icons.terrain,
            size: isCompact ? 12 : 14,
            color: isActive ? accentColor : AppColors.textHint.withOpacity(0.6),
          ),
        );
      }),
    );
  }
}
