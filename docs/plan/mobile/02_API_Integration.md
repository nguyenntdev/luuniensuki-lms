# 02_API_Integration.md — API Client & Integration Strategy

## Overview

This document details how the Flutter app integrates with the Luuniensuki LMS backend API at `https://lms.histolab.icu`.

## Base Configuration

### API Constants

```dart
// core/constants/api_constants.dart

class ApiConstants {
  static const String baseUrl = 'https://lms.histolab.icu';
  static const String apiVersion = 'v1';
  static const String apiPath = '/api/$apiVersion';
  
  // Timeouts
  static const Duration connectTimeout = Duration(seconds: 30);
  static const Duration receiveTimeout = Duration(seconds: 30);
  static const Duration sendTimeout = Duration(seconds: 30);
  
  // Endpoints - Auth
  static const String login = '$apiPath/auth/login';
  static const String register = '$apiPath/auth/register';
  static const String logout = '$apiPath/auth/logout';
  static const String refreshToken = '$apiPath/auth/refresh';
  static const String me = '$apiPath/auth/me';
  
  // Endpoints - Urns
  static const String urns = '$apiPath/urns';
  static String urn(String slug) => '$apiPath/urns/$slug';
  static String urnExam(String slug) => '$apiPath/urns/$slug/exam';
  static String urnExamSubmit(String slug) => '$apiPath/urns/$slug/exam/submit';
  
  // Endpoints - Motifs
  static String motif(String id) => '$apiPath/motifs/$id';
  static String motifLesson(String id) => '$apiPath/motifs/$id/lesson';
  static String motifQuiz(String id) => '$apiPath/motifs/$id/quiz';
  static String motifQuizSubmit(String id) => '$apiPath/motifs/$id/quiz/submit';
  
  // Endpoints - Progress
  static const String progressUnlock = '$apiPath/progress/unlock';
  static const String progressCompleteLesson = '$apiPath/progress/complete-lesson';
  
  // Endpoints - User
  static const String userDashboard = '$apiPath/users/me/dashboard';
  static const String userStats = '$apiPath/users/me/stats';
  static const String userBadges = '$apiPath/users/me/badges';
  static const String userProgress = '$apiPath/users/me/progress';
  static String userProfile(String userId) => '$apiPath/u/$userId';
  
  // Endpoints - Gamification
  static const String badges = '$apiPath/badges';
  static const String leaderboard = '$apiPath/leaderboard';
  static const String quests = '$apiPath/quests';
  static String quest(String slug) => '$apiPath/quests/$slug';
  
  // Endpoints - Recommendations
  static const String recommendations = '$apiPath/recommendations';
  
  // Endpoints - Certificates
  static String certificateVerify(String code) => '$apiPath/certificates/$code/verify';
}
```

## Dio Client Configuration

### Main API Client

```dart
// core/network/api_client.dart

import 'package:dio/dio.dart';

class ApiClient {
  final Dio _dio;
  
  ApiClient(this._dio);
  
  // GET request
  Future<Response<T>> get<T>(
    String path, {
    Map<String, dynamic>? queryParameters,
    Options? options,
    CancelToken? cancelToken,
  }) async {
    return _dio.get<T>(
      path,
      queryParameters: queryParameters,
      options: options,
      cancelToken: cancelToken,
    );
  }
  
  // POST request
  Future<Response<T>> post<T>(
    String path, {
    dynamic data,
    Map<String, dynamic>? queryParameters,
    Options? options,
    CancelToken? cancelToken,
  }) async {
    return _dio.post<T>(
      path,
      data: data,
      queryParameters: queryParameters,
      options: options,
      cancelToken: cancelToken,
    );
  }
  
  // PUT request
  Future<Response<T>> put<T>(
    String path, {
    dynamic data,
    Map<String, dynamic>? queryParameters,
    Options? options,
    CancelToken? cancelToken,
  }) async {
    return _dio.put<T>(
      path,
      data: data,
      queryParameters: queryParameters,
      options: options,
      cancelToken: cancelToken,
    );
  }
  
  // PATCH request
  Future<Response<T>> patch<T>(
    String path, {
    dynamic data,
    Map<String, dynamic>? queryParameters,
    Options? options,
    CancelToken? cancelToken,
  }) async {
    return _dio.patch<T>(
      path,
      data: data,
      queryParameters: queryParameters,
      options: options,
      cancelToken: cancelToken,
    );
  }
  
  // DELETE request
  Future<Response<T>> delete<T>(
    String path, {
    dynamic data,
    Map<String, dynamic>? queryParameters,
    Options? options,
    CancelToken? cancelToken,
  }) async {
    return _dio.delete<T>(
      path,
      data: data,
      queryParameters: queryParameters,
      options: options,
      cancelToken: cancelToken,
    );
  }
}
```

### Dio Provider

```dart
// core/network/dio_provider.dart

import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:riverpod_annotation/riverpod_annotation.dart';

part 'dio_provider.g.dart';

@riverpod
Dio dio(DioRef ref) {
  final dio = Dio(
    BaseOptions(
      baseUrl: ApiConstants.baseUrl,
      connectTimeout: ApiConstants.connectTimeout,
      receiveTimeout: ApiConstants.receiveTimeout,
      sendTimeout: ApiConstants.sendTimeout,
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
      },
    ),
  );
  
  // Add interceptors
  dio.interceptors.addAll([
    ref.watch(authInterceptorProvider),
    ref.watch(loggingInterceptorProvider),
    ref.watch(errorInterceptorProvider),
  ]);
  
  return dio;
}

@riverpod
ApiClient apiClient(ApiClientRef ref) {
  return ApiClient(ref.watch(dioProvider));
}
```

## Interceptors

### Auth Interceptor

```dart
// core/network/interceptors/auth_interceptor.dart

import 'package:dio/dio.dart';

class AuthInterceptor extends Interceptor {
  final SecureStorage _secureStorage;
  final Ref _ref;
  
  AuthInterceptor(this._secureStorage, this._ref);
  
  @override
  void onRequest(
    RequestOptions options,
    RequestInterceptorHandler handler,
  ) async {
    // Skip auth for public endpoints
    if (_isPublicEndpoint(options.path)) {
      return handler.next(options);
    }
    
    final accessToken = await _secureStorage.getAccessToken();
    if (accessToken != null) {
      options.headers['Authorization'] = 'Bearer $accessToken';
    }
    
    handler.next(options);
  }
  
  @override
  void onError(
    DioException err,
    ErrorInterceptorHandler handler,
  ) async {
    if (err.response?.statusCode == 401) {
      // Try to refresh token
      final refreshed = await _tryRefreshToken();
      if (refreshed) {
        // Retry the original request
        final response = await _retry(err.requestOptions);
        return handler.resolve(response);
      } else {
        // Logout user
        _ref.read(authNotifierProvider.notifier).logout();
      }
    }
    
    handler.next(err);
  }
  
  bool _isPublicEndpoint(String path) {
    const publicPaths = [
      '/api/v1/auth/login',
      '/api/v1/auth/register',
      '/api/v1/auth/refresh',
      '/health',
    ];
    return publicPaths.any((p) => path.contains(p));
  }
  
  Future<bool> _tryRefreshToken() async {
    try {
      final refreshToken = await _secureStorage.getRefreshToken();
      if (refreshToken == null) return false;
      
      final dio = Dio(BaseOptions(baseUrl: ApiConstants.baseUrl));
      final response = await dio.post(
        ApiConstants.refreshToken,
        options: Options(
          headers: {'Authorization': 'Bearer $refreshToken'},
        ),
      );
      
      if (response.statusCode == 200) {
        final newAccessToken = response.data['access_token'];
        final newRefreshToken = response.data['refresh_token'];
        
        await _secureStorage.saveAccessToken(newAccessToken);
        if (newRefreshToken != null) {
          await _secureStorage.saveRefreshToken(newRefreshToken);
        }
        
        return true;
      }
      return false;
    } catch (e) {
      return false;
    }
  }
  
  Future<Response> _retry(RequestOptions requestOptions) async {
    final accessToken = await _secureStorage.getAccessToken();
    
    final options = Options(
      method: requestOptions.method,
      headers: {
        ...requestOptions.headers,
        'Authorization': 'Bearer $accessToken',
      },
    );
    
    return Dio(BaseOptions(baseUrl: ApiConstants.baseUrl)).request(
      requestOptions.path,
      data: requestOptions.data,
      queryParameters: requestOptions.queryParameters,
      options: options,
    );
  }
}
```

### Logging Interceptor

```dart
// core/network/interceptors/logging_interceptor.dart

import 'dart:developer' as developer;
import 'package:dio/dio.dart';

class LoggingInterceptor extends Interceptor {
  @override
  void onRequest(RequestOptions options, RequestInterceptorHandler handler) {
    developer.log(
      '→ ${options.method} ${options.uri}',
      name: 'API',
    );
    if (options.data != null) {
      developer.log(
        'Body: ${options.data}',
        name: 'API',
      );
    }
    handler.next(options);
  }
  
  @override
  void onResponse(Response response, ResponseInterceptorHandler handler) {
    developer.log(
      '← ${response.statusCode} ${response.requestOptions.uri}',
      name: 'API',
    );
    handler.next(response);
  }
  
  @override
  void onError(DioException err, ErrorInterceptorHandler handler) {
    developer.log(
      '✖ ${err.response?.statusCode ?? 'NO_STATUS'} ${err.requestOptions.uri}',
      name: 'API',
      error: err.message,
    );
    handler.next(err);
  }
}
```

### Error Interceptor

```dart
// core/network/interceptors/error_interceptor.dart

import 'package:dio/dio.dart';

class ErrorInterceptor extends Interceptor {
  @override
  void onError(DioException err, ErrorInterceptorHandler handler) {
    final exception = _mapDioExceptionToServerException(err);
    handler.reject(
      DioException(
        requestOptions: err.requestOptions,
        error: exception,
        response: err.response,
        type: err.type,
      ),
    );
  }
  
  ServerException _mapDioExceptionToServerException(DioException err) {
    switch (err.type) {
      case DioExceptionType.connectionTimeout:
      case DioExceptionType.sendTimeout:
      case DioExceptionType.receiveTimeout:
        return ServerException(
          message: 'Connection timeout. Please try again.',
          code: 'TIMEOUT',
        );
        
      case DioExceptionType.connectionError:
        return ServerException(
          message: 'No internet connection.',
          code: 'NO_CONNECTION',
        );
        
      case DioExceptionType.badResponse:
        return _handleBadResponse(err.response);
        
      case DioExceptionType.cancel:
        return ServerException(
          message: 'Request was cancelled.',
          code: 'CANCELLED',
        );
        
      default:
        return ServerException(
          message: 'An unexpected error occurred.',
          code: 'UNKNOWN',
        );
    }
  }
  
  ServerException _handleBadResponse(Response? response) {
    if (response == null) {
      return ServerException(
        message: 'No response from server.',
        code: 'NO_RESPONSE',
      );
    }
    
    final data = response.data;
    
    // Handle our API error format
    if (data is Map<String, dynamic> && data.containsKey('error')) {
      final error = data['error'] as Map<String, dynamic>;
      return ServerException(
        message: error['message'] as String? ?? 'Unknown error',
        code: error['code'] as String? ?? 'UNKNOWN',
        details: error['details'] as Map<String, dynamic>?,
        statusCode: response.statusCode,
      );
    }
    
    // Generic status code handling
    switch (response.statusCode) {
      case 400:
        return ServerException(
          message: 'Bad request.',
          code: 'BAD_REQUEST',
          statusCode: 400,
        );
      case 401:
        return ServerException(
          message: 'Unauthorized. Please login again.',
          code: 'UNAUTHORIZED',
          statusCode: 401,
        );
      case 403:
        return ServerException(
          message: 'Access forbidden.',
          code: 'FORBIDDEN',
          statusCode: 403,
        );
      case 404:
        return ServerException(
          message: 'Resource not found.',
          code: 'NOT_FOUND',
          statusCode: 404,
        );
      case 422:
        return ServerException(
          message: 'Validation error.',
          code: 'VALIDATION_ERROR',
          statusCode: 422,
          details: data is Map<String, dynamic> ? data : null,
        );
      case 500:
        return ServerException(
          message: 'Internal server error.',
          code: 'SERVER_ERROR',
          statusCode: 500,
        );
      default:
        return ServerException(
          message: 'Server error (${response.statusCode}).',
          code: 'HTTP_${response.statusCode}',
          statusCode: response.statusCode,
        );
    }
  }
}
```

## API Response Models (DTOs)

### Base Response Wrapper

```dart
// core/network/models/api_response.dart

import 'package:freezed_annotation/freezed_annotation.dart';

part 'api_response.freezed.dart';
part 'api_response.g.dart';

@freezed
class ApiError with _$ApiError {
  const factory ApiError({
    required String code,
    required String message,
    @Default({}) Map<String, dynamic> details,
  }) = _ApiError;
  
  factory ApiError.fromJson(Map<String, dynamic> json) =>
      _$ApiErrorFromJson(json);
}

@freezed
class PaginatedResponse<T> with _$PaginatedResponse<T> {
  const factory PaginatedResponse({
    required List<T> items,
    required int total,
    required int page,
    required int pageSize,
    required bool hasMore,
  }) = _PaginatedResponse<T>;
}
```

### Auth DTOs

```dart
// features/auth/data/models/auth_dtos.dart

import 'package:freezed_annotation/freezed_annotation.dart';

part 'auth_dtos.freezed.dart';
part 'auth_dtos.g.dart';

@freezed
class LoginRequestDto with _$LoginRequestDto {
  const factory LoginRequestDto({
    required String email,
    required String password,
  }) = _LoginRequestDto;
  
  factory LoginRequestDto.fromJson(Map<String, dynamic> json) =>
      _$LoginRequestDtoFromJson(json);
}

@freezed
class RegisterRequestDto with _$RegisterRequestDto {
  const factory RegisterRequestDto({
    required String email,
    required String password,
    @JsonKey(name: 'display_name') required String displayName,
  }) = _RegisterRequestDto;
  
  factory RegisterRequestDto.fromJson(Map<String, dynamic> json) =>
      _$RegisterRequestDtoFromJson(json);
}

@freezed
class UserDto with _$UserDto {
  const factory UserDto({
    required String id,
    required String email,
    @JsonKey(name: 'display_name') required String displayName,
    @JsonKey(name: 'avatar_url') String? avatarUrl,
    String? username,
    required String role,
    @JsonKey(name: 'total_xp') required int totalXp,
    @JsonKey(name: 'starting_urn_id') String? startingUrnId,
    @JsonKey(name: 'is_profile_public') required bool isProfilePublic,
    @JsonKey(name: 'ai_personalization_enabled') required bool aiPersonalizationEnabled,
  }) = _UserDto;
  
  factory UserDto.fromJson(Map<String, dynamic> json) =>
      _$UserDtoFromJson(json);
}

@freezed
class AuthResponseDto with _$AuthResponseDto {
  const factory AuthResponseDto({
    required UserDto user,
    required StatsDto stats,
  }) = _AuthResponseDto;
  
  factory AuthResponseDto.fromJson(Map<String, dynamic> json) =>
      _$AuthResponseDtoFromJson(json);
}

@freezed
class StatsDto with _$StatsDto {
  const factory StatsDto({
    @JsonKey(name: 'total_xp') required int totalXp,
    required RankDto rank,
    @JsonKey(name: 'xp_to_next_rank') required int xpToNextRank,
    @JsonKey(name: 'next_rank') RankDto? nextRank,
  }) = _StatsDto;
  
  factory StatsDto.fromJson(Map<String, dynamic> json) =>
      _$StatsDtoFromJson(json);
}

@freezed
class RankDto with _$RankDto {
  const factory RankDto({
    required int level,
    required String name,
    required int xp,
  }) = _RankDto;
  
  factory RankDto.fromJson(Map<String, dynamic> json) =>
      _$RankDtoFromJson(json);
}
```

### Urn & Motif DTOs

```dart
// features/explore/data/models/urn_dtos.dart

import 'package:freezed_annotation/freezed_annotation.dart';

part 'urn_dtos.freezed.dart';
part 'urn_dtos.g.dart';

@freezed
class UrnDto with _$UrnDto {
  const factory UrnDto({
    required String id,
    required String slug,
    required String name,
    @JsonKey(name: 'name_en') String? nameEn,
    String? description,
    @JsonKey(name: 'thumbnail_url') String? thumbnailUrl,
    @JsonKey(name: 'model_url') String? modelUrl,
    @JsonKey(name: 'display_order') required int displayOrder,
    @JsonKey(name: 'is_demo') required bool isDemo,
    @JsonKey(name: 'motif_count') int? motifCount,
    @JsonKey(name: 'discovered_count') int? discoveredCount,
  }) = _UrnDto;
  
  factory UrnDto.fromJson(Map<String, dynamic> json) =>
      _$UrnDtoFromJson(json);
}

@freezed
class MotifDto with _$MotifDto {
  const factory MotifDto({
    required String id,
    required String slug,
    required String name,
    @JsonKey(name: 'name_en') String? nameEn,
    String? description,
    @JsonKey(name: 'thumbnail_url') String? thumbnailUrl,
    required String category,
    required String rarity,
    @JsonKey(name: 'urn_id') required String urnId,
    @JsonKey(name: 'pos_x') double? posX,
    @JsonKey(name: 'pos_y') double? posY,
    @JsonKey(name: 'pos_z') double? posZ,
    @JsonKey(name: 'bounding_radius') double? boundingRadius,
    @JsonKey(name: 'is_demo') required bool isDemo,
  }) = _MotifDto;
  
  factory MotifDto.fromJson(Map<String, dynamic> json) =>
      _$MotifDtoFromJson(json);
}

@freezed
class MotifDetailDto with _$MotifDetailDto {
  const factory MotifDetailDto({
    required MotifDto motif,
    LessonContentDto? lesson,
    ProgressDto? progress,
  }) = _MotifDetailDto;
  
  factory MotifDetailDto.fromJson(Map<String, dynamic> json) =>
      _$MotifDetailDtoFromJson(json);
}
```

### Lesson & Quiz DTOs

```dart
// features/lesson/data/models/lesson_dtos.dart

import 'package:freezed_annotation/freezed_annotation.dart';

part 'lesson_dtos.freezed.dart';
part 'lesson_dtos.g.dart';

@freezed
class LessonContentDto with _$LessonContentDto {
  const factory LessonContentDto({
    required String id,
    @JsonKey(name: 'intro_text') String? introText,
    String? description,
    @JsonKey(name: 'historical_context') String? historicalContext,
    String? symbolism,
    @JsonKey(name: 'fun_fact') String? funFact,
    @JsonKey(name: 'audio_narration_url') String? audioNarrationUrl,
    @JsonKey(name: 'video_url') String? videoUrl,
    @JsonKey(name: 'additional_images') List<String>? additionalImages,
  }) = _LessonContentDto;
  
  factory LessonContentDto.fromJson(Map<String, dynamic> json) =>
      _$LessonContentDtoFromJson(json);
}

@freezed
class QuizQuestionDto with _$QuizQuestionDto {
  const factory QuizQuestionDto({
    required String id,
    required String question,
    @JsonKey(name: 'question_type') required String questionType,
    required List<String> options,
    required int difficulty,
    String? explanation,
    @JsonKey(name: 'image_url') String? imageUrl,
    @JsonKey(name: 'target_mesh_name') String? targetMeshName,
  }) = _QuizQuestionDto;
  
  factory QuizQuestionDto.fromJson(Map<String, dynamic> json) =>
      _$QuizQuestionDtoFromJson(json);
}

@freezed
class QuizSubmitRequestDto with _$QuizSubmitRequestDto {
  const factory QuizSubmitRequestDto({
    required Map<String, String> answers,
    @JsonKey(name: 'time_spent_seconds') int? timeSpentSeconds,
  }) = _QuizSubmitRequestDto;
  
  factory QuizSubmitRequestDto.fromJson(Map<String, dynamic> json) =>
      _$QuizSubmitRequestDtoFromJson(json);
}

@freezed
class QuizResultDto with _$QuizResultDto {
  const factory QuizResultDto({
    required bool passed,
    required int score,
    @JsonKey(name: 'total_questions') required int totalQuestions,
    @JsonKey(name: 'correct_answers') required int correctAnswers,
    required int percentage,
    @JsonKey(name: 'xp_earned') required int xpEarned,
    @JsonKey(name: 'new_status') required String newStatus,
    List<QuizAnswerFeedbackDto>? feedback,
  }) = _QuizResultDto;
  
  factory QuizResultDto.fromJson(Map<String, dynamic> json) =>
      _$QuizResultDtoFromJson(json);
}

@freezed
class QuizAnswerFeedbackDto with _$QuizAnswerFeedbackDto {
  const factory QuizAnswerFeedbackDto({
    @JsonKey(name: 'question_id') required String questionId,
    required bool correct,
    @JsonKey(name: 'correct_answer') String? correctAnswer,
    String? explanation,
  }) = _QuizAnswerFeedbackDto;
  
  factory QuizAnswerFeedbackDto.fromJson(Map<String, dynamic> json) =>
      _$QuizAnswerFeedbackDtoFromJson(json);
}
```

### Progress DTO

```dart
// features/progress/data/models/progress_dtos.dart

import 'package:freezed_annotation/freezed_annotation.dart';

part 'progress_dtos.freezed.dart';
part 'progress_dtos.g.dart';

@freezed
class ProgressDto with _$ProgressDto {
  const factory ProgressDto({
    @JsonKey(name: 'motif_id') required String motifId,
    required String status,
    @JsonKey(name: 'xp_earned') required int xpEarned,
    @JsonKey(name: 'quiz_best_score') int? quizBestScore,
    @JsonKey(name: 'discovered_at') DateTime? discoveredAt,
    @JsonKey(name: 'learned_at') DateTime? learnedAt,
    @JsonKey(name: 'mastered_at') DateTime? masteredAt,
  }) = _ProgressDto;
  
  factory ProgressDto.fromJson(Map<String, dynamic> json) =>
      _$ProgressDtoFromJson(json);
}

@freezed
class UnlockRequestDto with _$UnlockRequestDto {
  const factory UnlockRequestDto({
    @JsonKey(name: 'motif_id') required String motifId,
  }) = _UnlockRequestDto;
  
  factory UnlockRequestDto.fromJson(Map<String, dynamic> json) =>
      _$UnlockRequestDtoFromJson(json);
}

@freezed
class UnlockResponseDto with _$UnlockResponseDto {
  const factory UnlockResponseDto({
    required ProgressDto progress,
    @JsonKey(name: 'xp_awarded') required int xpAwarded,
    @JsonKey(name: 'total_xp') required int totalXp,
    @JsonKey(name: 'badges_awarded') List<BadgeDto>? badgesAwarded,
  }) = _UnlockResponseDto;
  
  factory UnlockResponseDto.fromJson(Map<String, dynamic> json) =>
      _$UnlockResponseDtoFromJson(json);
}
```

### Gamification DTOs

```dart
// features/gamification/data/models/gamification_dtos.dart

import 'package:freezed_annotation/freezed_annotation.dart';

part 'gamification_dtos.freezed.dart';
part 'gamification_dtos.g.dart';

@freezed
class BadgeDto with _$BadgeDto {
  const factory BadgeDto({
    required String slug,
    required String name,
    @JsonKey(name: 'name_en') String? nameEn,
    required String description,
    @JsonKey(name: 'icon_url') required String iconUrl,
    required String category,
    @JsonKey(name: 'xp_bonus') required int xpBonus,
    @JsonKey(name: 'earned_at') DateTime? earnedAt,
  }) = _BadgeDto;
  
  factory BadgeDto.fromJson(Map<String, dynamic> json) =>
      _$BadgeDtoFromJson(json);
}

@freezed
class LeaderboardEntryDto with _$LeaderboardEntryDto {
  const factory LeaderboardEntryDto({
    required int rank,
    @JsonKey(name: 'user_id') required String userId,
    @JsonKey(name: 'display_name') required String displayName,
    @JsonKey(name: 'avatar_url') String? avatarUrl,
    @JsonKey(name: 'total_xp') required int totalXp,
    @JsonKey(name: 'badge_count') required int badgeCount,
  }) = _LeaderboardEntryDto;
  
  factory LeaderboardEntryDto.fromJson(Map<String, dynamic> json) =>
      _$LeaderboardEntryDtoFromJson(json);
}

@freezed
class QuestDto with _$QuestDto {
  const factory QuestDto({
    required String id,
    required String slug,
    required String name,
    String? description,
    String? category,
    @JsonKey(name: 'display_order') required int displayOrder,
    required String status,
    @JsonKey(name: 'progress_percent') required double progressPercent,
    @JsonKey(name: 'is_locked') required bool isLocked,
    @JsonKey(name: 'lock_reason') String? lockReason,
    QuestPrerequisiteDto? prerequisite,
    List<QuestRewardDto>? rewards,
  }) = _QuestDto;
  
  factory QuestDto.fromJson(Map<String, dynamic> json) =>
      _$QuestDtoFromJson(json);
}

@freezed
class QuestPrerequisiteDto with _$QuestPrerequisiteDto {
  const factory QuestPrerequisiteDto({
    required String id,
    required String slug,
    required String name,
  }) = _QuestPrerequisiteDto;
  
  factory QuestPrerequisiteDto.fromJson(Map<String, dynamic> json) =>
      _$QuestPrerequisiteDtoFromJson(json);
}

@freezed
class QuestRewardDto with _$QuestRewardDto {
  const factory QuestRewardDto({
    @JsonKey(name: 'reward_type') required String rewardType,
    int? amount,
    @JsonKey(name: 'badge_slug') String? badgeSlug,
    Map<String, dynamic>? metadata,
  }) = _QuestRewardDto;
  
  factory QuestRewardDto.fromJson(Map<String, dynamic> json) =>
      _$QuestRewardDtoFromJson(json);
}
```

## Data Sources

### Remote Data Source Pattern

```dart
// features/explore/data/datasources/urn_remote_datasource.dart

abstract class UrnRemoteDataSource {
  Future<List<UrnDto>> getUrns();
  Future<UrnDto> getUrn(String slug);
  Future<List<MotifDto>> getUrnMotifs(String urnId);
}

class UrnRemoteDataSourceImpl implements UrnRemoteDataSource {
  final ApiClient _apiClient;
  
  UrnRemoteDataSourceImpl(this._apiClient);
  
  @override
  Future<List<UrnDto>> getUrns() async {
    final response = await _apiClient.get<List<dynamic>>(ApiConstants.urns);
    return response.data!
        .map((json) => UrnDto.fromJson(json as Map<String, dynamic>))
        .toList();
  }
  
  @override
  Future<UrnDto> getUrn(String slug) async {
    final response = await _apiClient.get<Map<String, dynamic>>(
      ApiConstants.urn(slug),
    );
    return UrnDto.fromJson(response.data!);