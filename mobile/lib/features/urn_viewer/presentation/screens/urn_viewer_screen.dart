import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:model_viewer_plus/model_viewer_plus.dart';

import '../../../../core/theme/app_colors.dart';
import '../../domain/entities/urn.dart';
import '../providers/urn_provider.dart';
import '../widgets/discovery_animation.dart';
import '../widgets/hotspot_overlay.dart';
import '../widgets/motif_sidebar.dart';

/// 3D Urn Viewer Screen with hotspot interaction and motif discovery.
class UrnViewerScreen extends ConsumerStatefulWidget {
  final String urnSlug;

  const UrnViewerScreen({super.key, required this.urnSlug});

  @override
  ConsumerState<UrnViewerScreen> createState() => _UrnViewerScreenState();
}

class _UrnViewerScreenState extends ConsumerState<UrnViewerScreen>
    with TickerProviderStateMixin {
  bool _isLoading = true;
  bool _showHotspots = true;
  Motif? _selectedMotif;
  UnlockResult? _pendingDiscovery;
  bool _showDiscoveryAnimation = false;

  // Track camera position for hotspot positioning
  double _cameraRotationY = 0.0;
  double _cameraDistance = 5.0;

  @override
  void initState() {
    super.initState();
    // Set immersive mode for 3D viewer
    SystemChrome.setEnabledSystemUIMode(SystemUiMode.immersiveSticky);
  }

  @override
  void dispose() {
    // Restore system UI
    SystemChrome.setEnabledSystemUIMode(
      SystemUiMode.manual,
      overlays: SystemUiOverlay.values,
    );
    super.dispose();
  }

  Future<void> _handleHotspotTap(Motif motif) async {
    if (motif.isDiscovered) {
      // Already discovered - show sidebar
      setState(() => _selectedMotif = motif);
    } else {
      // Unlock the motif
      final result = await ref
          .read(discoveryNotifierProvider.notifier)
          .unlockMotif(motif.id);

      if (result != null && mounted) {
        setState(() {
          _pendingDiscovery = result;
          _showDiscoveryAnimation = true;
        });
      }
    }
  }

  void _onDiscoveryAnimationComplete() {
    setState(() {
      _showDiscoveryAnimation = false;
      if (_pendingDiscovery != null) {
        _selectedMotif = _pendingDiscovery!.motif;
        _pendingDiscovery = null;
      }
    });

    // Refresh the urn data to update hotspot states
    ref.invalidate(urnDetailProvider(widget.urnSlug));
  }

  void _closeSidebar() {
    setState(() => _selectedMotif = null);
  }

  void _navigateToLesson(Motif motif) {
    context.push('/motifs/${motif.id}/lesson');
  }

  void _navigateToQuiz(Motif motif) {
    context.push('/motifs/${motif.id}/quiz');
  }

  void _showUrnInfo(BuildContext context, UrnDetail urnDetail) {
    showModalBottomSheet(
      context: context,
      backgroundColor: Colors.transparent,
      builder: (context) => _buildUrnInfoSheet(urnDetail),
    );
  }

  @override
  Widget build(BuildContext context) {
    final urnAsync = ref.watch(urnDetailProvider(widget.urnSlug));

    return Scaffold(
      backgroundColor: Colors.black,
      extendBodyBehindAppBar: true,
      body: urnAsync.when(
        loading: () => _buildLoadingState(),
        error: (error, stack) => _buildErrorState(error.toString()),
        data: (urnDetail) => _buildViewerContent(urnDetail),
      ),
    );
  }

  Widget _buildLoadingState() {
    return const Center(
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          CircularProgressIndicator(color: AppColors.primary),
          SizedBox(height: 16),
          Text(
            'Đang tải...',
            style: TextStyle(color: Colors.white70),
          ),
        ],
      ),
    );
  }

  Widget _buildErrorState(String error) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Icon(Icons.error_outline, color: Colors.red, size: 64),
            const SizedBox(height: 16),
            Text(
              'Không thể tải mô hình',
              style: Theme.of(context).textTheme.headlineSmall?.copyWith(
                    color: Colors.white,
                  ),
            ),
            const SizedBox(height: 8),
            Text(
              error,
              textAlign: TextAlign.center,
              style: const TextStyle(color: Colors.white70),
            ),
            const SizedBox(height: 24),
            ElevatedButton.icon(
              onPressed: () {
                ref.invalidate(urnDetailProvider(widget.urnSlug));
              },
              icon: const Icon(Icons.refresh),
              label: const Text('Thử lại'),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildViewerContent(UrnDetail urnDetail) {
    final screenSize = MediaQuery.of(context).size;
    final sidebarWidth = screenSize.width * 0.85;

    return Stack(
      children: [
        // 3D Model Viewer - Full screen
        Positioned.fill(
          child: _build3DViewer(urnDetail),
        ),

        // Loading overlay
        if (_isLoading) _buildLoadingOverlay(),

        // Top controls
        Positioned(
          top: 0,
          left: 0,
          right: 0,
          child: _buildTopBar(urnDetail),
        ),

        // Hotspot overlays (positioned based on 3D coordinates)
        if (_showHotspots && !_isLoading)
          ...urnDetail.motifs.map(
            (motif) => HotspotOverlay(
              key: ValueKey(motif.id),
              motif: motif,
              screenSize: screenSize,
              cameraRotationY: _cameraRotationY,
              cameraDistance: _cameraDistance,
              onTap: () => _handleHotspotTap(motif),
            ),
          ),

        // Bottom info bar
        Positioned(
          left: 0,
          right: 0,
          bottom: 0,
          child: _buildBottomBar(urnDetail),
        ),

        // Motif sidebar
        AnimatedPositioned(
          duration: const Duration(milliseconds: 300),
          curve: Curves.easeInOut,
          right: _selectedMotif != null ? 0 : -sidebarWidth,
          top: 0,
          bottom: 0,
          width: sidebarWidth,
          child: _selectedMotif != null
              ? MotifSidebar(
                  motif: _selectedMotif!,
                  onClose: _closeSidebar,
                  onStartLesson: () => _navigateToLesson(_selectedMotif!),
                  onStartQuiz: () => _navigateToQuiz(_selectedMotif!),
                )
              : const SizedBox.shrink(),
        ),

        // Sidebar backdrop
        if (_selectedMotif != null)
          Positioned.fill(
            child: GestureDetector(
              onTap: _closeSidebar,
              child: Container(color: Colors.black.withOpacity(0.3)),
            ),
          ),

        // Discovery animation
        if (_showDiscoveryAnimation && _pendingDiscovery != null)
          Positioned.fill(
            child: DiscoveryAnimation(
              motif: _pendingDiscovery!.motif,
              xpEarned: _pendingDiscovery!.xpEarned,
              badgesEarned: _pendingDiscovery!.badgesEarned,
              onComplete: _onDiscoveryAnimationComplete,
            ),
          ),
      ],
    );
  }

  Widget _build3DViewer(UrnDetail urnDetail) {
    // Use remote URL for reliable model loading
    final modelPath = urnDetail.urn.effectiveModelUrl;

    debugPrint('[URN_VIEWER] Loading model from: $modelPath');

    // Set loading to false after model load delay
    if (_isLoading) {
      Future.delayed(const Duration(seconds: 3), () {
        if (mounted && _isLoading) {
          setState(() => _isLoading = false);
        }
      });
    }

    return ModelViewer(
      src: modelPath,
      alt: urnDetail.urn.name,
      ar: true, // Enable AR
      arModes: const ['scene-viewer', 'webxr', 'quick-look'],
      arScale: ArScale.auto,
      autoRotate: false,
      cameraControls: true,
      disableZoom: false,
      disablePan: false,
      disableTap: false,
      backgroundColor: const Color(0xFF1A1A1A),
      loading: Loading.eager,
      reveal: Reveal.auto,
      cameraOrbit: '0deg 75deg 5m',
      minCameraOrbit: 'auto auto 2m',
      maxCameraOrbit: 'auto auto 10m',
      fieldOfView: '45deg',
      interactionPrompt: InteractionPrompt.none,
      // Hotspot HTML for model-viewer (click detection)
      innerModelViewerHtml: _generateHotspotHtml(urnDetail.motifs),
      relatedJs: _generateHotspotJs(),
    );
  }

  String _generateHotspotHtml(List<Motif> motifs) {
    final buffer = StringBuffer();

    // Add CSS for hotspots
    buffer.writeln('''
      <style>
        .hotspot {
          display: block;
          width: 28px;
          height: 28px;
          border-radius: 50%;
          border: 3px solid white;
          background-color: rgba(212, 175, 55, 0.9);
          box-shadow: 0 0 10px rgba(212, 175, 55, 0.5);
          cursor: pointer;
          transition: transform 0.2s;
        }
        .hotspot:hover {
          transform: scale(1.2);
        }
        .hotspot.discovered {
          background-color: rgba(76, 175, 80, 0.9);
          box-shadow: 0 0 10px rgba(76, 175, 80, 0.5);
        }
        .hotspot.mastered {
          background-color: rgba(156, 39, 176, 0.9);
          box-shadow: 0 0 10px rgba(156, 39, 176, 0.5);
        }
        .hotspot-label {
          display: none;
          position: absolute;
          top: -30px;
          left: 50%;
          transform: translateX(-50%);
          white-space: nowrap;
          background: rgba(0,0,0,0.8);
          color: white;
          padding: 4px 8px;
          border-radius: 4px;
          font-size: 12px;
        }
        .hotspot:hover .hotspot-label {
          display: block;
        }
        @keyframes pulse {
          0%, 100% { transform: scale(1); }
          50% { transform: scale(1.3); }
        }
        .hotspot.undiscovered {
          animation: pulse 1.5s ease-in-out infinite;
        }
      </style>
    ''');

    // Add hotspot buttons
    for (final motif in motifs) {
      if (!motif.hasValidPosition) continue;

      String statusClass = 'undiscovered';
      if (motif.isMastered) {
        statusClass = 'mastered';
      } else if (motif.isDiscovered) {
        statusClass = 'discovered';
      }

      buffer.writeln('''
        <button class="hotspot $statusClass"
          slot="hotspot-${motif.id}"
          data-motif-id="${motif.id}"
          data-position="${motif.posX} ${motif.posY} ${motif.posZ}"
          data-normal="0 1 0">
          <span class="hotspot-label">${motif.name}</span>
        </button>
      ''');
    }

    return buffer.toString();
  }

  String _generateHotspotJs() {
    return '''
      // Add click handlers for hotspots
      document.querySelectorAll('.hotspot').forEach(hotspot => {
        hotspot.addEventListener('click', (e) => {
          e.stopPropagation();
          const motifId = hotspot.dataset.motifId;
          if (window.flutter_inappwebview) {
            window.flutter_inappwebview.callHandler('onHotspotClick', motifId);
          }
        });
      });

      // Track camera orbit changes
      const modelViewer = document.querySelector('model-viewer');
      if (modelViewer) {
        modelViewer.addEventListener('camera-change', (e) => {
          if (window.flutter_inappwebview) {
            const orbit = modelViewer.getCameraOrbit();
            window.flutter_inappwebview.callHandler('onCameraChange', {
              theta: orbit.theta,
              phi: orbit.phi,
              radius: orbit.radius
            });
          }
        });
      }
    ''';
  }

  Widget _buildTopBar(UrnDetail urnDetail) {
    return SafeArea(
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
        child: Row(
          children: [
            // Back button with glass effect
            _buildGlassIconButton(
              Icons.arrow_back,
              () => context.pop(),
              tooltip: 'Quay lại',
            ),

            const SizedBox(width: 8),

            // Title
            Expanded(
              child: Container(
                padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                decoration: BoxDecoration(
                  color: Colors.white.withOpacity(0.1),
                  borderRadius: BorderRadius.circular(20),
                  border: Border.all(
                    color: Colors.white.withOpacity(0.2),
                    width: 1,
                  ),
                ),
                child: Text(
                  urnDetail.urn.name,
                  style: const TextStyle(
                    color: Colors.white,
                    fontSize: 16,
                    fontWeight: FontWeight.bold,
                  ),
                  textAlign: TextAlign.center,
                  overflow: TextOverflow.ellipsis,
                ),
              ),
            ),

            const SizedBox(width: 8),

            // AR button
            _buildGlassIconButton(
              Icons.view_in_ar,
              () => _launchAR(urnDetail),
              tooltip: 'Xem AR',
              badge: 'AR',
            ),

            // Toggle hotspots
            _buildGlassIconButton(
              _showHotspots ? Icons.visibility : Icons.visibility_off,
              () => setState(() => _showHotspots = !_showHotspots),
              tooltip: _showHotspots ? 'Ẩn điểm nóng' : 'Hiện điểm nóng',
            ),

            // Info button
            _buildGlassIconButton(
              Icons.info_outline,
              () => _showUrnInfo(context, urnDetail),
              tooltip: 'Thông tin',
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildGlassIconButton(
    IconData icon,
    VoidCallback onPressed, {
    String? tooltip,
    String? badge,
  }) {
    return Container(
      decoration: BoxDecoration(
        color: Colors.white.withOpacity(0.1),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(
          color: Colors.white.withOpacity(0.2),
          width: 1,
        ),
      ),
      child: Stack(
        children: [
          IconButton(
            icon: Icon(icon, color: Colors.white, size: 22),
            onPressed: onPressed,
            tooltip: tooltip,
          ),
          if (badge != null)
            Positioned(
              right: 4,
              top: 4,
              child: Container(
                padding: const EdgeInsets.symmetric(horizontal: 4, vertical: 2),
                decoration: BoxDecoration(
                  color: const Color(0xFFD4A84B),
                  borderRadius: BorderRadius.circular(6),
                ),
                child: Text(
                  badge,
                  style: const TextStyle(
                    color: Color(0xFF1A1A2E),
                    fontSize: 8,
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ),
            ),
        ],
      ),
    );
  }

  void _launchAR(UrnDetail urnDetail) {
    // AR is already enabled in ModelViewer with ar: true
    // The model-viewer web component will handle AR launch
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Row(
          children: [
            const Icon(Icons.view_in_ar, color: Colors.white),
            const SizedBox(width: 12),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                mainAxisSize: MainAxisSize.min,
                children: [
                  const Text(
                    'Chế độ AR',
                    style: TextStyle(fontWeight: FontWeight.bold),
                  ),
                  Text(
                    'Nhấn vào nút AR trên mô hình 3D để xem trong không gian thực',
                    style: TextStyle(fontSize: 12),
                  ),
                ],
              ),
            ),
          ],
        ),
        backgroundColor: const Color(0xFF1A1A2E),
        behavior: SnackBarBehavior.floating,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(12),
          side: BorderSide(color: Colors.white.withOpacity(0.2)),
        ),
        duration: const Duration(seconds: 3),
      ),
    );
  }

  Widget _buildBottomBar(UrnDetail urnDetail) {
    final discovered = urnDetail.urn.discoveredCount;
    final total = urnDetail.urn.motifCount;
    final progress = total > 0 ? discovered / total : 0.0;

    return Container(
      padding: EdgeInsets.only(
        left: 16,
        right: 16,
        top: 12,
        bottom: MediaQuery.of(context).padding.bottom + 12,
      ),
      decoration: BoxDecoration(
        gradient: LinearGradient(
          begin: Alignment.topCenter,
          end: Alignment.bottomCenter,
          colors: [
            Colors.transparent,
            Colors.black.withOpacity(0.8),
          ],
        ),
      ),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          // Progress bar
          ClipRRect(
            borderRadius: BorderRadius.circular(4),
            child: LinearProgressIndicator(
              value: progress,
              backgroundColor: Colors.white24,
              valueColor: const AlwaysStoppedAnimation<Color>(AppColors.primary),
              minHeight: 6,
            ),
          ),
          const SizedBox(height: 8),

          // Stats row
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceEvenly,
            children: [
              _buildStatItem(
                icon: Icons.explore,
                label: 'Khám phá',
                value: '$discovered/$total',
                color: AppColors.statusDiscovered,
              ),
              _buildStatItem(
                icon: Icons.school,
                label: 'Học xong',
                value: '${urnDetail.urn.learnedCount}',
                color: AppColors.statusLearned,
              ),
              _buildStatItem(
                icon: Icons.star,
                label: 'Thành thạo',
                value: '${urnDetail.urn.masteredCount}',
                color: AppColors.statusMastered,
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildStatItem({
    required IconData icon,
    required String label,
    required String value,
    required Color color,
  }) {
    return Column(
      mainAxisSize: MainAxisSize.min,
      children: [
        Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(icon, color: color, size: 16),
            const SizedBox(width: 4),
            Text(
              value,
              style: TextStyle(
                color: color,
                fontWeight: FontWeight.bold,
                fontSize: 16,
              ),
            ),
          ],
        ),
        const SizedBox(height: 2),
        Text(
          label,
          style: const TextStyle(
            color: Colors.white70,
            fontSize: 11,
          ),
        ),
      ],
    );
  }

  Widget _buildLoadingOverlay() {
    return Container(
      color: Colors.black87,
      child: const Center(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            CircularProgressIndicator(color: AppColors.primary),
            SizedBox(height: 24),
            Text(
              'Đang tải mô hình 3D...',
              style: TextStyle(
                color: Colors.white,
                fontSize: 16,
              ),
            ),
            SizedBox(height: 8),
            Text(
              'Vui lòng chờ trong giây lát',
              style: TextStyle(
                color: Colors.white60,
                fontSize: 14,
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildUrnInfoSheet(UrnDetail urnDetail) {
    return Container(
      padding: const EdgeInsets.all(24),
      decoration: const BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Handle
          Center(
            child: Container(
              width: 40,
              height: 4,
              decoration: BoxDecoration(
                color: Colors.grey[300],
                borderRadius: BorderRadius.circular(2),
              ),
            ),
          ),
          const SizedBox(height: 24),

          // Title
          Text(
            urnDetail.urn.name,
            style: Theme.of(context).textTheme.headlineSmall?.copyWith(
                  fontWeight: FontWeight.bold,
                ),
          ),
          if (urnDetail.urn.nameEn != null) ...[
            const SizedBox(height: 4),
            Text(
              urnDetail.urn.nameEn!,
              style: Theme.of(context).textTheme.titleMedium?.copyWith(
                    color: Colors.grey[600],
                  ),
            ),
          ],
          const SizedBox(height: 16),

          // Description
          if (urnDetail.urn.description != null)
            Text(
              urnDetail.urn.description!,
              style: Theme.of(context).textTheme.bodyMedium,
            ),

          const SizedBox(height: 24),

          // Stats
          Row(
            children: [
              Expanded(
                child: _buildInfoStat(
                  'Tổng họa tiết',
                  '${urnDetail.urn.motifCount}',
                  Icons.grid_view,
                ),
              ),
              Expanded(
                child: _buildInfoStat(
                  'Đã khám phá',
                  '${urnDetail.urn.discoveredCount}',
                  Icons.explore,
                ),
              ),
              Expanded(
                child: _buildInfoStat(
                  'Tiến độ',
                  '${(urnDetail.urn.progress * 100).toInt()}%',
                  Icons.trending_up,
                ),
              ),
            ],
          ),

          const SizedBox(height: 24),
        ],
      ),
    );
  }

  Widget _buildInfoStat(String label, String value, IconData icon) {
    return Column(
      children: [
        Icon(icon, color: AppColors.primary, size: 28),
        const SizedBox(height: 8),
        Text(
          value,
          style: const TextStyle(
            fontSize: 20,
            fontWeight: FontWeight.bold,
          ),
        ),
        const SizedBox(height: 4),
        Text(
          label,
          style: TextStyle(
            fontSize: 12,
            color: Colors.grey[600],
          ),
        ),
      ],
    );
  }
}
