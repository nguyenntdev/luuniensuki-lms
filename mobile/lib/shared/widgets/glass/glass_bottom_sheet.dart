import 'package:flutter/material.dart';
import '../../theme/glass_theme.dart';
import 'true_glass_container.dart';

/// Shows a glassmorphism bottom sheet with blur effect
Future<T?> showGlassBottomSheet<T>({
  required BuildContext context,
  required Widget child,
  bool isScrollControlled = false,
  bool isDismissible = true,
  bool enableDrag = true,
  Color? backgroundColor,
  double? elevation,
}) {
  return showModalBottomSheet<T>(
    context: context,
    isScrollControlled: isScrollControlled,
    isDismissible: isDismissible,
    enableDrag: enableDrag,
    backgroundColor: Colors.transparent,
    elevation: elevation ?? 0,
    builder: (context) => GlassBottomSheetContent(
      child: child,
    ),
  );
}

/// The content wrapper for glass bottom sheet
class GlassBottomSheetContent extends StatelessWidget {
  final Widget child;

  const GlassBottomSheetContent({
    super.key,
    required this.child,
  });

  @override
  Widget build(BuildContext context) {
    return TrueGlassContainer(
      blurSigma: GlassTheme.blurSigmaStrong,
      opacity: 0.15,
      borderRadius: const BorderRadius.only(
        topLeft: Radius.circular(24),
        topRight: Radius.circular(24),
      ),
      borderColor: GlassTheme.glassBorderActive,
      borderWidth: GlassTheme.borderWidthActive,
      boxShadow: GlassTheme.glassShadowStrong,
      padding: EdgeInsets.zero,
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          // Handle bar
          Container(
            margin: const EdgeInsets.only(top: 12, bottom: 8),
            width: 40,
            height: 4,
            decoration: BoxDecoration(
              color: GlassTheme.textSecondary,
              borderRadius: BorderRadius.circular(2),
            ),
          ),
          // Content
          Flexible(
            child: Padding(
              padding: const EdgeInsets.fromLTRB(
                GlassTheme.spaceL,
                GlassTheme.spaceM,
                GlassTheme.spaceL,
                GlassTheme.spaceXL,
              ),
              child: child,
            ),
          ),
        ],
      ),
    );
  }
}

/// Builder function for scrollable glass bottom sheets
Future<T?> showScrollableGlassBottomSheet<T>({
  required BuildContext context,
  required Widget Function(BuildContext) builder,
  bool isDismissible = true,
  bool enableDrag = true,
  double initialChildSize = 0.6,
  double minChildSize = 0.25,
  double maxChildSize = 0.95,
}) {
  return showModalBottomSheet<T>(
    context: context,
    isScrollControlled: true,
    isDismissible: isDismissible,
    enableDrag: enableDrag,
    backgroundColor: Colors.transparent,
    elevation: 0,
    builder: (context) => DraggableScrollableSheet(
      initialChildSize: initialChildSize,
      minChildSize: minChildSize,
      maxChildSize: maxChildSize,
      builder: (context, scrollController) {
        return GlassBottomSheetContent(
          child: SingleChildScrollView(
            controller: scrollController,
            child: builder(context),
          ),
        );
      },
    ),
  );
}

