import 'package:equatable/equatable.dart';

/// Quest status
enum QuestStatus {
  notStarted,
  inProgress,
  completed,
  locked;

  String get name {
    switch (this) {
      case QuestStatus.notStarted:
        return 'not_started';
      case QuestStatus.inProgress:
        return 'in_progress';
      case QuestStatus.completed:
        return 'completed';
      case QuestStatus.locked:
        return 'locked';
    }
  }

  String get displayName {
    switch (this) {
      case QuestStatus.notStarted:
        return 'Chưa bắt đầu';
      case QuestStatus.inProgress:
        return 'Đang thực hiện';
      case QuestStatus.completed:
        return 'Đã hoàn thành';
      case QuestStatus.locked:
        return 'Đã khóa';
    }
  }

  static QuestStatus fromString(String? val) {
    switch (val?.toLowerCase()) {
      case 'in_progress':
      case 'inprogress':
        return QuestStatus.inProgress;
      case 'completed':
        return QuestStatus.completed;
      case 'locked':
        return QuestStatus.locked;
      case 'not_started':
      default:
        return QuestStatus.notStarted;
    }
  }
}

/// Quest reward
class QuestReward extends Equatable {
  final String rewardType;
  final int amount;
  final String? badgeSlug;

  const QuestReward({
    required this.rewardType,
    required this.amount,
    this.badgeSlug,
  });

  factory QuestReward.fromJson(Map<String, dynamic> json) {
    return QuestReward(
      rewardType: json['reward_type'] as String? ?? 'xp',
      amount: (json['amount'] as num?)?.toInt() ?? 0,
      badgeSlug: json['badge_slug'] as String?,
    );
  }

  Map<String, dynamic> toJson() => {
        'reward_type': rewardType,
        'amount': amount,
        if (badgeSlug != null) 'badge_slug': badgeSlug,
      };

  @override
  List<Object?> get props => [rewardType, amount, badgeSlug];
}

/// Quest objective
class QuestObjective extends Equatable {
  final String id;
  final String objectiveType;
  final String description;
  final int targetValue;
  final int currentValue;
  final bool isComplete;

  const QuestObjective({
    required this.id,
    required this.objectiveType,
    required this.description,
    required this.targetValue,
    required this.currentValue,
    required this.isComplete,
  });

  factory QuestObjective.fromJson(Map<String, dynamic> json) {
    final cur = (json['current_value'] as num?)?.toInt() ?? 0;
    final tgt = (json['target_value'] as num?)?.toInt() ?? 1;
    return QuestObjective(
      id: json['id']?.toString() ?? '',
      objectiveType: json['objective_type'] as String? ?? 'general',
      description: json['description'] as String? ??
          (json['objective_type'] == 'discover_motifs'
              ? 'Khám phá họa tiết lịch sử'
              : 'Hoàn thành bài học hoặc trắc nghiệm'),
      targetValue: tgt,
      currentValue: cur,
      isComplete: (json['is_complete'] as bool?) ?? (cur >= tgt),
    );
  }

  Map<String, dynamic> toJson() => {
        'id': id,
        'objective_type': objectiveType,
        'description': description,
        'target_value': targetValue,
        'current_value': currentValue,
        'is_complete': isComplete,
      };

  @override
  List<Object?> get props => [
        id,
        objectiveType,
        description,
        targetValue,
        currentValue,
        isComplete,
      ];
}

/// Quest step
class QuestStep extends Equatable {
  final String id;
  final String title;
  final String? description;
  final int displayOrder;
  final double completionPercent;
  final List<QuestObjective> objectives;

  const QuestStep({
    required this.id,
    required this.title,
    this.description,
    required this.displayOrder,
    required this.completionPercent,
    required this.objectives,
  });

  factory QuestStep.fromJson(Map<String, dynamic> json) {
    final rawObjectives = json['objectives'] as List? ?? [];
    return QuestStep(
      id: json['id']?.toString() ?? '',
      title: json['title'] as String? ?? 'Bước nhiệm vụ',
      description: json['description'] as String?,
      displayOrder: (json['display_order'] as num?)?.toInt() ?? 1,
      completionPercent:
          (json['completion_percent'] as num?)?.toDouble() ?? 0.0,
      objectives: rawObjectives
          .map((o) => QuestObjective.fromJson(Map<String, dynamic>.from(o as Map)))
          .toList(),
    );
  }

  Map<String, dynamic> toJson() => {
        'id': id,
        'title': title,
        if (description != null) 'description': description,
        'display_order': displayOrder,
        'completion_percent': completionPercent,
        'objectives': objectives.map((o) => o.toJson()).toList(),
      };

  @override
  List<Object?> get props => [
        id,
        title,
        description,
        displayOrder,
        completionPercent,
        objectives,
      ];
}

/// Main Quest entity
class Quest extends Equatable {
  final String id;
  final String slug;
  final String name;
  final String description;
  final String category;
  final QuestStatus status;
  final double progressPercent;
  final bool isLocked;
  final String? lockReason;
  final int estimatedMinutes;
  final List<QuestReward> rewards;
  final List<QuestStep> steps;

  const Quest({
    required this.id,
    required this.slug,
    required this.name,
    required this.description,
    required this.category,
    required this.status,
    required this.progressPercent,
    required this.isLocked,
    this.lockReason,
    required this.estimatedMinutes,
    required this.rewards,
    required this.steps,
  });

  int get xpReward {
    for (final r in rewards) {
      if (r.rewardType.toLowerCase() == 'xp' ||
          r.rewardType.toLowerCase() == 'points') {
        return r.amount;
      }
    }
    return 50;
  }

  int get gemsReward {
    for (final r in rewards) {
      if (r.rewardType.toLowerCase() == 'gems' ||
          r.rewardType.toLowerCase() == 'gem') {
        return r.amount;
      }
    }
    return 10;
  }

  factory Quest.fromJson(Map<String, dynamic> json) {
    final rawRewards = json['rewards'] as List? ?? [];
    final rawSteps = json['steps'] as List? ?? [];

    return Quest(
      id: json['id']?.toString() ?? '',
      slug: json['slug'] as String? ?? '',
      name: json['name'] as String? ?? 'Nhiệm vụ',
      description: json['description'] as String? ?? '',
      category: json['category'] as String? ?? 'di_san',
      status: QuestStatus.fromString(json['status'] as String?),
      progressPercent: (json['progress_percent'] as num?)?.toDouble() ?? 0.0,
      isLocked: (json['is_locked'] as bool?) ?? false,
      lockReason: json['lock_reason'] as String?,
      estimatedMinutes: (json['estimated_minutes'] as num?)?.toInt() ?? 10,
      rewards: rawRewards
          .map((r) => QuestReward.fromJson(Map<String, dynamic>.from(r as Map)))
          .toList(),
      steps: rawSteps
          .map((s) => QuestStep.fromJson(Map<String, dynamic>.from(s as Map)))
          .toList(),
    );
  }

  Map<String, dynamic> toJson() => {
        'id': id,
        'slug': slug,
        'name': name,
        'description': description,
        'category': category,
        'status': status.name,
        'progress_percent': progressPercent,
        'is_locked': isLocked,
        if (lockReason != null) 'lock_reason': lockReason,
        'estimated_minutes': estimatedMinutes,
        'rewards': rewards.map((r) => r.toJson()).toList(),
        'steps': steps.map((s) => s.toJson()).toList(),
      };

  Quest copyWith({
    String? id,
    String? slug,
    String? name,
    String? description,
    String? category,
    QuestStatus? status,
    double? progressPercent,
    bool? isLocked,
    String? lockReason,
    int? estimatedMinutes,
    List<QuestReward>? rewards,
    List<QuestStep>? steps,
  }) {
    return Quest(
      id: id ?? this.id,
      slug: slug ?? this.slug,
      name: name ?? this.name,
      description: description ?? this.description,
      category: category ?? this.category,
      status: status ?? this.status,
      progressPercent: progressPercent ?? this.progressPercent,
      isLocked: isLocked ?? this.isLocked,
      lockReason: lockReason ?? this.lockReason,
      estimatedMinutes: estimatedMinutes ?? this.estimatedMinutes,
      rewards: rewards ?? this.rewards,
      steps: steps ?? this.steps,
    );
  }

  @override
  List<Object?> get props => [
        id,
        slug,
        name,
        description,
        category,
        status,
        progressPercent,
        isLocked,
        lockReason,
        estimatedMinutes,
        rewards,
        steps,
      ];
}

/// Canonical default heritage quests for authentic offline / seed state
const List<Quest> kCanonicalQuests = [
  Quest(
    id: 'quest_kham_pha_cuu_dinh',
    slug: 'kham-pha-cuu-dinh',
    name: 'Khám Phá Cửu Đỉnh',
    description:
        'Tìm hiểu lịch sử đúc và bố trí của 9 đỉnh đồng triều Nguyễn tại Thế Tổ Miếu.',
    category: 'lich_su',
    status: QuestStatus.inProgress,
    progressPercent: 66.0,
    isLocked: false,
    estimatedMinutes: 15,
    rewards: [
      QuestReward(rewardType: 'xp', amount: 100),
      QuestReward(rewardType: 'gems', amount: 20),
    ],
    steps: [
      QuestStep(
        id: 'step_1',
        title: 'Khảo sát Cao Đỉnh',
        description: 'Quan sát các hình khắc rồng mây và vị trí tối thượng.',
        displayOrder: 1,
        completionPercent: 100.0,
        objectives: [
          QuestObjective(
            id: 'obj_1_1',
            objectiveType: 'view_urn',
            description: 'Mở chi tiết Cao Đỉnh trong bản đồ 3D',
            targetValue: 1,
            currentValue: 1,
            isComplete: true,
          ),
        ],
      ),
      QuestStep(
        id: 'step_2',
        title: 'Học 3 họa tiết tiêu biểu',
        description: 'Học bài học về Sông Gianh, Rồng Vàng, Cây Lúa.',
        displayOrder: 2,
        completionPercent: 66.0,
        objectives: [
          QuestObjective(
            id: 'obj_2_1',
            objectiveType: 'complete_lessons',
            description: 'Hoàn thành 3 bài học',
            targetValue: 3,
            currentValue: 2,
            isComplete: false,
          ),
        ],
      ),
    ],
  ),
  Quest(
    id: 'quest_ky_tich_song_nui',
    slug: 'ky-tich-song-nui',
    name: 'Kỳ Tích Sông Núi',
    description:
        'Tìm hiểu các biểu tượng sông núi và hải phận thiêng liêng khắc trên Cửu Đỉnh.',
    category: 'dia_ly',
    status: QuestStatus.notStarted,
    progressPercent: 0.0,
    isLocked: false,
    estimatedMinutes: 20,
    rewards: [
      QuestReward(rewardType: 'xp', amount: 150),
      QuestReward(rewardType: 'gems', amount: 25),
    ],
    steps: [
      QuestStep(
        id: 'step_2_1',
        title: 'Nhận diện Nam Hải & Đông Hải',
        description: 'Khám phá các vùng biển đảo thiêng liêng trên Huyền Đỉnh.',
        displayOrder: 1,
        completionPercent: 0.0,
        objectives: [
          QuestObjective(
            id: 'obj_2_1_1',
            objectiveType: 'discover_sea_reliefs',
            description: 'Định vị biển Đông và biển Nam trên đỉnh',
            targetValue: 2,
            currentValue: 0,
            isComplete: false,
          ),
        ],
      ),
    ],
  ),
  Quest(
    id: 'quest_bach_thao_bach_thu',
    slug: 'bach-thao-bach-thu',
    name: 'Bách Thảo Bách Thú',
    description:
        'Học hỏi về hệ động thực vật nhiệt đới phong phú được cha ông đúc nổi trên đồng.',
    category: 'sinh_vat',
    status: QuestStatus.notStarted,
    progressPercent: 0.0,
    isLocked: false,
    estimatedMinutes: 25,
    rewards: [
      QuestReward(rewardType: 'xp', amount: 120),
      QuestReward(rewardType: 'gems', amount: 15),
    ],
    steps: [
      QuestStep(
        id: 'step_3_1',
        title: 'Tìm hiểu thảo mộc quý',
        description: 'Học họa tiết Cây Lúa, Sen, Trầm Hương.',
        displayOrder: 1,
        completionPercent: 0.0,
        objectives: [
          QuestObjective(
            id: 'obj_3_1_1',
            objectiveType: 'learn_plants',
            description: 'Hoàn thành bài tập về thực vật học triều Nguyễn',
            targetValue: 3,
            currentValue: 0,
            isComplete: false,
          ),
        ],
      ),
    ],
  ),
  Quest(
    id: 'quest_chuyen_can_7_ngay',
    slug: 'chuyen-can-7-ngay',
    name: 'Chiến Binh Chuyên Cần',
    description: 'Duy trì chuỗi ngày học tập và khám phá di sản 7 ngày liên tục.',
    category: 'chuoi_ngay',
    status: QuestStatus.inProgress,
    progressPercent: 71.0,
    isLocked: false,
    estimatedMinutes: 30,
    rewards: [
      QuestReward(rewardType: 'xp', amount: 200),
      QuestReward(rewardType: 'gems', amount: 50),
    ],
    steps: [
      QuestStep(
        id: 'step_4_1',
        title: 'Học tập 7 ngày liên tiếp',
        description: 'Đạt streak 7 ngày để nhận huy hiệu di sản đặc biệt.',
        displayOrder: 1,
        completionPercent: 71.0,
        objectives: [
          QuestObjective(
            id: 'obj_4_1_1',
            objectiveType: 'streak_days',
            description: 'Duy trì chuỗi ngày liên tiếp',
            targetValue: 7,
            currentValue: 5,
            isComplete: false,
          ),
        ],
      ),
    ],
  ),
];
