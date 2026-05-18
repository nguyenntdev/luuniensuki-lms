import 'package:cached_network_image/cached_network_image.dart';
import 'package:flutter/material.dart';

import '../../../core/utils/url_utils.dart';

/// Cached network image with automatic URL fallback retries.
class ResilientCachedNetworkImage extends StatefulWidget {
  final String? imageUrl;
  final String fallbackUrl;
  final BoxFit fit;
  final double? width;
  final double? height;
  final PlaceholderWidgetBuilder? placeholder;
  final LoadingErrorWidgetBuilder? errorWidget;
  final Widget? emptyWidget;

  const ResilientCachedNetworkImage({
    super.key,
    required this.imageUrl,
    this.fallbackUrl = '',
    this.fit = BoxFit.cover,
    this.width,
    this.height,
    this.placeholder,
    this.errorWidget,
    this.emptyWidget,
  });

  @override
  State<ResilientCachedNetworkImage> createState() =>
      _ResilientCachedNetworkImageState();
}

class _ResilientCachedNetworkImageState
    extends State<ResilientCachedNetworkImage> {
  int _currentIndex = 0;
  bool _isSwitching = false;

  @override
  void didUpdateWidget(covariant ResilientCachedNetworkImage oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.imageUrl != widget.imageUrl ||
        oldWidget.fallbackUrl != widget.fallbackUrl) {
      _currentIndex = 0;
      _isSwitching = false;
    }
  }

  void _switchToNextCandidate(int candidateCount) {
    if (_isSwitching || _currentIndex >= candidateCount - 1) {
      return;
    }

    _isSwitching = true;
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (!mounted) {
        return;
      }
      setState(() {
        _currentIndex += 1;
        _isSwitching = false;
      });
    });
  }

  @override
  Widget build(BuildContext context) {
    final candidates = UrlUtils.getImageUrlCandidates(
      widget.imageUrl,
      fallback: widget.fallbackUrl,
    );

    if (candidates.isEmpty) {
      return widget.emptyWidget ?? const SizedBox.shrink();
    }

    if (_currentIndex >= candidates.length) {
      _currentIndex = candidates.length - 1;
    }

    final currentUrl = candidates[_currentIndex];

    return CachedNetworkImage(
      key: ValueKey(currentUrl),
      imageUrl: currentUrl,
      fit: widget.fit,
      width: widget.width,
      height: widget.height,
      placeholder: widget.placeholder,
      errorWidget: (context, url, error) {
        if (_currentIndex < candidates.length - 1) {
          _switchToNextCandidate(candidates.length);
          if (widget.placeholder != null) {
            return widget.placeholder!(context, url);
          }
          return widget.emptyWidget ?? const SizedBox.shrink();
        }

        if (widget.errorWidget != null) {
          return widget.errorWidget!(context, url, error);
        }
        return widget.emptyWidget ?? const SizedBox.shrink();
      },
    );
  }
}
