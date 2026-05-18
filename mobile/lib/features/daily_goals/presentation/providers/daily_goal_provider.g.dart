// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'daily_goal_provider.dart';

// **************************************************************************
// RiverpodGenerator
// **************************************************************************

String _$dailyGoalNotifierHash() => r'9e1d6a40747da022095eaf78c04b0a610957fa15';

/// Daily goal state management
///
/// Copied from [DailyGoalNotifier].
@ProviderFor(DailyGoalNotifier)
final dailyGoalNotifierProvider =
    NotifierProvider<DailyGoalNotifier, DailyGoal>.internal(
  DailyGoalNotifier.new,
  name: r'dailyGoalNotifierProvider',
  debugGetCreateSourceHash: const bool.fromEnvironment('dart.vm.product')
      ? null
      : _$dailyGoalNotifierHash,
  dependencies: null,
  allTransitiveDependencies: null,
);

typedef _$DailyGoalNotifier = Notifier<DailyGoal>;
String _$dailyGoalXpSyncHash() => r'de9d363015a1d80b498edd5c8256c171d3166ff3';

/// Provider that watches for XP changes and updates daily goal
///
/// Copied from [DailyGoalXpSync].
@ProviderFor(DailyGoalXpSync)
final dailyGoalXpSyncProvider =
    AutoDisposeNotifierProvider<DailyGoalXpSync, void>.internal(
  DailyGoalXpSync.new,
  name: r'dailyGoalXpSyncProvider',
  debugGetCreateSourceHash: const bool.fromEnvironment('dart.vm.product')
      ? null
      : _$dailyGoalXpSyncHash,
  dependencies: null,
  allTransitiveDependencies: null,
);

typedef _$DailyGoalXpSync = AutoDisposeNotifier<void>;
// ignore_for_file: type=lint
// ignore_for_file: subtype_of_sealed_class, invalid_use_of_internal_member, invalid_use_of_visible_for_testing_member, deprecated_member_use_from_same_package
