import 'package:flutter/material.dart';
import 'mascot_widget.dart';
import 'mascot_bubble.dart';
import '../../domain/mascot_messages.dart';

/// Compact mascot display for app bar or header
class CompactMascotDisplay extends StatelessWidget {
  final VoidCallback? onTap;
  final MascotExpression expression;

  const CompactMascotDisplay({
    super.key,
    this.onTap,
    this.expression = MascotExpression.happy,
  });

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap ??
          () {
            // Show random encouragement message when tapped
            showMascotBubble(
              context: context,
              message: MascotMessages.random(MascotMessages.encouragement),
              expression: MascotExpression.encouraging,
            );
          },
      child: Container(
        padding: const EdgeInsets.all(8),
        child: MascotWidget(
          expression: expression,
          size: 32,
          animate: true,
        ),
      ),
    );
  }
}

