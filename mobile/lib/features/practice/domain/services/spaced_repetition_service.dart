import 'dart:math';
import '../models/review_item.dart';

/// Service implementing the SM-2 spaced repetition algorithm
/// 
/// The SM-2 algorithm optimizes learning by scheduling reviews at increasing intervals
/// based on how well the user remembers the material.
/// 
/// Algorithm Details:
/// - Ease Factor (EF): Starts at 2.5, adjusts based on performance
/// - Interval: Days until next review
/// - Repetitions: Number of successful reviews
/// 
/// Quality ratings (0-5):
/// - 5: Perfect response
/// - 4: Correct with hesitation
/// - 3: Correct with difficulty
/// - 2: Incorrect, but easy recall
/// - 1: Incorrect, hard recall
/// - 0: Complete blackout
class SpacedRepetitionService {
  // Minimum ease factor to prevent items from becoming too difficult
  static const double _minEaseFactor = 1.3;
  
  // Maximum quality history to keep (for performance)
  static const int _maxQualityHistory = 100;

  /// Process a review and update the item based on quality rating
  /// 
  /// [item] - The review item being processed
  /// [quality] - Quality rating from 0 (complete blackout) to 5 (perfect)
  /// 
  /// Returns updated ReviewItem with new interval, ease factor, and next review date
  ReviewItem processReview(ReviewItem item, int quality) {
    // Validate quality is in range 0-5
    final validQuality = quality.clamp(0, 5);
    
    // Calculate new ease factor
    final newEaseFactor = _calculateNewEaseFactor(item.easeFactor, validQuality);
    
    // Determine new repetitions count
    final newRepetitions = validQuality >= 3 ? item.repetitions + 1 : 0;
    
    // Calculate new interval based on SM-2 algorithm
    final newInterval = _calculateNewInterval(
      currentInterval: item.interval,
      repetitions: newRepetitions,
      easeFactor: newEaseFactor,
      quality: validQuality,
    );
    
    // Calculate next review date
    final nextReviewDate = DateTime.now().add(Duration(days: newInterval));
    
    // Update quality history (keep last N entries)
    final updatedHistory = [
      ...item.qualityHistory,
      validQuality,
    ];
    final trimmedHistory = updatedHistory.length > _maxQualityHistory
        ? updatedHistory.sublist(updatedHistory.length - _maxQualityHistory)
        : updatedHistory;
    
    return item.copyWith(
      easeFactor: newEaseFactor,
      interval: newInterval,
      repetitions: newRepetitions,
      nextReviewDate: nextReviewDate,
      lastReviewDate: DateTime.now(),
      qualityHistory: trimmedHistory,
    );
  }

  /// Calculate new ease factor using SM-2 formula
  /// EF' = EF + (0.1 - (5-q) * (0.08 + (5-q) * 0.02))
  double _calculateNewEaseFactor(double currentEF, int quality) {
    final newEF = currentEF + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02));
    
    // Ensure ease factor doesn't go below minimum
    return max(_minEaseFactor, newEF);
  }

  /// Calculate new interval based on SM-2 algorithm
  int _calculateNewInterval({
    required int currentInterval,
    required int repetitions,
    required double easeFactor,
    required int quality,
  }) {
    // If quality < 3, restart from beginning
    if (quality < 3) {
      return 0; // Review again immediately or very soon
    }
    
    // SM-2 interval calculation
    if (repetitions == 1) {
      return 1; // First successful review: 1 day
    } else if (repetitions == 2) {
      return 6; // Second successful review: 6 days
    } else {
      // Subsequent reviews: multiply previous interval by ease factor
      final newInterval = (currentInterval * easeFactor).round();
      return newInterval;
    }
  }

  /// Get all items that are due for review
  /// 
  /// [items] - List of all review items
  /// Returns list of items where nextReviewDate <= now
  List<ReviewItem> getDueItems(List<ReviewItem> items) {
    final now = DateTime.now();
    return items.where((item) => item.isDue).toList();
  }

  /// Sort items by priority/urgency
  /// 
  /// Priority order:
  /// 1. Overdue items (oldest first)
  /// 2. Due items
  /// 3. Items due soon (within 24 hours)
  /// 4. Other items (soonest first)
  /// 
  /// [items] - List of review items to sort
  /// Returns sorted list with highest priority items first
  List<ReviewItem> sortByPriority(List<ReviewItem> items) {
    final sortedItems = List<ReviewItem>.from(items);
    
    sortedItems.sort((a, b) {
      // Use urgency score for primary sorting
      final urgencyComparison = b.urgencyScore.compareTo(a.urgencyScore);
      if (urgencyComparison != 0) return urgencyComparison;

      // If same urgency, sort by next review date (earlier first)
      return a.nextReviewDate.compareTo(b.nextReviewDate);
    });

    return sortedItems;
  }

  /// Calculate estimated retention percentage for an item
  ///
  /// Uses a forgetting curve estimation based on:
  /// - Time since last review
  /// - Ease factor (item difficulty)
  /// - Success rate history
  ///
  /// [item] - The review item to calculate retention for
  /// Returns estimated retention percentage (0.0 to 1.0)
  double calculateRetention(ReviewItem item) {
    // New items have no retention data
    if (item.isNew) return 0.0;

    // If not yet due, retention is assumed high
    if (!item.isDue) return 0.95;

    // Calculate days since last review
    final daysSinceReview = item.lastReviewDate != null
        ? DateTime.now().difference(item.lastReviewDate!).inDays
        : item.interval;

    // Base retention using exponential decay (forgetting curve)
    // R(t) = e^(-t/S)
    // where t = time since review, S = stability (related to ease factor and interval)

    // Stability increases with ease factor and interval
    final stability = item.interval * (item.easeFactor / 2.5);

    // Calculate base retention
    final baseRetention = exp(-daysSinceReview / max(1, stability));

    // Adjust based on historical success rate
    final successRate = item.successRate;
    final adjustedRetention = baseRetention * (0.7 + (successRate * 0.3));

    // Clamp between 0 and 1
    return adjustedRetention.clamp(0.0, 1.0);
  }

  /// Get items that need review soon (within specified days)
  ///
  /// [items] - List of all review items
  /// [daysAhead] - Number of days to look ahead (default: 3)
  /// Returns list of items due within the specified timeframe
  List<ReviewItem> getUpcomingItems(List<ReviewItem> items, {int daysAhead = 3}) {
    final now = DateTime.now();
    final futureDate = now.add(Duration(days: daysAhead));

    return items.where((item) {
      return item.nextReviewDate.isAfter(now) &&
             item.nextReviewDate.isBefore(futureDate);
    }).toList();
  }

  /// Get statistics for a collection of review items
  ///
  /// [items] - List of review items to analyze
  /// Returns a map with various statistics
  Map<String, dynamic> getStatistics(List<ReviewItem> items) {
    if (items.isEmpty) {
      return {
        'totalItems': 0,
        'dueItems': 0,
        'overdueItems': 0,
        'newItems': 0,
        'averageEaseFactor': 0.0,
        'averageInterval': 0.0,
        'averageRetention': 0.0,
        'totalReviews': 0,
      };
    }

    final dueItems = getDueItems(items);
    final overdueItems = items.where((item) => item.isOverdue).length;
    final newItems = items.where((item) => item.isNew).length;

    final totalEF = items.fold<double>(0.0, (sum, item) => sum + item.easeFactor);
    final averageEF = totalEF / items.length;

    final totalInterval = items.fold<int>(0, (sum, item) => sum + item.interval);
    final averageInterval = totalInterval / items.length;

    final retentions = items.map((item) => calculateRetention(item)).toList();
    final averageRetention = retentions.reduce((a, b) => a + b) / retentions.length;

    final totalReviews = items.fold<int>(0, (sum, item) => sum + item.totalReviews);

    return {
      'totalItems': items.length,
      'dueItems': dueItems.length,
      'overdueItems': overdueItems,
      'newItems': newItems,
      'averageEaseFactor': averageEF,
      'averageInterval': averageInterval,
      'averageRetention': averageRetention,
      'totalReviews': totalReviews,
    };
  }

  /// Get items filtered by difficulty level
  ///
  /// [items] - List of review items to filter
  /// [difficulty] - Difficulty level: 'easy', 'medium', or 'hard'
  /// Returns filtered list of items matching the difficulty
  List<ReviewItem> getItemsByDifficulty(List<ReviewItem> items, String difficulty) {
    return items.where((item) => item.difficultyLevel == difficulty).toList();
  }

  /// Get items filtered by category
  ///
  /// [items] - List of review items to filter
  /// [category] - Category name to filter by
  /// Returns filtered list of items in the specified category
  List<ReviewItem> getItemsByCategory(List<ReviewItem> items, String category) {
    return items.where((item) => item.category == category).toList();
  }

  /// Calculate optimal daily review count based on total items
  ///
  /// [totalItems] - Total number of items in the system
  /// Returns recommended number of daily reviews
  int getRecommendedDailyReviews(int totalItems) {
    if (totalItems <= 20) return 5;
    if (totalItems <= 50) return 10;
    if (totalItems <= 100) return 15;
    if (totalItems <= 200) return 20;
    return 25; // Cap at 25 reviews per day
  }

  /// Reset an item back to initial state
  /// Useful for items that need to be relearned from scratch
  ///
  /// [item] - The review item to reset
  /// [preserveHistory] - Whether to keep quality history (default: false)
  /// Returns reset ReviewItem
  ReviewItem resetItem(ReviewItem item, {bool preserveHistory = false}) {
    return item.copyWith(
      easeFactor: 2.5,
      interval: 0,
      repetitions: 0,
      nextReviewDate: DateTime.now(),
      lastReviewDate: null,
      qualityHistory: preserveHistory ? item.qualityHistory : [],
    );
  }
}

