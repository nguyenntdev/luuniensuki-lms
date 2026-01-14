import 'package:equatable/equatable.dart';

/// Type of gem transaction
enum GemTransactionType {
  earnedLesson('earned_lesson', 'Hoàn thành bài học'),
  earnedStreak('earned_streak', 'Đạt chuỗi học tập'),
  earnedPerfect('earned_perfect', 'Bài học hoàn hảo'),
  earnedBonus('earned_bonus', 'Thưởng'),
  spentStreakFreeze('spent_streak_freeze', 'Mua đóng băng chuỗi'),
  spentDoubleXp('spent_double_xp', 'Mua x2 XP'),
  spentHint('spent_hint', 'Mua gợi ý');

  final String value;
  final String displayName;

  const GemTransactionType(this.value, this.displayName);

  static GemTransactionType fromValue(String value) {
    return GemTransactionType.values.firstWhere(
      (type) => type.value == value,
      orElse: () => GemTransactionType.earnedBonus,
    );
  }

  bool get isEarned => value.startsWith('earned_');
  bool get isSpent => value.startsWith('spent_');
}

/// Gem transaction entity
class GemTransaction extends Equatable {
  final String id;
  final int amount;
  final GemTransactionType type;
  final String description;
  final DateTime createdAt;

  const GemTransaction({
    required this.id,
    required this.amount,
    required this.type,
    required this.description,
    required this.createdAt,
  });

  /// Create a copy with updated fields
  GemTransaction copyWith({
    String? id,
    int? amount,
    GemTransactionType? type,
    String? description,
    DateTime? createdAt,
  }) {
    return GemTransaction(
      id: id ?? this.id,
      amount: amount ?? this.amount,
      type: type ?? this.type,
      description: description ?? this.description,
      createdAt: createdAt ?? this.createdAt,
    );
  }

  @override
  List<Object?> get props => [id, amount, type, description, createdAt];

  @override
  String toString() {
    return 'GemTransaction(id: $id, amount: $amount, type: ${type.value}, description: $description)';
  }
}

