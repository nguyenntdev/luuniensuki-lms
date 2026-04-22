import 'package:flutter/material.dart';

import '../../../../core/theme/app_colors.dart';
import '../../../../core/theme/app_spacing.dart';
import '../../../../core/theme/app_typography.dart';
import '../../../urn_viewer/data/models/urn_dtos.dart';

/// Info tab showing motif metadata and details.
class InfoTab extends StatelessWidget {
  final MotifDetailDto motif;

  const InfoTab({super.key, required this.motif});

  @override
  Widget build(BuildContext context) {
    final isCompact = MediaQuery.of(context).size.width < 360;
    final contentPadding = EdgeInsets.all(
      isCompact ? AppSpacing.md : AppSpacing.lg,
    );

    return SingleChildScrollView(
      padding: contentPadding,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Basic info card
          _InfoCard(
            title: 'Thông tin cơ bản',
            children: [
              _InfoRow(
                icon: Icons.label_outline,
                label: 'Tên họa tiết',
                value: motif.name,
              ),
              if (motif.nameEn != null && motif.nameEn!.isNotEmpty)
                _InfoRow(
                  icon: Icons.translate,
                  label: 'Tên tiếng Anh',
                  value: motif.nameEn!,
                ),
              _InfoRow(
                icon: Icons.category_outlined,
                label: 'Phân loại',
                value: _getCategoryName(motif.category),
                valueColor: AppColors.primary,
              ),
              _InfoRow(
                icon: Icons.auto_awesome,
                label: 'Độ hiếm',
                value: _getRarityName(motif.rarity),
                valueColor: _getRarityColor(motif.rarity),
              ),
            ],
          ),

          const SizedBox(height: 16),

          // Position info card (for development/debug)
          _InfoCard(
            title: 'Vị trí trên đỉnh',
            children: [
              _InfoRow(
                icon: Icons.my_location,
                label: 'Mesh Name',
                value: motif.meshName,
                isCode: true,
              ),
              _InfoRow(
                icon: Icons.adjust,
                label: 'Tọa độ',
                value:
                    '(${motif.posX.toStringAsFixed(2)}, ${motif.posY.toStringAsFixed(2)}, ${motif.posZ.toStringAsFixed(2)})',
                isCode: true,
              ),
              _InfoRow(
                icon: Icons.radio_button_unchecked,
                label: 'Bán kính',
                value: motif.boundingRadius.toStringAsFixed(3),
                isCode: true,
              ),
            ],
          ),

          const SizedBox(height: 16),

          // Progress info card
          if (motif.progress != null) ...[
            _InfoCard(
              title: 'Tiến trình học tập',
              children: [
                _InfoRow(
                  icon: Icons.trending_up,
                  label: 'Trạng thái',
                  value: _getStatusName(motif.progress!.status),
                  valueColor: _getStatusColor(motif.progress!.status),
                ),
                _InfoRow(
                  icon: Icons.star,
                  label: 'XP đã nhận',
                  value: '${motif.progress!.xpEarned} XP',
                  valueColor: AppColors.xpGold,
                ),
                if (motif.progress!.discoveredAt != null)
                  _InfoRow(
                    icon: Icons.visibility,
                    label: 'Khám phá lúc',
                    value: _formatDateTime(motif.progress!.discoveredAt!),
                  ),
                if (motif.progress!.learnedAt != null)
                  _InfoRow(
                    icon: Icons.school,
                    label: 'Hoàn thành bài học',
                    value: _formatDateTime(motif.progress!.learnedAt!),
                  ),
                if (motif.progress!.masteredAt != null)
                  _InfoRow(
                    icon: Icons.emoji_events,
                    label: 'Thành thạo lúc',
                    value: _formatDateTime(motif.progress!.masteredAt!),
                  ),
                if (motif.progress!.quizBestScore != null)
                  _InfoRow(
                    icon: Icons.quiz,
                    label: 'Điểm cao nhất',
                    value: '${motif.progress!.quizBestScore}%',
                    valueColor: AppColors.success,
                  ),
              ],
            ),
            const SizedBox(height: 16),
          ],

          // Demo badge
          if (motif.isDemo)
            Container(
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: AppColors.info.withOpacity(0.1),
                borderRadius: BorderRadius.circular(12),
                border: Border.all(
                  color: AppColors.info.withOpacity(0.3),
                ),
              ),
              child: Row(
                children: [
                  Icon(
                    Icons.info_outline,
                    color: AppColors.info,
                    size: 20,
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: Text(
                      'Đây là họa tiết demo, có thể truy cập miễn phí.',
                      style: AppTypography.textTheme.bodySmall?.copyWith(
                        color: AppColors.info,
                      ),
                    ),
                  ),
                ],
              ),
            ),

          const SizedBox(height: 32),
        ],
      ),
    );
  }

  String _getCategoryName(String category) {
    switch (category.toLowerCase()) {
      case 'animal':
        return 'Động vật';
      case 'plant':
        return 'Thực vật';
      case 'celestial':
        return 'Thiên văn';
      case 'mythical':
        return 'Thần thoại';
      case 'landscape':
        return 'Phong cảnh';
      case 'symbol':
        return 'Biểu tượng';
      default:
        return category;
    }
  }

  String _getRarityName(String rarity) {
    switch (rarity.toLowerCase()) {
      case 'common':
        return 'Phổ thông';
      case 'uncommon':
        return 'Không phổ biến';
      case 'rare':
        return 'Hiếm';
      case 'epic':
        return 'Sử thi';
      case 'legendary':
        return 'Huyền thoại';
      default:
        return rarity;
    }
  }

  Color _getRarityColor(String rarity) {
    switch (rarity.toLowerCase()) {
      case 'common':
        return AppColors.rarityCommon;
      case 'uncommon':
        return AppColors.rarityUncommon;
      case 'rare':
        return AppColors.rarityRare;
      case 'epic':
        return AppColors.rarityEpic;
      case 'legendary':
        return AppColors.rarityLegendary;
      default:
        return AppColors.rarityCommon;
    }
  }

  String _getStatusName(String status) {
    switch (status.toLowerCase()) {
      case 'discovered':
        return 'Đã khám phá';
      case 'learned':
        return 'Đã học';
      case 'mastered':
        return 'Thành thạo';
      case 'hidden':
      default:
        return 'Chưa khám phá';
    }
  }

  Color _getStatusColor(String status) {
    switch (status.toLowerCase()) {
      case 'discovered':
        return AppColors.statusDiscovered;
      case 'learned':
        return AppColors.statusLearned;
      case 'mastered':
        return AppColors.statusMastered;
      case 'hidden':
      default:
        return AppColors.statusHidden;
    }
  }

  String _formatDateTime(String isoString) {
    try {
      final dateTime = DateTime.parse(isoString);
      return '${dateTime.day}/${dateTime.month}/${dateTime.year} ${dateTime.hour.toString().padLeft(2, '0')}:${dateTime.minute.toString().padLeft(2, '0')}';
    } catch (_) {
      return isoString;
    }
  }
}

/// Info card widget
class _InfoCard extends StatelessWidget {
  final String title;
  final List<Widget> children;

  const _InfoCard({
    required this.title,
    required this.children,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: AppColors.surface,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: AppColors.border),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            title,
            style: AppTypography.textTheme.titleSmall?.copyWith(
              color: AppColors.textSecondary,
              fontWeight: FontWeight.w600,
            ),
          ),
          const SizedBox(height: 12),
          ...children,
        ],
      ),
    );
  }
}

/// Info row widget
class _InfoRow extends StatelessWidget {
  final IconData icon;
  final String label;
  final String value;
  final Color? valueColor;
  final bool isCode;

  const _InfoRow({
    required this.icon,
    required this.label,
    required this.value,
    this.valueColor,
    this.isCode = false,
  });

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 6),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Icon(
            icon,
            size: 16,
            color: AppColors.textHint,
          ),
          const SizedBox(width: 10),
          Expanded(
            flex: 2,
            child: Text(
              label,
              style: AppTypography.textTheme.bodySmall?.copyWith(
                color: AppColors.textSecondary,
              ),
            ),
          ),
          const SizedBox(width: 8),
          Expanded(
            flex: 3,
            child: Text(
              value,
              style: isCode
                  ? TextStyle(
                      fontFamily: 'monospace',
                      fontSize: 12,
                      color: valueColor ?? AppColors.textPrimary,
                    )
                  : AppTypography.textTheme.bodySmall?.copyWith(
                      color: valueColor ?? AppColors.textPrimary,
                      fontWeight: FontWeight.w500,
                    ),
              textAlign: TextAlign.end,
            ),
          ),
        ],
      ),
    );
  }
}
