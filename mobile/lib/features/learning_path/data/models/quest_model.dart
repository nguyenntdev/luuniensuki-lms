import 'package:flutter/foundation.dart';

/// Reward associated with a quest.
@immutable
class QuestRewardModel {
  final String rewardType;
  final int? amount;
  final String? badgeSlug;
  final dynamic metadata;

  const QuestRewardModel({
    required this.rewardType,
    this.amount,
    this.badgeSlug,
    this.metadata,
  });

  factory QuestRewardModel.fromJson(Map<String, dynamic> json) {
    return QuestRewardModel(
      rewardType: json['reward_type']?.toString() ?? 'xp',
      amount: json['amount'] as int?,
      badgeSlug: json['badge_slug'] as String?,
      metadata: json['metadata'],
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'reward_type': rewardType,
      'amount': amount,
      'badge_slug': badgeSlug,
      'metadata': metadata,
    };
  }
}

/// Objective inside a quest step.
@immutable
class QuestObjectiveModel {
  final String id;
  final String objectiveType;
  final int targetValue;
  final int currentValue;
  final bool isComplete;
  final Map<String, dynamic>? params;

  const QuestObjectiveModel({
    required this.id,
    required this.objectiveType,
    required this.targetValue,
    required this.currentValue,
    required this.isComplete,
    this.params,
  });

  factory QuestObjectiveModel.fromJson(Map<String, dynamic> json) {
    return QuestObjectiveModel(
      id: json['id']?.toString() ?? '',
      objectiveType: json['objective_type']?.toString() ?? '',
      targetValue: json['target_value'] as int? ?? 1,
      currentValue: json['current_value'] as int? ?? 0,
      isComplete: json['is_complete'] as bool? ?? false,
      params: json['params'] != null
          ? Map<String, dynamic>.from(json['params'] as Map)
          : null,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'objective_type': objectiveType,
      'target_value': targetValue,
      'current_value': currentValue,
      'is_complete': isComplete,
      'params': params,
    };
  }

  /// Human-friendly description based on objective type and params.
  String get displayName {
    switch (objectiveType) {
      case 'discover_any':
        return 'Khám phá $targetValue họa tiết bất kỳ';
      case 'complete_lesson':
        return 'Hoàn thành bài học cho $targetValue họa tiết';
      case 'complete_lesson_category':
        final cat = params?['category'] ?? '';
        return 'Học $targetValue bài học về $cat';
      case 'discover_category':
        final cat = params?['category'] ?? '';
        return 'Khám phá $targetValue họa tiết chủ đề $cat';
      case 'master_category':
        final cat = params?['category'] ?? '';
        return 'Luyện thành thạo $targetValue họa tiết $cat';
      case 'quiz_pass_count':
        final cat = params?['category'] ?? 'họa tiết';
        return 'Đạt điểm chuẩn trắc nghiệm ($cat)';
      case 'urn_exam_pass':
        return 'Vượt qua kỳ sát hạch đỉnh';
      case 'source_evidence_task':
      case 'evidence_inquiry_task':
      case 'claim_evidence_task':
        return 'Khảo cứu và tổng hợp nguồn tư liệu lịch sử';
      case 'verified_claim_task':
      case 'claim_exploration_task':
        return 'Xác thực cứ liệu lịch sử';
      default:
        return 'Nhiệm vụ: $objectiveType';
    }
  }
}

/// Step containing objectives inside a quest.
@immutable
class QuestStepModel {
  final String id;
  final String title;
  final String? description;
  final int displayOrder;
  final double completionPercent;
  final List<QuestObjectiveModel> objectives;

  const QuestStepModel({
    required this.id,
    required this.title,
    this.description,
    required this.displayOrder,
    required this.completionPercent,
    required this.objectives,
  });

  factory QuestStepModel.fromJson(Map<String, dynamic> json) {
    return QuestStepModel(
      id: json['id']?.toString() ?? '',
      title: json['title']?.toString() ?? '',
      description: json['description']?.toString(),
      displayOrder: json['display_order'] as int? ?? 0,
      completionPercent: (json['completion_percent'] as num?)?.toDouble() ?? 0.0,
      objectives: (json['objectives'] as List<dynamic>?)
              ?.map((o) => QuestObjectiveModel.fromJson(o as Map<String, dynamic>))
              .toList() ??
          const [],
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'title': title,
      'description': description,
      'display_order': displayOrder,
      'completion_percent': completionPercent,
      'objectives': objectives.map((o) => o.toJson()).toList(),
    };
  }
}

/// Prerequisite quest info.
@immutable
class QuestPrerequisiteModel {
  final String id;
  final String slug;
  final String name;

  const QuestPrerequisiteModel({
    required this.id,
    required this.slug,
    required this.name,
  });

  factory QuestPrerequisiteModel.fromJson(Map<String, dynamic> json) {
    return QuestPrerequisiteModel(
      id: json['id']?.toString() ?? '',
      slug: json['slug']?.toString() ?? '',
      name: json['name']?.toString() ?? '',
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'slug': slug,
      'name': name,
    };
  }
}

/// Certificate issued upon completing a quest.
@immutable
class QuestCertificateModel {
  final String code;
  final DateTime issuedAt;
  final String issuerName;

  const QuestCertificateModel({
    required this.code,
    required this.issuedAt,
    required this.issuerName,
  });

  factory QuestCertificateModel.fromJson(Map<String, dynamic> json) {
    return QuestCertificateModel(
      code: json['code']?.toString() ?? '',
      issuedAt: json['issued_at'] != null
          ? DateTime.tryParse(json['issued_at'].toString()) ?? DateTime.now()
          : DateTime.now(),
      issuerName: json['issuer_name']?.toString() ?? 'Lưu Niên Sử Ký LMS',
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'code': code,
      'issued_at': issuedAt.toIso8601String(),
      'issuer_name': issuerName,
    };
  }
}

/// Main quest model representing a learning quest.
@immutable
class QuestModel {
  final String id;
  final String slug;
  final String name;
  final String? description;
  final String? category;
  final int displayOrder;
  final String status; // 'not_started', 'in_progress', 'completed', 'locked'
  final double progressPercent;
  final bool isLocked;
  final String? lockReason;
  final QuestPrerequisiteModel? prerequisite;
  final List<QuestRewardModel> rewards;
  final List<QuestStepModel> steps;
  final QuestCertificateModel? certificate;

  const QuestModel({
    required this.id,
    required this.slug,
    required this.name,
    this.description,
    this.category,
    required this.displayOrder,
    required this.status,
    required this.progressPercent,
    required this.isLocked,
    this.lockReason,
    this.prerequisite,
    required this.rewards,
    this.steps = const [],
    this.certificate,
  });

  bool get isCompleted => status == 'completed';
  bool get isInProgress => status == 'in_progress' || (progressPercent > 0 && !isCompleted);
  bool get canClaim => !isLocked && progressPercent >= 100.0 && !isCompleted;

  int get totalXpReward {
    return rewards
        .where((r) => r.rewardType.toLowerCase() == 'xp')
        .fold(0, (sum, r) => sum + (r.amount ?? 0));
  }

  List<String> get badgeRewards {
    return rewards
        .where((r) => r.rewardType.toLowerCase() == 'badge' && r.badgeSlug != null)
        .map((r) => r.badgeSlug!)
        .toList();
  }

  int get streakFreezeRewards {
    return rewards
        .where((r) => r.rewardType.toLowerCase() == 'streak_freeze')
        .fold(0, (sum, r) => sum + (r.amount ?? 1));
  }

  factory QuestModel.fromJson(Map<String, dynamic> json) {
    return QuestModel(
      id: json['id']?.toString() ?? '',
      slug: json['slug']?.toString() ?? '',
      name: json['name']?.toString() ?? '',
      description: json['description']?.toString(),
      category: json['category']?.toString(),
      displayOrder: json['display_order'] as int? ?? 0,
      status: json['status']?.toString() ?? 'not_started',
      progressPercent: (json['progress_percent'] as num?)?.toDouble() ?? 0.0,
      isLocked: json['is_locked'] as bool? ?? false,
      lockReason: json['lock_reason']?.toString(),
      prerequisite: json['prerequisite'] != null
          ? QuestPrerequisiteModel.fromJson(
              Map<String, dynamic>.from(json['prerequisite'] as Map))
          : null,
      rewards: (json['rewards'] as List<dynamic>?)
              ?.map((r) => QuestRewardModel.fromJson(r as Map<String, dynamic>))
              .toList() ??
          const [],
      steps: (json['steps'] as List<dynamic>?)
              ?.map((s) => QuestStepModel.fromJson(s as Map<String, dynamic>))
              .toList() ??
          const [],
      certificate: json['certificate'] != null
          ? QuestCertificateModel.fromJson(
              Map<String, dynamic>.from(json['certificate'] as Map))
          : null,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'slug': slug,
      'name': name,
      'description': description,
      'category': category,
      'display_order': displayOrder,
      'status': status,
      'progress_percent': progressPercent,
      'is_locked': isLocked,
      'lock_reason': lockReason,
      'prerequisite': prerequisite?.toJson(),
      'rewards': rewards.map((r) => r.toJson()).toList(),
      'steps': steps.map((s) => s.toJson()).toList(),
      'certificate': certificate?.toJson(),
    };
  }
}

/// Response returned from claiming a quest reward.
@immutable
class QuestClaimResponseModel {
  final String questId;
  final String questSlug;
  final String questName;
  final String status;
  final int xpAwarded;
  final List<String> badgesAwarded;
  final int streakFreezesAwarded;
  final QuestCertificateModel? certificate;
  final String message;

  const QuestClaimResponseModel({
    required this.questId,
    required this.questSlug,
    required this.questName,
    required this.status,
    required this.xpAwarded,
    required this.badgesAwarded,
    required this.streakFreezesAwarded,
    this.certificate,
    required this.message,
  });

  factory QuestClaimResponseModel.fromJson(Map<String, dynamic> json) {
    return QuestClaimResponseModel(
      questId: json['quest_id']?.toString() ?? '',
      questSlug: json['quest_slug']?.toString() ?? '',
      questName: json['quest_name']?.toString() ?? '',
      status: json['status']?.toString() ?? 'completed',
      xpAwarded: json['xp_awarded'] as int? ?? 0,
      badgesAwarded: (json['badges_awarded'] as List<dynamic>?)
              ?.map((b) => b.toString())
              .toList() ??
          const [],
      streakFreezesAwarded: json['streak_freezes_awarded'] as int? ?? 0,
      certificate: json['certificate'] != null
          ? QuestCertificateModel.fromJson(
              Map<String, dynamic>.from(json['certificate'] as Map))
          : null,
      message: json['message']?.toString() ?? 'Nhận thưởng thành công!',
    );
  }
}
