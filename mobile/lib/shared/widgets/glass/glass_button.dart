import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import '../../../core/theme/app_colors.dart';

/// A button with glassmorphism styling
/// Uses gradient or semi-transparent background without BackdropFilter
class GlassButton extends StatelessWidget {
  final String? text;
  final Widget? child;
  final VoidCallback? onPressed;
  final bool isLoading;
  final bool isPrimary;
  final double? height;
  final double? width;
  final IconData? icon;
  final EdgeInsets? padding;
  final Gradient? gradient;

  const GlassButton({
    super.key,
    this.text,
    this.child,
    this.onPressed,
    this.isLoading = false,
    this.isPrimary = true,
    this.height,
    this.width,
    this.icon,
    this.padding,
    this.gradient,
  }) : assert(text != null || child != null,
            'Either text or child must be provided');

  @override
  Widget build(BuildContext context) {
    final labelStyle = Theme.of(context).textTheme.labelLarge?.copyWith(
          fontWeight: FontWeight.w600,
          color: isPrimary ? AppColors.onPrimary : Colors.white,
        );

    return SizedBox(
      height: height ?? 56,
      width: width,
      child: Material(
        color: Colors.transparent,
        child: InkWell(
          onTap: isLoading
              ? null
              : onPressed == null
                  ? null
                  : () {
                      HapticFeedback.mediumImpact();
                      onPressed!();
                    },
          borderRadius: BorderRadius.circular(12),
          splashColor: isPrimary
              ? Colors.white.withOpacity(0.2)
              : AppColors.primary.withOpacity(0.2),
          child: Ink(
            decoration: BoxDecoration(
              gradient: gradient ??
                  (isPrimary
                      ? LinearGradient(
                          colors: [
                            AppColors.primary,
                            AppColors.primaryLight,
                          ],
                          begin: Alignment.topLeft,
                          end: Alignment.bottomRight,
                        )
                      : null),
              color: (gradient == null && !isPrimary)
                  ? Colors.white.withOpacity(0.1)
                  : null,
              borderRadius: BorderRadius.circular(14),
              border: isPrimary
                  ? null
                  : Border.all(
                      color: Colors.white.withOpacity(0.2),
                      width: 1.5,
                    ),
              boxShadow: isPrimary
                  ? [
                      BoxShadow(
                        color: AppColors.primary.withOpacity(0.35),
                        blurRadius: 18,
                        offset: const Offset(0, 10),
                      ),
                    ]
                  : [
                      BoxShadow(
                        color: Colors.black.withOpacity(0.2),
                        blurRadius: 16,
                        offset: const Offset(0, 8),
                      ),
                    ],
            ),
            child: Container(
              padding: padding ??
                  const EdgeInsets.symmetric(
                    horizontal: 24,
                    vertical: 16,
                  ),
              child: Center(
                child: isLoading
                    ? SizedBox(
                        height: 24,
                        width: 24,
                        child: CircularProgressIndicator(
                          strokeWidth: 2.5,
                          valueColor: AlwaysStoppedAnimation<Color>(
                            isPrimary ? const Color(0xFF1A1A2E) : Colors.white,
                          ),
                        ),
                      )
                    : child ??
                        Row(
                          mainAxisSize: MainAxisSize.min,
                          mainAxisAlignment: MainAxisAlignment.center,
                          children: [
                            if (icon != null) ...[
                              Icon(
                                icon,
                                size: 20,
                                color: isPrimary
                                    ? const Color(0xFF1A1A2E)
                                    : Colors.white,
                              ),
                              const SizedBox(width: 8),
                            ],
                            Text(
                              text ?? '',
                              style: labelStyle,
                            ),
                          ],
                        ),
              ),
            ),
          ),
        ),
      ),
    );
  }
}

/// A smaller icon-only glass button
class GlassIconButton extends StatelessWidget {
  final IconData icon;
  final VoidCallback? onPressed;
  final Color? color;
  final double size;

  const GlassIconButton({
    super.key,
    required this.icon,
    this.onPressed,
    this.color,
    this.size = 48,
  });

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      width: size,
      height: size,
      child: Material(
        color: Colors.transparent,
        child: InkWell(
          onTap: onPressed == null
              ? null
              : () {
                  HapticFeedback.lightImpact();
                  onPressed!();
                },
          borderRadius: BorderRadius.circular(size / 4),
          child: Container(
            decoration: BoxDecoration(
              color: Colors.white.withOpacity(0.1),
              borderRadius: BorderRadius.circular(size / 4),
              border: Border.all(
                color: Colors.white.withOpacity(0.2),
              ),
            ),
            child: Center(
              child: Icon(
                icon,
                size: size * 0.4,
                color: color ?? Colors.white,
              ),
            ),
          ),
        ),
      ),
    );
  }
}
