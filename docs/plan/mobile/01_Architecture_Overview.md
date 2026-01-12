# 01_Architecture_Overview.md — Flutter App Architecture

## Overview

This document defines the architecture, folder structure, and technical decisions for the Luuniensuki LMS Flutter mobile app.

## Architecture Pattern: Clean Architecture + Riverpod

We adopt a simplified Clean Architecture with three layers:

```
┌─────────────────────────────────────────────────────────────┐
│                    PRESENTATION LAYER                        │
│  (Screens, Widgets, Controllers/Notifiers)                  │
├─────────────────────────────────────────────────────────────┤
│                     DOMAIN LAYER                             │
│  (Entities, Repositories Interfaces, Use Cases)             │
├─────────────────────────────────────────────────────────────┤
│                      DATA LAYER                              │
│  (API Client, DTOs, Repository Implementations, Local DB)   │
└─────────────────────────────────────────────────────────────┘
```

### Why This Architecture?

1. **Testability:** Each layer can be tested independently
2. **Maintainability:** Clear separation of concerns
3. **Scalability:** Easy to add new features without affecting existing code
4. **API Independence:** Domain layer doesn't depend on API structure

## Folder Structure

```
lib/
├── main.dart                     # App entry point
├── app.dart                      # MaterialApp configuration
├── core/                         # Shared utilities and constants
│   ├── constants/
│   │   ├── api_constants.dart    # API URLs, endpoints
│   │   ├── app_constants.dart    # App-wide constants
│   │   └── asset_paths.dart      # Asset file paths
│   ├── errors/
│   │   ├── exceptions.dart       # Custom exceptions
│   │   └── failures.dart         # Failure classes for error handling
│   ├── network/
│   │   ├── api_client.dart       # Dio client with interceptors
│   │   ├── api_interceptor.dart  # Auth, logging, error interceptors
│   │   └── network_info.dart     # Connectivity checker
│   ├── storage/
│   │   ├── secure_storage.dart   # flutter_secure_storage wrapper
│   │   └── hive_storage.dart     # Hive local database
│   ├── theme/
│   │   ├── app_theme.dart        # ThemeData configuration
│   │   ├── app_colors.dart       # Color palette
│   │   └── app_typography.dart   # Text styles
│   └── utils/
│       ├── extensions.dart       # Dart extensions
│       ├── validators.dart       # Form validators
│       └── date_utils.dart       # Date formatting
│
├── features/                     # Feature modules
│   ├── auth/
│   │   ├── data/
│   │   │   ├── datasources/
│   │   │   │   ├── auth_remote_datasource.dart
│   │   │   │   └── auth_local_datasource.dart
│   │   │   ├── models/
│   │   │   │   ├── user_dto.dart
│   │   │   │   └── auth_response_dto.dart
│   │   │   └── repositories/
│   │   │       └── auth_repository_impl.dart
│   │   ├── domain/
│   │   │   ├── entities/
│   │   │   │   └── user.dart
│   │   │   ├── repositories/
│   │   │   │   └── auth_repository.dart
│   │   │   └── usecases/
│   │   │       ├── login_usecase.dart
│   │   │       ├── register_usecase.dart
│   │   │       └── logout_usecase.dart
│   │   └── presentation/
│   │       ├── providers/
│   │       │   └── auth_provider.dart
│   │       ├── screens/
│   │       │   ├── login_screen.dart
│   │       │   └── register_screen.dart
│   │       └── widgets/
│   │           ├── login_form.dart
│   │           └── social_login_buttons.dart
│   │
│   ├── explore/
│   │   ├── data/
│   │   ├── domain/
│   │   └── presentation/
│   │
│   ├── urn_viewer/
│   │   ├── data/
│   │   ├── domain/
│   │   └── presentation/
│   │
│   ├── lesson/
│   │   ├── data/
│   │   ├── domain/
│   │   └── presentation/
│   │
│   ├── quiz/
│   │   ├── data/
│   │   ├── domain/
│   │   └── presentation/
│   │
│   ├── collection/
│   │   ├── data/
│   │   ├── domain/
│   │   └── presentation/
│   │
│   ├── gamification/
│   │   ├── data/
│   │   ├── domain/
│   │   └── presentation/
│   │
│   ├── quests/
│   │   ├── data/
│   │   ├── domain/
│   │   └── presentation/
│   │
│   └── profile/
│       ├── data/
│       ├── domain/
│       └── presentation/
│
├── routing/
│   ├── app_router.dart           # GoRouter configuration
│   ├── route_names.dart          # Route name constants
│   └── route_guards.dart         # Auth guards
│
└── shared/
    ├── widgets/
    │   ├── app_scaffold.dart     # Common scaffold with nav
    │   ├── loading_widget.dart
    │   ├── error_widget.dart
    │   ├── empty_state.dart
    │   ├── cached_image.dart
    │   └── xp_badge.dart
    └── providers/
        └── shared_providers.dart # App-wide providers

test/
├── unit/                         # Unit tests
├── widget/                       # Widget tests
└── integration/                  # Integration tests

assets/
├── images/
├── icons/
├── fonts/
└── animations/                   # Lottie files
```

## State Management: Riverpod 2.x

### Why Riverpod?

1. **Compile-time safety:** No runtime errors from missing providers
2. **Testability:** Easy to override providers in tests
3. **Code generation:** Less boilerplate with riverpod_generator
4. **Scoping:** Auto-dispose when not needed

### Provider Types

```dart
// 1. Simple state - use StateProvider
final counterProvider = StateProvider<int>((ref) => 0);

// 2. Async data fetching - use FutureProvider
final urnsProvider = FutureProvider<List<Urn>>((ref) async {
  final repository = ref.watch(urnRepositoryProvider);
  return repository.getUrns();
});

// 3. Complex state with methods - use Notifier
@riverpod
class AuthNotifier extends _$AuthNotifier {
  @override
  AuthState build() => const AuthState.initial();

  Future<void> login(String email, String password) async {
    state = const AuthState.loading();
    final result = await ref.read(loginUseCaseProvider).execute(email, password);
    result.fold(
      (failure) => state = AuthState.error(failure.message),
      (user) => state = AuthState.authenticated(user),
    );
  }
}

// 4. Async state with methods - use AsyncNotifier
@riverpod
class MotifProgress extends _$MotifProgress {
  @override
  Future<UserProgress> build(String motifId) async {
    return ref.read(progressRepositoryProvider).getProgress(motifId);
  }

  Future<void> unlock() async {
    state = const AsyncValue.loading();
    state = await AsyncValue.guard(() => 
      ref.read(progressRepositoryProvider).unlockMotif(arg)
    );
  }
}
```

### Provider Organization

```dart
// features/auth/presentation/providers/auth_provider.dart

// Repository provider (from data layer)
@riverpod
AuthRepository authRepository(AuthRepositoryRef ref) {
  return AuthRepositoryImpl(
    remoteDataSource: ref.watch(authRemoteDataSourceProvider),
    localDataSource: ref.watch(authLocalDataSourceProvider),
    networkInfo: ref.watch(networkInfoProvider),
  );
}

// Use case providers (from domain layer)
@riverpod
LoginUseCase loginUseCase(LoginUseCaseRef ref) {
  return LoginUseCase(ref.watch(authRepositoryProvider));
}

// State notifier (presentation layer)
@riverpod
class AuthNotifier extends _$AuthNotifier {
  // ... implementation
}
```

## Navigation: GoRouter

### Router Configuration

```dart
// routing/app_router.dart

final routerProvider = Provider<GoRouter>((ref) {
  final authState = ref.watch(authNotifierProvider);
  
  return GoRouter(
    initialLocation: '/',
    refreshListenable: GoRouterRefreshStream(authState),
    redirect: (context, state) {
      final isLoggedIn = authState.isAuthenticated;
      final isAuthRoute = state.matchedLocation.startsWith('/auth');
      
      if (!isLoggedIn && !isAuthRoute) {
        return '/auth/login?returnUrl=${state.matchedLocation}';
      }
      if (isLoggedIn && isAuthRoute) {
        return '/';
      }
      return null;
    },
    routes: [
      // Shell route for bottom navigation
      ShellRoute(
        builder: (context, state, child) => MainShell(child: child),
        routes: [
          GoRoute(
            path: '/',
            name: RouteNames.home,
            builder: (context, state) => const HomeScreen(),
          ),
          GoRoute(
            path: '/explore',
            name: RouteNames.explore,
            builder: (context, state) => const ExploreScreen(),
          ),
          GoRoute(
            path: '/collection',
            name: RouteNames.collection,
            builder: (context, state) => const CollectionScreen(),
          ),
          GoRoute(
            path: '/achievements',
            name: RouteNames.achievements,
            builder: (context, state) => const AchievementsScreen(),
          ),
          GoRoute(
            path: '/profile',
            name: RouteNames.profile,
            builder: (context, state) => const ProfileScreen(),
          ),
        ],
      ),
      // Auth routes (no shell)
      GoRoute(
        path: '/auth/login',
        name: RouteNames.login,
        builder: (context, state) => const LoginScreen(),
      ),
      GoRoute(
        path: '/auth/register',
        name: RouteNames.register,
        builder: (context, state) => const RegisterScreen(),
      ),
      // Detail routes (no shell, full screen)
      GoRoute(
        path: '/urns/:urnSlug',
        name: RouteNames.urnViewer,
        builder: (context, state) => UrnViewerScreen(
          urnSlug: state.pathParameters['urnSlug']!,
        ),
      ),
      GoRoute(
        path: '/motif/:motifId',
        name: RouteNames.motifDetail,
        builder: (context, state) => MotifDetailScreen(
          motifId: state.pathParameters['motifId']!,
        ),
        routes: [
          GoRoute(
            path: 'quiz',
            name: RouteNames.quiz,
            builder: (context, state) => QuizScreen(
              motifId: state.pathParameters['motifId']!,
            ),
          ),
        ],
      ),
      GoRoute(
        path: '/quests/:questSlug',
        name: RouteNames.questDetail,
        builder: (context, state) => QuestDetailScreen(
          questSlug: state.pathParameters['questSlug']!,
        ),
      ),
    ],
  );
});
```

## Dependency Injection

All dependencies are provided via Riverpod providers:

```dart
// core/network/providers.dart

@riverpod
Dio dio(DioRef ref) {
  final dio = Dio(BaseOptions(
    baseUrl: ApiConstants.baseUrl,
    connectTimeout: const Duration(seconds: 30),
    receiveTimeout: const Duration(seconds: 30),
  ));
  
  dio.interceptors.addAll([
    AuthInterceptor(ref.watch(secureStorageProvider)),
    LoggingInterceptor(),
    ErrorInterceptor(),
  ]);
  
  return dio;
}

@riverpod
ApiClient apiClient(ApiClientRef ref) {
  return ApiClient(ref.watch(dioProvider));
}

@riverpod
NetworkInfo networkInfo(NetworkInfoRef ref) {
  return NetworkInfoImpl(Connectivity());
}
```

## Error Handling

### Either Pattern with dartz

```dart
// domain/repositories/auth_repository.dart
abstract class AuthRepository {
  Future<Either<Failure, User>> login(String email, String password);
  Future<Either<Failure, User>> register(String email, String password, String displayName);
  Future<Either<Failure, void>> logout();
}

// data/repositories/auth_repository_impl.dart
class AuthRepositoryImpl implements AuthRepository {
  @override
  Future<Either<Failure, User>> login(String email, String password) async {
    try {
      if (!await networkInfo.isConnected) {
        return Left(NetworkFailure('No internet connection'));
      }
      
      final response = await remoteDataSource.login(email, password);
      await localDataSource.cacheUser(response.user);
      await localDataSource.cacheTokens(response.accessToken, response.refreshToken);
      
      return Right(response.user.toEntity());
    } on ServerException catch (e) {
      return Left(ServerFailure(e.message));
    } on CacheException catch (e) {
      return Left(CacheFailure(e.message));
    } catch (e) {
      return Left(UnknownFailure(e.toString()));
    }
  }
}
```

### Failure Classes

```dart
// core/errors/failures.dart

abstract class Failure {
  final String message;
  final String? code;
  
  const Failure(this.message, {this.code});
}

class ServerFailure extends Failure {
  const ServerFailure(super.message, {super.code});
}

class NetworkFailure extends Failure {
  const NetworkFailure(super.message);
}

class CacheFailure extends Failure {
  const CacheFailure(super.message);
}

class AuthFailure extends Failure {
  const AuthFailure(super.message, {super.code});
}

class ValidationFailure extends Failure {
  final Map<String, List<String>> fieldErrors;
  
  const ValidationFailure(super.message, {this.fieldErrors = const {}});
}
```

## Local Storage

### Secure Storage (for tokens)

```dart
// core/storage/secure_storage.dart

abstract class SecureStorage {
  Future<void> saveAccessToken(String token);
  Future<String?> getAccessToken();
  Future<void> saveRefreshToken(String token);
  Future<String?> getRefreshToken();
  Future<void> clearTokens();
}

class SecureStorageImpl implements SecureStorage {
  final FlutterSecureStorage _storage;
  
  static const _accessTokenKey = 'access_token';
  static const _refreshTokenKey = 'refresh_token';
  
  SecureStorageImpl(this._storage);
  
  @override
  Future<void> saveAccessToken(String token) async {
    await _storage.write(key: _accessTokenKey, value: token);
  }
  
  // ... other methods
}
```

### Hive (for cached data)

```dart
// core/storage/hive_storage.dart

abstract class CacheStorage {
  Future<void> cacheUrns(List<UrnDto> urns);
  Future<List<UrnDto>?> getCachedUrns();
  Future<void> cacheMotifProgress(String motifId, ProgressDto progress);
  Future<ProgressDto?> getCachedProgress(String motifId);
  Future<void> clearCache();
}

class HiveCacheStorage implements CacheStorage {
  static const _urnsBox = 'urns_cache';
  static const _progressBox = 'progress_cache';
  
  @override
  Future<void> cacheUrns(List<UrnDto> urns) async {
    final box = await Hive.openBox<UrnDto>(_urnsBox);
    await box.clear();
    await box.addAll(urns);
  }
  
  // ... other methods
}
```

## Theme System

```dart
// core/theme/app_theme.dart

class AppTheme {
  static ThemeData get lightTheme => ThemeData(
    useMaterial3: true,
    colorScheme: ColorScheme.fromSeed(
      seedColor: AppColors.primary,
      brightness: Brightness.light,
    ),
    textTheme: AppTypography.textTheme,
    appBarTheme: const AppBarTheme(
      centerTitle: true,
      elevation: 0,
    ),
    cardTheme: CardTheme(
      elevation: 2,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(12),
      ),
    ),
    inputDecorationTheme: InputDecorationTheme(
      border: OutlineInputBorder(
        borderRadius: BorderRadius.circular(8),
      ),
      filled: true,
    ),
  );
  
  static ThemeData get darkTheme => ThemeData(
    useMaterial3: true,
    colorScheme: ColorScheme.fromSeed(
      seedColor: AppColors.primary,
      brightness: Brightness.dark,
    ),
    textTheme: AppTypography.textTheme,
    // ... dark theme customizations
  );
}

// core/theme/app_colors.dart
class AppColors {
  static const primary = Color(0xFFD4AF37);      // Vietnamese gold
  static const secondary = Color(0xFF8B0000);    // Imperial red
  static const background = Color(0xFFF5F0E6);   // Parchment
  static const surface = Color(0xFFFFFFFF);
  static const error = Color(0xFFB00020);
  
  // XP/Rank colors
  static const xpGold = Color(0xFFFFD700);
  static const streakOrange = Color(0xFFFF6B35);
  
  // Status colors
  static const discovered = Color(0xFF4CAF50);
  static const learned = Color(0xFF2196F3);
  static const mastered = Color(0xFF9C27B0);
}
```

## Key Dependencies

```yaml
# pubspec.yaml

dependencies:
  flutter:
    sdk: flutter
  
  # State Management
  flutter_riverpod: ^2.4.9
  riverpod_annotation: ^2.3.3
  
  # Navigation
  go_router: ^13.0.0
  
  # Networking
  dio: ^5.4.0
  connectivity_plus: ^5.0.2
  
  # Local Storage
  hive_flutter: ^1.1.0
  flutter_secure_storage: ^9.0.0
  
  # 3D Rendering
  model_viewer_plus: ^1.6.0
  # Alternative: flutter_3d_controller
  
  # UI Components
  cached_network_image: ^3.3.1
  shimmer: ^3.0.0
  lottie: ^3.0.0
  flutter_svg: ^2.0.9
  
  # Media
  just_audio: ^0.9.36
  video_player: ^2.8.2
  photo_view: ^0.14.0
  
  # Utilities
  dartz: ^0.10.1
  freezed_annotation: ^2.4.1
  json_annotation: ^4.8.1
  intl: ^0.18.1
  equatable: ^2.0.5
  
  # Firebase (optional)
  firebase_core: ^2.24.2
  firebase_messaging: ^14.7.10

dev_dependencies:
  flutter_test:
    sdk: flutter
  
  # Code Generation
  build_runner: ^2.4.8
  riverpod_generator: ^2.3.9
  freezed: ^2.4.6
  json_serializable: ^6.7.1
  
  # Testing
  mocktail: ^1.0.2
  
  # Linting
  flutter_lints: ^3.0.1
```

## Code Generation

Run after modifying annotated files:

```bash
# One-time generation
dart run build_runner build --delete-conflicting-outputs

# Watch mode during development
dart run build_runner watch --delete-conflicting-outputs
```

## Architecture Decision Records (ADRs)

### ADR-001: Riverpod over Bloc
**Decision:** Use Riverpod for state management
**Rationale:** 
- Simpler boilerplate than Bloc
- Better compile-time safety
- Easier testing with overrides
- Native support for async values

### ADR-002: GoRouter for Navigation
**Decision:** Use GoRouter instead of Navigator 2.0 directly
**Rationale:**
- Declarative routing
- Deep linking support
- Route guards for auth
- Type-safe path parameters

### ADR-003: Clean Architecture (Simplified)
**Decision:** Use 3-layer architecture without strict Use Case enforcement
**Rationale:**
- Balance between structure and pragmatism
- Use cases only for complex business logic
- Simple CRUD can call repository directly

### ADR-004: Hive for Offline Cache
**Decision:** Use Hive over SQLite
**Rationale:**
- NoSQL fits our JSON API responses
- Faster for simple key-value storage
- Easy to serialize Dart objects
- No native dependencies

### ADR-005: model_viewer_plus for 3D
**Decision:** Use model_viewer_plus for GLB rendering
**Rationale:**
- Based on Google's model-viewer
- WebView-based (works on all devices)
- AR support built-in
- Good performance for our model sizes
- Fallback: flutter_3d_controller for more control