import 'package:flutter/material.dart';

import '../../../../core/theme/app_colors.dart';
import '../../../../core/theme/app_spacing.dart';

/// Card showing an urn in the learning path with its progress and tracks.
class UrnPathCard extends StatefulWidget {
  final int urnIndex;
  final bool isCurrentUrn;

  const UrnPathCard({
    super.key,
    required this.urnIndex,
    this.isCurrentUrn = false,
  });

  @override
  State<UrnPathCard> createState() => _UrnPathCardState();
}

class _UrnPathCardState extends State<UrnPathCard>
    with SingleTickerProviderStateMixin {
  late AnimationController _animationController;
  late Animation<double> _expandAnimation;
  bool _isExpanded = false;

  @override
  void initState() {
    super.initState();
    _isExpanded = widget.isCurrentUrn;
    _animationController = AnimationController(
      duration: const Duration(milliseconds: 280),
      vsync: this,
    );
    _expandAnimation = CurvedAnimation(
      parent: _animationController,
      curve: Curves.easeInOut,
    );
    if (_isExpanded) {
      _animationController.value = 1.0;
    }
  }

  @override
  void dispose() {
    _animationController.dispose();
    super.dispose();
  }

  void _toggleExpanded() {
    setState(() {
      _isExpanded = !_isExpanded;
      if (_isExpanded) {
        _animationController.forward();
      } else {
        _animationController.reverse();
      }
    });
  }

  @override
  Widget build(BuildContext context) {
    final urnData = _getMockUrnData(widget.urnIndex);
    final isLocked = urnData.status == _UrnStatus.locked;

    return Column(
      children: [
        if (widget.urnIndex > 0) _buildPathConnector(isLocked),
        GestureDetector(
          onTap: isLocked ? null : _toggleExpanded,
          child: AnimatedContainer(
            duration: const Duration(milliseconds: 280),
            curve: Curves.easeInOut,
            decoration: BoxDecoration(
              gradient: LinearGradient(
                begin: Alignment.topLeft,
                end: Alignment.bottomRight,
                colors: _getGradientColors(urnData.status),
              ),
              borderRadius: BorderRadius.circular(AppSpacing.radiusLG),
              border: Border.all(
                color: _getBorderColor(urnData.status),
                width: widget.isCurrentUrn ? 2.4 : 1.4,
              ),
              boxShadow: [
                BoxShadow(
                  color: Colors.black.withOpacity(0.25),
                  blurRadius: 24,
                  offset: const Offset(0, 12),
                ),
                if (widget.isCurrentUrn)
                  BoxShadow(
                    color: AppColors.primary.withOpacity(0.25),
                    blurRadius: 28,
                    spreadRadius: -6,
                  ),
              ],
            ),
            child: ClipRRect(
              borderRadius: BorderRadius.circular(AppSpacing.radiusLG),
              child: Column(
                children: [
                  _buildUrnHeader(urnData),
                  SizeTransition(
                    sizeFactor: _expandAnimation,
                    axisAlignment: -1.0,
                    child: _buildTracksSection(urnData),
                  ),
                ],
              ),
            ),
          ),
        ),
      ],
    );
  }

  Widget _buildPathConnector(bool isLocked) {
    return Container(
      width: 6,
      height: 36,
      margin: const EdgeInsets.only(bottom: AppSpacing.sm),
      decoration: BoxDecoration(
        gradient: LinearGradient(
          begin: Alignment.topCenter,
          end: Alignment.bottomCenter,
          colors: [
            AppColors.primary.withOpacity(isLocked ? 0.15 : 0.4),
            AppColors.primary.withOpacity(isLocked ? 0.05 : 0.2),
          ],
        ),
        borderRadius: BorderRadius.circular(3),
      ),
    );
  }

  Widget _buildUrnHeader(_UrnData urnData) {
    final progressPercent = (urnData.progressPercent * 100).round();

    return Padding(
      padding: const EdgeInsets.all(AppSpacing.md),
      child: LayoutBuilder(
        builder: (context, constraints) {
          final isCompact = constraints.maxWidth < 360;
          final isNarrow = constraints.maxWidth < 320;
          return Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              _buildSummitBadge(urnData.status),
              AppSpacing.horizontalSpaceMD,
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      urnData.name,
                      style: TextStyle(
                        color: Colors.white,
                        fontSize: isCompact ? 16 : 18,
                        fontWeight: FontWeight.bold,
                      ),
                      maxLines: 2,
                      overflow: TextOverflow.ellipsis,
                    ),
                    if (urnData.nameEn != null &&
                        urnData.nameEn!.isNotEmpty) ...[
                      const SizedBox(height: 2),
                      Text(
                        urnData.nameEn!,
                        style: TextStyle(
                          color: Colors.white.withOpacity(0.6),
                          fontSize: isCompact ? 11 : 12,
                          fontStyle: FontStyle.italic,
                        ),
                        maxLines: 2,
                        overflow: TextOverflow.ellipsis,
                      ),
                    ],
                    AppSpacing.verticalSpaceXS,
                    if (urnData.status != _UrnStatus.locked)
                      _buildProgressBar(urnData.progressPercent),
                  ],
                ),
              ),
              const SizedBox(width: AppSpacing.sm),
              Column(
                mainAxisSize: MainAxisSize.min,
                crossAxisAlignment: CrossAxisAlignment.end,
                children: [
                  if (urnData.status == _UrnStatus.locked)
                    const Icon(Icons.lock, color: Colors.white54, size: 22)
                  else
                    _ProgressPill(
                      label: isNarrow
                          ? '$progressPercent%'
                          : '$progressPercent% hoàn thành',
                      color: _getStatusColor(urnData.status),
                    ),
                  if (urnData.status != _UrnStatus.locked) ...[
                    const SizedBox(height: 8),
                    AnimatedRotation(
                      turns: _isExpanded ? 0.5 : 0,
                      duration: const Duration(milliseconds: 280),
                      child: Icon(
                        Icons.keyboard_arrow_down,
                        color: Colors.white.withOpacity(0.7),
                      ),
                    ),
                  ],
                ],
              ),
            ],
          );
        },
      ),
    );
  }

  Widget _buildSummitBadge(_UrnStatus status) {
    final color = _getStatusColor(status);
    final icon = status == _UrnStatus.completed
        ? Icons.flag
        : status == _UrnStatus.inProgress
            ? Icons.terrain
            : Icons.lock_outline;

    return Container(
      width: 48,
      height: 48,
      decoration: BoxDecoration(
        color: color.withOpacity(0.2),
        shape: BoxShape.circle,
        border: Border.all(
          color: color.withOpacity(0.5),
          width: 2,
        ),
      ),
      child: Icon(
        icon,
        color: color,
        size: 24,
      ),
    );
  }

  Widget _buildProgressBar(double progress) {
    return Container(
      height: 6,
      decoration: BoxDecoration(
        color: Colors.white.withOpacity(0.12),
        borderRadius: BorderRadius.circular(AppSpacing.radiusXS),
      ),
      child: ClipRRect(
        borderRadius: BorderRadius.circular(AppSpacing.radiusXS),
        child: FractionallySizedBox(
          alignment: Alignment.centerLeft,
          widthFactor: progress.clamp(0.0, 1.0),
          child: Container(
            decoration: BoxDecoration(
              gradient: LinearGradient(
                colors: [AppColors.primary, AppColors.primaryLight],
              ),
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildTracksSection(_UrnData urnData) {
    return Container(
      padding: const EdgeInsets.fromLTRB(
        AppSpacing.md,
        AppSpacing.sm,
        AppSpacing.md,
        AppSpacing.md,
      ),
      decoration: BoxDecoration(
        gradient: LinearGradient(
          begin: Alignment.topCenter,
          end: Alignment.bottomCenter,
          colors: [
            Colors.white.withOpacity(0.05),
            Colors.white.withOpacity(0.02),
          ],
        ),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            'Các chủ đề trong đỉnh',
            style: TextStyle(
              color: Colors.white.withOpacity(0.7),
              fontSize: 14,
              fontWeight: FontWeight.w600,
            ),
          ),
          AppSpacing.verticalSpaceSM,
          ...urnData.tracks.asMap().entries.map((entry) {
            final index = entry.key;
            final track = entry.value;
            return Padding(
              padding: EdgeInsets.only(
                bottom: index < urnData.tracks.length - 1 ? AppSpacing.md : 0,
              ),
              child: _TrackItem(track: track),
            );
          }).toList(),
        ],
      ),
    );
  }

  List<Color> _getGradientColors(_UrnStatus status) {
    switch (status) {
      case _UrnStatus.completed:
        return [
          AppColors.success.withOpacity(0.15),
          AppColors.success.withOpacity(0.05),
        ];
      case _UrnStatus.inProgress:
        return [
          Colors.white.withOpacity(0.12),
          Colors.white.withOpacity(0.06),
        ];
      case _UrnStatus.locked:
        return [
          Colors.white.withOpacity(0.08),
          Colors.white.withOpacity(0.04),
        ];
    }
  }

  Color _getBorderColor(_UrnStatus status) {
    switch (status) {
      case _UrnStatus.completed:
        return AppColors.success.withOpacity(0.5);
      case _UrnStatus.inProgress:
        return Colors.white.withOpacity(0.2);
      case _UrnStatus.locked:
        return Colors.white.withOpacity(0.1);
    }
  }

  Color _getStatusColor(_UrnStatus status) {
    switch (status) {
      case _UrnStatus.completed:
        return AppColors.success;
      case _UrnStatus.inProgress:
        return AppColors.primary;
      case _UrnStatus.locked:
        return Colors.white54;
    }
  }

  _UrnData _getMockUrnData(int index) {
    final mockUrns = [
      _UrnData(
        name: 'Cao Đỉnh',
        nameEn: 'Cao Dinh',
        status: _UrnStatus.completed,
        progressPercent: 1.0,
        tracks: [
          _TrackData(name: 'Thảo Mộc', motifsTotal: 5, motifsCompleted: 5),
          _TrackData(name: 'Linh Thú', motifsTotal: 4, motifsCompleted: 4),
          _TrackData(name: 'Kiến Trúc', motifsTotal: 4, motifsCompleted: 4),
        ],
      ),
      _UrnData(
        name: 'Nhân Đỉnh',
        nameEn: 'Nhan Dinh',
        status: _UrnStatus.inProgress,
        progressPercent: 0.6,
        tracks: [
          _TrackData(name: 'Thảo Mộc', motifsTotal: 6, motifsCompleted: 4),
          _TrackData(name: 'Linh Thú', motifsTotal: 5, motifsCompleted: 3),
          _TrackData(name: 'Kiến Trúc', motifsTotal: 4, motifsCompleted: 2),
        ],
      ),
      _UrnData(
        name: 'Chương Đỉnh',
        nameEn: 'Chuong Dinh',
        status: _UrnStatus.locked,
        progressPercent: 0.0,
        tracks: [
          _TrackData(name: 'Thảo Mộc', motifsTotal: 5, motifsCompleted: 0),
          _TrackData(name: 'Linh Thú', motifsTotal: 4, motifsCompleted: 0),
        ],
      ),
      _UrnData(
        name: 'Anh Đỉnh',
        nameEn: 'Anh Dinh',
        status: _UrnStatus.locked,
        progressPercent: 0.0,
        tracks: [
          _TrackData(name: 'Thảo Mộc', motifsTotal: 4, motifsCompleted: 0),
          _TrackData(name: 'Linh Thú', motifsTotal: 5, motifsCompleted: 0),
        ],
      ),
      _UrnData(
        name: 'Nghị Đỉnh',
        nameEn: 'Nghi Dinh',
        status: _UrnStatus.locked,
        progressPercent: 0.0,
        tracks: [
          _TrackData(name: 'Linh Thú', motifsTotal: 5, motifsCompleted: 0),
          _TrackData(name: 'Kiến Trúc', motifsTotal: 4, motifsCompleted: 0),
        ],
      ),
      _UrnData(
        name: 'Thuần Đỉnh',
        nameEn: 'Thuan Dinh',
        status: _UrnStatus.locked,
        progressPercent: 0.0,
        tracks: [
          _TrackData(name: 'Thảo Mộc', motifsTotal: 5, motifsCompleted: 0),
          _TrackData(name: 'Thiên Văn', motifsTotal: 3, motifsCompleted: 0),
        ],
      ),
      _UrnData(
        name: 'Tuyên Đỉnh',
        nameEn: 'Tuyen Dinh',
        status: _UrnStatus.locked,
        progressPercent: 0.0,
        tracks: [
          _TrackData(name: 'Linh Thú', motifsTotal: 4, motifsCompleted: 0),
          _TrackData(name: 'Thảo Mộc', motifsTotal: 5, motifsCompleted: 0),
        ],
      ),
      _UrnData(
        name: 'Dụ Đỉnh',
        nameEn: 'Du Dinh',
        status: _UrnStatus.locked,
        progressPercent: 0.0,
        tracks: [
          _TrackData(name: 'Kiến Trúc', motifsTotal: 5, motifsCompleted: 0),
          _TrackData(name: 'Thủy Văn', motifsTotal: 4, motifsCompleted: 0),
        ],
      ),
      _UrnData(
        name: 'Huyền Đỉnh',
        nameEn: 'Huyen Dinh',
        status: _UrnStatus.locked,
        progressPercent: 0.0,
        tracks: [
          _TrackData(name: 'Thảo Mộc', motifsTotal: 6, motifsCompleted: 0),
          _TrackData(name: 'Linh Thú', motifsTotal: 4, motifsCompleted: 0),
        ],
      ),
    ];

    return mockUrns[index % mockUrns.length];
  }
}

class _ProgressPill extends StatelessWidget {
  final String label;
  final Color color;

  const _ProgressPill({required this.label, required this.color});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
      decoration: BoxDecoration(
        color: color.withOpacity(0.18),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: color.withOpacity(0.4)),
      ),
      child: Text(
        label,
        style: TextStyle(
          color: color,
          fontSize: 11,
          fontWeight: FontWeight.w600,
        ),
      ),
    );
  }
}

/// Track item widget showing a category track with motif nodes.
class _TrackItem extends StatelessWidget {
  final _TrackData track;

  const _TrackItem({required this.track});

  @override
  Widget build(BuildContext context) {
    return LayoutBuilder(
      builder: (context, constraints) {
        final isCompact = constraints.maxWidth < 360;

        return Container(
          padding: EdgeInsets.all(isCompact ? 12 : 16),
          decoration: BoxDecoration(
            color: Colors.white.withOpacity(0.05),
            borderRadius: BorderRadius.circular(AppSpacing.radiusMD),
            border: Border.all(
              color: Colors.white.withOpacity(0.1),
            ),
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Wrap(
                spacing: AppSpacing.sm,
                runSpacing: AppSpacing.xs,
                crossAxisAlignment: WrapCrossAlignment.center,
                children: [
                  _TrackBadge(label: track.name),
                  Text(
                    '${track.motifsCompleted}/${track.motifsTotal}',
                    style: TextStyle(
                      color: Colors.white.withOpacity(0.7),
                      fontSize: 12,
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 12),
              _PeakTrail(
                total: track.motifsTotal,
                completed: track.motifsCompleted,
              ),
            ],
          ),
        );
      },
    );
  }
}

class _TrackBadge extends StatelessWidget {
  final String label;

  const _TrackBadge({required this.label});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(
        horizontal: AppSpacing.sm,
        vertical: AppSpacing.xs,
      ),
      decoration: BoxDecoration(
        color: AppColors.primary.withOpacity(0.2),
        borderRadius: BorderRadius.circular(10),
      ),
      child: Text(
        label,
        style: const TextStyle(
          color: AppColors.primary,
          fontSize: 12,
          fontWeight: FontWeight.bold,
        ),
      ),
    );
  }
}

class _PeakTrail extends StatelessWidget {
  final int total;
  final int completed;

  const _PeakTrail({required this.total, required this.completed});

  @override
  Widget build(BuildContext context) {
    return LayoutBuilder(
      builder: (context, constraints) {
        final isCompact = constraints.maxWidth < 360;
        final size = isCompact ? 26.0 : 30.0;
        final spacing = isCompact ? 6.0 : 8.0;

        return Wrap(
          spacing: spacing,
          runSpacing: spacing,
          children: List.generate(total, (index) {
            final isCompleted = index < completed;
            final isCurrent = index == completed && completed < total;
            final isLocked = index > completed;

            return _PeakNode(
              size: size,
              status: isCompleted
                  ? _PeakStatus.completed
                  : isCurrent
                      ? _PeakStatus.current
                      : _PeakStatus.locked,
              index: index + 1,
            );
          }),
        );
      },
    );
  }
}

enum _PeakStatus { completed, current, locked }

class _PeakNode extends StatelessWidget {
  final double size;
  final _PeakStatus status;
  final int index;

  const _PeakNode({
    required this.size,
    required this.status,
    required this.index,
  });

  @override
  Widget build(BuildContext context) {
    final color = switch (status) {
      _PeakStatus.completed => AppColors.success,
      _PeakStatus.current => AppColors.primary,
      _PeakStatus.locked => Colors.white54,
    };

    final icon = switch (status) {
      _PeakStatus.completed => Icons.check_rounded,
      _PeakStatus.current => Icons.radio_button_checked,
      _PeakStatus.locked => Icons.lock_outline,
    };

    final fillColor = switch (status) {
      _PeakStatus.completed => color,
      _PeakStatus.current => color.withOpacity(0.15),
      _PeakStatus.locked => Colors.transparent,
    };

    final borderColor = switch (status) {
      _PeakStatus.completed => color.withOpacity(0.9),
      _PeakStatus.current => color.withOpacity(0.6),
      _PeakStatus.locked => Colors.white24,
    };

    final iconColor = switch (status) {
      _PeakStatus.completed => Colors.white,
      _PeakStatus.current => color,
      _PeakStatus.locked => Colors.white70,
    };

    return SizedBox(
      width: size,
      height: size,
      child: Stack(
        alignment: Alignment.center,
        children: [
          Container(
            width: size,
            height: size,
            decoration: BoxDecoration(
              shape: BoxShape.circle,
              color: fillColor,
              border: Border.all(
                color: borderColor,
                width: 1.6,
              ),
              boxShadow: status == _PeakStatus.locked
                  ? null
                  : [
                      BoxShadow(
                        color: color.withOpacity(0.35),
                        blurRadius: 8,
                        offset: const Offset(0, 4),
                      ),
                    ],
            ),
          ),
          Icon(
            icon,
            size: size * 0.45,
            color: iconColor,
          ),
        ],
      ),
    );
  }
}

/// Mock data model for urn.
class _UrnData {
  final String name;
  final String? nameEn;
  final _UrnStatus status;
  final double progressPercent;
  final List<_TrackData> tracks;

  _UrnData({
    required this.name,
    this.nameEn,
    required this.status,
    required this.progressPercent,
    required this.tracks,
  });
}

/// Status of an urn in the learning path.
enum _UrnStatus { completed, inProgress, locked }

/// Mock data model for track.
class _TrackData {
  final String name;
  final int motifsTotal;
  final int motifsCompleted;

  _TrackData({
    required this.name,
    required this.motifsTotal,
    required this.motifsCompleted,
  });
}
