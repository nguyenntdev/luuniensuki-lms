import 'package:freezed_annotation/freezed_annotation.dart';

part 'urn_dtos.freezed.dart';
part 'urn_dtos.g.dart';

/// Converter to handle options that might come as string or list from backend
class OptionsListConverter implements JsonConverter<List<String>, dynamic> {
  const OptionsListConverter();

  @override
  List<String> fromJson(dynamic json) {
    if (json == null) return [];
    if (json is List) {
      return json.map((e) => e?.toString() ?? '').where((e) => e.isNotEmpty).toList();
    }
    // If backend sends a string instead of list, return empty list
    // This prevents iterating over string characters
    return [];
  }

  @override
  dynamic toJson(List<String> object) => object;
}

/// Urn list item DTO (from /api/v1/urns)
@freezed
class UrnListItemDto with _$UrnListItemDto {
  const factory UrnListItemDto({
    required String id,
    required String slug,
    required String name,
    @JsonKey(name: 'name_en') String? nameEn,
    @JsonKey(name: 'display_order') @Default(0) int displayOrder,
    @JsonKey(name: 'thumbnail_url') String? thumbnailUrl,
    @JsonKey(name: 'model_url') String? modelUrl,
    @JsonKey(name: 'motif_count') @Default(0) int motifCount,
    @JsonKey(name: 'discovered_count') @Default(0) int discoveredCount,
    @JsonKey(name: 'learned_count') @Default(0) int learnedCount,
    @JsonKey(name: 'mastered_count') @Default(0) int masteredCount,
  }) = _UrnListItemDto;

  factory UrnListItemDto.fromJson(Map<String, dynamic> json) =>
      _$UrnListItemDtoFromJson(json);
}

/// Urn detail response DTO wrapper (from /api/v1/urns/{slug})
/// API returns {"urn": {...}, "motifs": [...]}
@freezed
class UrnDetailResponseDto with _$UrnDetailResponseDto {
  const factory UrnDetailResponseDto({
    required UrnDetailDto urn,
    @Default([]) List<MotifDto> motifs,
  }) = _UrnDetailResponseDto;

  factory UrnDetailResponseDto.fromJson(Map<String, dynamic> json) =>
      _$UrnDetailResponseDtoFromJson(json);
}

/// Urn detail DTO (nested inside response)
@freezed
class UrnDetailDto with _$UrnDetailDto {
  const factory UrnDetailDto({
    required String id,
    required String slug,
    required String name,
    @JsonKey(name: 'name_en') String? nameEn,
    @JsonKey(name: 'name_han') String? nameHan,
    String? represents,
    String? description,
    @JsonKey(name: 'description_en') String? descriptionEn,
    @JsonKey(name: 'display_order') @Default(0) int displayOrder,
    @JsonKey(name: 'thumbnail_url') String? thumbnailUrl,
    @JsonKey(name: 'model_url') String? modelUrl,
    @JsonKey(name: 'is_demo') @Default(false) bool isDemo,
  }) = _UrnDetailDto;

  factory UrnDetailDto.fromJson(Map<String, dynamic> json) =>
      _$UrnDetailDtoFromJson(json);
}

/// Motif DTO (from urn detail or /api/v1/motifs/{id})
@freezed
class MotifDto with _$MotifDto {
  const factory MotifDto({
    required String id,
    @JsonKey(name: 'urn_id') required String urnId,
    @JsonKey(name: 'mesh_name') required String meshName,
    required String name,
    @JsonKey(name: 'name_en') String? nameEn,
    required String category,
    required String rarity,
    @JsonKey(name: 'pos_x') @Default(0.0) double posX,
    @JsonKey(name: 'pos_y') @Default(0.0) double posY,
    @JsonKey(name: 'pos_z') @Default(0.0) double posZ,
    @JsonKey(name: 'bounding_radius') @Default(0.08) double boundingRadius,
    @JsonKey(name: 'thumbnail_url') String? thumbnailUrl,
    @JsonKey(name: 'image_url') String? imageUrl,
    @JsonKey(name: 'is_demo') @Default(false) bool isDemo,
  }) = _MotifDto;

  factory MotifDto.fromJson(Map<String, dynamic> json) =>
      _$MotifDtoFromJson(json);
}

/// URN info DTO (nested in motif detail response)
@freezed
class UrnInfoDto with _$UrnInfoDto {
  const factory UrnInfoDto({
    required String id,
    required String slug,
    required String name,
    @JsonKey(name: 'model_url') String? modelUrl,
    @JsonKey(name: 'thumbnail_url') String? thumbnailUrl,
    String? description,
    @JsonKey(name: 'display_order') @Default(0) int displayOrder,
  }) = _UrnInfoDto;

  factory UrnInfoDto.fromJson(Map<String, dynamic> json) =>
      _$UrnInfoDtoFromJson(json);
}

/// Motif detail DTO (from /api/v1/motifs/{id})
@freezed
class MotifDetailDto with _$MotifDetailDto {
  const factory MotifDetailDto({
    required String id,
    required UrnInfoDto urn,
    @JsonKey(name: 'mesh_name') required String meshName,
    required String name,
    @JsonKey(name: 'name_en') String? nameEn,
    required String category,
    required String rarity,
    @JsonKey(name: 'pos_x') @Default(0.0) double posX,
    @JsonKey(name: 'pos_y') @Default(0.0) double posY,
    @JsonKey(name: 'pos_z') @Default(0.0) double posZ,
    @JsonKey(name: 'bounding_radius') @Default(0.08) double boundingRadius,
    @JsonKey(name: 'thumbnail_url') String? thumbnailUrl,
    @JsonKey(name: 'image_url') String? imageUrl,
    @JsonKey(name: 'is_demo') @Default(false) bool isDemo,
    LessonContentDto? lesson,
    UserProgressDto? progress,
  }) = _MotifDetailDto;

  factory MotifDetailDto.fromJson(Map<String, dynamic> json) =>
      _$MotifDetailDtoFromJson(json);
}

/// Lesson content DTO
@freezed
class LessonContentDto with _$LessonContentDto {
  const factory LessonContentDto({
    String? id,
    @JsonKey(name: 'motif_id') String? motifId,
    @JsonKey(name: 'intro_text') String? introText,
    String? description,
    @JsonKey(name: 'historical_context') String? historicalContext,
    String? symbolism,
    @JsonKey(name: 'fun_fact') String? funFact,
    @JsonKey(name: 'audio_url') String? audioUrl,
    @JsonKey(name: 'video_url') String? videoUrl,
    @Default([]) List<String> images,
  }) = _LessonContentDto;

  factory LessonContentDto.fromJson(Map<String, dynamic> json) =>
      _$LessonContentDtoFromJson(json);
}

/// User progress DTO
@freezed
class UserProgressDto with _$UserProgressDto {
  const factory UserProgressDto({
    required String id,
    @JsonKey(name: 'user_id') required String userId,
    @JsonKey(name: 'motif_id') required String motifId,
    required String status,
    @JsonKey(name: 'discovered_at') String? discoveredAt,
    @JsonKey(name: 'learned_at') String? learnedAt,
    @JsonKey(name: 'mastered_at') String? masteredAt,
    @JsonKey(name: 'xp_earned') @Default(0) int xpEarned,
    @JsonKey(name: 'quiz_best_score') int? quizBestScore,
  }) = _UserProgressDto;

  factory UserProgressDto.fromJson(Map<String, dynamic> json) =>
      _$UserProgressDtoFromJson(json);
}

/// Unlock response DTO (from POST /api/v1/progress/unlock)
@freezed
class UnlockResponseDto with _$UnlockResponseDto {
  const factory UnlockResponseDto({
    required UserProgressDto progress,
    @JsonKey(name: 'xp_earned') @Default(0) int xpEarned,
    @JsonKey(name: 'total_xp') @Default(0) int totalXp,
    @JsonKey(name: 'new_badges') @Default([]) List<BadgeDto> newBadges,
    @JsonKey(name: 'streak_updated') @Default(false) bool streakUpdated,
    @JsonKey(name: 'current_streak') @Default(0) int currentStreak,
  }) = _UnlockResponseDto;

  factory UnlockResponseDto.fromJson(Map<String, dynamic> json) =>
      _$UnlockResponseDtoFromJson(json);
}

/// Badge DTO
@freezed
class BadgeDto with _$BadgeDto {
  const factory BadgeDto({
    required String id,
    required String slug,
    required String name,
    @JsonKey(name: 'name_en') String? nameEn,
    String? description,
    @JsonKey(name: 'icon_url') String? iconUrl,
    required String category,
    @JsonKey(name: 'xp_bonus') @Default(0) int xpBonus,
  }) = _BadgeDto;

  factory BadgeDto.fromJson(Map<String, dynamic> json) =>
      _$BadgeDtoFromJson(json);
}

/// Complete lesson response DTO
@freezed
class CompleteLessonResponseDto with _$CompleteLessonResponseDto {
  const factory CompleteLessonResponseDto({
    @JsonKey(name: 'user_id') required String userId,
    @JsonKey(name: 'motif_id') required String motifId,
    required String status,
    @JsonKey(name: 'lesson_viewed_at') DateTime? lessonViewedAt,
    @JsonKey(name: 'learned_at') DateTime? learnedAt,
    @JsonKey(name: 'xp_awarded') @Default(0) int xpEarned,
    @JsonKey(name: 'total_xp') @Default(0) int totalXp,
  }) = _CompleteLessonResponseDto;

  factory CompleteLessonResponseDto.fromJson(Map<String, dynamic> json) =>
      _$CompleteLessonResponseDtoFromJson(json);
}

/// Quiz question DTO
@freezed
class QuizQuestionDto with _$QuizQuestionDto {
  const factory QuizQuestionDto({
    required String id,
    @JsonKey(name: 'motif_id') String? motifId,
    @JsonKey(name: 'question_type') required String questionType,
    @JsonKey(name: 'question_text') required String questionText,
    @JsonKey(name: 'correct_answer') String? correctAnswer,
    @OptionsListConverter() @Default([]) List<String> options,
    @JsonKey(name: 'image_url') String? imageUrl,
    String? explanation,
    @JsonKey(name: 'display_order') @Default(0) int displayOrder,
    @JsonKey(name: 'target_mesh_name') String? targetMeshName,
    @Default(1) int difficulty,
  }) = _QuizQuestionDto;

  factory QuizQuestionDto.fromJson(Map<String, dynamic> json) =>
      _$QuizQuestionDtoFromJson(json);
}

/// Quiz response DTO (list of questions)
@freezed
class QuizResponseDto with _$QuizResponseDto {
  const factory QuizResponseDto({
    @JsonKey(name: 'motif_id') required String motifId,
    @JsonKey(name: 'motif_name') String? motifName,
    required List<QuizQuestionDto> questions,
    @Default(0) int attempts,
    @JsonKey(name: 'best_score') @Default(0) int bestScore,
    @JsonKey(name: 'pass_percent') @Default(80) int passPercent,
  }) = _QuizResponseDto;

  factory QuizResponseDto.fromJson(Map<String, dynamic> json) =>
      _$QuizResponseDtoFromJson(json);
}

/// Quiz submission request DTO
@freezed
class QuizSubmitRequestDto with _$QuizSubmitRequestDto {
  const factory QuizSubmitRequestDto({
    required List<QuizAnswerDto> answers,
    @JsonKey(name: 'time_taken_seconds') int? timeTakenSeconds,
  }) = _QuizSubmitRequestDto;

  factory QuizSubmitRequestDto.fromJson(Map<String, dynamic> json) =>
      _$QuizSubmitRequestDtoFromJson(json);
}

/// Quiz answer DTO
@freezed
class QuizAnswerDto with _$QuizAnswerDto {
  const factory QuizAnswerDto({
    @JsonKey(name: 'question_id') required String questionId,
    required String answer,
  }) = _QuizAnswerDto;

  factory QuizAnswerDto.fromJson(Map<String, dynamic> json) =>
      _$QuizAnswerDtoFromJson(json);
}

/// Quiz result DTO
@freezed
class QuizResultDto with _$QuizResultDto {
  const factory QuizResultDto({
    required bool passed,
    required int score,
    @JsonKey(name: 'total_questions') required int totalQuestions,
    @JsonKey(name: 'correct_answers') required int correctAnswers,
    @JsonKey(name: 'percentage') required int percentage,
    @JsonKey(name: 'xp_earned') @Default(0) int xpEarned,
    @JsonKey(name: 'total_xp') @Default(0) int totalXp,
    @JsonKey(name: 'new_badges') @Default([]) List<BadgeDto> newBadges,
    @JsonKey(name: 'is_new_best') @Default(false) bool isNewBest,
    UserProgressDto? progress,
  }) = _QuizResultDto;

  factory QuizResultDto.fromJson(Map<String, dynamic> json) =>
      _$QuizResultDtoFromJson(json);
}
