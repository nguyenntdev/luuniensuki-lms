import 'package:flutter/material.dart';

import '../../../../core/theme/app_colors.dart';
import '../../../../core/theme/app_spacing.dart';

/// Prestige tier based on total XP
enum PrestigeTier {
  novice(0, 999, 'Tân Binh', 'Novice', Colors.grey),
  apprentice(1000, 4999, 'Học Việc', 'Apprentice', Colors.green),
  journeyman(5000, 14999, 'Thợ Lành', 'Journeyman', Colors.blue),
  expert(15000, 49999, 'Chuyên Gia', 'Expert', Colors.purple),
  master(50000, 99999, 'Cao Thủ', 'Master', Colors.orange),
  grandmaster(100000, 999999999, 'Đại Cao Thủ', 'Grandmaster', Colors.red);

  final int minXp;
  final int maxXp;
  final String nameVi;
  final String nameEn;
  final Color color;

  const PrestigeTier(
    this.minXp,
    this.maxXp,
    this.nameVi,
    this.nameEn,
    this.color,
  );

  /// Get tier from XP
  static PrestigeTier fromXp(int xp) {
    for (final tier in PrestigeTier.values.reversed) {
      if (xp >= tier.minXp) {
        return tier;
      }
    }
    return PrestigeTier.novice;
  }

  /// Get progress within current tier (0.0 to 1.0)
  double getProgress(int xp) {
    if (xp < minXp) return 0.0;
    if (xp > maxXp) return 1.0;
    final range = maxXp - minXp;
    final progress = xp - minXp;
    return progress / range;
  }

  /// Get XP needed to reach next tier
  int getXpToNext(int xp) {
    if (this == PrestigeTier.grandmaster) return 0;
    final nextTier = PrestigeTier.values[index + 1];
    return nextTier.minXp - xp;
  }

  /// Get next tier
  PrestigeTier? get next {
    if (this == PrestigeTier.grandmaster) return null;
    return PrestigeTier.values[index + 1];
  }
}

/// Prestige badge widget showing user tier
class PrestigeBadge extends StatelessWidget {
  final int totalXp;
  final bool showProgress;
  final double size;

  const PrestigeBadge({
    super.key,
    required this.totalXp,
    this.showProgress = true,
    this.size = 80,
  });

  @override
  Widget build(BuildContext context) {
    final tier = PrestigeTier.fromXp(totalXp);
    final progress = tier.getProgress(totalXp);
    final xpToNext = tier.getXpToNext(totalXp);

    return Column(
      mainAxisSize: MainAxisSize.min,
      children: [
        // Badge
        Container(
          width: size,
          height: size,
          decoration: BoxDecoration(
            shape: BoxShape.circle,
            gradient: LinearGradient(
              begin: Alignment.topLeft,
              end: Alignment.bottomRight,
              colors: [
                tier.color.withOpacity(0.8),
                tier.color.withOpacity(0.5),
              ],
            ),
            border: Border.all(
              color: tier.color,
              width: 3,
            ),
            boxShadow: [
              BoxShadow(
                color: tier.color.withOpacity(0.5),
                blurRadius: 15,
                spreadRadius: 2,
              ),
            ],
          ),
          child: Stack(
            children: [
              // Tier icon
              Center(
                child: Icon(
                  _getIconForTier(tier),
                  size: size * 0.5,
                  color: Colors.white,
                ),
              ),
              // Progress ring
              if (showProgress && tier != PrestigeTier.grandmaster)
                Positioned.fill(
                  child: CircularProgressIndicator(
                    value: progress,
                    strokeWidth: 3,
                    backgroundColor: Colors.white.withOpacity(0.3),
                    valueColor: AlwaysStoppedAnimation<Color>(Colors.white),
                  ),
                ),
            ],
          ),
        ),
        const SizedBox(height: AppSpacing.sm),
        // Tier name
        Text(
          tier.nameVi,
          style: TextStyle(
            color: Colors.white,
            fontSize: size * 0.15,
            fontWeight: FontWeight.bold,
          ),
        ),
        // XP to next tier
        if (showProgress && tier != PrestigeTier.grandmaster) ...[
          const SizedBox(height: 4),
          Text(
            'Còn $xpToNext XP',
            style: TextStyle(
              color: Colors.white70,
              fontSize: size * 0.12,
            ),
          ),
        ],
      ],
    );
  }

  IconData _getIconForTier(PrestigeTier tier) {
    switch (tier) {
      case PrestigeTier.novice:
        return Icons.shield_outlined;
      case PrestigeTier.apprentice:
        return Icons.shield;
      case PrestigeTier.journeyman:
        return Icons.workspace_premium;
      case PrestigeTier.expert:
        return Icons.military_tech;
      case PrestigeTier.master:
        return Icons.stars;
      case PrestigeTier.grandmaster:
        return Icons.diamond;
    }
  }
}

