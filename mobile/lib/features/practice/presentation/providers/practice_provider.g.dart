// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'practice_provider.dart';

// **************************************************************************
// RiverpodGenerator
// **************************************************************************

String _$practiceSessionHash() => r'85384e7be5ec169dd3c630133177b53e970de30b';

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
    r'99f1826768bc8b65091d992bd80adf32afb87e64';

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
