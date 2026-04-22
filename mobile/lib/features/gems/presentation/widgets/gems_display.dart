import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../../core/theme/app_colors.dart';
import '../../../../core/theme/app_spacing.dart';
import '../providers/gems_provider.dart';

/// Gems display widget with animation
class GemsDisplay extends ConsumerStatefulWidget {
  final bool showLabel;
  final double iconSize;
  final TextStyle? textStyle;
  final VoidCallback? onTap;

  const GemsDisplay({
    super.key,
    this.showLabel = true,
    this.iconSize = 24,
    this.textStyle,
    this.onTap,
  });

  @override
  ConsumerState<GemsDisplay> createState() => _GemsDisplayState();
}

class _GemsDisplayState extends ConsumerState<GemsDisplay>
    with SingleTickerProviderStateMixin {
  late AnimationController _controller;
  late Animation<double> _scaleAnimation;
  int _previousBalance = 0;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      duration: const Duration(milliseconds: 300),
      vsync: this,
    );
    _scaleAnimation = Tween<double>(begin: 1.0, end: 1.3).animate(
      CurvedAnimation(
        parent: _controller,
        curve: Curves.elasticOut,
      ),
    );
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  void _animateIfChanged(int newBalance) {
    if (_previousBalance != 0 && newBalance != _previousBalance) {
      _controller.forward().then((_) => _controller.reverse());
    }
    _previousBalance = newBalance;
  }

  @override
  Widget build(BuildContext context) {
    final gemsState = ref.watch(gemsNotifierProvider);
    final balance = gemsState.balance;

    _animateIfChanged(balance);

    final content = Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        // Animated gem icon
        AnimatedBuilder(
          animation: _scaleAnimation,
          builder: (context, child) {
            return Transform.scale(
              scale: _scaleAnimation.value,
              child: child,
            );
          },
          child: Text(
            '💎',
            style: TextStyle(fontSize: widget.iconSize),
          ),
        ),
        const SizedBox(width: AppSpacing.xs),
        // Balance text
        Text(
          '$balance',
          style: widget.textStyle ??
              TextStyle(
                color: AppColors.gemYellow,
                fontSize: 16,
                fontWeight: FontWeight.bold,
              ),
        ),
        if (widget.showLabel) ...[
          const SizedBox(width: AppSpacing.xs),
          Text(
            'Gems',
            style: widget.textStyle?.copyWith(
                  fontWeight: FontWeight.normal,
                  color: Colors.white.withOpacity(0.7),
                ) ??
                TextStyle(
                  color: Colors.white.withOpacity(0.7),
                  fontSize: 14,
                ),
          ),
        ],
      ],
    );

    if (widget.onTap != null) {
      return InkWell(
        onTap: widget.onTap,
        borderRadius: BorderRadius.circular(AppSpacing.radiusMD),
        child: Padding(
          padding: const EdgeInsets.symmetric(
            horizontal: AppSpacing.sm,
            vertical: AppSpacing.xs,
          ),
          child: content,
        ),
      );
    }

    return content;
  }
}

/// Compact gems display for app bar
class CompactGemsDisplay extends ConsumerWidget {
  final VoidCallback? onTap;

  const CompactGemsDisplay({
    super.key,
    this.onTap,
  });

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final gemsState = ref.watch(gemsNotifierProvider);
    final balance = gemsState.balance;

    return Material(
      color: Colors.transparent,
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(20),
        child: Container(
          padding: const EdgeInsets.symmetric(
            horizontal: 12,
            vertical: 6,
          ),
          decoration: BoxDecoration(
            color: AppColors.gemYellow.withOpacity(0.1),
            borderRadius: BorderRadius.circular(20),
            border: Border.all(
              color: AppColors.gemYellow.withOpacity(0.3),
              width: 1,
            ),
          ),
          child: Row(
            mainAxisSize: MainAxisSize.min,
            children: [
              const Text('💎', style: TextStyle(fontSize: 16)),
              const SizedBox(width: 4),
              Text(
                '$balance',
                style: TextStyle(
                  color: AppColors.gemYellow,
                  fontSize: 14,
                  fontWeight: FontWeight.bold,
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

