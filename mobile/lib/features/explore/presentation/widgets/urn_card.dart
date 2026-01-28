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

class _UrnCardState extends State<UrnCard> with TickerProviderStateMixin {
  bool _isPressed = false;
  late AnimationController _glowController;
  late AnimationController _pulseController;
  late Animation<double> _pulseAnimation;

  @override
  void initState() {
    super.initState();

    // Glow animation controller for rotating border gradient (3 seconds)
    _glowController = AnimationController(
      vsync: this,
      duration: const Duration(seconds: 3),
    );

    // Pulse animation controller for scale effect (2 seconds)
    _pulseController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 2000),
    );

    _pulseAnimation = Tween<double>(
      begin: 1.0,
      end: 1.02,
    ).animate(CurvedAnimation(
      parent: _pulseController,
      curve: Curves.easeInOut,
    ));

    // Start animations if urn has progress or is completed
    if (widget.urn.hasProgress || widget.urn.isCompleted) {
      _glowController.repeat();
      _pulseController.repeat(reverse: true);
    }
  }

  @override
  void dispose() {
    _glowController.dispose();
    _pulseController.dispose();
    super.dispose();
  }

  @override
  void didUpdateWidget(UrnCard oldWidget) {
    super.didUpdateWidget(oldWidget);

    // Update animations if progress status changes
    if (oldWidget.urn.hasProgress != widget.urn.hasProgress ||
        oldWidget.urn.isCompleted != widget.urn.isCompleted) {
      if (widget.urn.hasProgress || widget.urn.isCompleted) {
        _glowController.repeat();
        _pulseController.repeat(reverse: true);
      } else {
        _glowController.stop();
        _pulseController.stop();
      }
    }
  }

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
          child: AnimatedBuilder(
            animation: Listenable.merge([_glowController, _pulseController]),
            builder: (context, child) {
              // Apply pulse scale only if urn has progress
              final scale = _isPressed
                  ? 0.95
                  : (widget.urn.hasProgress ? _pulseAnimation.value : 1.0);

              final hasProgress = widget.urn.hasProgress;
              final isCompleted = widget.urn.isCompleted;

              // Determine glow color based on status
              Color glowColor;
              if (isCompleted) {
                glowColor = AppColors.success;
              } else if (hasProgress) {
                glowColor = AppColors.primary;
              } else {
                glowColor = Colors.transparent;
              }

              // Animated shadow intensity based on pulse
              final shadowIntensity = hasProgress || isCompleted
                  ? 0.15 + (_pulseAnimation.value - 1.0) * 2.5
                  : 0.0;

              return Transform.scale(
                scale: scale,
                child: Stack(
                  children: [
                    // Main card container
                    Container(
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
                            color: glowColor.withOpacity(shadowIntensity),
                            blurRadius: 30,
                            spreadRadius: -5,
                          ),
                        ],
                      ),
                      child: ClipRRect(
                        borderRadius: BorderRadius.circular(AppSpacing.radiusLG),
                        child: _buildCardContent(isCompact, nameSize, subtitleSize, infoPadding),
                      ),
                    ),

                    // Animated rotating gradient border for completed/in-progress urns
                    if (hasProgress || isCompleted)
                      Positioned.fill(
                        child: IgnorePointer(
                          child: Container(
                            decoration: BoxDecoration(
                              borderRadius: BorderRadius.circular(AppSpacing.radiusLG),
                              border: Border.all(
                                color: glowColor.withOpacity(0.3 + shadowIntensity),
                                width: 2.0,
                              ),
                            ),
                          ),
                        ),
                      ),
                  ],
                ),
              );
            },
          ),
        );
      },
    );
  }

  Widget _buildCardContent(bool isCompact, double nameSize, double subtitleSize, double infoPadding) {
    return Column(
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
                child: _buildProgressBadge(isCompact),
              ),

              // Demo badge
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
                      style: TextStyle(
                        color: Colors.white,
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
                          color: Colors.white.withOpacity(0.65),
                          fontSize: subtitleSize,
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
    );
  }

  Widget _buildThumbnail() {
    if (widget.urn.thumbnailUrl != null && widget.urn.thumbnailUrl!.isNotEmpty) {
      // Convert relative URL to full URL
      final imageUrl = UrlUtils.getImageUrl(widget.urn.thumbnailUrl);

      return Hero(
        tag: 'urn_image_${widget.urn.slug}',
        child: CachedNetworkImage(
          imageUrl: imageUrl,
          fit: BoxFit.cover,
          placeholder: (context, url) => _buildPlaceholder(),
          errorWidget: (context, url, error) {
            debugPrint('[MOTIF_IMAGE] Failed to load urn thumbnail: $imageUrl - Error: $error');
            return _buildPlaceholder();
          },
        ),
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

  Widget _buildProgressBadge(bool isCompact) {
    final percent = (widget.urn.progressPercent * 100).round();
    final isCompleted = widget.urn.isCompleted;
    final fontSize = isCompact ? 11.0 : 13.0;
    final iconSize = isCompact ? 13.0 : 15.0;

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
            Icon(
              Icons.check_circle,
              color: Colors.white,
              size: iconSize,
            ),
            AppSpacing.horizontalSpaceXS,
          ],
          Text(
            '$percent%',
            style: TextStyle(
              color: Colors.white,
              fontSize: fontSize,
              fontWeight: FontWeight.bold,
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
