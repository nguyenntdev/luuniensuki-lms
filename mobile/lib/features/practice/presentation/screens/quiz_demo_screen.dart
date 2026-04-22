import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:lms/core/theme/app_colors.dart';
import 'package:lms/features/practice/domain/models/quiz_question.dart';
import 'package:lms/features/practice/presentation/widgets/quiz_types/multiple_choice_quiz.dart';
import 'package:lms/features/practice/presentation/widgets/quiz_types/image_matching_quiz.dart';
import 'package:lms/features/practice/presentation/widgets/quiz_types/true_false_quiz.dart';
import 'package:lms/features/practice/presentation/providers/quiz_session_provider.dart';

class QuizDemoScreen extends ConsumerStatefulWidget {
  const QuizDemoScreen({super.key});

  @override
  ConsumerState<QuizDemoScreen> createState() => _QuizDemoScreenState();
}

class _QuizDemoScreenState extends ConsumerState<QuizDemoScreen> {
  @override
  void initState() {
    super.initState();
    // Start a mixed quiz with all question types
    WidgetsBinding.instance.addPostFrameCallback((_) {
      ref.read(quizSessionProvider.notifier).startMixedQuiz();
    });
  }

  void _onCorrect() {
    final currentQuestion = ref.read(quizSessionProvider).currentQuestion;
    if (currentQuestion != null) {
      ref.read(quizSessionProvider.notifier).answerQuestion(
        currentQuestion.correctAnswer,
      );
    }

    Future.delayed(const Duration(milliseconds: 1500), () {
      if (mounted) {
        _nextQuestion();
      }
    });
  }

  void _onIncorrect() {
    Future.delayed(const Duration(milliseconds: 1500), () {
      if (mounted) {
        _nextQuestion();
      }
    });
  }

  void _nextQuestion() {
    ref.read(quizSessionProvider.notifier).nextQuestion();

    if (ref.read(quizSessionProvider).isCompleted) {
      _showCompletionDialog();
    }
  }

  void _showCompletionDialog() {
    final stats = ref.read(quizStatsProvider);
    final totalScore = stats['score'] as int;
    final correct = stats['correct'] as int;
    final total = stats['total'] as int;
    final accuracy = stats['accuracy'] as double;

    showDialog(
      context: context,
      barrierDismissible: false,
      builder: (context) => Dialog(
        backgroundColor: Colors.transparent,
        child: Container(
          padding: const EdgeInsets.all(24),
          decoration: BoxDecoration(
            gradient: LinearGradient(
              begin: Alignment.topLeft,
              end: Alignment.bottomRight,
              colors: [
                AppColors.darkSurface,
                AppColors.darkBackground,
              ],
            ),
            borderRadius: BorderRadius.circular(24),
            border: Border.all(
              color: AppColors.gold,
              width: 2,
            ),
          ),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Container(
                height: 80,
                width: 80,
                decoration: BoxDecoration(
                  shape: BoxShape.circle,
                  gradient: LinearGradient(
                    begin: Alignment.topLeft,
                    end: Alignment.bottomRight,
                    colors: [
                      AppColors.gold,
                      AppColors.gold.withOpacity(0.5),
                    ],
                  ),
                ),
                child: const Icon(
                  Icons.emoji_events,
                  size: 48,
                  color: Colors.white,
                ),
              ),
              const SizedBox(height: 24),
              const Text(
                'Hoàn thành!',
                style: TextStyle(
                  fontSize: 28,
                  fontWeight: FontWeight.bold,
                  color: AppColors.gold,
                ),
              ),
              const SizedBox(height: 16),
              Text(
                'Tổng điểm: $totalScore XP',
                style: const TextStyle(
                  fontSize: 20,
                  color: AppColors.textPrimary,
                ),
              ),
              const SizedBox(height: 8),
              Text(
                'Đúng: $correct/$total (${(accuracy * 100).toStringAsFixed(0)}%)',
                style: const TextStyle(
                  fontSize: 16,
                  color: AppColors.textSecondary,
                ),
              ),
              const SizedBox(height: 24),
              SizedBox(
                width: double.infinity,
                child: ElevatedButton(
                  onPressed: () {
                    Navigator.pop(context);
                    ref.read(quizSessionProvider.notifier).restart();
                  },
                  style: ElevatedButton.styleFrom(
                    backgroundColor: AppColors.gold,
                    foregroundColor: AppColors.darkBackground,
                    padding: const EdgeInsets.symmetric(vertical: 16),
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(12),
                    ),
                  ),
                  child: const Text(
                    'Làm lại',
                    style: TextStyle(
                      fontSize: 16,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final session = ref.watch(quizSessionProvider);
    final currentQuestion = session.currentQuestion;

    if (currentQuestion == null) {
      return Scaffold(
        backgroundColor: AppColors.darkBackground,
        body: const Center(
          child: CircularProgressIndicator(color: AppColors.gold),
        ),
      );
    }

    return Scaffold(
      backgroundColor: AppColors.darkBackground,
      appBar: AppBar(
        backgroundColor: AppColors.darkSurface,
        elevation: 0,
        title: const Text(
          'Quiz Demo',
          style: TextStyle(
            color: AppColors.gold,
            fontWeight: FontWeight.bold,
          ),
        ),
        centerTitle: true,
        leading: IconButton(
          icon: const Icon(Icons.arrow_back, color: AppColors.gold),
          onPressed: () => Navigator.pop(context),
        ),
      ),
      body: SafeArea(
        child: Column(
          children: [
            // Progress Bar
            Container(
              padding: const EdgeInsets.all(16),
              child: Column(
                children: [
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Text(
                        'Câu ${session.currentQuestionIndex + 1}/${session.questions.length}',
                        style: const TextStyle(
                          fontSize: 16,
                          color: AppColors.textSecondary,
                        ),
                      ),
                      Row(
                        children: [
                          const Icon(
                            Icons.stars,
                            color: AppColors.gold,
                            size: 20,
                          ),
                          const SizedBox(width: 8),
                          Text(
                            '${session.totalScore} XP',
                            style: const TextStyle(
                              fontSize: 16,
                              fontWeight: FontWeight.bold,
                              color: AppColors.gold,
                            ),
                          ),
                        ],
                      ),
                    ],
                  ),
                  const SizedBox(height: 12),
                  LinearProgressIndicator(
                    value: (session.currentQuestionIndex + 1) / session.questions.length,
                    backgroundColor: AppColors.darkSurface,
                    valueColor: const AlwaysStoppedAnimation<Color>(AppColors.gold),
                    minHeight: 8,
                    borderRadius: BorderRadius.circular(4),
                  ),
                ],
              ),
            ),

            // Quiz Content
            Expanded(
              child: SingleChildScrollView(
                padding: const EdgeInsets.all(16),
                child: _buildQuizWidget(currentQuestion),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildQuizWidget(QuizQuestion question) {
    switch (question.type) {
      case QuizType.multipleChoice:
        return MultipleChoiceQuiz(
          key: ValueKey(question.id),
          question: question,
          onCorrect: _onCorrect,
          onIncorrect: _onIncorrect,
        );
      case QuizType.imageMatching:
        return ImageMatchingQuiz(
          key: ValueKey(question.id),
          question: question,
          onCorrect: _onCorrect,
          onIncorrect: _onIncorrect,
        );
      case QuizType.trueFalse:
        return TrueFalseQuiz(
          key: ValueKey(question.id),
          question: question,
          onCorrect: _onCorrect,
          onIncorrect: _onIncorrect,
        );
      default:
        return const Center(
          child: Text(
            'Quiz type not supported yet',
            style: TextStyle(color: AppColors.textSecondary),
          ),
        );
    }
  }
}

