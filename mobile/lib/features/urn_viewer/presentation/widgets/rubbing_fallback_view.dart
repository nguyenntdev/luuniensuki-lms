import 'package:flutter/material.dart';

import '../../../../core/constants/api_constants.dart';
import '../../../../core/theme/app_colors.dart';
import '../../../../core/theme/app_typography.dart';
import '../../domain/entities/urn.dart';
import '../../domain/entities/urn_manifest.dart';

/// 2D Rubbing Fallback View for Urn Viewer (ADR 05 / Spec §V2-C).
///
/// Displayed when:
/// 1. 3D mesh is MISSING for this urn (8 of the 9 urns).
/// 2. Device memory/thermal constraints require graceful degradation.
/// 3. 3D model loading fails, times out, or WebGL context is lost.
/// 4. User explicitly chooses 2D archival inspection mode.
///
/// Features:
/// - Interactive zoom & pan on authentic HMCC 2D rubbing photograph.
/// - Clear archival reconstruction notice (no phantom assets or fake 3D primitives).
/// - Full interactive exploration of all 18 motifs (discovering, learning, quizzing).
/// - 100% equivalent learning progress and XP earning.
class RubbingFallbackView extends StatefulWidget {
  final UrnDetail urnDetail;
  final UrnManifest manifest;
  final List<Motif> motifs;
  final Function(Motif motif) onMotifTap;
  final VoidCallback? onReturnTo3D;
  final Motif? selectedMotif;
  final bool isMemoryOrThermalConstraint;
  final String? customBannerMessage;

  const RubbingFallbackView({
    super.key,
    required this.urnDetail,
    required this.manifest,
    required this.motifs,
    required this.onMotifTap,
    this.onReturnTo3D,
    this.selectedMotif,
    this.isMemoryOrThermalConstraint = false,
    this.customBannerMessage,
  });

  @override
  State<RubbingFallbackView> createState() => _RubbingFallbackViewState();
}

class _RubbingFallbackViewState extends State<RubbingFallbackView> {
  final TransformationController _transformController =
      TransformationController();
  bool _imageLoaded = false;
  // ignore: unused_field
  bool _imageError = false;
  bool _showMotifGrid = false;

  @override
  void dispose() {
    _transformController.dispose();
    super.dispose();
  }

  String _resolveRubbingUrl() {
    final assetUrl = widget.manifest.viewerFallback.assetUrl;
    if (assetUrl.startsWith('http://') || assetUrl.startsWith('https://')) {
      return assetUrl;
    }
    final cleanPath = assetUrl.startsWith('/') ? assetUrl.substring(1) : assetUrl;
    return '${ApiConstants.baseUrl}/$cleanPath';
  }

  @override
  Widget build(BuildContext context) {
    final rubbingUrl = _resolveRubbingUrl();
    final canSwitchTo3D = widget.manifest.hasPresentMesh && widget.onReturnTo3D != null;

    return Stack(
      children: [
        // 1. High-resolution 2D Rubbing Viewer with Pinch-to-Zoom
        Positioned.fill(
          child: Container(
            color: const Color(0xFF0F0F1A),
            child: InteractiveViewer(
              transformationController: _transformController,
              minScale: 0.8,
              maxScale: 4.5,
              boundaryMargin: const EdgeInsets.all(64),
              child: Center(
                child: Image.network(
                  rubbingUrl,
                  fit: BoxFit.contain,
                  loadingBuilder: (context, child, loadingProgress) {
                    if (loadingProgress == null) {
                      if (!_imageLoaded) {
                        WidgetsBinding.instance.addPostFrameCallback((_) {
                          if (mounted) setState(() => _imageLoaded = true);
                        });
                      }
                      return child;
                    }
                    final expected = loadingProgress.expectedTotalBytes;
                    final loaded = loadingProgress.cumulativeBytesLoaded;
                    final progress = (expected != null && expected > 0)
                        ? loaded / expected
                        : null;
                    return Center(
                      child: Column(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          CircularProgressIndicator(
                            value: progress,
                            valueColor: const AlwaysStoppedAnimation<Color>(
                                AppColors.primary),
                          ),
                          const SizedBox(height: 16),
                          const Text(
                            'Đang tải bản dập 2D lưu trữ...',
                            style: TextStyle(color: Colors.white70, fontSize: 13),
                          ),
                          if (progress != null) ...[
                            const SizedBox(height: 6),
                            Text(
                              '${(progress * 100).toInt()}%',
                              style: const TextStyle(
                                  color: Colors.white54, fontSize: 12),
                            ),
                          ],
                        ],
                      ),
                    );
                  },
                  errorBuilder: (context, error, stackTrace) {
                    return Center(
                      child: Padding(
                        padding: const EdgeInsets.all(24),
                        child: Column(
                          mainAxisSize: MainAxisSize.min,
                          children: [
                            const Icon(Icons.broken_image_outlined,
                                color: Colors.orange, size: 54),
                            const SizedBox(height: 12),
                            Text(
                              'Không thể tải ảnh bản dập từ máy chủ',
                              style: AppTypography.textTheme.titleSmall
                                  ?.copyWith(color: Colors.white),
                            ),
                            const SizedBox(height: 6),
                            Text(
                              rubbingUrl,
                              style: const TextStyle(
                                  color: Colors.white38,
                                  fontSize: 10,
                                  fontFamily: 'monospace'),
                              textAlign: TextAlign.center,
                            ),
                            const SizedBox(height: 16),
                            ElevatedButton.icon(
                              onPressed: () => setState(() {
                                _imageError = false;
                              }),
                              icon: const Icon(Icons.refresh, size: 16),
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
                  },
                ),
              ),
            ),
          ),
        ),

        // 2. Archival Fallback Notice Banner
        Positioned(
          top: MediaQuery.of(context).padding.top + 56,
          left: 12,
          right: 12,
          child: _buildArchivalNoticeBanner(canSwitchTo3D),
        ),

        // 3. Floating Quick Switch / Grid Button
        Positioned(
          right: 16,
          bottom: MediaQuery.of(context).padding.bottom + 90,
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              if (canSwitchTo3D) ...[
                FloatingActionButton.small(
                  heroTag: 'switch_3d_btn',
                  backgroundColor: AppColors.primary,
                  foregroundColor: AppColors.onPrimary,
                  onPressed: widget.onReturnTo3D,
                  tooltip: 'Chuyển sang mô hình 3D',
                  child: const Icon(Icons.view_in_ar),
                ),
                const SizedBox(height: 8),
              ],
              FloatingActionButton.small(
                heroTag: 'motif_grid_toggle',
                backgroundColor: Colors.black87,
                foregroundColor: Colors.white,
                onPressed: () => setState(() => _showMotifGrid = !_showMotifGrid),
                tooltip: _showMotifGrid ? 'Ẩn danh sách' : 'Hiện 18 họa tiết',
                child: Icon(_showMotifGrid ? Icons.close : Icons.grid_view),
              ),
              const SizedBox(height: 8),
              FloatingActionButton.small(
                heroTag: 'zoom_reset_btn',
                backgroundColor: Colors.black54,
                foregroundColor: Colors.white,
                onPressed: () {
                  _transformController.value = Matrix4.identity();
                },
                tooltip: 'Đặt lại thu phóng',
                child: const Icon(Icons.center_focus_strong, size: 18),
              ),
            ],
          ),
        ),

        // 4. Interactive Motif Grid Modal / Bottom Drawer
        if (_showMotifGrid)
          Positioned(
            left: 0,
            right: 0,
            bottom: MediaQuery.of(context).padding.bottom + 70,
            child: _buildMotifGridSheet(),
          ),
      ],
    );
  }

  Widget _buildArchivalNoticeBanner(bool canSwitchTo3D) {
    final title = widget.isMemoryOrThermalConstraint
        ? 'Thiết bị hạn chế bộ nhớ · Đang hiển thị bản dập 2D'
        : (widget.customBannerMessage ??
            'Mô hình 3D đang phục chế · Bản dập 2D thay thế');

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
      decoration: BoxDecoration(
        color: const Color(0xDD1E1A11),
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: Colors.amber.withOpacity(0.5), width: 1.2),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.5),
            blurRadius: 16,
            offset: const Offset(0, 4),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        mainAxisSize: MainAxisSize.min,
        children: [
          Row(
            children: [
              Container(
                width: 8,
                height: 8,
                decoration: const BoxDecoration(
                  color: Colors.amber,
                  shape: BoxShape.circle,
                ),
              ),
              const SizedBox(width: 8),
              Expanded(
                child: Text(
                  title,
                  style: const TextStyle(
                    color: Colors.amber,
                    fontSize: 12,
                    fontWeight: FontWeight.bold,
                  ),
                  overflow: TextOverflow.ellipsis,
                ),
              ),
              if (canSwitchTo3D)
                TextButton(
                  onPressed: widget.onReturnTo3D,
                  style: TextButton.styleFrom(
                    visualDensity: VisualDensity.compact,
                    padding:
                        const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                  ),
                  child: const Text(
                    'Mở 3D',
                    style: TextStyle(
                      color: AppColors.primary,
                      fontSize: 12,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                ),
            ],
          ),
          const SizedBox(height: 4),
          Text(
            'Hồ sơ lưu trữ bản dập 2D chuẩn xác từ Trung tâm Bảo tồn Di tích Cố đô Huế (HMCC). Toàn bộ 18 họa tiết đều có thể khám phá và làm bài tập học tập.',
            style: TextStyle(
              color: Colors.white.withOpacity(0.75),
              fontSize: 11,
              height: 1.3,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildMotifGridSheet() {
    return Container(
      margin: const EdgeInsets.symmetric(horizontal: 12),
      constraints: const BoxConstraints(maxHeight: 280),
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: const Color(0xF0181824),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: Colors.white.withOpacity(0.15)),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.7),
            blurRadius: 20,
            offset: const Offset(0, -4),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        mainAxisSize: MainAxisSize.min,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Row(
                children: [
                  const Icon(Icons.collections_bookmark_outlined,
                      color: AppColors.primary, size: 18),
                  const SizedBox(width: 8),
                  Text(
                    '18 Họa tiết trên ${widget.urnDetail.urn.name}',
                    style: const TextStyle(
                      color: Colors.white,
                      fontSize: 13,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                ],
              ),
              IconButton(
                icon: const Icon(Icons.close, color: Colors.white54, size: 18),
                onPressed: () => setState(() => _showMotifGrid = false),
                visualDensity: VisualDensity.compact,
              ),
            ],
          ),
          const SizedBox(height: 8),
          Expanded(
            child: ListView.separated(
              scrollDirection: Axis.horizontal,
              itemCount: widget.motifs.length,
              separatorBuilder: (_, __) => const SizedBox(width: 8),
              itemBuilder: (context, index) {
                final motif = widget.motifs[index];
                final isSelected = widget.selectedMotif?.id == motif.id;
                final statusColor = _statusColor(motif.status);

                return GestureDetector(
                  onTap: () {
                    widget.onMotifTap(motif);
                  },
                  child: Container(
                    width: 140,
                    padding: const EdgeInsets.all(10),
                    decoration: BoxDecoration(
                      color: isSelected
                          ? AppColors.primary.withOpacity(0.2)
                          : Colors.white.withOpacity(0.06),
                      borderRadius: BorderRadius.circular(12),
                      border: Border.all(
                        color: isSelected
                            ? AppColors.primary
                            : Colors.white.withOpacity(0.12),
                        width: isSelected ? 1.5 : 1.0,
                      ),
                    ),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        Row(
                          children: [
                            Container(
                              width: 8,
                              height: 8,
                              decoration: BoxDecoration(
                                color: statusColor,
                                shape: BoxShape.circle,
                              ),
                            ),
                            const SizedBox(width: 6),
                            Expanded(
                              child: Text(
                                _statusLabel(motif.status),
                                style: TextStyle(
                                  color: statusColor,
                                  fontSize: 10,
                                  fontWeight: FontWeight.bold,
                                ),
                                overflow: TextOverflow.ellipsis,
                              ),
                            ),
                          ],
                        ),
                        Text(
                          motif.name,
                          style: const TextStyle(
                            color: Colors.white,
                            fontSize: 13,
                            fontWeight: FontWeight.bold,
                          ),
                          maxLines: 2,
                          overflow: TextOverflow.ellipsis,
                        ),
                        Text(
                          motif.category.nameVi,
                          style: const TextStyle(
                            color: Colors.white54,
                            fontSize: 10,
                          ),
                          overflow: TextOverflow.ellipsis,
                        ),
                      ],
                    ),
                  ),
                );
              },
            ),
          ),
        ],
      ),
    );
  }

  Color _statusColor(MotifStatus status) {
    switch (status) {
      case MotifStatus.mastered:
        return AppColors.statusMastered;
      case MotifStatus.learned:
        return AppColors.statusLearned;
      case MotifStatus.discovered:
        return AppColors.statusDiscovered;
      case MotifStatus.hidden:
        return Colors.white38;
    }
  }

  String _statusLabel(MotifStatus status) {
    switch (status) {
      case MotifStatus.mastered:
        return 'Thành thạo';
      case MotifStatus.learned:
        return 'Đã học';
      case MotifStatus.discovered:
        return 'Đã khám phá';
      case MotifStatus.hidden:
        return 'Chưa mở';
    }
  }
}
