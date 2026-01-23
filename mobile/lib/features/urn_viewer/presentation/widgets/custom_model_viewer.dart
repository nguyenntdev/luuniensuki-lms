import 'dart:async';
import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:model_viewer_plus/model_viewer_plus.dart';

import '../../../../core/theme/app_colors.dart';
import '../../domain/entities/urn.dart';

/// Custom 3D model viewer widget using model_viewer_plus for a lighter native WebView.
///
/// This widget wraps the Google model-viewer web component and provides
/// JavaScript bridge callbacks for:
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
  final ValueChanged<dynamic>? onControllerReady;
  final Color backgroundColor;
  final bool autoRotate;
  final bool cameraControls;
  final bool disableZoom;
  final String? cameraOrbit;
  final String? minCameraOrbit;
  final String? maxCameraOrbit;
  final String? fieldOfView;
  final bool ar;
  final List<String>? arModes;
  final String? iosSrc;

  const CustomModelViewer({
    super.key,
    required this.modelUrl,
    required this.alt,
    this.hotspots = const [],
    this.onModelLoaded,
    this.onModelError,
    this.onProgress,
    this.onHotspotTap,
    this.onControllerReady,
    this.backgroundColor = const Color(0xFF1A1A2E),
    this.autoRotate = false,
    this.cameraControls = true,
    this.disableZoom = false,
    this.cameraOrbit,
    this.minCameraOrbit,
    this.maxCameraOrbit,
    this.fieldOfView,
    this.ar = false,
    this.arModes,
    this.iosSrc,
  });

  @override
  State<CustomModelViewer> createState() => _CustomModelViewerState();
}

class _CustomModelViewerState extends State<CustomModelViewer> {
  static const String _channelName = 'ModelViewerBridge';

  dynamic _webViewController;
  bool _isLoading = true;
  String? _errorMessage;
  double _loadProgress = 0.0;
  int _contextLossCount = 0;
  Timer? _safetyTimer;

  @override
  void initState() {
    super.initState();
    debugPrint(
        '[CUSTOM_MODEL_VIEWER] 🚀 Initializing for model: ${widget.modelUrl}');
    debugPrint('[CUSTOM_MODEL_VIEWER] 📊 Starting model load process...');
    _scheduleSafetyTimeout();
  }

  @override
  void didUpdateWidget(covariant CustomModelViewer oldWidget) {
    super.didUpdateWidget(oldWidget);

    if (oldWidget.modelUrl != widget.modelUrl) {
      debugPrint(
          '[CUSTOM_MODEL_VIEWER] 🔄 Model URL changed - resetting state');
      debugPrint('[CUSTOM_MODEL_VIEWER] 📊 New model URL: ${widget.modelUrl}');
      if (mounted) {
        setState(() {
          _loadProgress = 0.0;
          _errorMessage = null;
          _isLoading = true;
          _contextLossCount = 0;
        });
      }
      _scheduleSafetyTimeout();
    }
  }

  @override
  void dispose() {
    _safetyTimer?.cancel();
    super.dispose();
  }

  void _scheduleSafetyTimeout() {
    _safetyTimer?.cancel();
    _safetyTimer = Timer(const Duration(seconds: 120), () {
      if (mounted && _isLoading) {
        debugPrint(
            '[CUSTOM_MODEL_VIEWER] ⚠️ Model still loading after 2 minutes');
        debugPrint(
            '[CUSTOM_MODEL_VIEWER] ⚠️ Current progress: ${_loadProgress.toInt()}%');
        debugPrint(
            '[CUSTOM_MODEL_VIEWER] ℹ️ Large models (60-80MB) may take time to download');
        // Don't hide loading indicator - just log warning
        // Model will continue loading in background
      }
    });
  }

  String _buildHotspotsHtml() {
    return widget.hotspots.map((motif) {
      if (!motif.hasValidPosition) {
        return '';
      }

      final hotspotColor = _getHotspotColor(motif);
      final hotspotIcon = _getHotspotIcon(motif);

      return '''
        <button
          class="hotspot"
          slot="hotspot-${motif.id}"
          data-position="${motif.posX}m ${motif.posY}m ${motif.posZ}m"
          data-normal="0m 1m 0m"
          data-motif-id="${motif.id}"
          style="background-color: $hotspotColor;"
        >
          <span class="hotspot-icon">$hotspotIcon</span>
        </button>
      ''';
    }).join('\n');
  }

  String _buildRelatedCss() {
    return '''
      .hotspot {
        width: 40px;
        height: 40px;
        border-radius: 50%;
        cursor: pointer;
        pointer-events: auto;
        touch-action: none;
        display: flex;
        align-items: center;
        justify-content: center;
        opacity: 0.06;
        border: 1.5px solid rgba(255, 255, 255, 0.15);
        box-shadow: none;
        transition: opacity 0.15s ease, transform 0.2s ease, box-shadow 0.2s ease;
      }
      .hotspot.is-active,
      .hotspot:active {
        opacity: 0.45;
        border-color: rgba(255, 255, 255, 0.6);
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
      }
      .hotspot:hover {
        transform: scale(1.1);
      }
      .hotspot-icon {
        color: white;
        font-size: 20px;
        font-weight: bold;
        opacity: 0.9;
      }
    ''';
  }

  String _buildRelatedJs() {
    return '''
      (function () {
        console.log('[MODEL_VIEWER_JS] Initializing JavaScript bridge...');
        const channel = window.$_channelName;
        const send = (payload) => {
          console.log('[MODEL_VIEWER_JS] Sending message:', JSON.stringify(payload));
          if (channel && channel.postMessage) {
            channel.postMessage(JSON.stringify(payload));
          } else {
            console.error('[MODEL_VIEWER_JS] Channel not available!');
          }
        };

        // Send init message immediately
        send({ type: 'init', timestamp: Date.now() });

        const modelViewer = document.getElementById('modelViewer') || document.querySelector('model-viewer');
        if (!modelViewer) {
          console.error('[MODEL_VIEWER_JS] Model viewer element not found!');
          send({ type: 'error', error: 'Model viewer not found', timestamp: Date.now() });
          return;
        }
        console.log('[MODEL_VIEWER_JS] Model viewer element found');

        const notify = (type, data) => {
          send(Object.assign({ type: type, timestamp: Date.now() }, data || {}));
        };

        // Listen for model load
        modelViewer.addEventListener('load', () => {
          console.log('[MODEL_VIEWER_JS] Model loaded event fired');
          notify('load');
        });

        // Immediate check in case model already loaded before listeners attached
        if (modelViewer.loaded) {
          console.log('[MODEL_VIEWER_JS] Model already loaded (immediate check)');
          notify('load');
        }

        // Listen for errors
        modelViewer.addEventListener('error', (event) => {
          const message = event && event.detail && event.detail.message
            ? event.detail.message
            : 'Failed to load 3D model';
          console.error('[MODEL_VIEWER_JS] Error event:', message);
          notify('error', { error: message, detail: event && event.detail ? event.detail : {} });
        });

        // Listen for progress
        modelViewer.addEventListener('progress', (event) => {
          const progress = event && event.detail && typeof event.detail.totalProgress === 'number'
            ? event.detail.totalProgress * 100
            : 0;
          console.log('[MODEL_VIEWER_JS] Progress:', progress);
          notify('progress', { progress: progress });
        });

        modelViewer.addEventListener('model-visibility', (event) => {
          const visible = event && event.detail && event.detail.visible ? true : false;
          console.log('[MODEL_VIEWER_JS] Model visibility:', visible);
          notify('visibility', { visible: visible });
        });

        const hotspots = modelViewer.querySelectorAll('.hotspot');
        let lastTapAt = 0;
        hotspots.forEach((hotspot) => {
          hotspot.style.pointerEvents = 'auto';
          const handleTap = (event) => {
            event.stopPropagation();
            event.preventDefault();
            const now = Date.now();
            if (now - lastTapAt < 250) {
              return;
            }
            lastTapAt = now;
            const motifId = hotspot.getAttribute('data-motif-id');
            if (motifId) {
              notify('hotspot', { motifId: motifId });
            }
          };
          const activate = () => hotspot.classList.add('is-active');
          const deactivate = () => hotspot.classList.remove('is-active');
          hotspot.addEventListener('click', handleTap);
          hotspot.addEventListener('touchend', handleTap);
          hotspot.addEventListener('mouseup', handleTap);
          hotspot.addEventListener('pointerdown', activate);
          hotspot.addEventListener('pointerup', handleTap);
          hotspot.addEventListener('pointerup', deactivate);
          hotspot.addEventListener('pointercancel', deactivate);
          hotspot.addEventListener('pointerleave', deactivate);
        });

        const attachContextHandlers = () => {
          const root = modelViewer.shadowRoot;
          const canvas = root ? root.querySelector('canvas') : null;
          if (!canvas) {
            return;
          }
          canvas.addEventListener('webglcontextlost', (event) => {
            event.preventDefault();
            notify('webgl_lost');
          });
          canvas.addEventListener('webglcontextrestored', () => {
            notify('webgl_restored');
          });
        };

        modelViewer.addEventListener('load', attachContextHandlers);
        setTimeout(attachContextHandlers, 0);

        // Fallback: if model doesn't load after 60 seconds, check modelViewer state
        setTimeout(() => {
          if (modelViewer.loaded) {
            console.log('[MODEL_VIEWER_JS] Fallback check: model is loaded');
            notify('load');
          } else {
            console.log('[MODEL_VIEWER_JS] Fallback check: model not loaded - timeout');
            notify('error', { error: 'Model loading timed out' });
          }
        }, 60000);
      })();
    ''';
  }

  void _handleJavascriptMessage(String message) {
    Map<String, dynamic>? payload;
    try {
      final decoded = jsonDecode(message);
      if (decoded is Map<String, dynamic>) {
        payload = decoded;
      }
    } catch (error) {
      debugPrint('[CUSTOM_MODEL_VIEWER] Failed to parse JS message: $error');
    }

    if (payload == null) {
      return;
    }

    final type = payload['type']?.toString();
    switch (type) {
      case 'init':
        debugPrint('[CUSTOM_MODEL_VIEWER] 🚀 JavaScript bridge initialized');
        break;
      case 'load':
        debugPrint(
            '[CUSTOM_MODEL_VIEWER] ✅ Model loaded successfully - hiding loading overlay');
        debugPrint(
            '[CUSTOM_MODEL_VIEWER] ✅ Final progress: ${_loadProgress.toInt()}%');
        if (mounted) {
          setState(() {
            _isLoading = false;
            _errorMessage = null;
            _contextLossCount = 0;
          });
        }
        widget.onModelLoaded?.call();
        break;
      case 'error':
        final error = payload['error']?.toString() ?? 'Unknown error';
        debugPrint('[CUSTOM_MODEL_VIEWER] ❌ Model load error: $error');
        if (mounted) {
          setState(() {
            _isLoading = false;
            _errorMessage = error;
          });
        }
        widget.onModelError?.call(error);
        break;
      case 'progress':
        final progressValue = payload['progress'];
        final progress = progressValue is num ? progressValue.toDouble() : 0.0;
        debugPrint(
            '[CUSTOM_MODEL_VIEWER] 📊 Loading progress: ${progress.toInt()}%');
        if (mounted) {
          setState(() {
            _loadProgress = progress;
          });
        }
        widget.onProgress?.call(progress);
        break;
      case 'hotspot':
        final motifId = payload['motifId']?.toString();
        if (motifId != null) {
          debugPrint('[CUSTOM_MODEL_VIEWER] 🎯 Hotspot tapped: $motifId');
          widget.onHotspotTap?.call(motifId);
        }
        break;
      case 'webgl_lost':
        _contextLossCount += 1;
        debugPrint(
            '[CUSTOM_MODEL_VIEWER] ❌ WebGL context lost (count: $_contextLossCount)');
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
        break;
      case 'webgl_restored':
        debugPrint('[CUSTOM_MODEL_VIEWER] ⚠️ WebGL context restored');
        break;
      case 'visibility':
        debugPrint(
            '[CUSTOM_MODEL_VIEWER] Model visibility: ${payload['visible']}');
        break;
      default:
        break;
    }
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
      return '★';
    } else if (motif.isLearned) {
      return '✓';
    } else if (motif.isDiscovered) {
      return '•';
    } else {
      return '👆';
    }
  }

  @override
  Widget build(BuildContext context) {
    debugPrint(
        '[CUSTOM_MODEL_VIEWER] Building widget - _isLoading: $_isLoading, _errorMessage: $_errorMessage');
    final hotspotKey = widget.hotspots
        .map(
          (motif) =>
              '${motif.id}:${motif.posX.toStringAsFixed(3)}:${motif.posY.toStringAsFixed(3)}:${motif.posZ.toStringAsFixed(3)}',
        )
        .join('|');

    return Stack(
      children: [
        ModelViewer(
          key: ValueKey('${widget.modelUrl}::$hotspotKey'),
          src: widget.modelUrl,
          alt: widget.alt,
          backgroundColor: widget.backgroundColor,
          loading: Loading.eager,
          reveal: Reveal.auto,
          autoRotate: widget.autoRotate,
          cameraControls: widget.cameraControls,
          disableZoom: widget.disableZoom,
          cameraOrbit: widget.cameraOrbit,
          minCameraOrbit: widget.minCameraOrbit ?? 'auto auto 0.1m',
          maxCameraOrbit: widget.maxCameraOrbit ?? 'auto auto 1000m',
          fieldOfView: widget.fieldOfView ?? '45deg',
          ar: false,
          arModes: widget.arModes ?? const ['scene-viewer', 'webxr', 'quick-look'],
          iosSrc: widget.iosSrc,
          environmentImage: 'neutral',
          exposure: 1.2,
          shadowIntensity: 0,
          id: 'modelViewer',
          innerModelViewerHtml: _buildHotspotsHtml(),
          relatedCss: _buildRelatedCss(),
          relatedJs: _buildRelatedJs(),
          debugLogging: false,
          javascriptChannels: {
            JavascriptChannel(
              _channelName,
              onMessageReceived: (message) {
                _handleJavascriptMessage(message.message);
              },
            ),
          },
          onWebViewCreated: (controller) {
            _webViewController = controller;
            widget.onControllerReady?.call(controller);
          },
        ),
        if (_isLoading && _errorMessage == null)
          Container(
            color: widget.backgroundColor,
            child: Center(
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  const CircularProgressIndicator(
                    valueColor:
                        AlwaysStoppedAnimation<Color>(AppColors.primary),
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
                          _loadProgress = 0.0;
                        });
                        _scheduleSafetyTimeout();
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
}
