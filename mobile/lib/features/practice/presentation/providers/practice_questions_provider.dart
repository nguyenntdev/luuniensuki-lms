import 'dart:math';

import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../../core/constants/api_constants.dart';
import '../../../../core/network/api_client.dart';
import '../../../collection/data/models/collection_dtos.dart';
import '../../../urn_viewer/data/models/urn_dtos.dart';
import '../../domain/models/quiz_question.dart';

final practiceQuestionsProvider =
    FutureProvider.autoDispose<List<QuizQuestion>>((ref) async {
  final apiClient = ref.read(apiClientProvider);

  final collectionResponse = await apiClient.get<Map<String, dynamic>>(
    ApiConstants.userCollection,
    parser: (json) => json as Map<String, dynamic>,
  );
  final collection = CollectionResponseDto.fromJson(collectionResponse);

  final selectedMotifs = _selectMotifs(collection.items);
  if (selectedMotifs.isEmpty) {
    return [];
  }

  final quizzes = await Future.wait(
    selectedMotifs.map(
      (motifId) => apiClient
          .get<QuizResponseDto>(
            '/api/v1/motifs/$motifId/quiz',
            parser: (json) =>
                QuizResponseDto.fromJson(json as Map<String, dynamic>),
          )
          .catchError((_) => null),
    ),
  );

  final questions = <QuizQuestion>[];
  for (final quiz in quizzes) {
    if (quiz == null) continue;
    questions.addAll(_mapQuizQuestions(quiz.questions));
  }

  questions.shuffle(Random());
  return questions.take(10).toList();
});

List<String> _selectMotifs(List<CollectionMotifDto> items) {
  final learned = items.where((m) => m.status == 'learned').toList();
  final discovered = items.where((m) => m.status == 'discovered').toList();
  final mastered = items.where((m) => m.status == 'mastered').toList();

  final selected = <String>{};
  for (final item in learned.take(2)) {
    selected.add(item.id);
  }
  for (final item in discovered.take(1)) {
    selected.add(item.id);
  }
  if (selected.isEmpty) {
    for (final item in mastered.take(2)) {
      selected.add(item.id);
    }
  }
  if (selected.isEmpty) {
    for (final item in items.take(2)) {
      selected.add(item.id);
    }
  }

  return selected.toList();
}

List<QuizQuestion> _mapQuizQuestions(List<QuizQuestionDto> questions) {
  final result = <QuizQuestion>[];
  for (final question in questions) {
    final mapped = _mapQuizQuestion(question);
    if (mapped != null) {
      result.add(mapped);
    }
  }
  return result;
}

QuizQuestion? _mapQuizQuestion(QuizQuestionDto question) {
  final type = _mapQuizType(question.questionType);
  final normalized = _normalizeAnswer(type, question.correctAnswer);
  final options = _normalizeOptions(type, question.options, normalized);

  if (options.isEmpty) {
    return null;
  }

  return QuizQuestion(
    id: question.id,
    type: type,
    motifId: question.motifId,
    question: question.questionText,
    options: options,
    correctAnswer: normalized,
    imageUrl: question.imageUrl,
    explanation: question.explanation,
    points: 10,
  );
}

QuizType _mapQuizType(String rawType) {
  switch (rawType.toLowerCase()) {
    case 'true_false':
      return QuizType.trueFalse;
    case 'image_select':
      return QuizType.imageMatching;
    case 'mesh_location':
      return QuizType.multipleChoice;
    case 'multiple_choice':
    default:
      return QuizType.multipleChoice;
  }
}

String _normalizeAnswer(QuizType type, String answer) {
  final normalized = answer.trim().toLowerCase();
  if (type == QuizType.trueFalse) {
    if (normalized == 'true' || normalized == 'đúng' || normalized == 'dung') {
      return 'Đúng';
    }
    if (normalized == 'false' || normalized == 'sai') {
      return 'Sai';
    }
  }
  return answer.trim();
}

List<String> _normalizeOptions(
  QuizType type,
  List<String> options,
  String correctAnswer,
) {
  if (type == QuizType.trueFalse) {
    return const ['Đúng', 'Sai'];
  }

  if (options.isEmpty) {
    return correctAnswer.isNotEmpty ? [correctAnswer] : [];
  }

  final normalized = options.map((o) => o.trim()).where((o) => o.isNotEmpty);
  return normalized.toList();
}
