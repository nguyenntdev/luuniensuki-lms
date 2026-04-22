import 'package:flutter/material.dart';
import 'dart:async';

import '../../../../core/theme/app_colors.dart';
import 'mascot_widget.dart';

/// Speech bubble widget for mascot messages
/// Auto-dismisses after a duration or can be tapped to dismiss
class MascotBubble extends StatefulWidget {
  final String message;
  final MascotExpression expression;
  final Duration duration;
  final VoidCallback? onDismiss;
  final bool showMascot;

  const MascotBubble({
    super.key,
    required this.message,
    this.expression = MascotExpression.happy,
    this.duration = const Duration(seconds: 3),
    this.onDismiss,
    this.showMascot = true,
  });

  @override
  State<MascotBubble> createState() => _MascotBubbleState();
}

class _MascotBubbleState extends State<MascotBubble>
    with SingleTickerProviderStateMixin {
  late AnimationController _controller;
  late Animation<double> _scaleAnimation;
  late Animation<double> _opacityAnimation;
  Timer? _autoDismissTimer;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      duration: const Duration(milliseconds: 300),
      vsync: this,
    );

    _scaleAnimation = CurvedAnimation(
      parent: _controller,
      curve: Curves.easeOutBack,
    );

    _opacityAnimation = CurvedAnimation(
      parent: _controller,
      curve: Curves.easeIn,
    );

    _controller.forward();

    // Auto-dismiss after duration
    _autoDismissTimer = Timer(widget.duration, _dismiss);
  }

  @override
  void dispose() {
    _autoDismissTimer?.cancel();
    _controller.dispose();
    super.dispose();
  }

  void _dismiss() {
    _controller.reverse().then((_) {
      widget.onDismiss?.call();
    });
  }

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: _dismiss,
      child: AnimatedBuilder(
        animation: _controller,
        builder: (context, child) {
          return Transform.scale(
            scale: _scaleAnimation.value,
            child: Opacity(
              opacity: _opacityAnimation.value,
              child: child,
            ),
          );
        },
        child: Container(
          margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
          child: Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Mascot avatar
              if (widget.showMascot) ...[
                MascotWidget(
                  expression: widget.expression,
                  size: 50,
                  animate: true,
                ),
                const SizedBox(width: 12),
              ],

              // Speech bubble
              Expanded(
                child: Container(
                  padding: const EdgeInsets.all(16),
                  decoration: BoxDecoration(
                    color: Colors.white,
                    borderRadius: BorderRadius.circular(20),
                    boxShadow: [
                      BoxShadow(
                        color: Colors.black.withOpacity(0.1),
                        blurRadius: 10,
                        offset: const Offset(0, 4),
                      ),
                    ],
                  ),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Text(
                        widget.message,
                        style: const TextStyle(
                          fontSize: 15,
                          fontWeight: FontWeight.w500,
                          color: AppColors.textPrimary,
                          height: 1.4,
                        ),
                      ),
                      const SizedBox(height: 8),
                      Text(
                        'Nhấn để đóng',
                        style: TextStyle(
                          fontSize: 12,
                          color: Colors.grey[600],
                          fontStyle: FontStyle.italic,
                        ),
                      ),
                    ],
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

/// Show mascot bubble as an overlay
void showMascotBubble({
  required BuildContext context,
  required String message,
  MascotExpression expression = MascotExpression.happy,
  Duration duration = const Duration(seconds: 3),
  bool showMascot = true,
}) {
  final overlay = Overlay.of(context);
  late OverlayEntry overlayEntry;

  overlayEntry = OverlayEntry(
    builder: (context) => Positioned(
      top: MediaQuery.of(context).padding.top + 60,
      left: 0,
      right: 0,
      child: Material(
        color: Colors.transparent,
        child: MascotBubble(
          message: message,
          expression: expression,
          duration: duration,
          showMascot: showMascot,
          onDismiss: () {
            overlayEntry.remove();
          },
        ),
      ),
    ),
  );

  overlay.insert(overlayEntry);
}

