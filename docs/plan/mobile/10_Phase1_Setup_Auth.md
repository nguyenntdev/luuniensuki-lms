# 10_Phase1_Setup_Auth.md — Project Setup & Authentication

## Overview

Phase 1 establishes the Flutter project foundation, configures dependencies, implements the API client, and builds the complete authentication flow.

**Duration:** 2 weeks  
**Priority:** P0 (Critical Path)

---

## Week 1: Project Setup & Core Infrastructure

### Task 1.1: Create Flutter Project

**Estimated Time:** 2 hours

```bash
# Create project with organization
flutter create --org com.luuniensuki --project-name luuniensuki_lms .

# Verify Flutter version
flutter --version  # Should be 3.x

# Run initial build to verify setup
flutter run
```

**Acceptance Criteria:**
- [ ] Project compiles and runs on Android emulator
- [ ] Package name is `com.luuniensuki.lms`
- [ ] Minimum Android SDK is 21 (Android 5.0)

---

### Task 1.2: Configure pubspec.yaml

**Estimated Time:** 1 hour

```yaml
name: luuniensuki_lms
description: Luuniensuki LMS - Vietnamese Cultural Heritage Learning App
publish_to: 'none'
version: 1.0.0+1

environment:
  sdk: '>=3.2.0 <4.0.0'

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
  
  # 3D Rendering (Phase 3)
  model_viewer_plus: ^1.6.0
  
  # UI Components
  cached_network_image: ^3.3.1
  shimmer: ^3.0.0
  lottie: ^3.0.0
  flutter_svg: ^2.0.9
  
  # Media (Phase 4)
  just_audio: ^0.9.36
  video_player: ^2.8.2
  photo_view: ^0.14.0
  
  # Utilities
  dartz: ^0.10.1
  freezed_annotation: ^2.4.1
  json_annotation: ^4.8.1
  intl: ^0.18.1
  equatable: ^2.0.5
  
  # Icons
  cupertino_icons: ^1.0.6

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

flutter:
  uses-material-design: true
  
  assets:
    - assets/images/
    - assets/icons/
    - assets/animations/
```

**Acceptance Criteria:**
- [ ] All dependencies resolve without conflicts
- [ ] `flutter pub get` succeeds
- [ ] Project still builds after adding dependencies

---

### Task 1.3: Create Folder Structure

**Estimated Time:** 1 hour

```
lib/
├── main.dart
├── app.dart
├── core/
│   ├── constants/
│   │   ├── api_constants.dart
│   │   ├── app_constants.dart
│   │   └── asset_paths.dart
│   ├── errors/
│   │   ├── exceptions.dart
│   │   └── failures.dart
│   ├── network/
│   │   ├── api_client.dart
│   │   ├── dio_provider.dart
│   │   └── interceptors/
│   │       ├── auth_interceptor.dart
│   │       ├── logging_interceptor.dart
│   │       └── error_interceptor.dart
│   ├── storage/
│   │   ├── secure_storage.dart
│   │   └── hive_storage.dart
│   ├── theme/
│   │   ├── app_theme.dart
│   │   ├── app_colors.dart
│   │   └── app_typography.dart
│   └── utils/
│       ├── extensions.dart
│       └── validators.dart
├── features/
│   └── auth/
│       ├── data/
│       │   ├── datasources/
│       │   ├── models/
│       │   └── repositories/
│       ├── domain/
│       │   ├── entities/
│       │   ├── repositories/
│       │   └── usecases/
│       └── presentation/
│           ├── providers/
│           ├── screens/
│           └── widgets/
├── routing/
│   ├── app_router.dart
│   └── route_names.dart
└── shared/
    ├── widgets/
    └── providers/

assets/
├── images/
│   └── logo.png
├── icons/
└── animations/

test/
├── unit/
├── widget/
└── integration/
```

**Acceptance Criteria:**
- [ ] All directories created
- [ ] Empty placeholder files created for each module
- [ ] Assets folders exist with placeholder files

---

### Task 1.4: Implement Core Constants

**Estimated Time:** 1 hour

**File: `lib/core/constants/api_constants.dart`**

```dart
class ApiConstants {
  static const String baseUrl = 'https://lms.histolab.icu';
  static const String apiVersion = 'v1';
  static const String apiPath = '/api/$apiVersion';
  
  // Timeouts
  static const Duration connectTimeout = Duration(seconds: 30);
  static const Duration receiveTimeout = Duration(seconds: 30);
  
  // Auth Endpoints
  static const String login = '$apiPath/auth/login';
  static const String register = '$apiPath/auth/register';
  static const String logout = '$apiPath/auth/logout';
  static const String refreshToken = '$apiPath/auth/refresh';
  static const String me = '$apiPath/auth/me';
  
  // Content Endpoints
  static const String urns = '$apiPath/urns';
  static String urn(String slug) => '$apiPath/urns/$slug';
  static String motif(String id) => '$apiPath/motifs/$id';
  static String motifLesson(String id) => '$apiPath/motifs/$id/lesson';
  static String motifQuiz(String id) => '$apiPath/motifs/$id/quiz';
  
  // Progress Endpoints
  static const String progressUnlock = '$apiPath/progress/unlock';
  static const String progressCompleteLesson = '$apiPath/progress/complete-lesson';
  
  // Gamification Endpoints
  static const String badges = '$apiPath/badges';
  static const String leaderboard = '$apiPath/leaderboard';
  static const String quests = '$apiPath/quests';
}
```

**File: `lib/core/constants/app_constants.dart`**

```dart
class AppConstants {
  static const String appName = 'Lưu Niên Sử Kí';
  static const String appNameEn = 'Luuniensuki LMS';
  
  // XP System
  static const int discoveryXp = 25;
  static const int lessonXp = 50;
  static const int masteredXp = 75;
  static const int quizPassPercent = 80;
  
  // Cache Durations
  static const Duration urnsCacheDuration = Duration(hours: 24);
  static const Duration progressCacheDuration = Duration(minutes: 5);
}
```

**Acceptance Criteria:**
- [ ] Constants compile without errors
- [ ] API URLs match backend documentation

---

### Task 1.5: Implement Error Handling

**Estimated Time:** 2 hours

**File: `lib/core/errors/exceptions.dart`**

```dart
class ServerException implements Exception {
  final String message;
  final String? code;
  final int? statusCode;
  final Map<String, dynamic>? details;
  
  const ServerException({
    required this.message,
    this.code,
    this.statusCode,
    this.details,
  });
  
  @override
  String toString() => 'ServerException: $message (code: $code)';
}

class CacheException implements Exception {
  final String message;
  
  const CacheException(this.message);
  
  @override
  String toString() => 'CacheException: $message';
}

class NetworkException implements Exception {
  final String message;
  
  const NetworkException(this.message);
  
  @override
  String toString() => 'NetworkException: $message';
}
```

**File: `lib/core/errors/failures.dart`**

```dart
import 'package:equatable/equatable.dart';

abstract class Failure extends Equatable {
  final String message;
  final String? code;
  
  const Failure(this.message, {this.code});
  
  @override
  List<Object?> get props => [message, code];
}

class ServerFailure extends Failure {
  const ServerFailure(super.message, {super.code});
}

class NetworkFailure extends Failure {
  const NetworkFailure(super.message) : super(code: 'NETWORK_ERROR');
}

class CacheFailure extends Failure {
  const CacheFailure(super.message) : super(code: 'CACHE_ERROR');
}

class AuthFailure extends Failure {
  const AuthFailure(super.message, {super.code});
}

class ValidationFailure extends Failure {
  final Map<String, List<String>> fieldErrors;
  
  const ValidationFailure(
    super.message, {
    this.fieldErrors = const {},
    super.code = 'VALIDATION_ERROR',
  });
  
  @override
  List<Object?> get props => [message, code, fieldErrors];
}
```

**Acceptance Criteria:**
- [ ] Exception classes defined
- [ ] Failure classes with Equatable
- [ ] All tests pass

---

### Task 1.6: Implement Secure Storage

**Estimated Time:** 2 hours

**File: `lib/core/storage/secure_storage.dart`**

```dart
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:riverpod_annotation/riverpod_annotation.dart';

part 'secure_storage.g.dart';

abstract class SecureStorage {
  Future<void> saveAccessToken(String token);
  Future<String?> getAccessToken();
  Future<void> saveRefreshToken(String token);
  Future<String?> getRefreshToken();
  Future<void> clearTokens();
  Future<void> clearAll();
}

class SecureStorageImpl implements SecureStorage {
  final FlutterSecureStorage _storage;
  
  static const _accessTokenKey = 'luuniensuki_access_token';
  static const _refreshTokenKey = 'luuniensuki_refresh_token';
  
  SecureStorageImpl(this._storage);
  
  @override
  Future<void> saveAccessToken(String token) async {
    await _storage.write(key: _accessTokenKey, value: token);
  }
  
  @override
  Future<String?> getAccessToken() async {
    return _storage.read(key: _accessTokenKey);
  }
  
  @override
  Future<void> saveRefreshToken(String token) async {
    await _storage.write(key: _refreshTokenKey, value: token);
  }
  
  @override
  Future<String?> getRefreshToken() async {
    return _storage.read(key: _refreshTokenKey);
  }
  
  @override
  Future<void> clearTokens() async {
    await _storage.delete(key: _accessTokenKey);
    await _storage.delete(key: _refreshTokenKey);
  }
  
  @override
  Future<void> clearAll() async {
    await _storage.deleteAll();
  }
}

@riverpod
SecureStorage secureStorage(SecureStorageRef ref) {
  const storage = FlutterSecureStorage(
    aOptions: AndroidOptions(encryptedSharedPreferences: true),
  );
  return SecureStorageImpl(storage);
}
```

**Acceptance Criteria:**
- [ ] Tokens can be saved and retrieved
- [ ] Tokens can be cleared
- [ ] Android encrypted shared preferences enabled

---

### Task 1.7: Implement API Client with Interceptors

**Estimated Time:** 4 hours

**File: `lib/core/network/api_client.dart`**

See `02_API_Integration.md` for full implementation.

**File: `lib/core/network/interceptors/auth_interceptor.dart`**

```dart
import 'package:dio/dio.dart';

class AuthInterceptor extends Interceptor {
  final SecureStorage _secureStorage;
  
  static const _publicPaths = [
    '/api/v1/auth/login',
    '/api/v1/auth/register',
    '/api/v1/auth/refresh',
    '/health',
  ];
  
  AuthInterceptor(this._secureStorage);
  
  @override
  void onRequest(
    RequestOptions options,
    RequestInterceptorHandler handler,
  ) async {
    // Skip auth for public endpoints
    if (_isPublicEndpoint(options.path)) {
      return handler.next(options);
    }
    
    final accessToken = await _secureStorage.getAccessToken();
    if (accessToken != null) {
      options.headers['Authorization'] = 'Bearer $accessToken';
    }
    
    handler.next(options);
  }
  
  bool _isPublicEndpoint(String path) {
    return _publicPaths.any((p) => path.contains(p));
  }
}
```

**Acceptance Criteria:**
- [ ] Dio client configured with base URL and timeouts
- [ ] Auth interceptor adds Bearer token
- [ ] Logging interceptor logs requests/responses in debug mode
- [ ] Error interceptor converts DioException to ServerException

---

### Task 1.8: Implement Theme System

**Estimated Time:** 2 hours

**File: `lib/core/theme/app_colors.dart`**

```dart
import 'package:flutter/material.dart';

class AppColors {
  // Primary palette - Vietnamese imperial theme
  static const primary = Color(0xFFD4AF37);       // Vietnamese gold
  static const primaryDark = Color(0xFFB8962E);
  static const primaryLight = Color(0xFFE5C85C);
  
  // Secondary palette - Imperial red
  static const secondary = Color(0xFF8B0000);     // Dark red
  static const secondaryDark = Color(0xFF660000);
  static const secondaryLight = Color(0xFFB22222);
  
  // Background colors
  static const background = Color(0xFFF5F0E6);    // Parchment
  static const surface = Color(0xFFFFFFFF);
  static const surfaceVariant = Color(0xFFF0EBE0);
  
  // Text colors
  static const onPrimary = Color(0xFF1A1A1A);
  static const onSecondary = Color(0xFFFFFFFF);
  static const textPrimary = Color(0xFF1A1A1A);
  static const textSecondary = Color(0xFF666666);
  static const textHint = Color(0xFF999999);
  
  // Status colors
  static const success = Color(0xFF4CAF50);
  static const error = Color(0xFFB00020);
  static const warning = Color(0xFFFFA000);
  static const info = Color(0xFF2196F3);
  
  // Gamification colors
  static const xpGold = Color(0xFFFFD700);
  static const streakOrange = Color(0xFFFF6B35);
  static const badgePurple = Color(0xFF9C27B0);
  
  // Progress status colors
  static const hidden = Color(0xFF9E9E9E);
  static const discovered = Color(0xFF4CAF50);
  static const learned = Color(0xFF2196F3);
  static const mastered = Color(0xFF9C27B0);
  
  // Rarity colors
  static const common = Color(0xFF9E9E9E);
  static const uncommon = Color(0xFF4CAF50);
  static const rare = Color(0xFF2196F3);
  static const epic = Color(0xFF9C27B0);
  static const legendary = Color(0xFFFFD700);
}
```

**File: `lib/core/theme/app_theme.dart`**

```dart
import 'package:flutter/material.dart';
import 'app_colors.dart';
import 'app_typography.dart';

class AppTheme {
  static ThemeData get lightTheme => ThemeData(
    useMaterial3: true,
    colorScheme: ColorScheme.fromSeed(
      seedColor: AppColors.primary,
      brightness: Brightness.light,
      primary: AppColors.primary,
      secondary: AppColors.secondary,
      surface: AppColors.surface,
      background: AppColors.background,
      error: AppColors.error,
    ),
    scaffoldBackgroundColor: AppColors.background,
    textTheme: AppTypography.textTheme,
    appBarTheme: const AppBarTheme(
      centerTitle: true,
      elevation: 0,
      backgroundColor: AppColors.surface,
      foregroundColor: AppColors.textPrimary,
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
      fillColor: AppColors.surface,
    ),
    elevatedButtonTheme: ElevatedButtonThemeData(
      style: ElevatedButton.styleFrom(
        backgroundColor: AppColors.primary,
        foregroundColor: AppColors.onPrimary,
        minimumSize: const Size(double.infinity, 48),
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(8),
        ),
      ),
    ),
    outlinedButtonTheme: OutlinedButtonThemeData(
      style: OutlinedButton.styleFrom(
        minimumSize: const Size(double.infinity, 48),
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(8),
        ),
      ),
    ),
    bottomNavigationBarTheme: const BottomNavigationBarThemeData(
      backgroundColor: AppColors.surface,
      selectedItemColor: AppColors.primary,
      unselectedItemColor: AppColors.textHint,
      type: BottomNavigationBarType.fixed,
    ),
  );
  
  static ThemeData get darkTheme => ThemeData(
    useMaterial3: true,
    colorScheme: ColorScheme.fromSeed(
      seedColor: AppColors.primary,
      brightness: Brightness.dark,
    ),
    // ... dark theme customizations
  );
}
```

**Acceptance Criteria:**
- [ ] Light theme implemented with Vietnamese imperial colors
- [ ] Dark theme placeholder created
- [ ] Theme applied to MaterialApp

---

## Week 2: Authentication Implementation

### Task 2.1: Create Auth DTOs

**Estimated Time:** 2 hours

**File: `lib/features/auth/data/models/auth_dtos.dart`**

```dart
import 'package:freezed_annotation/freezed_annotation.dart';

part 'auth_dtos.freezed.dart';
part 'auth_dtos.g.dart';

@freezed
class LoginRequestDto with _$LoginRequestDto {
  const factory LoginRequestDto({
    required String email,
    required String password,
  }) = _LoginRequestDto;

  factory LoginRequestDto.fromJson(Map<String, dynamic> json) =>
      _$LoginRequestDtoFromJson(json);
}

@freezed
class RegisterRequestDto with _$RegisterRequestDto {
  const factory RegisterRequestDto({
    required String email,
    required String password,
    @JsonKey(name: 'display_name') required String displayName,
  }) = _RegisterRequestDto;

  factory RegisterRequestDto.fromJson(Map<String, dynamic> json) =>
      _$RegisterRequestDtoFromJson(json);
}

@freezed
class UserDto with _$UserDto {
  const factory UserDto({
    required String id,
    required String email,
    @JsonKey(name: 'display_name') required String displayName,
    @JsonKey(name: 'avatar_url') String? avatarUrl,
    String? username,
    required String role,
    @JsonKey(name: 'total_xp') required int totalXp,
    @JsonKey(name: 'is_profile_public') required bool isProfilePublic,
  }) = _UserDto;

  factory UserDto.fromJson(Map<String, dynamic> json) =>
      _$UserDtoFromJson(json);
}

@freezed
class AuthResponseDto with _$AuthResponseDto {
  const factory AuthResponseDto({
    required UserDto user,
    required StatsDto stats,
  }) = _AuthResponseDto;

  factory AuthResponseDto.fromJson(Map<String, dynamic> json) =>
      _$AuthResponseDtoFromJson(json);
}

@freezed
class StatsDto with _$StatsDto {
  const factory StatsDto({
    @JsonKey(name: 'total_xp') required int totalXp,
    required RankDto rank,
    @JsonKey(name: 'xp_to_next_rank') required int xpToNextRank,
    @JsonKey(name: 'next_rank') RankDto? nextRank,
  }) = _StatsDto;

  factory StatsDto.fromJson(Map<String, dynamic> json) =>
      _$StatsDtoFromJson(json);
}

@freezed
class RankDto with _$RankDto {
  const factory RankDto({
    required int level,
    required String name,
    required int xp,
  }) = _RankDto;

  factory RankDto.fromJson(Map<String, dynamic> json) =>
      _$RankDtoFromJson(json);
}
```

Run code generation:
```bash
dart run build_runner build --delete-conflicting-outputs
```

**Acceptance Criteria:**
- [ ] All DTOs defined with Freezed
- [ ] JSON serialization works
- [ ] Generated files compile

---

### Task 2.2: Create Auth Domain Entities

**Estimated Time:** 1 hour

**File: `lib/features/auth/domain/entities/user.dart`**

```dart
import 'package:equatable/equatable.dart';

class User extends Equatable {
  final String id;
  final String email;
  final String displayName;
  final String? avatarUrl;
  final String? username;
  final String role;
  final int totalXp;
  final bool isProfilePublic;
  final Rank rank;
  final int xpToNextRank;
  final Rank? nextRank;
  
  const User({
    required this.id,
    required this.email,
    required this.displayName,
    this.avatarUrl,
    this.username,
    required this.role,
    required this.totalXp,
    required this.isProfilePublic,
    required this.rank,
    required this.xpToNextRank,
    this.nextRank,
  });
  
  bool get isGuest => role == 'guest';
  bool get isLearner => role == 'learner';
  bool get isTeacher => role == 'teacher';
  bool get isAdmin => role == 'admin' || role == 'super_admin';
  
  @override
  List<Object?> get props => [id, email, displayName, role, totalXp];
}

class Rank extends Equatable {
  final int level;
  final String name;
  final int xp;
  
  const Rank({
    required this.level,
    required this.name,
    required this.xp,
  });
  
  @override
  List<Object?> get props => [level, name, xp];
}
```

**Acceptance Criteria:**
- [ ] User entity with all required fields
- [ ] Role helper getters
- [ ] Equatable implemented

---

### Task 2.3: Create Auth Repository

**Estimated Time:** 3 hours

**File: `lib/features/auth/domain/repositories/auth_repository.dart`**

```dart
import 'package:dartz/dartz.dart';
import '../entities/user.dart';
import '../../../../core/errors/failures.dart';

abstract class AuthRepository {
  Future<Either<Failure, User>> login(String email, String password);
  Future<Either<Failure, User>> register(String email, String password, String displayName);
  Future<Either<Failure, User>> getCurrentUser();
  Future<Either<Failure, void>> logout();
  Future<Either<Failure, bool>> refreshToken();
  Future<bool> isLoggedIn();
}
```

**File: `lib/features/auth/data/repositories/auth_repository_impl.dart`**

```dart
import 'package:dartz/dartz.dart';
import '../../domain/entities/user.dart';
import '../../domain/repositories/auth_repository.dart';
import '../datasources/auth_remote_datasource.dart';
import '../datasources/auth_local_datasource.dart';
import '../../../../core/errors/exceptions.dart';
import '../../../../core/errors/failures.dart';
import '../../../../core/network/network_info.dart';

class AuthRepositoryImpl implements AuthRepository {
  final AuthRemoteDataSource remoteDataSource;
  final AuthLocalDataSource localDataSource;
  final NetworkInfo networkInfo;
  
  AuthRepositoryImpl({
    required this.remoteDataSource,
    required this.localDataSource,
    required this.networkInfo,
  });
  
  @override
  Future<Either<Failure, User>> login(String email, String password) async {
    if (!await networkInfo.isConnected) {
      return const Left(NetworkFailure('No internet connection'));
    }
    
    try {
      final response = await remoteDataSource.login(email, password);
      final user = response.user.toEntity(response.stats);
      
      await localDataSource.cacheUser(response.user);
      
      return Right(user);
    } on ServerException catch (e) {
      return Left(AuthFailure(e.message, code: e.code));
    } catch (e) {
      return Left(ServerFailure('An unexpected error occurred: $e'));
    }
  }
  
  @override
  Future<Either<Failure, User>> register(
    String email,
    String password,
    String displayName,
  ) async {
    if (!await networkInfo.isConnected) {
      return const Left(NetworkFailure('No internet connection'));
    }
    
    try {
      final response = await remoteDataSource.register(email, password, displayName);
      final user = response.user.toEntity(response.stats);
      
      await localDataSource.cacheUser(response.user);
      
      return Right(user);
    } on ServerException catch (e) {
      return Left(AuthFailure(e.message, code: e.code));
    } catch (e) {
      return Left(ServerFailure('An unexpected error occurred: $e'));
    }
  }
  
  @override
  Future<Either<Failure, User>> getCurrentUser() async {
    try {
      // Try network first
      if (await networkInfo.isConnected) {
        final response = await remoteDataSource.getCurrentUser();
        await localDataSource.cacheUser(response.user);
        return Right(response.user.toEntity(response.stats));
      }
      
      // Fall back to cache
      final cachedUser = await localDataSource.getCachedUser();
      if (cachedUser != null) {
        return Right(cachedUser.toEntity(null));
      }
      
      return const Left(AuthFailure('Not authenticated'));
    } on ServerException catch (e) {
      if (e.statusCode == 401) {
        return const Left(AuthFailure('Session expired'));
      }
      return Left(AuthFailure(e.message, code: e.code));
    } catch (e) {
      return Left(ServerFailure('An unexpected error occurred: $e'));
    }
  }
  
  @override
  Future<Either<Failure, void>> logout() async {
    try {
      await remoteDataSource.logout();
    } catch (_) {
      // Ignore remote logout errors
    }
    
    await localDataSource.clearCache();
    return const Right(null);
  }
  
  @override
  Future<Either<Failure, bool>> refreshToken() async {
    try {
      final success = await remoteDataSource.refreshToken();
      return Right(success);
    } on ServerException catch (e) {
      return Left(AuthFailure(e.message, code: e.code));
    } catch (e) {
      return const Left(AuthFailure('Token refresh failed'));
    }
  }
  
  @override
  Future<bool> isLoggedIn() async {
    return localDataSource.hasValidSession();
  }
}
```

**Acceptance Criteria:**
- [ ] Repository interface defined
- [ ] Implementation handles network errors
- [ ] Caches user data locally
- [ ] Fallback to cache when offline

---

### Task 2.4: Create Auth State Provider

**Estimated Time:** 3 hours

**File: `lib/features/auth/presentation/providers/auth_state.dart`**

```dart
import 'package:freezed_annotation/freezed_annotation.dart';
import '../../domain/entities/user.dart';

part 'auth_state.freezed.dart';

@freezed
class AuthState with _$AuthState {
  const factory AuthState.initial() = _Initial;
  const factory AuthState.loading() = _Loading;
  const factory AuthState.authenticated(User user) = _Authenticated;
  const factory AuthState.unauthenticated() = _Unauthenticated;
  const factory AuthState.error(String message) = _Error;
}

extension AuthStateX on AuthState {
  bool get isAuthenticated => this is _Authenticated;
  bool get isLoading => this is _Loading;
  User? get user => mapOrNull(authenticated: (s) => s.user);
}
```

**File: `lib/features/auth/presentation/providers/auth_provider.dart`**

```dart
import 'package:riverpod_annotation/riverpod_annotation.dart';
import '../../domain/repositories/auth_repository.dart';
import 'auth_state.dart';

part 'auth_provider.g.dart';

@riverpod
class AuthNotifier extends _$AuthNotifier {
  @override
  AuthState build() {
    // Check initial auth state
    _checkAuthStatus();
    return const AuthState.initial();
  }
  
  Future<void> _checkAuthStatus() async {
    final repository = ref.read(authRepositoryProvider);
    
    if (await repository.isLoggedIn()) {
      final result = await repository.getCurrentUser();
      result.fold(
        (failure) => state = const AuthState.unauthenticated(),
        (user) => state = AuthState.authenticated(user),
      );
    } else {
      state = const AuthState.unauthenticated();
    }
  }
  
  Future<void> login(String email, String password) async {
    state = const AuthState.loading();
    
    final repository = ref.read(authReposit