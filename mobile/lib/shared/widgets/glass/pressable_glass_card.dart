import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import '../../../core/theme/app_colors.dart';

/// A pressable card with glassmorphism styling and 3D depth effect
/// 
/// Features:
/// - Scale down animation on press (default: 0.97)
/// - Translate Y for depth illusion (default: 4.0px)
/// - Dynamic shadow blur reduction on press (15 → 5)
/// - Haptic feedback on tap
/// - Smooth animations with customizable curves
/// - Optional border highlight on press
class PressableGlassCard extends StatefulWidget {
  final Widget child;
  final VoidCallback? onTap;
  final VoidCallback? onLongPress;
  final bool enable3DEffect;
  final double pressScale;
  final double pressDepth;
  final BorderRadius? borderRadius;
  final EdgeInsets? padding;
  final Gradient? gradient;
  final List<BoxShadow>? shadows;
  final Color? backgroundColor;
  final double opacity;
  final Border? border;

  const PressableGlassCard({
    super.key,
    required this.child,
    this.onTap,
    this.onLongPress,
    this.enable3DEffect = true,
    this.pressScale = 0.97,
    this.pressDepth = 4.0,
    this.borderRadius,
    this.padding,
    this.gradient,
    this.shadows,
    this.backgroundColor,
    this.opacity = 0.08,
    this.border,
  });

  @override
  State<PressableGlassCard> createState() => _PressableGlassCardState();
}

class _PressableGlassCardState extends State<PressableGlassCard>
    with SingleTickerProviderStateMixin {
  late AnimationController _controller;
  late Animation<double> _scaleAnimation;
  late Animation<double> _depthAnimation;
  late Animation<double> _shadowAnimation;

  bool _isPressed = false;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      duration: const Duration(milliseconds: 150),
      vsync: this,
    );

    _scaleAnimation = Tween<double>(
      begin: 1.0,
      end: widget.pressScale,
    ).animate(CurvedAnimation(
      parent: _controller,
      curve: Curves.easeInOut,
    ));

    _depthAnimation = Tween<double>(
      begin: 0.0,
      end: widget.pressDepth,
    ).animate(CurvedAnimation(
      parent: _controller,
      curve: Curves.easeInOut,
    ));

    _shadowAnimation = Tween<double>(
      begin: 15.0,
      end: 5.0,
    ).animate(CurvedAnimation(
      parent: _controller,
      curve: Curves.easeInOut,
    ));
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  void _handleTapDown(TapDownDetails details) {
    if (widget.enable3DEffect) {
      setState(() => _isPressed = true);
      _controller.forward();
    }
  }

  void _handleTapUp(TapUpDetails details) {
    if (widget.enable3DEffect) {
      setState(() => _isPressed = false);
      _controller.reverse();
    }
    if (widget.onTap != null) {
      HapticFeedback.lightImpact();
      widget.onTap!();
    }
  }

  void _handleTapCancel() {
    if (widget.enable3DEffect) {
      setState(() => _isPressed = false);
      _controller.reverse();
    }
  }

  void _handleLongPress() {
    if (widget.onLongPress != null) {
      HapticFeedback.mediumImpact();
      widget.onLongPress!();
    }
  }

  @override
  Widget build(BuildContext context) {
    final effectiveBorderRadius =
        widget.borderRadius ?? BorderRadius.circular(20);

    return GestureDetector(
      onTapDown: widget.onTap != null ? _handleTapDown : null,
      onTapUp: widget.onTap != null ? _handleTapUp : null,
      onTapCancel: widget.onTap != null ? _handleTapCancel : null,
      onLongPress: widget.onLongPress != null ? _handleLongPress : null,
      child: AnimatedBuilder(
        animation: _controller,
        builder: (context, child) {
          return Transform.scale(
            scale: _scaleAnimation.value,
            child: Transform.translate(
              offset: Offset(0, _depthAnimation.value),
              child: child,
            ),
          );
        },
        child: Container(
          padding: widget.padding ?? const EdgeInsets.all(20),
          decoration: BoxDecoration(
            gradient: widget.gradient,
            color: widget.gradient == null
                ? (widget.backgroundColor ??
                    AppColors.glassWhite.withOpacity(widget.opacity))
                : null,
            borderRadius: effectiveBorderRadius,
            border: widget.border ??
                Border.all(
                  color: _isPressed
                      ? AppColors.primary.withOpacity(0.4)
                      : AppColors.glassBorder,
                  width: 1.5,
                ),
            boxShadow: widget.shadows ??
                [
                  BoxShadow(
                    color: AppColors.black.withOpacity(0.25),
                    blurRadius: _shadowAnimation.value,
                    offset: const Offset(0, 12),
                  ),
                ],
          ),
          child: widget.child,
        ),
      ),
    );
  }
}

