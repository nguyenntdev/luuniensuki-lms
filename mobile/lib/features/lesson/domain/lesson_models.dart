import 'package:freezed_annotation/freezed_annotation.dart';

part 'lesson_models.freezed.dart';

/// Motif entity with lesson and progress data
@freezed
class MotifDetail with _$MotifDetail {
  const factory MotifDetail({
    required String id,
    required String urnId,
    required String meshName,
    required String name,
    String? nameEn,
    required String category,
    required String rarity,
    required double posX,
    required double posY,
    required double posZ,
    required double boundingRadius,
    String? thumbnailUrl,
    String? imageUrl,
    required bool isDemo,
    LessonContent? lesson,
    UserProgress? progress,
  }) = _MotifDetail;

  const MotifDetail._();

  /// Get display name (Vietnamese preferred)
  String get displayName => name;

  /// Check if motif is discovered
  bool get isDiscovered =>
      progress != null && progress!.status != ProgressStatus.hidden;

  /// Check if lesson is completed
  bool get isLearned =>
      progress != null &&
      (progress!.status == ProgressStatus.learned ||
          progress!.status == ProgressStatus.mastered);

  /// Check if quiz is passed
  bool get isMastered =>
      progress != null && progress!.status == ProgressStatus.mastered;
}

/// Lesson content entity
@freezed
class LessonContent with _$LessonContent {
  const factory LessonContent({
    required String id,
    required String motifId,
    String? introText,
    String? description,
    String? historicalContext,
    String? symbolism,
    String? funFact,
    String? audioUrl,
    String? videoUrl,
    @Default([]) List<String> images,
  }) = _LessonContent;

  const LessonContent._();

  /// Check if lesson has any content
  bool get hasContent =>
      introText != null ||
      description != null ||
      historicalContext != null ||
      symbolism != null ||
      funFact != null;

  /// Check if lesson has media
  bool get hasAudio => audioUrl != null && audioUrl!.isNotEmpty;
  bool get hasVideo => videoUrl != null && videoUrl!.isNotEmpty;
  bool get hasImages => images.isNotEmpty;
}

/// User progress entity
@freezed
class UserProgress with _$UserProgress {
  const factory UserProgress({
    required String id,
    required String oderId,
    required String motifId,
    required ProgressStatus status,
    DateTime? discoveredAt,
    DateTime? learnedAt,
    DateTime? masteredAt,
    @Default(0) int xpEarned,
    int? quizBestScore,
  }) = _UserProgress;

  const UserProgress._();

  /// Get the XP based on status
  int get expectedXp {
    switch (status) {
      case ProgressStatus.hidden:
        return 0;
      case ProgressStatus.discovered:
        return 25;
      case ProgressStatus.learned:
        return 75; // 25 + 50
      case ProgressStatus.mastered:
        return 150; // 25 + 50 + 75
    }
  }
}

/// Progress status enum
enum ProgressStatus {
  hidden,
  discovered,
  learned,
  mastered;

  /// Parse from string
  static ProgressStatus fromString(String value) {
    switch (value.toLowerCase()) {
      case 'discovered':
        return ProgressStatus.discovered;
      case 'learned':
        return ProgressStatus.learned;
      case 'mastered':
        return ProgressStatus.mastered;
      default:
        return ProgressStatus.hidden;
    }
  }

  /// Get display name in Vietnamese
  String get displayName {
    switch (this) {
      case ProgressStatus.hidden:
        return 'Chưa khám phá';
      case ProgressStatus.discovered:
        return 'Đã khám phá';
      case ProgressStatus.learned:
        return 'Đã học';
      case ProgressStatus.mastered:
        return 'Thành thạo';
    }
  }

  /// Get step index (0-based)
  int get stepIndex {
    switch (this) {
      case ProgressStatus.hidden:
        return -1;
      case ProgressStatus.discovered:
        return 0;
      case ProgressStatus.learned:
        return 1;
      case ProgressStatus.mastered:
        return 2;
    }
  }
}

/// Badge entity
@freezed
class Badge with _$Badge {
  const factory Badge({
    required String id,
    required String slug,
    required String name,
    String? nameEn,
    String? description,
    String? iconUrl,
    required String category,
    @Default(0) int xpBonus,
  }) = _Badge;
}

/// Lesson completion result
@freezed
class LessonCompletionResult with _$LessonCompletionResult {
  const factory LessonCompletionResult({
    required UserProgress progress,
    required int xpEarned,
    required int totalXp,
    @Default([]) List<Badge> newBadges,
  }) = _LessonCompletionResult;
}
