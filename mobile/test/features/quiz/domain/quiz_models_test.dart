import 'package:flutter_test/flutter_test.dart';
import 'package:luuniensuki_lms/features/quiz/domain/quiz_models.dart';

void main() {
  group('QuizQuestion', () {
    test('isCorrect returns true for exact match', () {
      const question = QuizQuestion(
        id: '1',
        motifId: 'motif1',
        questionType: QuestionType.multipleChoice,
        questionText: 'What is 2+2?',
        correctAnswer: '4',
      );

      expect(question.isCorrect('4'), true);
    });

    test('isCorrect returns true for matching answer (case-insensitive)', () {
      const question = QuizQuestion(
        id: '1',
        motifId: 'motif1',
        questionType: QuestionType.fillBlank,
        questionText: 'Capital of Vietnam?',
        correctAnswer: 'Hanoi',
      );

      expect(question.isCorrect('hanoi'), true);
      expect(question.isCorrect('HANOI'), true);
      expect(question.isCorrect('HaNoi'), true);
      expect(question.isCorrect('Hanoi'), true);
    });

    test('isCorrect returns true after trimming whitespace', () {
      const question = QuizQuestion(
        id: '1',
        motifId: 'motif1',
        questionType: QuestionType.fillBlank,
        questionText: 'Enter the word',
        correctAnswer: 'hello',
      );

      expect(question.isCorrect('  hello  '), true);
      expect(question.isCorrect('hello   '), true);
      expect(question.isCorrect('   hello'), true);
      expect(question.isCorrect('\thello\n'), true);
    });

    test('isCorrect handles case-insensitive and whitespace together', () {
      const question = QuizQuestion(
        id: '1',
        motifId: 'motif1',
        questionType: QuestionType.fillBlank,
        questionText: 'Name',
        correctAnswer: 'VietNam',
      );

      expect(question.isCorrect('  vietnam  '), true);
      expect(question.isCorrect('VIETNAM   '), true);
      expect(question.isCorrect('   VietNam'), true);
    });

    test('isCorrect returns false for incorrect answer', () {
      const question = QuizQuestion(
        id: '1',
        motifId: 'motif1',
        questionType: QuestionType.multipleChoice,
        questionText: 'What is 2+2?',
        correctAnswer: '4',
      );

      expect(question.isCorrect('5'), false);
      expect(question.isCorrect('three'), false);
      expect(question.isCorrect(''), false);
    });

    test('hasImage returns true when imageUrl is not empty', () {
      const question = QuizQuestion(
        id: '1',
        motifId: 'motif1',
        questionType: QuestionType.multipleChoice,
        questionText: 'Question',
        correctAnswer: 'Answer',
        imageUrl: 'https://example.com/image.jpg',
      );

      expect(question.hasImage, true);
    });

    test('hasImage returns false when imageUrl is null or empty', () {
      const question1 = QuizQuestion(
        id: '1',
        motifId: 'motif1',
        questionType: QuestionType.multipleChoice,
        questionText: 'Question',
        correctAnswer: 'Answer',
      );

      const question2 = QuizQuestion(
        id: '2',
        motifId: 'motif1',
        questionType: QuestionType.multipleChoice,
        questionText: 'Question',
        correctAnswer: 'Answer',
        imageUrl: '',
      );

      expect(question1.hasImage, false);
      expect(question2.hasImage, false);
    });

    test('hasExplanation returns true when explanation is not empty', () {
      const question = QuizQuestion(
        id: '1',
        motifId: 'motif1',
        questionType: QuestionType.multipleChoice,
        questionText: 'Question',
        correctAnswer: 'Answer',
        explanation: 'This is why...',
      );

      expect(question.hasExplanation, true);
    });

    test('hasExplanation returns false when explanation is null or empty', () {
      const question1 = QuizQuestion(
        id: '1',
        motifId: 'motif1',
        questionType: QuestionType.multipleChoice,
        questionText: 'Question',
        correctAnswer: 'Answer',
      );

      const question2 = QuizQuestion(
        id: '2',
        motifId: 'motif1',
        questionType: QuestionType.multipleChoice,
        questionText: 'Question',
        correctAnswer: 'Answer',
        explanation: '',
      );

      expect(question1.hasExplanation, false);
      expect(question2.hasExplanation, false);
    });
  });

  group('QuestionType.fromString', () {
    test('parses snake_case format correctly', () {
      expect(QuestionType.fromString('multiple_choice'), QuestionType.multipleChoice);
      expect(QuestionType.fromString('true_false'), QuestionType.trueFalse);
      expect(QuestionType.fromString('fill_blank'), QuestionType.fillBlank);
      expect(QuestionType.fromString('matching'), QuestionType.matching);
    });

    test('parses camelCase format correctly', () {
      expect(QuestionType.fromString('multipleChoice'), QuestionType.multipleChoice);
      expect(QuestionType.fromString('trueFalse'), QuestionType.trueFalse);
      expect(QuestionType.fromString('fillBlank'), QuestionType.fillBlank);
    });

    test('parses kebab-case format correctly', () {
      expect(QuestionType.fromString('multiple-choice'), QuestionType.multipleChoice);
      expect(QuestionType.fromString('true-false'), QuestionType.trueFalse);
      expect(QuestionType.fromString('fill-blank'), QuestionType.fillBlank);
    });

    test('parses uppercase formats correctly', () {
      expect(QuestionType.fromString('MULTIPLE_CHOICE'), QuestionType.multipleChoice);
      expect(QuestionType.fromString('TRUE_FALSE'), QuestionType.trueFalse);
      expect(QuestionType.fromString('FILL_BLANK'), QuestionType.fillBlank);
      expect(QuestionType.fromString('MATCHING'), QuestionType.matching);
    });

    test('parses alternate fill-blank formats', () {
      expect(QuestionType.fromString('fill_in_blank'), QuestionType.fillBlank);
      expect(QuestionType.fromString('fillInBlank'), QuestionType.fillBlank);
      expect(QuestionType.fromString('fill-in-blank'), QuestionType.fillBlank);
    });

    test('returns multipleChoice as default for unknown types', () {
      expect(QuestionType.fromString('unknown'), QuestionType.multipleChoice);
      expect(QuestionType.fromString('random'), QuestionType.multipleChoice);
      expect(QuestionType.fromString(''), QuestionType.multipleChoice);
    });

    test('displayName returns Vietnamese labels', () {
      expect(QuestionType.multipleChoice.displayName, 'Trắc nghiệm');
      expect(QuestionType.trueFalse.displayName, 'Đúng/Sai');
      expect(QuestionType.fillBlank.displayName, 'Điền vào chỗ trống');
      expect(QuestionType.matching.displayName, 'Nối cặp');
    });
  });

  group('Quiz', () {
    test('totalQuestions returns correct count', () {
      const quiz = Quiz(
        motifId: 'motif1',
        motifName: 'Test Motif',
        questions: [
          QuizQuestion(
            id: '1',
            motifId: 'motif1',
            questionType: QuestionType.multipleChoice,
            questionText: 'Q1',
            correctAnswer: 'A1',
          ),
          QuizQuestion(
            id: '2',
            motifId: 'motif1',
            questionType: QuestionType.trueFalse,
            questionText: 'Q2',
            correctAnswer: 'True',
          ),
        ],
      );

      expect(quiz.totalQuestions, 2);
    });

    test('hasQuestions returns true when questions exist', () {
      const quiz = Quiz(
        motifId: 'motif1',
        motifName: 'Test Motif',
        questions: [
          QuizQuestion(
            id: '1',
            motifId: 'motif1',
            questionType: QuestionType.multipleChoice,
            questionText: 'Q1',
            correctAnswer: 'A1',
          ),
        ],
      );

      expect(quiz.hasQuestions, true);
    });

    test('hasQuestions returns false when no questions', () {
      const quiz = Quiz(
        motifId: 'motif1',
        motifName: 'Test Motif',
        questions: [],
      );

      expect(quiz.hasQuestions, false);
    });

    test('passThreshold is 80 percent', () {
      expect(Quiz.passThreshold, 80);
    });
  });

  group('QuizResult', () {
    test('wrongAnswers calculation is correct', () {
      const result = QuizResult(
        passed: true,
        score: 8,
        totalQuestions: 10,
        correctAnswers: 8,
        percentage: 80,
      );

      expect(result.wrongAnswers, 2);
    });

    test('wrongAnswers returns 0 for perfect score', () {
      const result = QuizResult(
        passed: true,
        score: 10,
        totalQuestions: 10,
        correctAnswers: 10,
        percentage: 100,
      );

      expect(result.wrongAnswers, 0);
    });

    test('isPerfect returns true when percentage is 100', () {
      const result = QuizResult(
        passed: true,
        score: 10,
        totalQuestions: 10,
        correctAnswers: 10,
        percentage: 100,
      );

      expect(result.isPerfect, true);
    });

    test('isPerfect returns false when percentage is less than 100', () {
      const result = QuizResult(
        passed: true,
        score: 9,
        totalQuestions: 10,
        correctAnswers: 9,
        percentage: 90,
      );

      expect(result.isPerfect, false);
    });

    test('resultMessage for perfect score', () {
      const result = QuizResult(
        passed: true,
        score: 10,
        totalQuestions: 10,
        correctAnswers: 10,
        percentage: 100,
      );

      expect(result.resultMessage, 'Xuất sắc! Bạn đã trả lời đúng tất cả!');
    });

    test('resultMessage for passed score', () {
      const result = QuizResult(
        passed: true,
        score: 8,
        totalQuestions: 10,
        correctAnswers: 8,
        percentage: 80,
      );

      expect(result.resultMessage, 'Tuyệt vời! Bạn đã vượt qua bài trắc nghiệm!');
    });

    test('resultMessage for failed score', () {
      const result = QuizResult(
        passed: false,
        score: 6,
        totalQuestions: 10,
        correctAnswers: 6,
        percentage: 60,
      );

      expect(result.resultMessage, 'Chưa đạt. Hãy ôn lại bài học và thử lại nhé!');
    });

    test('resultEmoji for perfect score', () {
      const result = QuizResult(
        passed: true,
        score: 10,
        totalQuestions: 10,
        correctAnswers: 10,
        percentage: 100,
      );

      expect(result.resultEmoji, '🏆');
    });

    test('resultEmoji for passed score (not perfect)', () {
      const result = QuizResult(
        passed: true,
        score: 8,
        totalQuestions: 10,
        correctAnswers: 8,
        percentage: 80,
      );

      expect(result.resultEmoji, '🎉');
    });

    test('resultEmoji for score >= 50% but failed', () {
      const result = QuizResult(
        passed: false,
        score: 6,
        totalQuestions: 10,
        correctAnswers: 6,
        percentage: 60,
      );

      expect(result.resultEmoji, '📚');
    });

    test('resultEmoji for score < 50%', () {
      const result = QuizResult(
        passed: false,
        score: 3,
        totalQuestions: 10,
        correctAnswers: 3,
        percentage: 30,
      );

      expect(result.resultEmoji, '💪');
    });

    test('pass validation with 80% threshold', () {
      const passing = QuizResult(
        passed: true,
        score: 8,
        totalQuestions: 10,
        correctAnswers: 8,
        percentage: 80,
      );

      const failing = QuizResult(
        passed: false,
        score: 7,
        totalQuestions: 10,
        correctAnswers: 7,
        percentage: 70,
      );

      expect(passing.passed, true);
      expect(passing.percentage >= Quiz.passThreshold, true);
      expect(failing.passed, false);
      expect(failing.percentage < Quiz.passThreshold, true);
    });

    test('xpEarned and badges are included in result', () {
      const result = QuizResult(
        passed: true,
        score: 10,
        totalQuestions: 10,
        correctAnswers: 10,
        percentage: 100,
        xpEarned: 50,
        totalXp: 250,
        newBadges: [
          QuizBadge(
            id: 'badge1',
            slug: 'perfect-score',
            name: 'Perfect Score',
            category: 'quiz',
          ),
        ],
        isNewBest: true,
      );

      expect(result.xpEarned, 50);
      expect(result.totalXp, 250);
      expect(result.newBadges.length, 1);
      expect(result.isNewBest, true);
    });
  });

  group('QuizAttempt', () {
    test('formattedTime returns correct mm:ss format', () {
      final attempt = QuizAttempt(
        id: '1',
        motifId: 'motif1',
        score: 80,
        percentage: 80,
        passed: true,
        attemptedAt: DateTime.now(),
        timeTakenSeconds: 125,
      );

      expect(attempt.formattedTime, '02:05');
    });

    test('formattedTime handles zero padding correctly', () {
      final attempt = QuizAttempt(
        id: '1',
        motifId: 'motif1',
        score: 80,
        percentage: 80,
        passed: true,
        attemptedAt: DateTime.now(),
        timeTakenSeconds: 65,
      );

      expect(attempt.formattedTime, '01:05');
    });

    test('formattedTime returns null when timeTakenSeconds is null', () {
      final attempt = QuizAttempt(
        id: '1',
        motifId: 'motif1',
        score: 80,
        percentage: 80,
        passed: true,
        attemptedAt: DateTime.now(),
      );

      expect(attempt.formattedTime, null);
    });
  });
}


