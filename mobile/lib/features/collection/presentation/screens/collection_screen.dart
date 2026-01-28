import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:cached_network_image/cached_network_image.dart';

import '../../../../core/theme/app_colors.dart';
import '../../../../core/utils/url_utils.dart';
import '../../../../shared/widgets/glass/animated_background.dart';
import '../../../../shared/widgets/glass/glass_container.dart';
import '../../../../shared/widgets/shimmer/shimmer_skeleton.dart';
import '../../data/models/collection_dtos.dart';
import '../providers/collection_provider.dart';
import '../providers/collection_filter_provider.dart';

/// Filter options for the collection
enum CollectionFilter {
  all,
  discovered,
  learned,
  mastered,
}

/// Collection screen showing user's discovered motifs
class CollectionScreen extends ConsumerStatefulWidget {
  const CollectionScreen({super.key});

  @override
  ConsumerState<CollectionScreen> createState() => _CollectionScreenState();
}

class _CollectionScreenState extends ConsumerState<CollectionScreen>
    with SingleTickerProviderStateMixin {
  late AnimationController _controller;

  @override
  void initState() {
    super.initState();

    // Initialize animation controller
    _controller = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 800),
    );
    _controller.forward();

    // Load collection when screen is first created
    Future.microtask(() {
      ref.read(collectionNotifierProvider.notifier).loadCollection();
    });
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return AnimatedGradientBackground(
      child: SafeArea(
        child: Column(
          children: [
            // Header
            _buildHeader(),

            // Filter chips
            _buildFilterChips(),

            // Content
            Expanded(
              child: _buildContent(),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildHeader() {
    return Padding(
      padding: const EdgeInsets.fromLTRB(20, 16, 20, 8),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Text(
                'Bộ Sưu Tập',
                style: TextStyle(
                  color: Colors.white,
                  fontSize: 28,
                  fontWeight: FontWeight.bold,
                ),
              ),
              Text(
                'Các họa tiết bạn đã khám phá',
                style: TextStyle(
                  color: Colors.white.withOpacity(0.7),
                  fontSize: 14,
                ),
              ),
            ],
          ),
          // Search button
          Container(
            decoration: BoxDecoration(
              color: Colors.white.withOpacity(0.1),
              borderRadius: BorderRadius.circular(12),
            ),
            child: IconButton(
              icon: const Icon(Icons.search, color: Colors.white70),
              onPressed: () {
                ScaffoldMessenger.of(context).showSnackBar(
                  const SnackBar(content: Text('Tìm kiếm - Coming soon')),
                );
              },
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildFilterChips() {
    final selectedFilter = ref.watch(collectionFilterProvider);

    return SingleChildScrollView(
      scrollDirection: Axis.horizontal,
      padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 12),
      child: Row(
        children: CollectionFilter.values.map((filter) {
          final isSelected = selectedFilter == filter;
          return Padding(
            padding: const EdgeInsets.only(right: 8),
            child: GestureDetector(
              onTap: () => ref.read(collectionFilterProvider.notifier).state = filter,
              child: Container(
                padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
                decoration: BoxDecoration(
                  color: isSelected
                      ? AppColors.primary
                      : Colors.white.withOpacity(0.1),
                  borderRadius: BorderRadius.circular(20),
                  border: Border.all(
                    color: isSelected
                        ? AppColors.primary
                        : Colors.white.withOpacity(0.2),
                  ),
                ),
                child: Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Icon(
                      _getFilterIcon(filter),
                      size: 16,
                      color: isSelected
                          ? AppColors.onPrimary
                          : Colors.white70,
                    ),
                    const SizedBox(width: 6),
                    Text(
                      _getFilterLabel(filter),
                      style: TextStyle(
                        color: isSelected
                            ? AppColors.onPrimary
                            : Colors.white,
                        fontSize: 14,
                        fontWeight: isSelected ? FontWeight.bold : FontWeight.normal,
                      ),
                    ),
                  ],
                ),
              ),
            ),
          );
        }).toList(),
      ),
    );
  }

  IconData _getFilterIcon(CollectionFilter filter) {
    switch (filter) {
      case CollectionFilter.all:
        return Icons.grid_view;
      case CollectionFilter.discovered:
        return Icons.visibility;
      case CollectionFilter.learned:
        return Icons.school;
      case CollectionFilter.mastered:
        return Icons.star;
    }
  }

  String _getFilterLabel(CollectionFilter filter) {
    switch (filter) {
      case CollectionFilter.all:
        return 'Tất cả';
      case CollectionFilter.discovered:
        return 'Đã khám phá';
      case CollectionFilter.learned:
        return 'Đã học';
      case CollectionFilter.mastered:
        return 'Thành thạo';
    }
  }

  Widget _buildContent() {
    final state = ref.watch(collectionNotifierProvider);

    // Handle loading state
    if (state.isLoading && !state.hasData) {
      return _buildLoadingState();
    }

    // Handle error state
    if (state.hasError) {
      return Center(
        child: Padding(
          padding: const EdgeInsets.all(32),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Icon(
                Icons.error_outline,
                size: 64,
                color: Colors.white.withOpacity(0.3),
              ),
              const SizedBox(height: 16),
              Text(
                state.errorMessage ?? 'Đã xảy ra lỗi',
                textAlign: TextAlign.center,
                style: TextStyle(
                  color: Colors.white.withOpacity(0.8),
                  fontSize: 16,
                ),
              ),
              const SizedBox(height: 24),
              ElevatedButton.icon(
                onPressed: () {
                  ref.read(collectionNotifierProvider.notifier).loadCollection();
                },
                style: ElevatedButton.styleFrom(
                  backgroundColor: AppColors.primary,
                  foregroundColor: AppColors.onPrimary,
                  padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 12),
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(12),
                  ),
                ),
                icon: const Icon(Icons.refresh),
                label: const Text('Thử lại'),
              ),
            ],
          ),
        ),
      );
    }

    // Handle data state
    if (state.hasData && state.collection != null) {
      // Filter motifs based on selected filter
      final filteredMotifs = _filterMotifs(state.collection!.items);

      // Show empty state if no motifs match filter
      if (filteredMotifs.isEmpty) {
        return _buildEmptyState();
      }

      return _buildMotifGrid(filteredMotifs);
    }

    // Fallback to empty state
    return _buildEmptyState();
  }

  /// Build loading state with shimmer skeletons
  Widget _buildLoadingState() {
    return GridView.builder(
      padding: const EdgeInsets.fromLTRB(16, 8, 16, 100),
      gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
        crossAxisCount: 2,
        childAspectRatio: 0.85,
        crossAxisSpacing: 12,
        mainAxisSpacing: 12,
      ),
      // Show 8 shimmer cards as placeholder
      itemCount: 8,
      itemBuilder: (context, index) {
        return const ShimmerMotifCard();
      },
    );
  }

  /// Filter motifs based on selected filter
  List<CollectionMotifDto> _filterMotifs(List<CollectionMotifDto> motifs) {
    final selectedFilter = ref.read(collectionFilterProvider);

    switch (selectedFilter) {
      case CollectionFilter.all:
        // Show all motifs that are at least discovered
        return motifs.where((m) => m.status != 'hidden').toList();
      case CollectionFilter.discovered:
        return motifs.where((m) => m.status == 'discovered').toList();
      case CollectionFilter.learned:
        return motifs.where((m) => m.status == 'learned').toList();
      case CollectionFilter.mastered:
        return motifs.where((m) => m.status == 'mastered').toList();
    }
  }

  Widget _buildEmptyState() {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(32),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Container(
              width: 100,
              height: 100,
              decoration: BoxDecoration(
                color: Colors.white.withOpacity(0.1),
                shape: BoxShape.circle,
              ),
              child: Icon(
                Icons.collections_outlined,
                size: 48,
                color: Colors.white.withOpacity(0.3),
              ),
            ),
            const SizedBox(height: 24),
            Text(
              'Chưa có họa tiết nào',
              style: TextStyle(
                color: Colors.white.withOpacity(0.8),
                fontSize: 18,
                fontWeight: FontWeight.bold,
              ),
            ),
            const SizedBox(height: 8),
            Text(
              'Hãy khám phá các đỉnh để thu thập họa tiết',
              textAlign: TextAlign.center,
              style: TextStyle(
                color: Colors.white.withOpacity(0.5),
                fontSize: 14,
              ),
            ),
            const SizedBox(height: 24),
            ElevatedButton.icon(
              onPressed: () => context.go('/explore'),
              style: ElevatedButton.styleFrom(
                backgroundColor: AppColors.primary,
                foregroundColor: AppColors.onPrimary,
                padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 12),
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(12),
                ),
              ),
              icon: const Icon(Icons.explore),
              label: const Text('Khám phá ngay'),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildMotifGrid(List<CollectionMotifDto> motifs) {
    return RefreshIndicator(
      onRefresh: () async {
        await ref.read(collectionNotifierProvider.notifier).loadCollection();
      },
      color: AppColors.primary,
      backgroundColor: AppColors.surface,
      child: GridView.builder(
        padding: const EdgeInsets.fromLTRB(16, 8, 16, 100),
        physics: const AlwaysScrollableScrollPhysics(),
        gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
          crossAxisCount: 2,
          childAspectRatio: 0.85,
          crossAxisSpacing: 12,
          mainAxisSpacing: 12,
        ),
        itemCount: motifs.length,
        itemBuilder: (context, index) {
          final motif = motifs[index];
          return _buildAnimatedMotifCard(motif, index);
        },
      ),
    );
  }

  Widget _buildAnimatedMotifCard(CollectionMotifDto motif, int index) {
    return AnimatedBuilder(
      animation: _controller,
      builder: (context, child) {
        final delay = index * 0.1;
        final animation = CurvedAnimation(
          parent: _controller,
          curve: Interval(
            delay.clamp(0.0, 1.0),
            (delay + 0.4).clamp(0.0, 1.0),
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
      child: _buildMotifCard(motif),
    );
  }

  Widget _buildMotifCard(CollectionMotifDto motif) {
    return GestureDetector(
      onTap: () => context.push('/motifs/${motif.id}'),
      child: GlassContainer(
        padding: const EdgeInsets.all(12),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Motif thumbnail
            Expanded(
              child: Container(
                width: double.infinity,
                decoration: BoxDecoration(
                  color: Colors.white.withOpacity(0.05),
                  borderRadius: BorderRadius.circular(12),
                ),
                child: motif.thumbnailUrl != null && motif.thumbnailUrl!.isNotEmpty
                    ? Hero(
                        tag: 'motif_image_${motif.id}',
                        child: CachedNetworkImage(
                          imageUrl: UrlUtils.getImageUrl(motif.thumbnailUrl),
                          fit: BoxFit.cover,
                          width: double.infinity,
                          height: double.infinity,
                          placeholder: (context, url) => const ShimmerSkeleton(
                            width: double.infinity,
                            height: double.infinity,
                          ),
                          errorWidget: (context, url, error) => Center(
                            child: Icon(
                              Icons.image_not_supported_outlined,
                              size: 48,
                              color: Colors.white.withOpacity(0.3),
                            ),
                          ),
                        ),
                      )
                    : Center(
                        child: Icon(
                          Icons.image,
                          size: 48,
                          color: Colors.white.withOpacity(0.3),
                        ),
                      ),
              ),
            ),

            const SizedBox(height: 12),

            // Motif name
            Text(
              motif.name,
              style: const TextStyle(
                color: Colors.white,
                fontSize: 14,
                fontWeight: FontWeight.bold,
              ),
              maxLines: 1,
              overflow: TextOverflow.ellipsis,
            ),

            const SizedBox(height: 4),

            // Status badge
            Row(
              children: [
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                  decoration: BoxDecoration(
                    color: _getStatusColor(motif.status).withOpacity(0.2),
                    borderRadius: BorderRadius.circular(8),
                  ),
                  child: Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Icon(
                        _getStatusIcon(motif.status),
                        size: 12,
                        color: _getStatusColor(motif.status),
                      ),
                      const SizedBox(width: 4),
                      Text(
                        _getStatusLabel(motif.status),
                        style: TextStyle(
                          color: _getStatusColor(motif.status),
                          fontSize: 10,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                    ],
                  ),
                ),
                const Spacer(),
                Text(
                  motif.category,
                  style: TextStyle(
                    color: Colors.white.withOpacity(0.5),
                    fontSize: 10,
                  ),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Color _getStatusColor(String? status) {
    switch (status) {
      case 'mastered':
        return AppColors.primary;
      case 'learned':
        return AppColors.success;
      case 'discovered':
        return AppColors.info;
      default:
        return Colors.white.withOpacity(0.5);
    }
  }

  IconData _getStatusIcon(String? status) {
    switch (status) {
      case 'mastered':
        return Icons.star;
      case 'learned':
        return Icons.school;
      case 'discovered':
        return Icons.visibility;
      default:
        return Icons.lock;
    }
  }

  String _getStatusLabel(String? status) {
    switch (status) {
      case 'mastered':
        return 'Thành thạo';
      case 'learned':
        return 'Đã học';
      case 'discovered':
        return 'Đã khám phá';
      default:
        return 'Chưa mở';
    }
  }
}
