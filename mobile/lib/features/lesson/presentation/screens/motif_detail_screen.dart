import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:cached_network_image/cached_network_image.dart';

import '../../../../core/theme/app_colors.dart';
import '../../../../core/theme/app_typography.dart';
import '../../../../core/utils/url_utils.dart';
import '../../../../routing/route_names.dart';
import '../../../urn_viewer/data/models/urn_dtos.dart';
import '../providers/motif_detail_provider.dart';
import '../widgets/lesson_tab.dart';
import '../widgets/info_tab.dart';
import '../widgets/progress_stepper.dart';

/// Motif detail screen with lesson content and info tabs.
class MotifDetailScreen extends ConsumerStatefulWidget {
  final String motifId;

  const MotifDetailScreen({super.key, required this.motifId});

  @override
  ConsumerState<MotifDetailScreen> createState() => _MotifDetailScreenState();
}

class _MotifDetailScreenState extends ConsumerState<MotifDetailScreen>
    with SingleTickerProviderStateMixin {
  late TabController _tabController;

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 2, vsync: this);
  }

  @override
  void dispose() {
    _tabController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final motifAsync = ref.watch(motifDetailProvider(widget.motifId));

    return Scaffold(
      backgroundColor: AppColors.background,
      body: motifAsync.when(
        loading: () => const Center(
          child: CircularProgressIndicator(
            color: AppColors.primary,
          ),
        ),
        error: (e, s) => _buildErrorState(e.toString()),
        data: (motifDetail) => _buildContent(motifDetail),
      ),
    );
  }

  Widget _buildErrorState(String message) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(
              Icons.error_outline,
              size: 64,
              color: AppColors.error.withOpacity(0.7),
            ),
            const SizedBox(height: 16),
            Text(
              'Không thể tải thông tin',
              style: AppTypography.textTheme.titleLarge?.copyWith(
                color: AppColors.textPrimary,
              ),
            ),
            const SizedBox(height: 8),
            Text(
              message,
              style: AppTypography.textTheme.bodyMedium?.copyWith(
                color: AppColors.textSecondary,
              ),
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 24),
            ElevatedButton.icon(
              onPressed: () =>
                  ref.invalidate(motifDetailProvider(widget.motifId)),
              icon: const Icon(Icons.refresh),
              label: const Text('Thử lại'),
              style: ElevatedButton.styleFrom(
                backgroundColor: AppColors.primary,
                foregroundColor: AppColors.onPrimary,
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildContent(MotifDetailDto motifDetail) {
    return NestedScrollView(
      headerSliverBuilder: (context, innerBoxIsScrolled) => [
        // Hero image header
        SliverAppBar(
          expandedHeight: 280,
          pinned: true,
          backgroundColor: AppColors.surface,
          foregroundColor: AppColors.textPrimary,
          leading: IconButton(
            icon: Container(
              padding: const EdgeInsets.all(8),
              decoration: BoxDecoration(
                color: AppColors.background.withOpacity(0.7),
                shape: BoxShape.circle,
              ),
              child: const Icon(Icons.arrow_back, size: 20),
            ),
            onPressed: () => context.pop(),
          ),
          actions: [
            IconButton(
              icon: Container(
                padding: const EdgeInsets.all(8),
                decoration: BoxDecoration(
                  color: AppColors.background.withOpacity(0.7),
                  shape: BoxShape.circle,
                ),
                child: const Icon(Icons.share, size: 20),
              ),
              onPressed: () => _shareMotif(motifDetail),
            ),
          ],
          flexibleSpace: FlexibleSpaceBar(
            background: _buildHeroImage(motifDetail),
          ),
        ),

        // Progress stepper
        SliverToBoxAdapter(
          child: ProgressStepper(
            status: motifDetail.progress?.status ?? 'hidden',
          ),
        ),

        // Tab bar
        SliverPersistentHeader(
          pinned: true,
          delegate: _TabBarDelegate(
            TabBar(
              controller: _tabController,
              labelColor: AppColors.primary,
              unselectedLabelColor: AppColors.textSecondary,
              indicatorColor: AppColors.primary,
              indicatorWeight: 3,
              tabs: const [
                Tab(text: 'Bài Học'),
                Tab(text: 'Thông Tin'),
              ],
            ),
          ),
        ),
      ],
      body: TabBarView(
        controller: _tabController,
        children: [
          LessonTab(
            motif: motifDetail,
            lesson: motifDetail.lesson,
            progress: motifDetail.progress,
          ),
          InfoTab(motif: motifDetail),
        ],
      ),
    );
  }

  Widget _buildHeroImage(MotifDetailDto motif) {
    final imageUrl = UrlUtils.getImageUrl(motif.imageUrl ?? motif.thumbnailUrl);

    return Stack(
      fit: StackFit.expand,
      children: [
        // Background image
        if (imageUrl.isNotEmpty)
          CachedNetworkImage(
            imageUrl: imageUrl,
            fit: BoxFit.cover,
            placeholder: (_, __) => Container(
              color: AppColors.surfaceVariant,
              child: const Center(
                child: CircularProgressIndicator(
                  color: AppColors.primary,
                  strokeWidth: 2,
                ),
              ),
            ),
            errorWidget: (_, __, ___) => Container(
              color: AppColors.surfaceVariant,
              child: Icon(
                Icons.image_not_supported,
                size: 64,
                color: AppColors.textHint,
              ),
            ),
          )
        else
          Container(
            color: AppColors.surfaceVariant,
            child: Icon(
              Icons.image,
              size: 64,
              color: AppColors.textHint,
            ),
          ),

        // Gradient overlay
        Container(
          decoration: BoxDecoration(
            gradient: LinearGradient(
              begin: Alignment.topCenter,
              end: Alignment.bottomCenter,
              colors: [
                Colors.transparent,
                AppColors.background.withOpacity(0.3),
                AppColors.background.withOpacity(0.9),
              ],
              stops: const [0.0, 0.6, 1.0],
            ),
          ),
        ),

        // Motif info
        Positioned(
          left: 16,
          right: 16,
          bottom: 16,
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                motif.name,
                style: AppTypography.textTheme.headlineSmall?.copyWith(
                  color: AppColors.textPrimary,
                  fontWeight: FontWeight.bold,
                ),
              ),
              if (motif.nameEn != null) ...[
                const SizedBox(height: 4),
                Text(
                  motif.nameEn!,
                  style: AppTypography.textTheme.bodyMedium?.copyWith(
                    color: AppColors.textSecondary,
                    fontStyle: FontStyle.italic,
                  ),
                ),
              ],
              const SizedBox(height: 12),
              Row(
                children: [
                  _CategoryChip(category: motif.category),
                  const SizedBox(width: 8),
                  _RarityChip(rarity: motif.rarity),
                ],
              ),
            ],
          ),
        ),
      ],
    );
  }

  void _shareMotif(MotifDetailDto motif) {
    // TODO: Implement share functionality
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(
        content: Text('Tính năng chia sẻ đang phát triển'),
        backgroundColor: AppColors.surface,
      ),
    );
  }
}

/// Tab bar delegate for pinned tab bar
class _TabBarDelegate extends SliverPersistentHeaderDelegate {
  final TabBar tabBar;

  _TabBarDelegate(this.tabBar);

  @override
  Widget build(
    BuildContext context,
    double shrinkOffset,
    bool overlapsContent,
  ) {
    return Container(
      color: AppColors.background,
      child: tabBar,
    );
  }

  @override
  double get maxExtent => tabBar.preferredSize.height;

  @override
  double get minExtent => tabBar.preferredSize.height;

  @override
  bool shouldRebuild(covariant _TabBarDelegate oldDelegate) {
    return tabBar != oldDelegate.tabBar;
  }
}

/// Category chip widget
class _CategoryChip extends StatelessWidget {
  final String category;

  const _CategoryChip({required this.category});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
      decoration: BoxDecoration(
        color: AppColors.primary.withOpacity(0.15),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(
          color: AppColors.primary.withOpacity(0.3),
        ),
      ),
      child: Text(
        _getCategoryName(category),
        style: AppTypography.textTheme.labelSmall?.copyWith(
          color: AppColors.primary,
          fontWeight: FontWeight.w600,
        ),
      ),
    );
  }

  String _getCategoryName(String category) {
    switch (category.toLowerCase()) {
      case 'animal':
        return 'Động vật';
      case 'plant':
        return 'Thực vật';
      case 'celestial':
        return 'Thiên văn';
      case 'mythical':
        return 'Thần thoại';
      case 'landscape':
        return 'Phong cảnh';
      case 'symbol':
        return 'Biểu tượng';
      default:
        return category;
    }
  }
}

/// Rarity chip widget
class _RarityChip extends StatelessWidget {
  final String rarity;

  const _RarityChip({required this.rarity});

  @override
  Widget build(BuildContext context) {
    final color = _getRarityColor(rarity);

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
      decoration: BoxDecoration(
        color: color.withOpacity(0.15),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(
          color: color.withOpacity(0.3),
        ),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(
            Icons.auto_awesome,
            size: 12,
            color: color,
          ),
          const SizedBox(width: 4),
          Text(
            _getRarityName(rarity),
            style: AppTypography.textTheme.labelSmall?.copyWith(
              color: color,
              fontWeight: FontWeight.w600,
            ),
          ),
        ],
      ),
    );
  }

  Color _getRarityColor(String rarity) {
    switch (rarity.toLowerCase()) {
      case 'common':
        return AppColors.rarityCommon;
      case 'uncommon':
        return AppColors.rarityUncommon;
      case 'rare':
        return AppColors.rarityRare;
      case 'epic':
        return AppColors.rarityEpic;
      case 'legendary':
        return AppColors.rarityLegendary;
      default:
        return AppColors.rarityCommon;
    }
  }

  String _getRarityName(String rarity) {
    switch (rarity.toLowerCase()) {
      case 'common':
        return 'Phổ thông';
      case 'uncommon':
        return 'Không phổ biến';
      case 'rare':
        return 'Hiếm';
      case 'epic':
        return 'Sử thi';
      case 'legendary':
        return 'Huyền thoại';
      default:
        return rarity;
    }
  }
}
