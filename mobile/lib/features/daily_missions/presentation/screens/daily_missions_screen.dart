import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../../core/theme/app_colors.dart';
import '../../../../core/theme/app_spacing.dart';
import '../../../../shared/widgets/glass/animated_background.dart';
import '../../../../shared/widgets/progress/circular_progress_badge.dart';
import '../../../../shared/widgets/shimmer/shimmer_skeleton.dart';
import '../../../../shared/widgets/text/gradient_text.dart';
import '../../domain/entities/daily_mission.dart';
import '../providers/daily_missions_provider.dart';
import '../widgets/mission_card.dart';

/// Screen for displaying daily missions
class DailyMissionsScreen extends ConsumerWidget {
  const DailyMissionsScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final state = ref.watch(dailyMissionsNotifierProvider);

    return Scaffold(
      body: AnimatedGradientBackground(
        child: CustomScrollView(
          slivers: [
            // App bar
            SliverAppBar(
              floating: true,
              backgroundColor: Colors.transparent,
              elevation: 0,
              leading: IconButton(
                icon: const Icon(Icons.arrow_back, color: Colors.white),
                onPressed: () => context.pop(),
              ),
              title: const GradientText(
                'Nhiệm Vụ Hàng Ngày',
                style: TextStyle(
                  fontWeight: FontWeight.bold,
                  fontSize: 20,
                ),
              ),
              actions: [
                IconButton(
                  icon: const Icon(Icons.refresh, color: Colors.white),
                  onPressed: () {
                    ref.read(dailyMissionsNotifierProvider.notifier).refresh();
                  },
                ),
              ],
            ),

            // Content
            SliverPadding(
              padding: const EdgeInsets.all(AppSpacing.lg),
              sliver: SliverList(
                delegate: SliverChildListDelegate([
                  // Header card
                  _buildHeaderCard(context, state),

                  const SizedBox(height: AppSpacing.lg),

                  // Loading state
                  if (state.isLoading && state.summary == null)
                    _buildShimmerLoading(),

                  // Error state
                  if (state.error != null && state.summary == null)
                    _buildErrorCard(context, state.error!, ref),

                  // Missions list
                  if (state.summary != null) ...[
                    GradientText(
                      'Danh sách nhiệm vụ',
                      style: Theme.of(context).textTheme.titleLarge?.copyWith(
                            fontWeight: FontWeight.bold,
                          ),
                    ),
                    const SizedBox(height: AppSpacing.md),
                    ...state.summary!.missions.map(
                      (mission) => Padding(
                        padding: const EdgeInsets.only(bottom: AppSpacing.md),
                        child: _EnhancedMissionCard(mission: mission),
                      ),
                    ),
                  ],
                ]),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildHeaderCard(BuildContext context, DailyMissionsState state) {
    final summary = state.summary;
    final completionPercentage = summary?.completionPercentage ?? 0;

    return Container(
      padding: const EdgeInsets.all(AppSpacing.lg),
      decoration: BoxDecoration(
        gradient: LinearGradient(
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
          colors: [
            AppColors.primary.withOpacity(0.3),
            AppColors.primaryDark.withOpacity(0.2),
          ],
        ),
        borderRadius: BorderRadius.circular(20),
        border: Border.all(
          color: Colors.white.withOpacity(0.3),
          width: 1,
        ),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              CircularProgressBadge(
                progress: completionPercentage / 100,
                icon: Icons.flag,
                size: 56,
                strokeWidth: 5,
                progressColor: AppColors.xpGold,
              ),
              const SizedBox(width: AppSpacing.md),
              Expanded(
                child: GradientText(
                  'Tiến độ hôm nay',
                  style: Theme.of(context).textTheme.headlineSmall?.copyWith(
                        fontWeight: FontWeight.bold,
                      ),
                  gradient: AppColors.xpGradient,
                ),
              ),
            ],
          ),
          const SizedBox(height: AppSpacing.lg),

          // Stats row
          Row(
            children: [
              _buildStatItem(
                context,
                icon: Icons.check_circle,
                label: 'Hoàn thành',
                value: '${summary?.completedCount ?? 0}/${summary?.totalCount ?? 0}',
                color: AppColors.success,
              ),
              const SizedBox(width: AppSpacing.lg),
              _buildStatItem(
                context,
                icon: Icons.star,
                label: 'XP hôm nay',
                value: '${summary?.totalXpToday ?? 0}',
                color: AppColors.xpGold,
              ),
            ],
          ),

          const SizedBox(height: AppSpacing.md),

          // Progress bar
          ClipRRect(
            borderRadius: BorderRadius.circular(8),
            child: LinearProgressIndicator(
              value: completionPercentage / 100,
              minHeight: 12,
              backgroundColor: Colors.white.withOpacity(0.2),
              valueColor: AlwaysStoppedAnimation<Color>(AppColors.success),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildShimmerLoading() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        // Header shimmer
        const ShimmerSkeleton(width: 180, height: 24),
        const SizedBox(height: 8),
        const ShimmerSkeleton(width: 120, height: 14),
        const SizedBox(height: AppSpacing.lg),

        // Summary card shimmer
        Container(
          padding: const EdgeInsets.all(AppSpacing.lg),
          decoration: BoxDecoration(
            gradient: LinearGradient(
              begin: Alignment.topLeft,
              end: Alignment.bottomRight,
              colors: [
                Colors.white.withOpacity(0.12),
                Colors.white.withOpacity(0.06),
              ],
            ),
            borderRadius: BorderRadius.circular(20),
            border: Border.all(
              color: Colors.white.withOpacity(0.3),
              width: 1,
            ),
          ),
          child: Column(
            children: [
              Row(
                children: [
                  const ShimmerSkeleton(width: 56, height: 56, borderRadius: BorderRadius.all(Radius.circular(28))),
                  const SizedBox(width: AppSpacing.md),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: const [
                        ShimmerSkeleton(width: 150, height: 20),
                        SizedBox(height: 4),
                        ShimmerSkeleton(width: 100, height: 14),
                      ],
                    ),
                  ),
                ],
              ),
              const SizedBox(height: AppSpacing.lg),
              Row(
                children: const [
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        ShimmerSkeleton(width: 80, height: 12),
                        SizedBox(height: 4),
                        ShimmerSkeleton(width: 50, height: 16),
                      ],
                    ),
                  ),
                  SizedBox(width: AppSpacing.lg),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        ShimmerSkeleton(width: 80, height: 12),
                        SizedBox(height: 4),
                        ShimmerSkeleton(width: 50, height: 16),
                      ],
                    ),
                  ),
                ],
              ),
              const SizedBox(height: AppSpacing.md),
              const ShimmerSkeleton(width: double.infinity, height: 12, borderRadius: BorderRadius.all(Radius.circular(8))),
            ],
          ),
        ),
        const SizedBox(height: AppSpacing.lg),

        // Mission cards shimmer
        const ShimmerSkeleton(width: 150, height: 20),
        const SizedBox(height: AppSpacing.md),
        ...List.generate(4, (index) => Padding(
          padding: const EdgeInsets.only(bottom: AppSpacing.md),
          child: Container(
            padding: const EdgeInsets.all(AppSpacing.md),
            decoration: BoxDecoration(
              gradient: LinearGradient(
                begin: Alignment.topLeft,
                end: Alignment.bottomRight,
                colors: [
                  Colors.white.withOpacity(0.12),
                  Colors.white.withOpacity(0.06),
                ],
              ),
              borderRadius: BorderRadius.circular(16),
              border: Border.all(
                color: Colors.white.withOpacity(0.2),
                width: 1,
              ),
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: const [
                    ShimmerSkeleton(width: 48, height: 48, borderRadius: BorderRadius.all(Radius.circular(24))),
                    SizedBox(width: AppSpacing.md),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          ShimmerSkeleton(width: double.infinity, height: 16),
                          SizedBox(height: 4),
                          ShimmerSkeleton(width: 150, height: 12),
                        ],
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: AppSpacing.md),
                const ShimmerSkeleton(width: double.infinity, height: 8, borderRadius: BorderRadius.all(Radius.circular(8))),
                const SizedBox(height: AppSpacing.sm),
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: const [
                    ShimmerSkeleton(width: 60, height: 14),
                    ShimmerSkeleton(width: 80, height: 24, borderRadius: BorderRadius.all(Radius.circular(12))),
                  ],
                ),
              ],
            ),
          ),
        )),
      ],
    );
  }

  Widget _buildStatItem(
    BuildContext context, {
    required IconData icon,
    required String label,
    required String value,
    required Color color,
  }) {
    return Expanded(
      child: Row(
        children: [
          Icon(icon, color: color, size: 20),
          const SizedBox(width: 8),
          Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                label,
                style: Theme.of(context).textTheme.bodySmall?.copyWith(
                      color: Colors.white70,
                    ),
              ),
              Text(
                value,
                style: Theme.of(context).textTheme.titleMedium?.copyWith(
                      color: Colors.white,
                      fontWeight: FontWeight.bold,
                    ),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildErrorCard(
    BuildContext context,
    String error,
    WidgetRef ref,
  ) {
    return Container(
      padding: const EdgeInsets.all(AppSpacing.lg),
      decoration: BoxDecoration(
        color: AppColors.error.withOpacity(0.1),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(
          color: AppColors.error.withOpacity(0.3),
        ),
      ),
      child: Column(
        children: [
          Icon(
            Icons.error_outline,
            color: AppColors.error,
            size: 48,
          ),
          const SizedBox(height: AppSpacing.md),
          Text(
            'Lỗi tải nhiệm vụ',
            style: Theme.of(context).textTheme.titleMedium?.copyWith(
                  color: Colors.white,
                  fontWeight: FontWeight.bold,
                ),
          ),
          const SizedBox(height: AppSpacing.sm),
          Text(
            error,
            style: Theme.of(context).textTheme.bodySmall?.copyWith(
                  color: Colors.white70,
                ),
            textAlign: TextAlign.center,
          ),
          const SizedBox(height: AppSpacing.md),
          ElevatedButton(
            onPressed: () {
              ref.read(dailyMissionsNotifierProvider.notifier).refresh();
            },
            style: ElevatedButton.styleFrom(
              backgroundColor: AppColors.error,
              foregroundColor: Colors.white,
            ),
            child: const Text('Thử lại'),
          ),
        ],
      ),
    );
  }
}

/// Enhanced mission card with animations and gradient overlays
class _EnhancedMissionCard extends StatelessWidget {
  final DailyMission mission;

  const _EnhancedMissionCard({required this.mission});

  Gradient _getGradientForMissionType(MissionType type) {
    switch (type) {
      case MissionType.lesson:
        return LinearGradient(
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
          colors: [
            AppColors.info.withOpacity(0.15),
            AppColors.info.withOpacity(0.05),
          ],
        );
      case MissionType.quiz:
        return LinearGradient(
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
          colors: [
            AppColors.badgePurple.withOpacity(0.15),
            AppColors.badgePurple.withOpacity(0.05),
          ],
        );
      case MissionType.discovery:
        return LinearGradient(
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
          colors: [
            AppColors.success.withOpacity(0.15),
            AppColors.success.withOpacity(0.05),
          ],
        );
      case MissionType.streak:
        return LinearGradient(
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
          colors: [
            AppColors.streakOrange.withOpacity(0.15),
            AppColors.streakOrange.withOpacity(0.05),
          ],
        );
    }
  }

  Color _getColorForMissionType(MissionType type) {
    switch (type) {
      case MissionType.lesson:
        return AppColors.info;
      case MissionType.quiz:
        return AppColors.badgePurple;
      case MissionType.discovery:
        return AppColors.success;
      case MissionType.streak:
        return AppColors.streakOrange;
    }
  }

  IconData _getIconForMissionType(MissionType type) {
    switch (type) {
      case MissionType.lesson:
        return Icons.school;
      case MissionType.quiz:
        return Icons.quiz;
      case MissionType.discovery:
        return Icons.explore;
      case MissionType.streak:
        return Icons.local_fire_department;
    }
  }

  @override
  Widget build(BuildContext context) {
    final progressColor = mission.isCompleted
        ? AppColors.success
        : mission.progressPercentage > 50
            ? AppColors.warning
            : _getColorForMissionType(mission.missionType);

    final isCloseToCompletion = mission.progressPercentage >= 90 && !mission.isCompleted;

    return Container(
      decoration: BoxDecoration(
        gradient: _getGradientForMissionType(mission.missionType),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(
          color: mission.isCompleted
              ? AppColors.success.withOpacity(0.5)
              : Colors.white.withOpacity(0.2),
          width: mission.isCompleted ? 2 : 1,
        ),
      ),
      child: Stack(
        children: [
          // Pulsing effect for missions close to completion
          if (isCloseToCompletion)
            Positioned.fill(
              child: _PulsingOverlay(color: progressColor),
            ),

          // Main content
          Padding(
            padding: const EdgeInsets.all(AppSpacing.md),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                // Header row
                Row(
                  children: [
                    // Mission icon with circular progress
                    CircularProgressBadge(
                      progress: mission.progressPercentage / 100,
                      icon: _getIconForMissionType(mission.missionType),
                      size: 48,
                      strokeWidth: 3,
                      progressColor: progressColor,
                    ),
                    const SizedBox(width: AppSpacing.md),
                    // Mission name
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          GradientText(
                            mission.name,
                            style: Theme.of(context).textTheme.titleMedium?.copyWith(
                                  fontWeight: FontWeight.bold,
                                ),
                            gradient: mission.isCompleted
                                ? AppColors.xpGradient
                                : LinearGradient(
                                    colors: [Colors.white, Colors.white.withOpacity(0.9)],
                                  ),
                          ),
                          const SizedBox(height: 4),
                          Text(
                            mission.description,
                            style: Theme.of(context).textTheme.bodySmall?.copyWith(
                                  color: Colors.white70,
                                ),
                          ),
                        ],
                      ),
                    ),
                    // Animated completion badge
                    if (mission.isCompleted)
                      _AnimatedCheckmark(color: AppColors.success),
                  ],
                ),
                const SizedBox(height: AppSpacing.md),

                // Progress bar
                ClipRRect(
                  borderRadius: BorderRadius.circular(8),
                  child: LinearProgressIndicator(
                    value: mission.progressPercentage / 100,
                    minHeight: 8,
                    backgroundColor: Colors.white.withOpacity(0.2),
                    valueColor: AlwaysStoppedAnimation<Color>(progressColor),
                  ),
                ),
                const SizedBox(height: AppSpacing.sm),

                // Progress text and XP reward
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Text(
                      '${mission.currentCount} / ${mission.targetCount}',
                      style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                            color: Colors.white70,
                            fontWeight: FontWeight.bold,
                          ),
                    ),
                    Container(
                      padding: const EdgeInsets.symmetric(
                        horizontal: AppSpacing.sm,
                        vertical: 4,
                      ),
                      decoration: BoxDecoration(
                        color: AppColors.xpGold.withOpacity(0.2),
                        borderRadius: BorderRadius.circular(12),
                      ),
                      child: Row(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          Icon(
                            Icons.star,
                            color: AppColors.xpGold,
                            size: 16,
                          ),
                          const SizedBox(width: 4),
                          GradientText.xp(
                            '${mission.xpReward} XP',
                            style: Theme.of(context).textTheme.bodySmall?.copyWith(
                                  fontWeight: FontWeight.bold,
                                ),
                          ),
                        ],
                      ),
                    ),
                  ],
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}


/// Animated checkmark for completed missions
class _AnimatedCheckmark extends StatelessWidget {
  final Color color;

  const _AnimatedCheckmark({required this.color});

  @override
  Widget build(BuildContext context) {
    return TweenAnimationBuilder<double>(
      tween: Tween(begin: 0.0, end: 1.0),
      duration: const Duration(milliseconds: 600),
      curve: Curves.elasticOut,
      builder: (context, value, child) {
        return Transform.scale(
          scale: value,
          child: Opacity(
            opacity: value,
            child: Container(
              padding: const EdgeInsets.all(8),
              decoration: BoxDecoration(
                color: color.withOpacity(0.2),
                shape: BoxShape.circle,
              ),
              child: Icon(
                Icons.check,
                color: color,
                size: 20,
              ),
            ),
          ),
        );
      },
    );
  }
}

/// Pulsing overlay for missions close to completion
class _PulsingOverlay extends StatefulWidget {
  final Color color;

  const _PulsingOverlay({required this.color});

  @override
  State<_PulsingOverlay> createState() => _PulsingOverlayState();
}

class _PulsingOverlayState extends State<_PulsingOverlay>
    with SingleTickerProviderStateMixin {
  late AnimationController _controller;
  late Animation<double> _animation;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      duration: const Duration(milliseconds: 1500),
      vsync: this,
    )..repeat(reverse: true);

    _animation = Tween<double>(begin: 0.0, end: 0.1).animate(
      CurvedAnimation(parent: _controller, curve: Curves.easeInOut),
    );
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: _animation,
      builder: (context, child) {
        return Container(
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(16),
            gradient: LinearGradient(
              begin: Alignment.topLeft,
              end: Alignment.bottomRight,
              colors: [
                widget.color.withOpacity(_animation.value),
                widget.color.withOpacity(_animation.value * 0.5),
              ],
            ),
          ),
        );
      },
    );
  }
}
