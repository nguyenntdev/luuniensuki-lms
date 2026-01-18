import 'package:freezed_annotation/freezed_annotation.dart';

part 'review_item.freezed.dart';
part 'review_item.g.dart';

/// Review item entity representing a motif in the spaced repetition system
/// Uses the SM-2 algorithm for optimal review scheduling
@freezed
class ReviewItem with _$ReviewItem {
  const factory ReviewItem({
    /// Unique identifier of the motif being reviewed
    required String motifId,
    
    /// Ease Factor (EF) - Determines how quickly intervals increase
    /// Default: 2.5, Range: 1.3 to 2.5+
    /// Higher = easier item, intervals grow faster
    @Default(2.5) double easeFactor,
    
    /// Current interval in days until next review
    /// Grows based on performance (SM-2 algorithm)
    @Default(0) int interval,
    
    /// Number of consecutive successful reviews (quality >= 3)
    /// Resets to 0 when quality < 3
    @Default(0) int repetitions,
    
    /// Next scheduled review date
    required DateTime nextReviewDate,
    
    /// Last review date (null if never reviewed)
    DateTime? lastReviewDate,
    
    /// History of quality ratings (0-5) for analytics
    /// 5: Perfect, 4: Correct with hesitation, 3: Correct with difficulty
    /// 2: Incorrect but easy recall, 1: Incorrect hard recall, 0: Complete blackout
    @Default([]) List<int> qualityHistory,
    
    /// Optional: motif title for display purposes
    String? motifTitle,
    
    /// Optional: category for organization
    String? category,
  }) = _ReviewItem;

  const ReviewItem._();

  /// Create from JSON
  factory ReviewItem.fromJson(Map<String, dynamic> json) =>
      _$ReviewItemFromJson(json);

  /// Create a new review item for a motif that hasn't been reviewed yet
  factory ReviewItem.initial({
    required String motifId,
    String? motifTitle,
    String? category,
  }) =>
      ReviewItem(
        motifId: motifId,
        easeFactor: 2.5,
        interval: 0,
        repetitions: 0,
        nextReviewDate: DateTime.now(),
        lastReviewDate: null,
        qualityHistory: [],
        motifTitle: motifTitle,
        category: category,
      );

  /// Check if this item is due for review
  bool get isDue => DateTime.now().isAfter(nextReviewDate) || 
                    DateTime.now().isAtSameMomentAs(nextReviewDate);

  /// Check if this item is overdue (more than 1 day past due date)
  bool get isOverdue {
    if (!isDue) return false;
    final daysPastDue = DateTime.now().difference(nextReviewDate).inDays;
    return daysPastDue > 1;
  }

  /// Get days until next review (negative if overdue)
  int get daysUntilReview => nextReviewDate.difference(DateTime.now()).inDays;

  /// Get hours until next review (for items due soon)
  int get hoursUntilReview => nextReviewDate.difference(DateTime.now()).inHours;

  /// Calculate average quality from history
  double get averageQuality {
    if (qualityHistory.isEmpty) return 0.0;
    final sum = qualityHistory.reduce((a, b) => a + b);
    return sum / qualityHistory.length;
  }

  /// Get total number of reviews
  int get totalReviews => qualityHistory.length;

  /// Check if this is a new item (never reviewed)
  bool get isNew => lastReviewDate == null;

  /// Get difficulty level based on ease factor
  /// Easy: EF >= 2.5, Medium: 2.0 <= EF < 2.5, Hard: EF < 2.0
  String get difficultyLevel {
    if (easeFactor >= 2.5) return 'easy';
    if (easeFactor >= 2.0) return 'medium';
    return 'hard';
  }

  /// Get success rate from quality history (quality >= 3)
  double get successRate {
    if (qualityHistory.isEmpty) return 0.0;
    final successful = qualityHistory.where((q) => q >= 3).length;
    return successful / qualityHistory.length;
  }

  /// Get urgency score for prioritization (0-100)
  /// Higher score = more urgent to review
  int get urgencyScore {
    if (isOverdue) {
      // Very overdue items get highest priority
      final daysPastDue = DateTime.now().difference(nextReviewDate).inDays;
      return (100 + daysPastDue * 5).clamp(0, 200);
    } else if (isDue) {
      // Due items get high priority
      return 90;
    } else if (hoursUntilReview <= 24) {
      // Items due within 24 hours
      return 70;
    } else if (daysUntilReview <= 3) {
      // Items due within 3 days
      return 50;
    } else {
      // Not urgent
      return 20;
    }
  }

  /// Format next review date as human-readable string
  String get nextReviewFormatted {
    final now = DateTime.now();
    final difference = nextReviewDate.difference(now);
    
    if (isOverdue) {
      final daysPast = -difference.inDays;
      if (daysPast == 1) return 'Quá hạn 1 ngày';
      return 'Quá hạn $daysPast ngày';
    } else if (difference.inHours < 1) {
      return 'Bây giờ';
    } else if (difference.inHours < 24) {
      final hours = difference.inHours;
      return 'Trong $hours giờ';
    } else if (difference.inDays == 1) {
      return 'Ngày mai';
    } else if (difference.inDays <= 7) {
      return 'Trong ${difference.inDays} ngày';
    } else {
      final weeks = (difference.inDays / 7).floor();
      return 'Trong $weeks tuần';
    }
  }
}

