import 'package:flutter/material.dart';
import '../../theme/glass_theme.dart';
import 'true_glass_container.dart';

/// Shows a glassmorphism dialog with blur effect
Future<T?> showGlassDialog<T>({
  required BuildContext context,
  required Widget child,
  bool barrierDismissible = true,
  Color? barrierColor,
  String? barrierLabel,
  bool useSafeArea = true,
  RouteSettings? routeSettings,
}) {
  return showDialog<T>(
    context: context,
    barrierDismissible: barrierDismissible,
    barrierColor: barrierColor ?? Colors.black.withOpacity(0.5),
    barrierLabel: barrierLabel,
    useSafeArea: useSafeArea,
    routeSettings: routeSettings,
    builder: (context) => GlassDialogContent(
      child: child,
    ),
  );
}

/// The content wrapper for glass dialog
class GlassDialogContent extends StatelessWidget {
  final Widget child;
  final EdgeInsets? padding;

  const GlassDialogContent({
    super.key,
    required this.child,
    this.padding,
  });

  @override
  Widget build(BuildContext context) {
    return Dialog(
      backgroundColor: Colors.transparent,
      elevation: 0,
      insetPadding: const EdgeInsets.all(GlassTheme.spaceXL),
      child: TrueGlassContainer(
        blurSigma: GlassTheme.blurSigmaStrong,
        opacity: 0.15,
        borderColor: GlassTheme.glassBorderActive,
        borderWidth: GlassTheme.borderWidthActive,
        boxShadow: GlassTheme.glassShadowStrong,
        padding: padding ??
            const EdgeInsets.all(GlassTheme.spaceXL),
        child: child,
      ),
    );
  }
}

/// Glass alert dialog with title, content, and actions
Future<T?> showGlassAlertDialog<T>({
  required BuildContext context,
  Widget? title,
  Widget? content,
  List<Widget>? actions,
  bool barrierDismissible = true,
}) {
  return showGlassDialog<T>(
    context: context,
    barrierDismissible: barrierDismissible,
    child: Column(
      mainAxisSize: MainAxisSize.min,
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        if (title != null) ...[
          DefaultTextStyle(
            style: const TextStyle(
              color: GlassTheme.textPrimary,
              fontSize: 20,
              fontWeight: FontWeight.bold,
            ),
            child: title,
          ),
          const SizedBox(height: GlassTheme.spaceL),
        ],
        if (content != null) ...[
          DefaultTextStyle(
            style: const TextStyle(
              color: GlassTheme.textSecondary,
              fontSize: 14,
            ),
            child: content,
          ),
          const SizedBox(height: GlassTheme.spaceXL),
        ],
        if (actions != null && actions.isNotEmpty)
          Row(
            mainAxisAlignment: MainAxisAlignment.end,
            children: [
              for (int i = 0; i < actions.length; i++) ...[
                if (i > 0) const SizedBox(width: GlassTheme.spaceM),
                actions[i],
              ],
            ],
          ),
      ],
    ),
  );
}

/// Glass confirmation dialog with standard yes/no buttons
Future<bool?> showGlassConfirmDialog({
  required BuildContext context,
  required String title,
  required String message,
  String confirmText = 'Xác nhận',
  String cancelText = 'Hủy',
  bool barrierDismissible = true,
}) {
  return showGlassAlertDialog<bool>(
    context: context,
    barrierDismissible: barrierDismissible,
    title: Text(title),
    content: Text(message),
    actions: [
      TextButton(
        onPressed: () => Navigator.of(context).pop(false),
        child: Text(
          cancelText,
          style: const TextStyle(color: GlassTheme.textSecondary),
        ),
      ),
      ElevatedButton(
        onPressed: () => Navigator.of(context).pop(true),
        style: ElevatedButton.styleFrom(
          backgroundColor: GlassTheme.accentGold,
          foregroundColor: GlassTheme.textOnDark,
        ),
        child: Text(confirmText),
      ),
    ],
  );
}

