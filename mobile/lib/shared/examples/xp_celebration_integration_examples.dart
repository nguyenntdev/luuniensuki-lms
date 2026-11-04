// Integration Example: Quiz Result Screen with XP Celebration
// This shows how to integrate the XP celebration system into quiz_result_screen.dart

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../services/xp_celebration_service.dart';
import '../../features/auth/presentation/providers/auth_provider.dart';

class BadgeItem {
  final String slug;
  const BadgeItem(this.slug);
}

class QuizResultDto {
  final bool passed;
  final int xpEarned;
  final int totalXp;
  final int percentage;
  final List<BadgeItem> newBadges;
  const QuizResultDto({
    this.passed = true,
    this.xpEarned = 50,
    this.totalXp = 200,
    this.percentage = 90,
    this.newBadges = const [],
  });
}

class ActionResult {
  final int xpEarned;
  final int totalXp;
  final List<String> badges;
  final List<String> badgesEarned;
  const ActionResult({
    this.xpEarned = 25,
    this.totalXp = 225,
    this.badges = const [],
    this.badgesEarned = const [],
  });
}

class _QuizSubmissionNotifier {
  Future<QuizResultDto?> submitQuiz({
    required String motifId,
    required Map<String, String> answers,
    required int timeTakenSeconds,
  }) async => const QuizResultDto();
}

final quizSubmissionNotifierProvider =
    Provider<_QuizSubmissionNotifier>((ref) => _QuizSubmissionNotifier());

class _DiscoveryNotifier {
  Future<ActionResult?> completeLesson(String motifId) async =>
      const ActionResult();
}

final discoveryNotifierProvider =
    Provider<_DiscoveryNotifier>((ref) => _DiscoveryNotifier());

/// Example of integrating XP celebration into quiz result screen
class QuizResultScreenWithCelebration extends ConsumerStatefulWidget {
  final QuizResultDto result;
  final int oldUserXp; // IMPORTANT: Pass this from before quiz submission
  
  const QuizResultScreenWithCelebration({
    super.key,
    required this.result,
    required this.oldUserXp,
  });

  @override
  ConsumerState<QuizResultScreenWithCelebration> createState() => 
      _QuizResultScreenWithCelebrationState();
}

class _QuizResultScreenWithCelebrationState 
    extends ConsumerState<QuizResultScreenWithCelebration> {
  
  @override
  void initState() {
    super.initState();
    
    // Show XP celebration if quiz passed and XP was earned
    if (widget.result.passed && widget.result.xpEarned > 0) {
      WidgetsBinding.instance.addPostFrameCallback((_) {
        if (mounted) {
          context.showXpCelebration(
            xpGained: widget.result.xpEarned,
            oldTotalXp: widget.oldUserXp,
            newTotalXp: widget.result.totalXp,
            badges: widget.result.newBadges.map((b) => b.slug).toList(),
            onComplete: () {
              // Optional: Do something after celebration
              debugPrint('XP celebration completed!');
            },
          );
        }
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    // Your existing quiz result UI
    return Scaffold(
      appBar: AppBar(title: const Text('Quiz Results')),
      body: Center(
        child: Text('Score: ${widget.result.percentage}%'),
      ),
    );
  }
}

// ============================================================================
// IMPORTANT: How to track old XP before quiz submission
// ============================================================================

/// In your quiz screen, before submitting:
class QuizScreenExample extends ConsumerStatefulWidget {
  const QuizScreenExample({super.key});

  @override
  ConsumerState<QuizScreenExample> createState() => _QuizScreenExampleState();
}

class _QuizScreenExampleState extends ConsumerState<QuizScreenExample> {
  
  Future<void> _submitQuiz(Map<String, String> answers) async {
    // 1. Get current user XP BEFORE submission
    final user = ref.read(currentUserProvider);
    final oldXp = user?.totalXp ?? 0;
    
    // 2. Submit quiz
    final result = await ref
        .read(quizSubmissionNotifierProvider)
        .submitQuiz(
          motifId: 'motif-id',
          answers: answers,
          timeTakenSeconds: 120,
        );
    
    if (result != null && mounted) {
      // 3. Navigate to result screen with oldXp
      Navigator.push(
        context,
        MaterialPageRoute(
          builder: (context) => QuizResultScreenWithCelebration(
            result: result,
            oldUserXp: oldXp, // Pass the old XP here
          ),
        ),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Quiz')),
      body: Center(
        child: ElevatedButton(
          onPressed: () => _submitQuiz({}),
          child: const Text('Submit Quiz'),
        ),
      ),
    );
  }
}

// ============================================================================
// Alternative: Using celebrateXpGain helper
// ============================================================================

class AlternativeExample extends ConsumerWidget {
  const AlternativeExample({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return ElevatedButton(
      onPressed: () async {
        final user = ref.read(currentUserProvider);
        final oldXp = user?.totalXp ?? 0;
        
        // Simulate some action that earns XP
        final result = await _performAction();
        
        if (result != null && context.mounted) {
          // Use the helper extension
          context.celebrateXpGain(
            xpGained: result.xpEarned,
            oldTotalXp: oldXp,
            newTotalXp: result.totalXp,
            badges: result.badges,
          );
        }
      },
      child: const Text('Perform Action'),
    );
  }
  
  Future<ActionResult?> _performAction() async {
    // Your action logic
    return null;
  }
}

// ============================================================================
// Lesson Completion Integration Example
// ============================================================================

class LessonCompletionExample extends ConsumerWidget {
  final String motifId;
  
  const LessonCompletionExample({super.key, required this.motifId});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return ElevatedButton(
      onPressed: () async {
        // Get old XP
        final user = ref.read(currentUserProvider);
        final oldXp = user?.totalXp ?? 0;
        
        // Complete lesson
        final result = await ref
            .read(discoveryNotifierProvider)
            .completeLesson(motifId);
        
        if (result != null && context.mounted) {
          // Show celebration
          context.celebrateXpGain(
            xpGained: result.xpEarned,
            oldTotalXp: oldXp,
            newTotalXp: result.totalXp,
            badges: result.badgesEarned,
          );
        }
      },
      child: const Text('Complete Lesson'),
    );
  }
}
