# 15_Phase6_Offline_Polish.md — Offline Support & Polish

## Overview

Phase 6 implements offline caching, performance optimization, error handling improvements, and final polish before release.

**Duration:** 2 weeks  
**Priority:** P1 (High)  
**Prerequisites:** Phase 5 (Gamification) completed

---

## Week 1: Offline Support & Caching

### Task 6.1: Implement Hive Cache Layer

**Estimated Time:** 4 hours

**File: `lib/core/storage/cache_manager.dart`**

```dart
import 'package:hive_flutter/hive_flutter.dart';

class CacheManager {
  static const _urnsBox = 'urns_cache';
  static const _motifsBox = 'motifs_cache';
  static const _progressBox = 'progress_cache';
  static const _lessonsBox = 'lessons_cache';
  static const _userBox = 'user_cache';
  
  static Future<void> init() async {
    await Hive.initFlutter();
    
    // Register adapters
    Hive.registerAdapter(CachedUrnAdapter());
    Hive.registerAdapter(CachedMotifAdapter());
    Hive.registerAdapter(CachedProgressAdapter());
    Hive.registerAdapter(CachedLessonAdapter());
    
    // Open boxes
    await Future.wait([
      Hive.openBox<CachedUrn>(_urnsBox),
      Hive.openBox<CachedMotif>(_motifsBox),
      Hive.openBox<CachedProgress>(_progressBox),
      Hive.openBox<CachedLesson>(_lessonsBox),
      Hive.openBox(_userBox),
    ]);
  }
  
  // Urns
  static Box<CachedUrn> get urnsBox => Hive.box<CachedUrn>(_urnsBox);
  
  static Future<void> cacheUrns(List<UrnDto> urns) async {
    final box = urnsBox;
    await box.clear();
    for (final urn in urns) {
      await box.put(urn.slug, CachedUrn.fromDto(urn));
    }
  }
  
  static List<UrnDto>? getCachedUrns() {
    final box = urnsBox;
    if (box.isEmpty) return null;
    return box.values.map((e) => e.toDto()).toList();
  }
  
  // Motifs
  static Box<CachedMotif> get motifsBox => Hive.box<CachedMotif>(_motifsBox);
  
  static Future<void> cacheMotif(MotifDetailDto motif) async {
    await motifsBox.put(motif.motif.id, CachedMotif.fromDto(motif));
  }
  
  static MotifDetailDto? getCachedMotif(String id) {
    final cached = motifsBox.get(id);
    return cached?.toDto();
  }
  
  // Progress
  static Box<CachedProgress> get progressBox => Hive.box<CachedProgress>(_progressBox);
  
  static Future<void> cacheProgress(String motifId, ProgressDto progress) async {
    await progressBox.put(motifId, CachedProgress.fromDto(progress));
  }
  
  static ProgressDto? getCachedProgress(String motifId) {
    return progressBox.get(motifId)?.toDto();
  }
  
  // Lessons
  static Box<CachedLesson> get lessonsBox => Hive.box<CachedLesson>(_lessonsBox);
  
  static Future<void> cacheLesson(String motifId, LessonContentDto lesson) async {
    await lessonsBox.put(motifId, CachedLesson.fromDto(lesson));
  }
  
  static LessonContentDto? getCachedLesson(String motifId) {
    return lessonsBox.get(motifId)?.toDto();
  }
  
  // Clear all cache
  static Future<void> clearAll() async {
    await Future.wait([
      urnsBox.clear(),
      motifsBox.clear(),
      progressBox.clear(),
      lessonsBox.clear(),
    ]);
  }
  
  // Cache size info
  static Future<int> getCacheSize() async {
    int total = 0;
    for (final box in [urnsBox, motifsBox, progressBox, lessonsBox]) {
      // Approximate size
      total += box.length * 1024; // Rough estimate
    }
    return total;
  }
}
```

**Acceptance Criteria:**
- [ ] Hive initialized on app start
- [ ] Urns cached after API fetch
- [ ] Motifs cached on view
- [ ] Progress cached on update
- [ ] Clear cache functionality

---

### Task 6.2: Implement Offline-First Repository Pattern

**Estimated Time:** 6 hours

**File: `lib/features/explore/data/repositories/urn_repository_impl.dart`**

```dart
class UrnRepositoryImpl implements UrnRepository {
  final UrnRemoteDataSource remoteDataSource;
  final CacheManager cacheManager;
  final NetworkInfo networkInfo;
  
  UrnRepositoryImpl({
    required this.remoteDataSource,
    required this.cacheManager,
    required this.networkInfo,
  });
  
  @override
  Future<Either<Failure, List<Urn>>> getUrns({bool forceRefresh = false}) async {
    // Check cache first (if not forcing refresh)
    if (!forceRefresh) {
      final cached = CacheManager.getCachedUrns();
      if (cached != null && cached.isNotEmpty) {
        // Return cached data immediately
        _refreshInBackground();
        return Right(cached.map((e) => e.toEntity()).toList());
      }
    }
    
    // Fetch from network
    if (!await networkInfo.isConnected) {
      // Return cached if available, error if not
      final cached = CacheManager.getCachedUrns();
      if (cached != null) {
        return Right(cached.map((e) => e.toEntity()).toList());
      }
      return const Left(NetworkFailure('No internet connection'));
    }
    
    try {
      final urns = await remoteDataSource.getUrns();
      await CacheManager.cacheUrns(urns);
      return Right(urns.map((e) => e.toEntity()).toList());
    } on ServerException catch (e) {
      // Fall back to cache on error
      final cached = CacheManager.getCachedUrns();
      if (cached != null) {
        return Right(cached.map((e) => e.toEntity()).toList());
      }
      return Left(ServerFailure(e.message, code: e.code));
    }
  }
  
  Future<void> _refreshInBackground() async {
    if (!await networkInfo.isConnected) return;
    
    try {
      final urns = await remoteDataSource.getUrns();
      await CacheManager.cacheUrns(urns);
    } catch (_) {
      // Silently fail background refresh
    }
  }
}
```

**Acceptance Criteria:**
- [ ] Returns cached data immediately if available
- [ ] Background refresh when online
- [ ] Graceful fallback on network error
- [ ] Force refresh option

---

### Task 6.3: Implement Network Status Indicator

**Estimated Time:** 2 hours

**File: `lib/shared/widgets/network_status_bar.dart`**

```dart
import 'package:connectivity_plus/connectivity_plus.dart';

class NetworkStatusBar extends ConsumerWidget {
  const NetworkStatusBar({super.key});
  
  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final connectivityAsync = ref.watch(connectivityProvider);
    
    return connectivityAsync.when(
      loading: () => const SizedBox(),
      error: (_, __) => const SizedBox(),
      data: (result) {
        if (result == ConnectivityResult.none) {
          return Container(
            width: double.infinity,
            padding: const EdgeInsets.symmetric(vertical: 4),
            color: Colors.orange,
            child: const Row(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Icon(Icons.wifi_off, color: Colors.white, size: 16),
                SizedBox(width: 8),
                Text(
                  'Không có kết nối mạng',
                  style: TextStyle(color: Colors.white, fontSize: 12),
                ),
              ],
            ),
          );
        }
        return const SizedBox();
      },
    );
  }
}

@riverpod
Stream<ConnectivityResult> connectivity(ConnectivityRef ref) {
  return Connectivity().onConnectivityChanged;
}
```

**Acceptance Criteria:**
- [ ] Shows banner when offline
- [ ] Auto-hides when online
- [ ] Non-intrusive design

---

### Task 6.4: Implement Pending Actions Queue

**Estimated Time:** 4 hours

For actions that fail offline (unlock, complete lesson, quiz submit):

**File: `lib/core/storage/pending_actions_queue.dart`**

```dart
class PendingActionsQueue {
  static const _boxName = 'pending_actions';
  
  static Box<Map> get _box => Hive.box<Map>(_boxName);
  
  static Future<void> init() async {
    await Hive.openBox<Map>(_boxName);
  }
  
  static Future<void> enqueue(PendingAction action) async {
    await _box.add(action.toMap());
  }
  
  static List<PendingAction> getAll() {
    return _box.values.map((e) => PendingAction.fromMap(e)).toList();
  }
  
  static Future<void> remove(int index) async {
    await _box.deleteAt(index);
  }
  
  static Future<void> processQueue(ApiClient apiClient) async {
    final actions = getAll();
    
    for (int i = 0; i < actions.length; i++) {
      final action = actions[i];
      
      try {
        switch (action.type) {
          case ActionType.unlockMotif:
            await apiClient.post(
              ApiConstants.progressUnlock,
              data: {'motif_id': action.data['motifId']},
            );
            break;
          case ActionType.completeLesson:
            await apiClient.post(
              ApiConstants.progressCompleteLesson,
              data: {'motif_id': action.data['motifId']},
            );
            break;
          case ActionType.submitQuiz:
            await apiClient.post(
              ApiConstants.motifQuizSubmit(action.data['motifId']),
              data: action.data['payload'],
            );
            break;
        }
        
        await remove(i);
      } catch (e) {
        // Keep in queue for retry
        break; // Stop processing on first failure
      }
    }
  }
}

enum ActionType { unlockMotif, completeLesson, submitQuiz }

class PendingAction {
  final ActionType type;
  final Map<String, dynamic> data;
  final DateTime createdAt;
  
  PendingAction({
    required this.type,
    required this.data,
    DateTime? createdAt,
  }) : createdAt = createdAt ?? DateTime.now();
  
  Map<String, dynamic> toMap() => {
    'type': type.index,
    'data': data,
    'createdAt': createdAt.toIso8601String(),
  };
  
  factory PendingAction.fromMap(Map map) => PendingAction(
    type: ActionType.values[map['type'] as int],
    data: Map<String, dynamic>.from(map['data']),
    createdAt: DateTime.parse(map['createdAt'] as String),
  );
}
```

**Acceptance Criteria:**
- [ ] Actions queued when offline
- [ ] Auto-process when back online
- [ ] Retry logic for failed actions
- [ ] Queue persistence across app restart

---

## Week 2: Performance & Polish

### Task 6.5: Implement Image Pre-caching

**Estimated Time:** 3 hours

**File: `lib/core/utils/image_precache.dart`**

```dart
class ImagePrecache {
  static Future<void> precacheUrnThumbnails(
    BuildContext context,
    List<Urn> urns,
  ) async {
    for (final urn in urns) {
      if (urn.thumbnailUrl != null) {
        try {
          await precacheImage(
            CachedNetworkImageProvider(urn.thumbnailUrl!),
            context,
          );
        } catch (_) {
          // Ignore precache failures
        }
      }
    }
  }
  
  static Future<void> precacheMotifImages(
    BuildContext context,
    List<Motif> motifs,
  ) async {
    for (final motif in motifs) {
      if (motif.thumbnailUrl != null) {
        try {
          await precacheImage(
            CachedNetworkImageProvider(motif.thumbnailUrl!),
            context,
          );
        } catch (_) {
          // Ignore precache failures
        }
      }
    }
  }
}
```

**Acceptance Criteria:**
- [ ] Thumbnails precached on first load
- [ ] Non-blocking precache
- [ ] Cached images used on subsequent views

---

### Task 6.6: Implement Model Pre-download

**Estimated Time:** 3 hours

**File: `lib/core/utils/model_preloader.dart`**

```dart
class ModelPreloader {
  static final Map<String, String> _downloadedModels = {};
  static final Set<String> _downloading = {};
  
  static Future<String?> preloadModel(String url) async {
    if (_downloadedModels.containsKey(url)) {
      return _downloadedModels[url];
    }
    
    if (_downloading.contains(url)) {
      // Wait for existing download
      while (_downloading.contains(url)) {
        await Future.delayed(const Duration(milliseconds: 100));
      }
      return _downloadedModels[url];
    }
    
    _downloading.add(url);
    
    try {
      final cacheDir = await getTemporaryDirectory();
      final fileName = url.split('/').last;
      final filePath = '${cacheDir.path}/models/$fileName';
      
      final file = File(filePath);
      if (await file.exists()) {
        _downloadedModels[url] = filePath;
        _downloading.remove(url);
        return filePath;
      }
      
      // Create directory
      await Directory('${cacheDir.path}/models').create(recursive: true);
      
      // Download
      await Dio().download(url, filePath);
      
      _downloadedModels[url] = filePath;
      _downloading.remove(url);
      return filePath;
    } catch (e) {
      _downloading.remove(url);
      return null;
    }
  }
  
  static Future<void> preloadAllModels(List<Urn> urns) async {
    for (final urn in urns) {
      if (urn.modelUrl != null) {
        unawaited(preloadModel(urn.modelUrl!));
      }
    }
  }
  
  static Future<int> getCacheSize() async {
    final cacheDir = await getTemporaryDirectory();
    final modelsDir = Directory('${cacheDir.path}/models');
    
    if (!await modelsDir.exists()) return 0;
    
    int total = 0;
    await for (final file in modelsDir.list()) {
      if (file is File) {
        total += await file.length();
      }
    }
    return total;
  }
  
  static Future<void> clearCache() async {
    final cacheDir = await getTemporaryDirectory();
    final modelsDir = Directory('${cacheDir.path}/models');
    
    if (await modelsDir.exists()) {
      await modelsDir.delete(recursive: true);
    }
    
    _downloadedModels.clear();
  }
}
```

**Acceptance Criteria:**
- [ ] Models downloaded in background
- [ ] Local path returned for cached models
- [ ] Cache size tracking
- [ ] Clear cache option

---

### Task 6.7: Implement App-wide Error Handling

**Estimated Time:** 3 hours

**File: `lib/core/utils/error_handler.dart`**

```dart
class ErrorHandler {
  static void init() {
    FlutterError.onError = (details) {
      FlutterError.presentError(details);
      _logError(details.exception, details.stack);
    };
    
    PlatformDispatcher.instance.onError = (error, stack) {
      _logError(error, stack);
      return true;
    };
  }
  
  static void _logError(Object error, StackTrace? stack) {
    // Log to console in debug
    if (kDebugMode) {
      debugPrint('Error: $error');
      debugPrint('Stack: $stack');
    }
    
    // TODO: Send to crash reporting service (e.g., Firebase Crashlytics)
  }
  
  static String getUserFriendlyMessage(Object error) {
    if (error is NetworkFailure) {
      return 'Không có kết nối mạng. Vui lòng kiểm tra lại.';
    }
    if (error is AuthFailure) {
      return 'Phiên đăng nhập hết hạn. Vui lòng đăng nhập lại.';
    }
    if (error is ServerFailure) {
      return error.message;
    }
    if (error is ValidationFailure) {
      return error.message;
    }
    return 'Đã xảy ra lỗi. Vui lòng thử lại sau.';
  }
}

// Global error display
void showErrorSnackBar(BuildContext context, Object error) {
  ScaffoldMessenger.of(context).showSnackBar(
    SnackBar(
      content: Text(ErrorHandler.getUserFriendlyMessage(error)),
      backgroundColor: Theme.of(context).colorScheme.error,
      action: SnackBarAction(
        label: 'Đóng',
        textColor: Colors.white,
        onPressed: () {},
      ),
    ),
  );
}
```

**Acceptance Criteria:**
- [ ] Global error handler initialized
- [ ] User-friendly Vietnamese messages
- [ ] Snackbar for displaying errors
- [ ] Error logging for debugging

---

### Task 6.8: Implement Settings Screen

**Estimated Time:** 3 hours

**File: `lib/features/profile/presentation/screens/settings_screen.dart`**

```dart
class SettingsScreen extends ConsumerWidget {
  const SettingsScreen({super.key});
  
  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return Scaffold(
      appBar: AppBar(title: const Text('Cài đặt')),
      body: ListView(
        children: [
          // Account section
          _SectionHeader(title: 'Tài khoản'),
          ListTile(
            leading: const Icon(Icons.person_outline),
            title: const Text('Chỉnh sửa hồ sơ'),
            trailing: const Icon(Icons.chevron_right),
            onTap: () => context.push('/profile/edit'),
          ),
          ListTile(
            leading: const Icon(Icons.lock_outline),
            title: const Text('Đổi mật khẩu'),
            trailing: const Icon(Icons.chevron_right),
            onTap: () => context.push('/profile/change-password'),
          ),
          
          const Divider(),
          
          // App settings section
          _SectionHeader(title: 'Ứng dụng'),
          SwitchListTile(
            secondary: const Icon(Icons.dark_mode_outlined),
            title: const Text('Chế độ tối'),
            value: ref.watch(themeModeProvider) == ThemeMode.dark,
            onChanged: (value) {
              ref.read(themeModeProvider.notifier).state = 
                  value ? ThemeMode.dark : ThemeMode.light;
            },
          ),
          SwitchListTile(
            secondary: const Icon(Icons.notifications_outlined),
            title: const Text('Thông báo'),
            value: ref.watch(notificationsEnabledProvider),
            onChanged: (value) {
              ref.read(notificationsEnabledProvider.notifier).state = value;
            },
          ),
          
          const Divider(),
          
          // Cache section
          _SectionHeader(title: 'Bộ nhớ đệm'),
          FutureBuilder<int>(
            future: _getCacheSize(),
            builder: (context, snapshot) {
              final size = snapshot.data ?? 0;
              return ListTile(
                leading: const Icon(Icons.storage_outlined),
                title: const Text('Dung lượng cache'),
                subtitle: Text(_formatBytes(size)),
                trailing: TextButton(
                  onPressed: () => _clearCache(context, ref),
                  child: const Text('Xóa'),
                ),
              );
            },
          ),
          
          const Divider(),
          
          // About section
          _SectionHeader(title: 'Thông tin'),
          ListTile(
            leading: const Icon(Icons.info_outline),
            title: const Text('Phiên bản'),
            subtitle: const Text('1.0.0'),
          ),
          ListTile(
            leading: const Icon(Icons.description_outlined),
            title: const Text('Điều khoản sử dụng'),
            trailing: const Icon(Icons.chevron_right),
            onTap: () => _openTerms(context),
          ),
          ListTile(
            leading: const Icon(Icons.privacy_tip_outlined),
            title: const Text('Chính sách bảo mật'),
            trailing: const Icon(Icons.chevron_right),
            onTap: () => _openPrivacy(context),
          ),
          
          const Divider(),
          
          // Logout
          ListTile(
            leading: const Icon(Icons.logout, color: Colors.red),
            title: const Text('Đăng xuất', style: TextStyle(color: Colors.red)),
            onTap: () => _confirmLogout(context, ref),
          ),
          
          const SizedBox(height: 32),
        ],
      ),
    );
  }
  
  Future<int> _getCacheSize() async {
    final hiveSize = await CacheManager.getCacheSize();
    final modelSize = await ModelPreloader.getCacheSize();
    return hiveSize + modelSize;
  }
  
  String _formatBytes(int bytes) {
    if (bytes < 1024) return '$bytes B';
    if (bytes < 1024 * 1024) return '${(bytes / 1024).toStringAsFixed(1)} KB';
    return '${(bytes / (1024 * 1024)).toStringAsFixed(1)} MB';
  }
  
  Future<void> _clearCache(BuildContext context, WidgetRef ref) async {
    await CacheManager.clearAll();
    await ModelPreloader.clearCache();
    
    if (context.mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Đã xóa bộ nhớ đệm')),
      );
    }
  }
}

class _SectionHeader extends StatelessWidget {
  final String title;
  
  const _SectionHeader({required this.title});
  
  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.fromLTRB(16, 16, 16, 8),
      child: Text(
        title,
        style: Theme.of(context).textTheme.titleSmall?.copyWith(
          color: Theme.of(context).colorScheme.primary,
          fontWeight: FontWeight.bold,
        ),
      ),
    );
  }
}
```

**Acceptance Criteria:**
- [ ] Account settings
- [ ] Theme toggle
- [ ] Notifications toggle
- [ ] Cache management
- [ ] App info and legal links
- [ ] Logout

---

### Task 6.9: Performance Optimization

**Estimated Time:** 4 hours

**Optimizations to implement:**

1. **Lazy loading for lists**
```dart
// Use ListView.builder with cacheExtent
ListView.builder(
  cacheExtent: 500,
  itemBuilder: (context, index) => ...,
)
```

2. **Image optimization**
```dart
// Use memCacheWidth/memCacheHeight
CachedNetworkImage(
  imageUrl: url,
  memCacheWidth: 200, // Max width in memory
  memCacheHeight: 200,
)
```

3. **Widget const constructors**
```dart
// Ensure all static widgets use const
const SizedBox(height: 16),
const Icon(Icons.star),
```

4. **Avoid rebuilds with select**
```dart
// Only rebuild when specific value changes
ref.watch(authNotifierProvider.select((s) => s.user?.totalXp))
```

5. **Debounce search**
```dart
// Debounce text input
final searchQuery = useState('');
useEffect(() {
  final timer = Timer(Duration(milliseconds: 300), () {
    ref.read(searchProvider.notifier).search(searchQuery.value);
  });
  return timer.cancel;
}, [searchQuery.value]);
```

**Acceptance Criteria:**
- [ ] App cold start < 3 seconds
- [ ] Smooth 60fps scrolling
- [ ] No jank on screen transitions
- [ ] Memory usage < 200MB typical

---

## Phase 6 Checklist

### Offline Support
- [ ] P6-O1: Hive cache layer implemented
- [ ] P6-O2: Offline-first repositories
- [ ] P6-O3: Network status indicator
- [ ] P6-O4: Pending actions queue
- [ ] P6-O5: Auto-sync when online

### Caching
- [ ] P6-C1: Image precaching
- [ ] P6-C2: 3D model preloading
- [ ] P6-C3: Cache size tracking
- [ ] P6-C4: Clear cache functionality

### Error Handling
- [ ] P6-E1: Global error handler
- [ ] P6-E2: User-friendly messages (Vietnamese)
- [ ] P6-E3: Error snackbars
- [ ] P6-E4: Graceful degradation

### Settings
- [ ] P6-S1: Settings screen
- [ ] P6-S2: Theme toggle
- [ ] P6-S3: Notifications toggle
- [ ] P6-S4: Cache management

### Performance
- [ ] P6-P1: Lazy loading lists
- [ ] P6-P2: Image optimization
- [ ] P6-P3: Const constructors
- [ ] P6-P4: Selective rebuilds
- [ ] P6-P5: Input debouncing

---

## Testing Checklist

### Offline Testing
- [ ] Turn off airplane mode, verify cached data shows
- [ ] Complete actions offline, verify queued
- [ ] Go online, verify queue processed
- [ ] Force kill app offline, verify data persists

### Performance Testing
- [ ] Profile with DevTools
- [ ] Check memory usage
- [ ] Verify frame rate
- [ ] Test on low-end device

### Error Scenarios
- [ ] Test network timeout
- [ ] Test API errors (4xx, 5xx)
- [ ] Test expired session
- [ ] Test invalid data

---

## Pre-Release Polish

### UI/UX Review
- [ ] All Vietnamese text correct
- [ ] Consistent spacing and typography
- [ ] Loading states for all async operations
- [ ] Empty states for all lists
- [ ] Error states with retry

### Accessibility
- [ ] Semantic labels for icons
- [ ] Sufficient color contrast
- [ ] Text scaling support
- [ ] Screen reader compatibility

### Final Checks
- [ ] No hardcoded strings (use constants)
- [ ] No debug logs in release
- [ ] Proper error handling everywhere
- [ ] All TODOs addressed