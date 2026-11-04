import 'dart:async';
import 'package:dio/dio.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:riverpod_annotation/riverpod_annotation.dart';

import '../network/api_client.dart';
import '../storage/hive_storage.dart';

part 'offline_queue_service.g.dart';

/// Represents an offline queued operation for progress/quiz writes with idempotency key.
class OfflineOperation {
  final String operationId;
  final String resource; // e.g., 'inspection', 'submission', 'progression', 'quiz_submit'
  final Map<String, dynamic> payload;
  final DateTime createdAt;
  final int retryCount;
  final String idempotencyKey;
  final String status; // 'pending', 'syncing', 'completed', 'failed'
  final String? lastError;
  final Map<String, dynamic>? serverAck;
  final int xpAwarded;
  final String? conflictResolution;

  OfflineOperation({
    required this.operationId,
    required this.resource,
    required this.payload,
    required this.createdAt,
    this.retryCount = 0,
    required this.idempotencyKey,
    this.status = 'pending',
    this.lastError,
    this.serverAck,
    this.xpAwarded = 0,
    this.conflictResolution,
  });

  Map<String, dynamic> toJson() => {
        'operation_id': operationId,
        'resource': resource,
        'payload': payload,
        'created_at': createdAt.toIso8601String(),
        'retry_count': retryCount,
        'idempotency_key': idempotencyKey,
        'status': status,
        'last_error': lastError,
        'server_ack': serverAck,
        'xp_awarded': xpAwarded,
        'conflict_resolution': conflictResolution,
      };

  factory OfflineOperation.fromJson(Map<String, dynamic> json) =>
      OfflineOperation(
        operationId: json['operation_id'] as String? ?? '',
        resource: json['resource'] as String? ?? '',
        payload: json['payload'] as Map<String, dynamic>? ?? {},
        createdAt: json['created_at'] != null
            ? DateTime.parse(json['created_at'] as String)
            : DateTime.now(),
        retryCount: json['retry_count'] as int? ?? 0,
        idempotencyKey: json['idempotency_key'] as String? ?? '',
        status: json['status'] as String? ?? 'pending',
        lastError: json['last_error'] as String?,
        serverAck: json['server_ack'] as Map<String, dynamic>?,
        xpAwarded: json['xp_awarded'] as int? ?? 0,
        conflictResolution: json['conflict_resolution'] as String?,
      );

  OfflineOperation copyWith({
    int? retryCount,
    String? status,
    String? lastError,
    Map<String, dynamic>? serverAck,
    int? xpAwarded,
    String? conflictResolution,
  }) {
    return OfflineOperation(
      operationId: operationId,
      resource: resource,
      payload: payload,
      createdAt: createdAt,
      retryCount: retryCount ?? this.retryCount,
      idempotencyKey: idempotencyKey,
      status: status ?? this.status,
      lastError: lastError ?? this.lastError,
      serverAck: serverAck ?? this.serverAck,
      xpAwarded: xpAwarded ?? this.xpAwarded,
      conflictResolution: conflictResolution ?? this.conflictResolution,
    );
  }
}

/// Service managing offline write queue with idempotent synchronization.
class OfflineQueueService extends ChangeNotifier {
  final ApiClient? _apiClient;
  final HiveStorage? _hiveStorage;
  final List<OfflineOperation> _queue = [];

  OfflineQueueService({ApiClient? apiClient, HiveStorage? hiveStorage})
      : _apiClient = apiClient,
        _hiveStorage = hiveStorage {
    _loadQueueFromStorage();
  }

  List<OfflineOperation> get queue => List.unmodifiable(_queue);

  int get pendingCount => _queue
      .where((op) => op.status == 'pending' || op.status == 'failed')
      .length;

  Future<void> _loadQueueFromStorage() async {
    try {
      final rawData = _hiveStorage?.getSetting<dynamic>('offline_queue');
      if (rawData != null && rawData is List) {
        _queue.clear();
        for (final item in rawData) {
          if (item is Map) {
            _queue.add(
                OfflineOperation.fromJson(Map<String, dynamic>.from(item)));
          }
        }
        notifyListeners();
      }
    } catch (e) {
      debugPrint('[OfflineQueue] Load error: $e');
    }
  }

  Future<void> _saveQueueToStorage() async {
    try {
      final data = _queue.map((op) => op.toJson()).toList();
      await _hiveStorage?.setSetting('offline_queue', data);
    } catch (e) {
      debugPrint('[OfflineQueue] Save error: $e');
    }
  }

  /// Enqueue a write operation (e.g., quiz result or progress update).
  Future<OfflineOperation> enqueue({
    required String resource,
    required Map<String, dynamic> payload,
    String? idempotencyKey,
  }) async {
    final now = DateTime.now();
    final opId = 'op_${now.millisecondsSinceEpoch}_${_queue.length}';
    final key = idempotencyKey ?? 'idemp_${now.microsecondsSinceEpoch}';

    final op = OfflineOperation(
      operationId: opId,
      resource: resource,
      payload: payload,
      createdAt: now,
      idempotencyKey: key,
    );

    _queue.add(op);
    await _saveQueueToStorage();
    notifyListeners();

    // Fire off async queue processing
    unawaited(processQueue());

    return op;
  }

  /// Enqueue an inspection task (AR or turntable) with idempotency key.
  Future<OfflineOperation> enqueueInspection({
    required String targetSlug,
    String inspectionMode = 'turntable_3d',
    bool cameraPermissionGranted = false,
    int timeSpentSeconds = 10,
    List<String>? anglesInspected,
    List<String>? hotspotsExamined,
    String? idempotencyKey,
  }) async {
    return enqueue(
      resource: 'inspection',
      payload: {
        'target_slug': targetSlug,
        'inspection_mode': inspectionMode,
        'camera_permission_granted': cameraPermissionGranted,
        'time_spent_seconds': timeSpentSeconds,
        'angles_inspected': anglesInspected ?? ['front'],
        'hotspots_examined': hotspotsExamined ?? [],
      },
      idempotencyKey: idempotencyKey,
    );
  }

  /// Enqueue a student learning progression action (discover, complete_lesson, submit_quiz).
  Future<OfflineOperation> enqueueProgression({
    required String action,
    required String motifId,
    int timeSpentSeconds = 10,
    Map<String, dynamic>? answers,
    String? idempotencyKey,
  }) async {
    return enqueue(
      resource: 'progression',
      payload: {
        'action': action,
        'motif_id': motifId,
        'time_spent_seconds': timeSpentSeconds,
        if (answers != null) 'answers': answers,
      },
      idempotencyKey: idempotencyKey,
    );
  }

  /// Enqueue a student activity or assignment submission with idempotency key.
  Future<OfflineOperation> enqueueSubmission({
    required String resource,
    required Map<String, dynamic> submissionData,
    String? idempotencyKey,
  }) async {
    return enqueue(
      resource: resource,
      payload: submissionData,
      idempotencyKey: idempotencyKey,
    );
  }

  /// Attempt to synchronize all pending operations idempotently with backend.
  Future<void> processQueue() async {
    final client = _apiClient;
    if (client == null) return;

    final pendingIndices = <int>[];
    for (int i = 0; i < _queue.length; i++) {
      if (_queue[i].status == 'pending' || _queue[i].status == 'failed') {
        pendingIndices.add(i);
      }
    }

    if (pendingIndices.isEmpty) return;

    for (final i in pendingIndices) {
      final op = _queue[i];

      if (op.retryCount >= 5) {
        _queue[i] =
            op.copyWith(status: 'failed', lastError: 'Max retries reached (5)');
        continue;
      }

      _queue[i] = op.copyWith(status: 'syncing');
      notifyListeners();

      try {
        final response = await client.post<Map<String, dynamic>>(
          '/api/v1/offline/sync',
          data: {
            'operation_id': op.operationId,
            'resource': op.resource,
            'payload': op.payload,
            'created_at': op.createdAt.toIso8601String(),
            'idempotency_key': op.idempotencyKey,
          },
          options: Options(
            headers: {'X-Idempotency-Key': op.idempotencyKey},
          ),
        );

        final resData = response;
        final serverStatus = resData['status'] as String? ?? 'completed';
        final xp = resData['xp_awarded'] as int? ?? 0;
        final conflictRes = resData['conflict_resolution'] as String?;
        final serverAck = resData['server_ack'] is Map
            ? Map<String, dynamic>.from(resData['server_ack'] as Map)
            : resData;

        if (serverStatus == 'failed') {
          _queue[i] = op.copyWith(
            status: 'failed',
            lastError: resData['error'] as String? ?? 'Sync rejected by server',
            serverAck: serverAck,
          );
        } else {
          _queue[i] = op.copyWith(
            status: 'completed',
            serverAck: serverAck,
            xpAwarded: xp,
            conflictResolution: conflictRes,
          );
        }
      } catch (e) {
        if (e is DioException && e.response?.statusCode == 409) {
          final resData = (e.response?.data is Map)
              ? Map<String, dynamic>.from(e.response!.data as Map)
              : <String, dynamic>{};
          _queue[i] = op.copyWith(
            status: 'completed',
            conflictResolution: 'server_state_preserved',
            serverAck: resData,
            lastError: 'Conflict: ${resData['message'] ?? 'Resource conflict'}',
          );
        } else {
          debugPrint('[OfflineQueue] Sync error for ${op.operationId}: $e');
          _queue[i] = op.copyWith(
            status: 'pending',
            retryCount: op.retryCount + 1,
            lastError: e.toString(),
          );
        }
      }
    }

    await _saveQueueToStorage();
    notifyListeners();
  }

  /// Remove completed operations from queue.
  Future<void> clearCompleted() async {
    _queue.removeWhere((op) => op.status == 'completed');
    await _saveQueueToStorage();
    notifyListeners();
  }

  /// Clear entire queue.
  Future<void> clearAll() async {
    _queue.clear();
    await _saveQueueToStorage();
    notifyListeners();
  }
}

@Riverpod(keepAlive: true)
OfflineQueueService offlineQueueService(OfflineQueueServiceRef ref) {
  final apiClient = ref.watch(apiClientProvider);
  final storage = ref.watch(hiveStorageProvider);
  return OfflineQueueService(apiClient: apiClient, hiveStorage: storage);
}
