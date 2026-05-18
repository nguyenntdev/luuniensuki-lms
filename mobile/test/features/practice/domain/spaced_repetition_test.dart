import 'package:flutter_test/flutter_test.dart';
import 'package:luuniensuki_lms/features/practice/domain/models/review_item.dart';
import 'package:luuniensuki_lms/features/practice/domain/services/spaced_repetition_service.dart';

/// Example test file for SM-2 spaced repetition algorithm
/// 
/// Run with: flutter test test/features/practice/domain/spaced_repetition_test.dart
void main() {
  group('SpacedRepetitionService', () {
    late SpacedRepetitionService service;

    setUp(() {
      service = SpacedRepetitionService();
    });

    test('processReview with quality 5 should increase ease factor', () {
      final item = ReviewItem.initial(
        motifId: 'test_motif_1',
        motifTitle: 'Họa tiết rồng',
        category: 'Linh Thú',
      );

      final updated = service.processReview(item, 5);

      expect(updated.easeFactor, greaterThan(item.easeFactor));
      expect(updated.interval, equals(1)); // First successful review
      expect(updated.repetitions, equals(1));
      expect(updated.qualityHistory, equals([5]));
      expect(updated.lastReviewDate, isNotNull);
    });

    test('processReview with quality 4 should slightly increase ease factor', () {
      final item = ReviewItem.initial(motifId: 'test_motif_2');
      final updated = service.processReview(item, 4);

      expect(updated.easeFactor, lessThan(2.5)); // Quality 4 decreases from 2.5
      expect(updated.interval, equals(1));
      expect(updated.repetitions, equals(1));
    });

    test('processReview with quality < 3 should reset repetitions', () {
      var item = ReviewItem.initial(motifId: 'test_motif_3');
      
      // Build up some progress
      item = service.processReview(item, 5); // Rep 1, interval 1
      item = service.processReview(item, 5); // Rep 2, interval 6
      item = service.processReview(item, 5); // Rep 3, interval ~15
      
      // Now fail the review
      item = service.processReview(item, 2);

      expect(item.repetitions, equals(0));
      expect(item.interval, equals(0));
      expect(item.qualityHistory.last, equals(2));
    });

    test('SM-2 interval progression should follow algorithm', () {
      var item = ReviewItem.initial(motifId: 'test_motif_4');

      // First review (quality 5)
      item = service.processReview(item, 5);
      expect(item.interval, equals(1)); // 1 day
      expect(item.repetitions, equals(1));

      // Second review (quality 5)
      item = service.processReview(item, 5);
      expect(item.interval, equals(6)); // 6 days
      expect(item.repetitions, equals(2));

      // Third review (quality 4)
      final thirdItem = service.processReview(item, 4);
      expect(thirdItem.interval, greaterThan(6)); // Should be interval * EF
      expect(thirdItem.repetitions, equals(3));
    });

    test('getDueItems should return only due items', () {
      final now = DateTime.now();
      final items = [
        ReviewItem.initial(motifId: 'due_1')
            .copyWith(nextReviewDate: now.subtract(Duration(days: 1))),
        ReviewItem.initial(motifId: 'due_2')
            .copyWith(nextReviewDate: now),
        ReviewItem.initial(motifId: 'not_due')
            .copyWith(nextReviewDate: now.add(Duration(days: 1))),
      ];

      final dueItems = service.getDueItems(items);

      expect(dueItems.length, equals(2));
      expect(dueItems.any((item) => item.motifId == 'due_1'), isTrue);
      expect(dueItems.any((item) => item.motifId == 'due_2'), isTrue);
      expect(dueItems.any((item) => item.motifId == 'not_due'), isFalse);
    });

    test('sortByPriority should prioritize overdue items', () {
      final now = DateTime.now();
      final items = [
        ReviewItem.initial(motifId: 'future')
            .copyWith(nextReviewDate: now.add(Duration(days: 5))),
        ReviewItem.initial(motifId: 'due_now')
            .copyWith(nextReviewDate: now),
        ReviewItem.initial(motifId: 'overdue_3_days')
            .copyWith(nextReviewDate: now.subtract(Duration(days: 3))),
        ReviewItem.initial(motifId: 'overdue_1_day')
            .copyWith(nextReviewDate: now.subtract(Duration(days: 1))),
      ];

      final sorted = service.sortByPriority(items);

      expect(sorted[0].motifId, equals('overdue_3_days')); // Most overdue first
      expect(sorted[1].motifId, equals('overdue_1_day'));
      expect(sorted[2].motifId, equals('due_now'));
      expect(sorted[3].motifId, equals('future'));
    });

    test('calculateRetention should return reasonable values', () {
      var item = ReviewItem.initial(motifId: 'test_retention');
      
      // New items have no retention
      expect(service.calculateRetention(item), equals(0.0));

      // After a successful review, retention should be high
      item = service.processReview(item, 5);
      expect(service.calculateRetention(item), greaterThan(0.9));
    });

    test('getStatistics should return correct statistics', () {
      final now = DateTime.now();
      final items = [
        ReviewItem.initial(motifId: '1')
            .copyWith(nextReviewDate: now.subtract(Duration(days: 2))),
        ReviewItem.initial(motifId: '2')
            .copyWith(nextReviewDate: now),
        ReviewItem.initial(motifId: '3')
            .copyWith(nextReviewDate: now.add(Duration(days: 1))),
        ReviewItem.initial(motifId: '4'),
      ];

      final stats = service.getStatistics(items);

      expect(stats['totalItems'], equals(4));
      expect(stats['dueItems'], equals(2)); // Items 1 and 2
      expect(stats['overdueItems'], equals(1)); // Item 1
      expect(stats['newItems'], equals(4)); // All are new
      expect(stats['averageEaseFactor'], equals(2.5)); // Default
    });

    test('getUpcomingItems should return items due within specified days', () {
      final now = DateTime.now();
      final items = [
        ReviewItem.initial(motifId: 'tomorrow')
            .copyWith(nextReviewDate: now.add(Duration(days: 1))),
        ReviewItem.initial(motifId: 'in_2_days')
            .copyWith(nextReviewDate: now.add(Duration(days: 2))),
        ReviewItem.initial(motifId: 'in_5_days')
            .copyWith(nextReviewDate: now.add(Duration(days: 5))),
      ];

      final upcoming = service.getUpcomingItems(items, daysAhead: 3);

      expect(upcoming.length, equals(2));
      expect(upcoming.any((item) => item.motifId == 'tomorrow'), isTrue);
      expect(upcoming.any((item) => item.motifId == 'in_2_days'), isTrue);
      expect(upcoming.any((item) => item.motifId == 'in_5_days'), isFalse);
    });

    test('resetItem should restore initial state', () {
      var item = ReviewItem.initial(motifId: 'test_reset');
      
      // Build up some progress
      item = service.processReview(item, 5);
      item = service.processReview(item, 5);
      item = service.processReview(item, 4);

      expect(item.repetitions, greaterThan(0));
      expect(item.qualityHistory, isNotEmpty);

      // Reset without preserving history
      final resetItem = service.resetItem(item);

      expect(resetItem.easeFactor, equals(2.5));
      expect(resetItem.interval, equals(0));
      expect(resetItem.repetitions, equals(0));
      expect(resetItem.lastReviewDate, isNull);
      expect(resetItem.qualityHistory, isEmpty);
    });
  });

  group('ReviewItem', () {
    test('isDue should correctly identify due items', () {
      final now = DateTime.now();
      
      final overdueItem = ReviewItem.initial(motifId: '1')
          .copyWith(nextReviewDate: now.subtract(Duration(hours: 1)));
      final dueNowItem = ReviewItem.initial(motifId: '2')
          .copyWith(nextReviewDate: now);
      final futureItem = ReviewItem.initial(motifId: '3')
          .copyWith(nextReviewDate: now.add(Duration(hours: 1)));

      expect(overdueItem.isDue, isTrue);
      expect(dueNowItem.isDue, isTrue);
      expect(futureItem.isDue, isFalse);
    });

    test('difficultyLevel should correctly categorize items', () {
      final easyItem = ReviewItem.initial(motifId: '1')
          .copyWith(easeFactor: 2.5);
      final mediumItem = ReviewItem.initial(motifId: '2')
          .copyWith(easeFactor: 2.2);
      final hardItem = ReviewItem.initial(motifId: '3')
          .copyWith(easeFactor: 1.5);

      expect(easyItem.difficultyLevel, equals('easy'));
      expect(mediumItem.difficultyLevel, equals('medium'));
      expect(hardItem.difficultyLevel, equals('hard'));
    });

    test('successRate should calculate correctly', () {
      final item = ReviewItem.initial(motifId: '1')
          .copyWith(qualityHistory: [5, 4, 3, 2, 5, 4]); // 5 successful (>=3), 1 failed

      expect(item.successRate, closeTo(5 / 6, 0.01));
    });
  });
}

