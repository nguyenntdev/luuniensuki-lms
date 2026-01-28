import 'package:cached_network_image/cached_network_image.dart';
import 'package:flutter/material.dart';

import '../../../core/theme/app_colors.dart';
import '../../../core/utils/url_utils.dart';
import '../shimmer/shimmer_skeleton.dart';

/// A wrapper widget for [CachedNetworkImage] with consistent behavior across the app.
/// 
/// Features:
/// - Automatic URL resolution using [UrlUtils.getImageUrl]
/// - Default shimmer loading placeholder
/// - Default error widget with broken image icon
/// - Optional border radius for rounded corners
/// - Optional Hero animation support
/// - Handles null/empty URLs gracefully
///
/// Example:
/// ```dart
/// AppNetworkImage(
///   imageUrl: motif.thumbnailUrl,
///   width: 100,
///   height: 100,
///   borderRadius: BorderRadius.circular(12),
///   heroTag: 'motif-${motif.id}',
/// )
/// ```
class AppNetworkImage extends StatelessWidget {
  /// The image URL (can be relative or absolute, null or empty)
  final String? imageUrl;

  /// The width of the image
  final double? width;

  /// The height of the image
  final double? height;

  /// How to inscribe the image into the space allocated
  final BoxFit fit;

  /// Border radius for rounded corners
  final BorderRadius? borderRadius;

  /// Custom placeholder widget (defaults to ShimmerSkeleton)
  final Widget? placeholder;

  /// Custom error widget (defaults to broken image icon)
  final Widget? errorWidget;

  /// Optional hero tag for Hero animations
  final String? heroTag;

  /// Semantic label for accessibility (screen readers)
  final String? semanticLabel;

  const AppNetworkImage({
    super.key,
    required this.imageUrl,
    this.width,
    this.height,
    this.fit = BoxFit.cover,
    this.borderRadius,
    this.placeholder,
    this.errorWidget,
    this.heroTag,
    this.semanticLabel,
  });

  @override
  Widget build(BuildContext context) {
    // Resolve URL using UrlUtils
    final resolvedUrl = UrlUtils.getImageUrl(imageUrl);

    // If URL is null/empty, show error widget immediately
    if (resolvedUrl.isEmpty) {
      return _buildErrorWidget();
    }

    // Build the main image widget
    Widget imageWidget = ClipRRect(
      borderRadius: borderRadius ?? BorderRadius.zero,
      child: CachedNetworkImage(
        imageUrl: resolvedUrl,
        width: width,
        height: height,
        fit: fit,
        placeholder: (context, url) => _buildPlaceholder(),
        errorWidget: (context, url, error) => _buildErrorWidget(),
      ),
    );

    // Wrap with Hero if heroTag is provided
    if (heroTag != null) {
      imageWidget = Hero(
        tag: heroTag!,
        child: imageWidget,
      );
    }

    // Wrap with Semantics for accessibility
    return Semantics(
      label: semanticLabel ?? 'Hình ảnh',
      image: true,
      child: imageWidget,
    );
  }

  /// Build the placeholder widget (shown while loading)
  Widget _buildPlaceholder() {
    return placeholder ??
        ShimmerSkeleton(
          width: width,
          height: height,
          borderRadius: borderRadius,
        );
  }

  /// Build the error widget (shown when loading fails or URL is empty)
  Widget _buildErrorWidget() {
    return errorWidget ??
        Container(
          width: width,
          height: height,
          decoration: BoxDecoration(
            color: AppColors.surfaceVariant,
            borderRadius: borderRadius,
          ),
          child: Center(
            child: Icon(
              Icons.broken_image_outlined,
              size: (width != null && height != null) 
                  ? (width! < height! ? width! * 0.4 : height! * 0.4)
                  : 48,
              color: AppColors.textHint,
            ),
          ),
        );
  }
}

