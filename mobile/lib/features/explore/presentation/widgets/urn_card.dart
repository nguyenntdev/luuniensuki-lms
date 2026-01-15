import 'package:flutter/material.dart';
import 'package:cached_network_image/cached_network_image.dart';

import '../../../../core/theme/app_colors.dart';
import '../../../../core/theme/app_spacing.dart';
import '../../../../core/utils/url_utils.dart';
import '../../domain/entities/urn.dart';

/// A glassmorphism card displaying an urn with progress indicator
class UrnCard extends StatefulWidget {
  final Urn urn;
  final VoidCallback? onTap;

  const UrnCard({
    super.key,
    required this.urn,
    this.onTap,
  });

  @override
  State<UrnCard> createState() => _UrnCardState();
}

class _UrnCardState extends State<UrnCard> with SingleTickerProviderStateMixin {
  bool _isPressed = false;

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTapDown: (_) => setState(() => _isPressed = true),
      onTapUp: (_) {
        setState(() => _isPressed = false);
        widget.onTap?.call();
      },
      onTapCancel: () => setState(() => _isPressed = false),
      child: AnimatedScale(
        scale: _isPressed ? 0.95 : 1.0,
        duration: const Duration(milliseconds: 150),
        curve: Curves.easeOut,
        child: Container(
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
            boxShadow: [
              BoxShadow(
                color: Colors.black.withOpacity(0.2),
                blurRadius: 20,
                offset: const Offset(0, 10),
              ),
              BoxShadow(
                color: AppColors.primary.withOpacity(
                  widget.urn.isCompleted ? 0.15 : 0.0,
                ),
                blurRadius: 30,
                spreadRadius: -5,
              ),
            ],
          ),
          child: ClipRRect(
            borderRadius: BorderRadius.circular(AppSpacing.radiusLG),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                // Thumbnail with progress overlay
                Expanded(
                  flex: 3,
                  child: Stack(
                    fit: StackFit.expand,
                    children: [
                      // Urn thumbnail
                      _buildThumbnail(),

                      // Gradient overlay for better text visibility
                      Positioned.fill(
                        child: DecoratedBox(
                          decoration: BoxDecoration(
                            gradient: LinearGradient(
                              begin: Alignment.topCenter,
                              end: Alignment.bottomCenter,
                              colors: [
                                Colors.transparent,
                                Colors.black.withOpacity(0.3),
                              ],
                              stops: const [0.5, 1.0],
                            ),
                          ),
                        ),
                      ),

                      // Progress overlay
                      Positioned(
                        top: AppSpacing.sm,
                        right: AppSpacing.sm,
                        child: _buildProgressBadge(),
                      ),

                      // Demo badge
                      if (widget.urn.isDemo)
                        Positioned(
                          top: AppSpacing.sm,
                          left: AppSpacing.sm,
                          child: _buildDemoBadge(),
                        ),
                    ],
                  ),
                ),

                // Info section
                Expanded(
                  flex: 2,
                  child: Container(
                    padding: const EdgeInsets.all(AppSpacing.md),
                    decoration: BoxDecoration(
                      gradient: LinearGradient(
                        begin: Alignment.topCenter,
                        end: Alignment.bottomCenter,
                        colors: [
                          Colors.white.withOpacity(0.08),
                          Colors.white.withOpacity(0.04),
                        ],
                      ),
                    ),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        // Urn name
                        Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              widget.urn.name,
                              style: const TextStyle(
                                color: Colors.white,
                                fontSize: 17,
                                fontWeight: FontWeight.bold,
                                letterSpacing: 0.2,
                              ),
                              maxLines: 1,
                              overflow: TextOverflow.ellipsis,
                            ),
                            if (widget.urn.nameEn != null &&
                                widget.urn.nameEn!.isNotEmpty) ...[
                              AppSpacing.verticalSpaceXS,
                              Text(
                                widget.urn.nameEn!,
                                style: TextStyle(
                                  color: Colors.white.withOpacity(0.65),
                                  fontSize: 12,
                                  fontStyle: FontStyle.italic,
                                ),
                                maxLines: 1,
                                overflow: TextOverflow.ellipsis,
                              ),
                            ],
                          ],
                        ),

                        // Progress bar and stats
                        Column(
                          children: [
                            // Progress bar
                            _buildProgressBar(),
                            AppSpacing.verticalSpaceXS,
                            // Stats row
                            _buildStatsRow(),
                          ],
                        ),
                      ],
                    ),
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildThumbnail() {
    if (widget.urn.thumbnailUrl != null && widget.urn.thumbnailUrl!.isNotEmpty) {
      // Convert relative URL to full URL
      final imageUrl = UrlUtils.getImageUrl(widget.urn.thumbnailUrl);

      return CachedNetworkImage(
        imageUrl: imageUrl,
        fit: BoxFit.cover,
        placeholder: (context, url) => _buildPlaceholder(),
        errorWidget: (context, url, error) {
          debugPrint('[MOTIF_IMAGE] Failed to load urn thumbnail: $imageUrl - Error: $error');
          return _buildPlaceholder();
        },
      );
    }
    return _buildPlaceholder();
  }

  Widget _buildPlaceholder() {
    return Container(
      decoration: BoxDecoration(
        gradient: LinearGradient(
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
          colors: [
            AppColors.surfaceElevated,
            AppColors.surface,
          ],
        ),
      ),
      child: Center(
        child: Icon(
          Icons.account_balance,
          size: 52,
          color: Colors.white.withOpacity(0.3),
        ),
      ),
    );
  }

  Widget _buildProgressBadge() {
    final percent = (widget.urn.progressPercent * 100).round();
    final isCompleted = widget.urn.isCompleted;

    return Container(
      padding: const EdgeInsets.symmetric(
        horizontal: AppSpacing.sm + 2,
        vertical: AppSpacing.xs + 2,
      ),
      decoration: BoxDecoration(
        gradient: isCompleted
            ? LinearGradient(
                colors: [AppColors.success, AppColors.success.withOpacity(0.8)],
              )
            : LinearGradient(
                colors: [
                  AppColors.surface.withOpacity(0.9),
                  AppColors.surface.withOpacity(0.85),
                ],
              ),
        borderRadius: BorderRadius.circular(AppSpacing.radiusSM + 4),
        border: Border.all(
          color: isCompleted
              ? AppColors.success
              : Colors.white.withOpacity(0.25),
          width: 1.5,
        ),
        boxShadow: [
          BoxShadow(
            color: isCompleted
                ? AppColors.success.withOpacity(0.3)
                : Colors.black.withOpacity(0.3),
            blurRadius: 8,
            offset: const Offset(0, 2),
          ),
        ],
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          if (isCompleted) ...[
            const Icon(
              Icons.check_circle,
              color: Colors.white,
              size: 15,
            ),
            AppSpacing.horizontalSpaceXS,
          ],
          Text(
            '$percent%',
            style: const TextStyle(
              color: Colors.white,
              fontSize: 13,
              fontWeight: FontWeight.bold,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildDemoBadge() {
    return Container(
      padding: const EdgeInsets.symmetric(
        horizontal: AppSpacing.sm,
        vertical: AppSpacing.xs,
      ),
      decoration: BoxDecoration(
        gradient: LinearGradient(
          colors: [AppColors.primary, AppColors.primaryLight],
        ),
        borderRadius: BorderRadius.circular(AppSpacing.radiusSM),
        boxShadow: [
          BoxShadow(
            color: AppColors.primary.withOpacity(0.4),
            blurRadius: 8,
            offset: const Offset(0, 2),
          ),
        ],
      ),
      child: Text(
        'DEMO',
        style: TextStyle(
          color: AppColors.onPrimary,
          fontSize: 11,
          fontWeight: FontWeight.bold,
          letterSpacing: 0.5,
        ),
      ),
    );
  }

  Widget _buildProgressBar() {
    return Container(
      height: 7,
      decoration: BoxDecoration(
        color: Colors.white.withOpacity(0.15),
        borderRadius: BorderRadius.circular(AppSpacing.radiusXS),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.2),
            blurRadius: 4,
            offset: const Offset(0, 1),
          ),
        ],
      ),
      child: ClipRRect(
        borderRadius: BorderRadius.circular(AppSpacing.radiusXS),
        child: Stack(
          children: [
            FractionallySizedBox(
              alignment: Alignment.centerLeft,
              widthFactor: widget.urn.progressPercent.clamp(0.0, 1.0),
              child: Container(
                decoration: BoxDecoration(
                  gradient: LinearGradient(
                    colors: [AppColors.primary, AppColors.primaryLight],
                  ),
                ),
              ),
            ),
            // Shine effect
            Positioned.fill(
              child: DecoratedBox(
                decoration: BoxDecoration(
                  gradient: LinearGradient(
                    begin: Alignment.topCenter,
                    end: Alignment.bottomCenter,
                    colors: [
                      Colors.white.withOpacity(0.3),
                      Colors.transparent,
                    ],
                    stops: const [0.0, 0.5],
                  ),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildStatsRow() {
    return LayoutBuilder(
      builder: (context, constraints) {
        final stats = [
          _buildStatItem(
            icon: Icons.visibility_outlined,
            count: widget.urn.discoveredCount,
            total: widget.urn.motifCount,
            color: AppColors.info,
          ),
          _buildStatItem(
            icon: Icons.school_outlined,
            count: widget.urn.learnedCount,
            total: widget.urn.motifCount,
            color: AppColors.success,
          ),
          _buildStatItem(
            icon: Icons.star_outline,
            count: widget.urn.masteredCount,
            total: widget.urn.motifCount,
            color: AppColors.primary,
          ),
        ];

        if (constraints.maxWidth < 170) {
          return Wrap(
            spacing: AppSpacing.xs,
            runSpacing: AppSpacing.xs,
            alignment: WrapAlignment.spaceBetween,
            children: stats,
          );
        }

        return Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: stats,
        );
      },
    );
  }

  Widget _buildStatItem({
    required IconData icon,
    required int count,
    required int total,
    required Color color,
  }) {
    return Container(
      padding: const EdgeInsets.symmetric(
        horizontal: AppSpacing.xs + 2,
        vertical: AppSpacing.xs,
      ),
      decoration: BoxDecoration(
        color: color.withOpacity(0.15),
        borderRadius: BorderRadius.circular(AppSpacing.radiusXS),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(
            icon,
            size: 14,
            color: color.withOpacity(0.9),
          ),
          AppSpacing.horizontalSpaceXS,
          Text(
            '$count/$total',
            style: TextStyle(
              color: Colors.white.withOpacity(0.8),
              fontSize: 11,
              fontWeight: FontWeight.w600,
            ),
          ),
        ],
      ),
    );
  }
}
