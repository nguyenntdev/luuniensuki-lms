import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:lms/core/theme/app_colors.dart';
import 'package:lms/features/practice/domain/models/quiz_question.dart';
import 'package:lms/features/practice/presentation/widgets/quiz_types/quiz_types.dart';

/// Quiz Components Showcase
/// 
/// This screen demonstrates all quiz types with examples.
/// Use this as a reference for implementing quizzes in your app.
class QuizComponentsShowcase extends ConsumerStatefulWidget {
  const QuizComponentsShowcase({super.key});

  @override
  ConsumerState<QuizComponentsShowcase> createState() => _QuizComponentsShowcaseState();
}

class _QuizComponentsShowcaseState extends ConsumerState<QuizComponentsShowcase> {
  int selectedIndex = 0;

  final List<String> quizTypeNames = [
    'Multiple Choice',
    'Image Matching',
    'True/False',
  ];

  final List<QuizType> quizTypes = [
    QuizType.multipleChoice,
    QuizType.imageMatching,
    QuizType.trueFalse,
  ];

  @override
  Widget build(BuildContext context) {
    final questions = MockQuizData.getQuestionsByType(quizTypes[selectedIndex]);
    
    return Scaffold(
      backgroundColor: AppColors.darkBackground,
      appBar: AppBar(
        backgroundColor: AppColors.darkSurface,
        elevation: 0,
        title: const Text(
          'Quiz Components Showcase',
          style: TextStyle(
            color: AppColors.gold,
            fontWeight: FontWeight.bold,
          ),
        ),
        centerTitle: true,
      ),
      body: Column(
        children: [
          // Type Selector
          Container(
            height: 60,
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
            child: ListView.builder(
              scrollDirection: Axis.horizontal,
              itemCount: quizTypeNames.length,
              itemBuilder: (context, index) {
                final isSelected = selectedIndex == index;
                return Padding(
                  padding: const EdgeInsets.only(right: 12),
                  child: ChoiceChip(
                    label: Text(quizTypeNames[index]),
                    selected: isSelected,
                    onSelected: (selected) {
                      if (selected) {
                        setState(() {
                          selectedIndex = index;
                        });
                      }
                    },
                    backgroundColor: AppColors.darkSurface,
                    selectedColor: AppColors.gold,
                    labelStyle: TextStyle(
                      color: isSelected ? AppColors.darkBackground : AppColors.textPrimary,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                );
              },
            ),
          ),

          // Quiz Display
          Expanded(
            child: questions.isEmpty
                ? const Center(
                    child: Text(
                      'No questions for this type',
                      style: TextStyle(color: AppColors.textSecondary),
                    ),
                  )
                : PageView.builder(
                    itemCount: questions.length,
                    itemBuilder: (context, index) {
                      return SingleChildScrollView(
                        padding: const EdgeInsets.all(16),
                        child: Column(
                          children: [
                            // Question info
                            Container(
                              margin: const EdgeInsets.only(bottom: 16),
                              padding: const EdgeInsets.all(12),
                              decoration: BoxDecoration(
                                color: AppColors.darkSurface,
                                borderRadius: BorderRadius.circular(12),
                                border: Border.all(
                                  color: AppColors.gold.withOpacity(0.3),
                                ),
                              ),
                              child: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  Row(
                                    children: [
                                      Container(
                                        padding: const EdgeInsets.symmetric(
                                          horizontal: 8,
                                          vertical: 4,
                                        ),
                                        decoration: BoxDecoration(
                                          color: AppColors.gold,
                                          borderRadius: BorderRadius.circular(4),
                                        ),
                                        child: Text(
                                          'Question ${index + 1}/${questions.length}',
                                          style: const TextStyle(
                                            fontSize: 12,
                                            fontWeight: FontWeight.bold,
                                            color: AppColors.darkBackground,
                                          ),
                                        ),
                                      ),
                                      const Spacer(),
                                      Text(
                                        '${questions[index].points} XP',
                                        style: const TextStyle(
                                          fontSize: 14,
                                          fontWeight: FontWeight.bold,
                                          color: AppColors.gold,
                                        ),
                                      ),
                                    ],
                                  ),
                                  const SizedBox(height: 8),
                                  Text(
                                    'ID: ${questions[index].id}',
                                    style: const TextStyle(
                                      fontSize: 12,
                                      color: AppColors.textSecondary,
                                    ),
                                  ),
                                  if (questions[index].hint != null) ...[
                                    const SizedBox(height: 4),
                                    Text(
                                      'Hint: ${questions[index].hint}',
                                      style: const TextStyle(
                                        fontSize: 12,
                                        color: AppColors.textSecondary,
                                        fontStyle: FontStyle.italic,
                                      ),
                                    ),
                                  ],
                                ],
                              ),
                            ),

                            // Quiz widget
                            _buildQuizWidget(questions[index]),
                          ],
                        ),
                      );
                    },
                  ),
          ),
        ],
      ),
    );
  }

  Widget _buildQuizWidget(QuizQuestion question) {
    switch (question.type) {
      case QuizType.multipleChoice:
        return MultipleChoiceQuiz(
          key: ValueKey(question.id),
          question: question,
          onCorrect: () => _showSnackBar('Correct! +${question.points} XP', Colors.green),
          onIncorrect: () => _showSnackBar('Incorrect!', Colors.red),
        );
      case QuizType.imageMatching:
        return ImageMatchingQuiz(
          key: ValueKey(question.id),
          question: question,
          onCorrect: () => _showSnackBar('Correct! +${question.points} XP', Colors.green),
          onIncorrect: () => _showSnackBar('Incorrect!', Colors.red),
        );
      case QuizType.trueFalse:
        return TrueFalseQuiz(
          key: ValueKey(question.id),
          question: question,
          onCorrect: () => _showSnackBar('Correct! +${question.points} XP', Colors.green),
          onIncorrect: () => _showSnackBar('Incorrect!', Colors.red),
        );
      default:
        return Container(
          padding: const EdgeInsets.all(24),
          child: const Text(
            'Quiz type not implemented',
            style: TextStyle(color: AppColors.textSecondary),
          ),
        );
    }
  }

  void _showSnackBar(String message, Color color) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(message),
        backgroundColor: color,
        duration: const Duration(milliseconds: 1000),
      ),
    );
  }
}

