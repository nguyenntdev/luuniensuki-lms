import 'dart:io';
import 'dart:typed_data';
import 'dart:ui' as ui;

import 'package:flutter/material.dart';
import 'package:flutter/rendering.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:cached_network_image/cached_network_image.dart';
import 'package:share_plus/share_plus.dart';
import 'package:path_provider/path_provider.dart';
import 'package:dio/dio.dart';

import '../../../../core/theme/app_colors.dart';
import '../../../../core/theme/app_spacing.dart';
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
    final screenSize = MediaQuery.of(context).size;
    final isCompact = screenSize.width < 360 || screenSize.height < 700;
    final tabLabelStyle = AppTypography.textTheme.labelLarge?.copyWith(
      fontSize: isCompact ? 12 : 14,
      fontWeight: FontWeight.w600,
    );
    final tabLabelMuted = AppTypography.textTheme.labelLarge?.copyWith(
      fontSize: isCompact ? 12 : 14,
      fontWeight: FontWeight.w500,
      color: AppColors.textSecondary,
    );

    return NestedScrollView(
      headerSliverBuilder: (context, innerBoxIsScrolled) => [
        // Hero image header
        SliverAppBar(
          expandedHeight: isCompact ? 200 : 280,
          pinned: true,
          backgroundColor: AppColors.surface,
          foregroundColor: AppColors.textPrimary,
          leading: IconButton(
            icon: Container(
              padding: EdgeInsets.all(isCompact ? 6 : 8),
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
              labelStyle: tabLabelStyle,
              unselectedLabelStyle: tabLabelMuted,
              labelPadding: EdgeInsets.symmetric(
                horizontal: isCompact ? AppSpacing.sm : AppSpacing.md,
              ),
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
    final heroUrl = motif.imageUrl != null && motif.imageUrl!.trim().isNotEmpty
        ? motif.imageUrl
        : motif.thumbnailUrl;
    final imageUrl = UrlUtils.getImageUrl(heroUrl);

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
              if (motif.nameEn != null && motif.nameEn!.isNotEmpty) ...[
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
              Wrap(
                spacing: 8,
                runSpacing: 8,
                children: [
                  _CategoryChip(category: motif.category),
                  _RarityChip(rarity: motif.rarity),
                ],
              ),
            ],
          ),
        ),
      ],
    );
  }

  Future<void> _shareMotif(MotifDetailDto motif) async {
    try {
      // Show loading indicator
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Row(
            children: [
              SizedBox(
                width: 20,
                height: 20,
                child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white),
              ),
              SizedBox(width: 12),
              Text('Đang tạo ảnh chia sẻ...'),
            ],
          ),
          backgroundColor: AppColors.surface,
          duration: Duration(seconds: 15),
        ),
      );

      // Get best available image URL
      final heroUrl = motif.imageUrl != null && motif.imageUrl!.trim().isNotEmpty
          ? motif.imageUrl
          : motif.thumbnailUrl;

      if (heroUrl == null || heroUrl.trim().isEmpty) {
        ScaffoldMessenger.of(context).hideCurrentSnackBar();
        await Share.share(
          '🏛️ ${motif.name} - Khám phá tại ứng dụng Lưu Niên Sử Kí!',
        );
        return;
      }

      // Download the motif image first
      final imageUrl = UrlUtils.getImageUrl(heroUrl);
      final dio = Dio();
      final tempDir = await getTemporaryDirectory();
      final originalImagePath = '${tempDir.path}/motif_original_${motif.id}.jpg';

      await dio.download(imageUrl, originalImagePath);
      final originalImageFile = File(originalImagePath);
      final originalImageBytes = await originalImageFile.readAsBytes();

      // Create a beautiful share card using Flutter widgets
      final shareCardPath = await _createShareCard(motif, originalImageBytes);

      if (mounted) {
        ScaffoldMessenger.of(context).hideCurrentSnackBar();
      }

      // Share the card image
      await Share.shareXFiles(
        [XFile(shareCardPath, mimeType: 'image/png')],
        text: 'Khám phá họa tiết "${motif.name}" tại ứng dụng Lưu Niên Sử Kí!',
        subject: motif.name,
      );
    } catch (e) {
      debugPrint('Error sharing motif: $e');
      if (mounted) {
        ScaffoldMessenger.of(context).hideCurrentSnackBar();
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Không thể chia sẻ: $e'),
            backgroundColor: Colors.red,
          ),
        );
      }
    }
  }

  Future<String> _createShareCard(MotifDetailDto motif, List<int> imageBytes) async {
    // Card dimensions for social media (1080x1350 - Instagram portrait)
    const double cardWidth = 1080;
    const double cardHeight = 1350;

    // Create the share card widget
    final shareCardWidget = Material(
      color: Colors.transparent,
      child: Container(
        width: cardWidth,
        height: cardHeight,
        decoration: BoxDecoration(
          gradient: LinearGradient(
            begin: Alignment.topLeft,
            end: Alignment.bottomRight,
            colors: [
              const Color(0xFF1a1a2e),
              const Color(0xFF16213e),
              const Color(0xFF0f3460),
            ],
          ),
        ),
        child: Stack(
          children: [
            // Background pattern
            Positioned.fill(
              child: CustomPaint(
                painter: _PatternPainter(),
              ),
            ),
            // Content
            Padding(
              padding: const EdgeInsets.all(48),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.center,
                children: [
                  // App logo/branding
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 12),
                    decoration: BoxDecoration(
                      color: Colors.white.withOpacity(0.1),
                      borderRadius: BorderRadius.circular(30),
                      border: Border.all(color: Colors.white24),
                    ),
                    child: const Text(
                      '🏛️ LƯU NIÊN SỬ KÍ',
                      style: TextStyle(
                        color: Colors.white,
                        fontSize: 28,
                        fontWeight: FontWeight.bold,
                        letterSpacing: 2,
                      ),
                    ),
                  ),
                  const SizedBox(height: 40),
                  // Motif image in a decorative frame
                  Expanded(
                    child: Container(
                      decoration: BoxDecoration(
                        borderRadius: BorderRadius.circular(24),
                        boxShadow: [
                          BoxShadow(
                            color: AppColors.primary.withOpacity(0.3),
                            blurRadius: 30,
                            spreadRadius: 5,
                          ),
                        ],
                      ),
                      child: ClipRRect(
                        borderRadius: BorderRadius.circular(24),
                        child: Image.memory(
                          Uint8List.fromList(imageBytes),
                          fit: BoxFit.cover,
                          width: double.infinity,
                        ),
                      ),
                    ),
                  ),
                  const SizedBox(height: 40),
                  // Motif name
                  Text(
                    motif.name,
                    style: const TextStyle(
                      color: Colors.white,
                      fontSize: 48,
                      fontWeight: FontWeight.bold,
                    ),
                    textAlign: TextAlign.center,
                  ),
                  if (motif.nameEn != null) ...[
                    const SizedBox(height: 8),
                    Text(
                      motif.nameEn!,
                      style: TextStyle(
                        color: Colors.white.withOpacity(0.7),
                        fontSize: 28,
                        fontStyle: FontStyle.italic,
                      ),
                      textAlign: TextAlign.center,
                    ),
                  ],
                  const SizedBox(height: 24),
                  // Urn name badge
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 10),
                    decoration: BoxDecoration(
                      color: AppColors.primary.withOpacity(0.3),
                      borderRadius: BorderRadius.circular(20),
                      border: Border.all(color: AppColors.primary.withOpacity(0.5)),
                    ),
                    child: Text(
                      '📍 ${motif.urn.name}',
                      style: const TextStyle(
                        color: Colors.white,
                        fontSize: 24,
                      ),
                    ),
                  ),
                  const SizedBox(height: 16),
                  // Category and rarity
                  Row(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      _buildInfoChip('🎨 ${_getCategoryName(motif.category)}'),
                      const SizedBox(width: 16),
                      _buildInfoChip('⭐ ${_getRarityName(motif.rarity)}'),
                    ],
                  ),
                  const SizedBox(height: 32),
                  // Call to action
                  Text(
                    'Khám phá văn hóa Việt Nam',
                    style: TextStyle(
                      color: Colors.white.withOpacity(0.6),
                      fontSize: 20,
                    ),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );

    // Render widget to image
    final repaintBoundary = RenderRepaintBoundary();
    final renderView = RenderView(
      view: ui.PlatformDispatcher.instance.views.first,
      child: RenderPositionedBox(alignment: Alignment.center, child: repaintBoundary),
      configuration: ViewConfiguration(
        logicalConstraints: BoxConstraints.tight(const Size(cardWidth, cardHeight)),
        devicePixelRatio: 1.0,
      ),
    );

    final pipelineOwner = PipelineOwner();
    final buildOwner = BuildOwner(focusManager: FocusManager());

    pipelineOwner.rootNode = renderView;
    renderView.prepareInitialFrame();

    final rootElement = RenderObjectToWidgetAdapter<RenderBox>(
      container: repaintBoundary,
      child: shareCardWidget,
    ).attachToRenderTree(buildOwner);

    buildOwner.buildScope(rootElement);
    pipelineOwner.flushLayout();
    pipelineOwner.flushCompositingBits();
    pipelineOwner.flushPaint();

    final image = await repaintBoundary.toImage(pixelRatio: 1.0);
    final byteData = await image.toByteData(format: ui.ImageByteFormat.png);
    final pngBytes = byteData!.buffer.asUint8List();

    // Save to file
    final tempDir = await getTemporaryDirectory();
    final filePath = '${tempDir.path}/share_card_${motif.id}.png';
    final file = File(filePath);
    await file.writeAsBytes(pngBytes);

    return filePath;
  }

  Widget _buildInfoChip(String text) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      decoration: BoxDecoration(
        color: Colors.white.withOpacity(0.1),
        borderRadius: BorderRadius.circular(16),
      ),
      child: Text(
        text,
        style: const TextStyle(
          color: Colors.white,
          fontSize: 20,
        ),
      ),
    );
  }

  String _getCategoryName(String category) {
    const categories = {
      'animal': 'Động vật',
      'plant': 'Thực vật',
      'celestial': 'Thiên văn',
      'mythical': 'Thần thoại',
      'landscape': 'Phong cảnh',
      'symbol': 'Biểu tượng',
    };
    return categories[category] ?? category;
  }

  String _getRarityName(String rarity) {
    const rarities = {
      'common': 'Phổ thông',
      'uncommon': 'Không phổ biến',
      'rare': 'Hiếm',
      'epic': 'Sử thi',
      'legendary': 'Huyền thoại',
    };
    return rarities[rarity] ?? rarity;
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

/// Custom painter for decorative background pattern
class _PatternPainter extends CustomPainter {
  @override
  void paint(Canvas canvas, Size size) {
    final paint = Paint()
      ..color = Colors.white.withOpacity(0.03)
      ..style = PaintingStyle.stroke
      ..strokeWidth = 1;

    // Draw decorative circles
    for (int i = 0; i < 5; i++) {
      final radius = 100.0 + i * 150;
      canvas.drawCircle(
        Offset(size.width * 0.8, size.height * 0.2),
        radius,
        paint,
      );
    }

    // Draw diagonal lines
    for (int i = 0; i < 10; i++) {
      final y = i * 200.0 - 200;
      canvas.drawLine(
        Offset(-100, y),
        Offset(size.width + 100, y + size.width),
        paint,
      );
    }
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => false;
}
