import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../../core/theme/app_colors.dart';
import '../../../../core/theme/app_spacing.dart';
import '../../../../core/storage/hive_storage.dart';
import '../../../../shared/widgets/glass/index.dart';
import '../widgets/onboarding_page.dart';
import '../widgets/page_indicator.dart';

/// Onboarding screen shown to new users
/// Features 4-5 slides introducing app features with animations
class OnboardingScreen extends ConsumerStatefulWidget {
  const OnboardingScreen({super.key});

  @override
  ConsumerState<OnboardingScreen> createState() => _OnboardingScreenState();
}

class _OnboardingScreenState extends ConsumerState<OnboardingScreen>
    with SingleTickerProviderStateMixin {
  final PageController _pageController = PageController();
  int _currentPage = 0;
  late AnimationController _animationController;
  late Animation<double> _fadeAnimation;

  // Onboarding pages content
  final List<OnboardingPageData> _pages = [
    OnboardingPageData(
      title: 'Chào mừng đến với\nCửu Đỉnh Ký',
      description: 'Khám phá di sản văn hóa Việt Nam qua bộ sưu tập Cửu Đỉnh huyền thoại',
      icon: Icons.auto_awesome,
      gradient: AppColors.primaryGradient,
      color: AppColors.primary,
    ),
    OnboardingPageData(
      title: 'Khám phá 3D',
      description: 'Xem mô hình 3D chân thực của các đồng cổ. Xoay, phóng to và tìm hiểu chi tiết từng hoa văn',
      icon: Icons.view_in_ar_rounded,
      gradient: const LinearGradient(
        colors: [Color(0xFF60A5FA), Color(0xFF3B82F6)],
        begin: Alignment.topLeft,
        end: Alignment.bottomRight,
      ),
      color: AppColors.info,
    ),
    OnboardingPageData(
      title: 'Gamification',
      description: 'Tích lũy Hearts, Gems và Streaks khi hoàn thành bài học',
      icon: Icons.emoji_events_rounded,
      gradient: const LinearGradient(
        colors: [Color(0xFFF59E0B), Color(0xFFEF6B6B)],
        begin: Alignment.topLeft,
        end: Alignment.bottomRight,
      ),
      color: AppColors.warning,
    ),
    OnboardingPageData(
      title: 'Chọn mục tiêu',
      description: 'Đặt mục tiêu học tập hàng ngày và theo dõi tiến độ của bạn',
      icon: Icons.track_changes_rounded,
      gradient: const LinearGradient(
        colors: [Color(0xFF34D399), Color(0xFF10B981)],
        begin: Alignment.topLeft,
        end: Alignment.bottomRight,
      ),
      color: AppColors.success,
    ),
  ];

  @override
  void initState() {
    super.initState();
    _animationController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 600),
    );
    _fadeAnimation = Tween<double>(begin: 0.0, end: 1.0).animate(
      CurvedAnimation(
        parent: _animationController,
        curve: Curves.easeInOut,
      ),
    );
    _animationController.forward();
  }

  @override
  void dispose() {
    _pageController.dispose();
    _animationController.dispose();
    super.dispose();
  }

  void _onPageChanged(int page) {
    setState(() {
      _currentPage = page;
    });
    // Restart animation for new page
    _animationController.reset();
    _animationController.forward();
  }

  Future<void> _completeOnboarding() async {
    final storage = ref.read(hiveStorageProvider);
    await storage.setHasSeenOnboarding(true);
    
    if (mounted) {
      context.go('/explore');
    }
  }

  void _nextPage() {
    if (_currentPage < _pages.length - 1) {
      _pageController.nextPage(
        duration: const Duration(milliseconds: 400),
        curve: Curves.easeInOutCubic,
      );
    } else {
      _completeOnboarding();
    }
  }

  void _skipOnboarding() {
    _completeOnboarding();
  }

  @override
  Widget build(BuildContext context) {
    final isLastPage = _currentPage == _pages.length - 1;

    return Scaffold(
      body: AnimatedGradientBackground(
        duration: const Duration(seconds: 8),
        colors: const [
          Color(0xFF0A0E14),
          Color(0xFF141921),
          Color(0xFF1C232D),
          Color(0xFF0A0E14),
        ],
        child: SafeArea(
          child: Column(
            children: [
              // Skip button
              _buildTopBar(),

              // Page content
              Expanded(
                child: PageView.builder(
                  controller: _pageController,
                  onPageChanged: _onPageChanged,
                  itemCount: _pages.length,
                  itemBuilder: (context, index) {
                    return FadeTransition(
                      opacity: _fadeAnimation,
                      child: OnboardingPage(data: _pages[index]),
                    );
                  },
                ),
              ),

              // Page indicator
              PageIndicator(
                currentPage: _currentPage,
                pageCount: _pages.length,
              ),

              AppSpacing.verticalSpaceLG,

              // Navigation button
              _buildNavigationButton(isLastPage),

              AppSpacing.verticalSpaceXL,
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildTopBar() {
    return Padding(
      padding: const EdgeInsets.all(AppSpacing.md),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.end,
        children: [
          if (_currentPage < _pages.length - 1)
            TextButton(
              onPressed: _skipOnboarding,
              child: Text(
                'Bỏ qua',
                style: TextStyle(
                  color: AppColors.textSecondary,
                  fontSize: 16,
                  fontWeight: FontWeight.w500,
                ),
              ),
            ),
        ],
      ),
    );
  }

  Widget _buildNavigationButton(bool isLastPage) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: AppSpacing.lg),
      child: GlassButton(
        onPressed: _nextPage,
        gradient: _pages[_currentPage].gradient,
        padding: const EdgeInsets.symmetric(
          vertical: AppSpacing.md,
          horizontal: AppSpacing.xl,
        ),
        child: Row(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Text(
              isLastPage ? 'Bắt đầu' : 'Tiếp theo',
              style: const TextStyle(
                color: AppColors.onPrimary,
                fontSize: 18,
                fontWeight: FontWeight.bold,
              ),
            ),
            if (!isLastPage) ...[
              AppSpacing.horizontalSpaceSM,
              const Icon(
                Icons.arrow_forward_rounded,
                color: AppColors.onPrimary,
                size: 24,
              ),
            ],
          ],
        ),
      ),
    );
  }
}

/// Data class for onboarding page content
class OnboardingPageData {
  final String title;
  final String description;
  final IconData icon;
  final LinearGradient gradient;
  final Color color;

  const OnboardingPageData({
    required this.title,
    required this.description,
    required this.icon,
    required this.gradient,
    required this.color,
  });
}

