import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../../core/theme/app_colors.dart';
import '../../../../shared/widgets/glass/animated_background.dart';
import '../../../../shared/widgets/glass/glass_container.dart';
import '../../data/models/quest_model.dart';
import '../providers/quests_provider.dart';

/// Screen displaying in-depth quest details, steps, objectives, and reward claiming.
class QuestDetailScreen extends ConsumerStatefulWidget {
  final String questSlug;

  const QuestDetailScreen({super.key, required this.questSlug});

  @override
  ConsumerState<QuestDetailScreen> createState() => _QuestDetailScreenState();
}

class _QuestDetailScreenState extends ConsumerState<QuestDetailScreen> {
  late Future<QuestModel> _detailFuture;
  bool _isClaiming = false;

  @override
  void initState() {
    super.initState();
    _loadDetail();
  }

  void _loadDetail() {
    _detailFuture = ref
        .read(questsNotifierProvider.notifier)
        .getQuestDetail(widget.questSlug);
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: AnimatedGradientBackground(
        child: SafeArea(
          child: FutureBuilder<QuestModel>(
            future: _detailFuture,
            builder: (context, snapshot) {
              if (snapshot.connectionState == ConnectionState.waiting) {
                return const Center(
                  child: CircularProgressIndicator(color: AppColors.primary),
                );
              }

              if (snapshot.hasError) {
                return _buildErrorState(snapshot.error.toString());
              }

              final quest = snapshot.data!;
              return Column(
                children: [
                  _buildTopBar(context, quest),
                  Expanded(
                    child: SingleChildScrollView(
                      padding: const EdgeInsets.fromLTRB(16, 8, 16, 24),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          _buildQuestHeroCard(quest),
                          const SizedBox(height: 16),
                          _buildRewardsCard(quest),
                          if (quest.certificate != null) ...[
                            const SizedBox(height: 16),
                            _buildCertificateCard(quest.certificate!),
                          ],
                          const SizedBox(height: 20),
                          _buildStepsSection(quest),
                        ],
                      ),
                    ),
                  ),
                  _buildBottomActionBar(quest),
                ],
              );
            },
          ),
        ),
      ),
    );
  }

  Widget _buildTopBar(BuildContext context, QuestModel quest) {
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
          Expanded(
            child: Text(
              quest.name,
              style: const TextStyle(
                color: Colors.white,
                fontSize: 18,
                fontWeight: FontWeight.bold,
              ),
              maxLines: 1,
              overflow: TextOverflow.ellipsis,
            ),
          ),
          IconButton(
            onPressed: () {
              setState(() {
                _loadDetail();
              });
            },
            icon: const Icon(Icons.refresh, color: AppColors.primary, size: 22),
            style: IconButton.styleFrom(
              backgroundColor: Colors.white.withOpacity(0.08),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildQuestHeroCard(QuestModel quest) {
    return GlassContainer(
      padding: const EdgeInsets.all(18),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                decoration: BoxDecoration(
                  color: AppColors.primary.withOpacity(0.2),
                  borderRadius: BorderRadius.circular(8),
                  border: Border.all(color: AppColors.primary.withOpacity(0.4)),
                ),
                child: Text(
                  quest.category?.toUpperCase() ?? 'NHIỆM VỤ',
                  style: const TextStyle(
                    color: AppColors.primaryLight,
                    fontSize: 11,
                    fontWeight: FontWeight.bold,
                    letterSpacing: 0.8,
                  ),
                ),
              ),
              const Spacer(),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                decoration: BoxDecoration(
                  color: quest.isCompleted
                      ? AppColors.success.withOpacity(0.2)
                      : quest.isLocked
                          ? Colors.white10
                          : AppColors.warning.withOpacity(0.2),
                  borderRadius: BorderRadius.circular(8),
                ),
                child: Text(
                  quest.isCompleted
                      ? 'ĐÃ HOÀN THÀNH'
                      : quest.isLocked
                          ? 'ĐÃ KHÓA'
                          : quest.isInProgress
                              ? 'ĐANG THỰC HIỆN'
                              : 'CHƯA BẮT ĐẦU',
                  style: TextStyle(
                    color: quest.isCompleted
                        ? AppColors.success
                        : quest.isLocked
                            ? Colors.white54
                            : AppColors.warning,
                    fontSize: 11,
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ),
            ],
          ),
          const SizedBox(height: 12),
          Text(
            quest.name,
            style: const TextStyle(
              color: Colors.white,
              fontSize: 20,
              fontWeight: FontWeight.bold,
            ),
          ),
          if (quest.description != null) ...[
            const SizedBox(height: 8),
            Text(
              quest.description!,
              style: const TextStyle(color: Colors.white70, fontSize: 13, height: 1.4),
            ),
          ],
          const SizedBox(height: 16),
          // Progress bar
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              const Text(
                'Tiến độ nhiệm vụ',
                style: TextStyle(color: Colors.white70, fontSize: 13),
              ),
              Text(
                '${quest.progressPercent.toStringAsFixed(0)}%',
                style: const TextStyle(
                  color: Colors.white,
                  fontSize: 13,
                  fontWeight: FontWeight.bold,
                ),
              ),
            ],
          ),
          const SizedBox(height: 6),
          ClipRRect(
            borderRadius: BorderRadius.circular(6),
            child: LinearProgressIndicator(
              value: (quest.progressPercent / 100.0).clamp(0.0, 1.0),
              minHeight: 8,
              backgroundColor: Colors.white.withOpacity(0.12),
              valueColor: AlwaysStoppedAnimation<Color>(
                quest.isCompleted
                    ? AppColors.success
                    : quest.canClaim
                        ? AppColors.xpGold
                        : AppColors.primary,
              ),
            ),
          ),
          if (quest.isLocked && quest.lockReason != null) ...[
            const SizedBox(height: 12),
            Container(
              padding: const EdgeInsets.all(10),
              decoration: BoxDecoration(
                color: AppColors.warning.withOpacity(0.15),
                borderRadius: BorderRadius.circular(8),
                border: Border.all(color: AppColors.warning.withOpacity(0.3)),
              ),
              child: Row(
                children: [
                  const Icon(Icons.lock, color: AppColors.warning, size: 16),
                  const SizedBox(width: 8),
                  Expanded(
                    child: Text(
                      'Yêu cầu mở khóa: ${quest.lockReason}',
                      style: const TextStyle(color: AppColors.warning, fontSize: 12),
                    ),
                  ),
                ],
              ),
            ),
          ],
        ],
      ),
    );
  }

  Widget _buildRewardsCard(QuestModel quest) {
    return GlassContainer(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text(
            'Phần Thưởng Hoàn Thành',
            style: TextStyle(
              color: Colors.white,
              fontSize: 15,
              fontWeight: FontWeight.bold,
            ),
          ),
          const SizedBox(height: 12),
          Wrap(
            spacing: 12,
            runSpacing: 10,
            children: [
              if (quest.totalXpReward > 0)
                _buildRewardItem(
                  Icons.star_rounded,
                  AppColors.xpGold,
                  '+${quest.totalXpReward} XP',
                  'Kinh nghiệm',
                ),
              if (quest.badgeRewards.isNotEmpty)
                _buildRewardItem(
                  Icons.military_tech,
                  Colors.purpleAccent,
                  'Huy Hiệu',
                  quest.badgeRewards.join(', '),
                ),
              if (quest.streakFreezeRewards > 0)
                _buildRewardItem(
                  Icons.ac_unit,
                  Colors.lightBlueAccent,
                  '+${quest.streakFreezeRewards} Đóng Băng',
                  'Bảo vệ chuỗi',
                ),
              _buildRewardItem(
                Icons.workspace_premium,
                Colors.amberAccent,
                'Chứng Chỉ',
                'Xác thực số',
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildRewardItem(
      IconData icon, Color color, String title, String subtitle) {
    return Container(
      width: 140,
      padding: const EdgeInsets.all(10),
      decoration: BoxDecoration(
        color: color.withOpacity(0.12),
        borderRadius: BorderRadius.circular(10),
        border: Border.all(color: color.withOpacity(0.25)),
      ),
      child: Row(
        children: [
          Icon(icon, color: color, size: 22),
          const SizedBox(width: 8),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  title,
                  style: TextStyle(
                    color: color,
                    fontSize: 12,
                    fontWeight: FontWeight.bold,
                  ),
                  overflow: TextOverflow.ellipsis,
                ),
                Text(
                  subtitle,
                  style: const TextStyle(color: Colors.white60, fontSize: 10),
                  overflow: TextOverflow.ellipsis,
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildCertificateCard(QuestCertificateModel certificate) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        gradient: LinearGradient(
          colors: [
            AppColors.primaryDark.withOpacity(0.8),
            AppColors.primary.withOpacity(0.7),
          ],
        ),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: AppColors.xpGold.withOpacity(0.5), width: 1.5),
        boxShadow: [
          BoxShadow(
            color: AppColors.primary.withOpacity(0.3),
            blurRadius: 12,
            offset: const Offset(0, 4),
          ),
        ],
      ),
      child: Row(
        children: [
          Container(
            padding: const EdgeInsets.all(10),
            decoration: BoxDecoration(
              color: AppColors.xpGold.withOpacity(0.2),
              shape: BoxShape.circle,
            ),
            child: const Icon(Icons.verified, color: AppColors.xpGold, size: 28),
          ),
          const SizedBox(width: 14),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text(
                  'Chứng Chỉ Hoàn Thành Di Sản',
                  style: TextStyle(
                    color: Colors.white,
                    fontSize: 14,
                    fontWeight: FontWeight.bold,
                  ),
                ),
                const SizedBox(height: 4),
                Text(
                  'Mã số: ${certificate.code}',
                  style: const TextStyle(
                    color: AppColors.xpGold,
                    fontSize: 12,
                    fontFamily: 'monospace',
                  ),
                ),
                Text(
                  'Cấp bởi: ${certificate.issuerName}',
                  style: const TextStyle(color: Colors.white70, fontSize: 11),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildStepsSection(QuestModel quest) {
    if (quest.steps.isEmpty) {
      return const SizedBox.shrink();
    }

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Text(
          'Các Bước Thực Hiện & Mục Tiêu',
          style: TextStyle(
            color: Colors.white,
            fontSize: 16,
            fontWeight: FontWeight.bold,
          ),
        ),
        const SizedBox(height: 12),
        ...quest.steps.map((step) => _buildStepCard(step)),
      ],
    );
  }

  Widget _buildStepCard(QuestStepModel step) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 12),
      child: GlassContainer(
        padding: const EdgeInsets.all(14),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                CircleAvatar(
                  radius: 12,
                  backgroundColor: step.completionPercent >= 100.0
                      ? AppColors.success
                      : AppColors.primary,
                  child: step.completionPercent >= 100.0
                      ? const Icon(Icons.check, size: 14, color: Colors.white)
                      : Text(
                          '${step.displayOrder}',
                          style: const TextStyle(
                            color: Colors.white,
                            fontSize: 11,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                ),
                const SizedBox(width: 10),
                Expanded(
                  child: Text(
                    step.title,
                    style: const TextStyle(
                      color: Colors.white,
                      fontSize: 14,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                ),
                Text(
                  '${step.completionPercent.toStringAsFixed(0)}%',
                  style: TextStyle(
                    color: step.completionPercent >= 100.0
                        ? AppColors.success
                        : Colors.white70,
                    fontSize: 12,
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ],
            ),
            if (step.description != null) ...[
              const SizedBox(height: 6),
              Padding(
                padding: const EdgeInsets.only(left: 34),
                child: Text(
                  step.description!,
                  style: const TextStyle(color: Colors.white60, fontSize: 12),
                ),
              ),
            ],
            const SizedBox(height: 10),
            ...step.objectives.map((obj) => _buildObjectiveItem(obj)),
          ],
        ),
      ),
    );
  }

  Widget _buildObjectiveItem(QuestObjectiveModel objective) {
    return Container(
      margin: const EdgeInsets.only(top: 8),
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 8),
      decoration: BoxDecoration(
        color: Colors.white.withOpacity(0.04),
        borderRadius: BorderRadius.circular(8),
        border: Border.all(
          color: objective.isComplete
              ? AppColors.success.withOpacity(0.3)
              : Colors.white10,
        ),
      ),
      child: Row(
        children: [
          Icon(
            objective.isComplete
                ? Icons.check_circle
                : Icons.radio_button_unchecked,
            color: objective.isComplete ? AppColors.success : Colors.white38,
            size: 16,
          ),
          const SizedBox(width: 8),
          Expanded(
            child: Text(
              objective.displayName,
              style: TextStyle(
                color: objective.isComplete ? Colors.white70 : Colors.white,
                fontSize: 12,
              ),
            ),
          ),
          const SizedBox(width: 8),
          Text(
            '${objective.currentValue}/${objective.targetValue}',
            style: TextStyle(
              color: objective.isComplete ? AppColors.success : AppColors.primaryLight,
              fontSize: 12,
              fontWeight: FontWeight.bold,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildBottomActionBar(QuestModel quest) {
    if (quest.isLocked) {
      return Container(
        padding: const EdgeInsets.all(16),
        width: double.infinity,
        child: ElevatedButton.icon(
          onPressed: null,
          icon: const Icon(Icons.lock, size: 16),
          label: const Text('Nhiệm vụ bị khóa'),
        ),
      );
    }

    if (quest.isCompleted) {
      return Container(
        padding: const EdgeInsets.all(16),
        width: double.infinity,
        child: ElevatedButton.icon(
          onPressed: null,
          icon: const Icon(Icons.verified, color: AppColors.success, size: 18),
          label: const Text('Đã nhận toàn bộ phần thưởng'),
          style: ElevatedButton.styleFrom(
            backgroundColor: AppColors.success.withOpacity(0.2),
            foregroundColor: AppColors.success,
          ),
        ),
      );
    }

    if (quest.canClaim) {
      return Container(
        padding: const EdgeInsets.all(16),
        width: double.infinity,
        child: ElevatedButton(
          onPressed: _isClaiming ? null : () => _claimRewards(quest),
          style: ElevatedButton.styleFrom(
            backgroundColor: AppColors.xpGold,
            foregroundColor: Colors.black87,
            padding: const EdgeInsets.symmetric(vertical: 14),
            elevation: 6,
          ),
          child: _isClaiming
              ? const SizedBox(
                  height: 18,
                  width: 18,
                  child: CircularProgressIndicator(strokeWidth: 2, color: Colors.black87),
                )
              : const Text(
                  'NHẬN PHẦN THƯỞNG NGAY',
                  style: TextStyle(fontSize: 14, fontWeight: FontWeight.bold),
                ),
        ),
      );
    }

    if (!quest.isInProgress) {
      return Container(
        padding: const EdgeInsets.all(16),
        width: double.infinity,
        child: ElevatedButton(
          onPressed: () => _startQuest(quest.slug),
          style: ElevatedButton.styleFrom(
            backgroundColor: AppColors.primary,
            foregroundColor: AppColors.onPrimary,
            padding: const EdgeInsets.symmetric(vertical: 14),
          ),
          child: const Text(
            'BẮT ĐẦU NHIỆM VỤ',
            style: TextStyle(fontSize: 14, fontWeight: FontWeight.bold),
          ),
        ),
      );
    }

    return Container(
      padding: const EdgeInsets.all(16),
      width: double.infinity,
      child: OutlinedButton(
        onPressed: () => context.pop(),
        style: OutlinedButton.styleFrom(
          side: const BorderSide(color: AppColors.primary),
          padding: const EdgeInsets.symmetric(vertical: 14),
        ),
        child: Text(
          'ĐANG THỰC HIỆN (${quest.progressPercent.toStringAsFixed(0)}%) - TIẾP TỤC HỌC',
          style: const TextStyle(
            color: AppColors.primaryLight,
            fontSize: 13,
            fontWeight: FontWeight.bold,
          ),
        ),
      ),
    );
  }

  Future<void> _startQuest(String slug) async {
    final success =
        await ref.read(questsNotifierProvider.notifier).startQuest(slug);
    if (success && mounted) {
      setState(() {
        _loadDetail();
      });
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          backgroundColor: AppColors.primary,
          content: Text('Đã bắt đầu nhiệm vụ!'),
        ),
      );
    }
  }

  Future<void> _claimRewards(QuestModel quest) async {
    setState(() => _isClaiming = true);
    try {
      final res = await ref
          .read(questsNotifierProvider.notifier)
          .claimReward(quest.slug);

      if (mounted && res != null) {
        setState(() {
          _isClaiming = false;
          _loadDetail();
        });

        // Show celebratory success dialog
        showDialog(
          context: context,
          builder: (ctx) => AlertDialog(
            backgroundColor: AppColors.surface,
            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
            title: const Row(
              children: [
                Icon(Icons.emoji_events, color: AppColors.xpGold, size: 28),
                SizedBox(width: 10),
                Text('Chúc Mừng!', style: TextStyle(color: Colors.white)),
              ],
            ),
            content: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  'Bạn đã hoàn thành xuất sắc nhiệm vụ "${res.questName}"!',
                  style: const TextStyle(color: Colors.white70),
                ),
                const SizedBox(height: 12),
                Text(
                  '+${res.xpAwarded} XP đã được cộng vào tài khoản.',
                  style: const TextStyle(
                    color: AppColors.xpGold,
                    fontWeight: FontWeight.bold,
                  ),
                ),
                if (res.certificate != null) ...[
                  const SizedBox(height: 8),
                  Text(
                    'Chứng chỉ: ${res.certificate!.code}',
                    style: const TextStyle(
                      color: AppColors.primaryLight,
                      fontFamily: 'monospace',
                    ),
                  ),
                ],
              ],
            ),
            actions: [
              TextButton(
                onPressed: () => Navigator.of(ctx).pop(),
                child: const Text('Tuyệt vời'),
              ),
            ],
          ),
        );
      }
    } catch (e) {
      if (mounted) {
        setState(() => _isClaiming = false);
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

  Widget _buildErrorState(String error) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Icon(Icons.error_outline, color: AppColors.error, size: 48),
            const SizedBox(height: 16),
            Text(
              'Không thể tải chi tiết nhiệm vụ: $error',
              textAlign: TextAlign.center,
              style: const TextStyle(color: Colors.white70),
            ),
            const SizedBox(height: 16),
            ElevatedButton(
              onPressed: () => setState(() => _loadDetail()),
              child: const Text('Thử lại'),
            ),
          ],
        ),
      ),
    );
  }
}
