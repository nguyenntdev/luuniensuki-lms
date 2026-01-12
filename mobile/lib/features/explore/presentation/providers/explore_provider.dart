import 'package:flutter/foundation.dart';
import 'package:riverpod_annotation/riverpod_annotation.dart';

import '../../../../core/constants/api_constants.dart';
import '../../../../core/network/api_client.dart';
import '../../domain/entities/urn.dart';

part 'explore_provider.g.dart';

/// State for the explore screen
class ExploreState {
  final List<Urn> urns;
  final bool isLoading;
  final String? errorMessage;
  final bool isRefreshing;

  const ExploreState({
    this.urns = const [],
    this.isLoading = false,
    this.errorMessage,
    this.isRefreshing = false,
  });

  ExploreState copyWith({
    List<Urn>? urns,
    bool? isLoading,
    String? errorMessage,
    bool? isRefreshing,
  }) {
    return ExploreState(
      urns: urns ?? this.urns,
      isLoading: isLoading ?? this.isLoading,
      errorMessage: errorMessage,
      isRefreshing: isRefreshing ?? this.isRefreshing,
    );
  }

  bool get hasError => errorMessage != null;
  bool get hasData => urns.isNotEmpty;
}

/// Provider for explore screen state and actions
@Riverpod(keepAlive: true)
class ExploreNotifier extends _$ExploreNotifier {
  @override
  ExploreState build() {
    // Don't load immediately - wait for auth to be ready
    // Load will be triggered from UI when auth is ready
    return const ExploreState(isLoading: true);
  }

  ApiClient get _apiClient => ref.read(apiClientProvider);

  /// Initialize the provider - should be called when auth is ready
  void initialize() {
    if (!state.hasData && !state.isLoading) {
      loadUrns();
    }
  }

  /// Load all urns from API
  Future<void> loadUrns() async {
    if (state.isLoading && state.hasData) return;

    state = state.copyWith(isLoading: true, errorMessage: null);

    try {
      debugPrint('[EXPLORE] Loading urns from API...');

      final response = await _apiClient.get<List<dynamic>>(
        ApiConstants.urns,
      );

      debugPrint('[EXPLORE] Got ${response.length} urns');

      final urns = response
          .map((json) => Urn.fromJson(json as Map<String, dynamic>))
          .toList();

      // Sort by display order
      urns.sort((a, b) => a.displayOrder.compareTo(b.displayOrder));

      state = state.copyWith(
        urns: urns,
        isLoading: false,
        isRefreshing: false,
      );

      debugPrint('[EXPLORE] Urns loaded successfully');
    } catch (e, stackTrace) {
      debugPrint('[EXPLORE] Error loading urns: $e');
      debugPrint('[EXPLORE] StackTrace: $stackTrace');

      state = state.copyWith(
        isLoading: false,
        isRefreshing: false,
        errorMessage: _getErrorMessage(e),
      );
    }
  }

  /// Refresh urns (pull-to-refresh)
  Future<void> refreshUrns() async {
    if (state.isRefreshing) return;

    state = state.copyWith(isRefreshing: true, errorMessage: null);

    try {
      final response = await _apiClient.get<List<dynamic>>(
        ApiConstants.urns,
      );

      final urns = response
          .map((json) => Urn.fromJson(json as Map<String, dynamic>))
          .toList();

      urns.sort((a, b) => a.displayOrder.compareTo(b.displayOrder));

      state = state.copyWith(
        urns: urns,
        isRefreshing: false,
      );
    } catch (e) {
      state = state.copyWith(
        isRefreshing: false,
        errorMessage: _getErrorMessage(e),
      );
    }
  }

  /// Get error message from exception
  String _getErrorMessage(dynamic error) {
    if (error.toString().contains('SocketException') ||
        error.toString().contains('NetworkException')) {
      return 'Không có kết nối mạng. Vui lòng kiểm tra lại.';
    }
    if (error.toString().contains('TimeoutException')) {
      return 'Kết nối quá chậm. Vui lòng thử lại.';
    }
    return 'Đã xảy ra lỗi. Vui lòng thử lại.';
  }
}

/// Provider for a single urn by slug
@riverpod
Urn? urnBySlug(UrnBySlugRef ref, String slug) {
  final state = ref.watch(exploreNotifierProvider);
  try {
    return state.urns.firstWhere((urn) => urn.slug == slug);
  } catch (_) {
    return null;
  }
}

/// Provider for total progress across all urns
@riverpod
ExploreProgress exploreProgress(ExploreProgressRef ref) {
  final state = ref.watch(exploreNotifierProvider);

  if (state.urns.isEmpty) {
    return const ExploreProgress(
      totalMotifs: 0,
      discoveredMotifs: 0,
      learnedMotifs: 0,
      masteredMotifs: 0,
    );
  }

  int totalMotifs = 0;
  int discoveredMotifs = 0;
  int learnedMotifs = 0;
  int masteredMotifs = 0;

  for (final urn in state.urns) {
    totalMotifs += urn.motifCount;
    discoveredMotifs += urn.discoveredCount;
    learnedMotifs += urn.learnedCount;
    masteredMotifs += urn.masteredCount;
  }

  return ExploreProgress(
    totalMotifs: totalMotifs,
    discoveredMotifs: discoveredMotifs,
    learnedMotifs: learnedMotifs,
    masteredMotifs: masteredMotifs,
  );
}

/// Progress data across all urns
class ExploreProgress {
  final int totalMotifs;
  final int discoveredMotifs;
  final int learnedMotifs;
  final int masteredMotifs;

  const ExploreProgress({
    required this.totalMotifs,
    required this.discoveredMotifs,
    required this.learnedMotifs,
    required this.masteredMotifs,
  });

  double get discoveryPercent {
    if (totalMotifs == 0) return 0.0;
    return discoveredMotifs / totalMotifs;
  }

  double get masteryPercent {
    if (totalMotifs == 0) return 0.0;
    return masteredMotifs / totalMotifs;
  }

  int get remainingMotifs => totalMotifs - discoveredMotifs;
}
