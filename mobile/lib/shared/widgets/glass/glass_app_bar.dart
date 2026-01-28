import 'dart:ui';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import '../../theme/glass_theme.dart';

/// A glassmorphic app bar with backdrop blur effect
/// Provides a floating glass appearance at the top of the screen
class GlassAppBar extends StatelessWidget implements PreferredSizeWidget {
  final Widget? title;
  final List<Widget>? actions;
  final Widget? leading;
  final bool automaticallyImplyLeading;
  final double? elevation;
  final Color? backgroundColor;
  final double? blurSigma;
  final PreferredSizeWidget? bottom;
  final bool centerTitle;
  final double? titleSpacing;
  final double toolbarHeight;
  final SystemUiOverlayStyle? systemOverlayStyle;

  const GlassAppBar({
    super.key,
    this.title,
    this.actions,
    this.leading,
    this.automaticallyImplyLeading = true,
    this.elevation,
    this.backgroundColor,
    this.blurSigma,
    this.bottom,
    this.centerTitle = true,
    this.titleSpacing,
    this.toolbarHeight = kToolbarHeight,
    this.systemOverlayStyle,
  });

  @override
  Size get preferredSize => Size.fromHeight(
        toolbarHeight + (bottom?.preferredSize.height ?? 0.0),
      );

  @override
  Widget build(BuildContext context) {
    final effectiveBlur = blurSigma ?? GlassTheme.blurSigma;

    return ClipRRect(
      child: BackdropFilter(
        filter: ImageFilter.blur(
          sigmaX: effectiveBlur,
          sigmaY: effectiveBlur,
        ),
        child: AppBar(
          title: title,
          actions: actions,
          leading: leading,
          automaticallyImplyLeading: automaticallyImplyLeading,
          backgroundColor: backgroundColor ??
              GlassTheme.glassBackgroundStrong.withOpacity(0.3),
          elevation: elevation ?? 0,
          centerTitle: centerTitle,
          titleSpacing: titleSpacing,
          toolbarHeight: toolbarHeight,
          systemOverlayStyle: systemOverlayStyle ??
              SystemUiOverlayStyle.light.copyWith(
                statusBarColor: Colors.transparent,
              ),
          bottom: bottom,
          shape: const Border(
            bottom: BorderSide(
              color: GlassTheme.glassBorder,
              width: GlassTheme.borderWidth,
            ),
          ),
        ),
      ),
    );
  }
}

/// Sliver variant of glass app bar for use in CustomScrollView
class GlassSliverAppBar extends StatelessWidget {
  final Widget? title;
  final List<Widget>? actions;
  final Widget? leading;
  final bool automaticallyImplyLeading;
  final double? elevation;
  final Color? backgroundColor;
  final double? blurSigma;
  final Widget? flexibleSpace;
  final PreferredSizeWidget? bottom;
  final bool pinned;
  final bool floating;
  final bool snap;
  final double expandedHeight;
  final double toolbarHeight;
  final bool centerTitle;
  final SystemUiOverlayStyle? systemOverlayStyle;

  const GlassSliverAppBar({
    super.key,
    this.title,
    this.actions,
    this.leading,
    this.automaticallyImplyLeading = true,
    this.elevation,
    this.backgroundColor,
    this.blurSigma,
    this.flexibleSpace,
    this.bottom,
    this.pinned = false,
    this.floating = false,
    this.snap = false,
    this.expandedHeight = kToolbarHeight,
    this.toolbarHeight = kToolbarHeight,
    this.centerTitle = true,
    this.systemOverlayStyle,
  });

  @override
  Widget build(BuildContext context) {
    final effectiveBlur = blurSigma ?? GlassTheme.blurSigma;

    return SliverAppBar(
      title: title,
      actions: actions,
      leading: leading,
      automaticallyImplyLeading: automaticallyImplyLeading,
      backgroundColor:
          backgroundColor ?? GlassTheme.glassBackgroundStrong.withOpacity(0.3),
      elevation: elevation ?? 0,
      centerTitle: centerTitle,
      toolbarHeight: toolbarHeight,
      pinned: pinned,
      floating: floating,
      snap: snap,
      expandedHeight: expandedHeight,
      systemOverlayStyle: systemOverlayStyle ??
          SystemUiOverlayStyle.light.copyWith(
            statusBarColor: Colors.transparent,
          ),
      bottom: bottom,
      flexibleSpace: flexibleSpace != null
          ? ClipRRect(
              child: BackdropFilter(
                filter: ImageFilter.blur(
                  sigmaX: effectiveBlur,
                  sigmaY: effectiveBlur,
                ),
                child: flexibleSpace,
              ),
            )
          : null,
    );
  }
}
