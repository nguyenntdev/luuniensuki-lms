import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../../core/theme/app_colors.dart';
import '../../../../core/theme/app_spacing.dart';
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
  final String icon;
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
    icon: '🧊',
    color: AppColors.info,
    transactionType: GemTransactionType.spentStreakFreeze,
  ),
  ShopItem(
    id: 'double_xp',
    name: 'X2 Kinh Nghiệm',
    description: 'Nhân đôi XP kiếm được trong 30 phút',
    cost: 100,
    icon: '⚡',
    color: AppColors.warning,
    transactionType: GemTransactionType.spentDoubleXp,
  ),
  ShopItem(
    id: 'hint',
    name: 'Gợi Ý',
    description: 'Nhận gợi ý cho câu trả lời hiện tại',
    cost: 25,
    icon: '💡',
    color: AppColors.success,
    transactionType: GemTransactionType.spentHint,
  ),
];

/// Gems shop screen
class GemsShopScreen extends ConsumerWidget {
  const GemsShopScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
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
      body: Container(
        decoration: BoxDecoration(
          gradient: LinearGradient(
            begin: Alignment.topLeft,
            end: Alignment.bottomRight,
            colors: [
              AppColors.primaryDark,
              AppColors.primaryDark.withOpacity(0.8),
              AppColors.background,
            ],
          ),
        ),
        child: SafeArea(
          child: ListView(
            padding: const EdgeInsets.all(AppSpacing.md),
            children: [
              // Header
              _buildHeader(),
              AppSpacing.verticalSpaceLG,

              // Shop items
              ...shopItems.map((item) => Padding(
                    padding: const EdgeInsets.only(bottom: AppSpacing.md),
                    child: _buildShopItem(
                      context,
                      item,
                      gemsState.balance,
                      gemsNotifier,
                    ),
                  )),

              // How to earn gems section
              AppSpacing.verticalSpaceLG,
              _buildHowToEarnSection(),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildHeader() {
    return GlassContainer(
      padding: const EdgeInsets.all(AppSpacing.lg),
      child: Column(
        children: [
          Text(
            '💎',
            style: TextStyle(fontSize: 48),
          ),
          AppSpacing.verticalSpaceSM,
          Text(
            'Cửa Hàng Gems',
            style: TextStyle(
              color: Colors.white,
              fontSize: 24,
              fontWeight: FontWeight.bold,
            ),
          ),
          AppSpacing.verticalSpaceXS,
          Text(
            'Sử dụng Gems để mua các vật phẩm hữu ích',
            style: TextStyle(
              color: Colors.white.withOpacity(0.7),
              fontSize: 14,
            ),
            textAlign: TextAlign.center,
          ),
        ],
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

    return GlassContainer(
      padding: const EdgeInsets.all(AppSpacing.md),
      child: Row(
        children: [
          // Icon
          Container(
            width: 60,
            height: 60,
            decoration: BoxDecoration(
              gradient: LinearGradient(
                colors: [
                  item.color.withOpacity(0.3),
                  item.color.withOpacity(0.1),
                ],
              ),
              borderRadius: BorderRadius.circular(AppSpacing.radiusMD),
              border: Border.all(
                color: item.color.withOpacity(0.3),
              ),
            ),
            child: Center(
              child: Text(
                item.icon,
                style: TextStyle(fontSize: 32),
              ),
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
              ],
            ),
          ),
          AppSpacing.horizontalSpaceMD,
          // Purchase button
          ElevatedButton(
            onPressed: canAfford
                ? () => _purchaseItem(context, item, notifier)
                : null,
            style: ElevatedButton.styleFrom(
              backgroundColor: canAfford ? item.color : Colors.grey,
              foregroundColor: Colors.white,
              padding: const EdgeInsets.symmetric(
                horizontal: AppSpacing.md,
                vertical: AppSpacing.sm,
              ),
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(AppSpacing.radiusMD),
              ),
            ),
            child: Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                Text('${item.cost}', style: TextStyle(fontWeight: FontWeight.bold)),
                const SizedBox(width: 4),
                const Text('💎', style: TextStyle(fontSize: 14)),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildHowToEarnSection() {
    return GlassContainer(
      padding: const EdgeInsets.all(AppSpacing.md),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              const Text('📚', style: TextStyle(fontSize: 24)),
              AppSpacing.horizontalSpaceSM,
              Text(
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
          _buildEarnMethod('Hoàn thành bài học', '+10 Gems'),
          _buildEarnMethod('Hoàn thành mục tiêu hàng ngày', '+20 Gems'),
          _buildEarnMethod('Đạt chuỗi 7 ngày', '+50 Gems'),
          _buildEarnMethod('Bài học hoàn hảo (không sai)', '+5 Gems'),
        ],
      ),
    );
  }

  Widget _buildEarnMethod(String title, String reward) {
    return Padding(
      padding: const EdgeInsets.only(bottom: AppSpacing.sm),
      child: Row(
        children: [
          Container(
            width: 8,
            height: 8,
            decoration: BoxDecoration(
              color: AppColors.gemYellow,
              shape: BoxShape.circle,
            ),
          ),
          AppSpacing.horizontalSpaceSM,
          Expanded(
            child: Text(
              title,
              style: TextStyle(
                color: Colors.white.withOpacity(0.9),
                fontSize: 14,
              ),
            ),
          ),
          Text(
            reward,
            style: TextStyle(
              color: AppColors.gemYellow,
              fontSize: 14,
              fontWeight: FontWeight.bold,
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
            '${isEarned ? '+' : ''}${transaction.amount} 💎',
            style: TextStyle(
              color: color,
              fontSize: 14,
              fontWeight: FontWeight.bold,
            ),
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

