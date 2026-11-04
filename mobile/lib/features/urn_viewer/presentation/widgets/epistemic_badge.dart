import 'package:flutter/material.dart';

import '../../domain/entities/source_citation.dart';

/// Accessible badge displaying epistemic evidence certainty.
class EpistemicBadge extends StatelessWidget {
  final EpistemicCertainty certainty;
  final bool isCompact;
  final bool showDescription;

  const EpistemicBadge({
    super.key,
    required this.certainty,
    this.isCompact = false,
    this.showDescription = false,
  });

  @override
  Widget build(BuildContext context) {
    final config = _getBadgeConfig(certainty);

    final badgeWidget = Container(
      padding: EdgeInsets.symmetric(
        horizontal: isCompact ? 8 : 12,
        vertical: isCompact ? 4 : 6,
      ),
      decoration: BoxDecoration(
        color: config.backgroundColor,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: config.borderColor, width: 1),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(
            config.icon,
            size: isCompact ? 13 : 16,
            color: config.textColor,
          ),
          const SizedBox(width: 5),
          Text(
            certainty.labelVi,
            style: TextStyle(
              color: config.textColor,
              fontSize: isCompact ? 11 : 13,
              fontWeight: FontWeight.w600,
              letterSpacing: 0.2,
            ),
          ),
        ],
      ),
    );

    if (!showDescription) {
      return Semantics(
        label: 'Mức độ xác thực sử liệu: ${certainty.labelVi}',
        child: badgeWidget,
      );
    }

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      mainAxisSize: MainAxisSize.min,
      children: [
        Semantics(
          label: 'Mức độ xác thực sử liệu: ${certainty.labelVi}',
          child: badgeWidget,
        ),
        const SizedBox(height: 4),
        Text(
          config.description,
          style: TextStyle(
            fontSize: 11,
            color: Colors.grey[600],
            fontStyle: FontStyle.italic,
          ),
        ),
      ],
    );
  }

  _BadgeConfig _getBadgeConfig(EpistemicCertainty certainty) {
    switch (certainty) {
      case EpistemicCertainty.documented:
        return _BadgeConfig(
          icon: Icons.verified,
          textColor: const Color(0xFF1B5E20),
          backgroundColor: const Color(0xFFE8F5E9),
          borderColor: const Color(0xFFA5D6A7),
          description: 'Được chứng thực bằng nguồn thư tịch / sử liệu sơ cấp đã khảo đính.',
        );
      case EpistemicCertainty.traditional:
        return _BadgeConfig(
          icon: Icons.auto_stories,
          textColor: const Color(0xFF4A148C),
          backgroundColor: const Color(0xFFF3E5F5),
          borderColor: const Color(0xFFCE93D8),
          description: 'Ghi chép theo truyền thuyết dân gian, dã sử hoặc truyền khẩu văn hóa.',
        );
      case EpistemicCertainty.disputed:
        return _BadgeConfig(
          icon: Icons.warning_amber_rounded,
          textColor: const Color(0xFFB71C1C),
          backgroundColor: const Color(0xFFFFEBEE),
          borderColor: const Color(0xFFEF9A9A),
          description: 'Nội dung có tranh luận học thuật hoặc niên đại chưa đồng thuận.',
        );
      case EpistemicCertainty.uncertain:
      case EpistemicCertainty.unreviewed:
        return _BadgeConfig(
          icon: Icons.help_outline_rounded,
          textColor: const Color(0xFFE65100),
          backgroundColor: const Color(0xFFFFF3E0),
          borderColor: const Color(0xFFFFCC80),
          description: 'Tư liệu đang trong quá trình khảo cứu, đối chiếu văn bản học.',
        );
    }
  }
}

class _BadgeConfig {
  final IconData icon;
  final Color textColor;
  final Color backgroundColor;
  final Color borderColor;
  final String description;

  const _BadgeConfig({
    required this.icon,
    required this.textColor,
    required this.backgroundColor,
    required this.borderColor,
    required this.description,
  });
}
