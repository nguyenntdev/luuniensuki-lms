import 'package:flutter/material.dart';

import '../../../../core/theme/app_colors.dart';
import '../../../../core/theme/app_spacing.dart';
import '../../../../shared/widgets/glass/index.dart';
import '../screens/onboarding_screen.dart';

/// Individual onboarding page widget with animated content
class OnboardingPage extends StatefulWidget {
  final OnboardingPageData data;

  const OnboardingPage({
    super.key,
    required this.data,
  });

  @override
  State<OnboardingPage> createState() => _OnboardingPageState();
}

class _OnboardingPageState extends State<OnboardingPage>
    with SingleTickerProviderStateMixin {
  late AnimationController _controller;
  late Animation<double> _scaleAnimation;
  late Animation<double> _rotationAnimation;
  late Animation<Offset> _slideAnimation;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 800),
    );

    _scaleAnimation = Tween<double>(begin: 0.5, end: 1.0).animate(
      CurvedAnimation(
        parent: _controller,
        curve: const Interval(0.0, 0.6, curve: Curves.elasticOut),
      ),
    );

    _rotationAnimation = Tween<double>(begin: -0.2, end: 0.0).animate(
      CurvedAnimation(
        parent: _controller,
        curve: const Interval(0.0, 0.6, curve: Curves.easeOut),
      ),
    );

    _slideAnimation = Tween<Offset>(
      begin: const Offset(0, 0.3),
      end: Offset.zero,
    ).animate(
      CurvedAnimation(
        parent: _controller,
        curve: const Interval(0.3, 1.0, curve: Curves.easeOut),
      ),
    );

    _controller.forward();
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.all(AppSpacing.lg),
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          // Animated icon with glass container
          ScaleTransition(
            scale: _scaleAnimation,
            child: RotationTransition(
              turns: _rotationAnimation,
              child: GlassContainer(
                opacity: 0.15,
                padding: const EdgeInsets.all(AppSpacing.xxl),
                borderRadius: BorderRadius.circular(100),
                gradient: widget.data.gradient,
                child: Icon(
                  widget.data.icon,
                  size: 120,
                  color: AppColors.white,
                ),
              ),
            ),
          ),

          AppSpacing.verticalSpaceXXL,

          // Title and description with slide animation
          SlideTransition(
            position: _slideAnimation,
            child: Column(
              children: [
                // Title
                Text(
                  widget.data.title,
                  textAlign: TextAlign.center,
                  style: const TextStyle(
                    fontSize: 32,
                    fontWeight: FontWeight.bold,
                    color: AppColors.textPrimary,
                    height: 1.2,
                  ),
                ),

                AppSpacing.verticalSpaceLG,

                // Description in glass container
                GlassContainer(
                  opacity: 0.08,
                  padding: const EdgeInsets.all(AppSpacing.lg),
                  child: Text(
                    widget.data.description,
                    textAlign: TextAlign.center,
                    style: TextStyle(
                      fontSize: 16,
                      color: AppColors.textSecondary,
                      height: 1.5,
                    ),
                  ),
                ),
              ],
            ),
          ),

          // Feature highlights based on page
          AppSpacing.verticalSpaceXL,
          _buildFeatureHighlight(),
        ],
      ),
    );
  }

  Widget _buildFeatureHighlight() {
    // Add specific highlights based on page content
    final title = widget.data.title;

    if (title.contains('Gamification')) {
      return _buildGamificationIcons();
    } else if (title.contains('mục tiêu')) {
      return _buildGoalOptions();
    }

    return const SizedBox.shrink();
  }

  Widget _buildGamificationIcons() {
    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceEvenly,
      children: [
        _buildGamificationItem(Icons.favorite_rounded, 'Hearts', AppColors.error),
        _buildGamificationItem(Icons.diamond_rounded, 'Gems', AppColors.gemYellow),
        _buildGamificationItem(Icons.local_fire_department_rounded, 'Streaks', AppColors.streakOrange),
      ],
    );
  }

  Widget _buildGamificationItem(IconData icon, String label, Color color) {
    return GlassContainer(
      opacity: 0.1,
      padding: const EdgeInsets.symmetric(
        horizontal: AppSpacing.md,
        vertical: AppSpacing.sm,
      ),
      borderRadius: BorderRadius.circular(AppSpacing.radiusMD),
      child: Column(
        children: [
          Icon(
            icon,
            size: 32,
            color: color,
          ),
          AppSpacing.verticalSpaceXS,
          Text(
            label,
            style: TextStyle(
              color: color,
              fontSize: 12,
              fontWeight: FontWeight.w600,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildGoalOptions() {
    return Column(
      children: [
        _buildGoalOption('Thư giãn', '5 XP/ngày', false),
        AppSpacing.verticalSpaceSM,
        _buildGoalOption('Thường xuyên', '10 XP/ngày', true),
        AppSpacing.verticalSpaceSM,
        _buildGoalOption('Nghiêm túc', '20 XP/ngày', false),
      ],
    );
  }

  Widget _buildGoalOption(String title, String description, bool isSelected) {
    return GlassContainer(
      opacity: isSelected ? 0.15 : 0.08,
      padding: const EdgeInsets.symmetric(
        horizontal: AppSpacing.lg,
        vertical: AppSpacing.md,
      ),
      borderRadius: BorderRadius.circular(AppSpacing.radiusMD),
      border: Border.all(
        color: isSelected
            ? widget.data.color.withOpacity(0.5)
            : AppColors.glassBorder,
        width: 2,
      ),
      child: Row(
        children: [
          Icon(
            isSelected ? Icons.radio_button_checked : Icons.radio_button_off,
            color: isSelected ? widget.data.color : AppColors.textHint,
          ),
          AppSpacing.horizontalSpaceMD,
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  title,
                  style: TextStyle(
                    color: isSelected
                        ? AppColors.textPrimary
                        : AppColors.textSecondary,
                    fontSize: 16,
                    fontWeight: FontWeight.w600,
                  ),
                ),
                Text(
                  description,
                  style: TextStyle(
                    color: AppColors.textHint,
                    fontSize: 12,
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

