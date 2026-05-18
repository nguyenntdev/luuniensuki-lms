import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/constants/api_constants.dart';
import '../../../core/network/api_client.dart';

class AiChatService {
  final ApiClient _apiClient;

  AiChatService(this._apiClient);

  Future<Map<String, dynamic>> tutor({
    required String message,
    List<Map<String, String>> history = const [],
    Map<String, dynamic>? context,
    String? level,
  }) {
    return _apiClient.post<Map<String, dynamic>>(
      ApiConstants.aiTutor,
      data: {
        'message': message,
        'history': history,
        'context': context,
        'level': level,
      },
      parser: (json) => Map<String, dynamic>.from(json as Map),
    );
  }

  Future<Map<String, dynamic>> qa({
    required String question,
    Map<String, dynamic>? context,
    int limit = 6,
  }) {
    return _apiClient.post<Map<String, dynamic>>(
      ApiConstants.aiQa,
      data: {
        'question': question,
        'context': context,
        'limit': limit,
      },
      parser: (json) => Map<String, dynamic>.from(json as Map),
    );
  }

  Future<Map<String, dynamic>> summary({
    String? motifId,
    String? urnSlug,
    String? level,
  }) {
    return _apiClient.post<Map<String, dynamic>>(
      ApiConstants.aiSummary,
      data: {
        'motif_id': motifId,
        'urn_slug': urnSlug,
        'level': level,
      },
      parser: (json) => Map<String, dynamic>.from(json as Map),
    );
  }

  Future<Map<String, dynamic>> flashcards({
    String? topic,
    String? motifId,
    int count = 8,
    String? level,
  }) {
    return _apiClient.post<Map<String, dynamic>>(
      ApiConstants.aiFlashcards,
      data: {
        'topic': topic,
        'motif_id': motifId,
        'count': count,
        'level': level,
      },
      parser: (json) => Map<String, dynamic>.from(json as Map),
    );
  }

  Future<Map<String, dynamic>> explain({
    required String text,
    required String level,
  }) {
    return _apiClient.post<Map<String, dynamic>>(
      ApiConstants.aiExplain,
      data: {
        'text': text,
        'level': level,
      },
      parser: (json) => Map<String, dynamic>.from(json as Map),
    );
  }

  Future<Map<String, dynamic>> coach({
    String? goal,
    int? availabilityMinutesPerDay,
    int? daysPerWeek,
  }) {
    return _apiClient.post<Map<String, dynamic>>(
      ApiConstants.aiCoach,
      data: {
        'goal': goal,
        'availability_minutes_per_day': availabilityMinutesPerDay,
        'days_per_week': daysPerWeek,
      },
      parser: (json) => Map<String, dynamic>.from(json as Map),
    );
  }

  Future<Map<String, dynamic>> feedback({
    required String question,
    required String correctAnswer,
    required String userAnswer,
    Map<String, dynamic>? context,
  }) {
    return _apiClient.post<Map<String, dynamic>>(
      ApiConstants.aiFeedback,
      data: {
        'question': question,
        'correct_answer': correctAnswer,
        'user_answer': userAnswer,
        'context': context,
      },
      parser: (json) => Map<String, dynamic>.from(json as Map),
    );
  }

  Future<Map<String, dynamic>> reviewPlan() {
    return _apiClient.get<Map<String, dynamic>>(
      ApiConstants.aiReviewPlan,
      parser: (json) => Map<String, dynamic>.from(json as Map),
    );
  }

  Future<Map<String, dynamic>> diagnostic({
    String? urnId,
    String? urnSlug,
    int count = 6,
    String? level,
  }) {
    return _apiClient.post<Map<String, dynamic>>(
      ApiConstants.aiDiagnostic,
      data: {
        'urn_id': urnId,
        'urn_slug': urnSlug,
        'count': count,
        'level': level,
      },
      parser: (json) => Map<String, dynamic>.from(json as Map),
    );
  }
}

final aiChatServiceProvider = Provider<AiChatService>((ref) {
  final apiClient = ref.watch(apiClientProvider);
  return AiChatService(apiClient);
});
