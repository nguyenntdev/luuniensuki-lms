import 'dart:async';
import 'dart:convert';

import 'package:flutter/foundation.dart';
import 'package:hive_flutter/hive_flutter.dart';
import 'package:riverpod_annotation/riverpod_annotation.dart';

import '../network/network_info.dart';
import '../network/api_client.dart';

part 'sync_service.g.dart';

enum SyncOperationType {
  progressUpdate,
  quizSubmit,
  lessonComplete,
  motifUnlock,
}

class PendingSyncOperation {
  final String id;
  final SyncOperationType type;
  final Map<String, dynamic> data;
  final DateTime timestamp;
  final int retryCount;
  final String? userId;

  const PendingSyncOperation({
    required this.id,
    required this.type,
    required this.data,
    required this.timestamp,
    this.retryCount = 0,
    this.userId,
  });

  Map<String, dynamic> toJson() => {
        'id': id,
        'type': type.name,
        'data': data,
        'timestamp': timestamp.toIso8601String(),
        'retryCount': retryCount,
        'userId': userId,
      };

  factory PendingSyncOperation.fromJson(Map<String, dynamic> json) {
    return PendingSyncOperation(
      id: json['id'] as String,
      type: SyncOperationType.values.firstWhere(
        (e) => e.name == json['type'],
        orElse: () => SyncOperationType.progressUpdate,
      ),
      data: Map<String, dynamic>.from(json['data'] as Map),
      timestamp: DateTime.parse(json['timestamp'] as String),
      retryCount: json['retryCount'] as int? ?? 0,
      userId: json['userId'] as String?,
    );
  }

  PendingSyncOperation copyWith({
    int? retryCount,
  }) {
    return PendingSyncOperation(
      id: id,
      type: type,
      data: data,
      timestamp: timestamp,
      retryCount: retryCount ?? this.retryCount,
      userId: userId,
    );
  }
}

class SyncService {
  static const String _syncQueueBox = 'sync_queue';
  static const int _maxRetries = 3;

  final NetworkInfo _networkInfo;
  final ApiClient _apiClient;
  StreamSubscription<bool>? _connectivitySubscription;

  SyncService({
    required NetworkInfo networkInfo,
    required ApiClient apiClient,
  })  : _networkInfo = networkInfo,
        _apiClient = apiClient;

  Future<void> init() async {
    if (!Hive.isBoxOpen(_syncQueueBox)) {
      await Hive.openBox(_syncQueueBox);
    }

    _connectivitySubscription = _networkInfo.onConnectivityChanged.listen((isConnected) {
      if (isConnected) {
        debugPrint('[SYNC] Network restored - starting sync');
        syncPendingOperations();
      }
    });

    final isConnected = await _networkInfo.isConnected;
    if (isConnected) {
      syncPendingOperations();
    }
  }

  void dispose() {
    _connectivitySubscription?.cancel();
  }

  Box get _syncQueue => Hive.box(_syncQueueBox);

  Future<void> queueOperation(PendingSyncOperation operation) async {
    debugPrint('[SYNC] Queuing operation: ${operation.type.name} - ${operation.id}');
    await _syncQueue.put(operation.id, jsonEncode(operation.toJson()));
  }

  Future<List<PendingSyncOperation>> getPendingOperations() async {
    final operations = <PendingSyncOperation>[];
    for (var key in _syncQueue.keys) {
      try {
        final jsonStr = _syncQueue.get(key) as String;
        final operation = PendingSyncOperation.fromJson(jsonDecode(jsonStr) as Map<String, dynamic>);
        operations.add(operation);
      } catch (e) {
        debugPrint('[SYNC] Failed to parse operation $key: $e');
      }
    }
    return operations;
  }

  Future<void> syncPendingOperations() async {
    final isConnected = await _networkInfo.isConnected;
    if (!isConnected) {
      debugPrint('[SYNC] No network connection - skipping sync');
      return;
    }

    final operations = await getPendingOperations();
    if (operations.isEmpty) {
      debugPrint('[SYNC] No pending operations to sync');
      return;
    }

    debugPrint('[SYNC] Syncing ${operations.length} pending operations');

    for (final operation in operations) {
      await _syncOperation(operation);
    }
  }

  Future<void> _syncOperation(PendingSyncOperation operation) async {
    try {
      debugPrint('[SYNC] Syncing operation: ${operation.type.name} - ${operation.id}');

      final success = await _executeOperation(operation);

      if (success) {
        await _syncQueue.delete(operation.id);
        debugPrint('[SYNC] Operation synced successfully: ${operation.id}');
      } else {
        await _handleSyncFailure(operation);
      }
    } catch (e) {
      debugPrint('[SYNC] Error syncing operation ${operation.id}: $e');
      await _handleSyncFailure(operation);
    }
  }

  Future<bool> _executeOperation(PendingSyncOperation operation) async {
    try {
      switch (operation.type) {
        case SyncOperationType.progressUpdate:
          await _apiClient.post<Map<String, dynamic>>(
            '/api/v1/progress/update',
            data: operation.data,
          );
          return true;

        case SyncOperationType.quizSubmit:
          final motifId = operation.data['motif_id'] as String;
          await _apiClient.post<Map<String, dynamic>>(
            '/api/v1/motifs/$motifId/quiz/submit',
            data: operation.data,
          );
          return true;

        case SyncOperationType.lessonComplete:
          await _apiClient.post<Map<String, dynamic>>(
            '/api/v1/progress/complete-lesson',
            data: operation.data,
          );
          return true;

        case SyncOperationType.motifUnlock:
          await _apiClient.post<Map<String, dynamic>>(
            '/api/v1/progress/unlock',
            data: operation.data,
          );
          return true;

        default:
          debugPrint('[SYNC] Unknown operation type: ${operation.type}');
          return false;
      }
    } catch (e) {
      debugPrint('[SYNC] Failed to execute operation: $e');
      return false;
    }
  }

  Future<void> _handleSyncFailure(PendingSyncOperation operation) async {
    if (operation.retryCount >= _maxRetries) {
      debugPrint('[SYNC] Max retries reached for ${operation.id} - removing from queue');
      await _syncQueue.delete(operation.id);
    } else {
      final updated = operation.copyWith(retryCount: operation.retryCount + 1);
      await _syncQueue.put(operation.id, jsonEncode(updated.toJson()));
      debugPrint('[SYNC] Operation ${operation.id} will retry (${updated.retryCount}/$_maxRetries)');
    }
  }

  Future<void> clearQueue() async {
    await _syncQueue.clear();
    debugPrint('[SYNC] Queue cleared');
  }

  Future<int> getPendingCount() async {
    return _syncQueue.length;
  }

  Future<void> removePendingOperation(String id) async {
    await _syncQueue.delete(id);
    debugPrint('[SYNC] Removed operation: $id');
  }
}

@Riverpod(keepAlive: true)
SyncService syncService(SyncServiceRef ref) {
  final networkInfo = ref.watch(networkInfoProvider);
  final apiClient = ref.watch(apiClientProvider);

  final service = SyncService(
    networkInfo: networkInfo,
    apiClient: apiClient,
  );

  service.init();

  ref.onDispose(() {
    service.dispose();
  });

  return service;
}

@riverpod
Future<int> pendingSyncCount(PendingSyncCountRef ref) async {
  final syncService = ref.watch(syncServiceProvider);
  return syncService.getPendingCount();
}

@riverpod
class SyncNotifier extends _$SyncNotifier {
  @override
  FutureOr<void> build() async {
    final syncService = ref.watch(syncServiceProvider);
    await syncService.syncPendingOperations();
  }

  Future<void> triggerSync() async {
    state = const AsyncLoading();
    try {
      final syncService = ref.read(syncServiceProvider);
      await syncService.syncPendingOperations();
      state = const AsyncData(null);
    } catch (e, stack) {
      state = AsyncError(e, stack);
    }
  }

  Future<void> clearQueue() async {
    final syncService = ref.read(syncServiceProvider);
    await syncService.clearQueue();
    ref.invalidateSelf();
  }
}

