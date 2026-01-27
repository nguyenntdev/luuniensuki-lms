import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../../../core/theme/app_colors.dart';
import '../../../../core/theme/app_typography.dart';
import '../../../../core/theme/app_spacing.dart';
import '../../../auth/presentation/providers/auth_provider.dart';
import '../providers/hearts_provider.dart';
import '../widgets/hearts_display.dart';

/// Screen shown when user runs out of hearts
class HeartsRefillScreen extends ConsumerWidget {
  final String? returnPath;

  const HeartsRefillScreen({
    super.key,
    this.returnPath,
  });

  static const int gemCostForRefill = 50;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final heartState = ref.watch(heartsNotifierProvider);
    final authState = ref.watch(authNotifierProvider);
    final user = authState.user;
    
    // If user somehow has hearts, navigate back
    if (heartState.hasHearts) {
      WidgetsBinding.instance.addPostFrameCallback((_) {
        if (context.mounted) {
          if (returnPath != null) {
            context.go(returnPath!);
          } else {
            context.pop();
          }
        }
      });
    }

    return Scaffold(
      backgroundColor: AppColors.background,
      appBar: AppBar(
        backgroundColor: AppColors.surface,
        foregroundColor: AppColors.textPrimary,
        title: const Text('Hết Tim'),
        leading: IconButton(
          icon: const Icon(Icons.close),
          onPressed: () {
            if (returnPath != null) {
              context.go('/');
            } else {
              context.pop();
            }
          },
        ),
      ),
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(AppSpacing.lg),
          child: Column(
            children: [
              const SizedBox(height: 40),
              
              // Large heart icon with animation
              TweenAnimationBuilder<double>(
                tween: Tween(begin: 0.8, end: 1.0),
                duration: const Duration(milliseconds: 800),
                curve: Curves.elasticOut,
                builder: (context, value, child) {
                  return Transform.scale(
                    scale: value,
                    child: child,
                  );
                },
                child: Container(
                  width: 120,
                  height: 120,
                  decoration: BoxDecoration(
                    shape: BoxShape.circle,
                    color: AppColors.error.withOpacity(0.1),
                    border: Border.all(
                      color: AppColors.error.withOpacity(0.3),
                      width: 3,
                    ),
                  ),
                  child: Icon(
                    Icons.favorite_border,
                    size: 60,
                    color: AppColors.error,
                  ),
                ),
              ),
              
              const SizedBox(height: 32),
              
              // Title
              Text(
                'Bạn đã hết tim!',
                style: AppTypography.textTheme.headlineMedium?.copyWith(
                  color: AppColors.textPrimary,
                  fontWeight: FontWeight.bold,
                ),
                textAlign: TextAlign.center,
              ),
              
              const SizedBox(height: 12),
              
              // Description
              Text(
                'Chọn một trong các cách dưới đây để tiếp tục học:',
                style: AppTypography.textTheme.bodyLarge?.copyWith(
                  color: AppColors.textSecondary,
                ),
                textAlign: TextAlign.center,
              ),
              
              const SizedBox(height: 40),
              
              // Current hearts display
              HeartsDisplay(showTimer: true),
              
              const SizedBox(height: 32),
              
              // Options
              _buildRefillOptions(context, ref, user),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildRefillOptions(BuildContext context, WidgetRef ref, user) {
    final heartState = ref.watch(heartsNotifierProvider);
    final timeUntilNextRefill = heartState.getTimeUntilNextRefillFormatted();

    return Column(
      children: [
        // Option 1: Wait for refill
        _buildOptionCard(
          context: context,
          icon: Icons.access_time,
          iconColor: AppColors.info,
          title: 'Đợi Tim Hồi',
          description: timeUntilNextRefill.isNotEmpty
              ? 'Tim tiếp theo trong $timeUntilNextRefill'
              : 'Tim đang hồi phục...',
          buttonText: 'Đợi',
          onTap: () {
            if (returnPath != null) {
              context.go('/');
            } else {
              context.pop();
            }
          },
        ),
        
        const SizedBox(height: 16),

        // Option 2: Spend gems for full refill
        _buildOptionCard(
          context: context,
          icon: Icons.diamond_rounded,
          iconColor: AppColors.primary,
          title: 'Nạp Đầy Tim',
          description: 'Sử dụng $gemCostForRefill Gems để nạp đầy tim',
          buttonText: 'Nạp Đầy',
          onTap: () async {
            final currentGems = user?.totalXp ?? 0; // TODO: Add gems system
            final success = await ref.read(heartsNotifierProvider.notifier).refillWithGems(
              gemCost: gemCostForRefill,
              currentGems: currentGems,
            );

            if (success && context.mounted) {
              ScaffoldMessenger.of(context).showSnackBar(
                SnackBar(
                  content: Text('Đã nạp đầy tim!'),
                  backgroundColor: AppColors.success,
                ),
              );

              // Navigate back
              if (returnPath != null) {
                context.go(returnPath!);
              } else {
                context.pop();
              }
            } else if (context.mounted) {
              ScaffoldMessenger.of(context).showSnackBar(
                SnackBar(
                  content: Row(
                    children: [
                      Icon(Icons.diamond_rounded, size: 16, color: Colors.white),
                      const SizedBox(width: 8),
                      const Text('Không đủ Gems để nạp tim'),
                    ],
                  ),
                  backgroundColor: AppColors.error,
                ),
              );
            }
          },
          // TODO: Disable if not enough gems
          isEnabled: true,
        ),

        const SizedBox(height: 16),

        // Option 3: Practice mode (earn hearts back)
        _buildOptionCard(
          context: context,
          icon: Icons.school,
          iconColor: AppColors.success,
          title: 'Chế Độ Luyện Tập',
          description: 'Luyện tập để nhận lại tim',
          buttonText: 'Luyện Tập',
          onTap: () {
            // TODO: Navigate to practice mode
            ScaffoldMessenger.of(context).showSnackBar(
              SnackBar(
                content: Text('Chế độ luyện tập đang phát triển...'),
                backgroundColor: AppColors.info,
              ),
            );
          },
        ),

        const SizedBox(height: 16),

        // Option 4: Watch ad for 1 heart (placeholder)
        _buildOptionCard(
          context: context,
          icon: Icons.play_circle_outline,
          iconColor: AppColors.warning,
          title: 'Xem Quảng Cáo',
          description: 'Xem quảng cáo để nhận 1 tim',
          buttonText: 'Xem',
          onTap: () async {
            // TODO: Implement ad system
            // For now, just give a free heart
            await ref.read(heartsNotifierProvider.notifier).addHeart();

            if (context.mounted) {
              ScaffoldMessenger.of(context).showSnackBar(
                SnackBar(
                  content: Text('Đã nhận 1 tim!'),
                  backgroundColor: AppColors.success,
                ),
              );
            }
          },
        ),
      ],
    );
  }

  Widget _buildOptionCard({
    required BuildContext context,
    required IconData icon,
    required Color iconColor,
    required String title,
    required String description,
    required String buttonText,
    required VoidCallback onTap,
    bool isEnabled = true,
  }) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: AppColors.surface,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(
          color: AppColors.border,
          width: 1,
        ),
      ),
      child: Row(
        children: [
          // Icon
          Container(
            width: 48,
            height: 48,
            decoration: BoxDecoration(
              color: iconColor.withOpacity(0.15),
              shape: BoxShape.circle,
            ),
            child: Icon(
              icon,
              color: iconColor,
              size: 24,
            ),
          ),

          const SizedBox(width: 16),

          // Title and description
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  title,
                  style: AppTypography.textTheme.titleMedium?.copyWith(
                    color: AppColors.textPrimary,
                    fontWeight: FontWeight.bold,
                  ),
                ),
                const SizedBox(height: 4),
                Text(
                  description,
                  style: AppTypography.textTheme.bodySmall?.copyWith(
                    color: AppColors.textSecondary,
                  ),
                ),
              ],
            ),
          ),

          const SizedBox(width: 12),

          // Button
          ElevatedButton(
            onPressed: isEnabled ? onTap : null,
            style: ElevatedButton.styleFrom(
              backgroundColor: iconColor,
              foregroundColor: Colors.white,
              padding: const EdgeInsets.symmetric(
                horizontal: 20,
                vertical: 10,
              ),
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(12),
              ),
            ),
            child: Text(buttonText),
          ),
        ],
      ),
    );
  }
}

