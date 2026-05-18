import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../../core/theme/app_colors.dart';
import '../../../../core/theme/app_spacing.dart';
import '../../../../shared/widgets/glass/glass_container.dart';
import '../providers/notification_preferences_provider.dart';

class NotificationPreferencesWidget extends ConsumerWidget {
  const NotificationPreferencesWidget({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final prefs = ref.watch(notificationPreferencesProvider);

    return GlassContainer(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            'Cài đặt thông báo',
            style: TextStyle(
              color: Colors.white,
              fontSize: 18,
              fontWeight: FontWeight.bold,
            ),
          ),
          AppSpacing.verticalSpaceMD,
          
          _PreferenceItem(
            icon: Icons.local_fire_department,
            iconColor: const Color(0xFFFF6B35),
            title: 'Nhắc nhở chuỗi học',
            subtitle: 'Nhận nhắc nhở duy trì chuỗi học tập',
            value: prefs.streakReminders,
            onChanged: (value) {
              ref
                  .read(notificationPreferencesProvider.notifier)
                  .toggleStreakReminders(value);
            },
          ),
          
          _PreferenceItem(
            icon: Icons.flag,
            iconColor: const Color(0xFF60A5FA),
            title: 'Nhắc nhở mục tiêu hàng ngày',
            subtitle: 'Nhận nhắc nhở hoàn thành mục tiêu học tập',
            value: prefs.dailyGoalReminders,
            onChanged: (value) {
              ref
                  .read(notificationPreferencesProvider.notifier)
                  .toggleDailyGoalReminders(value);
            },
          ),
          
          _PreferenceItem(
            icon: Icons.emoji_events,
            iconColor: const Color(0xFFE8B44C),
            title: 'Thành tựu',
            subtitle: 'Nhận thông báo về thành tích mới',
            value: prefs.achievementNotifications,
            onChanged: (value) {
              ref
                  .read(notificationPreferencesProvider.notifier)
                  .toggleAchievementNotifications(value);
            },
          ),
          
          _PreferenceItem(
            icon: Icons.military_tech,
            iconColor: const Color(0xFFF59E0B),
            title: 'Huy hiệu',
            subtitle: 'Nhận thông báo khi đạt huy hiệu mới',
            value: prefs.badgeNotifications,
            onChanged: (value) {
              ref
                  .read(notificationPreferencesProvider.notifier)
                  .toggleBadgeNotifications(value);
            },
          ),
          
          _PreferenceItem(
            icon: Icons.arrow_upward,
            iconColor: const Color(0xFF8B5CF6),
            title: 'Lên cấp',
            subtitle: 'Nhận thông báo khi lên cấp độ mới',
            value: prefs.levelUpNotifications,
            onChanged: (value) {
              ref
                  .read(notificationPreferencesProvider.notifier)
                  .toggleLevelUpNotifications(value);
            },
          ),
          
          _PreferenceItem(
            icon: Icons.leaderboard,
            iconColor: const Color(0xFF9C27B0),
            title: 'Bảng xếp hạng',
            subtitle: 'Nhận cập nhật về vị trí xếp hạng',
            value: prefs.leaderboardUpdates,
            onChanged: (value) {
              ref
                  .read(notificationPreferencesProvider.notifier)
                  .toggleLeaderboardUpdates(value);
            },
          ),
          
          _PreferenceItem(
            icon: Icons.auto_awesome,
            iconColor: const Color(0xFF34D399),
            title: 'Nội dung mới',
            subtitle: 'Nhận thông báo khi có bài học mới',
            value: prefs.newContentNotifications,
            onChanged: (value) {
              ref
                  .read(notificationPreferencesProvider.notifier)
                  .toggleNewContentNotifications(value);
            },
          ),
          
          _PreferenceItem(
            icon: Icons.check_circle,
            iconColor: const Color(0xFF10B981),
            title: 'Nhiệm vụ',
            subtitle: 'Nhận thông báo về nhiệm vụ',
            value: prefs.questNotifications,
            onChanged: (value) {
              ref
                  .read(notificationPreferencesProvider.notifier)
                  .toggleQuestNotifications(value);
            },
          ),
          
          _PreferenceItem(
            icon: Icons.campaign,
            iconColor: const Color(0xFF6366F1),
            title: 'Thông báo hệ thống',
            subtitle: 'Nhận thông báo quan trọng từ hệ thống',
            value: prefs.systemAnnouncements,
            onChanged: (value) {
              ref
                  .read(notificationPreferencesProvider.notifier)
                  .toggleSystemAnnouncements(value);
            },
          ),
        ],
      ),
    );
  }
}

class _PreferenceItem extends StatelessWidget {
  final IconData icon;
  final Color iconColor;
  final String title;
  final String subtitle;
  final bool value;
  final ValueChanged<bool> onChanged;

  const _PreferenceItem({
    required this.icon,
    required this.iconColor,
    required this.title,
    required this.subtitle,
    required this.value,
    required this.onChanged,
  });

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: AppSpacing.md),
      child: Row(
        children: [
          Container(
            padding: const EdgeInsets.all(AppSpacing.sm),
            decoration: BoxDecoration(
              color: iconColor.withOpacity(0.2),
              borderRadius: BorderRadius.circular(AppSpacing.radiusSM),
            ),
            child: Icon(icon, color: iconColor, size: 20),
          ),
          AppSpacing.horizontalSpaceMD,
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  title,
                  style: const TextStyle(
                    color: Colors.white,
                    fontSize: 15,
                    fontWeight: FontWeight.w600,
                  ),
                ),
                Text(
                  subtitle,
                  style: TextStyle(
                    color: Colors.white.withOpacity(0.6),
                    fontSize: 13,
                  ),
                ),
              ],
            ),
          ),
          Switch(
            value: value,
            onChanged: onChanged,
            activeColor: AppColors.primary,
          ),
        ],
      ),
    );
  }
}

