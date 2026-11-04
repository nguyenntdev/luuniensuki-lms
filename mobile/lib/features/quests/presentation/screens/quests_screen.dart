import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../../core/theme/app_colors.dart';
import '../../../../core/theme/app_spacing.dart';
import '../../../../core/theme/app_typography.dart';
import '../../../../routing/route_names.dart';
import '../../../../shared/widgets/glass/animated_background.dart';
import '../../../../shared/widgets/glass/glass_container.dart';
import '../../domain/entities/quest.dart';
import '../providers/quests_provider.dart';

/// Quests screen displaying all active, completed, and available heritage quests
class QuestsScreen extends ConsumerWidget {
  const QuestsScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final state = ref.watch(questsNotifierProvider);
    final notifier = ref.read(questsNotifierProvider.notifier);

    return AnimatedGradientBackground(
      child: Scaffold(
        backgroundColor: Colors.transparent,
        appBar: AppBar(
          backgroundColor: Colors.transparent,
          elevation: 0,
          leading: IconButton(
            icon: const Icon(Icons.arrow_back, color: Colors.white),
            onPressed: () {
              if (Navigator.of(context).canPop()) {
                context.pop();
              } else {
                context.go(RoutePaths.explore);
              }
            },
          ),
          title: const Text(
            'Nhiệm Vụ Di Sản',
            style: TextStyle(
              fontSize: 22,
              fontWeight: FontWeight.bold,
              color: Colors.white,
            ),
          ),
          actions: [
            IconButton(
              icon: const Icon(Icons.refresh, color: Colors.white),
              tooltip: 'Làm mới',
              onPressed: () => notifier.loadQuests(),
            ),
          ],
        ),
        body: SafeArea(
          child: Column(
            children: [
              // Header Summary Card
              Padding(
                padding: const EdgeInsets.symmetric(
                  horizontal: AppSpacing.md,
                  vertical: AppSpacing.sm,
                ),
                child: _buildSummaryCard(context, state),
              ),

              // Filter Bar
              Padding(
                padding: const EdgeInsets.symmetric(
                  horizontal: AppSpacing.md,
                  vertical: AppSpacing.xs,
                ),
                child: _buildFilterBar(context, ref, state.filter),
              ),

              const SizedBox(height: AppSpacing.sm),

              // Quest List
              Expanded(
                child: state.isLoading
                    ? const Center(child: CircularProgressIndicator())
                    : state.filteredQuests.isEmpty
                        ? _buildEmptyState(context)
                        : ListView.separated(
                            padding: const EdgeInsets.symmetric(
                              horizontal: AppSpacing.md,
                              vertical: AppSpacing.sm,
                            ),
                            itemCount: state.filteredQuests.length,
                            separatorBuilder: (_, __) =>
                                const SizedBox(height: AppSpacing.md),
                            itemBuilder: (context, index) {
                              final quest = state.filteredQuests[index];
                              return _buildQuestCard(context, quest);
                            },
                          ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildSummaryCard(BuildContext context, QuestsState state) {
    return GlassContainer(
      child: Padding(
        padding: const EdgeInsets.all(AppSpacing.md),
        child: Row(
          mainAxisAlignment: MainAxisAlignment.spaceAround,
          children: [
            _buildStatItem(
              context,
              icon: Icons.assignment_turned_in,
              color: AppColors.success,
              value: '${state.completedCount}',
              label: 'Đã hoàn thành',
            ),
            Container(width: 1, height: 40, color: Colors.white24),
            _buildStatItem(
              context,
              icon: Icons.hourglass_top,
              color: AppColors.warning,
              value: '${state.inProgressCount}',
              label: 'Đang tiến hành',
            ),
            Container(width: 1, height: 40, color: Colors.white24),
            _buildStatItem(
              context,
              icon: Icons.military_tech,
              color: AppColors.primary,
              value: '${state.quests.length}',
              label: 'Tổng nhiệm vụ',
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildStatItem(
    BuildContext context, {
    required IconData icon,
    required Color color,
    required String value,
    required String label,
  }) {
    return Column(
      mainAxisSize: MainAxisSize.min,
      children: [
        Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(icon, color: color, size: 20),
            const SizedBox(width: 4),
            Text(
              value,
              style: const TextStyle(
                color: Colors.white,
                fontSize: 18,
                fontWeight: FontWeight.bold,
              ),
            ),
          ],
        ),
        const SizedBox(height: 4),
        Text(
          label,
          style: const TextStyle(
            color: Colors.white70,
            fontSize: 12,
          ),
        ),
      ],
    );
  }

  Widget _buildFilterBar(
    BuildContext context,
    WidgetRef ref,
    QuestFilter currentFilter,
  ) {
    final notifier = ref.read(questsNotifierProvider.notifier);

    return SingleChildScrollView(
      scrollDirection: Axis.horizontal,
      child: Row(
        children: [
          _buildChip(
            label: 'Tất cả',
            isSelected: currentFilter == QuestFilter.all,
            onSelected: () => notifier.setFilter(QuestFilter.all),
          ),
          const SizedBox(width: 8),
          _buildChip(
            label: 'Đang làm',
            isSelected: currentFilter == QuestFilter.inProgress,
            onSelected: () => notifier.setFilter(QuestFilter.inProgress),
          ),
          const SizedBox(width: 8),
          _buildChip(
            label: 'Đã hoàn thành',
            isSelected: currentFilter == QuestFilter.completed,
            onSelected: () => notifier.setFilter(QuestFilter.completed),
          ),
          const SizedBox(width: 8),
          _buildChip(
            label: 'Đã khóa',
            isSelected: currentFilter == QuestFilter.locked,
            onSelected: () => notifier.setFilter(QuestFilter.locked),
          ),
        ],
      ),
    );
  }

  Widget _buildChip({
    required String label,
    required bool isSelected,
    required VoidCallback onSelected,
  }) {
    return FilterChip(
      label: Text(label),
      selected: isSelected,
      onSelected: (_) => onSelected(),
      selectedColor: AppColors.primary.withOpacity(0.8),
      backgroundColor: Colors.white.withOpacity(0.08),
      labelStyle: TextStyle(
        color: isSelected ? Colors.white : Colors.white70,
        fontWeight: isSelected ? FontWeight.bold : FontWeight.normal,
        fontSize: 13,
      ),
    );
  }

  Widget _buildQuestCard(BuildContext context, Quest quest) {
    return GlassContainer(
      child: InkWell(
        borderRadius: BorderRadius.circular(16),
        onTap: () {
          context.push(RoutePaths.quest(quest.id));
        },
        child: Padding(
          padding: const EdgeInsets.all(AppSpacing.md),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Top Row: Title + Status Pill
              Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Expanded(
                    child: Text(
                      quest.name,
                      style: AppTypography.textTheme.titleMedium?.copyWith(
                        color: Colors.white,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                  ),
                  _buildStatusPill(quest.status, quest.isLocked),
                ],
              ),
              const SizedBox(height: 6),

              // Description
              Text(
                quest.description,
                maxLines: 2,
                overflow: TextOverflow.ellipsis,
                style: const TextStyle(
                  color: Colors.white70,
                  fontSize: 13,
                ),
              ),
              const SizedBox(height: 12),

              // Progress Bar
              ClipRRect(
                borderRadius: BorderRadius.circular(6),
                child: LinearProgressIndicator(
                  value: quest.progressPercent / 100.0,
                  backgroundColor: Colors.white12,
                  valueColor: AlwaysStoppedAnimation<Color>(
                    quest.progressPercent >= 100.0
                        ? AppColors.success
                        : AppColors.primary,
                  ),
                  minHeight: 8,
                ),
              ),
              const SizedBox(height: 10),

              // Bottom Row: Rewards & Estimated Time
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Row(
                    children: [
                      const Icon(Icons.stars, color: Colors.amber, size: 16),
                      const SizedBox(width: 4),
                      Text(
                        '+${quest.xpReward} XP',
                        style: const TextStyle(
                          color: Colors.white,
                          fontWeight: FontWeight.bold,
                          fontSize: 12,
                        ),
                      ),
                      const SizedBox(width: 12),
                      const Text(
                        '💎',
                        style: TextStyle(fontSize: 12),
                      ),
                      const SizedBox(width: 4),
                      Text(
                        '+${quest.gemsReward}',
                        style: const TextStyle(
                          color: Colors.white,
                          fontWeight: FontWeight.bold,
                          fontSize: 12,
                        ),
                      ),
                    ],
                  ),
                  Row(
                    children: [
                      const Icon(Icons.timer_outlined,
                          color: Colors.white60, size: 14),
                      const SizedBox(width: 4),
                      Text(
                        '${quest.estimatedMinutes} phút',
                        style: const TextStyle(
                          color: Colors.white60,
                          fontSize: 12,
                        ),
                      ),
                      const SizedBox(width: 6),
                      const Icon(
                        Icons.chevron_right,
                        color: Colors.white54,
                        size: 18,
                      ),
                    ],
                  ),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildStatusPill(QuestStatus status, bool isLocked) {
    if (isLocked || status == QuestStatus.locked) {
      return Container(
        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
        decoration: BoxDecoration(
          color: Colors.grey.withOpacity(0.3),
          borderRadius: BorderRadius.circular(10),
        ),
        child: const Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(Icons.lock, size: 12, color: Colors.white70),
            SizedBox(width: 4),
            Text(
              'Đã khóa',
              style: TextStyle(color: Colors.white70, fontSize: 11),
            ),
          ],
        ),
      );
    }

    Color color;
    String text;

    switch (status) {
      case QuestStatus.completed:
        color = AppColors.success;
        text = 'Đã xong';
        break;
      case QuestStatus.inProgress:
        color = AppColors.warning;
        text = 'Đang làm';
        break;
      case QuestStatus.notStarted:
      default:
        color = AppColors.info;
        text = 'Khả dụng';
        break;
    }

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
      decoration: BoxDecoration(
        color: color.withOpacity(0.2),
        borderRadius: BorderRadius.circular(10),
        border: Border.all(color: color.withOpacity(0.5), width: 1),
      ),
      child: Text(
        text,
        style: TextStyle(
          color: color,
          fontSize: 11,
          fontWeight: FontWeight.bold,
        ),
      ),
    );
  }

  Widget _buildEmptyState(BuildContext context) {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(Icons.assignment_outlined, size: 48, color: Colors.white38),
          const SizedBox(height: 12),
          const Text(
            'Không có nhiệm vụ nào trong danh mục này',
            style: TextStyle(color: Colors.white70, fontSize: 14),
          ),
        ],
      ),
    );
  }
}
