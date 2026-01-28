import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../../core/theme/app_colors.dart';
import '../../../../core/theme/app_spacing.dart';
import '../../../../core/theme/app_typography.dart';
import '../../../../shared/widgets/effects/shimmer_widget.dart';
import '../../../../shared/widgets/progress/circular_progress_badge.dart';
import '../../../../shared/widgets/text/gradient_text.dart';
import '../../../streak/presentation/widgets/compact_streak_widget.dart';
import '../providers/dashboard_summary_provider.dart';
import '../widgets/daily_lessons_widget.dart';
import '../widgets/urn_path_card.dart';

/// Learning Path screen - Shows structured learning progression
/// with daily lessons and urn path visualization
class LearningPathScreen extends ConsumerWidget {
  const LearningPathScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return SafeArea(
      bottom: false,  // Allow content to extend behind navbar
      child: CustomScrollView(
        slivers: [
          // Header
          _buildHeader(context, ref),

          // Daily Lessons Section
          SliverToBoxAdapter(
            child: Padding(
              padding: const EdgeInsets.fromLTRB(
                AppSpacing.md,
                AppSpacing.sm,
                AppSpacing.md,
                AppSpacing.sm,
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  // Section title with gradient
                  GradientText(
                    'Chặng leo hôm nay',
                    gradient: LinearGradient(
                      colors: [
                        Colors.white,
                        Colors.white.withOpacity(0.8),
                      ],
                    ),
                    style: AppTypography.cardTitle.copyWith(
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                ],
              ),
            ),
          ),

          // Daily Lessons Horizontal List
          const SliverToBoxAdapter(
            child: DailyLessonsWidget(),
          ),

          // Urn Path Section Header
          SliverToBoxAdapter(
            child: Padding(
              padding: const EdgeInsets.fromLTRB(
                AppSpacing.md,
                AppSpacing.xl,
                AppSpacing.md,
                AppSpacing.xs,
              ),
              child: Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      GradientText(
                        'Lộ trình theo đỉnh',
                        gradient: LinearGradient(
                          colors: [
                            Colors.white,
                            Colors.white.withOpacity(0.8),
                          ],
                        ),
                        style: AppTypography.cardTitle.copyWith(
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                    ],
                  ),
                ],
              ),
            ),
          ),

          // Urn Path - Vertical List with staggered animations
          SliverPadding(
            padding: const EdgeInsets.fromLTRB(
              AppSpacing.md,
              AppSpacing.sm,
              AppSpacing.md,
              120, // Bottom padding for nav bar
            ),
            sliver: SliverList(
              delegate: SliverChildBuilderDelegate(
                (context, index) {
                  return _StaggeredUrnCardWrapper(
                    index: index,
                    child: Padding(
                      padding: const EdgeInsets.only(bottom: AppSpacing.md),
                      child: UrnPathCard(
                        urnIndex: index,
                        isCurrentUrn: index == 1, // Mock: Second urn is current
                      ),
                    ),
                  );
                },
                childCount: 9, // Mock: 9 urns total
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildHeader(BuildContext context, WidgetRef ref) {
    return SliverToBoxAdapter(
          child: Padding(
        padding: const EdgeInsets.fromLTRB(
          AppSpacing.md,
          AppSpacing.sm,
          AppSpacing.md,
          AppSpacing.sm,
        ),
        child: LayoutBuilder(
          builder: (context, constraints) {
            final isCompact = constraints.maxWidth < 360;
            return Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    Expanded(
                      child: GradientText(
                        'Học Tập',
                        gradient: LinearGradient(
                          colors: [
                            Colors.white,
                            AppColors.primary.withOpacity(0.9),
                          ],
                          begin: Alignment.topLeft,
                          end: Alignment.bottomRight,
                        ),
                        style: AppTypography.screenTitle.copyWith(
                          fontSize: isCompact ? 22 : 26,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                    ),
                    const CompactStreakWidget(),
                  ],
                ),
                const SizedBox(height: AppSpacing.sm),
                _buildDailyProgressCard(ref),
              ],
            );
          },
        ),
      ),
    );
  }

  Widget _buildDailyProgressCard(WidgetRef ref) {
    final dashboardAsync = ref.watch(dashboardSummaryProvider);

    return dashboardAsync.when(
      loading: () => LayoutBuilder(
        builder: (context, constraints) {
          final isCompact = constraints.maxWidth < 360;
          return ShimmerWidget(
            child: Container(
              padding: const EdgeInsets.symmetric(
                horizontal: AppSpacing.md,
                vertical: AppSpacing.sm,
              ),
              decoration: BoxDecoration(
                gradient: LinearGradient(
                  begin: Alignment.topLeft,
                  end: Alignment.bottomRight,
                  colors: [
                    AppColors.primary.withOpacity(0.2),
                    AppColors.primaryDark.withOpacity(0.1),
                  ],
                ),
                borderRadius: BorderRadius.circular(AppSpacing.radiusMD),
                border: Border.all(
                  color: AppColors.primary.withOpacity(0.3),
                  width: 1.2,
                ),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      Container(
                        width: 60,
                        height: 20,
                        decoration: BoxDecoration(
                          color: Colors.white.withOpacity(0.2),
                          borderRadius: BorderRadius.circular(4),
                        ),
                      ),
                      const SizedBox(width: 8),
                      Container(
                        width: 80,
                        height: 16,
                        decoration: BoxDecoration(
                          color: Colors.white.withOpacity(0.15),
                          borderRadius: BorderRadius.circular(4),
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: AppSpacing.xs),
                  Container(
                    height: isCompact ? 5 : 6,
                    decoration: BoxDecoration(
                      color: Colors.white.withOpacity(0.15),
                      borderRadius: BorderRadius.circular(AppSpacing.radiusXS),
                    ),
                  ),
                ],
              ),
            ),
          );
        },
      ),
      error: (_, __) => _buildProgressCard(0, 5), // Fallback on error
      data: (dashboard) {
        // Calculate today's progress from pathMotifs
        final totalLessons = dashboard.pathMotifs.length;
        final completedLessons = dashboard.pathMotifs
            .where((m) => m.isLearned || m.isMastered)
            .length;

        return _buildProgressCard(
          completedLessons,
          totalLessons > 0 ? totalLessons : 5,
        );
      },
    );
  }

  Widget _buildProgressCard(int completedToday, int goalToday) {
    final progress = completedToday / goalToday;

    return LayoutBuilder(
      builder: (context, constraints) {
        final isCompact = constraints.maxWidth < 360;
        return Container(
          padding: const EdgeInsets.symmetric(
            horizontal: AppSpacing.md,
            vertical: AppSpacing.sm,
          ),
          decoration: BoxDecoration(
            gradient: LinearGradient(
              begin: Alignment.topLeft,
              end: Alignment.bottomRight,
              colors: [
                AppColors.primary.withOpacity(0.2),
                AppColors.primaryDark.withOpacity(0.1),
              ],
            ),
            borderRadius: BorderRadius.circular(AppSpacing.radiusMD),
            border: Border.all(
              color: AppColors.primary.withOpacity(0.3),
              width: 1.2,
            ),
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Wrap(
                spacing: 6,
                runSpacing: 4,
                crossAxisAlignment: WrapCrossAlignment.center,
                children: [
                  Text(
                    '$completedToday/$goalToday',
                    style: TextStyle(
                      color: AppColors.primary,
                      fontSize: isCompact ? 18 : 20,
                      fontWeight: FontWeight.bold,
                      height: 1,
                    ),
                  ),
                  Text(
                    'bài hôm nay',
                    style: TextStyle(
                      color: Colors.white.withOpacity(0.8),
                      fontSize: 13,
                      fontWeight: FontWeight.w500,
                    ),
                  ),
                  if (completedToday < goalToday)
                    GradientText.xp(
                      '+${(goalToday - completedToday) * 10} XP',
                      style: const TextStyle(
                        fontSize: 12,
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                ],
              ),
              const SizedBox(height: AppSpacing.xs),
              LinearProgressIndicator(
                value: progress.clamp(0.0, 1.0),
                minHeight: isCompact ? 5 : 6,
                backgroundColor: Colors.white.withOpacity(0.15),
                valueColor: const AlwaysStoppedAnimation<Color>(
                  AppColors.primary,
                ),
              ),
            ],
          ),
        );
      },
    );
  }
}

/// Wrapper widget for staggered entrance animation of urn cards
class _StaggeredUrnCardWrapper extends StatefulWidget {
  final int index;
  final Widget child;

  const _StaggeredUrnCardWrapper({
    required this.index,
    required this.child,
  });

  @override
  State<_StaggeredUrnCardWrapper> createState() =>
      _StaggeredUrnCardWrapperState();
}

class _StaggeredUrnCardWrapperState extends State<_StaggeredUrnCardWrapper> {
  @override
  Widget build(BuildContext context) {
    return TweenAnimationBuilder<double>(
      tween: Tween<double>(begin: 0.0, end: 1.0),
      duration: const Duration(milliseconds: 500),
      curve: Curves.easeOutCubic,
      builder: (context, value, child) {
        return Opacity(
          opacity: value,
          child: Transform.translate(
            offset: Offset(0, 20 * (1 - value)),
            child: child,
          ),
        );
      },
      child: widget.child,
    );
  }
}
