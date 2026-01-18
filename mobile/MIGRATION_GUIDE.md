# Migration Guide: Switching to Offline-First Pattern

## Overview

This guide shows how to migrate existing providers to use the new offline-first repository pattern.

## Before You Start

1. Ensure code generation is complete:
   ```bash
   flutter pub run build_runner build --delete-conflicting-outputs
   ```

2. Familiarize yourself with the new providers:
   - Read `OFFLINE_FIRST_QUICK_REFERENCE.md`
   - Review `offline_first_example_screen.dart`

## Migration Patterns

### Pattern 1: Simple Data Fetching

#### Before (Old Pattern)
```dart
// File: features/urn_viewer/presentation/providers/urn_provider.dart

@riverpod
Future<List<Urn>> urns(Ref ref) async {
  final apiClient = ref.watch(apiClientProvider);
  final hiveStorage = ref.watch(hiveStorageProvider);
  final networkInfo = ref.watch(networkInfoProvider);

  if (!await networkInfo.isConnected) {
    final cached = hiveStorage.getCachedUrns();
    if (cached != null) {
      return cached.map((json) => UrnToJson.fromJson(json)).toList();
    }
    throw const NetworkException('No internet connection');
  }

  try {
    final response = await apiClient.get<List<dynamic>>(ApiConstants.urns);
    final urns = (response as List)
        .map((json) => UrnListItemDto.fromJson(json as Map<String, dynamic>))
        .map((dto) => dto.toEntity())
        .toList();
    
    await hiveStorage.cacheUrns(urns.map((u) => u.toJson()).toList());
    return urns;
  } catch (e) {
    final cached = hiveStorage.getCachedUrns();
    if (cached != null) {
      return cached.map((json) => UrnToJson.fromJson(json)).toList();
    }
    rethrow;
  }
}
```

#### After (New Pattern)
```dart
// File: features/urn_viewer/presentation/providers/urn_provider.dart

@riverpod
Future<List<Urn>> urns(Ref ref) async {
  // Simply use the new offline-first provider
  return ref.watch(urnsOfflineFirstProvider.future);
}

// Or even simpler - just remove the old provider and use the new one directly in UI
```

#### In UI Widget
```dart
// Before
final urnsAsync = ref.watch(urnsProvider);

// After (same code - no changes needed!)
final urnsAsync = ref.watch(urnsOfflineFirstProvider);
```

### Pattern 2: Write Operations

#### Before (Old Pattern)
```dart
@riverpod
class LessonCompletion extends _$LessonCompletion {
  @override
  FutureOr<CompleteLessonResponseDto?> build() => null;

  Future<CompleteLessonResponseDto?> completeLesson(String motifId) async {
    state = const AsyncLoading();

    try {
      final apiClient = ref.read(apiClientProvider);
      final result = await apiClient.post<CompleteLessonResponseDto>(
        '/api/v1/progress/complete-lesson',
        data: {'motif_id': motifId},
        parser: (json) =>
            CompleteLessonResponseDto.fromJson(json as Map<String, dynamic>),
      );

      state = AsyncData(result);
      ref.invalidate(motifDetailProvider(motifId));
      return result;
    } catch (e, s) {
      state = AsyncError(e, s);
      return null;
    }
  }
}
```

#### After (New Pattern)
```dart
// Just use the new provider - it's already implemented!
// File: features/lesson/data/repositories/lesson_repository.dart

// In UI:
final completion = ref.read(lessonCompletionOfflineFirstProvider.notifier);
await completion.completeLesson(motifId);
```

### Pattern 3: Parameterized Providers

#### Before (Old Pattern)
```dart
@riverpod
Future<UrnDetail> urnDetail(Ref ref, String slug) async {
  final apiClient = ref.watch(apiClientProvider);
  final hiveStorage = ref.watch(hiveStorageProvider);
  final networkInfo = ref.watch(networkInfoProvider);

  if (!await networkInfo.isConnected) {
    final cached = hiveStorage.getCachedUrn(slug);
    if (cached != null) {
      final dto = UrnDetailResponseDto.fromJson(cached);
      return dto.toEntity();
    }
    throw const NetworkException('No internet connection');
  }

  try {
    final response = await apiClient.get<Map<String, dynamic>>(
      ApiConstants.urn(slug),
    );
    final dto = UrnDetailResponseDto.fromJson(response);
    final urnDetail = dto.toEntity();
    await hiveStorage.cacheUrn(slug, response);
    return urnDetail;
  } catch (e) {
    final cached = hiveStorage.getCachedUrn(slug);
    if (cached != null) {
      final dto = UrnDetailResponseDto.fromJson(cached);
      return dto.toEntity();
    }
    rethrow;
  }
}
```

#### After (New Pattern)
```dart
@riverpod
Future<UrnDetail> urnDetail(Ref ref, String slug) async {
  return ref.watch(urnDetailOfflineFirstProvider(slug).future);
}

// Or use the new provider directly
```

## Step-by-Step Migration

### Step 1: Update Import Statements

Add imports for new repositories:

```dart
// Add to your provider files
import '../data/repositories/urn_repository.dart';
import '../data/repositories/lesson_repository.dart';
```

### Step 2: Replace Provider Usage

#### Option A: Gradual Migration (Recommended)

Keep old providers, update UI components one by one:

```dart
// In a widget
// Before
final urns = ref.watch(urnsProvider);

// After
final urns = ref.watch(urnsOfflineFirstProvider);
```

#### Option B: Direct Replacement

Replace old provider implementation:

```dart
@riverpod
Future<List<Urn>> urns(Ref ref) async {
  // Old implementation removed
  // Delegate to new provider
  return ref.watch(urnsOfflineFirstProvider.future);
}
```

### Step 3: Update Error Handling

The new pattern uses `Either<Failure, T>` internally but throws exceptions at the provider level for Riverpod compatibility.

```dart
// Error handling remains the same in UI
final urnsAsync = ref.watch(urnsOfflineFirstProvider);

urnsAsync.when(
  data: (urns) => /* success */,
  loading: () => /* loading */,
  error: (error, stack) => /* error */,
);
```

### Step 4: Handle Offline Operations

For write operations, handle the "queued for sync" scenario:

```dart
final completion = ref.read(lessonCompletionOfflineFirstProvider.notifier);
final result = await completion.completeLesson(motifId);

if (result == null) {
  // Operation was queued for sync
  ScaffoldMessenger.of(context).showSnackBar(
    const SnackBar(
      content: Text('Saved offline. Will sync when online.'),
      backgroundColor: Colors.orange,
    ),
  );
} else {
  // Operation succeeded
  ScaffoldMessenger.of(context).showSnackBar(
    const SnackBar(content: Text('Lesson completed!')),
  );
}
```

### Step 5: Add Sync Status UI (Optional)

Add a sync indicator to your app:

```dart
class MyAppBar extends ConsumerWidget implements PreferredSizeWidget {
  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final pendingCount = ref.watch(pendingSyncCountProvider);

    return AppBar(
      title: const Text('My App'),
      actions: [
        if (pendingCount.hasValue && pendingCount.value! > 0)
          IconButton(
            icon: Badge(
              label: Text('${pendingCount.value}'),
              child: const Icon(Icons.sync),
            ),
            onPressed: () {
              ref.read(syncNotifierProvider.notifier).triggerSync();
            },
          ),
      ],
    );
  }

  @override
  Size get preferredSize => const Size.fromHeight(kToolbarHeight);
}
```

## Common Scenarios

### Scenario 1: List + Detail Views

```dart
// List Screen
class UrnsListScreen extends ConsumerWidget {
  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final urnsAsync = ref.watch(urnsOfflineFirstProvider);

    return urnsAsync.when(
      data: (urns) => ListView.builder(
        itemCount: urns.length,
        itemBuilder: (context, index) {
          final urn = urns[index];
          return ListTile(
            title: Text(urn.name),
            onTap: () => context.push('/urns/${urn.slug}'),
          );
        },
      ),
      loading: () => const CircularProgressIndicator(),
      error: (error, _) => ErrorWidget(error.toString()),
    );
  }
}

// Detail Screen
class UrnDetailScreen extends ConsumerWidget {
  final String slug;

  const UrnDetailScreen({required this.slug});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final urnDetailAsync = ref.watch(urnDetailOfflineFirstProvider(slug));

    return urnDetailAsync.when(
      data: (urnDetail) => /* show detail */,
      loading: () => const CircularProgressIndicator(),
      error: (error, _) => ErrorWidget(error.toString()),
    );
  }
}
```

### Scenario 2: Form Submission with Offline Support

```dart
class QuizScreen extends ConsumerStatefulWidget {
  final String motifId;
  
  const QuizScreen({required this.motifId});

  @override
  ConsumerState<QuizScreen> createState() => _QuizScreenState();
}

class _QuizScreenState extends ConsumerState<QuizScreen> {
  final List<QuizAnswerDto> answers = [];

  Future<void> _submitQuiz() async {
    final notifier = ref.read(quizSubmissionOfflineFirstProvider.notifier);
    
    final result = await notifier.submitQuiz(
      motifId: widget.motifId,
      answers: answers,
      timeTakenSeconds: 120,
    );

    if (!mounted) return;

    if (result == null) {
      // Queued for sync
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Quiz saved. Will submit when online.'),
          backgroundColor: Colors.orange,
        ),
      );
    } else if (result.passed) {
      // Success
      context.push('/quiz-result', extra: result);
    } else {
      // Failed but submitted
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('Score: ${result.score}/${result.totalQuestions}'),
          backgroundColor: Colors.red,
        ),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    final quizState = ref.watch(quizSubmissionOfflineFirstProvider);

    return Scaffold(
      body: /* quiz UI */,
      bottomNavigationBar: Padding(
        padding: const EdgeInsets.all(16),
        child: ElevatedButton(
          onPressed: quizState.isLoading ? null : _submitQuiz,
          child: quizState.isLoading
              ? const CircularProgressIndicator()
              : const Text('Submit'),
        ),
      ),
    );
  }
}
```

## Testing Your Migration

### Checklist

1. [ ] App starts without errors
2. [ ] Data loads correctly when online
3. [ ] Cached data shows when offline
4. [ ] Write operations queue when offline
5. [ ] Sync happens automatically when back online
6. [ ] Error messages are user-friendly
7. [ ] Loading states work correctly

### Test Script

```bash
# 1. Start app with network
flutter run

# 2. Navigate to content (check data loads)

# 3. Turn off network (airplane mode)

# 4. Navigate around (check cache works)

# 5. Try to submit data (check queuing works)

# 6. Turn network back on

# 7. Watch console for sync messages
# Expected: [SYNC] Network restored - starting sync
```

## Rollback Plan

If you need to rollback:

1. Remove/comment out imports of new repositories
2. Restore old provider implementations
3. Update UI to use old providers
4. The new files won't affect anything if not imported

## Support

- **Issues?** Check `OFFLINE_FIRST_IMPLEMENTATION.md`
- **Examples?** See `offline_first_example_screen.dart`
- **Quick Ref?** See `OFFLINE_FIRST_QUICK_REFERENCE.md`

---

**Ready to migrate?** Start with one feature at a time!
