import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../../core/theme/app_colors.dart';
import '../../../../core/theme/app_spacing.dart';
import '../../../../routing/route_names.dart';
import '../../../../shared/widgets/glass/glass_container.dart';
import '../../../quests/domain/entities/quest.dart';
import '../../../quests/presentation/providers/quests_provider.dart';

/// Card showing the current active heritage quest on the Learning Path.
class QuestPathCard extends ConsumerWidget {
  const QuestPathCard({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final state = ref.watch(questsNotifierProvider);
    final activeQuests = state.quests.where((q) => !q.isLocked && q.status != QuestStatus.completed).toList();
    final quest = activeQuests.isNotEmpty ? activeQuests.first : null;

    if (quest == null) {
      return const SizedBox.shrink();
    }

    final canClaim = quest.progressPercent >= 100.0 && quest.status != QuestStatus.completed;

    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: AppSpacing.md, vertical: AppSpacing.xs),
      child: GlassContainer(
        padding: const EdgeInsets.all(AppSpacing.md),
        child: InkWell(
          onTap: () => context.push('${RoutePaths.quests}/${quest.slug}'),
          borderRadius: BorderRadius.circular(AppSpacing.radiusMD),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Row(
                    children: [
                      Container(
                        padding: const EdgeInsets.all(6),
                        decoration: BoxDecoration(
                          color: canClaim
                              ? AppColors.xpGold.withOpacity(0.2)
                              : AppColors.primary.withOpacity(0.2),
                          borderRadius: BorderRadius.circular(8),
                          border: Border.all(
                            color: canClaim
                                ? AppColors.xpGold.withOpacity(0.5)
                                : AppColors.primary.withOpacity(0.4),
                          ),
                        ),
                        child: Icon(
                          canClaim ? Icons.emoji_events : Icons.flag,
                          color: canClaim ? AppColors.xpGold : AppColors.primaryLight,
                          size: 16,
                        ),
                      ),
                      const SizedBox(width: 8),
                      Text(
                        'Nhiệm vụ đang diễn ra',
                        style: TextStyle(
                          color: Colors.white.withOpacity(0.8),
                          fontSize: 12,
                          fontWeight: FontWeight.w600,
                        ),
                      ),
                    ],
                  ),
                  TextButton(
                    onPressed: () => context.push(RoutePaths.quests),
                    style: TextButton.styleFrom(
                      padding: EdgeInsets.zero,
                      minimumSize: const Size(50, 24),
                      tapTargetSize: MaterialTapTargetSize.shrinkWrap,
                    ),
                    child: const Row(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        Text(
                          'Tất cả',
                          style: TextStyle(
                            color: AppColors.primaryLight,
                            fontSize: 12,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                        Icon(Icons.chevron_right, size: 16, color: AppColors.primaryLight),
                      ],
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 8),
              Text(
                quest.name,
                style: const TextStyle(
                  color: Colors.white,
                  fontSize: 16,
                  fontWeight: FontWeight.bold,
                ),
              ),
              if (quest.description.isNotEmpty) ...[
                const SizedBox(height: 4),
                Text(
                  quest.description,
                  style: TextStyle(
                    color: Colors.white.withOpacity(0.7),
                    fontSize: 12,
                  ),
                  maxLines: 2,
                  overflow: TextOverflow.ellipsis,
                ),
              ],
              const SizedBox(height: 10),
              // Progress indicator
              Row(
                children: [
                  Expanded(
                    child: ClipRRect(
                      borderRadius: BorderRadius.circular(4),
                      child: LinearProgressIndicator(
                        value: (quest.progressPercent / 100.0).clamp(0.0, 1.0),
                        minHeight: 6,
                        backgroundColor: Colors.white.withOpacity(0.12),
                        valueColor: AlwaysStoppedAnimation<Color>(
                          canClaim ? AppColors.xpGold : AppColors.primary,
                        ),
                      ),
                    ),
                  ),
                  const SizedBox(width: 10),
                  Text(
                    '${quest.progressPercent.toStringAsFixed(0)}%',
                    style: TextStyle(
                      color: canClaim ? AppColors.xpGold : Colors.white70,
                      fontSize: 12,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 10),
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                    decoration: BoxDecoration(
                      color: AppColors.xpGold.withOpacity(0.15),
                      borderRadius: BorderRadius.circular(6),
                      border: Border.all(color: AppColors.xpGold.withOpacity(0.3)),
                    ),
                    child: Row(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        const Icon(Icons.star, color: AppColors.xpGold, size: 12),
                        const SizedBox(width: 4),
                        Text(
                          '+${quest.xpReward} XP',
                          style: const TextStyle(
                            color: AppColors.xpGold,
                            fontSize: 11,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                      ],
                    ),
                  ),
                  ElevatedButton(
                    onPressed: () => context.push('${RoutePaths.quests}/${quest.slug}'),
                    style: ElevatedButton.styleFrom(
                      backgroundColor: canClaim ? AppColors.xpGold : AppColors.primary,
                      foregroundColor: canClaim ? Colors.black87 : Colors.white,
                      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                      minimumSize: const Size(70, 30),
                      tapTargetSize: MaterialTapTargetSize.shrinkWrap,
                    ),
                    child: Text(
                      canClaim ? 'Nhận thưởng' : 'Chi tiết',
                      style: const TextStyle(fontSize: 11, fontWeight: FontWeight.bold),
                    ),
                  ),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }
}
