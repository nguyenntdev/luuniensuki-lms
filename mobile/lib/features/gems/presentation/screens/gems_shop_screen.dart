import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../../core/theme/app_colors.dart';
import '../../../../core/theme/app_spacing.dart';
import '../../../../shared/widgets/glass/animated_background.dart';
import '../../../../shared/widgets/glass/glass_container.dart';
import '../../domain/entities/gem_transaction.dart';
import '../providers/gems_provider.dart';
import '../widgets/gems_display.dart';

/// Shop item data
class ShopItem {
  final String id;
  final String name;
  final String description;
  final int cost;
  final IconData icon;
  final Color color;
  final GemTransactionType transactionType;

  const ShopItem({
    required this.id,
    required this.name,
    required this.description,
    required this.cost,
    required this.icon,
    required this.color,
    required this.transactionType,
  });
}

/// Available shop items
const List<ShopItem> shopItems = [
  ShopItem(
    id: 'streak_freeze',
    name: 'Đóng Băng Chuỗi',
    description: 'Bảo vệ chuỗi học tập của bạn trong 1 ngày',
    cost: 50,
    icon: Icons.ac_unit,
    color: AppColors.info,
    transactionType: GemTransactionType.spentStreakFreeze,
  ),
  ShopItem(
    id: 'double_xp',
    name: 'X2 Kinh Nghiệm',
    description: 'Nhân đôi XP kiếm được trong 30 phút',
    cost: 100,
    icon: Icons.bolt,
    color: AppColors.warning,
    transactionType: GemTransactionType.spentDoubleXp,
  ),
  ShopItem(
    id: 'hint',
    name: 'Gợi Ý',
    description: 'Nhận gợi ý cho câu trả lời hiện tại',
    cost: 25,
    icon: Icons.lightbulb_outline,
    color: AppColors.success,
    transactionType: GemTransactionType.spentHint,
  ),
];

/// Gems shop screen
class GemsShopScreen extends ConsumerStatefulWidget {
  const GemsShopScreen({super.key});

  @override
  ConsumerState<GemsShopScreen> createState() => _GemsShopScreenState();
}

class _GemsShopScreenState extends ConsumerState<GemsShopScreen>
    with SingleTickerProviderStateMixin {
  late AnimationController _animationController;

  @override
  void initState() {
    super.initState();
    _animationController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 800),
    );
    _animationController.forward();
  }

  @override
  void dispose() {
    _animationController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final gemsState = ref.watch(gemsNotifierProvider);
    final gemsNotifier = ref.read(gemsNotifierProvider.notifier);

    return Scaffold(
      extendBodyBehindAppBar: true,
      appBar: AppBar(
        backgroundColor: Colors.transparent,
        elevation: 0,
        leading: IconButton(
          icon: const Icon(Icons.arrow_back, color: Colors.white),
          onPressed: () => context.pop(),
        ),
        title: const Text(
          'Cửa Hàng Gems',
          style: TextStyle(
            color: Colors.white,
            fontWeight: FontWeight.bold,
          ),
        ),
        actions: [
          Padding(
            padding: const EdgeInsets.only(right: AppSpacing.md),
            child: Center(
              child: CompactGemsDisplay(
                onTap: () => _showTransactionHistory(context, ref),
              ),
            ),
          ),
        ],
      ),
      body: AnimatedGradientBackground(
        child: SafeArea(
          child: ListView(
            padding: const EdgeInsets.all(AppSpacing.md),
            children: [
              // Shop items with staggered animations
              ...List.generate(shopItems.length, (index) {
                final item = shopItems[index];
                return _buildAnimatedShopItem(
                  context,
                  item,
                  gemsState.balance,
                  gemsNotifier,
                  index,
                );
              }),

              // How to earn gems section
              AppSpacing.verticalSpaceLG,
              _buildAnimatedHowToEarnSection(),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildAnimatedShopItem(
    BuildContext context,
    ShopItem item,
    int balance,
    GemsNotifier notifier,
    int index,
  ) {
    return AnimatedBuilder(
      animation: _animationController,
      builder: (context, child) {
        final delay = index * 0.15;
        final animation = CurvedAnimation(
          parent: _animationController,
          curve: Interval(
            delay.clamp(0.0, 1.0),
            (delay + 0.5).clamp(0.0, 1.0),
            curve: Curves.easeOutCubic,
          ),
        );
        return FadeTransition(
          opacity: animation,
          child: SlideTransition(
            position: Tween<Offset>(
              begin: const Offset(0, 0.3),
              end: Offset.zero,
            ).animate(animation),
            child: child,
          ),
        );
      },
      child: Padding(
        padding: const EdgeInsets.only(bottom: AppSpacing.md),
        child: _buildShopItem(context, item, balance, notifier),
      ),
    );
  }

  Widget _buildShopItem(
    BuildContext context,
    ShopItem item,
    int balance,
    GemsNotifier notifier,
  ) {
    final canAfford = balance >= item.cost;
    final gemsNeeded = canAfford ? 0 : item.cost - balance;

    return AnimatedScale(
      scale: canAfford ? 1.0 : 0.98,
      duration: const Duration(milliseconds: 200),
      child: GestureDetector(
        onTap: canAfford ? () => _purchaseItem(context, item, notifier) : null,
        child: GlassContainer(
          padding: const EdgeInsets.all(AppSpacing.md),
          child: Row(
            children: [
              // Icon with enhanced styling
              Container(
                width: 64,
                height: 64,
                decoration: BoxDecoration(
                  gradient: LinearGradient(
                    begin: Alignment.topLeft,
                    end: Alignment.bottomRight,
                    colors: [
                      item.color.withOpacity(canAfford ? 0.8 : 0.3),
                      item.color.withOpacity(canAfford ? 0.5 : 0.2),
                    ],
                  ),
                  borderRadius: BorderRadius.circular(AppSpacing.radiusMD),
                  border: Border.all(
                    color: item.color.withOpacity(canAfford ? 0.5 : 0.2),
                    width: 2,
                  ),
                  boxShadow: canAfford
                      ? [
                          BoxShadow(
                            color: item.color.withOpacity(0.3),
                            blurRadius: 12,
                            spreadRadius: 0,
                          ),
                        ]
                      : null,
                ),
                child: Icon(
                  item.icon,
                  size: 32,
                  color: canAfford ? Colors.white : Colors.white38,
                ),
              ),
              AppSpacing.horizontalSpaceMD,
              // Details
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      item.name,
                      style: TextStyle(
                        color: Colors.white,
                        fontSize: 16,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                    AppSpacing.verticalSpaceXS,
                    Text(
                      item.description,
                      style: TextStyle(
                        color: Colors.white.withOpacity(0.7),
                        fontSize: 12,
                      ),
                    ),
                    if (!canAfford) ...[
                      AppSpacing.verticalSpaceXS,
                      Text(
                        'Cần thêm $gemsNeeded gems',
                        style: TextStyle(
                          color: AppColors.error.withOpacity(0.9),
                          fontSize: 11,
                          fontWeight: FontWeight.w500,
                        ),
                      ),
                    ],
                  ],
                ),
              ),
              AppSpacing.horizontalSpaceMD,
              // Purchase button
              Container(
                decoration: BoxDecoration(
                  gradient: canAfford
                      ? LinearGradient(
                          begin: Alignment.topLeft,
                          end: Alignment.bottomRight,
                          colors: [
                            item.color,
                            item.color.withOpacity(0.8),
                          ],
                        )
                      : null,
                  color: canAfford ? null : Colors.grey.withOpacity(0.3),
                  borderRadius: BorderRadius.circular(AppSpacing.radiusMD),
                  boxShadow: canAfford
                      ? [
                          BoxShadow(
                            color: item.color.withOpacity(0.3),
                            blurRadius: 8,
                            spreadRadius: 0,
                          ),
                        ]
                      : null,
                ),
                child: Material(
                  color: Colors.transparent,
                  child: InkWell(
                    onTap: canAfford
                        ? () => _purchaseItem(context, item, notifier)
                        : null,
                    borderRadius: BorderRadius.circular(AppSpacing.radiusMD),
                    child: Padding(
                      padding: const EdgeInsets.symmetric(
                        horizontal: AppSpacing.md,
                        vertical: AppSpacing.sm,
                      ),
                      child: Row(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          Text(
                            '${item.cost}',
                            style: TextStyle(
                              color: canAfford ? Colors.white : Colors.white38,
                              fontWeight: FontWeight.bold,
                              fontSize: 14,
                            ),
                          ),
                          const SizedBox(width: 4),
                          Icon(
                            Icons.diamond,
                            size: 16,
                            color: canAfford ? Colors.white : Colors.white38,
                          ),
                        ],
                      ),
                    ),
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildAnimatedHowToEarnSection() {
    return AnimatedBuilder(
      animation: _animationController,
      builder: (context, child) {
        final delay = shopItems.length * 0.15;
        final animation = CurvedAnimation(
          parent: _animationController,
          curve: Interval(
            delay.clamp(0.0, 1.0),
            (delay + 0.5).clamp(0.0, 1.0),
            curve: Curves.easeOutCubic,
          ),
        );
        return FadeTransition(
          opacity: animation,
          child: SlideTransition(
            position: Tween<Offset>(
              begin: const Offset(0, 0.3),
              end: Offset.zero,
            ).animate(animation),
            child: child,
          ),
        );
      },
      child: _buildHowToEarnSection(),
    );
  }

  Widget _buildHowToEarnSection() {
    return GlassContainer(
      padding: const EdgeInsets.all(AppSpacing.lg),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Container(
                padding: const EdgeInsets.all(8),
                decoration: BoxDecoration(
                  gradient: const LinearGradient(
                    colors: [
                      Color(0xFFFFD700),
                      Color(0xFFFFA500),
                    ],
                  ),
                  borderRadius: BorderRadius.circular(8),
                ),
                child: const Icon(
                  Icons.school,
                  color: Colors.white,
                  size: 20,
                ),
              ),
              AppSpacing.horizontalSpaceSM,
              const Text(
                'Cách Kiếm Gems',
                style: TextStyle(
                  color: Colors.white,
                  fontSize: 18,
                  fontWeight: FontWeight.bold,
                ),
              ),
            ],
          ),
          AppSpacing.verticalSpaceMD,
          _buildEarnMethod(
            Icons.check_circle_outline,
            'Hoàn thành bài học',
            '+10 Gems',
            AppColors.success,
          ),
          _buildEarnMethod(
            Icons.flag_outlined,
            'Hoàn thành mục tiêu hàng ngày',
            '+20 Gems',
            AppColors.warning,
          ),
          _buildEarnMethod(
            Icons.local_fire_department_outlined,
            'Đạt chuỗi 7 ngày',
            '+50 Gems',
            AppColors.error,
          ),
          _buildEarnMethod(
            Icons.stars_outlined,
            'Bài học hoàn hảo (không sai)',
            '+5 Gems',
            AppColors.info,
          ),
        ],
      ),
    );
  }

  Widget _buildEarnMethod(
    IconData icon,
    String title,
    String reward,
    Color color,
  ) {
    return Padding(
      padding: const EdgeInsets.only(bottom: AppSpacing.md),
      child: Row(
        children: [
          Container(
            width: 36,
            height: 36,
            decoration: BoxDecoration(
              color: color.withOpacity(0.15),
              borderRadius: BorderRadius.circular(8),
              border: Border.all(
                color: color.withOpacity(0.3),
                width: 1,
              ),
            ),
            child: Icon(
              icon,
              color: color,
              size: 18,
            ),
          ),
          AppSpacing.horizontalSpaceSM,
          Expanded(
            child: Text(
              title,
              style: TextStyle(
                color: Colors.white.withOpacity(0.9),
                fontSize: 14,
                fontWeight: FontWeight.w500,
              ),
            ),
          ),
          Container(
            padding: const EdgeInsets.symmetric(
              horizontal: 10,
              vertical: 4,
            ),
            decoration: BoxDecoration(
              gradient: LinearGradient(
                colors: [
                  AppColors.gemYellow.withOpacity(0.2),
                  AppColors.gemYellow.withOpacity(0.1),
                ],
              ),
              borderRadius: BorderRadius.circular(12),
              border: Border.all(
                color: AppColors.gemYellow.withOpacity(0.3),
                width: 1,
              ),
            ),
            child: Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                Text(
                  reward,
                  style: const TextStyle(
                    color: AppColors.gemYellow,
                    fontSize: 13,
                    fontWeight: FontWeight.bold,
                  ),
                ),
                const SizedBox(width: 4),
                const Icon(
                  Icons.diamond,
                  color: AppColors.gemYellow,
                  size: 14,
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Future<void> _purchaseItem(
    BuildContext context,
    ShopItem item,
    GemsNotifier notifier,
  ) async {
    final success = await notifier.spendGems(
      amount: item.cost,
      type: item.transactionType,
      description: 'Mua ${item.name}',
    );

    if (!context.mounted) return;

    if (success) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('Đã mua ${item.name}!'),
          backgroundColor: AppColors.success,
          behavior: SnackBarBehavior.floating,
        ),
      );
    } else {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: const Text('Không đủ Gems!'),
          backgroundColor: AppColors.error,
          behavior: SnackBarBehavior.floating,
        ),
      );
    }
  }

  void _showTransactionHistory(BuildContext context, WidgetRef ref) {
    final transactions = ref.read(gemsNotifierProvider).transactions;

    showModalBottomSheet(
      context: context,
      backgroundColor: Colors.transparent,
      builder: (context) => Container(
        decoration: BoxDecoration(
          gradient: LinearGradient(
            begin: Alignment.topLeft,
            end: Alignment.bottomRight,
            colors: [
              AppColors.primaryDark,
              AppColors.background,
            ],
          ),
          borderRadius: const BorderRadius.vertical(top: Radius.circular(20)),
        ),
        child: Column(
          children: [
            Padding(
              padding: const EdgeInsets.all(AppSpacing.md),
              child: Text(
                'Lịch Sử Giao Dịch',
                style: TextStyle(
                  color: Colors.white,
                  fontSize: 18,
                  fontWeight: FontWeight.bold,
                ),
              ),
            ),
            Expanded(
              child: transactions.isEmpty
                  ? Center(
                      child: Text(
                        'Chưa có giao dịch',
                        style: TextStyle(
                          color: Colors.white.withOpacity(0.7),
                        ),
                      ),
                    )
                  : ListView.builder(
                      itemCount: transactions.length,
                      padding: const EdgeInsets.all(AppSpacing.md),
                      itemBuilder: (context, index) {
                        final transaction = transactions[index];
                        return _buildTransactionItem(transaction);
                      },
                    ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildTransactionItem(GemTransaction transaction) {
    final isEarned = transaction.amount > 0;
    final color = isEarned ? AppColors.success : AppColors.error;

    return Padding(
      padding: const EdgeInsets.only(bottom: AppSpacing.sm),
      child: GlassContainer(
        padding: const EdgeInsets.all(AppSpacing.sm),
        child: Row(
        children: [
          Container(
            padding: const EdgeInsets.all(8),
            decoration: BoxDecoration(
              color: color.withOpacity(0.2),
              shape: BoxShape.circle,
            ),
            child: Icon(
              isEarned ? Icons.add : Icons.remove,
              color: color,
              size: 16,
            ),
          ),
          AppSpacing.horizontalSpaceSM,
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  transaction.description,
                  style: TextStyle(
                    color: Colors.white,
                    fontSize: 14,
                    fontWeight: FontWeight.w500,
                  ),
                ),
                Text(
                  _formatDate(transaction.createdAt),
                  style: TextStyle(
                    color: Colors.white.withOpacity(0.6),
                    fontSize: 12,
                  ),
                ),
              ],
            ),
          ),
          Text(
            '${isEarned ? '+' : ''}${transaction.amount}',
            style: TextStyle(
              color: color,
              fontSize: 14,
              fontWeight: FontWeight.bold,
            ),
          ),
          const SizedBox(width: 4),
          Icon(
            Icons.diamond,
            color: color,
            size: 14,
          ),
        ],
      ),
      ),
    );
  }

  String _formatDate(DateTime date) {
    final now = DateTime.now();
    final diff = now.difference(date);

    if (diff.inMinutes < 1) return 'Vừa xong';
    if (diff.inHours < 1) return '${diff.inMinutes} phút trước';
    if (diff.inDays < 1) return '${diff.inHours} giờ trước';
    if (diff.inDays < 7) return '${diff.inDays} ngày trước';

    return '${date.day}/${date.month}/${date.year}';
  }
}

