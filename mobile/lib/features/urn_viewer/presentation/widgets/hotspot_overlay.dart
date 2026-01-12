import 'dart:math' as math;

import 'package:flutter/material.dart';

import '../../../../core/theme/app_colors.dart';
import '../../domain/entities/urn.dart';

/// HotspotOverlay widget for displaying interactive hotspots on the 3D viewer.
/// Positions hotspots based on 3D coordinates projected to screen space.
class HotspotOverlay extends StatefulWidget {
  final Motif motif;
  final Size screenSize;
  final double cameraRotationY;
  final double cameraDistance;
  final VoidCallback onTap;

  const HotspotOverlay({
    super.key,
    required this.motif,
    required this.screenSize,
    required this.cameraRotationY,
    required this.cameraDistance,
    required this.onTap,
  });

  @override
  State<HotspotOverlay> createState() => _HotspotOverlayState();
}

class _HotspotOverlayState extends State<HotspotOverlay>
    with SingleTickerProviderStateMixin {
  late AnimationController _pulseController;
  late Animation<double> _pulseAnimation;

  @override
  void initState() {
    super.initState();
    _pulseController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 1500),
    );

    _pulseAnimation = Tween<double>(begin: 1.0, end: 1.3).animate(
      CurvedAnimation(parent: _pulseController, curve: Curves.easeInOut),
    );

    // Only pulse for undiscovered motifs
    if (!widget.motif.isDiscovered) {
      _pulseController.repeat(reverse: true);
    }
  }

  @override
  void didUpdateWidget(HotspotOverlay oldWidget) {
    super.didUpdateWidget(oldWidget);

    // Stop pulsing when discovered
    if (widget.motif.isDiscovered && _pulseController.isAnimating) {
      _pulseController.stop();
      _pulseController.value = 0;
    }
  }

  @override
  void dispose() {
    _pulseController.dispose();
    super.dispose();
  }

  /// Calculate screen position from 3D coordinates.
  /// This is a simplified projection - actual positioning is handled by model_viewer_plus.
  Offset _calculateScreenPosition() {
    final motif = widget.motif;

    // Simple orthographic-like projection for overlay positioning
    // The actual hotspot interaction is handled by model-viewer HTML hotspots
    final centerX = widget.screenSize.width / 2;
    final centerY = widget.screenSize.height / 2;

    // Apply rotation transform
    final cosTheta = math.cos(widget.cameraRotationY);
    final sinTheta = math.sin(widget.cameraRotationY);

    // Rotate point around Y axis
    final rotatedX = motif.posX * cosTheta - motif.posZ * sinTheta;
    final rotatedZ = motif.posX * sinTheta + motif.posZ * cosTheta;

    // Project to screen space (simplified)
    final scale = widget.screenSize.width / (widget.cameraDistance * 2);
    final screenX = centerX + rotatedX * scale;
    final screenY = centerY - motif.posY * scale * 0.8; // Y is inverted

    // Check if point is in front of camera
    if (rotatedZ > 0) {
      // Behind camera - move off screen
      return const Offset(-100, -100);
    }

    return Offset(screenX, screenY);
  }

  Color _getHotspotColor() {
    if (widget.motif.isMastered) {
      return AppColors.statusMastered;
    } else if (widget.motif.isLearned) {
      return AppColors.statusLearned;
    } else if (widget.motif.isDiscovered) {
      return AppColors.statusDiscovered;
    } else {
      return AppColors.primary;
    }
  }

  IconData _getHotspotIcon() {
    if (widget.motif.isMastered) {
      return Icons.star;
    } else if (widget.motif.isLearned) {
      return Icons.school;
    } else if (widget.motif.isDiscovered) {
      return Icons.check;
    } else {
      return Icons.touch_app;
    }
  }

  @override
  Widget build(BuildContext context) {
    // Skip if no valid position
    if (!widget.motif.hasValidPosition) {
      return const SizedBox.shrink();
    }

    final position = _calculateScreenPosition();
    final color = _getHotspotColor();
    final icon = _getHotspotIcon();
    final isDiscovered = widget.motif.isDiscovered;

    // Check if position is within screen bounds
    if (position.dx < -50 ||
        position.dx > widget.screenSize.width + 50 ||
        position.dy < -50 ||
        position.dy > widget.screenSize.height + 50) {
      return const SizedBox.shrink();
    }

    return Positioned(
      left: position.dx - 20,
      top: position.dy - 20,
      child: GestureDetector(
        onTap: widget.onTap,
        child: AnimatedBuilder(
          animation: _pulseAnimation,
          builder: (context, child) {
            final scale = isDiscovered ? 1.0 : _pulseAnimation.value;

            return Transform.scale(
              scale: scale,
              child: Container(
                width: 40,
                height: 40,
                decoration: BoxDecoration(
                  color: color.withOpacity(0.9),
                  shape: BoxShape.circle,
                  border: Border.all(
                    color: Colors.white,
                    width: 2,
                  ),
                  boxShadow: [
                    BoxShadow(
                      color: color.withOpacity(0.5),
                      blurRadius: 12,
                      spreadRadius: 2,
                    ),
                    BoxShadow(
                      color: color.withOpacity(0.3),
                      blurRadius: 24,
                      spreadRadius: 4,
                    ),
                  ],
                ),
                child: Icon(
                  icon,
                  color: Colors.white,
                  size: 20,
                ),
              ),
            );
          },
        ),
      ),
    );
  }
}

/// A smaller, simpler hotspot marker for list views or mini-maps.
class HotspotMarker extends StatelessWidget {
  final Motif motif;
  final double size;
  final VoidCallback? onTap;

  const HotspotMarker({
    super.key,
    required this.motif,
    this.size = 24,
    this.onTap,
  });

  Color _getColor() {
    if (motif.isMastered) {
      return AppColors.statusMastered;
    } else if (motif.isLearned) {
      return AppColors.statusLearned;
    } else if (motif.isDiscovered) {
      return AppColors.statusDiscovered;
    } else {
      return AppColors.statusHidden;
    }
  }

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        width: size,
        height: size,
        decoration: BoxDecoration(
          color: _getColor(),
          shape: BoxShape.circle,
          border: Border.all(
            color: Colors.white,
            width: 1,
          ),
        ),
      ),
    );
  }
}
