import 'package:flutter_test/flutter_test.dart';
import 'package:luuniensuki_lms/features/practice/domain/models/review_item.dart';
import 'package:luuniensuki_lms/features/practice/domain/services/spaced_repetition_service.dart';

void main() {
  late SpacedRepetitionService service;

  setUp(() {
    service = SpacedRepetitionService();
  });

  group('processReview', () {
    test('handles quality 5 (perfect response)', () {
      final item = ReviewItem.initial(motifId: 'motif1');
      final result = service.processReview(item, 5);

      expect(result.repetitions, 1);
      expect(result.easeFactor, greaterThan(2.5));
      expect(result.interval, 1);
      expect(result.qualityHistory.last, 5);
    });

    test('handles quality 4 (correct with hesitation)', () {
      final item = ReviewItem.initial(motifId: 'motif1');
      final result = service.processReview(item, 4);

      expect(result.repetitions, 1);
      expect(result.easeFactor, greaterThanOrEqualTo(2.5));
      expect(result.interval, 1);
      expect(result.qualityHistory.last, 4);
    });

    test('handles quality 3 (correct with difficulty)', () {
      final item = ReviewItem.initial(motifId: 'motif1');
      final result = service.processReview(item, 3);

      expect(result.repetitions, 1);
      expect(result.easeFactor, lessThan(2.5));
      expect(result.interval, 1);
      expect(result.qualityHistory.last, 3);
    });

    test('handles quality 2 (incorrect, resets repetitions)', () {
      final item = ReviewItem(
        motifId: 'motif1',
        easeFactor: 2.5,
        interval: 6,
        repetitions: 2,
        nextReviewDate: DateTime.now(),
      );
      final result = service.processReview(item, 2);

      expect(result.repetitions, 0);
      expect(result.interval, 0);
      expect(result.qualityHistory.last, 2);
    });

    test('handles quality 1 (incorrect hard recall, resets repetitions)', () {
      final item = ReviewItem(
        motifId: 'motif1',
        easeFactor: 2.5,
        interval: 10,
        repetitions: 3,
        nextReviewDate: DateTime.now(),
      );
      final result = service.processReview(item, 1);

      expect(result.repetitions, 0);
      expect(result.interval, 0);
      expect(result.qualityHistory.last, 1);
    });

    test('handles quality 0 (complete blackout, resets repetitions)', () {
      final item = ReviewItem(
        motifId: 'motif1',
        easeFactor: 2.5,
        interval: 15,
        repetitions: 5,
        nextReviewDate: DateTime.now(),
      );
      final result = service.processReview(item, 0);

      expect(result.repetitions, 0);
      expect(result.interval, 0);
      expect(result.qualityHistory.last, 0);
    });

    test('quality < 3 resets repetitions to 0', () {
      final item = ReviewItem(
        motifId: 'motif1',
        easeFactor: 2.5,
        interval: 10,
        repetitions: 5,
        nextReviewDate: DateTime.now(),
      );

      final result0 = service.processReview(item, 0);
      final result1 = service.processReview(item, 1);
      final result2 = service.processReview(item, 2);

      expect(result0.repetitions, 0);
      expect(result1.repetitions, 0);
      expect(result2.repetitions, 0);
    });

    test('quality >= 3 increments repetitions', () {
      final item = ReviewItem(
        motifId: 'motif1',
        easeFactor: 2.5,
        interval: 1,
        repetitions: 2,
        nextReviewDate: DateTime.now(),
      );

      final result3 = service.processReview(item, 3);
      final result4 = service.processReview(item, 4);
      final result5 = service.processReview(item, 5);

      expect(result3.repetitions, 3);
      expect(result4.repetitions, 3);
      expect(result5.repetitions, 3);
    });

    test('clamps quality values outside 0-5 range', () {
      final item = ReviewItem.initial(motifId: 'motif1');

      final resultNegative = service.processReview(item, -1);
      final resultTooHigh = service.processReview(item, 10);

      expect(resultNegative.qualityHistory.last, 0);
      expect(resultTooHigh.qualityHistory.last, 5);
    });

    test('updates lastReviewDate and nextReviewDate', () {
      final item = ReviewItem.initial(motifId: 'motif1');
      final beforeReview = DateTime.now();
      final result = service.processReview(item, 4);

      expect(result.lastReviewDate, isNotNull);
      expect(result.lastReviewDate!.isAfter(beforeReview.subtract(Duration(seconds: 1))), true);
      expect(result.nextReviewDate.isAfter(DateTime.now()), true);
    });

    test('maintains quality history with max limit', () {
      var item = ReviewItem.initial(motifId: 'motif1');

      for (int i = 0; i < 110; i++) {
        item = service.processReview(item, 3 + (i % 3));
      }

      expect(item.qualityHistory.length, lessThanOrEqualTo(100));
    });
  });

  group('calculateNewEaseFactor', () {
    test('quality 5 increases ease factor', () {
      final item = ReviewItem.initial(motifId: 'motif1');
      final result = service.processReview(item, 5);

      // EF' = 2.5 + (0.1 - (5-5) * (0.08 + (5-5) * 0.02))
      // EF' = 2.5 + 0.1 = 2.6
      expect(result.easeFactor, 2.6);
    });

    test('quality 4 maintains or slightly increases ease factor', () {
      final item = ReviewItem.initial(motifId: 'motif1');
      final result = service.processReview(item, 4);

      // EF' = 2.5 + (0.1 - (5-4) * (0.08 + (5-4) * 0.02))
      // EF' = 2.5 + (0.1 - 1 * 0.10) = 2.5
      expect(result.easeFactor, 2.5);
    });

    test('quality 3 decreases ease factor', () {
      final item = ReviewItem.initial(motifId: 'motif1');
      final result = service.processReview(item, 3);

      // EF' = 2.5 + (0.1 - (5-3) * (0.08 + (5-3) * 0.02))
      // EF' = 2.5 + (0.1 - 2 * 0.12) = 2.5 - 0.14 = 2.36
      expect(result.easeFactor, closeTo(2.36, 0.01));
    });

    test('quality 2 decreases ease factor more', () {
      final item = ReviewItem.initial(motifId: 'motif1');
      final result = service.processReview(item, 2);

      // EF' = 2.5 + (0.1 - (5-2) * (0.08 + (5-2) * 0.02))
      // EF' = 2.5 + (0.1 - 3 * 0.14) = 2.5 - 0.32 = 2.18
      expect(result.easeFactor, closeTo(2.18, 0.01));
    });

    test('quality 0 significantly decreases ease factor', () {
      final item = ReviewItem.initial(motifId: 'motif1');
      final result = service.processReview(item, 0);

      // EF' = 2.5 + (0.1 - (5-0) * (0.08 + (5-0) * 0.02))
      // EF' = 2.5 + (0.1 - 5 * 0.18) = 2.5 - 0.8 = 1.7
      expect(result.easeFactor, closeTo(1.7, 0.01));
    });

    test('ease factor never goes below minimum (1.3)', () {
      var item = ReviewItem.initial(motifId: 'motif1');

      // Process multiple poor quality reviews to try to push below minimum
      for (int i = 0; i < 10; i++) {
        item = service.processReview(item, 0);
      }

      expect(item.easeFactor, greaterThanOrEqualTo(1.3));
    });

    test('EF formula verification: EF\' = EF + (0.1 - (5-q) * (0.08 + (5-q) * 0.02))', () {
      const startingEF = 2.5;

      for (int quality = 0; quality <= 5; quality++) {
        final item = ReviewItem(
          motifId: 'motif1',
          easeFactor: startingEF,
          interval: 1,
          repetitions: 1,
          nextReviewDate: DateTime.now(),
        );
        final result = service.processReview(item, quality);

        final expectedEF = startingEF + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02));
        final expectedEFClamped = expectedEF < 1.3 ? 1.3 : expectedEF;

        expect(result.easeFactor, closeTo(expectedEFClamped, 0.01));
      }
    });
  });

  group('calculateNewInterval', () {
    test('first successful review (repetitions = 1) sets interval to 1 day', () {
      final item = ReviewItem.initial(motifId: 'motif1');
      final result = service.processReview(item, 4);

      expect(result.repetitions, 1);
      expect(result.interval, 1);
    });

    test('second successful review (repetitions = 2) sets interval to 6 days', () {
      final item = ReviewItem(
        motifId: 'motif1',
        easeFactor: 2.5,
        interval: 1,
        repetitions: 1,
        nextReviewDate: DateTime.now(),
      );
      final result = service.processReview(item, 4);

      expect(result.repetitions, 2);
      expect(result.interval, 6);
    });

    test('third successful review multiplies interval by ease factor', () {
      final item = ReviewItem(
        motifId: 'motif1',
        easeFactor: 2.5,
        interval: 6,
        repetitions: 2,
        nextReviewDate: DateTime.now(),
      );
      final result = service.processReview(item, 4);

      expect(result.repetitions, 3);
      // interval = 6 * 2.5 = 15
      expect(result.interval, 15);
    });

    test('interval progression: 1 -> 6 -> EF multiplied', () {
      var item = ReviewItem.initial(motifId: 'motif1');

      // First review
      item = service.processReview(item, 4);
      expect(item.interval, 1);
      expect(item.repetitions, 1);

      // Second review
      item = service.processReview(item, 4);
      expect(item.interval, 6);
      expect(item.repetitions, 2);

      // Third review with EF = 2.5
      item = service.processReview(item, 4);
      expect(item.interval, 15); // 6 * 2.5 = 15

      // Fourth review
      item = service.processReview(item, 4);
      expect(item.interval, closeTo(37.5, 1)); // 15 * 2.5 = 37.5, rounded
    });

    test('quality < 3 resets interval to 0', () {
      final item = ReviewItem(
        motifId: 'motif1',
        easeFactor: 2.5,
        interval: 15,
        repetitions: 5,
        nextReviewDate: DateTime.now(),
      );

      final result0 = service.processReview(item, 0);
      final result1 = service.processReview(item, 1);
      final result2 = service.processReview(item, 2);

      expect(result0.interval, 0);
      expect(result1.interval, 0);
      expect(result2.interval, 0);
    });

    test('interval grows exponentially with higher ease factor', () {
      var item = ReviewItem(
        motifId: 'motif1',
        easeFactor: 3.0,
        interval: 6,
        repetitions: 2,
        nextReviewDate: DateTime.now(),
      );

      // Third review: 6 * 3.0 = 18
      item = service.processReview(item, 5);
      expect(item.interval, 18);

      // Fourth review: 18 * 3.0 = 54
      item = service.processReview(item, 5);
      expect(item.interval, 54);
    });

    test('interval grows slower with lower ease factor', () {
      var item = ReviewItem(
        motifId: 'motif1',
        easeFactor: 1.5,
        interval: 6,
        repetitions: 2,
        nextReviewDate: DateTime.now(),
      );

      // Third review: 6 * 1.5 = 9
      item = service.processReview(item, 3);
      expect(item.interval, closeTo(9, 1));
    });
  });
}