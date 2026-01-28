import 'package:cached_network_image/cached_network_image.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../../../core/theme/app_colors.dart';
import '../../../../core/theme/app_spacing.dart';
import '../../../../core/theme/app_typography.dart';
import '../../../../core/utils/url_utils.dart';
import '../../../../routing/route_names.dart';
import '../../../../shared/widgets/effects/shimmer_widget.dart';
import '../../../../shared/widgets/progress/circular_progress_badge.dart';
import '../../../../shared/widgets/text/gradient_text.dart';
import '../../../hearts/presentation/widgets/hearts_display.dart';
import '../../../streak/presentation/providers/streak_provider.dart';
import '../providers/practice_provider.dart';
import '../providers/practice_urns_provider.dart';
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

    return Scaffold(
      backgroundColor: Colors.transparent,
      body: SafeArea(
        bottom: false,  // Allow content to extend behind navbar
        child: RefreshIndicator(
            onRefresh: () async {
              ref.invalidate(practiceUrnsProvider);
              // Wait a bit for provider to start loading, then let UI rebuild naturally
              // Don't use .future after invalidate to avoid "Bad state: Future already completed"
              await Future.delayed(const Duration(milliseconds: 100));
            },
            color: AppColors.primary,
            backgroundColor: AppColors.surface,
            child: CustomScrollView(
              physics: const AlwaysScrollableScrollPhysics(),
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
                _buildUrnsList(context, ref, 'Cần Ôn Tập', 8, AppColors.warning),

                SliverToBoxAdapter(
                  child: Padding(
                    padding: EdgeInsets.all(horizontalPadding),
                    child: _buildSectionHeader(
                        context, 'Học Mới', Icons.new_releases),
                  ),
                ),

                // New Items
                _buildUrnsList(context, ref, 'Học Mới', 5, AppColors.info),

                SliverToBoxAdapter(
                  child: Padding(
                    padding: EdgeInsets.all(horizontalPadding),
                    child: _buildSectionHeader(
                        context, 'Đã Thành Thạo', Icons.stars),
                  ),
                ),

                // Mastered Items
                _buildUrnsList(context, ref, 'Đã Thành Thạo', 12, AppColors.success),

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
    return TweenAnimationBuilder<double>(
      tween: Tween(begin: 0.0, end: 1.0),
      duration: const Duration(milliseconds: 600),
      curve: Curves.easeOutCubic,
      builder: (context, value, child) {
        return Transform.scale(
          scale: 0.9 + (value * 0.1),
          child: Opacity(
            opacity: value,
            child: child,
          ),
        );
      },
      child: LayoutBuilder(
        builder: (context, constraints) {
          final isCompact = constraints.maxWidth < 360;
          final padding = isCompact ? AppSpacing.md : AppSpacing.lg;
          return Container(
            width: double.infinity,
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
                      Icons.star_rounded,
                      AppColors.xpGold,
                      '${stats['xpEarned'] ?? 0}',
                      'XP',
                      isCompact,
                    ),
                    _buildStatItem(
                      context,
                      Icons.local_fire_department_rounded,
                      AppColors.streakOrange,
                      '$streak',
                      'Ngày',
                      isCompact,
                    ),
                    _buildStatItem(
                      context,
                      Icons.favorite_rounded,
                      AppColors.error,
                      '${stats['hearts'] ?? 5}',
                      'Tim',
                      isCompact,
                    ),
                    _buildStatItem(
                      context,
                      Icons.check_circle_rounded,
                      AppColors.success,
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
      ),
    );
  }

  Widget _buildStatItem(
    BuildContext context,
    IconData icon,
    Color iconColor,
    String value,
    String label,
    bool isCompact,
  ) {
    return Column(
      children: [
        Icon(
          icon,
          color: iconColor,
          size: isCompact ? 24 : 32,
        ),
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
    return TweenAnimationBuilder<double>(
      tween: Tween(begin: 0.0, end: 1.0),
      duration: const Duration(milliseconds: 700),
      curve: Curves.easeOutCubic,
      builder: (context, value, child) {
        return Transform.translate(
          offset: Offset(0, 20 * (1 - value)),
          child: Opacity(
            opacity: value,
            child: child,
          ),
        );
      },
      child: Material(
        color: Colors.transparent,
        child: InkWell(
          onTap: () {
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
          child: GradientText(
            title,
            style: AppTypography.textTheme.titleLarge?.copyWith(
                  fontWeight: FontWeight.bold,
                ),
            gradient: AppColors.primaryGradient,
            maxLines: 1,
            overflow: TextOverflow.ellipsis,
          ),
        ),
      ],
    );
  }

  Widget _buildUrnsList(
      BuildContext context, WidgetRef ref, String category, int count, Color accentColor) {
    final screenWidth = MediaQuery.of(context).size.width;
    final horizontalPadding = screenWidth < 360 ? AppSpacing.md : AppSpacing.lg;
    final urnsAsync = ref.watch(practiceUrnsProvider);

    return urnsAsync.when(
      loading: () => SliverToBoxAdapter(
        child: Padding(
          padding: EdgeInsets.symmetric(horizontal: horizontalPadding),
          child: Center(
            child: ShimmerWidget(
              child: Container(
                height: 100,
                decoration: BoxDecoration(
                  color: AppColors.surface.withOpacity(0.5),
                  borderRadius: BorderRadius.circular(14),
                ),
              ),
            ),
          ),
        ),
      ),
      error: (_, __) => _buildUrnsListWithData(
        context, [], category, count, accentColor, horizontalPadding,
      ),
      data: (urns) => _buildUrnsListWithData(
        context, urns, category, count, accentColor, horizontalPadding,
      ),
    );
  }

  Widget _buildUrnsListWithData(
    BuildContext context,
    List<PracticeUrn> urns,
    String category,
    int count,
    Color accentColor,
    double horizontalPadding,
  ) {
    final displayCount = urns.isEmpty ? count.clamp(0, 3) : urns.length.clamp(0, 3);

    return SliverPadding(
      padding: EdgeInsets.symmetric(horizontal: horizontalPadding),
      sliver: SliverList(
        delegate: SliverChildBuilderDelegate(
          (context, index) {
            final urn = urns.isNotEmpty && index < urns.length ? urns[index] : null;
            return Padding(
              padding: const EdgeInsets.only(bottom: AppSpacing.md),
              child: _buildUrnCard(context, index, category, accentColor, urn),
            );
          },
          childCount: displayCount > 0 ? displayCount : 1,
        ),
      ),
    );
  }

  Widget _buildUrnCard(
      BuildContext context, int index, String category, Color accentColor, PracticeUrn? urn) {
    // Fallback mock data if urn is null
    final mockUrns = [
      {
        'name': 'Họa Tiết Rồng',
        'progress': 0.8,
        'items': 12,
        'id': 'cao-dinh',
        'thumbnailUrl': 'https://lms.histolab.icu/assets/ban-duc-noi/CAO%20DINH/CAO%20DINH.jpg',
      },
      {
        'name': 'Họa Tiết Phượng',
        'progress': 0.6,
        'items': 8,
        'id': 'nhan-dinh',
        'thumbnailUrl': 'https://lms.histolab.icu/assets/ban-duc-noi/NHAN%20DINH/NH%C3%82N%20%C4%90%E1%BB%88NH.jpg',
      },
      {
        'name': 'Họa Tiết Sen',
        'progress': 0.4,
        'items': 5,
        'id': 'chuong-dinh',
        'thumbnailUrl': 'https://lms.histolab.icu/assets/ban-duc-noi/CHUONG%20DINH/CH%C6%AF%C6%A0NG%20%C4%90%E1%BB%88NH.jpg',
      },
    ];

    final mockData = mockUrns[index % mockUrns.length];
    final name = urn?.name ?? mockData['name'] as String;
    final progressValue = urn?.progress ?? mockData['progress'] as double;
    final itemCount = urn?.motifCount ?? mockData['items'] as int;
    final urnId = urn?.id ?? mockData['id'] as String;
    final thumbnailUrl = urn?.thumbnailUrl ?? mockData['thumbnailUrl'] as String;


    return Material(
      color: Colors.transparent,
      child: InkWell(
        onTap: () {
          context.push(RoutePaths.urn(urnId));
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
                  _buildUrnThumbnail(thumbnailUrl, accentColor, isCompact),
                  const SizedBox(width: AppSpacing.md),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          name,
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
                  Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      CircularProgressBadge(
                        progress: progressValue,
                        icon: Icons.terrain,
                        progressColor: accentColor,
                        size: isCompact ? 44 : 50,
                        strokeWidth: 3,
                      ),
                      const SizedBox(height: 4),
                      Text(
                        '$itemCount',
                        style: TextStyle(
                          color: accentColor,
                          fontSize: isCompact ? 11 : 12,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                    ],
                  ),
                ],
              ),
            );
          },
        ),
      ),
    );
  }

  Widget _buildUrnThumbnail(String? thumbnailUrl, Color accentColor, bool isCompact) {
    final size = isCompact ? 44.0 : 50.0;

    if (thumbnailUrl != null && thumbnailUrl.isNotEmpty) {
      final imageUrl = UrlUtils.getImageUrl(thumbnailUrl);
      return ClipRRect(
        borderRadius: BorderRadius.circular(12),
        child: CachedNetworkImage(
          imageUrl: imageUrl,
          width: size,
          height: size,
          fit: BoxFit.cover,
          placeholder: (_, __) => _buildThumbnailPlaceholder(accentColor, size),
          errorWidget: (_, __, ___) => _buildThumbnailPlaceholder(accentColor, size),
        ),
      );
    }

    return _buildThumbnailPlaceholder(accentColor, size);
  }

  Widget _buildThumbnailPlaceholder(Color accentColor, double size) {
    return Container(
      width: size,
      height: size,
      decoration: BoxDecoration(
        gradient: LinearGradient(
          colors: [accentColor, accentColor.withOpacity(0.6)],
        ),
        borderRadius: BorderRadius.circular(12),
      ),
      child: Icon(Icons.terrain, color: Colors.white, size: size * 0.52),
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
