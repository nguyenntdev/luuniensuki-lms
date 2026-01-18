import 'package:flutter/foundation.dart';
import '../constants/api_constants.dart';

/// Utility class for URL manipulation and validation
class UrlUtils {
  /// Convert a relative URL to a full URL by prepending the base URL
  static String? toFullUrl(String? url) {
    if (url == null) return null;
    final trimmed = url.trim();
    if (trimmed.isEmpty) return null;
    if (trimmed.startsWith('http://') || trimmed.startsWith('https://')) {
      return trimmed;
    }

    final base = ApiConstants.baseUrl.endsWith('/')
        ? ApiConstants.baseUrl.substring(0, ApiConstants.baseUrl.length - 1)
        : ApiConstants.baseUrl;
    final normalized = trimmed.startsWith('/') ? trimmed : '/$trimmed';

    // Log debug info for troubleshooting
    if (kDebugMode) {
      debugPrint('[MOTIF_IMAGE] Converting relative URL: $trimmed');
      debugPrint('[MOTIF_IMAGE] Full URL: $base$normalized');
    }

    return '$base$normalized';
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

  /// Get asset URL for images hosted under /assets/
  /// Commonly used for motif thumbnails at /assets/motifs/
  static String getAssetUrl(String relativePath) {
    // Remove leading slash if present
    final cleanPath =
        relativePath.startsWith('/') ? relativePath.substring(1) : relativePath;
    final base = ApiConstants.baseUrl.endsWith('/')
        ? ApiConstants.baseUrl.substring(0, ApiConstants.baseUrl.length - 1)
        : ApiConstants.baseUrl;
    return '$base/$cleanPath';
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
