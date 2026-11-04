import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../../core/services/model_preloader.dart';

/// State of 3D model download
enum ModelDownloadState {
  idle,
  downloading,
  completed,
  error,
  cached,
}

/// Download progress and metadata info
class ModelDownloadInfo {
  final ModelDownloadState state;
  final double progress;
  final int? totalBytes;
  final int? downloadedBytes;
  final String? localPath;
  final String? error;

  const ModelDownloadInfo({
    required this.state,
    this.progress = 0.0,
    this.totalBytes,
    this.downloadedBytes,
    this.localPath,
    this.error,
  });

  String get progressPercentage => '${(progress * 100).round()}%';

  String get downloadSizeFormatted {
    final preloader = ModelPreloader();
    final downloaded = preloader.formatBytes(downloadedBytes ?? 0);
    final total = totalBytes != null ? preloader.formatBytes(totalBytes!) : 'Unknown';
    return '$downloaded / $total';
  }

  ModelDownloadInfo copyWith({
    ModelDownloadState? state,
    double? progress,
    int? totalBytes,
    int? downloadedBytes,
    String? localPath,
    String? error,
  }) {
    return ModelDownloadInfo(
      state: state ?? this.state,
      progress: progress ?? this.progress,
      totalBytes: totalBytes ?? this.totalBytes,
      downloadedBytes: downloadedBytes ?? this.downloadedBytes,
      localPath: localPath ?? this.localPath,
      error: error ?? this.error,
    );
  }
}

/// Notifier managing 3D model download state
class ModelDownloadNotifier extends StateNotifier<ModelDownloadInfo> {
  final String modelUrl;
  final ModelPreloader _preloader = ModelPreloader();

  ModelDownloadNotifier(this.modelUrl)
      : super(const ModelDownloadInfo(state: ModelDownloadState.idle)) {
    _checkCache();
  }

  Future<void> _checkCache() async {
    final isCached = await _preloader.isModelCached(modelUrl);
    if (isCached) {
      final path = await _preloader.getCachedModelPath(modelUrl);
      state = state.copyWith(
        state: ModelDownloadState.cached,
        progress: 1.0,
        localPath: path,
      );
    }
  }

  Future<void> downloadModel() async {
    if (state.state == ModelDownloadState.downloading) return;

    state = state.copyWith(
      state: ModelDownloadState.downloading,
      progress: 0.0,
      error: null,
    );

    try {
      final path = await _preloader.preloadModel(
        modelUrl,
        onProgress: (received, total) {
          if (total > 0) {
            state = state.copyWith(
              progress: received / total,
              downloadedBytes: received,
              totalBytes: total,
            );
          }
        },
      );

      if (path != null) {
        state = state.copyWith(
          state: ModelDownloadState.completed,
          progress: 1.0,
          localPath: path,
        );
      } else {
        state = state.copyWith(
          state: ModelDownloadState.error,
          error: 'Download failed',
        );
      }
    } catch (e) {
      state = state.copyWith(
        state: ModelDownloadState.error,
        error: e.toString(),
      );
    }
  }

  void cancelDownload() {
    _preloader.cancelDownload(modelUrl);
    state = state.copyWith(
      state: ModelDownloadState.idle,
      progress: 0.0,
    );
  }
}

/// Provider for model download state scoped by modelUrl
final modelDownloadNotifierProvider = StateNotifierProvider.family<
    ModelDownloadNotifier, ModelDownloadInfo, String>(
  (ref, modelUrl) => ModelDownloadNotifier(modelUrl),
);
