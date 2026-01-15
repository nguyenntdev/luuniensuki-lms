import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_inappwebview/flutter_inappwebview.dart';

import '../../../../core/theme/app_colors.dart';
import '../../domain/entities/urn.dart';

/// Custom 3D model viewer widget using flutter_inappwebview for full JavaScript handler control.
///
/// This widget wraps the Google model-viewer web component in a WebView and provides
/// proper JavaScript handler integration for:
/// - Model load callbacks
/// - Progress tracking
/// - Error handling
/// - Hotspot tap detection
class CustomModelViewer extends StatefulWidget {
  final String modelUrl;
  final String alt;
  final List<Motif> hotspots;
  final VoidCallback? onModelLoaded;
  final Function(String error)? onModelError;
  final Function(double progress)? onProgress;
  final Function(String motifId)? onHotspotTap;
  final Color backgroundColor;
  final bool autoRotate;
  final bool cameraControls;
  final bool disableZoom;
  final String? cameraOrbit;
  final String? minCameraOrbit;
  final String? maxCameraOrbit;
  final String? fieldOfView;

  const CustomModelViewer({
    super.key,
    required this.modelUrl,
    required this.alt,
    this.hotspots = const [],
    this.onModelLoaded,
    this.onModelError,
    this.onProgress,
    this.onHotspotTap,
    this.backgroundColor = const Color(0xFF1A1A2E),
    this.autoRotate = false,
    this.cameraControls = true,
    this.disableZoom = false,
    this.cameraOrbit,
    this.minCameraOrbit,
    this.maxCameraOrbit,
    this.fieldOfView,
  });

  @override
  State<CustomModelViewer> createState() => _CustomModelViewerState();
}

class _CustomModelViewerState extends State<CustomModelViewer> {
  InAppWebViewController? _webViewController;
  bool _isLoading = true;
  String? _errorMessage;
  double _loadProgress = 0.0;
  int _contextLossCount = 0;
  int _renderProcessGoneCount = 0;

  @override
  void initState() {
    super.initState();
    debugPrint('[CUSTOM_MODEL_VIEWER] Initializing for model: ${widget.modelUrl}');
  }

  @override
  void dispose() {
    _webViewController?.dispose();
    super.dispose();
  }

  @override
  void didUpdateWidget(covariant CustomModelViewer oldWidget) {
    super.didUpdateWidget(oldWidget);

    if (oldWidget.modelUrl != widget.modelUrl) {
      debugPrint('[CUSTOM_MODEL_VIEWER] Model URL changed - reloading WebView');
      if (mounted) {
        setState(() {
          _loadProgress = 0.0;
          _errorMessage = null;
          _isLoading = true;
          _contextLossCount = 0;
          _renderProcessGoneCount = 0;
        });
      }
      _webViewController?.loadData(
        data: _generateHtml(),
        baseUrl: WebUri('https://lms.histolab.icu'),
        mimeType: 'text/html',
        encoding: 'utf-8',
      );
    }
  }

  _MotifBounds? _computeMotifBounds() {
    final positioned = widget.hotspots.where((motif) => motif.hasValidPosition).toList();
    if (positioned.isEmpty) {
      return null;
    }

    double minX = positioned.first.posX;
    double maxX = positioned.first.posX;
    double minY = positioned.first.posY;
    double maxY = positioned.first.posY;
    double minZ = positioned.first.posZ;
    double maxZ = positioned.first.posZ;

    for (final motif in positioned.skip(1)) {
      minX = minX < motif.posX ? minX : motif.posX;
      maxX = maxX > motif.posX ? maxX : motif.posX;
      minY = minY < motif.posY ? minY : motif.posY;
      maxY = maxY > motif.posY ? maxY : motif.posY;
      minZ = minZ < motif.posZ ? minZ : motif.posZ;
      maxZ = maxZ > motif.posZ ? maxZ : motif.posZ;
    }

    final centerX = (minX + maxX) / 2.0;
    final centerY = (minY + maxY) / 2.0;
    final centerZ = (minZ + maxZ) / 2.0;
    final sizeX = (maxX - minX).abs();
    final sizeY = (maxY - minY).abs();
    final sizeZ = (maxZ - minZ).abs();

    return _MotifBounds(
      centerX: centerX,
      centerY: centerY,
      centerZ: centerZ,
      sizeX: sizeX,
      sizeY: sizeY,
      sizeZ: sizeZ,
    );
  }

  /// Generate HTML content with model-viewer web component
  String _generateHtml() {
    final bgColor = _colorToHex(widget.backgroundColor);
    final motifBounds = _computeMotifBounds();
    final boundsCenterAttr = motifBounds == null
        ? ''
        : 'data-bounds-center="${motifBounds.centerX} ${motifBounds.centerY} ${motifBounds.centerZ}"';
    final boundsSizeAttr = motifBounds == null
        ? ''
        : 'data-bounds-size="${motifBounds.sizeX} ${motifBounds.sizeY} ${motifBounds.sizeZ}"';
    final cameraOrbitAttrValue = widget.cameraOrbit ?? 'auto auto auto';
    final cameraTargetAttrValue = 'auto auto auto';

    // Generate hotspot HTML
    final hotspotsHtml = widget.hotspots.map((motif) {
      if (!motif.hasValidPosition) return '';

      final hotspotColor = _getHotspotColor(motif);
      final hotspotIcon = _getHotspotIcon(motif);

      return '''
        <button
          class="hotspot"
          slot="hotspot-${motif.id}"
          data-position="${motif.posX}m ${motif.posY}m ${motif.posZ}m"
          data-normal="0m 1m 0m"
          data-motif-id="${motif.id}"
          style="background-color: $hotspotColor; border: 2px solid white;"
        >
          <span class="hotspot-icon">$hotspotIcon</span>
        </button>
      ''';
    }).join('\n');

    return '''
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>3D Model Viewer</title>
  <script type="module" src="https://unpkg.com/@google/model-viewer@3.4.0/dist/model-viewer.min.js"></script>
  <style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body {
      width: 100vw;
      height: 100vh;
      overflow: hidden;
      background-color: $bgColor;
    }
    model-viewer {
      width: 100%;
      height: 100%;
      background-color: $bgColor;
      --poster-color: $bgColor;
    }
    .hotspot {
      width: 40px;
      height: 40px;
      border-radius: 50%;
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
      transition: transform 0.2s ease;
    }
    .hotspot:hover {
      transform: scale(1.1);
    }
    .hotspot-icon {
      color: white;
      font-size: 20px;
      font-weight: bold;
    }
  </style>
</head>
<body>
  <model-viewer
    id="modelViewer"
    src="${widget.modelUrl}"
    alt="${widget.alt}"
    ${widget.autoRotate ? 'auto-rotate' : ''}
    ${widget.cameraControls ? 'camera-controls' : ''}
    ${widget.disableZoom ? 'disable-zoom' : ''}
    camera-orbit="$cameraOrbitAttrValue"
    ${widget.minCameraOrbit != null ? 'min-camera-orbit="${widget.minCameraOrbit}"' : 'min-camera-orbit="auto auto 0.1m"'}
    ${widget.maxCameraOrbit != null ? 'max-camera-orbit="${widget.maxCameraOrbit}"' : 'max-camera-orbit="auto auto 1000m"'}
    ${widget.fieldOfView != null ? 'field-of-view="${widget.fieldOfView}"' : 'field-of-view="45deg"'}
    camera-target="$cameraTargetAttrValue"
    loading="eager"
    reveal="auto"
    shadow-intensity="0"
    environment-image="neutral"
    exposure="1.2"
    $boundsCenterAttr
    $boundsSizeAttr
  >
    $hotspotsHtml
  </model-viewer>

  <script>
    let modelViewer = null;
    function initializeModelViewer() {
      console.log('[MODEL_VIEWER] Initializing...');
      if (!modelViewer) {
        console.warn('[MODEL_VIEWER] Missing modelViewer element');
        return;
      }
      console.log('[MODEL_VIEWER] Model src attribute:', modelViewer.getAttribute('src'));
      console.log('[MODEL_VIEWER] Model src property:', modelViewer.src);

    function parseFieldOfView(viewer) {
      const raw = viewer?.fieldOfView ?? viewer?.getFieldOfView?.();
      if (typeof raw === 'number') {
        return raw;
      }
      if (typeof raw === 'string') {
        const value = parseFloat(raw);
        if (!Number.isNaN(value)) {
          return value;
        }
      }
      return 45;
    }

    function logCameraState(prefix) {
      const orbit = modelViewer?.getCameraOrbit ? modelViewer.getCameraOrbit() : modelViewer?.cameraOrbit;
      const target = modelViewer?.getCameraTarget ? modelViewer.getCameraTarget() : modelViewer?.cameraTarget;
      console.log(prefix, 'orbit:', JSON.stringify(orbit), 'target:', JSON.stringify(target));
    }

    function getBoundsFromAttributes() {
      if (!modelViewer) {
        return null;
      }
      const centerAttr = modelViewer.getAttribute('data-bounds-center');
      const sizeAttr = modelViewer.getAttribute('data-bounds-size');
      if (!centerAttr || !sizeAttr) {
        return null;
      }
      const centerValues = centerAttr.split(' ').map((value) => Number.parseFloat(value));
      const sizeValues = sizeAttr.split(' ').map((value) => Number.parseFloat(value));
      if (centerValues.length < 3 || sizeValues.length < 3) {
        return null;
      }
      if (centerValues.some((value) => !Number.isFinite(value)) ||
          sizeValues.some((value) => !Number.isFinite(value))) {
        return null;
      }
      return {
        center: { x: centerValues[0], y: centerValues[1], z: centerValues[2] },
        size: { x: sizeValues[0], y: sizeValues[1], z: sizeValues[2] },
      };
    }

    function getBoundsFromSceneGraph() {
      if (!modelViewer) {
        return null;
      }
      const model = modelViewer.model;
      if (!model) {
        return null;
      }
      let box = null;
      if (typeof model.getBoundingBox === 'function') {
        box = model.getBoundingBox();
      } else if (model.boundingBox) {
        box = model.boundingBox;
      } else if (model.sceneGraph && model.sceneGraph.boundingBox) {
        box = model.sceneGraph.boundingBox;
      }
      const min = box?.min;
      const max = box?.max;
      if (!min || !max) {
        return null;
      }
      if (![min.x, min.y, min.z, max.x, max.y, max.z].every((value) => Number.isFinite(value))) {
        return null;
      }
      const center = {
        x: (min.x + max.x) / 2,
        y: (min.y + max.y) / 2,
        z: (min.z + max.z) / 2,
      };
      const size = {
        x: Math.abs(max.x - min.x),
        y: Math.abs(max.y - min.y),
        z: Math.abs(max.z - min.z),
      };
      return { center, size };
    }

    function ensureCameraLimits() {
      if (!modelViewer) {
        return;
      }
      if (!modelViewer.hasAttribute('min-camera-orbit')) {
        modelViewer.setAttribute('min-camera-orbit', 'auto auto 0.1m');
      }
      if (!modelViewer.hasAttribute('max-camera-orbit')) {
        modelViewer.setAttribute('max-camera-orbit', 'auto auto 1000m');
      }
    }

    function parseVectorString(value) {
      if (typeof value !== 'string') {
        return null;
      }
      const parts = value.split(' ').map((entry) => Number.parseFloat(entry));
      if (parts.length < 3) {
        return null;
      }
      if (parts.some((entry) => !Number.isFinite(entry))) {
        return null;
      }
      return { x: parts[0], y: parts[1], z: parts[2] };
    }

    let lastAppliedOrbit = null;
    let lastAppliedTarget = null;
    let visibilityRetryCount = 0;

    function getCurrentTarget() {
      if (!modelViewer) {
        return null;
      }
      if (typeof modelViewer.getCameraTarget === 'function') {
        const target = modelViewer.getCameraTarget();
        if (target && Number.isFinite(target.x) && Number.isFinite(target.y) && Number.isFinite(target.z)) {
          return { x: target.x, y: target.y, z: target.z };
        }
      }
      return parseVectorString(modelViewer.cameraTarget) || lastAppliedTarget;
    }

    function getCurrentOrbit() {
      if (!modelViewer || typeof modelViewer.getCameraOrbit !== 'function') {
        return lastAppliedOrbit;
      }
      const orbit = modelViewer.getCameraOrbit();
      if (!orbit || orbit.radius == null) {
        return lastAppliedOrbit;
      }
      return orbit;
    }

    function toDegrees(radians) {
      if (!Number.isFinite(radians)) {
        return 0;
      }
      return radians * 180 / Math.PI;
    }

    function applyCamera(target, theta, phi, radius) {
      if (!modelViewer || !target) {
        return false;
      }
      ensureCameraLimits();
      const safeRadius = Number.isFinite(radius) ? Math.max(radius, 0.5) : 1;
      const thetaDeg = toDegrees(theta);
      const phiDeg = Number.isFinite(phi) ? toDegrees(phi) : 75;
      const orbitString = `\${thetaDeg.toFixed(2)}deg \${phiDeg.toFixed(2)}deg \${safeRadius.toFixed(3)}m`;
      const targetString = `\${target.x.toFixed(4)}m \${target.y.toFixed(4)}m \${target.z.toFixed(4)}m`;
      lastAppliedOrbit = { theta, phi, radius: safeRadius };
      lastAppliedTarget = { x: target.x, y: target.y, z: target.z };

      if (modelViewer.cameraTarget != null && typeof modelViewer.cameraTarget === 'object') {
        modelViewer.cameraTarget = { x: target.x, y: target.y, z: target.z };
      } else {
        modelViewer.cameraTarget = targetString;
      }
      modelViewer.setAttribute('camera-target', targetString);

      if (modelViewer.cameraOrbit != null && typeof modelViewer.cameraOrbit === 'object') {
        modelViewer.cameraOrbit = { theta, phi, radius: safeRadius };
      } else {
        modelViewer.cameraOrbit = orbitString;
      }
      modelViewer.setAttribute('camera-orbit', orbitString);
      if (modelViewer.jumpCameraToGoal) {
        modelViewer.jumpCameraToGoal();
      }
      if (modelViewer.requestUpdate) {
        modelViewer.requestUpdate();
      }
      if (modelViewer.dismissPoster) {
        modelViewer.dismissPoster();
      }
      modelViewer.style.visibility = 'visible';
      modelViewer.style.opacity = '1';
      console.log('[MODEL_VIEWER] Applied camera:', orbitString, 'target:', targetString);
      return true;
    }

    function forceZoomOut() {
      const fallbackBounds = getBoundsFromAttributes();
      const size = fallbackBounds?.size;
      const maxDim = size ? Math.max(size.x || 0, size.y || 0, size.z || 0) : 1;
      const baseOrbit = lastAppliedOrbit || getCurrentOrbit();
      const baseRadius = Number.isFinite(baseOrbit?.radius) ? baseOrbit.radius : maxDim;
      const theta = Number.isFinite(baseOrbit?.theta) ? baseOrbit.theta : 0;
      const phi = Number.isFinite(baseOrbit?.phi) ? baseOrbit.phi : Math.PI / 2;
      const target = lastAppliedTarget || getCurrentTarget() || fallbackBounds?.center;
      if (!target) {
        return false;
      }
      visibilityRetryCount += 1;
      const multiplier = Math.min(6, 1.8 + visibilityRetryCount * 0.4);
      const bumpedRadius = Math.max(baseRadius * multiplier, maxDim * 6, baseRadius + 4);
      return applyCamera(target, theta, phi, bumpedRadius);
    }

    function expandCameraOrbit(multiplier) {
      const orbit = getCurrentOrbit();
      const target = getCurrentTarget();
      if (!orbit || !target) {
        return false;
      }
      const radius = Number.isFinite(orbit.radius) ? orbit.radius : 2;
      const newRadius = Math.max(radius * multiplier, radius + 0.5);
      applyCamera(target, orbit.theta, orbit.phi, newRadius);
      logCameraState('[MODEL_VIEWER] Expanded orbit');
      return true;
    }

    function fitCameraToModel() {
      if (!modelViewer) {
        return false;
      }
      ensureCameraLimits();
      console.log(
        '[MODEL_VIEWER] Bounds API:',
        typeof modelViewer.getBoundingBoxCenter,
        typeof modelViewer.getBoundingBoxSize
      );
      const sceneBounds = getBoundsFromSceneGraph();
      if (sceneBounds) {
        console.log(
          '[MODEL_VIEWER] Bounds from scene:',
          JSON.stringify(sceneBounds.center),
          JSON.stringify(sceneBounds.size)
        );
      }
      if (sceneBounds ||
          typeof modelViewer.getBoundingBoxCenter !== 'function' ||
          typeof modelViewer.getBoundingBoxSize !== 'function') {
        const fallbackBounds = sceneBounds ?? getBoundsFromAttributes();
        if (!fallbackBounds) {
          return false;
        }
        const size = fallbackBounds.size;
        const center = fallbackBounds.center;
        const maxDim = Math.max(size.x || 0, size.y || 0, size.z || 0);
        if (!Number.isFinite(maxDim) || maxDim <= 0) {
          return false;
        }
        const currentOrbit = getCurrentOrbit();
        const currentTarget = getCurrentTarget();
        const theta = Number.isFinite(currentOrbit?.theta) ? currentOrbit.theta : 0;
        const phi = Number.isFinite(currentOrbit?.phi) ? currentOrbit.phi : Math.PI / 2;
        const currentRadius = Number.isFinite(currentOrbit?.radius) ? currentOrbit.radius : 0;
        const target = currentTarget ?? center;
        const fov = parseFieldOfView(modelViewer);
        const radius = 0.5 * Math.sqrt(
          (size.x || 0) * (size.x || 0) +
          (size.y || 0) * (size.y || 0) +
          (size.z || 0) * (size.z || 0)
        );
        const distance = radius / Math.sin((fov * Math.PI / 180) / 2);
        const orbitDistance = Math.max(distance * 1.4, radius * 2, maxDim);
        const safeDistance = Math.max(orbitDistance, currentRadius * 1.8, maxDim * 4, 4);
        console.log('[MODEL_VIEWER] Bounds from motifs:', JSON.stringify(center), JSON.stringify(size));
        console.log('[MODEL_VIEWER] Fit camera fov:', fov, 'radius:', radius, 'orbit:', safeDistance);
        logCameraState('[MODEL_VIEWER] Before fit');
        applyCamera(target, theta, phi, safeDistance);
        logCameraState('[MODEL_VIEWER] After fit');
        return true;
      }

      const center = modelViewer.getBoundingBoxCenter();
      const size = modelViewer.getBoundingBoxSize();
      if (!center || !size) {
        return false;
      }

      const maxDim = Math.max(size.x || 0, size.y || 0, size.z || 0);
      if (!Number.isFinite(maxDim) || maxDim <= 0) {
        return false;
      }

      const fov = parseFieldOfView(modelViewer);
      const radius = 0.5 * Math.sqrt(
        (size.x || 0) * (size.x || 0) +
        (size.y || 0) * (size.y || 0) +
        (size.z || 0) * (size.z || 0)
      );
      const distance = radius / Math.sin((fov * Math.PI / 180) / 2);
      const orbitDistance = Math.max(distance * 1.4, radius * 2, maxDim);
      const currentOrbit = getCurrentOrbit();
      const theta = Number.isFinite(currentOrbit?.theta) ? currentOrbit.theta : 0;
      const phi = Number.isFinite(currentOrbit?.phi) ? currentOrbit.phi : Math.PI / 2;

      console.log('[MODEL_VIEWER] Bounds center:', center, 'size:', size);
      console.log('[MODEL_VIEWER] Fit camera fov:', fov, 'radius:', radius, 'orbit:', orbitDistance);
      logCameraState('[MODEL_VIEWER] Before fit');

      applyCamera(center, theta, phi, Math.max(orbitDistance, maxDim * 4, 4));
      logCameraState('[MODEL_VIEWER] After fit');
      return true;
    }

    // Model load success handler
    modelViewer.addEventListener('load', () => {
      console.log('[MODEL_VIEWER] ✅ Model loaded successfully');
      if (!fitCameraToModel()) {
        expandCameraOrbit(1.4);
      }
      requestAnimationFrame(() => {
        if (!fitCameraToModel()) {
          expandCameraOrbit(1.4);
        }
      });
      setTimeout(() => {
        if (!fitCameraToModel()) {
          expandCameraOrbit(1.4);
        }
      }, 150);
      attachContextLossHandler();
      if (window.flutter_inappwebview) {
        window.flutter_inappwebview.callHandler('onModelLoad', {
          success: true,
          timestamp: Date.now()
        });
      }
    });

    // Model load error handler
    modelViewer.addEventListener('error', (event) => {
      console.error('[MODEL_VIEWER] ❌ Model load error:', event);
      const errorMsg = event.detail?.message || 'Failed to load 3D model';
      if (window.flutter_inappwebview) {
        window.flutter_inappwebview.callHandler('onModelError', {
          error: errorMsg,
          detail: event.detail || {},
          timestamp: Date.now()
        });
      }
    });

    // Model load progress handler
    modelViewer.addEventListener('progress', (event) => {
      const progress = event.detail.totalProgress * 100;
      console.log('[MODEL_VIEWER] Loading progress:', progress.toFixed(1) + '%');
      if (window.flutter_inappwebview) {
        window.flutter_inappwebview.callHandler('onProgress', {
          progress: progress,
          timestamp: Date.now()
        });
      }
    });

    modelViewer.addEventListener('model-visibility', (event) => {
      const visible = event.detail.visible;
      console.log('[MODEL_VIEWER] Model visibility:', visible);
      if (!visible) {
        console.warn('[MODEL_VIEWER] Model hidden - re-fitting camera');
        logCameraState('[MODEL_VIEWER] Current camera');
        if (!fitCameraToModel()) {
          forceZoomOut();
        }
        setTimeout(() => {
          if (!fitCameraToModel()) {
            forceZoomOut();
          }
        }, 200);
      }
    });

    // Hotspot click handlers
    const hotspots = document.querySelectorAll('.hotspot');
    hotspots.forEach(hotspot => {
      hotspot.addEventListener('click', (e) => {
        e.stopPropagation();
        const motifId = hotspot.getAttribute('data-motif-id');
        console.log('[MODEL_VIEWER] 🎯 Hotspot tapped:', motifId);
        if (window.flutter_inappwebview && motifId) {
          window.flutter_inappwebview.callHandler('onHotspotTap', {
            motifId: motifId,
            timestamp: Date.now()
          });
        }
      });
    });

    // Camera orbit change tracking (optional)
    modelViewer.addEventListener('camera-change', () => {
      const orbit = modelViewer.getCameraOrbit();
      // Optionally send camera position updates
    });

    console.log('[MODEL_VIEWER] Initialization complete');
    console.log('[MODEL_VIEWER] Model src attribute:', modelViewer.getAttribute('src'));
    console.log('[MODEL_VIEWER] Model src property:', modelViewer.src);
    console.log('[MODEL_VIEWER] Hotspots count:', hotspots.length);

    function attachContextLossHandler() {
      const canvas = modelViewer?.shadowRoot?.querySelector('canvas');
      if (!canvas) {
        console.warn('[MODEL_VIEWER] Canvas not found for context loss handler');
        return;
      }
      canvas.addEventListener('webglcontextlost', (event) => {
        event.preventDefault();
        console.error('[MODEL_VIEWER] ❌ WebGL context lost');
        if (window.flutter_inappwebview) {
          window.flutter_inappwebview.callHandler('onWebglContextLost', {
            timestamp: Date.now()
          });
        }
      });
      canvas.addEventListener('webglcontextrestored', () => {
        console.warn('[MODEL_VIEWER] ⚠️ WebGL context restored');
        if (window.flutter_inappwebview) {
          window.flutter_inappwebview.callHandler('onWebglContextRestored', {
            timestamp: Date.now()
          });
        }
      });
      console.log('[MODEL_VIEWER] WebGL context handlers attached');
    }
  }

  if (window.customElements && customElements.whenDefined) {
    customElements.whenDefined('model-viewer').then(() => {
      modelViewer = document.getElementById('modelViewer');
      initializeModelViewer();
    });
  } else {
    modelViewer = document.getElementById('modelViewer');
    initializeModelViewer();
  }
  </script>
</body>
</html>
    ''';
  }

  /// Convert Color to hex string
  String _colorToHex(Color color) {
    return '#${color.value.toRadixString(16).padLeft(8, '0').substring(2)}';
  }

  /// Get hotspot color based on motif status
  String _getHotspotColor(Motif motif) {
    if (motif.isMastered) {
      return _colorToHex(AppColors.statusMastered);
    } else if (motif.isLearned) {
      return _colorToHex(AppColors.statusLearned);
    } else if (motif.isDiscovered) {
      return _colorToHex(AppColors.statusDiscovered);
    } else {
      return _colorToHex(AppColors.primary);
    }
  }

  /// Get hotspot icon based on motif status
  String _getHotspotIcon(Motif motif) {
    if (motif.isMastered) {
      return '★';  // Star
    } else if (motif.isLearned) {
      return '✓';  // Check
    } else if (motif.isDiscovered) {
      return '•';  // Dot
    } else {
      return '👆'; // Touch icon
    }
  }

  @override
  Widget build(BuildContext context) {
    debugPrint('[CUSTOM_MODEL_VIEWER] Building widget - _isLoading: $_isLoading, _errorMessage: $_errorMessage');

    return Stack(
      children: [
        InAppWebView(
          initialData: InAppWebViewInitialData(
            data: _generateHtml(),
            // Use the LMS domain as base URL to avoid CORS issues with model loading
            baseUrl: WebUri('https://lms.histolab.icu'),
            mimeType: 'text/html',
            encoding: 'utf-8',
          ),
          initialSettings: InAppWebViewSettings(
            transparentBackground: false,
            supportZoom: false,
            javaScriptEnabled: true,
            javaScriptCanOpenWindowsAutomatically: false,
            mediaPlaybackRequiresUserGesture: false,
            allowFileAccessFromFileURLs: true,
            allowUniversalAccessFromFileURLs: true,
            useShouldInterceptRequest: false,
            // Allow mixed content for loading resources
            mixedContentMode: MixedContentMode.MIXED_CONTENT_ALWAYS_ALLOW,
            // Enable cache to avoid re-downloading
            cacheEnabled: true,
            // Allow third-party cookies for CDN resources
            thirdPartyCookiesEnabled: true,
            // Hardware acceleration for better WebGL performance
            hardwareAcceleration: true,
            // Use wide viewport to handle 3D content
            useWideViewPort: true,
            // Disable text zoom to prevent layout issues
            textZoom: 100,
            useOnRenderProcessGone: true,
            useHybridComposition: true,
          ),
          onWebViewCreated: (controller) {
            _webViewController = controller;
            debugPrint('[CUSTOM_MODEL_VIEWER] WebView created');

            // Register JavaScript handlers
            _registerJavaScriptHandlers(controller);
          },
          onLoadStart: (controller, url) {
            debugPrint('[CUSTOM_MODEL_VIEWER] Page load started: $url');
            setState(() {
              _isLoading = true;
              _errorMessage = null;
            });
          },
          onLoadStop: (controller, url) async {
            debugPrint('[CUSTOM_MODEL_VIEWER] Page load completed: $url');
            // Add a safety timeout - hide loading overlay after 3 seconds if still showing
            Future.delayed(const Duration(seconds: 3), () {
              if (mounted && _isLoading) {
                debugPrint('[CUSTOM_MODEL_VIEWER] Safety timeout - forcing _isLoading = false');
                setState(() {
                  _isLoading = false;
                });
              }
            });
          },
          onConsoleMessage: (controller, consoleMessage) {
            debugPrint('[CUSTOM_MODEL_VIEWER] Console: ${consoleMessage.message}');
          },
          onReceivedError: (controller, request, error) {
            debugPrint('[CUSTOM_MODEL_VIEWER] WebView error: ${error.description}');
            setState(() {
              _errorMessage = error.description;
              _isLoading = false;
            });
          },
          onRenderProcessGone: (controller, detail) {
            _renderProcessGoneCount += 1;
            debugPrint(
              '[CUSTOM_MODEL_VIEWER] ❌ Render process gone (crash: ${detail.didCrash}, priority: ${detail.rendererPriorityAtExit})',
            );
            if (_renderProcessGoneCount <= 1) {
              setState(() {
                _isLoading = true;
                _errorMessage = null;
              });
              _webViewController?.reload();
              return;
            }
            if (mounted) {
              setState(() {
                _isLoading = false;
                _errorMessage = 'WebView render process crashed';
              });
            }
            widget.onModelError?.call('WebView render process crashed');
          },
        ),

        // Loading overlay
        if (_isLoading && _errorMessage == null)
          Container(
            color: widget.backgroundColor,
            child: Center(
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  const CircularProgressIndicator(
                    valueColor: AlwaysStoppedAnimation<Color>(AppColors.primary),
                  ),
                  const SizedBox(height: 16),
                  Text(
                    'Đang tải mô hình 3D...',
                    style: TextStyle(
                      color: AppColors.textSecondary,
                      fontSize: 14,
                    ),
                  ),
                  const SizedBox(height: 8),
                  Text(
                    '${_loadProgress.toInt()}%',
                    style: TextStyle(
                      color: AppColors.primary,
                      fontSize: 16,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                ],
              ),
            ),
          ),

        // Error overlay
        if (_errorMessage != null)
          Container(
            color: widget.backgroundColor,
            child: Center(
              child: Padding(
                padding: const EdgeInsets.all(24),
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Icon(
                      Icons.error_outline,
                      size: 64,
                      color: AppColors.error,
                    ),
                    const SizedBox(height: 16),
                    Text(
                      'Lỗi tải mô hình',
                      style: TextStyle(
                        color: AppColors.textPrimary,
                        fontSize: 18,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                    const SizedBox(height: 8),
                    Text(
                      _errorMessage!,
                      textAlign: TextAlign.center,
                      style: TextStyle(
                        color: AppColors.textSecondary,
                        fontSize: 14,
                      ),
                    ),
                    const SizedBox(height: 24),
                    ElevatedButton.icon(
                      onPressed: () {
                        setState(() {
                          _errorMessage = null;
                          _isLoading = true;
                        });
                        _webViewController?.reload();
                      },
                      icon: const Icon(Icons.refresh),
                      label: const Text('Thử lại'),
                      style: ElevatedButton.styleFrom(
                        backgroundColor: AppColors.primary,
                        foregroundColor: AppColors.background,
                      ),
                    ),
                  ],
                ),
              ),
            ),
          ),
      ],
    );
  }

  /// Register JavaScript handlers for communication with the WebView
  void _registerJavaScriptHandlers(InAppWebViewController controller) {
    // Model load success handler
    controller.addJavaScriptHandler(
      handlerName: 'onModelLoad',
      callback: (args) {
        debugPrint('[CUSTOM_MODEL_VIEWER] ✅ Model loaded successfully - hiding loading overlay');
        debugPrint('[CUSTOM_MODEL_VIEWER] Current _isLoading before: $_isLoading');
        if (mounted) {
          setState(() {
            _isLoading = false;
            _errorMessage = null;
            _contextLossCount = 0;
          });
          debugPrint('[CUSTOM_MODEL_VIEWER] Current _isLoading after: $_isLoading');
        }
        widget.onModelLoaded?.call();
      },
    );

    // Model load error handler
    controller.addJavaScriptHandler(
      handlerName: 'onModelError',
      callback: (args) {
        final error = args.isNotEmpty ? args[0]['error'] ?? 'Unknown error' : 'Unknown error';
        debugPrint('[CUSTOM_MODEL_VIEWER] ❌ Model load error: $error');
        if (mounted) {
          setState(() {
            _isLoading = false;
            _errorMessage = error;
          });
        }
        widget.onModelError?.call(error);
      },
    );

    // Progress handler
    controller.addJavaScriptHandler(
      handlerName: 'onProgress',
      callback: (args) {
        if (args.isNotEmpty) {
          final progress = args[0]['progress'] ?? 0.0;
          if (mounted) {
            setState(() {
              _loadProgress = progress.toDouble();
            });
          }
          widget.onProgress?.call(progress.toDouble());
        }
      },
    );

    // Hotspot tap handler
    controller.addJavaScriptHandler(
      handlerName: 'onHotspotTap',
      callback: (args) {
        if (args.isNotEmpty) {
          final motifId = args[0]['motifId'];
          if (motifId != null) {
            debugPrint('[CUSTOM_MODEL_VIEWER] 🎯 Hotspot tapped: $motifId');
            widget.onHotspotTap?.call(motifId);
          }
        }
      },
    );

    controller.addJavaScriptHandler(
      handlerName: 'onWebglContextLost',
      callback: (args) {
        _contextLossCount += 1;
        debugPrint('[CUSTOM_MODEL_VIEWER] ❌ WebGL context lost (count: $_contextLossCount)');
        if (_contextLossCount <= 1) {
          setState(() {
            _isLoading = true;
            _errorMessage = null;
          });
          _webViewController?.reload();
          return;
        }
        if (mounted) {
          setState(() {
            _isLoading = false;
            _errorMessage = 'WebGL context lost';
          });
        }
        widget.onModelError?.call('WebGL context lost');
      },
    );

    controller.addJavaScriptHandler(
      handlerName: 'onWebglContextRestored',
      callback: (args) {
        debugPrint('[CUSTOM_MODEL_VIEWER] ⚠️ WebGL context restored');
      },
    );

    debugPrint('[CUSTOM_MODEL_VIEWER] JavaScript handlers registered');
  }
}

class _MotifBounds {
  final double centerX;
  final double centerY;
  final double centerZ;
  final double sizeX;
  final double sizeY;
  final double sizeZ;

  const _MotifBounds({
    required this.centerX,
    required this.centerY,
    required this.centerZ,
    required this.sizeX,
    required this.sizeY,
    required this.sizeZ,
  });
}
