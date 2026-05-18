import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../../../core/theme/app_colors.dart';
import '../../../domain/models/quiz_question.dart';

class TrueFalseQuiz extends ConsumerStatefulWidget {
  final QuizQuestion question;
  final VoidCallback? onCorrect;
  final VoidCallback? onIncorrect;

  const TrueFalseQuiz({
    super.key,
    required this.question,
    this.onCorrect,
    this.onIncorrect,
  });

  @override
  ConsumerState<TrueFalseQuiz> createState() => _TrueFalseQuizState();
}

class _TrueFalseQuizState extends ConsumerState<TrueFalseQuiz>
    with TickerProviderStateMixin {
  String? selectedAnswer;
  bool? isCorrect;
  bool showFeedback = false;
  late AnimationController _feedbackController;
  late AnimationController _shakeController;
  late Animation<double> _scaleAnimation;
  late Animation<double> _glowAnimation;
  late Animation<double> _shakeAnimation;

  @override
  void initState() {
    super.initState();
    _feedbackController = AnimationController(
      duration: const Duration(milliseconds: 300),
      vsync: this,
    );
    _shakeController = AnimationController(
      duration: const Duration(milliseconds: 500),
      vsync: this,
    );
    _scaleAnimation = Tween<double>(begin: 1.0, end: 1.05).animate(
      CurvedAnimation(parent: _feedbackController, curve: Curves.easeOut),
    );
    _glowAnimation = Tween<double>(begin: 0.0, end: 1.0).animate(
      CurvedAnimation(parent: _feedbackController, curve: Curves.easeOut),
    );
    _shakeAnimation = Tween<double>(begin: 0.0, end: 10.0).animate(
      CurvedAnimation(parent: _shakeController, curve: Curves.elasticIn),
    );
  }

  @override
  void dispose() {
    _feedbackController.dispose();
    _shakeController.dispose();
    super.dispose();
  }

  void _selectAnswer(String answer) {
    if (showFeedback) return;

    setState(() {
      selectedAnswer = answer;
      isCorrect = answer == widget.question.correctAnswer;
      showFeedback = true;
    });

    if (isCorrect!) {
      _feedbackController.forward();
    } else {
      _shakeController.forward();
    }

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
      child: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          // Question Icon
          Container(
            height: 80,
            width: 80,
            margin: const EdgeInsets.symmetric(horizontal: 100),
            decoration: BoxDecoration(
              shape: BoxShape.circle,
              gradient: LinearGradient(
                begin: Alignment.topLeft,
                end: Alignment.bottomRight,
                colors: [
                  AppColors.primary.withOpacity(0.3),
                  AppColors.primary.withOpacity(0.1),
                ],
              ),
              border: Border.all(
                color: AppColors.primary.withOpacity(0.5),
                width: 2,
              ),
            ),
            child: const Icon(
              Icons.quiz,
              size: 40,
              color: AppColors.primary,
            ),
          ),
          const SizedBox(height: 24),

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
          const SizedBox(height: 32),

          // True/False Buttons
          Row(
            children: [
              // True Button
              Expanded(
                child: _TrueFalseButton(
                  label: 'Đúng',
                  icon: Icons.check_circle_outline,
                  color: Colors.green,
                  isSelected: selectedAnswer == 'Đúng',
                  isCorrect: showFeedback && widget.question.correctAnswer == 'Đúng' ? true : null,
                  isIncorrect: showFeedback && selectedAnswer == 'Đúng' && widget.question.correctAnswer != 'Đúng' ? true : null,
                  onTap: () => _selectAnswer('Đúng'),
                  scaleAnimation: selectedAnswer == 'Đúng' && isCorrect == true ? _scaleAnimation : null,
                  glowAnimation: selectedAnswer == 'Đúng' && isCorrect == true ? _glowAnimation : null,
                  shakeAnimation: selectedAnswer == 'Đúng' && isCorrect == false ? _shakeAnimation : null,
                ),
              ),
              const SizedBox(width: 16),
              // False Button
              Expanded(
                child: _TrueFalseButton(
                  label: 'Sai',
                  icon: Icons.cancel_outlined,
                  color: Colors.red,
                  isSelected: selectedAnswer == 'Sai',
                  isCorrect: showFeedback && widget.question.correctAnswer == 'Sai' ? true : null,
                  isIncorrect: showFeedback && selectedAnswer == 'Sai' && widget.question.correctAnswer != 'Sai' ? true : null,
                  onTap: () => _selectAnswer('Sai'),
                  scaleAnimation: selectedAnswer == 'Sai' && isCorrect == true ? _scaleAnimation : null,
                  glowAnimation: selectedAnswer == 'Sai' && isCorrect == true ? _glowAnimation : null,
                  shakeAnimation: selectedAnswer == 'Sai' && isCorrect == false ? _shakeAnimation : null,
                ),
              ),
            ],
          ),

          // Feedback Section
          if (showFeedback) ...[
            const SizedBox(height: 24),
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
                                ? 'Chính xác! +${widget.question.points} XP' 
                                : 'Không chính xác!',
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
    );
  }
}

class _TrueFalseButton extends StatelessWidget {
  final String label;
  final IconData icon;
  final Color color;
  final bool isSelected;
  final bool? isCorrect;
  final bool? isIncorrect;
  final VoidCallback onTap;
  final Animation<double>? scaleAnimation;
  final Animation<double>? glowAnimation;
  final Animation<double>? shakeAnimation;

  const _TrueFalseButton({
    required this.label,
    required this.icon,
    required this.color,
    required this.isSelected,
    required this.isCorrect,
    required this.isIncorrect,
    required this.onTap,
    this.scaleAnimation,
    this.glowAnimation,
    this.shakeAnimation,
  });

  @override
  Widget build(BuildContext context) {
    Color backgroundColor;
    Color borderColor;
    Color textColor;
    List<BoxShadow> boxShadow = [];

    if (isCorrect == true) {
      backgroundColor = color.withOpacity(0.2);
      borderColor = color;
      textColor = color;
      boxShadow = [
        BoxShadow(
          color: color.withOpacity(0.5),
          blurRadius: 20,
          spreadRadius: 2,
        ),
      ];
    } else if (isIncorrect == true) {
      backgroundColor = Colors.red.withOpacity(0.2);
      borderColor = Colors.red;
      textColor = Colors.red;
    } else if (isSelected) {
      backgroundColor = color.withOpacity(0.1);
      borderColor = color;
      textColor = color;
    } else {
      backgroundColor = AppColors.surface.withOpacity(0.5);
      borderColor = color.withOpacity(0.3);
      textColor = AppColors.textPrimary;
    }

    Widget button = Container(
      height: 120,
      decoration: BoxDecoration(
        color: backgroundColor,
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: borderColor, width: 2),
        boxShadow: boxShadow,
      ),
      child: Material(
        color: Colors.transparent,
        child: InkWell(
          onTap: (isCorrect != null || isIncorrect != null) ? null : onTap,
          borderRadius: BorderRadius.circular(20),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Icon(
                icon,
                size: 48,
                color: textColor,
              ),
              const SizedBox(height: 8),
              Text(
                label,
                style: TextStyle(
                  fontSize: 20,
                  fontWeight: FontWeight.bold,
                  color: textColor,
                ),
              ),
            ],
          ),
        ),
      ),
    );

    if (shakeAnimation != null) {
      return AnimatedBuilder(
        animation: shakeAnimation!,
        builder: (context, child) {
          return Transform.translate(
            offset: Offset(shakeAnimation!.value * (shakeAnimation!.value % 2 == 0 ? 1 : -1), 0),
            child: child,
          );
        },
        child: button,
      );
    }

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

