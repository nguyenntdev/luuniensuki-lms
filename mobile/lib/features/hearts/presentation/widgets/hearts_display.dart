import 'dart:async';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../../core/theme/app_colors.dart';
import '../providers/hearts_provider.dart';

/// Widget that displays hearts and countdown timer
class HeartsDisplay extends ConsumerStatefulWidget {
  final bool showTimer;
  final VoidCallback? onTap;

  const HeartsDisplay({
    super.key,
    this.showTimer = true,
    this.onTap,
  });

  @override
  ConsumerState<HeartsDisplay> createState() => _HeartsDisplayState();
}

class _HeartsDisplayState extends ConsumerState<HeartsDisplay> {
  Timer? _timer;
  
  @override
  void initState() {
    super.initState();
    // Update timer display every second
    _timer = Timer.periodic(const Duration(seconds: 1), (_) {
      if (mounted) {
        setState(() {});
      }
    });
  }
  
  @override
  void dispose() {
    _timer?.cancel();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final heartState = ref.watch(heartsNotifierProvider);

    return GestureDetector(
      onTap: widget.onTap,
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
        decoration: BoxDecoration(
          color: AppColors.surface,
          borderRadius: BorderRadius.circular(20),
          border: Border.all(
            color: heartState.hasHearts
                ? AppColors.error.withOpacity(0.3)
                : AppColors.border,
            width: 1.5,
          ),
        ),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            // Heart icons
            ..._buildHeartIcons(heartState),
            
            // Countdown timer (only show if not full and showTimer is true)
            if (widget.showTimer && !heartState.isFull && !heartState.isUnlimited) ...[
              const SizedBox(width: 8),
              Icon(
                Icons.access_time,
                size: 14,
                color: AppColors.textSecondary,
              ),
              const SizedBox(width: 4),
              Text(
                heartState.getTimeUntilNextRefillFormatted(),
                style: TextStyle(
                  color: AppColors.textSecondary,
                  fontSize: 12,
                  fontWeight: FontWeight.w600,
                ),
              ),
            ],
          ],
        ),
      ),
    );
  }

  List<Widget> _buildHeartIcons(heartState) {
    final List<Widget> hearts = [];
    final maxHearts = heartState.maxHearts;
    final currentHearts = heartState.currentHearts;
    final isUnlimited = heartState.isUnlimited;

    // If unlimited, show infinity symbol
    if (isUnlimited) {
      hearts.add(
        Icon(
          Icons.all_inclusive,
          size: 20,
          color: AppColors.error,
        ),
      );
      return hearts;
    }

    // Show heart icons
    for (int i = 0; i < maxHearts; i++) {
      final isFilled = i < currentHearts;
      
      hearts.add(
        Padding(
          padding: EdgeInsets.only(left: i > 0 ? 2 : 0),
          child: Icon(
            isFilled ? Icons.favorite : Icons.favorite_border,
            size: 18,
            color: isFilled ? AppColors.error : AppColors.textSecondary.withOpacity(0.3),
          ),
        ),
      );
    }

    return hearts;
  }
}

/// Compact hearts display for headers
class CompactHeartsDisplay extends ConsumerWidget {
  final VoidCallback? onTap;

  const CompactHeartsDisplay({
    super.key,
    this.onTap,
  });

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final heartState = ref.watch(heartsNotifierProvider);

    return GestureDetector(
      onTap: onTap,
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
        decoration: BoxDecoration(
          color: AppColors.surface,
          borderRadius: BorderRadius.circular(16),
          border: Border.all(
            color: AppColors.error.withOpacity(0.3),
            width: 1.5,
          ),
        ),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(
              heartState.isUnlimited ? Icons.all_inclusive : Icons.favorite,
              size: 16,
              color: AppColors.error,
            ),
            const SizedBox(width: 4),
            Text(
              heartState.isUnlimited ? '∞' : '${heartState.currentHearts}',
              style: TextStyle(
                color: AppColors.textPrimary,
                fontSize: 14,
                fontWeight: FontWeight.bold,
              ),
            ),
          ],
        ),
      ),
    );
  }
}

