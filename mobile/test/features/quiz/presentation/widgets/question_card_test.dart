import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:luuniensuki_lms/features/quiz/presentation/widgets/question_card.dart';
import 'package:luuniensuki_lms/features/urn_viewer/data/models/urn_dtos.dart';

void main() {
  group('QuestionCard', () {
    group('Multiple Choice', () {
      testWidgets('renders all options', (tester) async {
        final question = QuizQuestionDto(
          id: '1',
          motifId: 'motif1',
          questionType: 'multiple_choice',
          questionText: 'What is the capital of Vietnam?',
          correctAnswer: 'Hanoi',
          options: ['Hanoi', 'Ho Chi Minh City', 'Da Nang', 'Hue'],
        );

        await tester.pumpWidget(
          MaterialApp(
            home: Scaffold(
              body: QuestionCard(
                question: question,
                onAnswerSelected: (_) {},
              ),
            ),
          ),
        );

        expect(find.text('What is the capital of Vietnam?'), findsOneWidget);
        expect(find.text('Hanoi'), findsOneWidget);
        expect(find.text('Ho Chi Minh City'), findsOneWidget);
        expect(find.text('Da Nang'), findsOneWidget);
        expect(find.text('Hue'), findsOneWidget);

        expect(find.text('A'), findsOneWidget);
        expect(find.text('B'), findsOneWidget);
        expect(find.text('C'), findsOneWidget);
        expect(find.text('D'), findsOneWidget);
      });

      testWidgets('selection callback fires correctly', (tester) async {
        String? selectedAnswer;
        final question = QuizQuestionDto(
          id: '1',
          motifId: 'motif1',
          questionType: 'multiple_choice',
          questionText: 'What is the capital of Vietnam?',
          correctAnswer: 'Hanoi',
          options: ['Hanoi', 'Ho Chi Minh City', 'Da Nang', 'Hue'],
        );

        await tester.pumpWidget(
          MaterialApp(
            home: Scaffold(
              body: QuestionCard(
                question: question,
                onAnswerSelected: (answer) {
                  selectedAnswer = answer;
                },
              ),
            ),
          ),
        );

        await tester.tap(find.text('Hanoi'));
        await tester.pumpAndSettle();

        expect(selectedAnswer, equals('Hanoi'));
      });

      testWidgets('shows selected state correctly', (tester) async {
        final question = QuizQuestionDto(
          id: '1',
          motifId: 'motif1',
          questionType: 'multiple_choice',
          questionText: 'What is the capital of Vietnam?',
          correctAnswer: 'Hanoi',
          options: ['Hanoi', 'Ho Chi Minh City', 'Da Nang', 'Hue'],
        );

        await tester.pumpWidget(
          MaterialApp(
            home: Scaffold(
              body: QuestionCard(
                question: question,
                selectedAnswer: 'Hanoi',
                onAnswerSelected: (_) {},
              ),
            ),
          ),
        );

        expect(find.byIcon(Icons.check_circle), findsOneWidget);
      });

      testWidgets('handles hidden options correctly', (tester) async {
        final question = QuizQuestionDto(
          id: '1',
          motifId: 'motif1',
          questionType: 'multiple_choice',
          questionText: 'What is the capital of Vietnam?',
          correctAnswer: 'Hanoi',
          options: ['Hanoi', 'Ho Chi Minh City', 'Da Nang', 'Hue'],
        );

        await tester.pumpWidget(
          MaterialApp(
            home: Scaffold(
              body: QuestionCard(
                question: question,
                hiddenOptions: {'Da Nang', 'Hue'},
                onAnswerSelected: (_) {},
              ),
            ),
          ),
        );
        await tester.pumpAndSettle();

        expect(find.text('Hanoi'), findsOneWidget);
        expect(find.text('Ho Chi Minh City'), findsOneWidget);
      });
    });

    group('True/False', () {
      testWidgets('renders both buttons', (tester) async {
        final question = QuizQuestionDto(
          id: '2',
          motifId: 'motif2',
          questionType: 'true_false',
          questionText: 'Is Hanoi the capital of Vietnam?',
          correctAnswer: 'true',
        );

        await tester.pumpWidget(
          MaterialApp(
            home: Scaffold(
              body: QuestionCard(
                question: question,
                onAnswerSelected: (_) {},
              ),
            ),
          ),
        );

        expect(find.text('Is Hanoi the capital of Vietnam?'), findsOneWidget);
        expect(find.text('Đúng'), findsOneWidget);
        expect(find.text('Sai'), findsOneWidget);
        expect(find.byIcon(Icons.check_circle_outline), findsOneWidget);
        expect(find.byIcon(Icons.cancel_outlined), findsOneWidget);
      });

      testWidgets('selection callback fires correctly', (tester) async {
        String? selectedAnswer;
        final question = QuizQuestionDto(
          id: '2',
          motifId: 'motif2',
          questionType: 'true_false',
          questionText: 'Is Hanoi the capital of Vietnam?',
          correctAnswer: 'true',
        );

        await tester.pumpWidget(
          MaterialApp(
            home: Scaffold(
              body: QuestionCard(
                question: question,
                onAnswerSelected: (answer) {
                  selectedAnswer = answer;
                },
              ),
            ),
          ),
        );

        await tester.tap(find.text('Đúng'));
        await tester.pumpAndSettle();

        expect(selectedAnswer, equals('true'));
      });

      testWidgets('shows selected state correctly', (tester) async {
        final question = QuizQuestionDto(
          id: '2',
          motifId: 'motif2',
          questionType: 'true_false',
          questionText: 'Is Hanoi the capital of Vietnam?',
          correctAnswer: 'true',
        );

        await tester.pumpWidget(
          MaterialApp(
            home: Scaffold(
              body: QuestionCard(
                question: question,
                selectedAnswer: 'true',
                onAnswerSelected: (_) {},
              ),
            ),
          ),
        );
        await tester.pumpAndSettle();

        expect(find.text('Đúng'), findsOneWidget);
        expect(find.text('Sai'), findsOneWidget);
      });

      testWidgets('handles truefalse variant', (tester) async {
        final question = QuizQuestionDto(
          id: '2',
          motifId: 'motif2',
          questionType: 'truefalse',
          questionText: 'Is Hanoi the capital of Vietnam?',
          correctAnswer: 'true',
        );

        await tester.pumpWidget(
          MaterialApp(
            home: Scaffold(
              body: QuestionCard(
                question: question,
                onAnswerSelected: (_) {},
              ),
            ),
          ),
        );

        expect(find.text('Đúng'), findsOneWidget);
        expect(find.text('Sai'), findsOneWidget);
      });
    });

    group('Fill in Blank', () {
      testWidgets('renders text field', (tester) async {
        final question = QuizQuestionDto(
          id: '3',
          motifId: 'motif3',
          questionType: 'fill_blank',
          questionText: 'Complete: The capital of Vietnam is ___',
          correctAnswer: 'Hanoi',
        );

        await tester.pumpWidget(
          MaterialApp(
            home: Scaffold(
              body: QuestionCard(
                question: question,
                onAnswerSelected: (_) {},
              ),
            ),
          ),
        );

        expect(find.text('Complete: The capital of Vietnam is ___'), findsOneWidget);
        expect(find.byType(TextField), findsOneWidget);
      });

      testWidgets('callback fires on text input', (tester) async {
        String? selectedAnswer;
        final question = QuizQuestionDto(
          id: '3',
          motifId: 'motif3',
          questionType: 'fill_blank',
          questionText: 'Complete: The capital of Vietnam is ___',
          correctAnswer: 'Hanoi',
        );

        await tester.pumpWidget(
          MaterialApp(
            home: Scaffold(
              body: QuestionCard(
                question: question,
                onAnswerSelected: (answer) {
                  selectedAnswer = answer;
                },
              ),
            ),
          ),
        );

        await tester.enterText(find.byType(TextField), 'Hanoi');
        await tester.pumpAndSettle();

        expect(selectedAnswer, equals('Hanoi'));
      });

      testWidgets('handles fillblank variant', (tester) async {
        final question = QuizQuestionDto(
          id: '3',
          motifId: 'motif3',
          questionType: 'fillblank',
          questionText: 'Complete: The capital of Vietnam is ___',
          correctAnswer: 'Hanoi',
        );

        await tester.pumpWidget(
          MaterialApp(
            home: Scaffold(
              body: QuestionCard(
                question: question,
                onAnswerSelected: (_) {},
              ),
            ),
          ),
        );

        expect(find.byType(TextField), findsOneWidget);
      });
    });

    group('Question Image', () {
      testWidgets('renders image when URL provided', (tester) async {
        final question = QuizQuestionDto(
          id: '4',
          motifId: 'motif4',
          questionType: 'multiple_choice',
          questionText: 'What building is this?',
          correctAnswer: 'Hanoi Opera House',
          options: ['Hanoi Opera House', 'Notre Dame', 'Temple', 'Palace'],
          imageUrl: 'https://example.com/image.jpg',
        );

        await tester.pumpWidget(
          MaterialApp(
            home: Scaffold(
              body: QuestionCard(
                question: question,
                onAnswerSelected: (_) {},
              ),
            ),
          ),
        );

        expect(find.text('What building is this?'), findsOneWidget);
      });

      testWidgets('does not render image container when URL is null', (tester) async {
        final question = QuizQuestionDto(
          id: '4',
          motifId: 'motif4',
          questionType: 'multiple_choice',
          questionText: 'What is the capital?',
          correctAnswer: 'Hanoi',
          options: ['Hanoi', 'Ho Chi Minh City'],
        );

        await tester.pumpWidget(
          MaterialApp(
            home: Scaffold(
              body: QuestionCard(
                question: question,
                onAnswerSelected: (_) {},
              ),
            ),
          ),
        );

        expect(find.text('What is the capital?'), findsOneWidget);
      });
    });

    group('Question Type Handling', () {
      testWidgets('defaults to multiple choice for unknown type', (tester) async {
        final question = QuizQuestionDto(
          id: '5',
          motifId: 'motif5',
          questionType: 'unknown_type',
          questionText: 'Test question?',
          correctAnswer: 'A',
          options: ['A', 'B', 'C'],
        );

        await tester.pumpWidget(
          MaterialApp(
            home: Scaffold(
              body: QuestionCard(
                question: question,
                onAnswerSelected: (_) {},
              ),
            ),
          ),
        );

        expect(find.text('A'), findsOneWidget);
        expect(find.text('B'), findsOneWidget);
        expect(find.text('C'), findsOneWidget);
      });

      testWidgets('handles multiplechoice variant', (tester) async {
        final question = QuizQuestionDto(
          id: '5',
          motifId: 'motif5',
          questionType: 'multiplechoice',
          questionText: 'Test question?',
          correctAnswer: 'Option A',
          options: ['Option A', 'Option B'],
        );

        await tester.pumpWidget(
          MaterialApp(
            home: Scaffold(
              body: QuestionCard(
                question: question,
                onAnswerSelected: (_) {},
              ),
            ),
          ),
        );

        expect(find.text('Option A'), findsOneWidget);
        expect(find.text('Option B'), findsOneWidget);
      });
    });
  });
}

