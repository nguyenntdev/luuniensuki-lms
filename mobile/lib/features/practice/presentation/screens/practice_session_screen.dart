import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../../../core/theme/app_colors.dart';
import '../../../../core/theme/app_spacing.dart';
import '../../../../shared/widgets/glass/animated_background.dart';
import '../../../hearts/presentation/providers/hearts_provider.dart';
import '../../../hearts/presentation/widgets/hearts_display.dart';
import '../../../hearts/presentation/widgets/heart_lost_animation.dart';
import '../../domain/models/quiz_question.dart';
import '../providers/quiz_session_provider.dart';
import '../widgets/quiz_types/multiple_choice_quiz.dart';
import '../widgets/quiz_types/image_matching_quiz.dart';
import '../widgets/quiz_types/true_false_quiz.dart';

/// Practice session screen with quiz questions
class PracticeSessionScreen extends ConsumerStatefulWidget {
  const PracticeSessionScreen({super.key});

  @override
  ConsumerState<PracticeSessionScreen> createState() => _PracticeSessionScreenState();
}

class _PracticeSessionScreenState extends ConsumerState<PracticeSessionScreen> {
  bool _showingFeedback = false;

  @override
  void initState() {
    super.initState();
    // Start a mixed quiz session if not already started
    WidgetsBinding.instance.addPostFrameCallback((_) {
      final session = ref.read(quizSessionProvider);
      if (session.questions.isEmpty) {
        ref.read(quizSessionProvider.notifier).startMixedQuiz();
      }
    });
  }

  void _handleCorrectAnswer() {
    if (_showingFeedback) return;
    setState(() => _showingFeedback = true);

    // Update session
    final session = ref.read(quizSessionProvider);
    final currentQuestion = session.currentQuestion;
    if (currentQuestion != null) {
      ref.read(quizSessionProvider.notifier).answerQuestion(currentQuestion.correctAnswer);
    }

    // Wait for animation then move to next
    Future.delayed(const Duration(milliseconds: 1500), () {
      if (mounted) {
        setState(() => _showingFeedback = false);
        ref.read(quizSessionProvider.notifier).nextQuestion();

        // Check if session is complete
        final updatedSession = ref.read(quizSessionProvider);
        if (updatedSession.isCompleted) {
          _showCompletionScreen();
        }
      }
    });
  }

  void _handleIncorrectAnswer() async {
    if (_showingFeedback) return;
    setState(() => _showingFeedback = true);

    // Lose a heart
    await ref.read(heartsNotifierProvider.notifier).loseHeart();

    // Show heart lost animation
    if (mounted) {
      showHeartLostAnimation(context);
    }

    // Update session
    final session = ref.read(quizSessionProvider);
    final currentQuestion = session.currentQuestion;
    if (currentQuestion != null) {
      ref.read(quizSessionProvider.notifier).answerQuestion('wrong_answer');
    }

    // Check if out of hearts
    final heartState = ref.read(heartsNotifierProvider);
    if (!heartState.hasHearts) {
      Future.delayed(const Duration(milliseconds: 1500), () {
        if (mounted) {
          context.go('/hearts-refill?returnPath=/practice');
        }
      });
      return;
    }

    // Wait for animation then move to next
    Future.delayed(const Duration(milliseconds: 1500), () {
      if (mounted) {
        setState(() => _showingFeedback = false);
        ref.read(quizSessionProvider.notifier).nextQuestion();

        // Check if session is complete
        final updatedSession = ref.read(quizSessionProvider);
        if (updatedSession.isCompleted) {
          _showCompletionScreen();
        }
      }
    });
  }

  void _showCompletionScreen() {
    showDialog(
      context: context,
      barrierDismissible: false,
      builder: (context) => _buildCompletionDialog(),
    );
  }

  @override
  Widget build(BuildContext context) {
    final session = ref.watch(quizSessionProvider);
    final currentQuestion = session.currentQuestion;

    if (session.questions.isEmpty) {
      return const Scaffold(
        body: Center(child: CircularProgressIndicator()),
      );
    }

    if (currentQuestion == null) {
      return const Scaffold(
        body: Center(child: Text('Đang tải...')),
      );
    }

    final progress = (session.currentQuestionIndex + 1) / session.questions.length;

    return AnimatedGradientBackground(
      child: Scaffold(
        backgroundColor: Colors.transparent,
        appBar: AppBar(
          backgroundColor: Colors.transparent,
          elevation: 0,
          leading: IconButton(
            icon: const Icon(Icons.close, color: Colors.white),
            onPressed: () => _showExitDialog(),
          ),
          title: Column(
            children: [
              Text(
                'Câu ${session.currentQuestionIndex + 1}/${session.questions.length}',
                style: const TextStyle(
                  color: Colors.white,
                  fontSize: 16,
                  fontWeight: FontWeight.bold,
                ),
              ),
              const SizedBox(height: 4),
              ClipRRect(
                borderRadius: BorderRadius.circular(4),
                child: LinearProgressIndicator(
                  value: progress,
                  backgroundColor: Colors.white.withOpacity(0.2),
                  valueColor: const AlwaysStoppedAnimation(AppColors.primary),
                  minHeight: 4,
                ),
              ),
            ],
          ),
          centerTitle: true,
          actions: [
            Padding(
              padding: const EdgeInsets.only(right: 8),
              child: CompactHeartsDisplay(),
            ),
          ],
        ),
        body: SafeArea(
          child: Padding(
            padding: const EdgeInsets.all(AppSpacing.lg),
            child: Column(
              children: [
                // XP Display
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                  decoration: BoxDecoration(
                    color: AppColors.xpGold.withOpacity(0.2),
                    borderRadius: BorderRadius.circular(20),
                    border: Border.all(
                      color: AppColors.xpGold.withOpacity(0.5),
                      width: 1,
                    ),
                  ),
                  child: Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      const Icon(Icons.star, color: AppColors.xpGold, size: 20),
                      const SizedBox(width: 8),
                      Text(
                        '${session.totalScore} XP',
                        style: const TextStyle(
                          color: AppColors.xpGold,
                          fontSize: 16,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                    ],
                  ),
                ),
                const SizedBox(height: AppSpacing.lg),

                // Quiz Widget
                Expanded(
                  child: _buildQuizWidget(currentQuestion),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildQuizWidget(QuizQuestion question) {
    switch (question.type) {
      case QuizType.multipleChoice:
        return MultipleChoiceQuiz(
          question: question,
          onCorrect: _handleCorrectAnswer,
          onIncorrect: _handleIncorrectAnswer,
        );
      case QuizType.imageMatching:
        return ImageMatchingQuiz(
          question: question,
          onCorrect: _handleCorrectAnswer,
          onIncorrect: _handleIncorrectAnswer,
        );
      case QuizType.trueFalse:
        return TrueFalseQuiz(
          question: question,
          onCorrect: _handleCorrectAnswer,
          onIncorrect: _handleIncorrectAnswer,
        );
      default:
        return Center(
          child: Text(
            'Quiz type not supported: ${question.type}',
            style: const TextStyle(color: Colors.white),
          ),
        );
    }
  }

  Widget _buildCompletionDialog() {
    final session = ref.read(quizSessionProvider);
    final accuracy = session.accuracy;
    final stars = accuracy >= 0.9 ? 3 : accuracy >= 0.7 ? 2 : 1;

    return Dialog(
      backgroundColor: Colors.transparent,
      child: Container(
        padding: const EdgeInsets.all(AppSpacing.xl),
        decoration: BoxDecoration(
          gradient: LinearGradient(
            begin: Alignment.topLeft,
            end: Alignment.bottomRight,
            colors: [
              AppColors.surface,
              AppColors.surfaceElevated,
            ],
          ),
          borderRadius: BorderRadius.circular(24),
          border: Border.all(
            color: AppColors.primary.withOpacity(0.3),
            width: 2,
          ),
        ),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            // Stars
            Row(
              mainAxisAlignment: MainAxisAlignment.center,
              children: List.generate(3, (index) {
                return Icon(
                  index < stars ? Icons.star : Icons.star_border,
                  color: AppColors.xpGold,
                  size: 48,
                );
              }),
            ),
            const SizedBox(height: AppSpacing.lg),

            // Title
            const Text(
              'Hoàn Thành!',
              style: TextStyle(
                color: Colors.white,
                fontSize: 28,
                fontWeight: FontWeight.bold,
              ),
            ),
            const SizedBox(height: AppSpacing.md),

            // Stats
            _buildStatRow('Tổng điểm', '${session.totalScore} XP', AppColors.xpGold),
            _buildStatRow('Chính xác', '${(accuracy * 100).toInt()}%', AppColors.success),
            _buildStatRow('Đúng/Sai', '${session.correctAnswers}/${session.incorrectAnswers}', AppColors.info),

            const SizedBox(height: AppSpacing.xl),

            // Buttons
            Row(
              children: [
                Expanded(
                  child: OutlinedButton(
                    onPressed: () {
                      Navigator.of(context).pop();
                      context.go('/practice');
                    },
                    style: OutlinedButton.styleFrom(
                      foregroundColor: Colors.white,
                      side: const BorderSide(color: Colors.white),
                      padding: const EdgeInsets.symmetric(vertical: 16),
                    ),
                    child: const Text('Về Trang Chủ'),
                  ),
                ),
                const SizedBox(width: AppSpacing.md),
                Expanded(
                  child: ElevatedButton(
                    onPressed: () {
                      Navigator.of(context).pop();
                      ref.read(quizSessionProvider.notifier).startMixedQuiz();
                    },
                    style: ElevatedButton.styleFrom(
                      backgroundColor: AppColors.primary,
                      foregroundColor: AppColors.onPrimary,
                      padding: const EdgeInsets.symmetric(vertical: 16),
                    ),
                    child: const Text('Tiếp Tục'),
                  ),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildStatRow(String label, String value, Color color) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 8),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(
            label,
            style: const TextStyle(
              color: AppColors.textSecondary,
              fontSize: 16,
            ),
          ),
          Text(
            value,
            style: TextStyle(
              color: color,
              fontSize: 18,
              fontWeight: FontWeight.bold,
            ),
          ),
        ],
      ),
    );
  }

  void _showExitDialog() {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        backgroundColor: AppColors.surface,
        title: const Text(
          'Thoát Luyện Tập?',
          style: TextStyle(color: Colors.white),
        ),
        content: const Text(
          'Tiến độ của bạn sẽ không được lưu.',
          style: TextStyle(color: AppColors.textSecondary),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(context).pop(),
            child: const Text('Hủy'),
          ),
          TextButton(
            onPressed: () {
              Navigator.of(context).pop();
              context.go('/practice');
            },
            child: const Text(
              'Thoát',
              style: TextStyle(color: AppColors.error),
            ),
          ),
        ],
      ),
    );
  }
}

