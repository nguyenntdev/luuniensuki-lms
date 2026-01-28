import 'package:cached_network_image/cached_network_image.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../../core/theme/app_colors.dart';
import '../../../../core/theme/app_spacing.dart';
import '../../../../core/theme/app_typography.dart';
import '../../../../core/utils/url_utils.dart';
import '../../../../routing/route_names.dart';
import '../../../../shared/widgets/animations/staggered_animation_wrapper.dart';
import '../../../hearts/presentation/widgets/hearts_display.dart';
import '../../../streak/presentation/widgets/compact_streak_widget.dart';
import '../../data/models/dashboard_summary.dart';
import '../providers/dashboard_summary_provider.dart';
import '../widgets/daily_lessons_widget.dart';

class LearningHubScreen extends ConsumerWidget {
  const LearningHubScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final summaryAsync = ref.watch(dashboardSummaryProvider);
    final screenWidth = MediaQuery.of(context).size.width;
    final horizontalPadding =
        screenWidth < 360 ? AppSpacing.md : AppSpacing.lg;

    return Scaffold(
      backgroundColor: Colors.transparent,
      body: SafeArea(
        bottom: false,  // Allow content to extend behind navbar
        child: CustomScrollView(
          slivers: [
            SliverToBoxAdapter(
              child: _buildHeader(context),
            ),
            SliverToBoxAdapter(
              child: Padding(
                padding: EdgeInsets.symmetric(horizontal: horizontalPadding),
                child: _buildTodaySummaryCard(context, summaryAsync),
              ),
            ),
            SliverToBoxAdapter(
              child: Padding(
                padding: EdgeInsets.fromLTRB(
                  horizontalPadding,
                  AppSpacing.lg,
                  horizontalPadding,
                  AppSpacing.sm,
                ),
                child: _buildSectionHeader(
                  context,
                  'Bài học & ôn tập',
                  Icons.auto_stories,
                ),
              ),
            ),
            const SliverToBoxAdapter(
              child: DailyLessonsWidget(),
            ),
            SliverToBoxAdapter(
              child: Padding(
                padding: EdgeInsets.symmetric(horizontal: horizontalPadding),
                child: _buildQuickReviewTile(context, summaryAsync),
              ),
            ),
            SliverToBoxAdapter(
              child: Padding(
                padding: EdgeInsets.fromLTRB(
                  horizontalPadding,
                  AppSpacing.lg,
                  horizontalPadding,
                  AppSpacing.sm,
                ),
                child: _buildSectionHeader(
                  context,
                  'Lộ trình theo đỉnh',
                  Icons.terrain,
                ),
              ),
            ),
            _buildPathMotifsSliver(
              context: context,
              summaryAsync: summaryAsync,
              horizontalPadding: horizontalPadding,
            ),
            const SliverToBoxAdapter(
              child: SizedBox(height: 120),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildHeader(BuildContext context) {
    final screenWidth = MediaQuery.of(context).size.width;
    final isCompact = screenWidth < 360;
    final title = Text(
      'Học & Luyện',
      style: AppTypography.textTheme.headlineSmall?.copyWith(
        color: Colors.white,
        fontSize: isCompact ? 20 : 24,
        fontWeight: FontWeight.bold,
      ),
    );
    final headerActions = Wrap(
      spacing: AppSpacing.sm,
      runSpacing: AppSpacing.xs,
      crossAxisAlignment: WrapCrossAlignment.center,
      children: const [
        CompactHeartsDisplay(),
        CompactStreakWidget(),
      ],
    );

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
          isCompact
              ? Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    title,
                    const SizedBox(height: AppSpacing.xs),
                    headerActions,
                  ],
                )
              : Row(
                  children: [
                    Expanded(child: title),
                    headerActions,
                  ],
                ),
          SizedBox(height: isCompact ? AppSpacing.xs : AppSpacing.sm),
          Text(
            'Theo dõi tiến độ, chọn bài học và luyện tập nhanh mỗi ngày.',
            style: AppTypography.textTheme.bodySmall?.copyWith(
              color: Colors.white.withOpacity(0.7),
            ),
            maxLines: 2,
            overflow: TextOverflow.ellipsis,
          ),
        ],
      ),
    );
  }

  Widget _buildTodaySummaryCard(
    BuildContext context,
    AsyncValue<DashboardSummary> summaryAsync,
  ) {
    return LayoutBuilder(
      builder: (context, constraints) {
        final isCompact = constraints.maxWidth < 360;
        final padding = isCompact ? AppSpacing.md : AppSpacing.lg;

        final content = summaryAsync.when(
          loading: () => _buildSummaryPlaceholder(isCompact),
          error: (_, __) => _buildSummaryPlaceholder(isCompact),
          data: (summary) {
            final stats = summary.collectionStats;
            return Wrap(
              spacing: AppSpacing.md,
              runSpacing: AppSpacing.md,
              children: [
                _buildSummaryChip(
                  icon: Icons.explore,
                  label: 'Khám phá',
                  value: '${stats.discovered}/${stats.total}',
                  isCompact: isCompact,
                ),
                _buildSummaryChip(
                  icon: Icons.school,
                  label: 'Đã học',
                  value: '${stats.learned}',
                  isCompact: isCompact,
                ),
                _buildSummaryChip(
                  icon: Icons.workspace_premium,
                  label: 'Thành thạo',
                  value: '${stats.mastered}',
                  isCompact: isCompact,
                ),
                _buildSummaryChip(
                  icon: Icons.local_fire_department,
                  label: 'Streak',
                  value: '${summary.streak.currentStreak} ngày',
                  isCompact: isCompact,
                ),
              ],
            );
          },
        );

        return Container(
          width: double.infinity,
          padding: EdgeInsets.all(padding),
          decoration: BoxDecoration(
            color: Colors.white.withOpacity(0.08),
            borderRadius: BorderRadius.circular(20),
            border: Border.all(
              color: Colors.white.withOpacity(0.12),
            ),
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                'Tổng quan hôm nay',
                style: AppTypography.textTheme.titleLarge?.copyWith(
                  color: Colors.white,
                  fontWeight: FontWeight.bold,
                ),
              ),
              const SizedBox(height: AppSpacing.md),
              content,
            ],
          ),
        );
      },
    );
  }

  Widget _buildSummaryPlaceholder(bool isCompact) {
    return Wrap(
      spacing: AppSpacing.md,
      runSpacing: AppSpacing.md,
      children: List.generate(4, (_) => _buildSummarySkeleton(isCompact)),
    );
  }

  Widget _buildSummarySkeleton(bool isCompact) {
    final size = isCompact ? 34.0 : 38.0;
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
      decoration: BoxDecoration(
        color: Colors.white.withOpacity(0.06),
        borderRadius: BorderRadius.circular(16),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Container(
            width: size,
            height: size,
            decoration: BoxDecoration(
              color: Colors.white.withOpacity(0.12),
              shape: BoxShape.circle,
            ),
          ),
          const SizedBox(width: 10),
          Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Container(
                width: 50,
                height: 10,
                decoration: BoxDecoration(
                  color: Colors.white.withOpacity(0.12),
                  borderRadius: BorderRadius.circular(6),
                ),
              ),
              const SizedBox(height: 6),
              Container(
                width: 34,
                height: 10,
                decoration: BoxDecoration(
                  color: Colors.white.withOpacity(0.1),
                  borderRadius: BorderRadius.circular(6),
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildSummaryChip({
    required IconData icon,
    required String label,
    required String value,
    required bool isCompact,
  }) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
      decoration: BoxDecoration(
        color: Colors.white.withOpacity(0.08),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: Colors.white.withOpacity(0.12)),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Container(
            padding: const EdgeInsets.all(8),
            decoration: BoxDecoration(
              color: Colors.white.withOpacity(0.12),
              shape: BoxShape.circle,
            ),
            child: Icon(icon, color: Colors.white, size: isCompact ? 16 : 18),
          ),
          const SizedBox(width: 10),
          Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                label,
                style: TextStyle(
                  color: Colors.white.withOpacity(0.65),
                  fontSize: 11,
                ),
              ),
              Text(
                value,
                style: TextStyle(
                  color: Colors.white,
                  fontSize: isCompact ? 13 : 14,
                  fontWeight: FontWeight.bold,
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildQuickReviewTile(
    BuildContext context,
    AsyncValue<DashboardSummary> summaryAsync,
  ) {
    return summaryAsync.when(
      loading: () => const SizedBox.shrink(),
      error: (_, __) => const SizedBox.shrink(),
      data: (summary) {
        final pendingCount = summary.pathMotifs
            .where((motif) => motif.status == 'learned')
            .length;
        return Container(
          margin: const EdgeInsets.symmetric(vertical: AppSpacing.md),
          child: Material(
            color: Colors.transparent,
            child: InkWell(
              onTap: () => context.push('/practice'),
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
                ),
                child: Row(
                  children: [
                    Container(
                      padding: const EdgeInsets.all(12),
                      decoration: BoxDecoration(
                        color: Colors.white.withOpacity(0.2),
                        borderRadius: BorderRadius.circular(12),
                      ),
                      child: const Icon(
                        Icons.play_arrow,
                        color: Colors.white,
                        size: 28,
                      ),
                    ),
                    const SizedBox(width: AppSpacing.md),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            'Ôn tập nhanh',
                            style: TextStyle(
                              color: Colors.white,
                              fontSize: 18,
                              fontWeight: FontWeight.bold,
                            ),
                          ),
                          const SizedBox(height: 4),
                          Text(
                            pendingCount > 0
                                ? '$pendingCount bài đang chờ ôn tập'
                                : 'Sẵn sàng ôn tập ngay',
                            style: TextStyle(
                              color: Colors.white.withOpacity(0.9),
                              fontSize: 13,
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
                ),
              ),
            ),
          ),
        );
      },
    );
  }

  Widget _buildSectionHeader(
    BuildContext context,
    String title,
    IconData icon,
  ) {
    return Row(
      children: [
        Icon(icon, color: AppColors.primary, size: 22),
        const SizedBox(width: AppSpacing.sm),
        Expanded(
          child: Text(
            title,
            style: AppTypography.textTheme.titleLarge?.copyWith(
              color: Colors.white,
              fontWeight: FontWeight.bold,
            ),
          ),
        ),
      ],
    );
  }

  Widget _buildPathMotifsSliver({
    required BuildContext context,
    required AsyncValue<DashboardSummary> summaryAsync,
    required double horizontalPadding,
  }) {
    return summaryAsync.when(
      loading: () => SliverToBoxAdapter(
        child: Padding(
          padding: EdgeInsets.symmetric(horizontal: horizontalPadding),
          child: const LinearProgressIndicator(
            color: AppColors.primary,
            backgroundColor: Colors.transparent,
          ),
        ),
      ),
      error: (_, __) => SliverToBoxAdapter(
        child: Padding(
          padding: EdgeInsets.symmetric(horizontal: horizontalPadding),
          child: Text(
            'Không thể tải lộ trình. Vui lòng thử lại.',
            style: TextStyle(color: Colors.white.withOpacity(0.7)),
          ),
        ),
      ),
      data: (summary) {
        if (summary.pathMotifs.isEmpty) {
          return SliverToBoxAdapter(
            child: Padding(
              padding: EdgeInsets.symmetric(horizontal: horizontalPadding),
              child: Text(
                'Chưa có dữ liệu lộ trình. Hãy chọn đỉnh để bắt đầu.',
                style: TextStyle(color: Colors.white.withOpacity(0.7)),
              ),
            ),
          );
        }

        return SliverPadding(
          padding: EdgeInsets.fromLTRB(
            horizontalPadding,
            AppSpacing.sm,
            horizontalPadding,
            AppSpacing.lg,
          ),
          sliver: SliverList(
            delegate: SliverChildBuilderDelegate(
              (context, index) {
                final motif = summary.pathMotifs[index];
                return StaggeredAnimationWrapper(
                  index: index,
                  child: Padding(
                    padding: const EdgeInsets.only(bottom: AppSpacing.md),
                    child: _PathMotifCard(
                      motif: motif,
                      index: index,
                      total: summary.pathMotifs.length,
                    ),
                  ),
                );
              },
              childCount: summary.pathMotifs.length,
            ),
          ),
        );
      },
    );
  }
}

class _PathMotifCard extends StatelessWidget {
  final DashboardPathMotif motif;
  final int index;
  final int total;

  const _PathMotifCard({
    required this.motif,
    required this.index,
    required this.total,
  });

  @override
  Widget build(BuildContext context) {
    final imageUrl = UrlUtils.getImageUrl(motif.thumbnailUrl);
    final statusColor = _statusColor(motif.status);
    final statusLabel = _statusLabel(motif.status);
    final hasPrevious = index > 0;
    final hasNext = index < total - 1;

    return Material(
      color: Colors.transparent,
      child: InkWell(
        onTap: () {
          if (motif.isLearned || motif.isMastered) {
            context.push(RoutePaths.quiz(motif.id));
          } else {
            context.push(RoutePaths.motif(motif.id));
          }
        },
        borderRadius: BorderRadius.circular(18),
        child: IntrinsicHeight(
          child: Row(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              _buildRouteIndicator(
                statusColor,
                hasPrevious: hasPrevious,
                hasNext: hasNext,
              ),
              const SizedBox(width: AppSpacing.sm),
              Expanded(
                child: Container(
                  padding: const EdgeInsets.all(AppSpacing.md),
                  decoration: BoxDecoration(
                    color: Colors.white.withOpacity(0.06),
                    borderRadius: BorderRadius.circular(18),
                    border: Border.all(
                      color: statusColor.withOpacity(0.35),
                    ),
                  ),
                  child: Row(
                    children: [
                      ClipRRect(
                        borderRadius: BorderRadius.circular(14),
                        child: imageUrl.isEmpty
                            ? Container(
                                width: 72,
                                height: 72,
                                color: Colors.white.withOpacity(0.08),
                                child: Icon(
                                  Icons.auto_awesome_mosaic,
                                  color: Colors.white.withOpacity(0.6),
                                ),
                              )
                            : CachedNetworkImage(
                                imageUrl: imageUrl,
                                width: 72,
                                height: 72,
                                fit: BoxFit.cover,
                                placeholder: (_, __) => Container(
                                  width: 72,
                                  height: 72,
                                  color: Colors.white.withOpacity(0.08),
                                ),
                                errorWidget: (_, __, ___) => Container(
                                  width: 72,
                                  height: 72,
                                  color: Colors.white.withOpacity(0.08),
                                  child: Icon(
                                    Icons.broken_image_outlined,
                                    color: Colors.white.withOpacity(0.6),
                                  ),
                                ),
                              ),
                      ),
                      const SizedBox(width: AppSpacing.md),
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              motif.name,
                              style: const TextStyle(
                                color: Colors.white,
                                fontSize: 15,
                                fontWeight: FontWeight.w600,
                              ),
                              maxLines: 2,
                              overflow: TextOverflow.ellipsis,
                            ),
                            if (motif.nameEn != null &&
                                motif.nameEn!.isNotEmpty) ...[
                              const SizedBox(height: 4),
                              Text(
                                motif.nameEn!,
                                style: TextStyle(
                                  color: Colors.white.withOpacity(0.6),
                                  fontSize: 12,
                                  fontStyle: FontStyle.italic,
                                ),
                                maxLines: 1,
                                overflow: TextOverflow.ellipsis,
                              ),
                            ],
                            const SizedBox(height: 8),
                            Row(
                              children: [
                                Container(
                                  padding: const EdgeInsets.symmetric(
                                    horizontal: 10,
                                    vertical: 4,
                                  ),
                                  decoration: BoxDecoration(
                                    color: statusColor.withOpacity(0.2),
                                    borderRadius: BorderRadius.circular(12),
                                    border: Border.all(
                                      color: statusColor.withOpacity(0.35),
                                    ),
                                  ),
                                  child: Text(
                                    statusLabel,
                                    style: TextStyle(
                                      color: statusColor,
                                      fontSize: 11,
                                      fontWeight: FontWeight.w600,
                                    ),
                                  ),
                                ),
                                const Spacer(),
                                Icon(
                                  Icons.chevron_right,
                                  color: Colors.white.withOpacity(0.6),
                                ),
                              ],
                            ),
                          ],
                        ),
                      ),
                    ],
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildRouteIndicator(
    Color statusColor, {
    required bool hasPrevious,
    required bool hasNext,
  }) {
    final lineColor = statusColor.withOpacity(0.35);
    return SizedBox(
      width: 24,
      child: Column(
        children: [
          Expanded(
            child: Container(
              width: 2,
              color: hasPrevious ? lineColor : Colors.transparent,
            ),
          ),
          Container(
            width: 14,
            height: 14,
            decoration: BoxDecoration(
              color: statusColor.withOpacity(0.9),
              shape: BoxShape.circle,
              boxShadow: [
                BoxShadow(
                  color: statusColor.withOpacity(0.35),
                  blurRadius: 6,
                  spreadRadius: 1,
                ),
              ],
            ),
          ),
          Expanded(
            child: Container(
              width: 2,
              color: hasNext ? lineColor : Colors.transparent,
            ),
          ),
        ],
      ),
    );
  }
}

String _statusLabel(String status) {
  switch (status) {
    case 'mastered':
      return 'Thành thạo';
    case 'learned':
      return 'Đã học';
    case 'discovered':
      return 'Đã khám phá';
    default:
      return 'Chưa mở';
  }
}

Color _statusColor(String status) {
  switch (status) {
    case 'mastered':
      return AppColors.success;
    case 'learned':
      return AppColors.primary;
    case 'discovered':
      return AppColors.info;
    default:
      return AppColors.textSecondary;
  }
}
