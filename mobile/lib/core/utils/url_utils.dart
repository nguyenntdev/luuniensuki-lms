import '../constants/api_constants.dart';

class UrlUtils {
  /// Convert a relative URL to a full URL by prepending the base URL
  static String? toFullUrl(String? url) {
    if (url == null || url.isEmpty) return null;
    if (url.startsWith('http://') || url.startsWith('https://')) {
      return url;
    }
    return '${ApiConstants.baseUrl}$url';
  }
  
  /// Get a valid image URL with fallback
  static String getImageUrl(String? url, {String fallback = ''}) {
    return toFullUrl(url) ?? fallback;
  }
}

