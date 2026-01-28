import 'package:flutter/material.dart';
import 'dart:math' as math;

import '../../../core/theme/app_colors.dart';

/// Animated avatar with rotating gradient ring
/// Features:
/// - Smooth rotating gradient ring around avatar (3 second rotation)
/// - Gold/primary color gradient
/// - Inner avatar with shadow
/// - Level badge with glow effect
/// - Fallback to initials if no avatar URL
class AnimatedAvatarRing extends StatefulWidget {
  final String? avatarUrl;
  final String? displayName;
  final int level;
  final double size;
  final Color? ringColor;

  const AnimatedAvatarRing({
    super.key,
    this.avatarUrl,
    this.displayName,
    this.level = 1,
    this.size = 120,
    this.ringColor,
  });

  @override
  State<AnimatedAvatarRing> createState() => _AnimatedAvatarRingState();
}

class _AnimatedAvatarRingState extends State<AnimatedAvatarRing>
    with SingleTickerProviderStateMixin {
  late AnimationController _rotationController;

  @override
  void initState() {
    super.initState();
    _rotationController = AnimationController(
      vsync: this,
      duration: const Duration(seconds: 3),
    )..repeat();
  }

  @override
  void dispose() {
    _rotationController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      width: widget.size,
      height: widget.size + 30,
      child: Stack(
        alignment: Alignment.topCenter,
        children: [
          // Rotating gradient ring
          SizedBox(
            width: widget.size,
            height: widget.size,
            child: AnimatedBuilder(
              animation: _rotationController,
              builder: (context, child) {
                return Transform.rotate(
                  angle: _rotationController.value * 2 * math.pi,
                  child: child,
                );
              },
              child: Container(
                decoration: BoxDecoration(
                  shape: BoxShape.circle,
                  gradient: SweepGradient(
                    colors: [
                      widget.ringColor ?? AppColors.primary,
                      widget.ringColor ?? AppColors.primaryLight,
                      widget.ringColor ?? AppColors.primaryDark,
                      widget.ringColor ?? AppColors.primary,
                    ],
                    stops: const [0.0, 0.3, 0.7, 1.0],
                  ),
                ),
              ),
            ),
          ),

          // Inner avatar with padding and shadow
          Positioned(
            top: 4,
            child: Container(
              width: widget.size - 8,
              height: widget.size - 8,
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                color: AppColors.surface,
                boxShadow: [
                  BoxShadow(
                    color: (widget.ringColor ?? AppColors.primary).withOpacity(0.3),
                    blurRadius: 20,
                    spreadRadius: 3,
                  ),
                ],
              ),
              child: ClipOval(
                child: _buildAvatar(),
              ),
            ),
          ),

          // Level badge at bottom with glow
          Positioned(
            bottom: 0,
            child: Container(
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 6),
              decoration: BoxDecoration(
                gradient: LinearGradient(
                  colors: [
                    widget.ringColor ?? AppColors.primary,
                    widget.ringColor ?? AppColors.primaryDark,
                  ],
                ),
                borderRadius: BorderRadius.circular(20),
                boxShadow: [
                  BoxShadow(
                    color: (widget.ringColor ?? AppColors.primary).withOpacity(0.6),
                    blurRadius: 12,
                    spreadRadius: 2,
                  ),
                ],
              ),
              child: Text(
                'Lv. ${widget.level}',
                style: const TextStyle(
                  color: AppColors.onPrimary,
                  fontSize: 14,
                  fontWeight: FontWeight.bold,
                  letterSpacing: 0.5,
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildAvatar() {
    if (widget.avatarUrl != null && widget.avatarUrl!.isNotEmpty) {
      return Image.network(
        widget.avatarUrl!,
        fit: BoxFit.cover,
        errorBuilder: (_, __, ___) => _buildAvatarPlaceholder(),
      );
    }
    return _buildAvatarPlaceholder();
  }

  Widget _buildAvatarPlaceholder() {
    final initial = _getInitial();
    return Container(
      decoration: BoxDecoration(
        gradient: LinearGradient(
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
          colors: [
            AppColors.primary.withOpacity(0.3),
            AppColors.primaryDark.withOpacity(0.1),
          ],
        ),
      ),
      child: Center(
        child: Text(
          initial,
          style: TextStyle(
            color: AppColors.primary,
            fontSize: widget.size * 0.4,
            fontWeight: FontWeight.bold,
          ),
        ),
      ),
    );
  }

  String _getInitial() {
    if (widget.displayName != null && widget.displayName!.isNotEmpty) {
      return widget.displayName![0].toUpperCase();
    }
    return '?';
  }
}

