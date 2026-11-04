import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../domain/models/quiz_question.dart';

// Quiz Session State
class QuizSessionState {
  final List<QuizQuestion> questions;
  final int currentQuestionIndex;
  final int totalScore;
  final List<String> answeredQuestions;
  final Map<String, bool> answerResults; // questionId -> isCorrect
  final bool isServerVerified;
  final String? sessionId;
  final List<String> serverAwardedBadges;

  QuizSessionState({
    required this.questions,
    this.currentQuestionIndex = 0,
    this.totalScore = 0,
    this.answeredQuestions = const [],
    this.answerResults = const {},
    this.isServerVerified = false,
    this.sessionId,
    this.serverAwardedBadges = const [],
  });

  QuizSessionState copyWith({
    List<QuizQuestion>? questions,
    int? currentQuestionIndex,
    int? totalScore,
    List<String>? answeredQuestions,
    Map<String, bool>? answerResults,
    bool? isServerVerified,
    String? sessionId,
    List<String>? serverAwardedBadges,
  }) {
    return QuizSessionState(
      questions: questions ?? this.questions,
      currentQuestionIndex: currentQuestionIndex ?? this.currentQuestionIndex,
      totalScore: totalScore ?? this.totalScore,
      answeredQuestions: answeredQuestions ?? this.answeredQuestions,
      answerResults: answerResults ?? this.answerResults,
      isServerVerified: isServerVerified ?? this.isServerVerified,
      sessionId: sessionId ?? this.sessionId,
      serverAwardedBadges: serverAwardedBadges ?? this.serverAwardedBadges,
    );
  }

  bool get isCompleted => currentQuestionIndex >= questions.length;
  QuizQuestion? get currentQuestion => 
      currentQuestionIndex < questions.length 
          ? questions[currentQuestionIndex] 
          : null;
  int get correctAnswers => answerResults.values.where((v) => v).length;
  int get incorrectAnswers => answerResults.values.where((v) => !v).length;
  double get accuracy => 
      answeredQuestions.isEmpty 
          ? 0.0 
          : correctAnswers / answeredQuestions.length;
}

// Quiz Session Notifier
class QuizSessionNotifier extends StateNotifier<QuizSessionState> {
  QuizSessionNotifier() : super(QuizSessionState(questions: []));

  // Start a new quiz session with server-verified questions
  void startQuiz(List<QuizQuestion> questions, {bool isServerVerified = false, String? sessionId}) {
    state = QuizSessionState(
      questions: questions,
      isServerVerified: isServerVerified,
      sessionId: sessionId,
    );
  }

  // Start quiz with specific type (offline fallback; unverified for graded badges)
  void startQuizByType(QuizType type) {
    final questions = MockQuizData.getQuestionsByType(type);
    startQuiz(questions, isServerVerified: false);
  }

  // Start quiz with all types mixed (offline fallback; unverified for graded badges)
  void startMixedQuiz() {
    final questions = List<QuizQuestion>.from(MockQuizData.mockQuestions)
      ..shuffle();
    startQuiz(questions, isServerVerified: false);
  }

  // Answer current question
  void answerQuestion(String answer) {
    final currentQuestion = state.currentQuestion;
    if (currentQuestion == null) return;

    final isCorrect = answer == currentQuestion.correctAnswer;
    final newScore = isCorrect 
        ? state.totalScore + currentQuestion.points 
        : state.totalScore;

    final newAnsweredQuestions = [
      ...state.answeredQuestions,
      currentQuestion.id,
    ];

    final newAnswerResults = {
      ...state.answerResults,
      currentQuestion.id: isCorrect,
    };

    state = state.copyWith(
      totalScore: newScore,
      answeredQuestions: newAnsweredQuestions,
      answerResults: newAnswerResults,
    );
  }

  // Move to next question
  void nextQuestion() {
    if (state.currentQuestionIndex < state.questions.length) {
      state = state.copyWith(
        currentQuestionIndex: state.currentQuestionIndex + 1,
      );
    }
  }

  // Update state with server-verified grading results and awarded badges
  void applyServerResults({
    required int score,
    required List<String> awardedBadges,
  }) {
    state = state.copyWith(
      totalScore: score,
      isServerVerified: true,
      serverAwardedBadges: awardedBadges,
    );
  }

  // Move to previous question
  void previousQuestion() {
    if (state.currentQuestionIndex > 0) {
      state = state.copyWith(
        currentQuestionIndex: state.currentQuestionIndex - 1,
      );
    }
  }

  // Reset quiz
  void reset() {
    state = QuizSessionState(questions: []);
  }

  // Restart current quiz
  void restart() {
    state = QuizSessionState(questions: state.questions);
  }
}

// Provider
final quizSessionProvider = 
    StateNotifierProvider<QuizSessionNotifier, QuizSessionState>((ref) {
  return QuizSessionNotifier();
});

// Computed providers
final currentQuestionProvider = Provider<QuizQuestion?>((ref) {
  return ref.watch(quizSessionProvider).currentQuestion;
});

final quizProgressProvider = Provider<double>((ref) {
  final session = ref.watch(quizSessionProvider);
  if (session.questions.isEmpty) return 0.0;
  return session.currentQuestionIndex / session.questions.length;
});

final quizStatsProvider = Provider<Map<String, dynamic>>((ref) {
  final session = ref.watch(quizSessionProvider);
  return {
    'total': session.questions.length,
    'answered': session.answeredQuestions.length,
    'correct': session.correctAnswers,
    'incorrect': session.incorrectAnswers,
    'score': session.totalScore,
    'accuracy': session.accuracy,
  };
});

