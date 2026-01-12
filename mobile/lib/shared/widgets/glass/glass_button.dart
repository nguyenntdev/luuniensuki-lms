import 'package:flutter/material.dart';

import '../../../core/theme/app_colors.dart';

/// A button with glassmorphism styling
/// Uses gradient or semi-transparent background without BackdropFilter
class GlassButton extends StatelessWidget {
  final String text;
  final VoidCallback? onPressed;
  final bool isLoading;
  final bool isPrimary;
  final double? height;
  final double? width;
  final IconData? icon;
  final EdgeInsets? padding;

  const GlassButton({
    super.key,
    required this.text,
    this.onPressed,
    this.isLoading = false,
    this.isPrimary = true,
    this.height,
    this.width,
    this.icon,
    this.padding,
  });

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      height: height ?? 56,
      width: width,
      child: Material(
        color: Colors.transparent,
        child: InkWell(
          onTap: isLoading ? null : onPressed,
          borderRadius: BorderRadius.circular(12),
          splashColor: isPrimary
              ? Colors.white.withOpacity(0.2)
              : AppColors.primary.withOpacity(0.2),
          child: Ink(
            decoration: BoxDecoration(
              gradient: isPrimary
                  ? LinearGradient(
                      colors: [
                        AppColors.primary,
                        AppColors.primaryLight,
                      ],
                      begin: Alignment.topLeft,
                      end: Alignment.bottomRight,
                    )
                  : null,
              color: isPrimary ? null : Colors.white.withOpacity(0.1),
              borderRadius: BorderRadius.circular(12),
              border: isPrimary
                  ? null
                  : Border.all(
                      color: Colors.white.withOpacity(0.2),
                      width: 1.5,
                    ),
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
                            isPrimary
                                ? const Color(0xFF1A1A2E)
                                : Colors.white,
                          ),
                        ),
                      )
                    : Row(
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
                            text,
                            style: TextStyle(
                              fontSize: 16,
                              fontWeight: FontWeight.w600,
                              color: isPrimary
                                  ? const Color(0xFF1A1A2E)
                                  : Colors.white,
                              letterSpacing: 0.5,
                            ),
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
          onTap: onPressed,
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
