import 'dart:io';
import 'package:dio/dio.dart';
import 'package:flutter/foundation.dart';
import 'package:crypto/crypto.dart';
import 'dart:convert';

/// Service for downloading and caching 3D models
class ModelPreloader {
  static final ModelPreloader _instance = ModelPreloader._internal();
  factory ModelPreloader() => _instance;
  ModelPreloader._internal();

  final Dio _dio = Dio(
    BaseOptions(
      connectTimeout: const Duration(seconds: 30),
      receiveTimeout: const Duration(minutes: 5),
    ),
  );

  final Map<String, CancelToken> _activeDownloads = {};
  final Map<String, double> _downloadProgress = {};

  /// Get the cache directory for models
  Future<Directory> get _cacheDir async {
    final appDir = await _resolveBaseDir();
    final cacheDir = Directory('${appDir.path}/model_cache');
    if (!await cacheDir.exists()) {
      await cacheDir.create(recursive: true);
    }
    return cacheDir;
  }

  Future<Directory> _resolveBaseDir() async {
    try {
      final tempDir = Directory.systemTemp;
      final filesDir = Directory('${tempDir.parent.path}/files');
      if (!await filesDir.exists()) {
        await filesDir.create(recursive: true);
      }
      return filesDir;
    } catch (_) {
      final fallback =
          Directory('${Directory.systemTemp.path}/luuniensuki_app');
      if (!await fallback.exists()) {
        await fallback.create(recursive: true);
      }
      return fallback;
    }
  }

  /// Generate a cache key from URL
  String _getCacheKey(String url) {
    final bytes = utf8.encode(url);
    final digest = sha256.convert(bytes);
    return digest.toString();
  }

  /// Get the cached file path for a URL
  Future<File> _getCachedFile(String url) async {
    final dir = await _cacheDir;
    final key = _getCacheKey(url);
    // Preserve file extension for model_viewer_plus
    final ext = url.split('.').last.split('?').first;
    return File('${dir.path}/$key.$ext');
  }

  /// Check if a model is already cached
  Future<bool> isCached(String modelUrl) async {
    final file = await _getCachedFile(modelUrl);
    return await file.exists();
  }

  /// Get the model path, downloading if necessary
  Future<String> getModelPath(
    String modelUrl, {
    void Function(double progress)? onProgress,
  }) async {
    // Check if already cached
    final cachedFile = await _getCachedFile(modelUrl);
    if (await cachedFile.exists()) {
      return cachedFile.path;
    }

    // Download the model
    final cancelToken = CancelToken();
    _activeDownloads[modelUrl] = cancelToken;
    _downloadProgress[modelUrl] = 0.0;

    try {
      await _dio.download(
        modelUrl,
        cachedFile.path,
        cancelToken: cancelToken,
        onReceiveProgress: (received, total) {
          if (total != -1) {
            final progress = received / total;
            _downloadProgress[modelUrl] = progress;
            onProgress?.call(progress);
          }
        },
      );

      _activeDownloads.remove(modelUrl);
      _downloadProgress.remove(modelUrl);

      return cachedFile.path;
    } catch (e) {
      // Clean up failed download
      if (await cachedFile.exists()) {
        await cachedFile.delete();
      }
      _activeDownloads.remove(modelUrl);
      _downloadProgress.remove(modelUrl);
      rethrow;
    }
  }

  /// Preload multiple models in the background
  Future<void> preloadModels(List<String> urls) async {
    await Future.wait(
      urls.map((url) async {
        try {
          // Only download if not already cached
          if (!await isCached(url)) {
            await getModelPath(url);
          }
        } catch (e) {
          // Continue with other downloads even if one fails
          debugPrint('Failed to preload model $url: $e');
        }
      }),
    );
  }

  /// Cancel an active download
  void cancelDownload(String url) {
    final cancelToken = _activeDownloads[url];
    if (cancelToken != null && !cancelToken.isCancelled) {
      cancelToken.cancel('User cancelled download');
      _activeDownloads.remove(url);
      _downloadProgress.remove(url);
    }
  }

  /// Get current download progress for a URL
  double? getProgress(String url) {
    return _downloadProgress[url];
  }

  /// Check if a download is active
  bool isDownloading(String url) {
    return _activeDownloads.containsKey(url);
  }

  /// Clear all cached models
  Future<void> clearCache() async {
    final dir = await _cacheDir;
    if (await dir.exists()) {
      await dir.delete(recursive: true);
      await dir.create(recursive: true);
    }
  }

  /// Get total cache size in bytes
  Future<int> getCacheSize() async {
    final dir = await _cacheDir;
    if (!await dir.exists()) {
      return 0;
    }

    int totalSize = 0;
    await for (final entity in dir.list(recursive: true)) {
      if (entity is File) {
        totalSize += await entity.length();
      }
    }
    return totalSize;
  }

  /// Get cache size as a human-readable string
  Future<String> getCacheSizeFormatted() async {
    final bytes = await getCacheSize();
    return _formatBytes(bytes);
  }

  /// Format bytes to human-readable string
  String _formatBytes(int bytes) {
    if (bytes < 1024) return '$bytes B';
    if (bytes < 1024 * 1024) return '${(bytes / 1024).toStringAsFixed(1)} KB';
    if (bytes < 1024 * 1024 * 1024) {
      return '${(bytes / (1024 * 1024)).toStringAsFixed(1)} MB';
    }
    return '${(bytes / (1024 * 1024 * 1024)).toStringAsFixed(1)} GB';
  }
}
