import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../domain/models/quiz_question.dart';

// Quiz Session State
class QuizSessionState {
  final List<QuizQuestion> questions;
  final int currentQuestionIndex;
  final int totalScore;
  final List<String> answeredQuestions;
  final Map<String, bool> answerResults; // questionId -> isCorrect

  QuizSessionState({
    required this.questions,
    this.currentQuestionIndex = 0,
    this.totalScore = 0,
    this.answeredQuestions = const [],
    this.answerResults = const {},
  });

  QuizSessionState copyWith({
    List<QuizQuestion>? questions,
    int? currentQuestionIndex,
    int? totalScore,
    List<String>? answeredQuestions,
    Map<String, bool>? answerResults,
  }) {
    return QuizSessionState(
      questions: questions ?? this.questions,
      currentQuestionIndex: currentQuestionIndex ?? this.currentQuestionIndex,
      totalScore: totalScore ?? this.totalScore,
      answeredQuestions: answeredQuestions ?? this.answeredQuestions,
      answerResults: answerResults ?? this.answerResults,
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

  // Start a new quiz session
  void startQuiz(List<QuizQuestion> questions) {
    state = QuizSessionState(questions: questions);
  }

  // Start quiz with specific type
  void startQuizByType(QuizType type) {
    final questions = MockQuizData.getQuestionsByType(type);
    startQuiz(questions);
  }

  // Start quiz with all types mixed
  void startMixedQuiz() {
    final questions = List<QuizQuestion>.from(MockQuizData.mockQuestions)
      ..shuffle();
    startQuiz(questions);
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

