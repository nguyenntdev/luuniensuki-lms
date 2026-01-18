import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:riverpod_annotation/riverpod_annotation.dart';
import '../../domain/models/quiz_question.dart';
import '../../domain/models/review_item.dart';
import '../../domain/services/spaced_repetition_service.dart';

part 'practice_provider.g.dart';

/// State for practice session
class PracticeSessionState {
  final List<QuizQuestion> questions;
  final int currentQuestionIndex;
  final int totalXp;
  final int hearts;
  final List<bool> answerResults; // true = correct, false = incorrect
  final bool isCompleted;
  final DateTime sessionStartTime;
  final Map<String, ReviewItem> reviewItems; // motifId -> ReviewItem

  const PracticeSessionState({
    required this.questions,
    this.currentQuestionIndex = 0,
    this.totalXp = 0,
    this.hearts = 5,
    this.answerResults = const [],
    this.isCompleted = false,
    required this.sessionStartTime,
    this.reviewItems = const {},
  });

  PracticeSessionState copyWith({
    List<QuizQuestion>? questions,
    int? currentQuestionIndex,
    int? totalXp,
    int? hearts,
    List<bool>? answerResults,
    bool? isCompleted,
    DateTime? sessionStartTime,
    Map<String, ReviewItem>? reviewItems,
  }) {
    return PracticeSessionState(
      questions: questions ?? this.questions,
      currentQuestionIndex: currentQuestionIndex ?? this.currentQuestionIndex,
      totalXp: totalXp ?? this.totalXp,
      hearts: hearts ?? this.hearts,
      answerResults: answerResults ?? this.answerResults,
      isCompleted: isCompleted ?? this.isCompleted,
      sessionStartTime: sessionStartTime ?? this.sessionStartTime,
      reviewItems: reviewItems ?? this.reviewItems,
    );
  }

  QuizQuestion? get currentQuestion =>
      currentQuestionIndex < questions.length
          ? questions[currentQuestionIndex]
          : null;

  int get correctAnswers => answerResults.where((r) => r).length;
  int get incorrectAnswers => answerResults.where((r) => !r).length;
  double get accuracy =>
      answerResults.isEmpty ? 0.0 : correctAnswers / answerResults.length;
  
  Duration get sessionDuration => DateTime.now().difference(sessionStartTime);
  bool get hasHearts => hearts > 0;
}

/// Practice session notifier
@riverpod
class PracticeSession extends _$PracticeSession {
  final _spacedRepetitionService = SpacedRepetitionService();

  @override
  PracticeSessionState build() {
    return PracticeSessionState(
      questions: [],
      sessionStartTime: DateTime.now(),
    );
  }

  /// Start a new practice session with questions
  void startSession(List<QuizQuestion> questions, {int initialHearts = 5}) {
    state = PracticeSessionState(
      questions: questions,
      sessionStartTime: DateTime.now(),
      hearts: initialHearts,
    );
  }

  /// Start quick review session with due items
  void startQuickReview(List<ReviewItem> dueItems) {
    final questions = _generateQuestionsFromReviewItems(dueItems);
    final reviewItemsMap = {for (var item in dueItems) item.motifId: item};
    
    state = PracticeSessionState(
      questions: questions,
      sessionStartTime: DateTime.now(),
      reviewItems: reviewItemsMap,
    );
  }

  /// Answer current question
  void answerQuestion(String answer, {required bool isCorrect}) {
    final currentQuestion = state.currentQuestion;
    if (currentQuestion == null) return;

    // Update XP
    final xpGained = isCorrect ? currentQuestion.points : 0;
    final newXp = state.totalXp + xpGained;

    // Update hearts (lose heart on incorrect answer)
    final newHearts = isCorrect ? state.hearts : (state.hearts - 1);

    // Update answer results
    final newAnswerResults = [...state.answerResults, isCorrect];

    // Update review item if this is a review session
    Map<String, ReviewItem>? updatedReviewItems;
    if (state.reviewItems.containsKey(currentQuestion.motifId)) {
      final reviewItem = state.reviewItems[currentQuestion.motifId]!;
      final quality = isCorrect ? 5 : 2; // Perfect recall or incorrect
      final updatedItem = _spacedRepetitionService.processReview(reviewItem, quality);
      updatedReviewItems = {...state.reviewItems, currentQuestion.motifId: updatedItem};
    }

    state = state.copyWith(
      totalXp: newXp,
      hearts: newHearts,
      answerResults: newAnswerResults,
      reviewItems: updatedReviewItems,
    );
  }

  /// Move to next question
  void nextQuestion() {
    if (state.currentQuestionIndex < state.questions.length - 1) {
      state = state.copyWith(
        currentQuestionIndex: state.currentQuestionIndex + 1,
      );
    } else {
      // Session completed
      state = state.copyWith(isCompleted: true);
    }
  }

  /// Generate quiz questions from review items
  List<QuizQuestion> _generateQuestionsFromReviewItems(List<ReviewItem> items) {
    // TODO: In production, fetch real questions from backend
    // For now, use mock data filtered by motif IDs
    return MockQuizData.mockQuestions.take(items.length.clamp(5, 10)).toList();
  }
}

/// Provider for daily practice stats
@riverpod
class DailyPracticeStats extends _$DailyPracticeStats {
  @override
  Map<String, int> build() {
    // TODO: Load from storage or backend
    return {
      'xpEarned': 145,
      'streak': 7,
      'hearts': 5,
      'questionsAnswered': 23,
    };
  }

  void updateXp(int xp) {
    state = {...state, 'xpEarned': (state['xpEarned'] ?? 0) + xp};
  }
}

