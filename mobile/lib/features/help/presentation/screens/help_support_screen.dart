import 'package:flutter/material.dart';
import 'package:url_launcher/url_launcher.dart';

import '../../../../core/theme/app_colors.dart';
import '../../../../core/theme/app_spacing.dart';
import '../../../../shared/widgets/glass/animated_background.dart';
import '../../../../shared/widgets/glass/glass_container.dart';
import '../../../../shared/widgets/glass/liquid_glass_app_bar.dart';

class HelpSupportScreen extends StatefulWidget {
  const HelpSupportScreen({super.key});

  @override
  State<HelpSupportScreen> createState() => _HelpSupportScreenState();
}

class _HelpSupportScreenState extends State<HelpSupportScreen> {
  int? _expandedIndex;

  final List<FAQItem> _faqs = [
    FAQItem(
      question: 'Làm thế nào để khám phá mô hình 3D?',
      answer: 'Để khám phá mô hình 3D, bạn chỉ cần chạm và vuốt trên màn hình. '
          'Sử dụng một ngón tay để xoay mô hình, hai ngón tay để phóng to/thu nhỏ, '
          'và vuốt để di chuyển vị trí. Bạn cũng có thể nhấn nút AR để xem mô hình '
          'trong thế giới thực qua camera của bạn.',
    ),
    FAQItem(
      question: 'Điểm XP được tính như thế nào?',
      answer:
          'Điểm XP (Experience Points) được tính dựa trên các hoạt động học tập của bạn:\n\n'
          '• Hoàn thành bài học: +10 XP\n'
          '• Hoàn thành bài quiz: +15 XP\n'
          '• Đạt 100% quiz: +25 XP\n'
          '• Khám phá mô hình 3D: +5 XP\n'
          '• Học liên tục mỗi ngày: +20 XP\n\n'
          'Càng học nhiều, bạn càng kiếm được nhiều XP để thăng hạng!',
    ),
    FAQItem(
      question: 'Làm sao để đạt hạng cao hơn?',
      answer:
          'Để thăng hạng, bạn cần tích lũy đủ điểm XP. Các hạng bao gồm:\n\n'
          '• Beginner: 0-99 XP\n'
          '• Novice: 100-299 XP\n'
          '• Intermediate: 300-599 XP\n'
          '• Advanced: 600-999 XP\n'
          '• Expert: 1000-1999 XP\n'
          '• Master: 2000+ XP\n\n'
          'Hãy học đều đặn và hoàn thành các bài quiz để nhanh chóng thăng hạng!',
    ),
    FAQItem(
      question: 'Tôi có thể học offline không?',
      answer: 'Hiện tại, ứng dụng cần kết nối internet để:\n\n'
          '• Tải nội dung bài học mới\n'
          '• Hiển thị mô hình 3D\n'
          '• Đồng bộ tiến độ học tập\n'
          '• Cập nhật điểm XP và hạng\n\n'
          'Chúng tôi đang phát triển tính năng học offline và sẽ cập nhật '
          'trong các phiên bản tiếp theo.',
    ),
    FAQItem(
      question: 'Làm thế nào để theo dõi tiến độ học tập?',
      answer: 'Bạn có thể theo dõi tiến độ học tập của mình qua:\n\n'
          '• Tab Profile: Xem tổng quan XP, hạng, và streak\n'
          '• Tab Progress: Xem chi tiết từng bài học đã hoàn thành\n'
          '• Biểu đồ tiến độ: Theo dõi xu hướng học tập theo tuần\n\n'
          'Hệ thống sẽ tự động đồng bộ tiến độ của bạn.',
    ),
  ];

  Future<void> _launchEmail() async {
    final emailUri = Uri(
      scheme: 'mailto',
      path: 'support@eduquest.vn',
      query: 'subject=Hỗ trợ EduQuest AR',
    );

    if (await canLaunchUrl(emailUri)) {
      await launchUrl(emailUri);
      return;
    }

    _showSnack('Không thể mở ứng dụng email');
  }

  Future<void> _launchURL(String url) async {
    final uri = Uri.parse(url);
    if (await canLaunchUrl(uri)) {
      await launchUrl(uri, mode: LaunchMode.externalApplication);
      return;
    }

    _showSnack('Không thể mở liên kết');
  }

  void _showSnack(String message) {
    if (!mounted) return;
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(message),
        backgroundColor: AppColors.error,
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: GradientBackground(
        child: SafeArea(
          child: Column(
            children: [
              _buildAppBar(context),
              Expanded(
                child: SingleChildScrollView(
                  padding: const EdgeInsets.fromLTRB(
                    AppSpacing.md,
                    0,
                    AppSpacing.md,
                    AppSpacing.lg,
                  ),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.stretch,
                    children: [
                      _buildFAQSection(),
                      AppSpacing.verticalSpaceMD,
                      _buildSupportSection(),
                      AppSpacing.verticalSpaceMD,
                      _buildResourcesSection(),
                      AppSpacing.verticalSpaceMD,
                      _buildSocialMediaSection(),
                    ],
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildAppBar(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.all(AppSpacing.md),
      child: LiquidGlassAppBar(
        title: 'Trợ Giúp & Hỗ Trợ',
        subtitle: 'FAQ, kênh hỗ trợ và tài nguyên học tập',
        compact: true,
        leading: LiquidGlassAppBarAction(
          icon: Icons.arrow_back_ios_new,
          tooltip: 'Quay lại',
          onTap: () => Navigator.pop(context),
        ),
      ),
    );
  }

  Widget _buildFAQSection() {
    return _buildSectionCard(
      title: 'Câu Hỏi Thường Gặp',
      icon: Icons.help_outline,
      iconColors: [AppColors.primary, AppColors.primaryDark],
      child: ListView.separated(
        shrinkWrap: true,
        physics: const NeverScrollableScrollPhysics(),
        itemCount: _faqs.length,
        separatorBuilder: (_, __) => const SizedBox(height: AppSpacing.xs),
        itemBuilder: (_, index) => _buildFAQItem(_faqs[index], index),
      ),
    );
  }

  Widget _buildFAQItem(FAQItem faq, int index) {
    final isExpanded = _expandedIndex == index;

    return GlassContainer(
      padding: EdgeInsets.zero,
      borderRadius: BorderRadius.circular(AppSpacing.radiusMD),
      child: ClipRRect(
        borderRadius: BorderRadius.circular(AppSpacing.radiusMD),
        child: Theme(
          data: Theme.of(context).copyWith(
            dividerColor: Colors.transparent,
            splashColor: AppColors.primary.withOpacity(0.12),
          ),
          child: ExpansionTile(
            tilePadding: const EdgeInsets.symmetric(
              horizontal: AppSpacing.md,
              vertical: AppSpacing.xs,
            ),
            title: Text(
              faq.question,
              style: const TextStyle(
                fontSize: 15,
                fontWeight: FontWeight.w600,
                color: AppColors.textPrimary,
              ),
            ),
            trailing: Icon(
              isExpanded ? Icons.keyboard_arrow_up : Icons.keyboard_arrow_down,
              color: AppColors.textSecondary,
            ),
            onExpansionChanged: (expanded) {
              setState(() {
                _expandedIndex = expanded ? index : null;
              });
            },
            children: [
              Padding(
                padding: const EdgeInsets.fromLTRB(
                  AppSpacing.md,
                  0,
                  AppSpacing.md,
                  AppSpacing.md,
                ),
                child: Text(
                  faq.answer,
                  style: const TextStyle(
                    fontSize: 14,
                    color: AppColors.textSecondary,
                    height: 1.5,
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildSupportSection() {
    return _buildSectionCard(
      title: 'Liên Hệ Hỗ Trợ',
      icon: Icons.support_agent,
      iconColors: [AppColors.secondary, AppColors.accent],
      child: Column(
        children: [
          _buildActionTile(
            icon: Icons.email_outlined,
            title: 'Gửi Email Hỗ Trợ',
            subtitle: 'support@eduquest.vn',
            onTap: _launchEmail,
          ),
          AppSpacing.verticalSpaceSM,
          _buildActionTile(
            icon: Icons.bug_report_outlined,
            title: 'Báo Lỗi',
            subtitle: 'Giúp chúng tôi cải thiện ứng dụng',
            onTap: _launchEmail,
          ),
        ],
      ),
    );
  }

  Widget _buildResourcesSection() {
    return _buildSectionCard(
      title: 'Tài Nguyên',
      icon: Icons.menu_book,
      iconColors: [AppColors.info, AppColors.primary],
      child: Column(
        children: [
          _buildActionTile(
            icon: Icons.play_circle_outline,
            title: 'Hướng Dẫn Sử Dụng',
            subtitle: 'Video tutorial chi tiết',
            onTap: () => _launchURL('https://youtube.com/@eduquestar'),
          ),
          AppSpacing.verticalSpaceSM,
          _buildActionTile(
            icon: Icons.article_outlined,
            title: 'Tài Liệu Hướng Dẫn',
            subtitle: 'Tài liệu PDF chi tiết',
            onTap: () => _launchURL('https://eduquest.vn/docs'),
          ),
        ],
      ),
    );
  }

  Widget _buildSocialMediaSection() {
    return _buildSectionCard(
      title: 'Kết Nối Với Chúng Tôi',
      icon: Icons.share,
      iconColors: [AppColors.primary, AppColors.secondary],
      child: Wrap(
        spacing: AppSpacing.md,
        runSpacing: AppSpacing.sm,
        alignment: WrapAlignment.spaceAround,
        children: [
          _buildSocialButton(
            icon: Icons.facebook,
            label: 'Facebook',
            onTap: () => _launchURL('https://facebook.com/eduquestar'),
          ),
          _buildSocialButton(
            icon: Icons.video_library,
            label: 'YouTube',
            onTap: () => _launchURL('https://youtube.com/@eduquestar'),
          ),
          _buildSocialButton(
            icon: Icons.phone,
            label: 'Zalo',
            onTap: () => _launchURL('https://zalo.me/eduquestar'),
          ),
        ],
      ),
    );
  }

  Widget _buildSectionCard({
    required String title,
    required IconData icon,
    required List<Color> iconColors,
    required Widget child,
  }) {
    return GlassContainer(
      padding: const EdgeInsets.all(AppSpacing.md),
      borderRadius: BorderRadius.circular(AppSpacing.radiusLG),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Container(
                padding: const EdgeInsets.all(AppSpacing.sm),
                decoration: BoxDecoration(
                  gradient: LinearGradient(colors: iconColors),
                  borderRadius: BorderRadius.circular(AppSpacing.radiusMD),
                ),
                child: Icon(icon, color: AppColors.textPrimary, size: 20),
              ),
              AppSpacing.horizontalSpaceSM,
              Text(
                title,
                style: const TextStyle(
                  fontSize: 18,
                  fontWeight: FontWeight.bold,
                  color: AppColors.textPrimary,
                ),
              ),
            ],
          ),
          AppSpacing.verticalSpaceMD,
          child,
        ],
      ),
    );
  }

  Widget _buildActionTile({
    required IconData icon,
    required String title,
    required String subtitle,
    required VoidCallback onTap,
  }) {
    return GlassContainer(
      padding: EdgeInsets.zero,
      borderRadius: BorderRadius.circular(AppSpacing.radiusMD),
      child: Material(
        color: Colors.transparent,
        child: InkWell(
          onTap: onTap,
          borderRadius: BorderRadius.circular(AppSpacing.radiusMD),
          child: Padding(
            padding: const EdgeInsets.all(AppSpacing.md),
            child: Row(
              children: [
                Icon(icon, color: AppColors.textPrimary, size: 22),
                AppSpacing.horizontalSpaceSM,
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        title,
                        style: const TextStyle(
                          fontSize: 15,
                          fontWeight: FontWeight.w600,
                          color: AppColors.textPrimary,
                        ),
                      ),
                      const SizedBox(height: 2),
                      Text(
                        subtitle,
                        style: const TextStyle(
                          fontSize: 13,
                          color: AppColors.textSecondary,
                        ),
                      ),
                    ],
                  ),
                ),
                Icon(
                  Icons.arrow_forward_ios,
                  color: AppColors.textSecondary.withOpacity(0.8),
                  size: 16,
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildSocialButton({
    required IconData icon,
    required String label,
    required VoidCallback onTap,
  }) {
    return GestureDetector(
      onTap: onTap,
      child: Column(
        children: [
          GlassContainer(
            padding: const EdgeInsets.all(AppSpacing.md),
            borderRadius: BorderRadius.circular(AppSpacing.radiusMD),
            child: Icon(icon, color: AppColors.textPrimary, size: 26),
          ),
          AppSpacing.verticalSpaceXS,
          Text(
            label,
            style: const TextStyle(
              fontSize: 13,
              color: AppColors.textPrimary,
              fontWeight: FontWeight.w500,
            ),
          ),
        ],
      ),
    );
  }
}

class FAQItem {
  final String question;
  final String answer;

  FAQItem({
    required this.question,
    required this.answer,
  });
}
