import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:confetti/confetti.dart';

import '../../../../core/theme/app_colors.dart';
import '../../../../core/theme/app_typography.dart';
import '../../../../core/services/sound_service.dart';
import '../../../urn_viewer/data/models/urn_dtos.dart';
import '../../../gems/presentation/providers/gems_provider.dart';
import '../../../gems/domain/entities/gem_transaction.dart';
import '../../../mascot/presentation/widgets/mascot_bubble.dart';
import '../../../mascot/presentation/widgets/mascot_widget.dart';
import '../../../mascot/domain/mascot_messages.dart';

/// Quiz result screen showing score and feedback.
class QuizResultScreen extends ConsumerStatefulWidget {
  final QuizResultDto result;
  final List<QuizQuestionDto> questions;
  final Map<String, String> answers;
  final String motifId;

  const QuizResultScreen({
    super.key,
    required this.result,
    required this.questions,
    required this.answers,
    required this.motifId,
  });

  @override
  ConsumerState<QuizResultScreen> createState() => _QuizResultScreenState();
}

class _QuizResultScreenState extends ConsumerState<QuizResultScreen> {
  late ConfettiController _confettiController;

  @override
  void initState() {
    super.initState();
    _confettiController = ConfettiController(
      duration: const Duration(seconds: 3),
    );

    // Play confetti for passing or perfect scores
    if (widget.result.passed) {
      WidgetsBinding.instance.addPostFrameCallback((_) {
        _confettiController.play();

        // Play lesson complete sound
        ref.read(soundServiceProvider).playLessonComplete();

        // Award bonus gems for perfect score (100%)
        if (widget.result.percentage == 100) {
          ref.read(gemsNotifierProvider.notifier).addGems(
                amount: 5,
                type: GemTransactionType.earnedPerfect,
                description: 'Hoàn hảo: ${widget.result.totalQuestions}/${widget.result.totalQuestions} câu đúng',
              );

          // Show perfect score message from mascot
          Future.delayed(const Duration(milliseconds: 500), () {
            if (mounted) {
              showMascotBubble(
                context: context,
                message: MascotMessages.random(MascotMessages.perfectScore),
                expression: MascotExpression.celebrating,
                duration: const Duration(seconds: 4),
              );
            }
          });
        } else {
          // Show celebration message for passing
          Future.delayed(const Duration(milliseconds: 500), () {
            if (mounted) {
              showMascotBubble(
                context: context,
                message: MascotMessages.random(MascotMessages.celebration),
                expression: MascotExpression.happy,
                duration: const Duration(seconds: 4),
              );
            }
          });
        }
      });
    } else {
      // Show motivation for failing
      WidgetsBinding.instance.addPostFrameCallback((_) {
        Future.delayed(const Duration(milliseconds: 500), () {
          if (mounted) {
            showMascotBubble(
              context: context,
              message: MascotMessages.random(MascotMessages.motivation),
              expression: MascotExpression.encouraging,
              duration: const Duration(seconds: 4),
            );
          }
        });
      });
    }
  }

  @override
  void dispose() {
    _confettiController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.background,
      body: Stack(
        children: [
          // Main content
          SafeArea(
            child: SingleChildScrollView(
              padding: const EdgeInsets.all(24),
              child: Column(
                children: [
                  const SizedBox(height: 24),

                  // Result header
                  _buildResultHeader(),

                  const SizedBox(height: 32),

                  // Score card
                  _buildScoreCard(),

                  const SizedBox(height: 24),

                  // Stats row
                  _buildStatsRow(),

                  // New badges section
                  if (widget.result.newBadges.isNotEmpty) ...[
                    const SizedBox(height: 24),
                    _buildBadgesSection(),
                  ],

                  const SizedBox(height: 32),

                  // Action buttons
                  _buildActionButtons(),

                  const SizedBox(height: 24),

                  // Question review section
                  _buildReviewSection(),

                  const SizedBox(height: 32),
                ],
              ),
            ),
          ),

          // Confetti overlay
          Align(
            alignment: Alignment.topCenter,
            child: ConfettiWidget(
              confettiController: _confettiController,
              blastDirectionality: BlastDirectionality.explosive,
              shouldLoop: false,
              colors: const [
                AppColors.primary,
                AppColors.xpGold,
                AppColors.success,
                AppColors.badgePurple,
                Colors.orange,
              ],
              numberOfParticles: 30,
              gravity: 0.2,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildResultHeader() {
    final isPassed = widget.result.passed;
    final isPerfect = widget.result.percentage == 100;

    String emoji;
    String title;
    String subtitle;

    if (isPerfect) {
      emoji = '🏆';
      title = 'Xuất sắc!';
      subtitle = 'Bạn đã trả lời đúng tất cả câu hỏi!';
    } else if (isPassed) {
      emoji = '🎉';
      title = 'Tuyệt vời!';
      subtitle = 'Bạn đã vượt qua bài trắc nghiệm!';
    } else {
      emoji = '💪';
      title = 'Cố gắng thêm!';
      subtitle = 'Hãy ôn lại bài học và thử lại nhé!';
    }

    return Column(
      children: [
        Text(
          emoji,
          style: const TextStyle(fontSize: 64),
        ),
        const SizedBox(height: 16),
        Text(
          title,
          style: AppTypography.textTheme.headlineMedium?.copyWith(
            color: isPassed ? AppColors.success : AppColors.textPrimary,
            fontWeight: FontWeight.bold,
          ),
        ),
        const SizedBox(height: 8),
        Text(
          subtitle,
          style: AppTypography.textTheme.bodyLarge?.copyWith(
            color: AppColors.textSecondary,
          ),
          textAlign: TextAlign.center,
        ),
      ],
    );
  }

  Widget _buildScoreCard() {
    final isPassed = widget.result.passed;
    final percentage = widget.result.percentage;

    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(24),
      decoration: BoxDecoration(
        gradient: LinearGradient(
          colors: isPassed
              ? [
                  AppColors.success.withOpacity(0.15),
                  AppColors.success.withOpacity(0.05),
                ]
              : [
                  AppColors.error.withOpacity(0.15),
                  AppColors.error.withOpacity(0.05),
                ],
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
        ),
        borderRadius: BorderRadius.circular(20),
        border: Border.all(
          color: isPassed
              ? AppColors.success.withOpacity(0.3)
              : AppColors.error.withOpacity(0.3),
        ),
      ),
      child: Column(
        children: [
          // Percentage circle
          Stack(
            alignment: Alignment.center,
            children: [
              SizedBox(
                width: 120,
                height: 120,
                child: CircularProgressIndicator(
                  value: percentage / 100,
                  strokeWidth: 10,
                  backgroundColor: AppColors.border,
                  valueColor: AlwaysStoppedAnimation<Color>(
                    isPassed ? AppColors.success : AppColors.error,
                  ),
                ),
              ),
              Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Text(
                    '$percentage%',
                    style: AppTypography.textTheme.headlineLarge?.copyWith(
                      color: isPassed ? AppColors.success : AppColors.error,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                  Text(
                    isPassed ? 'Đạt' : 'Chưa đạt',
                    style: AppTypography.textTheme.labelMedium?.copyWith(
                      color: isPassed ? AppColors.success : AppColors.error,
                    ),
                  ),
                ],
              ),
            ],
          ),

          const SizedBox(height: 20),

          // Pass threshold info
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
            decoration: BoxDecoration(
              color: AppColors.surfaceElevated,
              borderRadius: BorderRadius.circular(20),
            ),
            child: Text(
              'Yêu cầu: 80% để đạt',
              style: AppTypography.textTheme.labelMedium?.copyWith(
                color: AppColors.textSecondary,
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildStatsRow() {
    return Row(
      children: [
        Expanded(
          child: _StatCard(
            icon: Icons.check_circle,
            iconColor: AppColors.success,
            value: '${widget.result.correctAnswers}',
            label: 'Đúng',
          ),
        ),
        const SizedBox(width: 12),
        Expanded(
          child: _StatCard(
            icon: Icons.cancel,
            iconColor: AppColors.error,
            value: '${widget.result.totalQuestions - widget.result.correctAnswers}',
            label: 'Sai',
          ),
        ),
        const SizedBox(width: 12),
        Expanded(
          child: _StatCard(
            icon: Icons.star,
            iconColor: AppColors.xpGold,
            value: '+${widget.result.xpEarned}',
            label: 'XP',
          ),
        ),
      ],
    );
  }

  Widget _buildBadgesSection() {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: AppColors.badgeSurface,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(
          color: AppColors.badgePurple.withOpacity(0.3),
        ),
      ),
      child: Column(
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              const Icon(
                Icons.military_tech,
                color: AppColors.badgePurple,
                size: 24,
              ),
              const SizedBox(width: 8),
              Text(
                'Huy hiệu mới!',
                style: AppTypography.textTheme.titleMedium?.copyWith(
                  color: AppColors.badgePurple,
                  fontWeight: FontWeight.bold,
                ),
              ),
            ],
          ),
          const SizedBox(height: 12),
          Wrap(
            spacing: 8,
            runSpacing: 8,
            alignment: WrapAlignment.center,
            children: widget.result.newBadges.map((badge) {
              return Container(
                padding: const EdgeInsets.symmetric(
                  horizontal: 12,
                  vertical: 8,
                ),
                decoration: BoxDecoration(
                  color: AppColors.surface,
                  borderRadius: BorderRadius.circular(20),
                ),
                child: Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    const Icon(
                      Icons.emoji_events,
                      color: AppColors.xpGold,
                      size: 18,
                    ),
                    const SizedBox(width: 6),
                    Text(
                      badge.name,
                      style: AppTypography.textTheme.labelMedium?.copyWith(
                        color: AppColors.textPrimary,
                        fontWeight: FontWeight.w500,
                      ),
                    ),
                  ],
                ),
              );
            }).toList(),
          ),
        ],
      ),
    );
  }

  Widget _buildActionButtons() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        // Retry button (if failed)
        if (!widget.result.passed)
          ElevatedButton.icon(
            onPressed: () {
              context.pop();
            },
            icon: const Icon(Icons.refresh),
            label: const Text('Làm lại'),
            style: ElevatedButton.styleFrom(
              backgroundColor: AppColors.primary,
              foregroundColor: AppColors.onPrimary,
              padding: const EdgeInsets.symmetric(vertical: 16),
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(12),
              ),
            ),
          ),

        if (!widget.result.passed) const SizedBox(height: 12),

        // Back to lesson button
        OutlinedButton.icon(
          onPressed: () {
            // Pop back to motif detail
            context.pop();
            context.pop();
          },
          icon: const Icon(Icons.arrow_back),
          label: const Text('Quay lại bài học'),
          style: OutlinedButton.styleFrom(
            foregroundColor: AppColors.textSecondary,
            side: BorderSide(color: AppColors.border),
            padding: const EdgeInsets.symmetric(vertical: 16),
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(12),
            ),
          ),
        ),

        const SizedBox(height: 12),

        // Continue exploring button (if passed)
        if (widget.result.passed)
          ElevatedButton.icon(
            onPressed: () {
              // Go back to explore/urn viewer
              context.go('/explore');
            },
            icon: const Icon(Icons.explore),
            label: const Text('Tiếp tục khám phá'),
            style: ElevatedButton.styleFrom(
              backgroundColor: AppColors.primary,
              foregroundColor: AppColors.onPrimary,
              padding: const EdgeInsets.symmetric(vertical: 16),
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(12),
              ),
            ),
          ),
      ],
    );
  }

  Widget _buildReviewSection() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          children: [
            Icon(
              Icons.rate_review_outlined,
              color: AppColors.textSecondary,
              size: 20,
            ),
            const SizedBox(width: 8),
            Text(
              'Xem lại câu trả lời',
              style: AppTypography.textTheme.titleMedium?.copyWith(
                color: AppColors.textSecondary,
                fontWeight: FontWeight.w600,
              ),
            ),
          ],
        ),
        const SizedBox(height: 16),
        ...widget.questions.asMap().entries.map((entry) {
          final index = entry.key;
          final question = entry.value;
          final userAnswer = widget.answers[question.id] ?? '';
          final isCorrect =
              userAnswer.trim().toLowerCase() ==
              question.correctAnswer.trim().toLowerCase();

          return _QuestionReviewCard(
            index: index + 1,
            question: question,
            userAnswer: userAnswer,
            isCorrect: isCorrect,
          );
        }),
      ],
    );
  }
}

/// Stat card widget
class _StatCard extends StatelessWidget {
  final IconData icon;
  final Color iconColor;
  final String value;
  final String label;

  const _StatCard({
    required this.icon,
    required this.iconColor,
    required this.value,
    required this.label,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: AppColors.surface,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: AppColors.border),
      ),
      child: Column(
        children: [
          Icon(icon, color: iconColor, size: 24),
          const SizedBox(height: 8),
          Text(
            value,
            style: AppTypography.textTheme.titleLarge?.copyWith(
              color: iconColor,
              fontWeight: FontWeight.bold,
            ),
          ),
          const SizedBox(height: 2),
          Text(
            label,
            style: AppTypography.textTheme.labelSmall?.copyWith(
              color: AppColors.textSecondary,
            ),
          ),
        ],
      ),
    );
  }
}

/// Question review card widget
class _QuestionReviewCard extends StatelessWidget {
  final int index;
  final QuizQuestionDto question;
  final String userAnswer;
  final bool isCorrect;

  const _QuestionReviewCard({
    required this.index,
    required this.question,
    required this.userAnswer,
    required this.isCorrect,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: AppColors.surface,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(
          color: isCorrect
              ? AppColors.success.withOpacity(0.3)
              : AppColors.error.withOpacity(0.3),
        ),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Header
          Row(
            children: [
              Container(
                width: 28,
                height: 28,
                decoration: BoxDecoration(
                  color: isCorrect
                      ? AppColors.success.withOpacity(0.15)
                      : AppColors.error.withOpacity(0.15),
                  shape: BoxShape.circle,
                ),
                child: Center(
                  child: Text(
                    '$index',
                    style: TextStyle(
                      color: isCorrect ? AppColors.success : AppColors.error,
                      fontWeight: FontWeight.bold,
                      fontSize: 12,
                    ),
                  ),
                ),
              ),
              const SizedBox(width: 10),
              Expanded(
                child: Text(
                  question.questionText,
                  style: AppTypography.textTheme.bodyMedium?.copyWith(
                    color: AppColors.textPrimary,
                  ),
                  maxLines: 2,
                  overflow: TextOverflow.ellipsis,
                ),
              ),
              Icon(
                isCorrect ? Icons.check_circle : Icons.cancel,
                color: isCorrect ? AppColors.success : AppColors.error,
                size: 24,
              ),
            ],
          ),

          const SizedBox(height: 12),

          // User's answer
          Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                'Bạn chọn: ',
                style: AppTypography.textTheme.labelSmall?.copyWith(
                  color: AppColors.textHint,
                ),
              ),
              Expanded(
                child: Text(
                  userAnswer.isEmpty ? '(Không trả lời)' : userAnswer,
                  style: AppTypography.textTheme.bodySmall?.copyWith(
                    color: isCorrect ? AppColors.success : AppColors.error,
                    fontWeight: FontWeight.w500,
                  ),
                ),
              ),
            ],
          ),

          // Correct answer (if wrong)
          if (!isCorrect) ...[
            const SizedBox(height: 4),
            Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  'Đáp án đúng: ',
                  style: AppTypography.textTheme.labelSmall?.copyWith(
                    color: AppColors.textHint,
                  ),
                ),
                Expanded(
                  child: Text(
                    question.correctAnswer,
                    style: AppTypography.textTheme.bodySmall?.copyWith(
                      color: AppColors.success,
                      fontWeight: FontWeight.w500,
                    ),
                  ),
                ),
              ],
            ),
          ],

          // Explanation (if available)
          if (question.explanation != null &&
              question.explanation!.isNotEmpty) ...[
            const SizedBox(height: 8),
            Container(
              padding: const EdgeInsets.all(10),
              decoration: BoxDecoration(
                color: AppColors.surfaceElevated,
                borderRadius: BorderRadius.circular(8),
              ),
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Icon(
                    Icons.lightbulb_outline,
                    size: 16,
                    color: AppColors.primary,
                  ),
                  const SizedBox(width: 8),
                  Expanded(
                    child: Text(
                      question.explanation!,
                      style: AppTypography.textTheme.bodySmall?.copyWith(
                        color: AppColors.textSecondary,
                        fontStyle: FontStyle.italic,
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ],
        ],
      ),
    );
  }
}
