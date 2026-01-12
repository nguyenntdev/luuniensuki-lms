import 'package:cached_network_image/cached_network_image.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../../core/theme/app_colors.dart';
import '../../domain/entities/urn.dart';

/// Sidebar widget that displays motif details and actions.
class MotifSidebar extends ConsumerWidget {
  final Motif motif;
  final VoidCallback onClose;
  final VoidCallback onStartLesson;
  final VoidCallback onStartQuiz;

  const MotifSidebar({
    super.key,
    required this.motif,
    required this.onClose,
    required this.onStartLesson,
    required this.onStartQuiz,
  });

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final theme = Theme.of(context);

    return Material(
      elevation: 16,
      child: Container(
        color: theme.colorScheme.surface,
        child: SafeArea(
          left: false,
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              // Header with close button
              _buildHeader(context),

              // Content
              Expanded(
                child: SingleChildScrollView(
                  padding: const EdgeInsets.all(16),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      // Thumbnail
                      if (motif.thumbnailUrl != null)
                        _buildThumbnail(motif.thumbnailUrl!),

                      const SizedBox(height: 16),

                      // Motif name
                      Text(
                        motif.name,
                        style: theme.textTheme.headlineSmall?.copyWith(
                          fontWeight: FontWeight.bold,
                        ),
                      ),

                      if (motif.nameEn != null) ...[
                        const SizedBox(height: 4),
                        Text(
                          motif.nameEn!,
                          style: theme.textTheme.titleMedium?.copyWith(
                            color: Colors.grey[600],
                          ),
                        ),
                      ],

                      const SizedBox(height: 12),

                      // Category and rarity chips
                      Wrap(
                        spacing: 8,
                        runSpacing: 8,
                        children: [
                          _buildCategoryChip(motif.category),
                          _buildRarityChip(motif.rarity),
                        ],
                      ),

                      const SizedBox(height: 20),

                      // Progress stepper
                      _buildProgressStepper(),

                      const SizedBox(height: 20),

                      // XP info
                      _buildXpInfo(),

                      const SizedBox(height: 16),

                      // Description
                      if (motif.description != null) ...[
                        Text(
                          'Mô tả',
                          style: theme.textTheme.titleSmall?.copyWith(
                            fontWeight: FontWeight.bold,
                            color: AppColors.textSecondary,
                          ),
                        ),
                        const SizedBox(height: 8),
                        Text(
                          motif.description!,
                          style: theme.textTheme.bodyMedium,
                        ),
                      ],
                    ],
                  ),
                ),
              ),

              // Action button
              Padding(
                padding: const EdgeInsets.all(16),
                child: _buildActionButton(context),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildHeader(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
      decoration: BoxDecoration(
        color: AppColors.primary.withOpacity(0.1),
        border: Border(
          bottom: BorderSide(color: AppColors.primary.withOpacity(0.2)),
        ),
      ),
      child: Row(
        children: [
          IconButton(
            icon: const Icon(Icons.close),
            onPressed: onClose,
            tooltip: 'Đóng',
          ),
          const Expanded(
            child: Text(
              'Chi tiết họa tiết',
              style: TextStyle(
                fontWeight: FontWeight.w600,
                fontSize: 16,
              ),
            ),
          ),
          // Status indicator
          _buildStatusIndicator(),
        ],
      ),
    );
  }

  Widget _buildStatusIndicator() {
    final statusColor = _getStatusColor(motif.status);
    final statusLabel = _getStatusLabel(motif.status);

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
      decoration: BoxDecoration(
        color: statusColor.withOpacity(0.2),
        borderRadius: BorderRadius.circular(16),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(
            _getStatusIcon(motif.status),
            size: 14,
            color: statusColor,
          ),
          const SizedBox(width: 4),
          Text(
            statusLabel,
            style: TextStyle(
              color: statusColor,
              fontSize: 12,
              fontWeight: FontWeight.w600,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildThumbnail(String url) {
    return ClipRRect(
      borderRadius: BorderRadius.circular(12),
      child: AspectRatio(
        aspectRatio: 16 / 10,
        child: CachedNetworkImage(
          imageUrl: url,
          fit: BoxFit.cover,
          placeholder: (context, url) => Container(
            color: Colors.grey[200],
            child: const Center(
              child: CircularProgressIndicator(strokeWidth: 2),
            ),
          ),
          errorWidget: (context, url, error) => Container(
            color: Colors.grey[200],
            child: const Icon(Icons.image_not_supported, size: 48),
          ),
        ),
      ),
    );
  }

  Widget _buildCategoryChip(MotifCategory category) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
      decoration: BoxDecoration(
        color: AppColors.primary.withOpacity(0.1),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: AppColors.primary.withOpacity(0.3)),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(
            _getCategoryIcon(category),
            size: 14,
            color: AppColors.primary,
          ),
          const SizedBox(width: 4),
          Text(
            category.nameVi,
            style: const TextStyle(
              color: AppColors.primary,
              fontSize: 12,
              fontWeight: FontWeight.w500,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildRarityChip(MotifRarity rarity) {
    final color = _getRarityColor(rarity);

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
      decoration: BoxDecoration(
        color: color.withOpacity(0.1),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: color.withOpacity(0.3)),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(Icons.auto_awesome, size: 14, color: color),
          const SizedBox(width: 4),
          Text(
            rarity.nameVi,
            style: TextStyle(
              color: color,
              fontSize: 12,
              fontWeight: FontWeight.w500,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildProgressStepper() {
    final steps = [
      _ProgressStep(
        label: 'Khám Phá',
        xp: 25,
        icon: Icons.explore,
        isCompleted: motif.isDiscovered,
        isCurrent: motif.status == MotifStatus.discovered,
      ),
      _ProgressStep(
        label: 'Bài Học',
        xp: 50,
        icon: Icons.school,
        isCompleted: motif.isLearned,
        isCurrent: motif.status == MotifStatus.learned,
      ),
      _ProgressStep(
        label: 'Trắc Nghiệm',
        xp: 75,
        icon: Icons.quiz,
        isCompleted: motif.isMastered,
        isCurrent: false,
      ),
    ];

    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.grey[50],
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: Colors.grey[200]!),
      ),
      child: Row(
        children: [
          for (int i = 0; i < steps.length; i++) ...[
            Expanded(child: _buildStepItem(steps[i])),
            if (i < steps.length - 1)
              Expanded(
                child: Container(
                  height: 2,
                  color: steps[i].isCompleted
                      ? AppColors.statusDiscovered
                      : Colors.grey[300],
                ),
              ),
          ],
        ],
      ),
    );
  }

  Widget _buildStepItem(_ProgressStep step) {
    Color circleColor;
    Color iconColor;

    if (step.isCompleted) {
      circleColor = AppColors.statusDiscovered;
      iconColor = Colors.white;
    } else if (step.isCurrent) {
      circleColor = AppColors.primary;
      iconColor = Colors.white;
    } else {
      circleColor = Colors.grey[300]!;
      iconColor = Colors.grey[500]!;
    }

    return Column(
      mainAxisSize: MainAxisSize.min,
      children: [
        Container(
          width: 36,
          height: 36,
          decoration: BoxDecoration(
            color: circleColor,
            shape: BoxShape.circle,
          ),
          child: Icon(
            step.isCompleted ? Icons.check : step.icon,
            color: iconColor,
            size: 18,
          ),
        ),
        const SizedBox(height: 6),
        Text(
          step.label,
          style: TextStyle(
            fontSize: 11,
            fontWeight: step.isCurrent ? FontWeight.bold : FontWeight.normal,
            color: step.isCompleted || step.isCurrent
                ? AppColors.textPrimary
                : AppColors.textHint,
          ),
          textAlign: TextAlign.center,
        ),
        const SizedBox(height: 2),
        Text(
          '+${step.xp} XP',
          style: TextStyle(
            fontSize: 10,
            color: step.isCompleted
                ? AppColors.statusDiscovered
                : AppColors.textHint,
            fontWeight: FontWeight.w500,
          ),
        ),
      ],
    );
  }

  Widget _buildXpInfo() {
    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        gradient: LinearGradient(
          colors: [
            AppColors.xpGold.withOpacity(0.1),
            AppColors.xpGold.withOpacity(0.05),
          ],
        ),
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: AppColors.xpGold.withOpacity(0.3)),
      ),
      child: Row(
        children: [
          const Icon(Icons.stars, color: AppColors.xpGold, size: 24),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text(
                  'XP đã kiếm được',
                  style: TextStyle(
                    fontSize: 12,
                    color: AppColors.textSecondary,
                  ),
                ),
                Text(
                  '${motif.xpEarned} / 150 XP',
                  style: const TextStyle(
                    fontSize: 16,
                    fontWeight: FontWeight.bold,
                    color: AppColors.xpGold,
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildActionButton(BuildContext context) {
    switch (motif.status) {
      case MotifStatus.hidden:
        return const SizedBox.shrink();

      case MotifStatus.discovered:
        return ElevatedButton.icon(
          onPressed: onStartLesson,
          icon: const Icon(Icons.school),
          label: const Text('Bắt đầu bài học'),
          style: ElevatedButton.styleFrom(
            padding: const EdgeInsets.symmetric(vertical: 14),
          ),
        );

      case MotifStatus.learned:
        return Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            ElevatedButton.icon(
              onPressed: onStartQuiz,
              icon: const Icon(Icons.quiz),
              label: const Text('Làm trắc nghiệm'),
              style: ElevatedButton.styleFrom(
                padding: const EdgeInsets.symmetric(vertical: 14),
              ),
            ),
            const SizedBox(height: 8),
            TextButton.icon(
              onPressed: onStartLesson,
              icon: const Icon(Icons.replay, size: 18),
              label: const Text('Xem lại bài học'),
            ),
          ],
        );

      case MotifStatus.mastered:
        return Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Container(
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: AppColors.statusMastered.withOpacity(0.1),
                borderRadius: BorderRadius.circular(8),
              ),
              child: const Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Icon(Icons.verified, color: AppColors.statusMastered),
                  SizedBox(width: 8),
                  Text(
                    'Đã thành thạo!',
                    style: TextStyle(
                      color: AppColors.statusMastered,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 8),
            Row(
              children: [
                Expanded(
                  child: OutlinedButton.icon(
                    onPressed: onStartLesson,
                    icon: const Icon(Icons.replay, size: 18),
                    label: const Text('Xem lại'),
                  ),
                ),
                const SizedBox(width: 8),
                Expanded(
                  child: OutlinedButton.icon(
                    onPressed: onStartQuiz,
                    icon: const Icon(Icons.quiz, size: 18),
                    label: const Text('Làm lại'),
                  ),
                ),
              ],
            ),
          ],
        );
    }
  }

  // Helper methods

  Color _getStatusColor(MotifStatus status) {
    switch (status) {
      case MotifStatus.hidden:
        return AppColors.statusHidden;
      case MotifStatus.discovered:
        return AppColors.statusDiscovered;
      case MotifStatus.learned:
        return AppColors.statusLearned;
      case MotifStatus.mastered:
        return AppColors.statusMastered;
    }
  }

  String _getStatusLabel(MotifStatus status) {
    switch (status) {
      case MotifStatus.hidden:
        return 'Chưa khám phá';
      case MotifStatus.discovered:
        return 'Đã khám phá';
      case MotifStatus.learned:
        return 'Đã học';
      case MotifStatus.mastered:
        return 'Thành thạo';
    }
  }

  IconData _getStatusIcon(MotifStatus status) {
    switch (status) {
      case MotifStatus.hidden:
        return Icons.lock;
      case MotifStatus.discovered:
        return Icons.explore;
      case MotifStatus.learned:
        return Icons.school;
      case MotifStatus.mastered:
        return Icons.star;
    }
  }

  IconData _getCategoryIcon(MotifCategory category) {
    switch (category) {
      case MotifCategory.thaoMoc:
        return Icons.eco;
      case MotifCategory.dongVat:
        return Icons.pets;
      case MotifCategory.diaLy:
        return Icons.terrain;
      case MotifCategory.voBi:
        return Icons.security;
      case MotifCategory.thienVan:
        return Icons.nights_stay;
      case MotifCategory.kienTruc:
        return Icons.architecture;
      case MotifCategory.nongNghiep:
        return Icons.agriculture;
      case MotifCategory.linhThu:
        return Icons.auto_awesome;
      case MotifCategory.giaoThuong:
        return Icons.sailing;
    }
  }

  Color _getRarityColor(MotifRarity rarity) {
    switch (rarity) {
      case MotifRarity.common:
        return AppColors.rarityCommon;
      case MotifRarity.uncommon:
        return AppColors.rarityUncommon;
      case MotifRarity.rare:
        return AppColors.rarityRare;
      case MotifRarity.epic:
        return AppColors.rarityEpic;
      case MotifRarity.legendary:
        return AppColors.rarityLegendary;
    }
  }
}

class _ProgressStep {
  final String label;
  final int xp;
  final IconData icon;
  final bool isCompleted;
  final bool isCurrent;

  const _ProgressStep({
    required this.label,
    required this.xp,
    required this.icon,
    required this.isCompleted,
    required this.isCurrent,
  });
}
