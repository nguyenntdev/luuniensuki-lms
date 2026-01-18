import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../../../core/theme/app_colors.dart';
import '../../../../../core/utils/url_utils.dart';
import '../../../domain/models/quiz_question.dart';
import 'package:cached_network_image/cached_network_image.dart';

class ImageMatchingQuiz extends ConsumerStatefulWidget {
  final QuizQuestion question;
  final VoidCallback? onCorrect;
  final VoidCallback? onIncorrect;

  const ImageMatchingQuiz({
    super.key,
    required this.question,
    this.onCorrect,
    this.onIncorrect,
  });

  @override
  ConsumerState<ImageMatchingQuiz> createState() => _ImageMatchingQuizState();
}

class _ImageMatchingQuizState extends ConsumerState<ImageMatchingQuiz>
    with SingleTickerProviderStateMixin {
  String? selectedAnswer;
  bool? isCorrect;
  bool showFeedback = false;
  late AnimationController _feedbackController;
  late Animation<double> _scaleAnimation;
  late Animation<double> _glowAnimation;

  @override
  void initState() {
    super.initState();
    _feedbackController = AnimationController(
      duration: const Duration(milliseconds: 300),
      vsync: this,
    );
    _scaleAnimation = Tween<double>(begin: 1.0, end: 1.05).animate(
      CurvedAnimation(parent: _feedbackController, curve: Curves.easeOut),
    );
    _glowAnimation = Tween<double>(begin: 0.0, end: 1.0).animate(
      CurvedAnimation(parent: _feedbackController, curve: Curves.easeOut),
    );
  }

  @override
  void dispose() {
    _feedbackController.dispose();
    super.dispose();
  }

  void _selectAnswer(String answer) {
    if (showFeedback) return;

    setState(() {
      selectedAnswer = answer;
      isCorrect = answer == widget.question.correctAnswer;
      showFeedback = true;
    });

    _feedbackController.forward();

    Future.delayed(const Duration(milliseconds: 1500), () {
      if (mounted) {
        if (isCorrect!) {
          widget.onCorrect?.call();
        } else {
          widget.onIncorrect?.call();
        }
      }
    });
  }

  Widget _buildImage(String rawUrl) {
    final imageUrl = UrlUtils.getImageUrl(rawUrl);

    if (imageUrl.isEmpty) {
      return Container(
        color: AppColors.surface,
        child: const Icon(
          Icons.image_not_supported,
          color: AppColors.primary,
          size: 64,
        ),
      );
    }

    return CachedNetworkImage(
      imageUrl: imageUrl,
      fit: BoxFit.cover,
      placeholder: (context, url) => Container(
        color: AppColors.surface,
        child: const Center(
          child: CircularProgressIndicator(
            color: AppColors.primary,
          ),
        ),
      ),
      errorWidget: (context, url, error) {
        debugPrint('[PRACTICE_IMAGE] Failed to load image: $imageUrl - Error: $error');
        return Container(
          color: AppColors.surface,
          child: const Icon(
            Icons.image_not_supported,
            color: AppColors.primary,
            size: 64,
          ),
        );
      },
    );
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(24),
      decoration: BoxDecoration(
        gradient: LinearGradient(
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
          colors: [
            AppColors.background.withOpacity(0.8),
            AppColors.surface.withOpacity(0.8),
          ],
        ),
        borderRadius: BorderRadius.circular(24),
        border: Border.all(
          color: AppColors.primary.withOpacity(0.2),
          width: 1,
        ),
        boxShadow: [
          BoxShadow(
            color: AppColors.primary.withOpacity(0.1),
            blurRadius: 20,
            spreadRadius: 5,
          ),
        ],
      ),
      child: SingleChildScrollView(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            // Question
            Text(
              widget.question.question,
              style: const TextStyle(
                fontSize: 20,
                fontWeight: FontWeight.bold,
                color: AppColors.primary,
              ),
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 24),

            // Image Container with Glass Morphism
            Container(
              height: 250,
              decoration: BoxDecoration(
                borderRadius: BorderRadius.circular(20),
                border: Border.all(
                  color: AppColors.primary.withOpacity(0.3),
                  width: 2,
                ),
                boxShadow: [
                  BoxShadow(
                    color: AppColors.primary.withOpacity(0.2),
                    blurRadius: 20,
                    spreadRadius: 2,
                  ),
                ],
              ),
              child: ClipRRect(
                borderRadius: BorderRadius.circular(18),
                child: widget.question.imageUrl != null
                    ? _buildImage(widget.question.imageUrl!)
                    : Container(
                        color: AppColors.surface,
                        child: const Icon(
                          Icons.image,
                          color: AppColors.primary,
                          size: 64,
                        ),
                      ),
              ),
            ),
            const SizedBox(height: 24),

            // Options List
            ...widget.question.options.map((option) {
              final isSelected = selectedAnswer == option;
              final isCorrectOption = option == widget.question.correctAnswer;

              return Padding(
                padding: const EdgeInsets.only(bottom: 12),
                child: _OptionButton(
                  option: option,
                  isSelected: isSelected,
                  isCorrect: showFeedback && isCorrectOption ? true : null,
                  isIncorrect: showFeedback && isSelected && !isCorrectOption ? true : null,
                  onTap: () => _selectAnswer(option),
                  scaleAnimation: isSelected ? _scaleAnimation : null,
                  glowAnimation: isSelected ? _glowAnimation : null,
                ),
              );
            }).toList(),

            // Feedback Section
            if (showFeedback) ...[
              const SizedBox(height: 16),
              AnimatedBuilder(
                animation: _feedbackController,
                builder: (context, child) {
                  return Opacity(
                    opacity: _glowAnimation.value,
                    child: child,
                  );
                },
                child: Container(
                  padding: const EdgeInsets.all(16),
                  decoration: BoxDecoration(
                    color: isCorrect!
                        ? Colors.green.withOpacity(0.1)
                        : Colors.red.withOpacity(0.1),
                    borderRadius: BorderRadius.circular(12),
                    border: Border.all(
                      color: isCorrect! ? Colors.green : Colors.red,
                      width: 2,
                    ),
                  ),
                  child: Column(
                    children: [
                      Row(
                        children: [
                          Icon(
                            isCorrect! ? Icons.check_circle : Icons.cancel,
                            color: isCorrect! ? Colors.green : Colors.red,
                            size: 24,
                          ),
                          const SizedBox(width: 12),
                          Expanded(
                            child: Text(
                              isCorrect!
                                  ? '+${widget.question.points} XP'
                                  : 'Sai rồi!',
                              style: TextStyle(
                                fontSize: 18,
                                fontWeight: FontWeight.bold,
                                color: isCorrect! ? Colors.green : Colors.red,
                              ),
                            ),
                          ),
                        ],
                      ),
                      if (widget.question.explanation != null) ...[
                        const SizedBox(height: 8),
                        Text(
                          widget.question.explanation!,
                          style: const TextStyle(
                            fontSize: 14,
                            color: AppColors.textSecondary,
                          ),
                        ),
                      ],
                    ],
                  ),
                ),
              ),
            ],
          ],
        ),
      ),
    );
  }
}

class _OptionButton extends StatelessWidget {
  final String option;
  final bool isSelected;
  final bool? isCorrect;
  final bool? isIncorrect;
  final VoidCallback onTap;
  final Animation<double>? scaleAnimation;
  final Animation<double>? glowAnimation;

  const _OptionButton({
    required this.option,
    required this.isSelected,
    required this.isCorrect,
    required this.isIncorrect,
    required this.onTap,
    this.scaleAnimation,
    this.glowAnimation,
  });

  @override
  Widget build(BuildContext context) {
    Color backgroundColor;
    Color borderColor;
    Color textColor;
    List<BoxShadow> boxShadow = [];

    if (isCorrect == true) {
      backgroundColor = Colors.green.withOpacity(0.2);
      borderColor = Colors.green;
      textColor = Colors.green;
      boxShadow = [
        BoxShadow(
          color: Colors.green.withOpacity(0.5),
          blurRadius: 20,
          spreadRadius: 2,
        ),
      ];
    } else if (isIncorrect == true) {
      backgroundColor = Colors.red.withOpacity(0.2);
      borderColor = Colors.red;
      textColor = Colors.red;
    } else if (isSelected) {
      backgroundColor = AppColors.primary.withOpacity(0.1);
      borderColor = AppColors.primary;
      textColor = AppColors.primary;
    } else {
      backgroundColor = AppColors.surface.withOpacity(0.5);
      borderColor = AppColors.primary.withOpacity(0.3);
      textColor = AppColors.textPrimary;
    }

    Widget button = Container(
      height: 60,
      decoration: BoxDecoration(
        color: backgroundColor,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: borderColor, width: 2),
        boxShadow: boxShadow,
      ),
      child: Material(
        color: Colors.transparent,
        child: InkWell(
          onTap: (isCorrect != null || isIncorrect != null) ? null : onTap,
          borderRadius: BorderRadius.circular(16),
          child: Center(
            child: Padding(
              padding: const EdgeInsets.symmetric(horizontal: 16),
              child: Text(
                option,
                style: TextStyle(
                  fontSize: 16,
                  fontWeight: FontWeight.w600,
                  color: textColor,
                ),
                textAlign: TextAlign.center,
              ),
            ),
          ),
        ),
      ),
    );

    if (scaleAnimation != null && glowAnimation != null) {
      return AnimatedBuilder(
        animation: Listenable.merge([scaleAnimation, glowAnimation]),
        builder: (context, child) {
          return Transform.scale(
            scale: scaleAnimation!.value,
            child: child,
          );
        },
        child: button,
      );
    }

    return button;
  }
}

