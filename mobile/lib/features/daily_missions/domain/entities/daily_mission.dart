import 'package:equatable/equatable.dart';

/// Mission type enum
enum MissionType {
  lesson('lesson', 'Bài học'),
  quiz('quiz', 'Bài kiểm tra'),
  discovery('discovery', 'Khám phá'),
  streak('streak', 'Chuỗi ngày');

  final String value;
  final String displayName;

  const MissionType(this.value, this.displayName);

  static MissionType fromString(String value) {
    return MissionType.values.firstWhere(
      (type) => type.value == value,
      orElse: () => MissionType.lesson,
    );
  }
}

/// Daily mission entity
class DailyMission extends Equatable {
  final String id;
  final String slug;
  final String name;
  final String description;
  final MissionType missionType;
  final int targetCount;
  final int xpReward;
  final bool isActive;
  final int currentCount;
  final bool isCompleted;
  final DateTime? completedAt;
  final int xpAwarded;
  final int progressPercentage;

  const DailyMission({
    required this.id,
    required this.slug,
    required this.name,
    required this.description,
    required this.missionType,
    required this.targetCount,
    required this.xpReward,
    this.isActive = true,
    this.currentCount = 0,
    this.isCompleted = false,
    this.completedAt,
    this.xpAwarded = 0,
    this.progressPercentage = 0,
  });

  /// Calculate progress percentage
  int get calculatedProgress {
    if (targetCount == 0) return 0;
    return ((currentCount / targetCount) * 100).clamp(0, 100).toInt();
  }

  /// Check if mission is completed
  bool get isComplete => currentCount >= targetCount;

  /// Remaining count to complete mission
  int get remainingCount {
    final remaining = targetCount - currentCount;
    return remaining < 0 ? 0 : remaining;
  }

  /// Create initial mission
  factory DailyMission.initial() {
    return const DailyMission(
      id: '',
      slug: '',
      name: '',
      description: '',
      missionType: MissionType.lesson,
      targetCount: 1,
      xpReward: 0,
    );
  }

  /// Copy with
  DailyMission copyWith({
    String? id,
    String? slug,
    String? name,
    String? description,
    MissionType? missionType,
    int? targetCount,
    int? xpReward,
    bool? isActive,
    int? currentCount,
    bool? isCompleted,
    DateTime? completedAt,
    int? xpAwarded,
    int? progressPercentage,
  }) {
    return DailyMission(
      id: id ?? this.id,
      slug: slug ?? this.slug,
      name: name ?? this.name,
      description: description ?? this.description,
      missionType: missionType ?? this.missionType,
      targetCount: targetCount ?? this.targetCount,
      xpReward: xpReward ?? this.xpReward,
      isActive: isActive ?? this.isActive,
      currentCount: currentCount ?? this.currentCount,
      isCompleted: isCompleted ?? this.isCompleted,
      completedAt: completedAt ?? this.completedAt,
      xpAwarded: xpAwarded ?? this.xpAwarded,
      progressPercentage: progressPercentage ?? this.progressPercentage,
    );
  }

  @override
  List<Object?> get props => [
        id,
        slug,
        name,
        description,
        missionType,
        targetCount,
        xpReward,
        isActive,
        currentCount,
        isCompleted,
        completedAt,
        xpAwarded,
        progressPercentage,
      ];
}

/// Daily missions summary
class DailyMissionsSummary extends Equatable {
  final List<DailyMission> missions;
  final int totalXpToday;
  final int completedCount;
  final int totalCount;

  const DailyMissionsSummary({
    required this.missions,
    required this.totalXpToday,
    required this.completedCount,
    required this.totalCount,
  });

  /// Get completion percentage
  int get completionPercentage {
    if (totalCount == 0) return 0;
    return ((completedCount / totalCount) * 100).toInt();
  }

  @override
  List<Object?> get props => [
        missions,
        totalXpToday,
        completedCount,
        totalCount,
      ];
}

