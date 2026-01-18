# Offline-First Quick Reference

## Quick Commands

### Generate Code
```bash
cd mobile
flutter pub get
flutter pub run build_runner build --delete-conflicting-outputs
```

### Run App
```bash
cd mobile
flutter run
```

## Common Patterns

### 1. Fetch Data (Read Operation)

```dart
// Provider
@riverpod
Future<List<Urn>> urns(Ref ref) async {
  final repository = ref.watch(urnRepositoryProvider);
  final result = await repository.getUrns();
  
  return result.fold(
    (failure) => throw Exception(failure.message),
    (data) => data,
  );
}

// UI Widget
final urnsAsync = ref.watch(urnsProvider);

urnsAsync.when(
  data: (urns) => ListView.builder(...),
  loading: () => CircularProgressIndicator(),
  error: (error, _) => ErrorWidget(error),
);
```

### 2. Submit Data (Write Operation)

```dart
// Repository method queues operation if offline
Future<void> submitQuiz() async {
  final repository = ref.read(lessonRepositoryProvider);
  final result = await repository.submitQuiz(
    motifId: motifId,
    answers: answers,
  );
  
  result.fold(
    (failure) {
      if (failure is NetworkFailure) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Saved offline. Will sync when online.')),
        );
      }
    },
    (success) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Quiz submitted!')),
      );
    },
  );
}
```

### 3. Check Sync Status

```dart
// Get pending count
final pendingCount = await ref.read(pendingSyncCountProvider.future);

// Watch for changes
ref.listen(pendingSyncCountProvider, (previous, next) {
  next.whenData((count) {
    if (count > 0) {
      // Show sync indicator in UI
    }
  });
});
```

### 4. Manual Sync

```dart
// Trigger sync
final syncNotifier = ref.read(syncNotifierProvider.notifier);
await syncNotifier.triggerSync();
```

## File Locations

### Core Files
```
mobile/lib/core/
├── repositories/
│   └── offline_first_repository.dart
├── services/
│   └── sync_service.dart
└── storage/
    └── hive_storage.dart
```

### Repository Implementations
```
mobile/lib/features/
├── urn_viewer/data/repositories/
│   └── urn_repository.dart
└── lesson/data/repositories/
    └── lesson_repository.dart
```

## Provider Reference

### Core Providers

```dart
// Network status
final networkInfo = ref.watch(networkInfoProvider);
final isConnected = await networkInfo.isConnected;

// Storage
final storage = ref.watch(hiveStorageProvider);

// Sync service
final syncService = ref.watch(syncServiceProvider);
```

### Data Providers

```dart
// Urns (offline-first)
final urns = ref.watch(urnsOfflineFirstProvider);

// Urn detail (offline-first)
final urnDetail = ref.watch(urnDetailOfflineFirstProvider(slug));

// Motif detail (offline-first)
final motifDetail = ref.watch(motifDetailOfflineFirstProvider(motifId));
```

### Action Providers

```dart
// Complete lesson
final lessonCompletion = ref.read(lessonCompletionOfflineFirstProvider.notifier);
await lessonCompletion.completeLesson(motifId);

// Submit quiz
final quizSubmission = ref.read(quizSubmissionOfflineFirstProvider.notifier);
await quizSubmission.submitQuiz(
  motifId: motifId,
  answers: answers,
  timeTakenSeconds: timeTaken,
);
```

## Debugging

### Enable Debug Logging

All operations log to console with prefixes:

```dart
[SYNC] Network restored - starting sync
[SYNC] Queuing operation: lessonComplete - abc123
[GetUrns] Network available - fetching fresh data
[GetUrns] Data cached successfully
[CompleteLesson] Offline - operation will be queued for sync
```

### Check Cache Status

```dart
final storage = ref.read(hiveStorageProvider);

// Check cache validity
bool isValid = storage.isCacheValid('urns', Duration(hours: 24));

// Get cache time
DateTime? cacheTime = storage.getCacheTime('urns');
```

### Inspect Pending Operations

```dart
final syncService = ref.read(syncServiceProvider);
final pending = await syncService.getPendingOperations();

for (final op in pending) {
  print('${op.type}: ${op.data} (retry: ${op.retryCount})');
}
```

## Testing Offline Mode

### Disable Network

```dart
// In iOS Simulator: Settings → Wi-Fi → Off
// In Android Emulator: Settings → Network & Internet → Wi-Fi → Off
// Or use airplane mode
```

### Verify Behavior

1. Open app with network on
2. Navigate to content (data cached)
3. Turn off network
4. Navigate back - should still work
5. Try to submit data - should queue
6. Turn network back on
7. Data should sync automatically

## Common Issues

### Issue: `syncServiceProvider` not found
**Solution**: Run code generation
```bash
flutter pub run build_runner build --delete-conflicting-outputs
```

### Issue: Cache not updating
**Solution**: Clear cache
```dart
await ref.read(hiveStorageProvider).clearAllCache();
```

### Issue: Operations not syncing
**Solution**: Check network and manually trigger
```dart
final isConnected = await ref.read(networkInfoProvider).isConnected;
if (isConnected) {
  await ref.read(syncNotifierProvider.notifier).triggerSync();
}
```

## Dependencies Added

```yaml
dependencies:
  uuid: ^4.2.2  # For generating operation IDs
```

## Next Steps

1. ✅ Core implementation complete
2. ⏳ Run code generation
3. ⏳ Update existing providers to use pattern
4. ⏳ Test offline functionality
5. ⏳ Add UI indicators for sync status
