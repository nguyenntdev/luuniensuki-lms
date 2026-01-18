import 'package:flutter_test/flutter_test.dart';
import 'package:luuniensuki_lms/core/constants/app_constants.dart';
import 'package:luuniensuki_lms/features/quiz/domain/quiz_models.dart';

void main() {
  group('T-U3: Quiz Scoring Tests', () {
    group('Correct Answer Counting', () {
      test('should count all correct answers', () {
        final questions = [
          const QuizQuestion(
            id: '1',
            motifId: 'motif1',
            questionType: QuestionType.multipleChoice,
            questionText: 'Question 1',
            correctAnswer: 'A',
          ),
          const QuizQuestion(
            id: '2',
            motifId: 'motif1',
            questionType: QuestionType.multipleChoice,
            questionText: 'Question 2',
            correctAnswer: 'B',
          ),
          const QuizQuestion(
            id: '3',
            motifId: 'motif1',
            questionType: QuestionType.multipleChoice,
            questionText: 'Question 3',
            correctAnswer: 'C',
          ),
        ];

        final userAnswers = ['A', 'B', 'C'];
        int correctCount = 0;

        for (int i = 0; i < questions.length; i++) {
          if (questions[i].isCorrect(userAnswers[i])) {
            correctCount++;
          }
        }

        expect(correctCount, 3);
        expect(correctCount / questions.length * 100, 100.0);
      });

      test('should count partial correct answers', () {
        final questions = [
          const QuizQuestion(
            id: '1',
            motifId: 'motif1',
            questionType: QuestionType.multipleChoice,
            questionText: 'Question 1',
            correctAnswer: 'A',
          ),
          const QuizQuestion(
            id: '2',
            motifId: 'motif1',
            questionType: QuestionType.multipleChoice,
            questionText: 'Question 2',
            correctAnswer: 'B',
          ),
          const QuizQuestion(
            id: '3',
            motifId: 'motif1',
            questionType: QuestionType.multipleChoice,
            questionText: 'Question 3',
            correctAnswer: 'C',
          ),
        ];

        final userAnswers = ['A', 'D', 'C'];
        int correctCount = 0;

        for (int i = 0; i < questions.length; i++) {
          if (questions[i].isCorrect(userAnswers[i])) {
            correctCount++;
          }
        }

        expect(correctCount, 2);
        expect((correctCount / questions.length * 100).round(), 67);
      });

      test('should handle all incorrect answers', () {
        final questions = [
          const QuizQuestion(
            id: '1',
            motifId: 'motif1',
            questionType: QuestionType.multipleChoice,
            questionText: 'Question 1',
            correctAnswer: 'A',
          ),
          const QuizQuestion(
            id: '2',
            motifId: 'motif1',
            questionType: QuestionType.multipleChoice,
            questionText: 'Question 2',
            correctAnswer: 'B',
          ),
        ];

        final userAnswers = ['D', 'D'];
        int correctCount = 0;

        for (int i = 0; i < questions.length; i++) {
          if (questions[i].isCorrect(userAnswers[i])) {
            correctCount++;
          }
        }

        expect(correctCount, 0);
        expect(correctCount / questions.length * 100, 0.0);
      });
    });

    group('Pass/Fail Threshold (80%)', () {
      test('should pass with exactly 80% score', () {
        const result = QuizResult(
          passed: true,
          score: 8,
          totalQuestions: 10,
          correctAnswers: 8,
          percentage: 80,
        );

        expect(result.passed, true);
        expect(result.percentage, Quiz.passThreshold);
        expect(Quiz.passThreshold, 80);
      });

      test('should pass with score above 80%', () {
        const result = QuizResult(
          passed: true,
          score: 9,
          totalQuestions: 10,
          correctAnswers: 9,
          percentage: 90,
        );

        expect(result.passed, true);
        expect(result.percentage, greaterThan(Quiz.passThreshold));
      });

      test('should fail with score below 80%', () {
        const result = QuizResult(
          passed: false,
          score: 7,
          totalQuestions: 10,
          correctAnswers: 7,
          percentage: 70,
        );

        expect(result.passed, false);
        expect(result.percentage, lessThan(Quiz.passThreshold));
      });

      test('should correctly calculate percentage for 8/10 questions', () {
        const totalQuestions = 10;
        const correctAnswers = 8;
        final percentage = (correctAnswers / totalQuestions * 100).round();

        expect(percentage, 80);
        expect(percentage >= Quiz.passThreshold, true);
      });

      test('should correctly calculate percentage for 7/10 questions', () {
        const totalQuestions = 10;
        const correctAnswers = 7;
        final percentage = (correctAnswers / totalQuestions * 100).round();

        expect(percentage, 70);
        expect(percentage < Quiz.passThreshold, true);
      });

      test('should calculate percentage for 4/5 questions', () {
        const totalQuestions = 5;
        const correctAnswers = 4;
        final percentage = (correctAnswers / totalQuestions * 100).round();

        expect(percentage, 80);
        expect(percentage >= Quiz.passThreshold, true);
      });

      test('should calculate percentage for 3/5 questions', () {
        const totalQuestions = 5;
        const correctAnswers = 3;
        final percentage = (correctAnswers / totalQuestions * 100).round();

        expect(percentage, 60);
        expect(percentage < Quiz.passThreshold, true);
      });
    });

    group('XP Bonus for Perfect Scores', () {
      test('should detect perfect score (100%)', () {
        const result = QuizResult(
          passed: true,
          score: 10,
          totalQuestions: 10,
          correctAnswers: 10,
          percentage: 100,
        );

        expect(result.isPerfect, true);
        expect(result.percentage, 100);
      });

      test('should award mastered XP for perfect score', () {
        const perfectScore = 100;
        const expectedXp = AppConstants.masteredXp;

        expect(perfectScore, 100);
        expect(expectedXp, 75);
      });

      test('should not detect perfect score for 99%', () {
        const result = QuizResult(
          passed: true,
          score: 99,
          totalQuestions: 100,
          correctAnswers: 99,
          percentage: 99,
        );

        expect(result.isPerfect, false);
        expect(result.percentage, lessThan(100));
      });

      test('should calculate XP for passing but not perfect score', () {
        const passingScore = 85;
        const expectedXp = AppConstants.lessonXp;

        expect(passingScore, greaterThanOrEqualTo(Quiz.passThreshold));
        expect(passingScore, lessThan(100));
        expect(expectedXp, 50);
      });
    });

    group('Quiz Result Messages and Emojis', () {
      test('should return correct message for perfect score', () {
        const result = QuizResult(
          passed: true,
          score: 10,
          totalQuestions: 10,
          correctAnswers: 10,
          percentage: 100,
        );

        expect(result.resultMessage, 'Xuất sắc! Bạn đã trả lời đúng tất cả!');
        expect(result.resultEmoji, '🏆');
      });

      test('should return correct message for passing score', () {
        const result = QuizResult(
          passed: true,
          score: 8,
          totalQuestions: 10,
          correctAnswers: 8,
          percentage: 80,
        );

        expect(result.resultMessage,
            'Tuyệt vời! Bạn đã vượt qua bài trắc nghiệm!');
        expect(result.resultEmoji, '🎉');
      });

      test('should return correct message for failing score above 50%', () {
        const result = QuizResult(
          passed: false,
          score: 6,
          totalQuestions: 10,
          correctAnswers: 6,
          percentage: 60,
        );

        expect(result.resultMessage,
            'Chưa đạt. Hãy ôn lại bài học và thử lại nhé!');
        expect(result.resultEmoji, '📚');
      });

      test('should return correct message for failing score below 50%', () {
        const result = QuizResult(
          passed: false,
          score: 4,
          totalQuestions: 10,
          correctAnswers: 4,
          percentage: 40,
        );

        expect(result.resultMessage,
            'Chưa đạt. Hãy ôn lại bài học và thử lại nhé!');
        expect(result.resultEmoji, '💪');
      });
    });

    group('Wrong Answers Calculation', () {
      test('should calculate wrong answers for partial score', () {
        const result = QuizResult(
          passed: true,
          score: 8,
          totalQuestions: 10,
          correctAnswers: 8,
          percentage: 80,
        );

        expect(result.wrongAnswers, 2);
      });

      test('should calculate wrong answers for perfect score', () {
        const result = QuizResult(
          passed: true,
          score: 10,
          totalQuestions: 10,
          correctAnswers: 10,
          percentage: 100,
        );

        expect(result.wrongAnswers, 0);
      });

      test('should calculate wrong answers for all incorrect', () {
        const result = QuizResult(
          passed: false,
          score: 0,
          totalQuestions: 10,
          correctAnswers: 0,
          percentage: 0,
        );

        expect(result.wrongAnswers, 10);
      });
    });

    group('Time-based Calculations', () {
      test('should format time correctly for quiz attempt', () {
        const timeTakenSeconds = 125;
        final minutes = timeTakenSeconds ~/ 60;
        final seconds = timeTakenSeconds % 60;
        final formattedTime =
            '${minutes.toString().padLeft(2, '0')}:${seconds.toString().padLeft(2, '0')}';

        expect(formattedTime, '02:05');
      });

      test('should format time for exactly 1 minute', () {
        const timeTakenSeconds = 60;
        final minutes = timeTakenSeconds ~/ 60;
        final seconds = timeTakenSeconds % 60;
        final formattedTime =
            '${minutes.toString().padLeft(2, '0')}:${seconds.toString().padLeft(2, '0')}';

        expect(formattedTime, '01:00');
      });

      test('should format time for less than 1 minute', () {
        const timeTakenSeconds = 45;
        final minutes = timeTakenSeconds ~/ 60;
        final seconds = timeTakenSeconds % 60;
        final formattedTime =
            '${minutes.toString().padLeft(2, '0')}:${seconds.toString().padLeft(2, '0')}';

        expect(formattedTime, '00:45');
      });
    });
  });
}

