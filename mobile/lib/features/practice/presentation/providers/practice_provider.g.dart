// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'practice_provider.dart';

// **************************************************************************
// RiverpodGenerator
// **************************************************************************

String _$practiceSessionHash() => r'46a461d9dee70bfb544bc5f303e0d6624a97d5b0';

/// Practice session notifier
///
/// Copied from [PracticeSession].
@ProviderFor(PracticeSession)
final practiceSessionProvider =
    AutoDisposeNotifierProvider<PracticeSession, PracticeSessionState>.internal(
  PracticeSession.new,
  name: r'practiceSessionProvider',
  debugGetCreateSourceHash: const bool.fromEnvironment('dart.vm.product')
      ? null
      : _$practiceSessionHash,
  dependencies: null,
  allTransitiveDependencies: null,
);

typedef _$PracticeSession = AutoDisposeNotifier<PracticeSessionState>;
String _$dailyPracticeStatsHash() =>
    r'5b36ea024a2cb2ebedb26de4fdea4f0d2e337d0d';

/// Provider for daily practice stats
///
/// Copied from [DailyPracticeStats].
@ProviderFor(DailyPracticeStats)
final dailyPracticeStatsProvider =
    AutoDisposeNotifierProvider<DailyPracticeStats, Map<String, int>>.internal(
  DailyPracticeStats.new,
  name: r'dailyPracticeStatsProvider',
  debugGetCreateSourceHash: const bool.fromEnvironment('dart.vm.product')
      ? null
      : _$dailyPracticeStatsHash,
  dependencies: null,
  allTransitiveDependencies: null,
);

typedef _$DailyPracticeStats = AutoDisposeNotifier<Map<String, int>>;
// ignore_for_file: type=lint
// ignore_for_file: subtype_of_sealed_class, invalid_use_of_internal_member, invalid_use_of_visible_for_testing_member, deprecated_member_use_from_same_package
