import 'package:flutter_test/flutter_test.dart';
import 'package:luuniensuki_lms/core/constants/app_constants.dart';
import 'package:luuniensuki_lms/features/lesson/domain/lesson_models.dart';

void main() {
  group('T-U2: Progress Calculation Tests', () {
    group('XP Calculation for Different Actions', () {
      test('should calculate XP for discovery action (25 XP)', () {
        const xp = AppConstants.discoveryXp;

        expect(xp, 25);
      });

      test('should calculate XP for lesson completion (50 XP)', () {
        const xp = AppConstants.lessonXp;

        expect(xp, 50);
      });

      test('should calculate XP for quiz mastery (75 XP)', () {
        const xp = AppConstants.masteredXp;

        expect(xp, 75);
      });

      test('should calculate cumulative XP for discovered status', () {
        const progress = UserProgress(
          id: '1',
          oderId: 'order1',
          motifId: 'motif1',
          status: ProgressStatus.discovered,
          xpEarned: 25,
        );

        expect(progress.expectedXp, 25);
        expect(progress.status, ProgressStatus.discovered);
      });

      test('should calculate cumulative XP for learned status', () {
        const progress = UserProgress(
          id: '1',
          oderId: 'order1',
          motifId: 'motif1',
          status: ProgressStatus.learned,
          xpEarned: 75,
        );

        expect(progress.expectedXp, 75);
        expect(progress.status, ProgressStatus.learned);
      });

      test('should calculate cumulative XP for mastered status', () {
        const progress = UserProgress(
          id: '1',
          oderId: 'order1',
          motifId: 'motif1',
          status: ProgressStatus.mastered,
          xpEarned: 150,
        );

        expect(progress.expectedXp, 150);
        expect(progress.status, ProgressStatus.mastered);
      });

      test('should have 0 XP for hidden status', () {
        const progress = UserProgress(
          id: '1',
          oderId: 'order1',
          motifId: 'motif1',
          status: ProgressStatus.hidden,
          xpEarned: 0,
        );

        expect(progress.expectedXp, 0);
        expect(progress.status, ProgressStatus.hidden);
      });
    });

    group('Rank Progression Based on XP Thresholds', () {
      test('should return correct rank for 0 XP (Lính Mới)', () {
        final rank = AppConstants.getRankForXp(0);

        expect(rank['level'], 1);
        expect(rank['name'], 'Lính Mới');
        expect(rank['xp'], 0);
      });

      test('should return correct rank for 100 XP (Học Viên)', () {
        final rank = AppConstants.getRankForXp(100);

        expect(rank['level'], 2);
        expect(rank['name'], 'Học Viên');
        expect(rank['xp'], 100);
      });

      test('should return correct rank for 300 XP (Thư Sinh)', () {
        final rank = AppConstants.getRankForXp(300);

        expect(rank['level'], 3);
        expect(rank['name'], 'Thư Sinh');
        expect(rank['xp'], 300);
      });

      test('should return correct rank for 600 XP (Tri Huyện)', () {
        final rank = AppConstants.getRankForXp(600);

        expect(rank['level'], 4);
        expect(rank['name'], 'Tri Huyện');
        expect(rank['xp'], 600);
      });

      test('should return correct rank for 1000 XP (Tiến Sĩ)', () {
        final rank = AppConstants.getRankForXp(1000);

        expect(rank['level'], 5);
        expect(rank['name'], 'Tiến Sĩ');
        expect(rank['xp'], 1000);
      });

      test('should return correct rank for 1500 XP (Thượng Thư)', () {
        final rank = AppConstants.getRankForXp(1500);

        expect(rank['level'], 6);
        expect(rank['name'], 'Thượng Thư');
        expect(rank['xp'], 1500);
      });

      test('should return correct rank for 2100 XP (Thái Tử)', () {
        final rank = AppConstants.getRankForXp(2100);

        expect(rank['level'], 7);
        expect(rank['name'], 'Thái Tử');
        expect(rank['xp'], 2100);
      });

      test('should return correct rank for 2800 XP (Hoàng Đế)', () {
        final rank = AppConstants.getRankForXp(2800);

        expect(rank['level'], 8);
        expect(rank['name'], 'Hoàng Đế');
        expect(rank['xp'], 2800);
      });

      test('should return correct rank for 3600 XP (Sử Quan)', () {
        final rank = AppConstants.getRankForXp(3600);

        expect(rank['level'], 9);
        expect(rank['name'], 'Sử Quan');
        expect(rank['xp'], 3600);
      });

      test('should return first rank for XP below first threshold', () {
        final rank = AppConstants.getRankForXp(50);

        expect(rank['level'], 1);
        expect(rank['name'], 'Lính Mới');
      });

      test('should return correct rank for XP between thresholds', () {
        final rank = AppConstants.getRankForXp(250);

        expect(rank['level'], 2);
        expect(rank['name'], 'Học Viên');
      });
    });

    group('Next Rank Calculation', () {
      test('should return next rank for user at level 1', () {
        final nextRank = AppConstants.getNextRank(50);

        expect(nextRank, isNotNull);
        expect(nextRank!['level'], 2);
        expect(nextRank['name'], 'Học Viên');
        expect(nextRank['xp'], 100);
      });

      test('should return next rank for user at level 5', () {
        final nextRank = AppConstants.getNextRank(1200);

        expect(nextRank, isNotNull);
        expect(nextRank!['level'], 6);
        expect(nextRank['name'], 'Thượng Thư');
        expect(nextRank['xp'], 1500);
      });

      test('should return null when user is at max rank', () {
        final nextRank = AppConstants.getNextRank(5000);

        expect(nextRank, isNull);
      });
    });

    group('Level Up Detection', () {
      test('should detect level up when XP crosses threshold', () {
        final didLevelUp = AppConstants.didLevelUp(95, 105);

        expect(didLevelUp, true);
      });

      test('should not detect level up when XP stays in same range', () {
        final didLevelUp = AppConstants.didLevelUp(150, 200);

        expect(didLevelUp, false);
      });

      test('should detect multiple level up jumps', () {
        final didLevelUp = AppConstants.didLevelUp(50, 350);

        expect(didLevelUp, true);
      });

      test('should not detect level up when XP stays at same level', () {
        final didLevelUp = AppConstants.didLevelUp(600, 650);

        expect(didLevelUp, false);
      });
    });

    group('Progress Percentage Calculations', () {
      test('should calculate 0% progress at rank minimum', () {
        const totalXp = 100;
        final rank = AppConstants.getRankForXp(totalXp);
        final nextRank = AppConstants.getNextRank(totalXp);

        final xpInCurrentRank = totalXp - rank['xp'];
        final xpNeededForNext = nextRank!['xp'] - rank['xp'];
        final progress = (xpInCurrentRank / xpNeededForNext) * 100;

        expect(progress, 0.0);
      });

      test('should calculate 50% progress at midpoint', () {
        const totalXp = 200;
        final rank = AppConstants.getRankForXp(totalXp);
        final nextRank = AppConstants.getNextRank(totalXp);

        final xpInCurrentRank = totalXp - rank['xp'];
        final xpNeededForNext = nextRank!['xp'] - rank['xp'];
        final progress = (xpInCurrentRank / xpNeededForNext) * 100;

        expect(progress, 50.0);
      });

      test('should calculate 100% progress just before level up', () {
        const totalXp = 299;
        final rank = AppConstants.getRankForXp(totalXp);
        final nextRank = AppConstants.getNextRank(totalXp);

        final xpInCurrentRank = totalXp - rank['xp'];
        final xpNeededForNext = nextRank!['xp'] - rank['xp'];
        final progress = (xpInCurrentRank / xpNeededForNext) * 100;

        expect(progress, closeTo(99.5, 0.5));
      });

      test('should handle progress calculation at max rank', () {
        const totalXp = 5000;
        final rank = AppConstants.getRankForXp(totalXp);
        final nextRank = AppConstants.getNextRank(totalXp);

        expect(rank['level'], 9);
        expect(nextRank, isNull);
      });
    });
  });
}

