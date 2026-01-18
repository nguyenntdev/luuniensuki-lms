# Offline-First Repository Pattern (P6-C4)

## Overview

The offline-first repository pattern enables the mobile app to work seamlessly offline by implementing a robust data synchronization strategy that prioritizes network requests but gracefully falls back to cached data when offline.

## Architecture

### Core Components

1. **OfflineFirstRepository** - Base class for offline-first data access
2. **SyncService** - Tracks and syncs pending offline changes
3. **Repository Implementations** - Concrete repositories using the pattern

## File Structure

```
mobile/lib/core/
├── repositories/
│   └── offline_first_repository.dart    # Base class
├── services/
│   └── sync_service.dart                # Sync coordination
└── storage/
    └── hive_storage.dart                 # Updated with sync queue

mobile/lib/features/
├── urn_viewer/data/repositories/
│   └── urn_repository.dart              # Offline-first URN operations
└── lesson/data/repositories/
    └── lesson_repository.dart            # Offline-first lesson operations
```

## Usage Patterns

### 1. Read Operations (Network-First with Cache Fallback)

```dart
class UrnRepository extends OfflineFirstRepository<List<Urn>> {
  Future<Either<Failure, List<Urn>>> getUrns() async {
    return executeOfflineFirst<List<Urn>>(
      networkCall: () async {
        // Fetch from network
        final response = await apiClient.get('/api/v1/urns');
        return parseResponse(response);
      },
      getCached: () async {
        // Get from cache
        return hiveStorage.getCachedUrns();
      },
      saveCache: (urns) async {
        // Save to cache
        await hiveStorage.cacheUrns(urns);
      },
      operationName: 'GetUrns',
    );
  }
}
```

### 2. Write Operations (With Automatic Sync Queue)

```dart
Future<Either<Failure, CompleteLessonResponseDto>> completeLesson(String motifId) async {
  return executeWriteOperation<CompleteLessonResponseDto>(
    networkCall: () async {
      final response = await apiClient.post(
        '/api/v1/progress/complete-lesson',
        data: {'motif_id': motifId},
      );
      return CompleteLessonResponseDto.fromJson(response);
    },
    onSuccess: () async {
      // Update local cache on success
      await hiveStorage.updateProgressForMotif(motifId, {...});
    },
    operationName: 'CompleteLesson($motifId)',
  ).then((result) async {
    // Queue for sync if network fails
    if (result.isLeft()) {
      await syncService.queueOperation(
        PendingSyncOperation(
          id: uuid.v4(),
          type: SyncOperationType.lessonComplete,
          data: {'motif_id': motifId},
          timestamp: DateTime.now(),
        ),
      );
    }
    return result;
  });
}
```

### 3. Cache-First Strategy (For Fast Loading)

```dart
Future<Either<Failure, T>> getData() async {
  return executeCacheFirst<T>(
    networkCall: () async { /* ... */ },
    getCached: () async { /* ... */ },
    saveCache: (data) async { /* ... */ },
    isCacheValid: () => hiveStorage.isCacheValid('key', Duration(hours: 1)),
    operationName: 'GetData',
  );
}
```

## Sync Service

### Automatic Synchronization

The `SyncService` automatically:
- Monitors network connectivity
- Queues failed write operations
- Retries operations when network is restored
- Handles conflict resolution

### Operation Types

```dart
enum SyncOperationType {
  progressUpdate,
  quizSubmit,
  lessonComplete,
  motifUnlock,
}
```

### Pending Operations

```dart
class PendingSyncOperation {
  final String id;
  final SyncOperationType type;
  final Map<String, dynamic> data;
  final DateTime timestamp;
  final int retryCount;
  final String? userId;
}
```

### Manual Sync Trigger

```dart
// Trigger sync manually
final syncNotifier = ref.read(syncNotifierProvider.notifier);
await syncNotifier.triggerSync();

// Get pending count
final pendingCount = await ref.read(pendingSyncCountProvider.future);

// Clear queue (use with caution)
await syncNotifier.clearQueue();
```

## Integration with Existing Providers

### Before (Old Pattern)

```dart
@riverpod
Future<List<Urn>> urns(Ref ref) async {
  final apiClient = ref.watch(apiClientProvider);
  final hiveStorage = ref.watch(hiveStorageProvider);
  final networkInfo = ref.watch(networkInfoProvider);

  if (!await networkInfo.isConnected) {
    final cached = hiveStorage.getCachedUrns();
    if (cached != null) return cached;
    throw NetworkException('No internet');
  }

  try {
    final response = await apiClient.get('/api/v1/urns');
    await hiveStorage.cacheUrns(response);
    return response;
  } catch (e) {
    final cached = hiveStorage.getCachedUrns();
    if (cached != null) return cached;
    rethrow;
  }
}
```

### After (New Pattern)

```dart
@riverpod
Future<List<Urn>> urnsOfflineFirst(Ref ref) async {
  final repository = ref.watch(urnRepositoryProvider);
  final result = await repository.getUrns();
  
  return result.fold(
    (failure) => throw Exception(failure.message),
    (urns) => urns,
  );
}
```

## Benefits

### 1. Consistency
- All data access follows the same pattern
- Centralized error handling
- Unified caching strategy

### 2. Maintainability
- Reduced code duplication
- Clear separation of concerns
- Easier to test

### 3. User Experience
- App works offline seamlessly
- Automatic background sync
- No data loss during offline periods
- Transparent retry mechanism

### 4. Performance
- Network-first for fresh data
- Cache fallback for reliability
- Background refresh option
- Optimized cache validation

## Configuration

### Cache Duration

Set cache validity periods in HiveStorage:

```dart
// Check if cache is valid
bool isValid = hiveStorage.isCacheValid(
  'urns',
  Duration(hours: 24), // Cache valid for 24 hours
);
```

### Sync Settings

Configure sync behavior:

```dart
class SyncService {
  static const int _maxRetries = 3;  // Max retry attempts

  // Retry intervals can be customized
  Future<void> _retryWithBackoff(int retryCount) async {
    final delay = Duration(seconds: pow(2, retryCount).toInt());
    await Future.delayed(delay);
  }
}
```

## Error Handling

### Failure Types

```dart
// Network failure - no internet connection
NetworkFailure('No internet connection')

// Server failure - API error
ServerFailure('Server error', statusCode: 500)

// Cache failure - no cached data
CacheFailure('No cached data available')

// Auth failure - session expired
AuthFailure.sessionExpired()
```

### Graceful Degradation

```dart
// 1. Try network
// 2. On network error, try cache
// 3. If cache available, use it
// 4. Otherwise, return appropriate failure
```

## Testing

### Unit Tests

```dart
test('should return cached data when offline', () async {
  // Arrange
  when(() => networkInfo.isConnected).thenAnswer((_) async => false);
  when(() => hiveStorage.getCachedUrns()).thenReturn(testUrns);

  // Act
  final result = await repository.getUrns();

  // Assert
  expect(result, Right(testUrns));
  verify(() => hiveStorage.getCachedUrns()).called(1);
  verifyNever(() => apiClient.get(any()));
});
```

## Migration Guide

### Step 1: Update Existing Providers

Replace direct API calls with repository pattern:

```dart
// Old
final response = await apiClient.get('/api/v1/urns');

// New
final repository = ref.watch(urnRepositoryProvider);
final result = await repository.getUrns();
```

### Step 2: Initialize Sync Service

In `main.dart`:

```dart
void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await HiveStorage.init();

  runApp(
    ProviderScope(
      child: MyApp(),
    ),
  );
}
```

The SyncService initializes automatically via the provider.

### Step 3: Handle Write Operations

Queue operations when offline:

```dart
final result = await repository.completeLesson(motifId);
result.fold(
  (failure) {
    // Show user-friendly message
    if (failure is NetworkFailure) {
      showSnackBar('Saved offline. Will sync when online.');
    }
  },
  (success) {
    showSnackBar('Lesson completed!');
  },
);
```

## Monitoring

### Check Sync Status

```dart
// Get pending operations count
final count = await ref.read(pendingSyncCountProvider.future);

// Watch for changes
ref.listen(pendingSyncCountProvider, (previous, next) {
  next.whenData((count) {
    if (count > 0) {
      print('$count operations pending sync');
    }
  });
});
```

### Debug Logging

All operations log to console with prefixes:
- `[SYNC]` - Sync service operations
- `[GetUrns]` - Operation-specific logs
- `[CompleteLesson]` - Write operation logs

## Best Practices

1. **Always use repositories** - Don't bypass the pattern
2. **Set appropriate cache durations** - Balance freshness vs offline capability
3. **Handle failures gracefully** - Show user-friendly messages
4. **Monitor sync queue** - Alert users of pending operations
5. **Test offline scenarios** - Ensure app works without network

## Troubleshooting

### Issue: Data not syncing

```dart
// Check network connectivity
final isConnected = await ref.read(networkInfoProvider).isConnected;

// Manually trigger sync
await ref.read(syncNotifierProvider.notifier).triggerSync();
```

### Issue: Cache not updating

```dart
// Clear specific cache
await hiveStorage.clearContentCache();

// Or clear all cache
await hiveStorage.clearAllCache();
```

### Issue: Pending operations stuck

```dart
// View pending operations
final syncService = ref.read(syncServiceProvider);
final pending = await syncService.getPendingOperations();

// Clear if needed (use with caution)
await syncService.clearQueue();
```

## Next Steps

1. Run code generation: `flutter pub run build_runner build --delete-conflicting-outputs`
2. Test offline functionality
3. Monitor sync behavior in production
4. Adjust cache durations based on usage patterns
5. Implement conflict resolution for concurrent updates

