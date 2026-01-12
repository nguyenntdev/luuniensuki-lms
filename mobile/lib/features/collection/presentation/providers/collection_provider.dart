import 'package:flutter/foundation.dart';
import 'package:riverpod_annotation/riverpod_annotation.dart';

import '../../../../core/constants/api_constants.dart';
import '../../../../core/network/api_client.dart';
import '../../data/models/collection_dtos.dart';

part 'collection_provider.g.dart';

/// State for the collection screen
class CollectionState {
  final CollectionResponseDto? collection;
  final bool isLoading;
  final String? errorMessage;
  final bool isRefreshing;

  const CollectionState({
    this.collection,
    this.isLoading = false,
    this.errorMessage,
    this.isRefreshing = false,
  });

  CollectionState copyWith({
    CollectionResponseDto? collection,
    bool? isLoading,
    String? errorMessage,
    bool? isRefreshing,
  }) {
    return CollectionState(
      collection: collection ?? this.collection,
      isLoading: isLoading ?? this.isLoading,
      errorMessage: errorMessage,
      isRefreshing: isRefreshing ?? this.isRefreshing,
    );
  }

  bool get hasError => errorMessage != null;
  bool get hasData => collection != null;
}

/// Provider for collection screen state and actions
@Riverpod(keepAlive: true)
class CollectionNotifier extends _$CollectionNotifier {
  @override
  CollectionState build() {
    return const CollectionState(isLoading: true);
  }

  ApiClient get _apiClient => ref.read(apiClientProvider);

  /// Load user's collection from API
  Future<void> loadCollection() async {
    if (state.isLoading && state.hasData) return;

    state = state.copyWith(isLoading: true, errorMessage: null);

    try {
      debugPrint('[COLLECTION] Loading collection from API...');

      final response = await _apiClient.get<Map<String, dynamic>>(
        ApiConstants.userCollection,
      );

      debugPrint('[COLLECTION] Got collection response');

      final collection = CollectionResponseDto.fromJson(response);

      state = state.copyWith(
        collection: collection,
        isLoading: false,
        isRefreshing: false,
      );

      debugPrint('[COLLECTION] Collection loaded successfully: ${collection.stats.discovered}/${collection.stats.total}');
    } catch (e, stackTrace) {
      debugPrint('[COLLECTION] Error loading collection: $e');
      debugPrint('[COLLECTION] StackTrace: $stackTrace');

      state = state.copyWith(
        isLoading: false,
        isRefreshing: false,
        errorMessage: _getErrorMessage(e),
      );
    }
  }

  /// Refresh collection (pull-to-refresh)
  Future<void> refreshCollection() async {
    if (state.isRefreshing) return;

    state = state.copyWith(isRefreshing: true, errorMessage: null);

    try {
      final response = await _apiClient.get<Map<String, dynamic>>(
        ApiConstants.userCollection,
      );

      final collection = CollectionResponseDto.fromJson(response);

      state = state.copyWith(
        collection: collection,
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

