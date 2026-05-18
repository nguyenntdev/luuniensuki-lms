import 'dart:async';
import 'dart:convert';
import 'dart:io';

import 'package:device_info_plus/device_info_plus.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../../core/theme/app_colors.dart';
import '../../../../core/theme/app_typography.dart';
import '../../../../core/utils/url_utils.dart';
import '../../../../routing/route_names.dart';
import '../../domain/entities/urn.dart';
import '../providers/urn_provider.dart';
import '../widgets/custom_model_viewer.dart';
import '../widgets/discovery_animation.dart';
import '../widgets/motif_sidebar.dart';

enum ModelQuality {
  low,
  medium,
  high,
}

class _ModelSelection {
  final String url;
  final ModelQuality quality;
  final bool isLocal;
  final List<String> fallbackUrls;

  const _ModelSelection({
    required this.url,
    required this.quality,
    required this.isLocal,
    required this.fallbackUrls,
  });
}

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
  bool _modelLoadError = false;
  String? _errorMessage;
  Motif? _selectedMotif;
  UnlockResult? _pendingDiscovery;
  bool _showDiscoveryAnimation = false;

  String? _resolvedModelUrl;
  ModelQuality? _modelQuality;
  bool _isResolvingModel = false;
  List<String> _modelFallbackUrls = [];
  int _modelFallbackIndex = 0;

  static const String _motifCoordinateAsset =
      'assets/data/motif-coordinates-cao-dinh.json';
  final Map<String, _MotifCoordinate> _motifCoordinates = {};
  bool _motifCoordinatesLoaded = false;

  // Timer for model loading timeout
  Timer? _loadingTimer;

  // Debug tracking
  double _modelLoadProgress = 0.0;
  String? _debugInfo;
  bool _isOnline = true;
  DateTime? _loadStartTime;

  @override
  void initState() {
    super.initState();

    _loadStartTime = DateTime.now();

    debugPrint('[URN_VIEWER] ═══════════════════════════════════════');
    debugPrint('[URN_VIEWER] === 3D VIEWER DEBUG START ===');
    debugPrint('[URN_VIEWER] Screen initializing for slug: ${widget.urnSlug}');
    debugPrint('[URN_VIEWER] Timestamp: ${DateTime.now().toIso8601String()}');
    debugPrint('[URN_VIEWER] ═══════════════════════════════════════');

    // Check network connectivity
    _checkConnectivity();
    _loadMotifCoordinates();

    // Set immersive mode for 3D viewer
    SystemChrome.setEnabledSystemUIMode(SystemUiMode.immersiveSticky);

    // Extended timeout for model loading (60 seconds)
    // After timeout, just hide the loading overlay but keep model loading in background
    // Only show error if there's an actual error event from ModelViewer
    _loadingTimer = Timer(const Duration(seconds: 60), () {
      if (mounted && _isLoading) {
        final elapsed = DateTime.now().difference(_loadStartTime!).inSeconds;
        setState(() {
          _isLoading = false;
          // Don't set error state - let the model continue loading
        });
        debugPrint('[URN_VIEWER] ⚠️ Model loading timeout after $elapsed seconds - continuing in background');
        debugPrint('[URN_VIEWER] Last progress: ${(_modelLoadProgress * 100).toInt()}%');
      }
    });
  }

  /// Check network connectivity before loading model
  Future<void> _checkConnectivity() async {
    try {
      // Simple connectivity check using socket
      final result = await InternetAddress.lookup('google.com')
          .timeout(const Duration(seconds: 5));
      _isOnline = result.isNotEmpty && result[0].rawAddress.isNotEmpty;
      debugPrint('[URN_VIEWER] Network connectivity check: ${_isOnline ? "✅ Online" : "❌ Offline"}');
    } catch (e) {
      _isOnline = false;
      debugPrint('[URN_VIEWER] ❌ Network connectivity check failed: $e');
      if (mounted) {
        setState(() {
          _errorMessage = 'Không có kết nối Internet. Vui lòng kiểm tra và thử lại.';
        });
      }
    }
  }

  Future<void> _loadMotifCoordinates() async {
    if (_motifCoordinatesLoaded) {
      return;
    }
    try {
      final raw = await rootBundle.loadString(_motifCoordinateAsset);
      final decoded = jsonDecode(raw);
      if (decoded is! List) {
        throw const FormatException('Expected list of motif coordinates');
      }
      for (final entry in decoded) {
        if (entry is! Map) {
          continue;
        }
        final motifName = (entry['motif_name'] ?? '').toString();
        final meshName = (entry['mesh_name'] ?? '').toString();
        final posX = (entry['pos_x'] as num?)?.toDouble();
        final posY = (entry['pos_y'] as num?)?.toDouble();
        final posZ = (entry['pos_z'] as num?)?.toDouble();
        final boundingRadius = (entry['bounding_radius'] as num?)?.toDouble();
        if (motifName.isEmpty && meshName.isEmpty) {
          continue;
        }
        if (posX == null || posY == null || posZ == null || boundingRadius == null) {
          continue;
        }
        final coordinate = _MotifCoordinate(
          motifName: motifName,
          meshName: meshName,
          posX: posX,
          posY: posY,
          posZ: posZ,
          boundingRadius: boundingRadius,
        );
        final primaryKey = _normalizeMotifKey(motifName.isNotEmpty ? motifName : meshName);
        _motifCoordinates[primaryKey] = coordinate;
        if (meshName.isNotEmpty) {
          _motifCoordinates[_normalizeMotifKey(meshName)] = coordinate;
        }
      }
      _motifCoordinatesLoaded = true;
      if (mounted) {
        setState(() {});
      }
      debugPrint('[URN_VIEWER] ✅ Loaded motif coordinates: ${_motifCoordinates.length}');
    } catch (e) {
      _motifCoordinatesLoaded = true;
      debugPrint('[URN_VIEWER] ❌ Failed to load motif coordinates: $e');
    }
  }

  String _normalizeMotifKey(String value) {
    return value.trim().toLowerCase();
  }

  List<Motif> _applyMotifCoordinates(UrnDetail urnDetail) {
    if (urnDetail.urn.slug != 'cao-dinh' || _motifCoordinates.isEmpty) {
      return urnDetail.motifs;
    }
    return urnDetail.motifs.map((motif) {
      final nameKey = _normalizeMotifKey(motif.name);
      final meshKey = _normalizeMotifKey(motif.meshName);
      final coordinate = _motifCoordinates[nameKey] ?? _motifCoordinates[meshKey];
      if (coordinate == null) {
        return motif;
      }
      return motif.copyWith(
        posX: coordinate.posX,
        posY: coordinate.posY,
        posZ: coordinate.posZ,
        boundingRadius: coordinate.boundingRadius,
      );
    }).toList();
  }

  @override
  void dispose() {
    debugPrint('[URN_VIEWER] Screen disposing for slug: ${widget.urnSlug}');

    // Cancel the loading timer to prevent memory leak
    _loadingTimer?.cancel();

    // Restore system UI
    SystemChrome.setEnabledSystemUIMode(
      SystemUiMode.manual,
      overlays: SystemUiOverlay.values,
    );

    debugPrint('[URN_VIEWER] === 3D VIEWER DEBUG END ===');
    super.dispose();
  }

  Future<void> _resolveModelUrl(UrnDetail urnDetail) async {
    if (_isResolvingModel || _resolvedModelUrl != null) {
      return;
    }

    _isResolvingModel = true;
    final selection = await _selectModelUrl(urnDetail);
    if (!mounted) {
      return;
    }

    setState(() {
      _resolvedModelUrl = selection.url;
      _modelQuality = selection.quality;
      _modelFallbackUrls = selection.fallbackUrls;
      _modelFallbackIndex = 0;
      _isResolvingModel = false;
    });
  }

  Future<_ModelSelection> _selectModelUrl(UrnDetail urnDetail) async {
    final baseUrl = urnDetail.urn.remoteModelUrl;
    final deviceInfo = DeviceInfoPlugin();
    bool isLowRamDevice = false;
    int? totalMemMb;

    if (Platform.isAndroid) {
      final androidInfo = await deviceInfo.androidInfo;
      isLowRamDevice = androidInfo.isLowRamDevice;
      totalMemMb = await _readAndroidTotalMemoryMb();

      debugPrint('[URN_VIEWER] Device: ${androidInfo.manufacturer} ${androidInfo.model}');
      debugPrint('[URN_VIEWER] SDK: ${androidInfo.version.sdkInt}');
      debugPrint('[URN_VIEWER] Low RAM: $isLowRamDevice');
      if (totalMemMb != null) {
        debugPrint('[URN_VIEWER] Total RAM: ${totalMemMb}MB');
      }
    }

    final quality = _chooseModelQuality(
      totalMemMb: totalMemMb,
      isLowRamDevice: isLowRamDevice,
    );

    final normalizedBaseUrl = UrlUtils.toFullUrl(baseUrl) ?? baseUrl;
    final candidates = _buildModelCandidates(
      baseUrl: normalizedBaseUrl,
      includeQualityVariants: urnDetail.urn.slug == 'cao-dinh',
      quality: quality,
    );
    final selectedUrl =
        candidates.isNotEmpty ? candidates.first : normalizedBaseUrl;
    final fallbackUrls =
        candidates.length > 1 ? candidates.sublist(1) : const <String>[];

    debugPrint('[URN_VIEWER] Selected model quality: $quality');
    debugPrint('[URN_VIEWER] Primary model URL: $selectedUrl');
    debugPrint('[URN_VIEWER] Fallback model URLs: $fallbackUrls');
    return _ModelSelection(
      url: selectedUrl,
      quality: quality,
      isLocal: false,
      fallbackUrls: fallbackUrls,
    );
  }

  ModelQuality _chooseModelQuality({
    required int? totalMemMb,
    required bool isLowRamDevice,
  }) {
    if (isLowRamDevice) {
      return ModelQuality.low;
    }
    if (totalMemMb != null) {
      if (totalMemMb <= 3072) {
        return ModelQuality.low;
      }
      if (totalMemMb <= 4096) {
        return ModelQuality.medium;
      }
      return ModelQuality.high;
    }
    return ModelQuality.medium;
  }

  Future<int?> _readAndroidTotalMemoryMb() async {
    if (!Platform.isAndroid) {
      return null;
    }

    try {
      final data = await File('/proc/meminfo').readAsString();
      final match = RegExp(r'^MemTotal:\s+(\d+) kB', multiLine: true).firstMatch(data);
      if (match == null) {
        return null;
      }
      final totalKb = int.tryParse(match.group(1) ?? '');
      if (totalKb == null) {
        return null;
      }
      return totalKb ~/ 1024;
    } catch (e) {
      debugPrint('[URN_VIEWER] Failed to read /proc/meminfo: $e');
      return null;
    }
  }

  String _applyQualitySuffix(String url, ModelQuality quality) {
    final suffix = switch (quality) {
      ModelQuality.low => '-512',
      ModelQuality.medium => '-1k',
      ModelQuality.high => '-2k',
    };
    final uri = Uri.parse(url);
    final path = uri.path;
    if (!path.toLowerCase().endsWith('.glb')) {
      return url;
    }

    final updatedPath =
        path.replaceFirst(RegExp(r'\.glb$', caseSensitive: false), '$suffix.glb');
    return uri.replace(path: updatedPath).toString();
  }

  List<String> _buildModelCandidates({
    required String baseUrl,
    required bool includeQualityVariants,
    required ModelQuality quality,
  }) {
    final candidates = <String>[];

    void addCandidate(String? url) {
      if (url == null || url.isEmpty) {
        return;
      }

      final normalized = UrlUtils.toFullUrl(url) ?? url;
      if (!candidates.contains(normalized)) {
        candidates.add(normalized);
      }

      final apiAssetVariant = _toApiAssetsVariant(normalized);
      if (apiAssetVariant != null && !candidates.contains(apiAssetVariant)) {
        candidates.add(apiAssetVariant);
      }
    }

    // Reliability-first: start with the base URL, then try alternates.
    addCandidate(baseUrl);

    if (includeQualityVariants) {
      addCandidate(_applyQualitySuffix(baseUrl, quality));
      for (final variant in ModelQuality.values) {
        if (variant == quality) {
          continue;
        }
        addCandidate(_applyQualitySuffix(baseUrl, variant));
      }
    }

    return candidates;
  }

  String? _toApiAssetsVariant(String absoluteUrl) {
    final uri = Uri.tryParse(absoluteUrl);
    if (uri == null || uri.host.isEmpty) {
      return null;
    }

    final path = uri.path;
    if (!path.startsWith('/assets/')) {
      return null;
    }

    return uri.replace(path: '/api$path').toString();
  }

  Future<void> _handleHotspotTap(Motif motif) async {
    if (motif.isDiscovered) {
      _openMotifDetail(motif);
      return;
    }

    final result = await ref
        .read(discoveryNotifierProvider.notifier)
        .unlockMotif(motif.id);

    if (result != null && mounted) {
      setState(() {
        _pendingDiscovery = result;
        _showDiscoveryAnimation = true;
      });
      return;
    }

    // Fallback: still open detail even if unlock failed.
    if (mounted) {
      _openMotifDetail(motif);
    }
  }

  void _onDiscoveryAnimationComplete() {
    final discoveredMotif = _pendingDiscovery?.motif;
    setState(() {
      _showDiscoveryAnimation = false;
      _pendingDiscovery = null;
    });

    if (discoveredMotif != null) {
      _openMotifDetail(discoveredMotif);
    }

    // Refresh the urn data to update hotspot states
    ref.invalidate(urnDetailProvider(widget.urnSlug));
  }

  void _closeSidebar() {
    setState(() => _selectedMotif = null);
  }

  void _openMotifDetail(Motif motif) {
    context.push(RoutePaths.motif(motif.id));
  }

  void _navigateToLesson(Motif motif) {
    context.push(RoutePaths.lesson(motif.id));
  }

  void _navigateToQuiz(Motif motif) {
    context.push(RoutePaths.quiz(motif.id));
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
    final motifs = _applyMotifCoordinates(urnDetail);

    // Log urn details on first build
    debugPrint('[URN_VIEWER] ───────────────────────────────────────');
    debugPrint('[URN_VIEWER] Building viewer content');
    debugPrint('[URN_VIEWER] Urn ID: ${urnDetail.urn.id}');
    debugPrint('[URN_VIEWER] Urn Name: ${urnDetail.urn.name}');
    debugPrint('[URN_VIEWER] Urn Slug: ${urnDetail.urn.slug}');
    debugPrint('[URN_VIEWER] Model URL from API: ${urnDetail.urn.modelUrl}');
    debugPrint('[URN_VIEWER] Effective Model URL: ${urnDetail.urn.effectiveModelUrl}');
    debugPrint('[URN_VIEWER] Motif count: ${urnDetail.motifs.length}');
    debugPrint('[URN_VIEWER] Discovered count: ${urnDetail.urn.discoveredCount}');
    debugPrint('[URN_VIEWER] Network status: ${_isOnline ? "Online" : "Offline"}');
    debugPrint('[URN_VIEWER] ───────────────────────────────────────');

    // Build debug info string
    _debugInfo = _buildDebugInfoString(urnDetail);

    return Stack(
      children: [
        // 3D Model Viewer - Full screen
        Positioned.fill(
          child: _build3DViewer(urnDetail, motifs),
        ),

        // Loading overlay
        if (_isLoading && !_modelLoadError) _buildLoadingOverlay(),

        // Model load error overlay
        if (_modelLoadError) _buildModelErrorOverlay(),

        // Top controls
        Positioned(
          top: 0,
          left: 0,
          right: 0,
          child: _buildTopBar(urnDetail),
        ),

        // Hotspots are rendered inside the 3D viewer to avoid overlay issues.

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

  Widget _build3DViewer(UrnDetail urnDetail, List<Motif> motifs) {
    if (_resolvedModelUrl == null) {
      _resolveModelUrl(urnDetail);
      return Container(
        color: const Color(0xFF1A1A2E),
        child: const Center(
          child: CircularProgressIndicator(
            valueColor: AlwaysStoppedAnimation<Color>(AppColors.primary),
          ),
        ),
      );
    }

    final modelPath = _resolvedModelUrl!;
    final allowAutoRotate = _modelQuality != ModelQuality.low;

    // Verify model URL format
    _verifyModelUrl(modelPath, urnDetail);

    debugPrint('[URN_VIEWER] ┌─────────────────────────────────────');
    debugPrint('[URN_VIEWER] │ Starting 3D Model Load');
    debugPrint('[URN_VIEWER] │ Model URL: $modelPath');
    debugPrint('[URN_VIEWER] │ URL is valid: ${Uri.tryParse(modelPath) != null}');
    debugPrint('[URN_VIEWER] │ Loading state: $_isLoading');
    debugPrint('[URN_VIEWER] │ Error state: $_modelLoadError');
    debugPrint('[URN_VIEWER] │ Progress: ${(_modelLoadProgress * 100).toInt()}%');
    debugPrint('[URN_VIEWER] └─────────────────────────────────────');

    return CustomModelViewer(
      modelUrl: modelPath,
      alt: urnDetail.urn.name,
      hotspots: _showHotspots ? motifs : const [],
      backgroundColor: const Color(0xFF1A1A2E),
      autoRotate: false,
      cameraControls: true,
      disableZoom: false,
      onModelLoaded: () {
        debugPrint('[URN_VIEWER] ✅ Model loaded successfully via CustomModelViewer');
        if (mounted) {
          setState(() {
            _isLoading = false;
            _modelLoadError = false;
            _errorMessage = null;
          });
        }
      },
      onModelError: (error) {
        debugPrint('[URN_VIEWER] ❌ Model load error: $error');
        if (_modelFallbackIndex < _modelFallbackUrls.length) {
          final fallbackUrl = _modelFallbackUrls[_modelFallbackIndex];
          _modelFallbackIndex += 1;
          debugPrint('[URN_VIEWER] ⚠️ Falling back to: $fallbackUrl');
          setState(() {
            _resolvedModelUrl = fallbackUrl;
            _isLoading = true;
            _modelLoadError = false;
            _errorMessage = null;
          });
          return;
        }
        if (mounted) {
          setState(() {
            _isLoading = false;
            _modelLoadError = true;
            _errorMessage = error;
          });
        }
      },
      onProgress: (progress) {
        if (mounted) {
          setState(() {
            _modelLoadProgress = progress / 100.0;
            if (progress >= 100 && _isLoading) {
              _isLoading = false;
              _modelLoadError = false;
              _errorMessage = null;
            }
          });
        }
      },
      onHotspotTap: (motifId) {
        debugPrint('[URN_VIEWER] 🎯 Hotspot tapped: $motifId');
        Motif? motif;
        try {
          motif = motifs.firstWhere((m) => m.id == motifId);
        } catch (_) {
          debugPrint('[URN_VIEWER] ⚠️ Hotspot motif not found: $motifId');
        }
        if (motif == null) {
          return;
        }
        _handleHotspotTap(motif);
      },
    );
  }

  /// Verify and log model URL details
  void _verifyModelUrl(String modelPath, UrnDetail urnDetail) {
    debugPrint('[URN_VIEWER] 🔍 Model URL Verification:');
    debugPrint('[URN_VIEWER]   Raw model URL: ${urnDetail.urn.modelUrl}');
    debugPrint('[URN_VIEWER]   Effective URL: $modelPath');
    if (_modelQuality != null) {
      debugPrint('[URN_VIEWER]   Selected quality: $_modelQuality');
    }

    final uri = Uri.tryParse(modelPath);
    if (uri != null) {
      debugPrint('[URN_VIEWER]   ✅ URL is valid');
      debugPrint('[URN_VIEWER]   Scheme: ${uri.scheme}');
      debugPrint('[URN_VIEWER]   Host: ${uri.host}');
      debugPrint('[URN_VIEWER]   Path: ${uri.path}');
      debugPrint('[URN_VIEWER]   Extension: ${uri.path.split('.').last}');
    } else {
      debugPrint('[URN_VIEWER]   ❌ URL is INVALID!');
    }
  }

  /// Build debug info string for copying
  String _buildDebugInfoString(UrnDetail urnDetail) {
    final buffer = StringBuffer();
    buffer.writeln('=== URN VIEWER DEBUG INFO ===');
    buffer.writeln('Timestamp: ${DateTime.now().toIso8601String()}');
    buffer.writeln('Urn ID: ${urnDetail.urn.id}');
    buffer.writeln('Urn Slug: ${urnDetail.urn.slug}');
    buffer.writeln('Urn Name: ${urnDetail.urn.name}');
    buffer.writeln('Model URL: ${urnDetail.urn.modelUrl}');
    buffer.writeln('Effective URL: ${urnDetail.urn.effectiveModelUrl}');
    buffer.writeln('Motif Count: ${urnDetail.motifs.length}');
    buffer.writeln('Discovered: ${urnDetail.urn.discoveredCount}');
    buffer.writeln('Network: ${_isOnline ? "Online" : "Offline"}');
    buffer.writeln('Loading: $_isLoading');
    buffer.writeln('Error: $_modelLoadError');
    buffer.writeln('Progress: ${(_modelLoadProgress * 100).toInt()}%');
    if (_errorMessage != null) {
      buffer.writeln('Error Message: $_errorMessage');
    }
    if (_loadStartTime != null) {
      final elapsed = DateTime.now().difference(_loadStartTime!);
      buffer.writeln('Time Elapsed: ${elapsed.inSeconds}s');
    }
    buffer.writeln('Platform: ${Platform.operatingSystem} ${Platform.operatingSystemVersion}');
    buffer.writeln('===========================');
    return buffer.toString();
  }

  Widget _buildTopBar(UrnDetail urnDetail) {
    final screenWidth = MediaQuery.of(context).size.width;
    final isCompact = screenWidth < 360;
    final titleStyle = AppTypography.textTheme.titleMedium?.copyWith(
      color: Colors.white,
      fontSize: isCompact ? 14 : 16,
      fontWeight: FontWeight.bold,
    );

    return SafeArea(
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
        child: isCompact
            ? Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  Row(
                    children: [
                      _buildGlassIconButton(
                        Icons.arrow_back,
                        () => context.pop(),
                        tooltip: 'Quay lại',
                        iconSize: 20,
                      ),
                      const SizedBox(width: 8),
                      Expanded(
                        child: Container(
                          padding: const EdgeInsets.symmetric(
                            horizontal: 12,
                            vertical: 6,
                          ),
                          decoration: BoxDecoration(
                            color: Colors.white.withOpacity(0.1),
                            borderRadius: BorderRadius.circular(16),
                            border: Border.all(
                              color: Colors.white.withOpacity(0.2),
                              width: 1,
                            ),
                          ),
                          child: Text(
                            urnDetail.urn.name,
                            style: titleStyle,
                            textAlign: TextAlign.center,
                            overflow: TextOverflow.ellipsis,
                          ),
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 8),
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceEvenly,
                    children: [
                      _buildGlassIconButton(
                        Icons.view_in_ar,
                        () => _launchAR(urnDetail),
                        tooltip: 'Xem AR',
                        badge: 'AR',
                        iconSize: 20,
                      ),
                      _buildGlassIconButton(
                        _showHotspots ? Icons.visibility : Icons.visibility_off,
                        () => setState(() => _showHotspots = !_showHotspots),
                        tooltip: _showHotspots ? 'Ẩn điểm nóng' : 'Hiện điểm nóng',
                        iconSize: 20,
                      ),
                      _buildGlassIconButton(
                        Icons.info_outline,
                        () => _showUrnInfo(context, urnDetail),
                        tooltip: 'Thông tin',
                        iconSize: 20,
                      ),
                    ],
                  ),
                ],
              )
            : Row(
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
                      padding: const EdgeInsets.symmetric(
                        horizontal: 16,
                        vertical: 8,
                      ),
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
                        style: titleStyle,
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
    double iconSize = 22,
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
            icon: Icon(icon, color: Colors.white, size: iconSize),
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
                  color: AppColors.primary,
                  borderRadius: BorderRadius.circular(6),
                ),
                child: Text(
                  badge,
                  style: const TextStyle(
                    color: AppColors.onPrimary,
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
        backgroundColor: AppColors.surface,
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
    final screenWidth = MediaQuery.of(context).size.width;
    final isCompact = screenWidth < 360;

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
          if (isCompact)
            Wrap(
              alignment: WrapAlignment.center,
              spacing: 16,
              runSpacing: 8,
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
            )
          else
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
    final progressPercent = (_modelLoadProgress * 100).toInt();

    return Container(
      color: Colors.black87,
      child: Center(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const CircularProgressIndicator(color: AppColors.primary),
            const SizedBox(height: 24),
            const Text(
              'Đang tải mô hình 3D...',
              style: TextStyle(
                color: Colors.white,
                fontSize: 18,
                fontWeight: FontWeight.bold,
              ),
            ),
            const SizedBox(height: 12),
            Text(
              progressPercent > 0 ? '$progressPercent%' : 'Vui lòng đợi',
              style: const TextStyle(
                color: Colors.white70,
                fontSize: 15,
              ),
            ),
            const SizedBox(height: 20),
            const Padding(
              padding: EdgeInsets.symmetric(horizontal: 32),
              child: Text(
                'Thiết bị yếu có thể mất nhiều thời gian hơn',
                style: TextStyle(
                  color: Colors.white54,
                  fontSize: 13,
                  fontStyle: FontStyle.italic,
                ),
                textAlign: TextAlign.center,
              ),
            ),
            if (!_isOnline) ...[
              const SizedBox(height: 16),
              Container(
                margin: const EdgeInsets.symmetric(horizontal: 32),
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: Colors.orange.withOpacity(0.2),
                  borderRadius: BorderRadius.circular(8),
                  border: Border.all(color: Colors.orange),
                ),
                child: const Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Icon(Icons.warning_amber, color: Colors.orange, size: 20),
                    SizedBox(width: 8),
                    Expanded(
                      child: Text(
                        'Không có kết nối mạng',
                        style: TextStyle(color: Colors.orange, fontSize: 13),
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ],
        ),
      ),
    );
  }

  Widget _buildModelErrorOverlay() {
    return Container(
      color: Colors.black87,
      child: Center(
        child: Padding(
          padding: const EdgeInsets.all(32),
          child: SingleChildScrollView(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                // Error icon
                Container(
                  padding: const EdgeInsets.all(20),
                  decoration: BoxDecoration(
                    color: Colors.red.withOpacity(0.2),
                    shape: BoxShape.circle,
                  ),
                  child: const Icon(
                    Icons.error_outline,
                    color: Colors.red,
                    size: 64,
                  ),
                ),
                const SizedBox(height: 24),

                // Error title
                const Text(
                  'Không thể tải mô hình 3D',
                  style: TextStyle(
                    color: Colors.white,
                    fontSize: 20,
                    fontWeight: FontWeight.bold,
                  ),
                  textAlign: TextAlign.center,
                ),
                const SizedBox(height: 12),

                // Error message
                Text(
                  _errorMessage ??
                      'Đã xảy ra lỗi khi tải mô hình. Vui lòng kiểm tra kết nối mạng.',
                  style: const TextStyle(
                    color: Colors.white70,
                    fontSize: 14,
                  ),
                  textAlign: TextAlign.center,
                ),
                const SizedBox(height: 24),

                // Debug info (in debug mode)
                if (_debugInfo != null) ...[
                  Container(
                    padding: const EdgeInsets.all(12),
                    decoration: BoxDecoration(
                      color: Colors.black.withOpacity(0.3),
                      borderRadius: BorderRadius.circular(8),
                      border: Border.all(color: Colors.white24),
                    ),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        const Row(
                          children: [
                            Icon(Icons.bug_report, color: Colors.orange, size: 16),
                            SizedBox(width: 8),
                            Text(
                              'Thông tin gỡ lỗi',
                              style: TextStyle(
                                color: Colors.orange,
                                fontSize: 12,
                                fontWeight: FontWeight.bold,
                              ),
                            ),
                          ],
                        ),
                        const SizedBox(height: 8),
                        Text(
                          _debugInfo!,
                          style: const TextStyle(
                            color: Colors.white60,
                            fontSize: 10,
                            fontFamily: 'monospace',
                          ),
                        ),
                      ],
                    ),
                  ),
                  const SizedBox(height: 16),

                  // Copy debug info button
                  OutlinedButton.icon(
                    onPressed: () {
                      Clipboard.setData(ClipboardData(text: _debugInfo!));
                      ScaffoldMessenger.of(context).showSnackBar(
                        const SnackBar(
                          content: Text('Đã sao chép thông tin gỡ lỗi'),
                          duration: Duration(seconds: 2),
                        ),
                      );
                      debugPrint('[URN_VIEWER] 📋 Debug info copied to clipboard');
                    },
                    icon: const Icon(Icons.copy, size: 16),
                    label: const Text('Sao chép thông tin gỡ lỗi'),
                    style: OutlinedButton.styleFrom(
                      foregroundColor: Colors.orange,
                      side: const BorderSide(color: Colors.orange),
                    ),
                  ),
                  const SizedBox(height: 8),
                ],

                // Retry button
                ElevatedButton.icon(
                  onPressed: () {
                    debugPrint('[URN_VIEWER] 🔄 User initiated retry');
                    setState(() {
                      _isLoading = true;
                      _modelLoadError = false;
                      _errorMessage = null;
                      _modelLoadProgress = 0.0;
                      _loadStartTime = DateTime.now();
                    });
                    // Refresh the urn data
                    ref.invalidate(urnDetailProvider(widget.urnSlug));
                    // Reset timeout (60 seconds)
                    _loadingTimer?.cancel();
                    _loadingTimer = Timer(const Duration(seconds: 60), () {
                      if (mounted && _isLoading) {
                        final elapsed = DateTime.now().difference(_loadStartTime!).inSeconds;
                        setState(() {
                          _isLoading = false;
                          // Don't set error state - let the model continue loading
                        });
                        debugPrint('[URN_VIEWER] ⚠️ Model loading timeout after $elapsed seconds - continuing in background');
                      }
                    });
                  },
                  icon: const Icon(Icons.refresh),
                  label: const Text('Thử lại'),
                  style: ElevatedButton.styleFrom(
                    backgroundColor: AppColors.primary,
                    foregroundColor: AppColors.onPrimary,
                    padding: const EdgeInsets.symmetric(
                      horizontal: 32,
                      vertical: 16,
                    ),
                    textStyle: const TextStyle(
                      fontSize: 16,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                ),
                const SizedBox(height: 16),

                // Back button
                TextButton.icon(
                  onPressed: () => context.pop(),
                  icon: const Icon(Icons.arrow_back),
                  label: const Text('Quay lại'),
                  style: TextButton.styleFrom(
                    foregroundColor: Colors.white70,
                  ),
                ),

                const SizedBox(height: 24),

                // Troubleshooting tips
                Container(
                  padding: const EdgeInsets.all(16),
                  decoration: BoxDecoration(
                    color: Colors.white.withOpacity(0.05),
                    borderRadius: BorderRadius.circular(12),
                    border: Border.all(
                      color: Colors.white.withOpacity(0.1),
                    ),
                  ),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Text(
                        'Gợi ý khắc phục:',
                        style: TextStyle(
                          color: Colors.white,
                          fontSize: 14,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                      const SizedBox(height: 8),
                      _buildTroubleshootingTip(
                        '• Kiểm tra kết nối Internet',
                      ),
                      _buildTroubleshootingTip(
                        '• Thử chuyển sang WiFi hoặc 4G/5G',
                      ),
                      _buildTroubleshootingTip(
                        '• Khởi động lại ứng dụng',
                      ),
                      _buildTroubleshootingTip(
                        '• Xóa cache và thử lại',
                      ),
                    ],
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildTroubleshootingTip(String text) {
    return Padding(
      padding: const EdgeInsets.only(top: 4),
      child: Text(
        text,
        style: const TextStyle(
          color: Colors.white60,
          fontSize: 12,
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

class _MotifCoordinate {
  final String motifName;
  final String meshName;
  final double posX;
  final double posY;
  final double posZ;
  final double boundingRadius;

  const _MotifCoordinate({
    required this.motifName,
    required this.meshName,
    required this.posX,
    required this.posY,
    required this.posZ,
    required this.boundingRadius,
  });
}
