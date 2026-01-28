import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../../core/theme/app_colors.dart';
import '../../../../core/theme/app_typography.dart';
import '../../../../core/services/sound_service.dart';
import '../../../../shared/widgets/shimmer/shimmer_skeleton.dart';
import '../../../urn_viewer/data/models/urn_dtos.dart';
import '../../../hearts/presentation/providers/hearts_provider.dart';
import '../../../hearts/presentation/widgets/hearts_display.dart';
import '../../../hearts/presentation/widgets/heart_lost_animation.dart';
import '../../../gems/presentation/providers/gems_provider.dart';
import '../../../gems/domain/entities/gem_transaction.dart';
import '../../data/models/quiz_progress.dart';
import '../providers/quiz_provider.dart';
import '../widgets/question_card.dart';
import '../widgets/hint_used_dialog.dart';
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
  final Map<String, bool> _incorrectAnswers = {}; // Track incorrect answers
  final Map<String, bool> _hintsUsed = {}; // Track hints used per question
  final Map<String, Set<String>> _hiddenOptions = {}; // Track hidden options per question
  int _totalGemsSpentOnHints = 0; // Track total gems spent on hints
  DateTime? _startTime;
  bool _isSubmitting = false;
  bool _hasCheckedSavedProgress = false;

  static const int _hintCost = 5; // Cost in gems per hint

  @override
  void initState() {
    super.initState();
    _startTime = DateTime.now();

    // Check for saved progress after build
    WidgetsBinding.instance.addPostFrameCallback((_) {
      _checkForSavedProgress();
    });
  }

  /// Check if there's saved progress and show resume dialog
  Future<void> _checkForSavedProgress() async {
    if (_hasCheckedSavedProgress) return;
    _hasCheckedSavedProgress = true;

    final quizState = ref.read(quizStateProvider(widget.motifId));

    if (quizState.hasSavedProgress && quizState.savedProgress != null) {
      final savedProgress = quizState.savedProgress!;

      try {
        // Verify quiz content hasn't changed - read AsyncValue state directly
        // instead of using .future to avoid race conditions
        final quizAsync = ref.read(quizProvider(widget.motifId));

        // Only proceed if quiz data is already available
        if (!quizAsync.hasValue || quizAsync.value == null) {
          // Quiz data not loaded yet, skip saved progress check
          // The build method will handle loading the quiz
          debugPrint('[QuizScreen] Quiz data not ready yet, skipping saved progress check');
          return;
        }

        final quiz = quizAsync.value!;

        // Check mounted after reading provider
        if (!mounted) return;

        final currentHash = QuizProgress.createQuestionsHash(
          quiz.questions.map((q) => {'id': q.id}).toList(),
        );

        if (currentHash != savedProgress.questionsHash) {
          // Quiz content changed, clear old progress
          ref.read(quizStateProvider(widget.motifId).notifier).clearProgress();
          return;
        }

        // Show resume dialog
        if (mounted) {
          final shouldResume = await _showResumeDialog(savedProgress);

          // Re-verify quiz data after dialog closes (user may have been on dialog for a while)
          if (!mounted) return;
          final currentQuizAsync = ref.read(quizProvider(widget.motifId));
          if (!currentQuizAsync.hasValue || currentQuizAsync.value == null) {
            debugPrint('[QuizScreen] Quiz data no longer valid after dialog');
            return;
          }
          final currentQuiz = currentQuizAsync.value!;

          if (shouldResume == true) {
            _resumeFromSavedProgress(savedProgress, currentQuiz.questions.length);
          } else {
            // Start fresh
            ref.read(quizStateProvider(widget.motifId).notifier).startFresh(currentQuiz);
          }
        }
      } catch (e, stackTrace) {
        // Log error for debugging instead of swallowing silently
        debugPrint('[QuizScreen] Error checking saved progress: $e');
        debugPrint('[QuizScreen] Stack trace: $stackTrace');
        // Don't rethrow - allow quiz to load normally via main build method
      }
    }
  }

  /// Show dialog asking user to resume or start fresh
  Future<bool?> _showResumeDialog(QuizProgress progress) {
    return showDialog<bool>(
      context: context,
      barrierDismissible: false,
      builder: (context) => AlertDialog(
        backgroundColor: AppColors.surface,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(16),
        ),
        title: Row(
          children: [
            Icon(Icons.restore, color: AppColors.primary, size: 24),
            const SizedBox(width: 8),
            Expanded(
              child: Text(
                'Tiếp tục bài quiz?',
                style: AppTypography.textTheme.titleLarge?.copyWith(
                  color: AppColors.textPrimary,
                ),
              ),
            ),
          ],
        ),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Bạn có bài quiz chưa hoàn thành:',
              style: AppTypography.textTheme.bodyMedium?.copyWith(
                color: AppColors.textSecondary,
              ),
            ),
            const SizedBox(height: 12),
            _buildProgressInfo('Câu hỏi', '${progress.currentQuestionIndex + 1}'),
            const SizedBox(height: 8),
            _buildProgressInfo('Đã trả lời', '${progress.answers.length} câu'),
            const SizedBox(height: 8),
            _buildProgressInfo('Thời gian', _formatDuration(progress.timeSpentSeconds)),
            const SizedBox(height: 16),
            Text(
              'Bạn muốn tiếp tục hay bắt đầu lại?',
              style: AppTypography.textTheme.bodyMedium?.copyWith(
                color: AppColors.textPrimary,
                fontWeight: FontWeight.w500,
              ),
            ),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => context.pop(false),
            child: Text(
              'Bắt đầu lại',
              style: TextStyle(color: AppColors.textSecondary),
            ),
          ),
          ElevatedButton(
            onPressed: () => context.pop(true),
            style: ElevatedButton.styleFrom(
              backgroundColor: AppColors.primary,
              foregroundColor: AppColors.onPrimary,
            ),
            child: const Text('Tiếp tục'),
          ),
        ],
      ),
    );
  }

  Widget _buildProgressInfo(String label, String value) {
    return Row(
      children: [
        Icon(Icons.check_circle_outline, size: 16, color: AppColors.primary),
        const SizedBox(width: 8),
        Text(
          '$label: ',
          style: AppTypography.textTheme.bodySmall?.copyWith(
            color: AppColors.textSecondary,
          ),
        ),
        Text(
          value,
          style: AppTypography.textTheme.bodySmall?.copyWith(
            color: AppColors.textPrimary,
            fontWeight: FontWeight.w600,
          ),
        ),
      ],
    );
  }

  String _formatDuration(int seconds) {
    final minutes = seconds ~/ 60;
    final secs = seconds % 60;
    if (minutes > 0) {
      return '$minutes phút $secs giây';
    }
    return '$secs giây';
  }

  /// Resume from saved progress
  /// [questionCount] is used to validate and clamp the current question index
  void _resumeFromSavedProgress(QuizProgress progress, int questionCount) {
    // Validate and clamp index to prevent RangeError
    final maxIndex = questionCount > 0 ? questionCount - 1 : 0;
    final safeIndex = progress.currentQuestionIndex.clamp(0, maxIndex);

    setState(() {
      _currentQuestionIndex = safeIndex;
      _answers.addAll(progress.answers);
      _incorrectAnswers.addAll(progress.incorrectAnswers);
      _startTime = DateTime.now().subtract(
        Duration(seconds: progress.timeSpentSeconds),
      );
    });

    ref.read(quizStateProvider(widget.motifId).notifier).resumeProgress();
  }


  @override
  Widget build(BuildContext context) {
    final quizAsync = ref.watch(quizProvider(widget.motifId));

    // Debug logging
    debugPrint('[QuizScreen] build() called for motifId: ${widget.motifId}');
    debugPrint('[QuizScreen] quizAsync state: ${quizAsync.runtimeType}');
    debugPrint('[QuizScreen] isLoading: ${quizAsync.isLoading}, hasError: ${quizAsync.hasError}, hasValue: ${quizAsync.hasValue}');
    if (quizAsync.hasError) {
      debugPrint('[QuizScreen] Error: ${quizAsync.error}');
    }
    if (quizAsync.hasValue) {
      debugPrint('[QuizScreen] Value: ${quizAsync.value?.questions.length ?? 0} questions');
    }

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
          // Gems display
          Padding(
            padding: const EdgeInsets.only(right: 8),
            child: Center(
              child: Container(
                padding: const EdgeInsets.symmetric(
                  horizontal: 12,
                  vertical: 6,
                ),
                decoration: BoxDecoration(
                  color: AppColors.primary.withOpacity(0.15),
                  borderRadius: BorderRadius.circular(16),
                ),
                child: Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Icon(
                      Icons.diamond_rounded,
                      color: AppColors.gemYellow,
                      size: 16,
                    ),
                    const SizedBox(width: 4),
                    Text(
                      '${ref.watch(gemsNotifierProvider).balance}',
                      style: AppTypography.textTheme.labelLarge?.copyWith(
                        color: AppColors.primary,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                  ],
                ),
              ),
            ),
          ),

          // Hearts display
          Padding(
            padding: const EdgeInsets.only(right: 8),
            child: CompactHeartsDisplay(
              onTap: () {
                // Show hearts info dialog
                _showHeartsInfoDialog(context);
              },
            ),
          ),

          // Question counter
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
        loading: () => _buildQuizShimmer(),
        error: (e, s) => _buildErrorState(e.toString()),
        data: (quiz) => _buildQuizContent(quiz),
      ),
    );
  }

  /// Format raw error message to user-friendly Vietnamese message
  String _formatErrorForUser(String rawError) {
    if (rawError.contains('Lesson not completed') ||
        rawError.contains('lesson not completed')) {
      return 'Bạn cần hoàn thành bài học trước khi làm trắc nghiệm.';
    }
    if (rawError.contains('NotFoundException') ||
        rawError.contains('404') ||
        rawError.contains('Not Found')) {
      return 'Không tìm thấy bài trắc nghiệm cho họa tiết này.';
    }
    if (rawError.contains('NetworkException') ||
        rawError.contains('SocketException') ||
        rawError.contains('timeout') ||
        rawError.contains('Connection refused')) {
      return 'Không có kết nối mạng. Vui lòng kiểm tra lại.';
    }
    if (rawError.contains('401') || rawError.contains('Unauthorized')) {
      return 'Phiên đăng nhập đã hết hạn. Vui lòng đăng nhập lại.';
    }
    if (rawError.contains('500') || rawError.contains('Internal Server Error')) {
      return 'Lỗi máy chủ. Vui lòng thử lại sau.';
    }
    // Log the raw error for debugging but show generic message
    debugPrint('[QuizScreen] Unhandled error: $rawError');
    return 'Đã xảy ra lỗi. Vui lòng thử lại sau.';
  }

  Widget _buildErrorState(String message) {
    final displayMessage = _formatErrorForUser(message);

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
              displayMessage,
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
            const SizedBox(height: 12),
            TextButton(
              onPressed: () => context.pop(),
              child: Text(
                'Quay lại',
                style: TextStyle(color: AppColors.textSecondary),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildQuizShimmer() {
    return SafeArea(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Progress bar shimmer
            ShimmerSkeleton(
              width: double.infinity,
              height: 8,
              borderRadius: BorderRadius.circular(4),
            ),
            const SizedBox(height: 16),
            // Question number shimmer
            ShimmerSkeleton(
              width: 120,
              height: 20,
              borderRadius: BorderRadius.circular(4),
            ),
            const SizedBox(height: 24),
            // Question text shimmer (2 lines)
            ShimmerSkeleton(
              width: double.infinity,
              height: 24,
              borderRadius: BorderRadius.circular(4),
            ),
            const SizedBox(height: 8),
            ShimmerSkeleton(
              width: MediaQuery.of(context).size.width * 0.7,
              height: 24,
              borderRadius: BorderRadius.circular(4),
            ),
            const SizedBox(height: 32),
            // Answer options shimmer (4 cards)
            Expanded(
              child: ListView.builder(
                itemCount: 4,
                itemBuilder: (context, index) => Padding(
                  padding: const EdgeInsets.only(bottom: 12),
                  child: ShimmerSkeleton(
                    width: double.infinity,
                    height: 60,
                    borderRadius: BorderRadius.circular(12),
                  ),
                ),
              ),
            ),
            const SizedBox(height: 16),
            // Navigation buttons shimmer
            Row(
              children: [
                Expanded(
                  child: ShimmerSkeleton(
                    width: double.infinity,
                    height: 48,
                    borderRadius: BorderRadius.circular(12),
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: ShimmerSkeleton(
                    width: double.infinity,
                    height: 48,
                    borderRadius: BorderRadius.circular(12),
                  ),
                ),
              ],
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

    // Validate index bounds to prevent RangeError
    if (_currentQuestionIndex >= quiz.questions.length) {
      debugPrint('[QuizScreen] Index out of bounds: $_currentQuestionIndex >= ${quiz.questions.length}, clamping to 0');
      _currentQuestionIndex = 0;
    }

    final currentQuestion = quiz.questions[_currentQuestionIndex];
    final isLastQuestion = _currentQuestionIndex == quiz.questions.length - 1;
    final hasAnswer = _answers.containsKey(currentQuestion.id);
    final allAnswered = _answers.length == quiz.questions.length;
    final isMultipleChoice = currentQuestion.questionType.toLowerCase() == 'multiple_choice' ||
                            currentQuestion.questionType.toLowerCase() == 'multiplechoice';
    final hasUsedHint = _hintsUsed[currentQuestion.id] ?? false;
    final gemsState = ref.watch(gemsNotifierProvider);
    final canAffordHint = gemsState.balance >= _hintCost;

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
            child: Column(
              children: [
                // Hint button (only for multiple choice questions)
                if (isMultipleChoice && currentQuestion.options.length >= 4)
                  Padding(
                    padding: const EdgeInsets.only(bottom: 16),
                    child: _buildHintButton(
                      currentQuestion,
                      hasUsedHint: hasUsedHint,
                      canAffordHint: canAffordHint,
                    ),
                  ),

                // Question card
                QuestionCard(
                  question: currentQuestion,
                  selectedAnswer: _answers[currentQuestion.id],
                  hiddenOptions: _hiddenOptions[currentQuestion.id],
                  onAnswerSelected: (answer) async {
                    // Check if this is a new answer
                    final previousAnswer = _answers[currentQuestion.id];

                    setState(() {
                      _answers[currentQuestion.id] = answer;
                    });

                    // Save progress auto-save
                    ref.read(quizStateProvider(widget.motifId).notifier).setAnswer(
                      currentQuestion.id,
                      answer,
                    );

                    // Check if answer is incorrect and we haven't already penalized this question
                    final correctAnswer = currentQuestion.correctAnswer ?? '';
                    final isCorrect = correctAnswer.trim().toLowerCase() ==
                                      answer.trim().toLowerCase();

                    // Play sound effect based on answer
                    final soundService = ref.read(soundServiceProvider);
                    if (isCorrect) {
                      await soundService.playCorrect();
                    } else {
                      await soundService.playWrong();
                    }

                    if (!isCorrect &&
                        previousAnswer != answer &&
                        !_incorrectAnswers.containsKey(currentQuestion.id)) {
                      // Mark this question as having an incorrect answer
                      _incorrectAnswers[currentQuestion.id] = true;

                      // Save incorrect answer state
                      ref.read(quizStateProvider(widget.motifId).notifier).markIncorrect(
                        currentQuestion.id,
                      );

                      // Deduct a heart
                      await ref.read(heartsNotifierProvider.notifier).loseHeart();

                      // Show heart lost animation
                      if (mounted) {
                        showHeartLostAnimation(context);
                      }

                      // Check if out of hearts
                      final hasHearts = ref.read(heartsNotifierProvider).hasHearts;
                      if (!hasHearts && mounted) {
                        // Navigate to hearts refill screen after a short delay
                        await Future.delayed(const Duration(milliseconds: 1500));
                        if (mounted) {
                          context.push('/hearts-refill?returnPath=/quiz/${widget.motifId}');
                        }
                      }
                    }
                  },
                ),
              ],
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
                        // Save progress
                        ref.read(quizStateProvider(widget.motifId).notifier).setQuestionIndex(
                          _currentQuestionIndex,
                        );
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
                                  // Save progress
                                  ref.read(quizStateProvider(widget.motifId).notifier).setQuestionIndex(
                                    _currentQuestionIndex,
                                  );
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

  /// Build hint button widget
  Widget _buildHintButton(
    QuizQuestionDto question, {
    required bool hasUsedHint,
    required bool canAffordHint,
  }) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: AppColors.surfaceElevated,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(
          color: AppColors.border,
          width: 1,
        ),
      ),
      child: Row(
        children: [
          // Hint icon
          Container(
            width: 40,
            height: 40,
            decoration: BoxDecoration(
              color: hasUsedHint
                  ? AppColors.textHint.withOpacity(0.2)
                  : AppColors.warning.withOpacity(0.2),
              shape: BoxShape.circle,
            ),
            child: Icon(
              Icons.lightbulb_outline,
              color: hasUsedHint ? AppColors.textHint : AppColors.warning,
              size: 24,
            ),
          ),

          const SizedBox(width: 12),

          // Hint text
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  hasUsedHint ? 'Đã sử dụng gợi ý' : 'Gợi ý',
                  style: AppTypography.textTheme.titleSmall?.copyWith(
                    color: hasUsedHint
                        ? AppColors.textHint
                        : AppColors.textPrimary,
                    fontWeight: FontWeight.w600,
                  ),
                ),
                const SizedBox(height: 2),
                Text(
                  hasUsedHint
                      ? '2 đáp án sai đã bị loại'
                      : 'Loại bỏ 2 đáp án sai',
                  style: AppTypography.textTheme.bodySmall?.copyWith(
                    color: AppColors.textSecondary,
                  ),
                ),
              ],
            ),
          ),

          // Use hint button
          if (!hasUsedHint)
            ElevatedButton.icon(
              onPressed: canAffordHint
                  ? () => _useHint(question)
                  : null,
              icon: Icon(
                Icons.diamond_rounded,
                color: AppColors.onPrimary,
                size: 16,
              ),
              label: Text('$_hintCost'),
              style: ElevatedButton.styleFrom(
                backgroundColor: AppColors.warning,
                foregroundColor: AppColors.onPrimary,
                disabledBackgroundColor: AppColors.textHint.withOpacity(0.3),
                padding: const EdgeInsets.symmetric(
                  horizontal: 16,
                  vertical: 8,
                ),
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(20),
                ),
              ),
            ),
        ],
      ),
    );
  }

  /// Use hint - removes 2 wrong answers for multiple choice questions
  Future<void> _useHint(QuizQuestionDto question) async {
    // Check if already used hint for this question
    if (_hintsUsed[question.id] ?? false) return;

    // Check if can afford
    final gemsNotifier = ref.read(gemsNotifierProvider.notifier);
    if (!gemsNotifier.canAfford(_hintCost)) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: const Text('Không đủ gems để sử dụng gợi ý!'),
            backgroundColor: AppColors.error,
            behavior: SnackBarBehavior.floating,
          ),
        );
      }
      return;
    }

    // Deduct gems
    final success = await gemsNotifier.spendGems(
      amount: _hintCost,
      type: GemTransactionType.spentHint,
      description: 'Sử dụng gợi ý trong quiz',
    );

    if (!success) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: const Text('Không thể sử dụng gợi ý!'),
            backgroundColor: AppColors.error,
            behavior: SnackBarBehavior.floating,
          ),
        );
      }
      return;
    }

    // Find 2 wrong answers to hide
    final correctAnswer = question.correctAnswer ?? '';
    final wrongOptions = question.options
        .where((option) => option.trim().toLowerCase() != correctAnswer.trim().toLowerCase())
        .toList();

    // Shuffle and take 2
    wrongOptions.shuffle();
    final optionsToHide = wrongOptions.take(2).toSet();

    // Update state
    setState(() {
      _hintsUsed[question.id] = true;
      _hiddenOptions[question.id] = optionsToHide;
      _totalGemsSpentOnHints += _hintCost;
    });

    // Show hint used dialog
    if (mounted) {
      showDialog(
        context: context,
        barrierDismissible: false,
        builder: (context) => HintUsedDialog(
          gemsDeducted: _hintCost,
          onDismiss: () {
            if (mounted) {
              Navigator.of(context).pop();
            }
          },
        ),
      );
    }
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
          'Tiến trình làm bài đã được tự động lưu. Bạn có thể tiếp tục sau. Bạn có chắc chắn muốn thoát?',
          style: AppTypography.textTheme.bodyMedium?.copyWith(
            color: AppColors.textSecondary,
          ),
        ),
        actions: [
          TextButton(
            onPressed: () => context.pop(),
            child: Text(
              'Tiếp tục làm',
              style: TextStyle(color: AppColors.textSecondary),
            ),
          ),
          TextButton(
            onPressed: () {
              context.pop();
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

  void _showHeartsInfoDialog(BuildContext context) {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        backgroundColor: AppColors.surface,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(16),
        ),
        title: Row(
          children: [
            Icon(Icons.favorite, color: AppColors.error, size: 24),
            const SizedBox(width: 8),
            Text(
              'Hệ Thống Tim',
              style: AppTypography.textTheme.titleLarge?.copyWith(
                color: AppColors.textPrimary,
              ),
            ),
          ],
        ),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Mỗi câu trả lời sai sẽ làm bạn mất 1 tim.',
              style: AppTypography.textTheme.bodyMedium?.copyWith(
                color: AppColors.textSecondary,
              ),
            ),
            const SizedBox(height: 12),
            Text(
              '• Tim sẽ tự động hồi mỗi 30 phút',
              style: AppTypography.textTheme.bodyMedium?.copyWith(
                color: AppColors.textSecondary,
              ),
            ),
            const SizedBox(height: 8),
            Text(
              '• Tối đa 5 tim',
              style: AppTypography.textTheme.bodyMedium?.copyWith(
                color: AppColors.textSecondary,
              ),
            ),
            const SizedBox(height: 8),
            Row(
              children: [
                Text(
                  '• Khi hết tim, bạn có thể đợi hoặc nạp bằng ',
                  style: AppTypography.textTheme.bodyMedium?.copyWith(
                    color: AppColors.textSecondary,
                  ),
                ),
                Icon(
                  Icons.diamond_rounded,
                  color: AppColors.gemYellow,
                  size: 16,
                ),
              ],
            ),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => context.pop(),
            child: Text(
              'Đã hiểu',
              style: TextStyle(color: AppColors.primary),
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

    // Add null check for _startTime
    final startTime = _startTime;
    if (startTime == null) {
      if (mounted) {
        setState(() {
          _isSubmitting = false;
        });
      }
      return;
    }

    final timeSpent = DateTime.now().difference(startTime).inSeconds;

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
