import 'package:flutter/material.dart';
import 'package:cached_network_image/cached_network_image.dart';

import '../../../../core/theme/app_colors.dart';
import '../../../../core/theme/app_typography.dart';
import '../../../../core/utils/url_utils.dart';
import '../../../urn_viewer/data/models/urn_dtos.dart';

/// Question card widget that renders different question types.
class QuestionCard extends StatelessWidget {
  final QuizQuestionDto question;
  final String? selectedAnswer;
  final Function(String) onAnswerSelected;
  final Set<String>? hiddenOptions; // Options to hide (for hint system)

  const QuestionCard({
    super.key,
    required this.question,
    this.selectedAnswer,
    required this.onAnswerSelected,
    this.hiddenOptions,
  });

  @override
  Widget build(BuildContext context) {
    final resolvedImageUrl = UrlUtils.getImageUrl(question.imageUrl);
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        // Question image (if available)
        if (resolvedImageUrl.isNotEmpty) ...[
          ClipRRect(
            borderRadius: BorderRadius.circular(12),
            child: CachedNetworkImage(
              imageUrl: resolvedImageUrl,
              width: double.infinity,
              height: 180,
              fit: BoxFit.cover,
              placeholder: (_, __) => Container(
                height: 180,
                color: AppColors.surfaceVariant,
                child: const Center(
                  child: CircularProgressIndicator(
                    color: AppColors.primary,
                    strokeWidth: 2,
                  ),
                ),
              ),
              errorWidget: (_, __, ___) => Container(
                height: 180,
                color: AppColors.surfaceVariant,
                child: Icon(
                  Icons.broken_image,
                  color: AppColors.textHint,
                  size: 48,
                ),
              ),
            ),
          ),
          const SizedBox(height: 20),
        ],

        // Question text
        Container(
          width: double.infinity,
          padding: const EdgeInsets.all(16),
          decoration: BoxDecoration(
            color: AppColors.surface,
            borderRadius: BorderRadius.circular(12),
            border: Border.all(color: AppColors.border),
          ),
          child: Text(
            question.questionText,
            style: AppTypography.quizQuestion.copyWith(
              color: AppColors.textPrimary,
            ),
          ),
        ),

        const SizedBox(height: 20),

        // Answer options based on question type
        _buildAnswerOptions(),
      ],
    );
  }

  Widget _buildAnswerOptions() {
    final questionType = question.questionType.toLowerCase();

    switch (questionType) {
      case 'true_false':
      case 'truefalse':
        return _TrueFalseOptions(
          selectedAnswer: selectedAnswer,
          onAnswerSelected: onAnswerSelected,
        );
      case 'fill_blank':
      case 'fillblank':
      case 'fill_in_blank':
        return _FillBlankOption(
          selectedAnswer: selectedAnswer,
          onAnswerSelected: onAnswerSelected,
        );
      case 'multiple_choice':
      case 'multiplechoice':
      default:
        return _MultipleChoiceOptions(
          options: question.options,
          selectedAnswer: selectedAnswer,
          onAnswerSelected: onAnswerSelected,
          hiddenOptions: hiddenOptions,
        );
    }
  }
}

/// Multiple choice options widget
class _MultipleChoiceOptions extends StatelessWidget {
  final List<String> options;
  final String? selectedAnswer;
  final Function(String) onAnswerSelected;
  final Set<String>? hiddenOptions;

  const _MultipleChoiceOptions({
    required this.options,
    this.selectedAnswer,
    required this.onAnswerSelected,
    this.hiddenOptions,
  });

  @override
  Widget build(BuildContext context) {
    return Column(
      children: options.asMap().entries.map((entry) {
        final index = entry.key;
        final option = entry.value;
        final isSelected = selectedAnswer == option;
        final optionLabel = String.fromCharCode(65 + index); // A, B, C, D...
        final isHidden = hiddenOptions?.contains(option) ?? false;

        // Skip rendering hidden options with fade out animation
        if (isHidden) {
          return Padding(
            padding: const EdgeInsets.only(bottom: 12),
            child: AnimatedOpacity(
              opacity: 0.0,
              duration: const Duration(milliseconds: 500),
              child: AnimatedContainer(
                duration: const Duration(milliseconds: 500),
                height: 0,
                child: _OptionButton(
                  label: optionLabel,
                  text: option,
                  isSelected: false,
                  onTap: () {}, // Disabled
                ),
              ),
            ),
          );
        }

        return Padding(
          padding: const EdgeInsets.only(bottom: 12),
          child: _OptionButton(
            label: optionLabel,
            text: option,
            isSelected: isSelected,
            onTap: () => onAnswerSelected(option),
          ),
        );
      }).toList(),
    );
  }
}

/// True/False options widget
class _TrueFalseOptions extends StatelessWidget {
  final String? selectedAnswer;
  final Function(String) onAnswerSelected;

  const _TrueFalseOptions({
    this.selectedAnswer,
    required this.onAnswerSelected,
  });

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        Expanded(
          child: _TrueFalseButton(
            label: 'Đúng',
            value: 'true',
            icon: Icons.check_circle_outline,
            color: AppColors.success,
            isSelected: selectedAnswer?.toLowerCase() == 'true',
            onTap: () => onAnswerSelected('true'),
          ),
        ),
        const SizedBox(width: 12),
        Expanded(
          child: _TrueFalseButton(
            label: 'Sai',
            value: 'false',
            icon: Icons.cancel_outlined,
            color: AppColors.error,
            isSelected: selectedAnswer?.toLowerCase() == 'false',
            onTap: () => onAnswerSelected('false'),
          ),
        ),
      ],
    );
  }
}

/// Fill in the blank option widget
class _FillBlankOption extends StatefulWidget {
  final String? selectedAnswer;
  final Function(String) onAnswerSelected;

  const _FillBlankOption({
    this.selectedAnswer,
    required this.onAnswerSelected,
  });

  @override
  State<_FillBlankOption> createState() => _FillBlankOptionState();
}

class _FillBlankOptionState extends State<_FillBlankOption> {
  late TextEditingController _controller;

  @override
  void initState() {
    super.initState();
    _controller = TextEditingController(text: widget.selectedAnswer);
  }

  @override
  void didUpdateWidget(_FillBlankOption oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (widget.selectedAnswer != oldWidget.selectedAnswer) {
      _controller.text = widget.selectedAnswer ?? '';
    }
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: BoxDecoration(
        color: AppColors.surface,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: AppColors.border),
      ),
      child: TextField(
        controller: _controller,
        onChanged: widget.onAnswerSelected,
        style: TextStyle(
          color: AppColors.textPrimary,
          fontSize: 16,
        ),
        decoration: InputDecoration(
          hintText: 'Nhập câu trả lời của bạn...',
          hintStyle: TextStyle(
            color: AppColors.textHint,
          ),
          filled: true,
          fillColor: AppColors.surfaceElevated,
          border: OutlineInputBorder(
            borderRadius: BorderRadius.circular(12),
            borderSide: BorderSide.none,
          ),
          enabledBorder: OutlineInputBorder(
            borderRadius: BorderRadius.circular(12),
            borderSide: BorderSide(color: AppColors.border),
          ),
          focusedBorder: OutlineInputBorder(
            borderRadius: BorderRadius.circular(12),
            borderSide: BorderSide(color: AppColors.primary, width: 2),
          ),
          contentPadding: const EdgeInsets.all(16),
        ),
      ),
    );
  }
}

/// Option button for multiple choice
class _OptionButton extends StatefulWidget {
  final String label;
  final String text;
  final bool isSelected;
  final VoidCallback onTap;

  const _OptionButton({
    required this.label,
    required this.text,
    required this.isSelected,
    required this.onTap,
  });

  @override
  State<_OptionButton> createState() => _OptionButtonState();
}

class _OptionButtonState extends State<_OptionButton> {
  bool _isPressed = false;

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTapDown: (_) => setState(() => _isPressed = true),
      onTapUp: (_) {
        setState(() => _isPressed = false);
        widget.onTap();
      },
      onTapCancel: () => setState(() => _isPressed = false),
      child: AnimatedScale(
        scale: _isPressed ? 0.96 : 1.0,
        duration: const Duration(milliseconds: 100),
        child: AnimatedContainer(
          duration: const Duration(milliseconds: 200),
          padding: const EdgeInsets.all(16),
          decoration: BoxDecoration(
            color: widget.isSelected
                ? AppColors.primary.withOpacity(0.1)
                : AppColors.surface,
            borderRadius: BorderRadius.circular(12),
            border: Border.all(
              color: widget.isSelected ? AppColors.primary : AppColors.border,
              width: widget.isSelected ? 2 : 1,
            ),
          ),
          child: Row(
            children: [
              // Option label (A, B, C, D)
              Container(
                width: 32,
                height: 32,
                decoration: BoxDecoration(
                  color: widget.isSelected
                      ? AppColors.primary
                      : AppColors.surfaceElevated,
                  shape: BoxShape.circle,
                ),
                child: Center(
                  child: Text(
                    widget.label,
                    style: TextStyle(
                      color: widget.isSelected
                          ? AppColors.onPrimary
                          : AppColors.textSecondary,
                      fontWeight: FontWeight.bold,
                      fontSize: 14,
                    ),
                  ),
                ),
              ),
              const SizedBox(width: 12),

              // Option text
              Expanded(
                child: Text(
                  widget.text,
                  style: AppTypography.quizOption.copyWith(
                    color: widget.isSelected
                        ? AppColors.primary
                        : AppColors.textPrimary,
                    fontWeight: widget.isSelected ? FontWeight.w600 : FontWeight.normal,
                  ),
                ),
              ),

              // Selection indicator
              if (widget.isSelected)
                Icon(
                  Icons.check_circle,
                  color: AppColors.primary,
                  size: 24,
                ),
            ],
          ),
        ),
      ),
    );
  }
}

/// True/False button widget
class _TrueFalseButton extends StatefulWidget {
  final String label;
  final String value;
  final IconData icon;
  final Color color;
  final bool isSelected;
  final VoidCallback onTap;

  const _TrueFalseButton({
    required this.label,
    required this.value,
    required this.icon,
    required this.color,
    required this.isSelected,
    required this.onTap,
  });

  @override
  State<_TrueFalseButton> createState() => _TrueFalseButtonState();
}

class _TrueFalseButtonState extends State<_TrueFalseButton> {
  bool _isPressed = false;

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTapDown: (_) => setState(() => _isPressed = true),
      onTapUp: (_) {
        setState(() => _isPressed = false);
        widget.onTap();
      },
      onTapCancel: () => setState(() => _isPressed = false),
      child: AnimatedScale(
        scale: _isPressed ? 0.96 : 1.0,
        duration: const Duration(milliseconds: 100),
        child: AnimatedContainer(
          duration: const Duration(milliseconds: 200),
          padding: const EdgeInsets.symmetric(vertical: 24),
          decoration: BoxDecoration(
            color: widget.isSelected ? widget.color.withOpacity(0.15) : AppColors.surface,
            borderRadius: BorderRadius.circular(12),
            border: Border.all(
              color: widget.isSelected ? widget.color : AppColors.border,
              width: widget.isSelected ? 2 : 1,
            ),
          ),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Icon(
                widget.icon,
                size: 40,
                color: widget.isSelected ? widget.color : AppColors.textHint,
              ),
              const SizedBox(height: 8),
              Text(
                widget.label,
                style: AppTypography.textTheme.titleMedium?.copyWith(
                  color: widget.isSelected ? widget.color : AppColors.textSecondary,
                  fontWeight: widget.isSelected ? FontWeight.bold : FontWeight.normal,
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
