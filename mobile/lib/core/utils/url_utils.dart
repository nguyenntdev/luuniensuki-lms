import 'package:flutter/foundation.dart';
import '../constants/api_constants.dart';

/// Utility class for URL manipulation and validation
class UrlUtils {
  static String _trimTrailingSlash(String value) {
    if (value.endsWith('/')) {
      return value.substring(0, value.length - 1);
    }
    return value;
  }

  static String _encodeAbsoluteUrl(String url) {
    // Encode Unicode/whitespace in path segments while keeping URL structure.
    final encoded = Uri.encodeFull(url);
    final uri = Uri.tryParse(encoded);
    return uri?.toString() ?? encoded;
  }

  static String? _toApiAssetsVariant(String absoluteUrl) {
    final uri = Uri.tryParse(absoluteUrl);
    if (uri == null || uri.host.isEmpty) return null;
    if (!uri.path.startsWith('/assets/')) return null;
    return uri.replace(path: '/api${uri.path}').toString();
  }

  /// Convert a relative URL to a full URL by prepending the base URL
  static String? toFullUrl(String? url) {
    if (url == null) return null;
    final trimmed = url.trim();
    if (trimmed.isEmpty) return null;

    // Protocol-relative URL (e.g. //cdn.example.com/file.jpg)
    if (trimmed.startsWith('//')) {
      return _encodeAbsoluteUrl('https:$trimmed');
    }

    if (trimmed.startsWith('http://') || trimmed.startsWith('https://')) {
      return _encodeAbsoluteUrl(trimmed);
    }

    final base = _trimTrailingSlash(ApiConstants.baseUrl);
    final normalized = trimmed.startsWith('/') ? trimmed : '/$trimmed';
    final fullUrl = _encodeAbsoluteUrl('$base$normalized');

    // Log debug info for troubleshooting
    if (kDebugMode) {
      debugPrint('[MOTIF_IMAGE] Converting relative URL: $trimmed');
      debugPrint('[MOTIF_IMAGE] Full URL: $fullUrl');
    }

    return fullUrl;
  }

  /// Get a valid image URL with fallback
  /// Returns the full URL if available, otherwise returns the fallback
  static String getImageUrl(String? url, {String fallback = ''}) {
    final fullUrl = toFullUrl(url);
    if (fullUrl == null && fallback.isNotEmpty) {
      return toFullUrl(fallback) ?? fallback;
    }

    if (kDebugMode && fullUrl != null) {
      debugPrint('[MOTIF_IMAGE] Image URL: $fullUrl');
    }

    return fullUrl ?? fallback;
  }

  /// Return ordered image URL candidates for resilient loading.
  /// For asset paths, we include both `/assets/*` and `/api/assets/*` variants.
  static List<String> getImageUrlCandidates(String? url, {String fallback = ''}) {
    final candidates = <String>[];

    void addCandidate(String? rawUrl) {
      final normalized = toFullUrl(rawUrl);
      if (normalized == null || normalized.isEmpty) {
        return;
      }
      if (!candidates.contains(normalized)) {
        candidates.add(normalized);
      }
      final apiVariant = _toApiAssetsVariant(normalized);
      if (apiVariant != null && !candidates.contains(apiVariant)) {
        candidates.add(apiVariant);
      }
    }

    addCandidate(url);
    if (fallback.isNotEmpty) {
      addCandidate(fallback);
    }

    return candidates;
  }

  /// Get asset URL for images hosted under /assets/
  /// Commonly used for motif thumbnails at /assets/motifs/
  static String getAssetUrl(String relativePath) {
    final cleanPath =
        relativePath.startsWith('/') ? relativePath.substring(1) : relativePath;
    return toFullUrl('/$cleanPath') ?? '/$cleanPath';
  }

  /// Validate if a URL is properly formed
  static bool isValidUrl(String? url) {
    if (url == null || url.isEmpty) return false;

    try {
      final uri = Uri.parse(url);
      return uri.hasScheme && uri.host.isNotEmpty;
    } catch (e) {
      if (kDebugMode) {
        debugPrint('[MOTIF_IMAGE] Invalid URL: $url - Error: $e');
      }
      return false;
    }
  }
}
