import 'package:riverpod_annotation/riverpod_annotation.dart';
import '../../../../core/constants/api_constants.dart';
import '../../../../core/network/api_client.dart';
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
  final String? sessionId;
  final Map<String, String> userAnswers; // questionId -> answer
  final bool isServerVerified;
  final List<String> verifiedBadges;
  final List<String> deniedBadges;
  final int? serverScore;
  final bool? serverPassed;

  const PracticeSessionState({
    required this.questions,
    this.currentQuestionIndex = 0,
    this.totalXp = 0,
    this.hearts = 5,
    this.answerResults = const [],
    this.isCompleted = false,
    required this.sessionStartTime,
    this.reviewItems = const {},
    this.sessionId,
    this.userAnswers = const {},
    this.isServerVerified = false,
    this.verifiedBadges = const [],
    this.deniedBadges = const [],
    this.serverScore,
    this.serverPassed,
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
    String? sessionId,
    Map<String, String>? userAnswers,
    bool? isServerVerified,
    List<String>? verifiedBadges,
    List<String>? deniedBadges,
    int? serverScore,
    bool? serverPassed,
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
      sessionId: sessionId ?? this.sessionId,
      userAnswers: userAnswers ?? this.userAnswers,
      isServerVerified: isServerVerified ?? this.isServerVerified,
      verifiedBadges: verifiedBadges ?? this.verifiedBadges,
      deniedBadges: deniedBadges ?? this.deniedBadges,
      serverScore: serverScore ?? this.serverScore,
      serverPassed: serverPassed ?? this.serverPassed,
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
  void startSession(List<QuizQuestion> questions, {int initialHearts = 5, String? sessionId}) {
    state = PracticeSessionState(
      questions: questions,
      sessionStartTime: DateTime.now(),
      hearts: initialHearts,
      sessionId: sessionId,
    );
  }

  /// Sync real published quiz questions from backend practice sync endpoint
  Future<void> syncQuestionsFromBackend({
    required ApiClient client,
    String? motifId,
    String? lessonId,
    String? category,
    String? mode,
    int limit = 10,
  }) async {
    final queryParams = <String, dynamic>{
      'limit': limit,
      if (mode != null) 'mode': mode,
      if (motifId != null) 'motif_id': motifId,
      if (lessonId != null) 'lesson_id': lessonId,
      if (category != null) 'category': category,
    };

    final response = await client.get<Map<String, dynamic>>(
      ApiConstants.practiceSync,
      queryParameters: queryParams,
      parser: (json) => json as Map<String, dynamic>,
    );

    final rawItems = (response['items'] as List<dynamic>?) ?? [];
    final questions = rawItems.map((item) {
      final map = item as Map<String, dynamic>;
      final typeStr = map['question_type'] as String? ?? 'multiple_choice';
      final optionsList = (map['options'] as List<dynamic>?)
              ?.map((o) => o.toString())
              .toList() ??
          <String>[];

      return QuizQuestion(
        id: map['id'] as String,
        type: _mapQuestionType(typeStr),
        motifId: (map['motif_id'] as String?) ?? (motifId ?? ''),
        question: map['question_text'] as String,
        options: optionsList,
        correctAnswer: '', // Intentionally not leaked to client
        points: (map['points'] as int?) ?? 10,
        explanation: map['explanation'] as String?,
        hint: map['hint'] as String?,
      );
    }).toList();

    state = PracticeSessionState(
      questions: questions,
      sessionStartTime: DateTime.now(),
      sessionId: response['session_id'] as String?,
    );
  }

  /// Submit practice answers to server for authoritative grading and badge awards
  Future<Map<String, dynamic>> submitSessionToServer({
    required ApiClient client,
    String? motifId,
    String? lessonId,
    int? timeTakenSeconds,
    List<String>? clientClaimedBadges,
  }) async {
    final payload = <String, dynamic>{
      if (state.sessionId != null) 'session_id': state.sessionId,
      if (motifId != null) 'motif_id': motifId,
      if (lessonId != null) 'lesson_id': lessonId,
      'answers': state.userAnswers,
      'time_taken_seconds': timeTakenSeconds ?? state.sessionDuration.inSeconds,
      if (clientClaimedBadges != null) 'client_claimed_badges': clientClaimedBadges,
    };

    final result = await client.post<Map<String, dynamic>>(
      ApiConstants.practiceSubmit,
      data: payload,
      parser: (json) => json as Map<String, dynamic>,
    );

    // Negative abuse invariant:
    // Only server-verified badges returned in 'awarded_badges' are accepted.
    final rawBadges = (result['awarded_badges'] as List<dynamic>?) ?? [];
    final awardedBadges = rawBadges
        .map((b) => (b as Map<String, dynamic>)['slug'] as String)
        .toList();
    final deniedBadges = (result['denied_badges'] as List<dynamic>?)
            ?.map((b) => b.toString())
            .toList() ??
        <String>[];

    state = state.copyWith(
      isCompleted: true,
      isServerVerified: true,
      verifiedBadges: awardedBadges,
      deniedBadges: deniedBadges,
      serverScore: result['score'] as int?,
      serverPassed: result['passed'] as bool?,
      totalXp: (result['total_xp'] as int?) ?? state.totalXp,
    );

    return result;
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
    final newUserAnswers = {
      ...state.userAnswers,
      currentQuestion.id: answer,
    };

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
      userAnswers: newUserAnswers,
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

  /// Helper to map question type strings to QuizType
  QuizType _mapQuestionType(String typeStr) {
    switch (typeStr) {
      case 'multiple_choice':
      case 'short_response':
        return QuizType.multipleChoice;
      case 'image_identification':
      case 'image_matching':
      case 'image_select':
        return QuizType.imageMatching;
      case 'true_false':
        return QuizType.trueFalse;
      case 'fill_in_blank':
        return QuizType.fillInBlank;
      default:
        return QuizType.multipleChoice;
    }
  }

  /// Generate quiz questions from review items.
  /// NOTE: Production runtime must synchronize questions from backend API.
  /// Mock questions are strictly prohibited for verified completion badges.
  List<QuizQuestion> _generateQuestionsFromReviewItems(List<ReviewItem> items) {
    // Negative abuse prevention:
    // Real review sessions must be initialized with syncQuestionsFromBackend.
    // Fallback MockQuizData is restricted to offline preview only and cannot award verified badges.
    return items.map((item) {
      return QuizQuestion(
        id: 'review_${item.motifId}',
        type: QuizType.multipleChoice,
        motifId: item.motifId,
        question: 'Ôn tập họa tiết ${item.motifId}',
        options: ['Lựa chọn A', 'Lựa chọn B', 'Lựa chọn C', 'Lựa chọn D'],
        correctAnswer: '',
        points: 10,
      );
    }).toList();
  }
}

/// Provider for daily practice stats
@riverpod
class DailyPracticeStats extends _$DailyPracticeStats {
  @override
  Map<String, int> build() {
    // Loaded from backend or initialized safely
    return {
      'xpEarned': 0,
      'streak': 0,
      'hearts': 5,
      'questionsAnswered': 0,
    };
  }

  void updateXp(int xp) {
    state = {...state, 'xpEarned': (state['xpEarned'] ?? 0) + xp};
  }
}


