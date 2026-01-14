// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'hearts_provider.dart';

// **************************************************************************
// RiverpodGenerator
// **************************************************************************

String _$hasHeartsHash() => r'17e1adb6fef7a223f012c9891f86ed7f24604c44';

/// Helper provider to check if user has hearts
///
/// Copied from [hasHearts].
@ProviderFor(hasHearts)
final hasHeartsProvider = AutoDisposeProvider<bool>.internal(
  hasHearts,
  name: r'hasHeartsProvider',
  debugGetCreateSourceHash:
      const bool.fromEnvironment('dart.vm.product') ? null : _$hasHeartsHash,
  dependencies: null,
  allTransitiveDependencies: null,
);

@Deprecated('Will be removed in 3.0. Use Ref instead')
// ignore: unused_element
typedef HasHeartsRef = AutoDisposeProviderRef<bool>;
String _$currentHeartsHash() => r'9c1269aa4bc1736612673612db8cb45bc26e874a';

/// Helper provider to get current hearts count
///
/// Copied from [currentHearts].
@ProviderFor(currentHearts)
final currentHeartsProvider = AutoDisposeProvider<int>.internal(
  currentHearts,
  name: r'currentHeartsProvider',
  debugGetCreateSourceHash: const bool.fromEnvironment('dart.vm.product')
      ? null
      : _$currentHeartsHash,
  dependencies: null,
  allTransitiveDependencies: null,
);

@Deprecated('Will be removed in 3.0. Use Ref instead')
// ignore: unused_element
typedef CurrentHeartsRef = AutoDisposeProviderRef<int>;
String _$heartsNotifierHash() => r'72d4b51008d2c0d13da1b5863c9b668c3d81ab61';

/// Provider for managing hearts/energy system
///
/// Copied from [HeartsNotifier].
@ProviderFor(HeartsNotifier)
final heartsNotifierProvider =
    AutoDisposeNotifierProvider<HeartsNotifier, HeartState>.internal(
  HeartsNotifier.new,
  name: r'heartsNotifierProvider',
  debugGetCreateSourceHash: const bool.fromEnvironment('dart.vm.product')
      ? null
      : _$heartsNotifierHash,
  dependencies: null,
  allTransitiveDependencies: null,
);

typedef _$HeartsNotifier = AutoDisposeNotifier<HeartState>;
// ignore_for_file: type=lint
// ignore_for_file: subtype_of_sealed_class, invalid_use_of_internal_member, invalid_use_of_visible_for_testing_member, deprecated_member_use_from_same_package
