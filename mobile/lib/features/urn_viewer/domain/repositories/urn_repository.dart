import 'package:dartz/dartz.dart';

import '../../../../core/errors/failures.dart';
import '../entities/urn.dart';

/// Abstract interface for urn and motif operations.
abstract class UrnRepository {
  /// Get list of all urns with progress summary.
  Future<Either<Failure, List<Urn>>> getUrns();

  /// Get urn detail with all motifs.
  Future<Either<Failure, UrnDetail>> getUrnDetail(String slug);

  /// Get a specific motif by ID.
  Future<Either<Failure, Motif>> getMotif(String motifId);

  /// Unlock/discover a motif.
  Future<Either<Failure, UnlockResult>> unlockMotif(String motifId);

  /// Complete lesson for a motif.
  Future<Either<Failure, UnlockResult>> completeLesson(String motifId);

  /// Get quiz questions for a motif.
  Future<Either<Failure, List<QuizQuestion>>> getQuizQuestions(String motifId);

  /// Submit quiz answers and get result.
  Future<Either<Failure, QuizResult>> submitQuiz({
    required String motifId,
    required List<QuizAnswer> answers,
    int? timeTakenSeconds,
  });

  /// Get user's progress for a specific motif.
  Future<Either<Failure, MotifProgress?>> getMotifProgress(String motifId);

  /// Get all user progress (for collection screen).
  Future<Either<Failure, Map<String, MotifProgress>>> getAllProgress();
}

/// Quiz question entity
class QuizQuestion {
  final String id;
  final String motifId;
  final QuestionType type;
  final String questionText;
  final String correctAnswer;
  final List<String> options;
  final String? imageUrl;
  final String? explanation;
  final int displayOrder;

  const QuizQuestion({
    required this.id,
    required this.motifId,
    required this.type,
    required this.questionText,
    required this.correctAnswer,
    this.options = const [],
    this.imageUrl,
    this.explanation,
    this.displayOrder = 0,
  });
}

/// Question type enum
enum QuestionType {
  multipleChoice('multiple_choice'),
  trueFalse('true_false'),
  fillBlank('fill_blank'),
  matching('matching');

  final String value;

  const QuestionType(this.value);

  static QuestionType fromString(String value) {
    return QuestionType.values.firstWhere(
      (t) => t.value == value || t.name == value,
      orElse: () => QuestionType.multipleChoice,
    );
  }
}

/// Quiz answer entity
class QuizAnswer {
  final String questionId;
  final String answer;

  const QuizAnswer({
    required this.questionId,
    required this.answer,
  });

  Map<String, dynamic> toJson() => {
        'question_id': questionId,
        'answer': answer,
      };
}

/// Quiz result entity
class QuizResult {
  final bool passed;
  final int score;
  final int totalQuestions;
  final int correctAnswers;
  final int percentage;
  final int xpEarned;
  final int totalXp;
  final List<String> newBadges;
  final bool isNewBest;
  final MotifProgress? progress;

  const QuizResult({
    required this.passed,
    required this.score,
    required this.totalQuestions,
    required this.correctAnswers,
    required this.percentage,
    this.xpEarned = 0,
    this.totalXp = 0,
    this.newBadges = const [],
    this.isNewBest = false,
    this.progress,
  });
}

/// Motif progress entity
class MotifProgress {
  final String id;
  final String motifId;
  final MotifStatus status;
  final DateTime? discoveredAt;
  final DateTime? learnedAt;
  final DateTime? masteredAt;
  final int xpEarned;
  final int? quizBestScore;

  const MotifProgress({
    required this.id,
    required this.motifId,
    required this.status,
    this.discoveredAt,
    this.learnedAt,
    this.masteredAt,
    this.xpEarned = 0,
    this.quizBestScore,
  });

  /// Check if motif has been discovered
  bool get isDiscovered => status != MotifStatus.hidden;

  /// Check if lesson is completed
  bool get isLearned =>
      status == MotifStatus.learned || status == MotifStatus.mastered;

  /// Check if quiz is passed
  bool get isMastered => status == MotifStatus.mastered;
}
