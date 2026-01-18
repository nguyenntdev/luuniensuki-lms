import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import '../../../../core/theme/app_colors.dart';
import '../../../../shared/widgets/glass/glass_container.dart';
import '../../data/models/badge_dto.dart';

/// Bottom sheet widget for displaying badge details
class BadgeDetailSheet extends StatelessWidget {
  final BadgeDto badge;

  const BadgeDetailSheet({
    super.key,
    required this.badge,
  });

  static void show(BuildContext context, BadgeDto badge) {
    showModalBottomSheet(
      context: context,
      backgroundColor: Colors.transparent,
      isScrollControlled: true,
      builder: (context) => BadgeDetailSheet(badge: badge),
    );
  }

  @override
  Widget build(BuildContext context) {
    final isEarned = badge.earnedAt != null;
    final earnedDate = badge.earnedAt != null
        ? DateFormat('dd/MM/yyyy').format(DateTime.parse(badge.earnedAt!))
        : null;

    return Container(
      decoration: BoxDecoration(
        gradient: LinearGradient(
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
          colors: [
            AppColors.background.withOpacity(0.95),
            AppColors.surface.withOpacity(0.95),
          ],
        ),
        borderRadius: const BorderRadius.vertical(top: Radius.circular(24)),
      ),
      child: SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              // Handle bar
              Container(
                width: 40,
                height: 4,
                margin: const EdgeInsets.only(bottom: 24),
                decoration: BoxDecoration(
                  color: Colors.white.withOpacity(0.3),
                  borderRadius: BorderRadius.circular(2),
                ),
              ),

              // Badge icon
              Container(
                width: 120,
                height: 120,
                decoration: BoxDecoration(
                  shape: BoxShape.circle,
                  gradient: isEarned
                      ? const LinearGradient(
                          colors: [AppColors.primaryDark, AppColors.primaryLight],
                        )
                      : null,
                  color: isEarned ? null : Colors.white.withOpacity(0.1),
                  boxShadow: isEarned
                      ? [
                          BoxShadow(
                            color: AppColors.primary.withOpacity(0.4),
                            blurRadius: 24,
                            spreadRadius: 4,
                          ),
                        ]
                      : null,
                ),
                child: Icon(
                  _getCategoryIcon(badge.category),
                  color: isEarned
                      ? AppColors.onPrimary
                      : Colors.white.withOpacity(0.3),
                  size: 60,
                ),
              ),

              const SizedBox(height: 24),

              // Badge name
              Text(
                badge.name,
                style: TextStyle(
                  color: isEarned ? Colors.white : Colors.white.withOpacity(0.7),
                  fontSize: 24,
                  fontWeight: FontWeight.bold,
                ),
                textAlign: TextAlign.center,
              ),

              const SizedBox(height: 8),

              // Category badge
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                decoration: BoxDecoration(
                  color: AppColors.primary.withOpacity(0.2),
                  borderRadius: BorderRadius.circular(16),
                ),
                child: Text(
                  _getCategoryName(badge.category),
                  style: const TextStyle(
                    color: AppColors.primary,
                    fontSize: 12,
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ),

              const SizedBox(height: 24),

              // Description
              if (badge.description != null)
                GlassContainer(
                  padding: const EdgeInsets.all(16),
                  opacity: 0.08,
                  child: Text(
                    badge.description!,
                    style: TextStyle(
                      color: Colors.white.withOpacity(0.9),
                      fontSize: 14,
                      height: 1.5,
                    ),
                    textAlign: TextAlign.center,
                  ),
                ),

              const SizedBox(height: 16),

              // XP Bonus and Status
              Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  // XP Bonus
                  GlassContainer(
                    padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                    opacity: 0.08,
                    child: Row(
                      children: [
                        const Icon(
                          Icons.star,
                          color: AppColors.xpGold,
                          size: 20,
                        ),
                        const SizedBox(width: 8),
                        Text(
                          '+${badge.xpBonus} XP',
                          style: const TextStyle(
                            color: Colors.white,
                            fontSize: 16,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                      ],
                    ),
                  ),

                  const SizedBox(width: 12),

                  // Status
                  GlassContainer(
                    padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                    opacity: isEarned ? 0.12 : 0.08,
                    border: Border.all(
                      color: isEarned
                          ? AppColors.success.withOpacity(0.5)
                          : Colors.white.withOpacity(0.1),
                    ),
                    child: Row(
                      children: [
                        Icon(
                          isEarned ? Icons.check_circle : Icons.lock,
                          color: isEarned ? AppColors.success : Colors.white.withOpacity(0.5),
                          size: 20,
                        ),
                        const SizedBox(width: 8),
                        Text(
                          isEarned ? 'Đã nhận' : 'Chưa đạt',
                          style: TextStyle(
                            color: isEarned ? AppColors.success : Colors.white.withOpacity(0.7),
                            fontSize: 16,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                      ],
                    ),
                  ),
                ],
              ),

              // Earned date
              if (earnedDate != null) ...[
                const SizedBox(height: 16),
                Text(
                  'Đạt được vào $earnedDate',
                  style: TextStyle(
                    color: Colors.white.withOpacity(0.6),
                    fontSize: 12,
                  ),
                ),
              ],

              const SizedBox(height: 8),
            ],
          ),
        ),
      ),
    );
  }

  IconData _getCategoryIcon(String category) {
    switch (category.toLowerCase()) {
      case 'discovery':
        return Icons.visibility;
      case 'learning':
        return Icons.school;
      case 'mastery':
        return Icons.star;
      case 'streak':
        return Icons.local_fire_department;
      case 'collection':
        return Icons.collections;
      case 'achievement':
        return Icons.workspace_premium;
      default:
        return Icons.military_tech;
    }
  }

  String _getCategoryName(String category) {
    switch (category.toLowerCase()) {
      case 'discovery':
        return 'Khám Phá';
      case 'learning':
        return 'Học Tập';
      case 'mastery':
        return 'Thành Thạo';
      case 'streak':
        return 'Chuỗi Ngày';
      case 'collection':
        return 'Sưu Tập';
      case 'achievement':
        return 'Thành Tích';
      default:
        return category;
    }
  }
}

