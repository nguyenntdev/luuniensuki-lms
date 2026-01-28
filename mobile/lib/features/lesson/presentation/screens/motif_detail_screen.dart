import 'dart:io';
import 'dart:ui' as ui;

import 'package:flutter/material.dart';
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
    with SingleTickerProviderStateMixin, WidgetsBindingObserver {
  late TabController _tabController;

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 2, vsync: this);
    WidgetsBinding.instance.addObserver(this);

    // Force refresh when screen is first opened
    // This ensures we get fresh data after discovery
    WidgetsBinding.instance.addPostFrameCallback((_) {
      ref.invalidate(motifDetailProvider(widget.motifId));
    });
  }

  @override
  void dispose() {
    WidgetsBinding.instance.removeObserver(this);
    _tabController.dispose();
    super.dispose();
  }

  @override
  void didChangeAppLifecycleState(AppLifecycleState state) {
    super.didChangeAppLifecycleState(state);

    // Refresh data when app resumes
    if (state == AppLifecycleState.resumed) {
      ref.invalidate(motifDetailProvider(widget.motifId));
    }
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
          Hero(
            tag: 'motif_image_${motif.id}',
            child: CachedNetworkImage(
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
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Row(
            children: [
              SizedBox(width: 20, height: 20, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white)),
              SizedBox(width: 12),
              Text('Đang tạo ảnh chia sẻ...'),
            ],
          ),
          backgroundColor: AppColors.surface,
          duration: Duration(seconds: 15),
        ),
      );

      final heroUrl = motif.imageUrl ?? motif.thumbnailUrl;
      if (heroUrl == null || heroUrl.trim().isEmpty) {
        ScaffoldMessenger.of(context).hideCurrentSnackBar();
        await Share.share('${motif.name} - Khám phá tại ứng dụng Cửu Đỉnh Ký!');
        return;
      }

      final imageUrl = UrlUtils.getImageUrl(heroUrl);
      final tempDir = await getTemporaryDirectory();
      final originalPath = '${tempDir.path}/original_${motif.id}.jpg';

      await Dio().download(imageUrl, originalPath);

      // Load original image
      final originalBytes = await File(originalPath).readAsBytes();
      final codec = await ui.instantiateImageCodec(originalBytes);
      final frame = await codec.getNextFrame();
      final originalImage = frame.image;

      // Create 4:5 ratio image (1080x1350) for Instagram/Facebook
      const int outputWidth = 1080;
      const int outputHeight = 1350;
      const double captionBarHeight = 280.0;  // Increased for larger fonts
      final double imageAreaHeight = outputHeight - captionBarHeight;

      final recorder = ui.PictureRecorder();
      final canvas = Canvas(recorder);

      // Fill background with dark gradient color
      final bgPaint = Paint()
        ..shader = ui.Gradient.linear(
          const Offset(0, 0),
          Offset(0, outputHeight.toDouble()),
          [const Color(0xFF1A1A2E), const Color(0xFF0F0F1A)],
        );
      canvas.drawRect(
        Rect.fromLTWH(0, 0, outputWidth.toDouble(), outputHeight.toDouble()),
        bgPaint,
      );

      // Calculate image scaling to fit in image area (contain)
      final double scaleX = outputWidth / originalImage.width;
      final double scaleY = imageAreaHeight / originalImage.height;
      final double scale = scaleX < scaleY ? scaleX : scaleY;

      final double scaledWidth = originalImage.width * scale;
      final double scaledHeight = originalImage.height * scale;
      final double imageX = (outputWidth - scaledWidth) / 2;
      final double imageY = (imageAreaHeight - scaledHeight) / 2;

      // Draw original image centered in top area
      canvas.save();
      canvas.translate(imageX, imageY);
      canvas.scale(scale);
      canvas.drawImage(originalImage, Offset.zero, Paint()..filterQuality = ui.FilterQuality.high);
      canvas.restore();

      // Draw decorative gold top border line on image
      final goldBorderPaint = Paint()
        ..color = const Color(0xFFD4A84B)
        ..strokeWidth = 6;
      canvas.drawLine(
        const Offset(0, 3),
        Offset(outputWidth.toDouble(), 3),
        goldBorderPaint,
      );

      // Draw caption bar at bottom with gradient
      final barGradient = Paint()
        ..shader = ui.Gradient.linear(
          Offset(0, imageAreaHeight),
          Offset(0, outputHeight.toDouble()),
          [const Color(0xFF0A0A14), const Color(0xFF14141E)],
        );
      canvas.drawRect(
        Rect.fromLTWH(0, imageAreaHeight, outputWidth.toDouble(), captionBarHeight),
        barGradient,
      );

      // Draw decorative gold line at caption bar top
      final goldLinePaint = Paint()
        ..shader = ui.Gradient.linear(
          Offset(40, imageAreaHeight + 2),
          Offset(outputWidth - 40, imageAreaHeight + 2),
          [const Color(0x00D4A84B), const Color(0xFFD4A84B), const Color(0xFFD4A84B), const Color(0x00D4A84B)],
          [0.0, 0.2, 0.8, 1.0],
        )
        ..strokeWidth = 3;
      canvas.drawLine(
        Offset(40, imageAreaHeight + 2),
        Offset(outputWidth - 40, imageAreaHeight + 2),
        goldLinePaint,
      );

      // Draw decorative corner ornaments (gold dots pattern)
      final ornamentPaint = Paint()..color = const Color(0xFFD4A84B).withOpacity(0.4);
      for (int i = 0; i < 3; i++) {
        canvas.drawCircle(Offset(30 + i * 12, imageAreaHeight + 20), 3, ornamentPaint);
        canvas.drawCircle(Offset(outputWidth - 30 - i * 12, imageAreaHeight + 20), 3, ornamentPaint);
      }

      // Draw caption text - Line 1: Motif name (GOLD, LARGER)
      final textStyle1 = ui.TextStyle(
        color: const Color(0xFFD4A84B),  // Imperial Gold
        fontSize: 56,  // Increased from 48
        fontWeight: ui.FontWeight.bold,
        letterSpacing: 0.5,
      );
      final paragraph1Builder = ui.ParagraphBuilder(ui.ParagraphStyle(
        textAlign: ui.TextAlign.left,
        maxLines: 2,
        ellipsis: '...',
      ))
        ..pushStyle(textStyle1)
        ..addText(motif.name);
      final paragraph1 = paragraph1Builder.build()..layout(const ui.ParagraphConstraints(width: outputWidth - 80.0));
      canvas.drawParagraph(paragraph1, Offset(40, imageAreaHeight + 40));

      // Draw caption text - Line 2: Urn name (WHITE with slight gold tint)
      final textStyle2 = ui.TextStyle(
        color: const Color(0xFFF5F0E5),  // Warm white
        fontSize: 36,  // Increased from 32
      );
      final paragraph2Builder = ui.ParagraphBuilder(ui.ParagraphStyle(
        textAlign: ui.TextAlign.left,
        maxLines: 1,
        ellipsis: '...',
      ))
        ..pushStyle(textStyle2)
        ..addText('📍 ${motif.urn.name}');
      final paragraph2 = paragraph2Builder.build()..layout(const ui.ParagraphConstraints(width: outputWidth - 80.0));
      canvas.drawParagraph(paragraph2, Offset(40, imageAreaHeight + 135));

      // Draw app branding (GOLD with icon)
      final textStyle3 = ui.TextStyle(
        color: const Color(0xFFD4A84B),  // Imperial Gold
        fontSize: 32,  // Increased from 28
        fontWeight: ui.FontWeight.bold,
        letterSpacing: 1.0,
      );
      final paragraph3Builder = ui.ParagraphBuilder(ui.ParagraphStyle(
        textAlign: ui.TextAlign.left,
      ))
        ..pushStyle(textStyle3)
        ..addText('Cửu Đỉnh Ký');
      final paragraph3 = paragraph3Builder.build()..layout(const ui.ParagraphConstraints(width: outputWidth - 80.0));
      canvas.drawParagraph(paragraph3, Offset(40, imageAreaHeight + 200));

      // Draw decorative bottom ornament line
      canvas.drawLine(
        Offset(40, imageAreaHeight + 255),
        Offset(outputWidth - 40, imageAreaHeight + 255),
        goldLinePaint,
      );

      // Convert to image
      final picture = recorder.endRecording();
      final finalImage = await picture.toImage(outputWidth, outputHeight);
      final byteData = await finalImage.toByteData(format: ui.ImageByteFormat.png);

      final sharePath = '${tempDir.path}/share_${motif.id}.png';
      await File(sharePath).writeAsBytes(byteData!.buffer.asUint8List());

      if (mounted) {
        ScaffoldMessenger.of(context).hideCurrentSnackBar();
      }

      await Share.shareXFiles(
        [XFile(sharePath, mimeType: 'image/png')],
        subject: motif.name,
      );
    } catch (e) {
      debugPrint('Error sharing: $e');
      if (mounted) {
        ScaffoldMessenger.of(context).hideCurrentSnackBar();
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Lỗi: $e'), backgroundColor: Colors.red),
        );
      }
    }
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
