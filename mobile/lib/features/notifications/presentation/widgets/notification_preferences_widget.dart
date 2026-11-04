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

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        // Master Push Notification Consent Card
        GlassContainer(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  Container(
                    padding: const EdgeInsets.all(AppSpacing.sm),
                    decoration: BoxDecoration(
                      color: AppColors.primary.withOpacity(0.2),
                      borderRadius: BorderRadius.circular(AppSpacing.radiusSM),
                    ),
                    child: const Icon(
                      Icons.notifications_active,
                      color: AppColors.primary,
                      size: 22,
                    ),
                  ),
                  AppSpacing.horizontalSpaceMD,
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        const Text(
                          'Bật thông báo đẩy',
                          style: TextStyle(
                            color: Colors.white,
                            fontSize: 16,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                        Text(
                          prefs.pushEnabled
                              ? 'Đã chấp thuận nhận thông báo đẩy'
                              : 'Đã từ chối - Dừng nhận mọi thông báo',
                          style: TextStyle(
                            color: prefs.pushEnabled
                                ? AppColors.success
                                : Colors.white.withOpacity(0.6),
                            fontSize: 13,
                          ),
                        ),
                      ],
                    ),
                  ),
                  Switch(
                    value: prefs.pushEnabled,
                    onChanged: (value) {
                      ref
                          .read(notificationPreferencesProvider.notifier)
                          .togglePushConsent(value);
                    },
                    activeColor: AppColors.primary,
                  ),
                ],
              ),
              AppSpacing.verticalSpaceSM,
              Container(
                padding: const EdgeInsets.all(AppSpacing.sm),
                decoration: BoxDecoration(
                  color: Colors.white.withOpacity(0.05),
                  borderRadius: BorderRadius.circular(AppSpacing.radiusSM),
                  border: Border.all(
                    color: Colors.white.withOpacity(0.1),
                  ),
                ),
                child: Row(
                  children: [
                    const Icon(
                      Icons.shield_outlined,
                      color: AppColors.secondary,
                      size: 16,
                    ),
                    AppSpacing.horizontalSpaceSM,
                    Expanded(
                      child: Text(
                        'Quyền riêng tư: Hệ thống cam kết không bao giờ gửi thông tin cá nhân (email, SĐT, tên thật) của học sinh qua thông báo đẩy.',
                        style: TextStyle(
                          color: Colors.white.withOpacity(0.7),
                          fontSize: 11,
                          height: 1.3,
                        ),
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ),
        ),
        AppSpacing.verticalSpaceMD,

        // Notification Categories
        GlassContainer(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Text(
                'Tùy chỉnh danh mục thông báo',
                style: TextStyle(
                  color: Colors.white,
                  fontSize: 18,
                  fontWeight: FontWeight.bold,
                ),
              ),
              AppSpacing.verticalSpaceMD,

              // Teacher / Classroom Alerts
              _PreferenceItem(
                icon: Icons.school,
                iconColor: const Color(0xFF3B82F6),
                title: 'Thông báo lớp học & Bài nộp',
                subtitle: 'Nhận thông báo khi có bài nộp mới (Dành cho Giáo viên)',
                value: prefs.pushEnabled && prefs.teacherAlerts,
                onChanged: prefs.pushEnabled
                    ? (value) {
                        ref
                            .read(notificationPreferencesProvider.notifier)
                            .toggleTeacherAlerts(value);
                      }
                    : (_) {},
              ),

              // Partner / Booking Alerts
              _PreferenceItem(
                icon: Icons.storefront,
                iconColor: const Color(0xFF10B981),
                title: 'Thông báo đặt chỗ & Trải nghiệm',
                subtitle: 'Nhận thông báo khi có khách gửi yêu cầu (Đối tác nghệ nhân)',
                value: prefs.pushEnabled && prefs.partnerAlerts,
                onChanged: prefs.pushEnabled
                    ? (value) {
                        ref
                            .read(notificationPreferencesProvider.notifier)
                            .togglePartnerAlerts(value);
                      }
                    : (_) {},
              ),

              _PreferenceItem(
                icon: Icons.local_fire_department,
                iconColor: const Color(0xFFFF6B35),
                title: 'Nhắc nhở chuỗi học',
                subtitle: 'Nhận nhắc nhở duy trì chuỗi học tập',
                value: prefs.pushEnabled && prefs.streakReminders,
                onChanged: prefs.pushEnabled
                    ? (value) {
                        ref
                            .read(notificationPreferencesProvider.notifier)
                            .toggleStreakReminders(value);
                      }
                    : (_) {},
              ),

              _PreferenceItem(
                icon: Icons.flag,
                iconColor: const Color(0xFF60A5FA),
                title: 'Nhắc nhở mục tiêu hàng ngày',
                subtitle: 'Nhận nhắc nhở hoàn thành mục tiêu học tập',
                value: prefs.pushEnabled && prefs.dailyGoalReminders,
                onChanged: prefs.pushEnabled
                    ? (value) {
                        ref
                            .read(notificationPreferencesProvider.notifier)
                            .toggleDailyGoalReminders(value);
                      }
                    : (_) {},
              ),

              _PreferenceItem(
                icon: Icons.emoji_events,
                iconColor: const Color(0xFFE8B44C),
                title: 'Thành tựu',
                subtitle: 'Nhận thông báo về thành tích mới',
                value: prefs.pushEnabled && prefs.achievementNotifications,
                onChanged: prefs.pushEnabled
                    ? (value) {
                        ref
                            .read(notificationPreferencesProvider.notifier)
                            .toggleAchievementNotifications(value);
                      }
                    : (_) {},
              ),

              _PreferenceItem(
                icon: Icons.military_tech,
                iconColor: const Color(0xFFF59E0B),
                title: 'Huy hiệu',
                subtitle: 'Nhận thông báo khi đạt huy hiệu mới',
                value: prefs.pushEnabled && prefs.badgeNotifications,
                onChanged: prefs.pushEnabled
                    ? (value) {
                        ref
                            .read(notificationPreferencesProvider.notifier)
                            .toggleBadgeNotifications(value);
                      }
                    : (_) {},
              ),

              _PreferenceItem(
                icon: Icons.arrow_upward,
                iconColor: const Color(0xFF8B5CF6),
                title: 'Lên cấp',
                subtitle: 'Nhận thông báo khi lên cấp độ mới',
                value: prefs.pushEnabled && prefs.levelUpNotifications,
                onChanged: prefs.pushEnabled
                    ? (value) {
                        ref
                            .read(notificationPreferencesProvider.notifier)
                            .toggleLevelUpNotifications(value);
                      }
                    : (_) {},
              ),

              _PreferenceItem(
                icon: Icons.leaderboard,
                iconColor: const Color(0xFF9C27B0),
                title: 'Bảng xếp hạng',
                subtitle: 'Nhận cập nhật về vị trí xếp hạng',
                value: prefs.pushEnabled && prefs.leaderboardUpdates,
                onChanged: prefs.pushEnabled
                    ? (value) {
                        ref
                            .read(notificationPreferencesProvider.notifier)
                            .toggleLeaderboardUpdates(value);
                      }
                    : (_) {},
              ),

              _PreferenceItem(
                icon: Icons.auto_awesome,
                iconColor: const Color(0xFF34D399),
                title: 'Nội dung mới',
                subtitle: 'Nhận thông báo khi có bài học mới',
                value: prefs.pushEnabled && prefs.newContentNotifications,
                onChanged: prefs.pushEnabled
                    ? (value) {
                        ref
                            .read(notificationPreferencesProvider.notifier)
                            .toggleNewContentNotifications(value);
                      }
                    : (_) {},
              ),

              _PreferenceItem(
                icon: Icons.check_circle,
                iconColor: const Color(0xFF10B981),
                title: 'Nhiệm vụ',
                subtitle: 'Nhận thông báo về nhiệm vụ',
                value: prefs.pushEnabled && prefs.questNotifications,
                onChanged: prefs.pushEnabled
                    ? (value) {
                        ref
                            .read(notificationPreferencesProvider.notifier)
                            .toggleQuestNotifications(value);
                      }
                    : (_) {},
              ),

              _PreferenceItem(
                icon: Icons.campaign,
                iconColor: const Color(0xFF6366F1),
                title: 'Thông báo hệ thống',
                subtitle: 'Nhận thông báo quan trọng từ hệ thống',
                value: prefs.pushEnabled && prefs.systemAnnouncements,
                onChanged: prefs.pushEnabled
                    ? (value) {
                        ref
                            .read(notificationPreferencesProvider.notifier)
                            .toggleSystemAnnouncements(value);
                      }
                    : (_) {},
              ),
            ],
          ),
        ),
      ],
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

