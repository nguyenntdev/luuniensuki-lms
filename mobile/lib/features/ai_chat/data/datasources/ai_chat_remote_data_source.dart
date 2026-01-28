import 'dart:async';
import 'dart:convert';

import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../../core/constants/api_constants.dart';
import '../../../../core/network/api_client.dart';

class AiChatStreamEvent {
  final String type;
  final String? content;
  final List<dynamic>? citations;
  final String? message;
  final String? jobId;

  AiChatStreamEvent({
    required this.type,
    this.content,
    this.citations,
    this.message,
    this.jobId,
  });

  factory AiChatStreamEvent.fromJson(Map<String, dynamic> json) {
    return AiChatStreamEvent(
      type: json['type'] as String,
      content: json['content'] as String?,
      citations: json['citations'] as List<dynamic>?,
      message: json['message'] as String?,
      jobId: json['job_id'] as String?,
    );
  }
}

class AiChatRemoteDataSource {
  final ApiClient _apiClient;
  final Dio _dio;

  AiChatRemoteDataSource(this._apiClient, this._dio);

  Stream<AiChatStreamEvent> streamTutorResponse({
    required String message,
    required List<Map<String, String>> history,
    Map<String, dynamic>? context,
    String? level,
  }) async* {
    final url = '${ApiConstants.baseUrl}/api/v1/ai/tutor/stream';
    
    final payload = {
      'message': message,
      'history': history,
      if (context != null) 'context': context,
      if (level != null) 'level': level,
    };

    try {
      final response = await _dio.post(
        url,
        data: payload,
        options: Options(
          headers: {
            'Accept': 'text/event-stream',
            'Cache-Control': 'no-cache',
          },
          responseType: ResponseType.stream,
        ),
      );

      final stream = response.data.stream as Stream<List<int>>;
      
      await for (final chunk in stream) {
        final lines = utf8.decode(chunk).split('\n');
        
        for (final line in lines) {
          if (line.isEmpty || !line.startsWith('data: ')) {
            continue;
          }
          
          final jsonStr = line.substring(6).trim();
          if (jsonStr.isEmpty) continue;
          
          try {
            final json = jsonDecode(jsonStr) as Map<String, dynamic>;
            yield AiChatStreamEvent.fromJson(json);
          } catch (e) {
            // Skip invalid JSON
            continue;
          }
        }
      }
    } catch (e) {
      rethrow;
    }
  }

  Future<Map<String, dynamic>> sendTutorMessage({
    required String message,
    required List<Map<String, String>> history,
    Map<String, dynamic>? context,
    String? level,
  }) async {
    return _apiClient.post<Map<String, dynamic>>(
      '/api/v1/ai/tutor',
      data: {
        'message': message,
        'history': history,
        if (context != null) 'context': context,
        if (level != null) 'level': level,
      },
      parser: (json) => json as Map<String, dynamic>,
    );
  }

  Future<Map<String, dynamic>> sendQaMessage({
    required String question,
    Map<String, dynamic>? context,
    int limit = 6,
  }) async {
    return _apiClient.post<Map<String, dynamic>>(
      '/api/v1/ai/qa',
      data: {
        'question': question,
        if (context != null) 'context': context,
        'limit': limit,
      },
      parser: (json) => json as Map<String, dynamic>,
    );
  }
}

final aiChatRemoteDataSourceProvider = Provider<AiChatRemoteDataSource>((ref) {
  final apiClient = ref.watch(apiClientProvider);
  final dio = ref.watch(dioProvider);
  return AiChatRemoteDataSource(apiClient, dio);
});

