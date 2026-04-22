import 'package:flutter/material.dart';

import '../../../../core/theme/app_colors.dart';
import '../../../../core/theme/app_spacing.dart';
import '../../../../shared/widgets/images/resilient_cached_network_image.dart';
import '../../domain/entities/urn.dart';

/// A liquid-glass inspired card displaying an urn with progress indicator.
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
    return LayoutBuilder(
      builder: (context, constraints) {
        final isCompact = constraints.maxWidth < 160;
        final nameSize = isCompact ? 15.0 : 17.0;
        final subtitleSize = isCompact ? 11.0 : 12.0;
        final infoPadding = isCompact ? AppSpacing.sm : AppSpacing.md;

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
                    AppColors.surfaceElevated.withOpacity(0.96),
                    AppColors.surface.withOpacity(0.9),
                    AppColors.surfaceVariant.withOpacity(0.86),
                  ],
                ),
                borderRadius: BorderRadius.circular(AppSpacing.radiusLG),
                border: Border.all(
                  color: AppColors.glassBorder.withOpacity(0.9),
                  width: 1.5,
                ),
                boxShadow: [
                  BoxShadow(
                    color: Colors.black.withOpacity(0.24),
                    blurRadius: 24,
                    offset: const Offset(0, 12),
                  ),
                  BoxShadow(
                    color: AppColors.primary.withOpacity(
                      widget.urn.isCompleted ? 0.15 : 0.0,
                    ),
                    blurRadius: 30,
                    spreadRadius: -5,
                  ),
                  BoxShadow(
                    color: Colors.white.withOpacity(0.06),
                    blurRadius: 2,
                    spreadRadius: -1,
                    offset: const Offset(0, -1),
                  ),
                ],
              ),
              child: ClipRRect(
                borderRadius: BorderRadius.circular(AppSpacing.radiusLG),
                child: Stack(
                  children: [
                    Column(
                      crossAxisAlignment: CrossAxisAlignment.stretch,
                      children: [
                        // Thumbnail with progress overlay
                        Expanded(
                          flex: 3,
                          child: Stack(
                            fit: StackFit.expand,
                            children: [
                              _buildThumbnail(),
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
                              Positioned(
                                top: AppSpacing.sm,
                                right: AppSpacing.sm,
                                child: _buildProgressBadge(isCompact),
                              ),
                              if (widget.urn.isDemo)
                                Positioned(
                                  top: AppSpacing.sm,
                                  left: AppSpacing.sm,
                                  child: _buildDemoBadge(isCompact),
                                ),
                            ],
                          ),
                        ),

                        // Info section
                        Expanded(
                          flex: 2,
                          child: Container(
                            padding: EdgeInsets.all(infoPadding),
                            decoration: BoxDecoration(
                              gradient: LinearGradient(
                                begin: Alignment.topCenter,
                                end: Alignment.bottomCenter,
                                colors: [
                                  AppColors.surfaceElevated.withOpacity(0.92),
                                  AppColors.surface.withOpacity(0.86),
                                  AppColors.surfaceVariant.withOpacity(0.8),
                                ],
                              ),
                            ),
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              mainAxisAlignment: MainAxisAlignment.spaceBetween,
                              children: [
                                Column(
                                  crossAxisAlignment: CrossAxisAlignment.start,
                                  children: [
                                    Text(
                                      widget.urn.name,
                                      style: TextStyle(
                                        color: AppColors.textPrimary,
                                        fontSize: nameSize,
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
                                          color: AppColors.textSecondary,
                                          fontSize: subtitleSize,
                                          fontStyle: FontStyle.italic,
                                        ),
                                        maxLines: 1,
                                        overflow: TextOverflow.ellipsis,
                                      ),
                                    ],
                                  ],
                                ),
                                Column(
                                  children: [
                                    _buildProgressBar(),
                                    AppSpacing.verticalSpaceXS,
                                    _buildStatsRow(),
                                  ],
                                ),
                              ],
                            ),
                          ),
                        ),
                      ],
                    ),
                    Positioned.fill(
                      child: IgnorePointer(
                        child: DecoratedBox(
                          decoration: BoxDecoration(
                            gradient: LinearGradient(
                              begin: Alignment.topLeft,
                              end: Alignment.bottomRight,
                              colors: [
                                Colors.white.withOpacity(0.14),
                                Colors.white.withOpacity(0.05),
                                Colors.transparent,
                              ],
                              stops: const [0.0, 0.18, 0.58],
                            ),
                          ),
                        ),
                      ),
                    ),
                  ],
                ),
              ),
            ),
          ),
        );
      },
    );
  }

  Widget _buildThumbnail() {
    if (widget.urn.thumbnailUrl != null &&
        widget.urn.thumbnailUrl!.isNotEmpty) {
      return ResilientCachedNetworkImage(
        imageUrl: widget.urn.thumbnailUrl,
        fit: BoxFit.cover,
        placeholder: (context, url) => _buildPlaceholder(),
        errorWidget: (context, url, error) {
          debugPrint(
            '[MOTIF_IMAGE] Failed to load urn thumbnail: $url - Error: $error',
          );
          return _buildPlaceholder();
        },
        emptyWidget: _buildPlaceholder(),
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
          color: AppColors.textSecondary.withOpacity(0.45),
        ),
      ),
    );
  }

  Widget _buildProgressBadge(bool isCompact) {
    final percent = (widget.urn.progressPercent * 100).round();
    final isCompleted = widget.urn.isCompleted;
    final fontSize = isCompact ? 11.0 : 13.0;
    final iconSize = isCompact ? 13.0 : 15.0;
    final borderRadius = BorderRadius.circular(AppSpacing.radiusSM + 4);

    return ClipRRect(
      borderRadius: borderRadius,
      child: Stack(
        children: [
          Container(
            padding: const EdgeInsets.symmetric(
              horizontal: AppSpacing.sm + 2,
              vertical: AppSpacing.xs + 2,
            ),
            decoration: BoxDecoration(
              gradient: isCompleted
                  ? LinearGradient(
                      colors: [
                        AppColors.success,
                        AppColors.success.withOpacity(0.8),
                      ],
                    )
                  : LinearGradient(
                      begin: Alignment.topLeft,
                      end: Alignment.bottomRight,
                      colors: [
                        AppColors.surface.withOpacity(0.92),
                        AppColors.surfaceVariant.withOpacity(0.86),
                      ],
                    ),
              borderRadius: borderRadius,
              border: Border.all(
                color: isCompleted
                    ? AppColors.success.withOpacity(0.9)
                    : AppColors.glassBorder.withOpacity(0.9),
                width: 1.2,
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
                  Icon(
                    Icons.check_circle,
                    color: AppColors.textPrimary,
                    size: iconSize,
                  ),
                  AppSpacing.horizontalSpaceXS,
                ],
                Text(
                  '$percent%',
                  style: TextStyle(
                    color: AppColors.textPrimary,
                    fontSize: fontSize,
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ],
            ),
          ),
          Positioned.fill(
            child: IgnorePointer(
              child: DecoratedBox(
                decoration: BoxDecoration(
                  gradient: LinearGradient(
                    begin: Alignment.topCenter,
                    end: Alignment.bottomCenter,
                    colors: [
                      Colors.white.withOpacity(0.2),
                      Colors.white.withOpacity(0.05),
                      Colors.transparent,
                    ],
                    stops: const [0.0, 0.35, 0.85],
                  ),
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildDemoBadge(bool isCompact) {
    final fontSize = isCompact ? 10.0 : 11.0;

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
          fontSize: fontSize,
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
        color: AppColors.surfaceVariant.withOpacity(0.88),
        borderRadius: BorderRadius.circular(AppSpacing.radiusXS),
        border: Border.all(
          color: AppColors.glassBorder.withOpacity(0.35),
          width: 0.8,
        ),
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
            Positioned.fill(
              child: DecoratedBox(
                decoration: BoxDecoration(
                  gradient: LinearGradient(
                    begin: Alignment.topCenter,
                    end: Alignment.bottomCenter,
                    colors: [
                      AppColors.textPrimary.withOpacity(0.25),
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
        border: Border.all(
          color: color.withOpacity(0.3),
          width: 0.8,
        ),
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
              color: AppColors.textPrimary.withOpacity(0.85),
              fontSize: 11,
              fontWeight: FontWeight.w600,
            ),
          ),
        ],
      ),
    );
  }
}
