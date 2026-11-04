import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../../core/theme/app_colors.dart';
import '../../../../routing/route_names.dart';
import '../../../../shared/widgets/glass/animated_background.dart';
import '../../../../shared/widgets/glass/glass_container.dart';
import '../../data/models/quest_model.dart';
import '../providers/quests_provider.dart';

/// Quests screen displaying all learning quests categorized by status.
class QuestsScreen extends ConsumerStatefulWidget {
  const QuestsScreen({super.key});

  @override
  ConsumerState<QuestsScreen> createState() => _QuestsScreenState();
}

class _QuestsScreenState extends ConsumerState<QuestsScreen>
    with SingleTickerProviderStateMixin {
  late TabController _tabController;

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 3, vsync: this);
  }

  @override
  void dispose() {
    _tabController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final questsState = ref.watch(questsNotifierProvider);

    return Scaffold(
      body: AnimatedGradientBackground(
        child: SafeArea(
          child: Column(
            children: [
              _buildHeader(context),
              if (questsState.isOffline) _buildOfflineBanner(),
              _buildTabBar(questsState),
              Expanded(
                child: questsState.isLoading
                    ? const Center(
                        child: CircularProgressIndicator(color: AppColors.primary),
                      )
                    : questsState.error != null && questsState.quests.isEmpty
                        ? _buildErrorView(questsState.error!)
                        : TabBarView(
                            controller: _tabController,
                            children: [
                              _buildQuestList(questsState.activeQuests, 'active'),
                              _buildQuestList(questsState.completedQuests, 'completed'),
                              _buildQuestList(questsState.lockedQuests, 'locked'),
                            ],
                          ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildHeader(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.fromLTRB(16, 12, 16, 8),
      child: Row(
        children: [
          IconButton(
            onPressed: () => context.pop(),
            icon: const Icon(Icons.arrow_back_ios_new, color: Colors.white, size: 20),
            style: IconButton.styleFrom(
              backgroundColor: Colors.white.withOpacity(0.08),
              padding: const EdgeInsets.all(8),
            ),
          ),
          const SizedBox(width: 12),
          const Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  'Nhiệm Vụ Di Sản',
                  style: TextStyle(
                    color: Colors.white,
                    fontSize: 22,
                    fontWeight: FontWeight.bold,
                  ),
                ),
                Text(
                  'Khám phá Cửu Đỉnh & Nhận chứng chỉ',
                  style: TextStyle(
                    color: Colors.white70,
                    fontSize: 12,
                  ),
                ),
              ],
            ),
          ),
          IconButton(
            onPressed: () => ref.read(questsNotifierProvider.notifier).loadQuests(),
            icon: const Icon(Icons.refresh, color: AppColors.primary, size: 22),
            style: IconButton.styleFrom(
              backgroundColor: Colors.white.withOpacity(0.08),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildOfflineBanner() {
    return Container(
      width: double.infinity,
      margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 4),
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
      decoration: BoxDecoration(
        color: AppColors.warning.withOpacity(0.2),
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: AppColors.warning.withOpacity(0.4)),
      ),
      child: const Row(
        children: [
          Icon(Icons.cloud_off, color: AppColors.warning, size: 16),
          SizedBox(width: 8),
          Expanded(
            child: Text(
              'Chế độ ngoại tuyến: Hiển thị nhiệm vụ lưu tạm',
              style: TextStyle(color: Colors.white, fontSize: 12),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildTabBar(QuestsState state) {
    return Container(
      margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      padding: const EdgeInsets.all(4),
      decoration: BoxDecoration(
        color: Colors.white.withOpacity(0.08),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: Colors.white.withOpacity(0.08)),
      ),
      child: TabBar(
        controller: _tabController,
        indicator: BoxDecoration(
          gradient: const LinearGradient(
            colors: [AppColors.primaryDark, AppColors.primaryLight],
          ),
          borderRadius: BorderRadius.circular(12),
        ),
        indicatorSize: TabBarIndicatorSize.tab,
        labelColor: AppColors.onPrimary,
        unselectedLabelColor: Colors.white70,
        labelStyle: const TextStyle(fontWeight: FontWeight.bold, fontSize: 13),
        dividerColor: Colors.transparent,
        tabs: [
          Tab(text: 'Khả dụng (${state.activeQuests.length})'),
          Tab(text: 'Đã đạt (${state.completedQuests.length})'),
          Tab(text: 'Đã khóa (${state.lockedQuests.length})'),
        ],
      ),
    );
  }

  Widget _buildQuestList(List<QuestModel> quests, String tabType) {
    if (quests.isEmpty) {
      return RefreshIndicator(
        onRefresh: () => ref.read(questsNotifierProvider.notifier).loadQuests(),
        child: ListView(
          physics: const AlwaysScrollableScrollPhysics(),
          children: [
            SizedBox(height: MediaQuery.of(context).size.height * 0.2),
            Icon(
              tabType == 'completed'
                  ? Icons.emoji_events_outlined
                  : tabType == 'locked'
                      ? Icons.lock_outline
                      : Icons.assignment_outlined,
              size: 64,
              color: Colors.white30,
            ),
            const SizedBox(height: 16),
            Center(
              child: Text(
                tabType == 'completed'
                    ? 'Chưa hoàn thành nhiệm vụ nào'
                    : tabType == 'locked'
                        ? 'Không có nhiệm vụ nào bị khóa'
                        : 'Không có nhiệm vụ khả dụng',
                style: const TextStyle(color: Colors.white70, fontSize: 15),
              ),
            ),
          ],
        ),
      );
    }

    return RefreshIndicator(
      onRefresh: () => ref.read(questsNotifierProvider.notifier).loadQuests(),
      child: ListView.builder(
        padding: const EdgeInsets.fromLTRB(16, 8, 16, 24),
        itemCount: quests.length,
        itemBuilder: (context, index) {
          final quest = quests[index];
          return _buildQuestCard(quest);
        },
      ),
    );
  }

  Widget _buildQuestCard(QuestModel quest) {
    final canClaim = quest.canClaim;
    final isLocked = quest.isLocked;

    return Padding(
      padding: const EdgeInsets.only(bottom: 12),
      child: GlassContainer(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Container(
                  width: 44,
                  height: 44,
                  decoration: BoxDecoration(
                    color: isLocked
                        ? Colors.white.withOpacity(0.06)
                        : quest.isCompleted
                            ? AppColors.success.withOpacity(0.18)
                            : AppColors.primary.withOpacity(0.18),
                    borderRadius: BorderRadius.circular(12),
                    border: Border.all(
                      color: isLocked
                          ? Colors.white12
                          : quest.isCompleted
                              ? AppColors.success.withOpacity(0.4)
                              : AppColors.primary.withOpacity(0.4),
                    ),
                  ),
                  child: Icon(
                    isLocked
                        ? Icons.lock
                        : quest.isCompleted
                            ? Icons.verified
                            : Icons.military_tech,
                    color: isLocked
                        ? Colors.white38
                        : quest.isCompleted
                            ? AppColors.success
                            : AppColors.primary,
                    size: 24,
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        quest.name,
                        style: TextStyle(
                          color: isLocked ? Colors.white60 : Colors.white,
                          fontSize: 16,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                      if (quest.description != null) ...[
                        const SizedBox(height: 4),
                        Text(
                          quest.description!,
                          style: TextStyle(
                            color: isLocked ? Colors.white38 : Colors.white70,
                            fontSize: 12,
                          ),
                          maxLines: 2,
                          overflow: TextOverflow.ellipsis,
                        ),
                      ],
                    ],
                  ),
                ),
              ],
            ),
            const SizedBox(height: 12),
            // Progress Bar
            Row(
              children: [
                Expanded(
                  child: ClipRRect(
                    borderRadius: BorderRadius.circular(6),
                    child: LinearProgressIndicator(
                      value: (quest.progressPercent / 100.0).clamp(0.0, 1.0),
                      minHeight: 8,
                      backgroundColor: Colors.white.withOpacity(0.1),
                      valueColor: AlwaysStoppedAnimation<Color>(
                        quest.isCompleted
                            ? AppColors.success
                            : canClaim
                                ? AppColors.xpGold
                                : AppColors.primary,
                      ),
                    ),
                  ),
                ),
                const SizedBox(width: 10),
                Text(
                  '${quest.progressPercent.toStringAsFixed(0)}%',
                  style: TextStyle(
                    color: isLocked ? Colors.white38 : Colors.white70,
                    fontSize: 12,
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 12),
            // Rewards row and action button
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Wrap(
                  spacing: 6,
                  children: [
                    if (quest.totalXpReward > 0)
                      _buildRewardChip(
                        '+${quest.totalXpReward} XP',
                        Icons.star_rounded,
                        AppColors.xpGold,
                      ),
                    if (quest.badgeRewards.isNotEmpty)
                      _buildRewardChip(
                        'Huy hiệu',
                        Icons.military_tech,
                        Colors.purpleAccent,
                      ),
                    if (quest.streakFreezeRewards > 0)
                      _buildRewardChip(
                        '+${quest.streakFreezeRewards} Băng',
                        Icons.ac_unit,
                        Colors.lightBlueAccent,
                      ),
                  ],
                ),
                _buildActionButton(quest),
              ],
            ),
            if (isLocked && quest.lockReason != null) ...[
              const SizedBox(height: 8),
              Row(
                children: [
                  const Icon(Icons.info_outline, color: AppColors.warning, size: 14),
                  const SizedBox(width: 4),
                  Expanded(
                    child: Text(
                      'Yêu cầu: ${quest.lockReason}',
                      style: const TextStyle(color: AppColors.warning, fontSize: 11),
                      overflow: TextOverflow.ellipsis,
                    ),
                  ),
                ],
              ),
            ],
          ],
        ),
      ),
    );
  }

  Widget _buildRewardChip(String label, IconData icon, Color color) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
      decoration: BoxDecoration(
        color: color.withOpacity(0.12),
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: color.withOpacity(0.3)),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(icon, color: color, size: 13),
          const SizedBox(width: 4),
          Text(
            label,
            style: TextStyle(
              color: color,
              fontSize: 11,
              fontWeight: FontWeight.w600,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildActionButton(QuestModel quest) {
    if (quest.isLocked) {
      return TextButton(
        onPressed: null,
        child: const Text('Đã khóa', style: TextStyle(color: Colors.white38)),
      );
    }

    if (quest.isCompleted) {
      return OutlinedButton.icon(
        onPressed: () => context.push('${RoutePaths.quests}/${quest.slug}'),
        icon: const Icon(Icons.check_circle, color: AppColors.success, size: 15),
        label: const Text('Xem lại', style: TextStyle(color: Colors.white70, fontSize: 12)),
        style: OutlinedButton.styleFrom(
          side: const BorderSide(color: Colors.white24),
          padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
        ),
      );
    }

    if (quest.canClaim) {
      return ElevatedButton(
        onPressed: () => _handleClaim(quest.slug),
        style: ElevatedButton.styleFrom(
          backgroundColor: AppColors.xpGold,
          foregroundColor: Colors.black87,
          padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
          elevation: 4,
        ),
        child: const Text(
          'Nhận thưởng',
          style: TextStyle(fontWeight: FontWeight.bold, fontSize: 12),
        ),
      );
    }

    return ElevatedButton(
      onPressed: () => context.push('${RoutePaths.quests}/${quest.slug}'),
      style: ElevatedButton.styleFrom(
        backgroundColor: AppColors.primary,
        foregroundColor: AppColors.onPrimary,
        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
      ),
      child: Text(
        quest.isInProgress ? 'Chi tiết' : 'Bắt đầu',
        style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 12),
      ),
    );
  }

  Future<void> _handleClaim(String slug) async {
    try {
      final res = await ref.read(questsNotifierProvider.notifier).claimReward(slug);
      if (mounted && res != null) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            backgroundColor: AppColors.success,
            content: Text(
              'Chúc mừng! Đã nhận ${res.xpAwarded} XP cho nhiệm vụ "${res.questName}"!',
              style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold),
            ),
          ),
        );
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            backgroundColor: AppColors.error,
            content: Text(
              'Không thể nhận thưởng: ${e.toString().replaceAll("Exception: ", "")}',
              style: const TextStyle(color: Colors.white),
            ),
          ),
        );
      }
    }
  }

  Widget _buildErrorView(String error) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Icon(Icons.error_outline, color: AppColors.error, size: 48),
            const SizedBox(height: 16),
            Text(
              error,
              textAlign: TextAlign.center,
              style: const TextStyle(color: Colors.white70),
            ),
            const SizedBox(height: 16),
            ElevatedButton(
              onPressed: () => ref.read(questsNotifierProvider.notifier).loadQuests(),
              child: const Text('Thử lại'),
            ),
          ],
        ),
      ),
    );
  }
}
