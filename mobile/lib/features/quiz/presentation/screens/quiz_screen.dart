import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../../core/theme/app_colors.dart';
import '../../../../core/theme/app_typography.dart';
import '../../../urn_viewer/data/models/urn_dtos.dart';
import '../providers/quiz_provider.dart';
import '../widgets/question_card.dart';
import 'quiz_result_screen.dart';

/// Quiz screen with question navigation and submission.
class QuizScreen extends ConsumerStatefulWidget {
  final String motifId;

  const QuizScreen({super.key, required this.motifId});

  @override
  ConsumerState<QuizScreen> createState() => _QuizScreenState();
}

class _QuizScreenState extends ConsumerState<QuizScreen> {
  int _currentQuestionIndex = 0;
  final Map<String, String> _answers = {};
  DateTime? _startTime;
  bool _isSubmitting = false;

  @override
  void initState() {
    super.initState();
    _startTime = DateTime.now();
  }

  @override
  Widget build(BuildContext context) {
    final quizAsync = ref.watch(quizProvider(widget.motifId));

    return Scaffold(
      backgroundColor: AppColors.background,
      appBar: AppBar(
        backgroundColor: AppColors.surface,
        foregroundColor: AppColors.textPrimary,
        title: const Text('Trắc nghiệm'),
        leading: IconButton(
          icon: const Icon(Icons.close),
          onPressed: () => _showExitConfirmation(context),
        ),
        actions: [
          quizAsync.maybeWhen(
            data: (quiz) => Center(
              child: Padding(
                padding: const EdgeInsets.only(right: 16),
                child: Container(
                  padding: const EdgeInsets.symmetric(
                    horizontal: 12,
                    vertical: 6,
                  ),
                  decoration: BoxDecoration(
                    color: AppColors.primary.withOpacity(0.15),
                    borderRadius: BorderRadius.circular(16),
                  ),
                  child: Text(
                    '${_currentQuestionIndex + 1}/${quiz.questions.length}',
                    style: AppTypography.textTheme.labelLarge?.copyWith(
                      color: AppColors.primary,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                ),
              ),
            ),
            orElse: () => const SizedBox(),
          ),
        ],
      ),
      body: quizAsync.when(
        loading: () => const Center(
          child: CircularProgressIndicator(
            color: AppColors.primary,
          ),
        ),
        error: (e, s) => _buildErrorState(e.toString()),
        data: (quiz) => _buildQuizContent(quiz),
      ),
    );
  }

  Widget _buildErrorState(String message) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(
              Icons.error_outline,
              size: 64,
              color: AppColors.error.withOpacity(0.7),
            ),
            const SizedBox(height: 16),
            Text(
              'Không thể tải câu hỏi',
              style: AppTypography.textTheme.titleLarge?.copyWith(
                color: AppColors.textPrimary,
              ),
            ),
            const SizedBox(height: 8),
            Text(
              message,
              style: AppTypography.textTheme.bodyMedium?.copyWith(
                color: AppColors.textSecondary,
              ),
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 24),
            ElevatedButton.icon(
              onPressed: () =>
                  ref.invalidate(quizProvider(widget.motifId)),
              icon: const Icon(Icons.refresh),
              label: const Text('Thử lại'),
              style: ElevatedButton.styleFrom(
                backgroundColor: AppColors.primary,
                foregroundColor: AppColors.onPrimary,
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildQuizContent(QuizResponseDto quiz) {
    if (quiz.questions.isEmpty) {
      return _buildEmptyState();
    }

    final currentQuestion = quiz.questions[_currentQuestionIndex];
    final isLastQuestion = _currentQuestionIndex == quiz.questions.length - 1;
    final hasAnswer = _answers.containsKey(currentQuestion.id);
    final allAnswered = _answers.length == quiz.questions.length;

    return Column(
      children: [
        // Progress bar
        LinearProgressIndicator(
          value: (_currentQuestionIndex + 1) / quiz.questions.length,
          backgroundColor: AppColors.surfaceElevated,
          valueColor: const AlwaysStoppedAnimation<Color>(AppColors.primary),
          minHeight: 4,
        ),

        // Question content
        Expanded(
          child: SingleChildScrollView(
            padding: const EdgeInsets.all(16),
            child: QuestionCard(
              question: currentQuestion,
              selectedAnswer: _answers[currentQuestion.id],
              onAnswerSelected: (answer) {
                setState(() {
                  _answers[currentQuestion.id] = answer;
                });
              },
            ),
          ),
        ),

        // Navigation buttons
        Container(
          padding: const EdgeInsets.all(16),
          decoration: BoxDecoration(
            color: AppColors.surface,
            border: Border(
              top: BorderSide(color: AppColors.border),
            ),
          ),
          child: SafeArea(
            top: false,
            child: Row(
              children: [
                // Previous button
                if (_currentQuestionIndex > 0)
                  Expanded(
                    child: OutlinedButton.icon(
                      onPressed: () {
                        setState(() {
                          _currentQuestionIndex--;
                        });
                      },
                      icon: const Icon(Icons.arrow_back, size: 18),
                      label: const Text('Câu trước'),
                      style: OutlinedButton.styleFrom(
                        foregroundColor: AppColors.textSecondary,
                        side: BorderSide(color: AppColors.border),
                        padding: const EdgeInsets.symmetric(vertical: 14),
                        shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(12),
                        ),
                      ),
                    ),
                  ),

                if (_currentQuestionIndex > 0) const SizedBox(width: 12),

                // Next/Submit button
                Expanded(
                  child: isLastQuestion
                      ? ElevatedButton.icon(
                          onPressed: allAnswered && !_isSubmitting
                              ? () => _submitQuiz(quiz)
                              : null,
                          icon: _isSubmitting
                              ? const SizedBox(
                                  width: 18,
                                  height: 18,
                                  child: CircularProgressIndicator(
                                    strokeWidth: 2,
                                    color: AppColors.onPrimary,
                                  ),
                                )
                              : const Icon(Icons.check, size: 18),
                          label: Text(_isSubmitting ? 'Đang nộp...' : 'Nộp bài'),
                          style: ElevatedButton.styleFrom(
                            backgroundColor: AppColors.success,
                            foregroundColor: Colors.white,
                            disabledBackgroundColor:
                                AppColors.success.withOpacity(0.5),
                            padding: const EdgeInsets.symmetric(vertical: 14),
                            shape: RoundedRectangleBorder(
                              borderRadius: BorderRadius.circular(12),
                            ),
                          ),
                        )
                      : ElevatedButton.icon(
                          onPressed: hasAnswer
                              ? () {
                                  setState(() {
                                    _currentQuestionIndex++;
                                  });
                                }
                              : null,
                          icon: const Icon(Icons.arrow_forward, size: 18),
                          label: const Text('Câu tiếp'),
                          style: ElevatedButton.styleFrom(
                            backgroundColor: AppColors.primary,
                            foregroundColor: AppColors.onPrimary,
                            disabledBackgroundColor:
                                AppColors.primary.withOpacity(0.5),
                            padding: const EdgeInsets.symmetric(vertical: 14),
                            shape: RoundedRectangleBorder(
                              borderRadius: BorderRadius.circular(12),
                            ),
                          ),
                        ),
                ),
              ],
            ),
          ),
        ),
      ],
    );
  }

  Widget _buildEmptyState() {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(32),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(
              Icons.quiz_outlined,
              size: 64,
              color: AppColors.textHint,
            ),
            const SizedBox(height: 16),
            Text(
              'Chưa có câu hỏi',
              style: AppTypography.textTheme.titleMedium?.copyWith(
                color: AppColors.textPrimary,
              ),
            ),
            const SizedBox(height: 8),
            Text(
              'Câu hỏi trắc nghiệm đang được cập nhật.',
              style: AppTypography.textTheme.bodyMedium?.copyWith(
                color: AppColors.textSecondary,
              ),
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 24),
            ElevatedButton(
              onPressed: () => context.pop(),
              style: ElevatedButton.styleFrom(
                backgroundColor: AppColors.primary,
                foregroundColor: AppColors.onPrimary,
              ),
              child: const Text('Quay lại'),
            ),
          ],
        ),
      ),
    );
  }

  void _showExitConfirmation(BuildContext context) {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        backgroundColor: AppColors.surface,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(16),
        ),
        title: Text(
          'Thoát trắc nghiệm?',
          style: AppTypography.textTheme.titleLarge?.copyWith(
            color: AppColors.textPrimary,
          ),
        ),
        content: Text(
          'Tiến trình làm bài sẽ bị mất. Bạn có chắc chắn muốn thoát?',
          style: AppTypography.textTheme.bodyMedium?.copyWith(
            color: AppColors.textSecondary,
          ),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: Text(
              'Tiếp tục làm',
              style: TextStyle(color: AppColors.textSecondary),
            ),
          ),
          TextButton(
            onPressed: () {
              Navigator.pop(context);
              context.pop();
            },
            child: Text(
              'Thoát',
              style: TextStyle(color: AppColors.error),
            ),
          ),
        ],
      ),
    );
  }

  Future<void> _submitQuiz(QuizResponseDto quiz) async {
    if (_isSubmitting) return;

    setState(() {
      _isSubmitting = true;
    });

    final timeSpent = DateTime.now().difference(_startTime!).inSeconds;

    try {
      final result = await ref.read(quizSubmissionProvider.notifier).submit(
            motifId: widget.motifId,
            answers: _answers,
            timeSpentSeconds: timeSpent,
          );

      if (result != null && mounted) {
        Navigator.pushReplacement(
          context,
          MaterialPageRoute(
            builder: (context) => QuizResultScreen(
              result: result,
              questions: quiz.questions,
              answers: _answers,
              motifId: widget.motifId,
            ),
          ),
        );
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Lỗi: ${e.toString()}'),
            backgroundColor: AppColors.error,
          ),
        );
      }
    } finally {
      if (mounted) {
        setState(() {
          _isSubmitting = false;
        });
      }
    }
  }
}
