import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:url_launcher/url_launcher.dart';

import '../../../../core/theme/app_colors.dart';
import '../../../../core/theme/app_spacing.dart';
import '../../../../shared/widgets/glass/animated_background.dart';
import '../../../../shared/widgets/glass/glass_container.dart';
import '../providers/settings_provider.dart';

/// Settings screen for app configuration and preferences
class SettingsScreen extends ConsumerWidget {
  const SettingsScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final settings = ref.watch(settingsNotifierProvider);

    return AnimatedGradientBackground(
      child: Scaffold(
        backgroundColor: Colors.transparent,
        appBar: AppBar(
          backgroundColor: Colors.transparent,
          elevation: 0,
          leading: IconButton(
            icon: const Icon(Icons.arrow_back, color: Colors.white),
            onPressed: () => context.pop(),
          ),
          title: const Text(
            'Cài đặt',
            style: TextStyle(
              color: Colors.white,
              fontSize: 20,
              fontWeight: FontWeight.bold,
            ),
          ),
        ),
        body: SafeArea(
          child: ListView(
            padding: const EdgeInsets.all(AppSpacing.md),
            children: [
              // Learning Goals Section
              _SectionHeader(title: 'Mục tiêu học tập'),
              AppSpacing.verticalSpaceSM,
              _buildLearningGoalsSection(context),

              AppSpacing.verticalSpaceLG,

              // Notifications Section
              _SectionHeader(title: 'Thông báo'),
              AppSpacing.verticalSpaceSM,
              _buildNotificationSettings(context, ref, settings),

              AppSpacing.verticalSpaceLG,

              // Sound & Effects Section
              _SectionHeader(title: 'Âm thanh & Hiệu ứng'),
              AppSpacing.verticalSpaceSM,
              _buildSoundSettings(context, ref, settings),

              AppSpacing.verticalSpaceLG,

              // Language Section
              _SectionHeader(title: 'Ngôn ngữ'),
              AppSpacing.verticalSpaceSM,
              _buildLanguageSettings(context, ref, settings),

              AppSpacing.verticalSpaceLG,

              // Storage Section
              _SectionHeader(title: 'Lưu trữ'),
              AppSpacing.verticalSpaceSM,
              _buildStorageSettings(context, ref),

              AppSpacing.verticalSpaceLG,

              // About Section
              _SectionHeader(title: 'Về ứng dụng'),
              AppSpacing.verticalSpaceSM,
              _buildAboutSection(context),

              AppSpacing.verticalSpaceLG,

              // Legal Section
              _SectionHeader(title: 'Pháp lý'),
              AppSpacing.verticalSpaceSM,
              _buildLegalSection(context),

              const SizedBox(height: 120), // Bottom padding
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildLearningGoalsSection(BuildContext context) {
    return GlassContainer(
      padding: const EdgeInsets.all(AppSpacing.md),
      child: _buildActionTile(
        icon: Icons.flag_outlined,
        title: 'Mục tiêu hàng ngày',
        subtitle: 'Đặt mục tiêu XP cho mỗi ngày',
        color: AppColors.primary,
        onTap: () => context.push('/daily-goal'),
      ),
    );
  }

  Widget _buildNotificationSettings(
      BuildContext context, WidgetRef ref, SettingsState settings) {
    return GlassContainer(
      padding: const EdgeInsets.all(AppSpacing.md),
      child: Column(
        children: [
          _buildSwitchTile(
            icon: Icons.notifications_active_outlined,
            title: 'Nhận thông báo',
            subtitle: 'Nhận nhắc nhở học tập hàng ngày',
            value: settings.notificationsEnabled,
            onChanged: (value) {
              ref
                  .read(settingsNotifierProvider.notifier)
                  .setNotifications(value);
            },
            color: AppColors.warning,
          ),
        ],
      ),
    );
  }

  Widget _buildSoundSettings(
      BuildContext context, WidgetRef ref, SettingsState settings) {
    return GlassContainer(
      padding: const EdgeInsets.all(AppSpacing.md),
      child: Column(
        children: [
          _buildSwitchTile(
            icon: Icons.volume_up_outlined,
            title: 'Hiệu ứng âm thanh',
            subtitle: 'Bật/tắt âm thanh trong ứng dụng',
            value: settings.soundEffectsEnabled,
            onChanged: (value) {
              ref
                  .read(settingsNotifierProvider.notifier)
                  .setSoundEffects(value);
            },
            color: AppColors.info,
          ),
        ],
      ),
    );
  }

  Widget _buildLanguageSettings(
      BuildContext context, WidgetRef ref, SettingsState settings) {
    return GlassContainer(
      padding: const EdgeInsets.all(AppSpacing.md),
      child: Column(
        children: [
          _buildLanguageTile(
            icon: Icons.language_outlined,
            title: 'Ngôn ngữ',
            currentLanguage: settings.language,
            onTap: () => _showLanguageDialog(context, ref, settings),
            color: AppColors.success,
          ),
        ],
      ),
    );
  }

  Widget _buildStorageSettings(BuildContext context, WidgetRef ref) {
    return GlassContainer(
      padding: const EdgeInsets.all(AppSpacing.md),
      child: _buildActionTile(
        icon: Icons.cleaning_services_outlined,
        title: 'Xóa bộ nhớ cache',
        subtitle: 'Giải phóng dung lượng lưu trữ',
        color: AppColors.warning,
        onTap: () => _showClearCacheDialog(context, ref),
      ),
    );
  }

  Widget _buildAboutSection(BuildContext context) {
    return GlassContainer(
      padding: const EdgeInsets.all(AppSpacing.md),
      child: Column(
        children: [
          _buildInfoTile(
            icon: Icons.info_outline,
            title: 'Phiên bản',
            subtitle: '1.4.0 (Build 5)',
            color: AppColors.info,
          ),
          Padding(
            padding: const EdgeInsets.symmetric(vertical: AppSpacing.sm),
            child: Divider(
              color: Colors.white.withOpacity(0.1),
              height: 1,
            ),
          ),
          _buildInfoTile(
            icon: Icons.copyright_outlined,
            title: 'Lưu Niên Sử Kí',
            subtitle: '© 2024 - Học tập văn hóa Việt',
            color: AppColors.primary,
          ),
        ],
      ),
    );
  }

  Widget _buildLegalSection(BuildContext context) {
    return GlassContainer(
      padding: const EdgeInsets.all(AppSpacing.md),
      child: Column(
        children: [
          _buildActionTile(
            icon: Icons.privacy_tip_outlined,
            title: 'Chính sách bảo mật',
            subtitle: 'Xem chính sách bảo mật của chúng tôi',
            color: AppColors.textSecondary,
            onTap: () => _launchUrl('https://luuniensuki.com/privacy-policy'),
          ),
          Padding(
            padding: const EdgeInsets.symmetric(vertical: AppSpacing.sm),
            child: Divider(
              color: Colors.white.withOpacity(0.1),
              height: 1,
            ),
          ),
          _buildActionTile(
            icon: Icons.description_outlined,
            title: 'Điều khoản sử dụng',
            subtitle: 'Xem điều khoản và điều kiện',
            color: AppColors.textSecondary,
            onTap: () => _launchUrl('https://luuniensuki.com/terms-of-service'),
          ),
        ],
      ),
    );
  }

  // Helper widget builders
  Widget _buildSwitchTile({
    required IconData icon,
    required String title,
    required String subtitle,
    required bool value,
    required ValueChanged<bool> onChanged,
    required Color color,
  }) {
    return Row(
      children: [
        Container(
          width: 48,
          height: 48,
          decoration: BoxDecoration(
            gradient: LinearGradient(
              colors: [
                color.withOpacity(0.3),
                color.withOpacity(0.1),
              ],
            ),
            borderRadius: BorderRadius.circular(AppSpacing.radiusMD),
            border: Border.all(
              color: color.withOpacity(0.3),
            ),
          ),
          child: Icon(
            icon,
            color: color,
            size: 24,
          ),
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
                  fontSize: 16,
                  fontWeight: FontWeight.w600,
                ),
              ),
              AppSpacing.verticalSpaceXS,
              Text(
                subtitle,
                style: TextStyle(
                  color: Colors.white.withOpacity(0.6),
                  fontSize: 12,
                ),
              ),
            ],
          ),
        ),
        Switch(
          value: value,
          onChanged: onChanged,
          activeColor: AppColors.primary,
          activeTrackColor: AppColors.primary.withOpacity(0.5),
        ),
      ],
    );
  }


  Widget _buildLanguageTile({
    required IconData icon,
    required String title,
    required String currentLanguage,
    required VoidCallback onTap,
    required Color color,
  }) {
    final languageDisplay = currentLanguage == 'vi' ? 'Tiếng Việt' : 'English';

    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(AppSpacing.radiusMD),
      child: Row(
        children: [
          Container(
            width: 48,
            height: 48,
            decoration: BoxDecoration(
              gradient: LinearGradient(
                colors: [
                  color.withOpacity(0.3),
                  color.withOpacity(0.1),
                ],
              ),
              borderRadius: BorderRadius.circular(AppSpacing.radiusMD),
              border: Border.all(
                color: color.withOpacity(0.3),
              ),
            ),
            child: Icon(
              icon,
              color: color,
              size: 24,
            ),
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
                    fontSize: 16,
                    fontWeight: FontWeight.w600,
                  ),
                ),
                AppSpacing.verticalSpaceXS,
                Text(
                  languageDisplay,
                  style: TextStyle(
                    color: Colors.white.withOpacity(0.6),
                    fontSize: 12,
                  ),
                ),
              ],
            ),
          ),
          Icon(
            Icons.chevron_right,
            color: Colors.white.withOpacity(0.3),
            size: 24,
          ),
        ],
      ),
    );
  }

  Widget _buildActionTile({
    required IconData icon,
    required String title,
    required String subtitle,
    required Color color,
    required VoidCallback onTap,
  }) {
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(AppSpacing.radiusMD),
      child: Row(
        children: [
          Container(
            width: 48,
            height: 48,
            decoration: BoxDecoration(
              gradient: LinearGradient(
                colors: [
                  color.withOpacity(0.3),
                  color.withOpacity(0.1),
                ],
              ),
              borderRadius: BorderRadius.circular(AppSpacing.radiusMD),
              border: Border.all(
                color: color.withOpacity(0.3),
              ),
            ),
            child: Icon(
              icon,
              color: color,
              size: 24,
            ),
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
                    fontSize: 16,
                    fontWeight: FontWeight.w600,
                  ),
                ),
                AppSpacing.verticalSpaceXS,
                Text(
                  subtitle,
                  style: TextStyle(
                    color: Colors.white.withOpacity(0.6),
                    fontSize: 12,
                  ),
                ),
              ],
            ),
          ),
          Icon(
            Icons.chevron_right,
            color: Colors.white.withOpacity(0.3),
            size: 24,
          ),
        ],
      ),
    );
  }

  Widget _buildInfoTile({
    required IconData icon,
    required String title,
    required String subtitle,
    required Color color,
  }) {
    return Row(
      children: [
        Container(
          width: 48,
          height: 48,
          decoration: BoxDecoration(
            gradient: LinearGradient(
              colors: [
                color.withOpacity(0.3),
                color.withOpacity(0.1),
              ],
            ),
            borderRadius: BorderRadius.circular(AppSpacing.radiusMD),
            border: Border.all(
              color: color.withOpacity(0.3),
            ),
          ),
          child: Icon(
            icon,
            color: color,
            size: 24,
          ),
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
                  fontSize: 16,
                  fontWeight: FontWeight.w600,
                ),
              ),
              AppSpacing.verticalSpaceXS,
              Text(
                subtitle,
                style: TextStyle(
                  color: Colors.white.withOpacity(0.6),
                  fontSize: 12,
                ),
              ),
            ],
          ),
        ),
      ],
    );
  }

  // Dialog methods
  void _showLanguageDialog(
      BuildContext context, WidgetRef ref, SettingsState settings) {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        backgroundColor: AppColors.surface,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(AppSpacing.radiusLG),
          side: BorderSide(color: Colors.white.withOpacity(0.15)),
        ),
        title: Row(
          children: [
            Container(
              padding: const EdgeInsets.all(AppSpacing.sm),
              decoration: BoxDecoration(
                gradient: LinearGradient(
                  colors: [
                    AppColors.success.withOpacity(0.3),
                    AppColors.success.withOpacity(0.1),
                  ],
                ),
                borderRadius: BorderRadius.circular(AppSpacing.radiusSM),
              ),
              child: Icon(
                Icons.language,
                color: AppColors.success,
                size: 20,
              ),
            ),
            AppSpacing.horizontalSpaceSM,
            const Text(
              'Chọn ngôn ngữ',
              style: TextStyle(
                color: Colors.white,
                fontWeight: FontWeight.bold,
              ),
            ),
          ],
        ),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            _buildLanguageOption(
              context: context,
              ref: ref,
              language: 'vi',
              title: 'Tiếng Việt',
              isSelected: settings.language == 'vi',
            ),
            AppSpacing.verticalSpaceSM,
            _buildLanguageOption(
              context: context,
              ref: ref,
              language: 'en',
              title: 'English',
              isSelected: settings.language == 'en',
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildLanguageOption({
    required BuildContext context,
    required WidgetRef ref,
    required String language,
    required String title,
    required bool isSelected,
  }) {
    return InkWell(
      onTap: () {
        ref.read(settingsNotifierProvider.notifier).setLanguage(language);
        Navigator.pop(context);
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Ngôn ngữ đã được chuyển sang $title'),
            backgroundColor: AppColors.success,
            behavior: SnackBarBehavior.floating,
            margin: const EdgeInsets.all(AppSpacing.md),
          ),
        );
      },
      borderRadius: BorderRadius.circular(AppSpacing.radiusMD),
      child: Container(
        padding: const EdgeInsets.all(AppSpacing.md),
        decoration: BoxDecoration(
          color: isSelected
              ? AppColors.success.withOpacity(0.2)
              : Colors.transparent,
          borderRadius: BorderRadius.circular(AppSpacing.radiusMD),
          border: Border.all(
            color: isSelected
                ? AppColors.success
                : Colors.white.withOpacity(0.2),
            width: isSelected ? 2 : 1,
          ),
        ),
        child: Row(
          children: [
            Expanded(
              child: Text(
                title,
                style: TextStyle(
                  color: isSelected ? AppColors.success : Colors.white,
                  fontSize: 16,
                  fontWeight: isSelected ? FontWeight.bold : FontWeight.normal,
                ),
              ),
            ),
            if (isSelected)
              Icon(
                Icons.check_circle,
                color: AppColors.success,
                size: 24,
              ),
          ],
        ),
      ),
    );
  }

  void _showClearCacheDialog(BuildContext context, WidgetRef ref) {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        backgroundColor: AppColors.surface,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(AppSpacing.radiusLG),
          side: BorderSide(color: Colors.white.withOpacity(0.15)),
        ),
        title: Row(
          children: [
            Container(
              padding: const EdgeInsets.all(AppSpacing.sm),
              decoration: BoxDecoration(
                gradient: LinearGradient(
                  colors: [
                    AppColors.warning.withOpacity(0.3),
                    AppColors.warning.withOpacity(0.1),
                  ],
                ),
                borderRadius: BorderRadius.circular(AppSpacing.radiusSM),
              ),
              child: Icon(
                Icons.cleaning_services,
                color: AppColors.warning,
                size: 20,
              ),
            ),
            AppSpacing.horizontalSpaceSM,
            const Text(
              'Xóa bộ nhớ cache',
              style: TextStyle(
                color: Colors.white,
                fontWeight: FontWeight.bold,
              ),
            ),
          ],
        ),
        content: Text(
          'Bạn có chắc chắn muốn xóa bộ nhớ cache? Điều này sẽ giải phóng dung lượng lưu trữ nhưng có thể làm chậm ứng dụng lần đầu sử dụng.',
          style: TextStyle(
            color: Colors.white.withOpacity(0.8),
            fontSize: 15,
          ),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            style: TextButton.styleFrom(
              padding: const EdgeInsets.symmetric(
                horizontal: AppSpacing.lg,
                vertical: AppSpacing.sm,
              ),
            ),
            child: Text(
              'Hủy',
              style: TextStyle(
                color: Colors.white.withOpacity(0.7),
                fontWeight: FontWeight.w600,
              ),
            ),
          ),
          ElevatedButton(
            onPressed: () async {
              Navigator.pop(context);
              await ref.read(settingsNotifierProvider.notifier).clearCache();
              if (context.mounted) {
                ScaffoldMessenger.of(context).showSnackBar(
                  const SnackBar(
                    content: Text('Đã xóa bộ nhớ cache thành công'),
                    backgroundColor: AppColors.success,
                    behavior: SnackBarBehavior.floating,
                    margin: EdgeInsets.all(AppSpacing.md),
                  ),
                );
              }
            },
            style: ElevatedButton.styleFrom(
              backgroundColor: AppColors.warning,
              foregroundColor: AppColors.onPrimary,
              padding: const EdgeInsets.symmetric(
                horizontal: AppSpacing.lg,
                vertical: AppSpacing.sm,
              ),
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(AppSpacing.radiusSM),
              ),
            ),
            child: const Text(
              'Xóa',
              style: TextStyle(fontWeight: FontWeight.w600),
            ),
          ),
        ],
      ),
    );
  }

  Future<void> _launchUrl(String urlString) async {
    final uri = Uri.parse(urlString);
    if (await canLaunchUrl(uri)) {
      await launchUrl(uri, mode: LaunchMode.externalApplication);
    }
  }
}

// Section header widget
class _SectionHeader extends StatelessWidget {
  final String title;

  const _SectionHeader({required this.title});

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(left: AppSpacing.xs),
      child: Text(
        title,
        style: TextStyle(
          color: Colors.white.withOpacity(0.9),
          fontSize: 18,
          fontWeight: FontWeight.bold,
          letterSpacing: 0.5,
        ),
      ),
    );
  }
}

