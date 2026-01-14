import 'package:flutter/material.dart';
import 'package:shimmer/shimmer.dart';

import '../../../core/theme/app_colors.dart';
import '../../../core/theme/app_spacing.dart';

/// Base shimmer skeleton component
/// Uses app colors to match dark theme
class ShimmerSkeleton extends StatelessWidget {
  final double? width;
  final double? height;
  final BorderRadius? borderRadius;
  final EdgeInsetsGeometry? margin;

  const ShimmerSkeleton({
    super.key,
    this.width,
    this.height,
    this.borderRadius,
    this.margin,
  });

  @override
  Widget build(BuildContext context) {
    return Shimmer.fromColors(
      baseColor: AppColors.surface,
      highlightColor: AppColors.surfaceElevated,
      child: Container(
        width: width,
        height: height,
        margin: margin,
        decoration: BoxDecoration(
          color: AppColors.surface,
          borderRadius: borderRadius ?? BorderRadius.circular(AppSpacing.radiusMD),
        ),
      ),
    );
  }
}

/// Shimmer skeleton for UrnCard
/// Matches the UrnCard design with glass effect
class ShimmerUrnCard extends StatelessWidget {
  const ShimmerUrnCard({super.key});

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: BoxDecoration(
        gradient: LinearGradient(
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
          colors: [
            Colors.white.withOpacity(0.12),
            Colors.white.withOpacity(0.06),
          ],
        ),
        borderRadius: BorderRadius.circular(AppSpacing.radiusLG),
        border: Border.all(
          color: Colors.white.withOpacity(0.2),
          width: 1.5,
        ),
      ),
      child: ClipRRect(
        borderRadius: BorderRadius.circular(AppSpacing.radiusLG),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            // Thumbnail shimmer
            Expanded(
              flex: 3,
              child: Shimmer.fromColors(
                baseColor: AppColors.surface,
                highlightColor: AppColors.surfaceElevated,
                child: Container(
                  color: AppColors.surface,
                ),
              ),
            ),

            // Content shimmer
            Expanded(
              flex: 2,
              child: Container(
                padding: const EdgeInsets.all(AppSpacing.md),
                decoration: BoxDecoration(
                  gradient: LinearGradient(
                    begin: Alignment.topCenter,
                    end: Alignment.bottomCenter,
                    colors: [
                      Colors.black.withOpacity(0.4),
                      Colors.black.withOpacity(0.7),
                    ],
                  ),
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  mainAxisAlignment: MainAxisAlignment.end,
                  children: [
                    // Title shimmer
                    ShimmerSkeleton(
                      width: double.infinity,
                      height: 20,
                      borderRadius: BorderRadius.circular(AppSpacing.radiusXS),
                    ),
                    const SizedBox(height: AppSpacing.sm),
                    // Subtitle shimmer
                    ShimmerSkeleton(
                      width: 120,
                      height: 14,
                      borderRadius: BorderRadius.circular(AppSpacing.radiusXS),
                    ),
                    const SizedBox(height: AppSpacing.sm),
                    // Progress bar shimmer
                    ShimmerSkeleton(
                      width: double.infinity,
                      height: 6,
                      borderRadius: BorderRadius.circular(AppSpacing.radiusXS),
                    ),
                  ],
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

/// Shimmer skeleton for MotifCard
/// Matches the collection motif card design
class ShimmerMotifCard extends StatelessWidget {
  const ShimmerMotifCard({super.key});

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: BoxDecoration(
        gradient: LinearGradient(
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
          colors: [
            Colors.white.withOpacity(0.12),
            Colors.white.withOpacity(0.06),
          ],
        ),
        borderRadius: BorderRadius.circular(AppSpacing.radiusLG),
        border: Border.all(
          color: Colors.white.withOpacity(0.2),
          width: 1.5,
        ),
      ),
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Thumbnail shimmer
            Expanded(
              child: ShimmerSkeleton(
                width: double.infinity,
                height: double.infinity,
              ),
            ),

            const SizedBox(height: 12),

            // Motif name shimmer
            ShimmerSkeleton(
              width: double.infinity,
              height: 16,
              borderRadius: BorderRadius.circular(AppSpacing.radiusXS),
            ),

            const SizedBox(height: 8),

            // Status badge shimmer
            Row(
              children: [
                ShimmerSkeleton(
                  width: 60,
                  height: 20,
                  borderRadius: BorderRadius.circular(AppSpacing.radiusSM),
                ),
                const SizedBox(width: 8),
                ShimmerSkeleton(
                  width: 50,
                  height: 20,
                  borderRadius: BorderRadius.circular(AppSpacing.radiusSM),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}

/// Shimmer skeleton for list items
/// Generic list item skeleton for various uses
class ShimmerListItem extends StatelessWidget {
  final bool showLeading;
  final bool showTrailing;
  final double height;

  const ShimmerListItem({
    super.key,
    this.showLeading = true,
    this.showTrailing = true,
    this.height = 70,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      height: height,
      margin: const EdgeInsets.symmetric(
        horizontal: AppSpacing.md,
        vertical: AppSpacing.xs,
      ),
      padding: const EdgeInsets.all(AppSpacing.md),
      decoration: BoxDecoration(
        gradient: LinearGradient(
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
          colors: [
            Colors.white.withOpacity(0.12),
            Colors.white.withOpacity(0.06),
          ],
        ),
        borderRadius: BorderRadius.circular(AppSpacing.radiusMD),
        border: Border.all(
          color: Colors.white.withOpacity(0.2),
          width: 1.5,
        ),
      ),
      child: Row(
        children: [
          // Leading icon/image shimmer
          if (showLeading) ...[
            ShimmerSkeleton(
              width: 50,
              height: 50,
              borderRadius: BorderRadius.circular(AppSpacing.radiusSM),
            ),
            const SizedBox(width: AppSpacing.md),
          ],

          // Content shimmer
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                ShimmerSkeleton(
                  width: double.infinity,
                  height: 16,
                  borderRadius: BorderRadius.circular(AppSpacing.radiusXS),
                ),
                const SizedBox(height: AppSpacing.sm),
                ShimmerSkeleton(
                  width: 150,
                  height: 12,
                  borderRadius: BorderRadius.circular(AppSpacing.radiusXS),
                ),
              ],
            ),
          ),

          // Trailing icon shimmer
          if (showTrailing) ...[
            const SizedBox(width: AppSpacing.md),
            ShimmerSkeleton(
              width: 24,
              height: 24,
              borderRadius: BorderRadius.circular(AppSpacing.radiusXS),
            ),
          ],
        ],
      ),
    );
  }
}

