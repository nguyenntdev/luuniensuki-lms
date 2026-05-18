import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../mascot.dart';

/// Example integrations for the mascot feature
/// Copy these patterns to integrate mascot in your screens

// =============================================================================
// EXAMPLE 1: Show mascot on button press
// =============================================================================
class MascotButtonExample extends StatelessWidget {
  const MascotButtonExample({super.key});

  @override
  Widget build(BuildContext context) {
    return ElevatedButton(
      onPressed: () {
        showMascotBubble(
          context: context,
          message: MascotMessages.random(MascotMessages.encouragement),
          expression: MascotExpression.happy,
        );
      },
      child: const Text('Show Mascot Message'),
    );
  }
}

// =============================================================================
// EXAMPLE 2: Context-aware mascot for achievement
// =============================================================================
class AchievementMascotExample extends StatelessWidget {
  final bool isPerfect;

  const AchievementMascotExample({super.key, this.isPerfect = false});

  void _showAchievement(BuildContext context) {
    final message = isPerfect
        ? MascotMessages.random(MascotMessages.perfectScore)
        : MascotMessages.random(MascotMessages.celebration);

    showMascotBubble(
      context: context,
      message: message,
      expression: isPerfect
          ? MascotExpression.celebrating
          : MascotExpression.happy,
      duration: const Duration(seconds: 4),
    );
  }

  @override
  Widget build(BuildContext context) {
    return ElevatedButton(
      onPressed: () => _showAchievement(context),
      child: const Text('Complete Achievement'),
    );
  }
}

// =============================================================================
// EXAMPLE 3: Mascot in app bar
// =============================================================================
class MascotAppBarExample extends StatelessWidget {
  const MascotAppBarExample({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('My Screen'),
        actions: const [
          CompactMascotDisplay(),
          SizedBox(width: 8),
        ],
      ),
      body: const Center(
        child: Text('Screen content'),
      ),
    );
  }
}

// =============================================================================
// EXAMPLE 4: Empty state with mascot
// =============================================================================
class EmptyStateMascotExample extends StatelessWidget {
  const EmptyStateMascotExample({super.key});

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          const MascotWidget(
            expression: MascotExpression.neutral,
            size: 100,
            animate: true,
          ),
          const SizedBox(height: 24),
          Text(
            MascotMessages.random(MascotMessages.emptyState),
            style: const TextStyle(fontSize: 18),
            textAlign: TextAlign.center,
          ),
          const SizedBox(height: 16),
          ElevatedButton(
            onPressed: () {
              // Navigate to content
            },
            child: const Text('Bắt đầu ngay'),
          ),
        ],
      ),
    );
  }
}

// =============================================================================
// EXAMPLE 5: Streak warning
// =============================================================================
class StreakWarningMascotExample extends ConsumerWidget {
  const StreakWarningMascotExample({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    // Check if user hasn't studied today
    final shouldShowWarning = true; // Replace with actual logic

    if (shouldShowWarning) {
      WidgetsBinding.instance.addPostFrameCallback((_) {
        showMascotBubble(
          context: context,
          message: MascotMessages.random(MascotMessages.streakWarning),
          expression: MascotExpression.worried,
          duration: const Duration(seconds: 5),
        );
      });
    }

    return const Placeholder();
  }
}

// =============================================================================
// EXAMPLE 6: First-time user experience
// =============================================================================
class FirstTimeUserMascotExample extends StatefulWidget {
  const FirstTimeUserMascotExample({super.key});

  @override
  State<FirstTimeUserMascotExample> createState() =>
      _FirstTimeUserMascotExampleState();
}

class _FirstTimeUserMascotExampleState
    extends State<FirstTimeUserMascotExample> {
  @override
  void initState() {
    super.initState();

    // Show welcome message for first-time users
    WidgetsBinding.instance.addPostFrameCallback((_) {
      Future.delayed(const Duration(milliseconds: 500), () {
        if (mounted) {
          showMascotBubble(
            context: context,
            message: MascotMessages.random(MascotMessages.welcome),
            expression: MascotExpression.excited,
            duration: const Duration(seconds: 4),
          );
        }
      });
    });
  }

  @override
  Widget build(BuildContext context) {
    return const Placeholder();
  }
}

// =============================================================================
// EXAMPLE 7: Failed quiz with motivation
// =============================================================================
void showFailedQuizMascot(BuildContext context, {int? score}) {
  Future.delayed(const Duration(milliseconds: 500), () {
    if (context.mounted) {
      showMascotBubble(
        context: context,
        message: MascotMessages.random(MascotMessages.motivation),
        expression: MascotExpression.encouraging,
        duration: const Duration(seconds: 4),
      );
    }
  });
}

// =============================================================================
// EXAMPLE 8: Daily goal completed
// =============================================================================
void showDailyGoalComplete(BuildContext context) {
  showMascotBubble(
    context: context,
    message: "Mục tiêu hôm nay hoàn thành! Xuất sắc! 🎯",
    expression: MascotExpression.celebrating,
    duration: const Duration(seconds: 4),
  );
}

// =============================================================================
// EXAMPLE 9: Lesson started (first lesson)
// =============================================================================
void showFirstLessonStart(BuildContext context) {
  showMascotBubble(
    context: context,
    message: MascotMessages.random(MascotMessages.firstLesson),
    expression: MascotExpression.excited,
    duration: const Duration(seconds: 3),
  );
}

// =============================================================================
// EXAMPLE 10: Custom message
// =============================================================================
void showCustomMascotMessage(
  BuildContext context, {
  required String message,
  MascotExpression expression = MascotExpression.happy,
}) {
  showMascotBubble(
    context: context,
    message: message,
    expression: expression,
  );
}

