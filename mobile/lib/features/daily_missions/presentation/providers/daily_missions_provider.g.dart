// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'daily_missions_provider.dart';

// **************************************************************************
// RiverpodGenerator
// **************************************************************************

String _$dailyMissionsListHash() => r'a29f9839464c43b61ac0b0142065d61b8dc0b537';

/// Provider to get missions list
///
/// Copied from [dailyMissionsList].
@ProviderFor(dailyMissionsList)
final dailyMissionsListProvider =
    AutoDisposeProvider<List<DailyMission>>.internal(
  dailyMissionsList,
  name: r'dailyMissionsListProvider',
  debugGetCreateSourceHash: const bool.fromEnvironment('dart.vm.product')
      ? null
      : _$dailyMissionsListHash,
  dependencies: null,
  allTransitiveDependencies: null,
);

@Deprecated('Will be removed in 3.0. Use Ref instead')
// ignore: unused_element
typedef DailyMissionsListRef = AutoDisposeProviderRef<List<DailyMission>>;
String _$completedMissionsCountHash() =>
    r'9ecab7b4481ea63ac181b2398987daf0cd0f223b';

/// Provider to get completed missions count
///
/// Copied from [completedMissionsCount].
@ProviderFor(completedMissionsCount)
final completedMissionsCountProvider = AutoDisposeProvider<int>.internal(
  completedMissionsCount,
  name: r'completedMissionsCountProvider',
  debugGetCreateSourceHash: const bool.fromEnvironment('dart.vm.product')
      ? null
      : _$completedMissionsCountHash,
  dependencies: null,
  allTransitiveDependencies: null,
);

@Deprecated('Will be removed in 3.0. Use Ref instead')
// ignore: unused_element
typedef CompletedMissionsCountRef = AutoDisposeProviderRef<int>;
String _$totalXpTodayHash() => r'ef54379cfb6648785cb347c35803f90626840770';

/// Provider to get total XP earned today
///
/// Copied from [totalXpToday].
@ProviderFor(totalXpToday)
final totalXpTodayProvider = AutoDisposeProvider<int>.internal(
  totalXpToday,
  name: r'totalXpTodayProvider',
  debugGetCreateSourceHash:
      const bool.fromEnvironment('dart.vm.product') ? null : _$totalXpTodayHash,
  dependencies: null,
  allTransitiveDependencies: null,
);

@Deprecated('Will be removed in 3.0. Use Ref instead')
// ignore: unused_element
typedef TotalXpTodayRef = AutoDisposeProviderRef<int>;
String _$dailyMissionsNotifierHash() =>
    r'40d2c6b73d52e79f09ddcf37f2f251e743461aa7';

/// Provider for daily missions
///
/// Copied from [DailyMissionsNotifier].
@ProviderFor(DailyMissionsNotifier)
final dailyMissionsNotifierProvider = AutoDisposeNotifierProvider<
    DailyMissionsNotifier, DailyMissionsState>.internal(
  DailyMissionsNotifier.new,
  name: r'dailyMissionsNotifierProvider',
  debugGetCreateSourceHash: const bool.fromEnvironment('dart.vm.product')
      ? null
      : _$dailyMissionsNotifierHash,
  dependencies: null,
  allTransitiveDependencies: null,
);

typedef _$DailyMissionsNotifier = AutoDisposeNotifier<DailyMissionsState>;
// ignore_for_file: type=lint
// ignore_for_file: subtype_of_sealed_class, invalid_use_of_internal_member, invalid_use_of_visible_for_testing_member, deprecated_member_use_from_same_package
