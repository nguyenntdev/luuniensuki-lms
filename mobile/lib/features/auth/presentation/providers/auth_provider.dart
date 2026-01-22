import 'package:dartz/dartz.dart';
import 'package:flutter/foundation.dart';
import 'package:riverpod_annotation/riverpod_annotation.dart';


import '../../../../core/errors/failures.dart';
import '../../../../core/network/api_client.dart';
import '../../../../core/network/network_info.dart';
import '../../../../core/storage/hive_storage.dart';
import '../../../../core/storage/secure_storage.dart';
import '../../data/datasources/auth_local_datasource.dart';
import '../../data/datasources/auth_remote_datasource.dart';
import '../../data/repositories/auth_repository_impl.dart';
import '../../domain/entities/user.dart';
import '../../domain/repositories/auth_repository.dart';
import 'auth_state.dart';

part 'auth_provider.g.dart';

/// Provides the AuthRemoteDataSource
@Riverpod(keepAlive: true)
AuthRemoteDataSource authRemoteDataSource(AuthRemoteDataSourceRef ref) {
  final dio = ref.watch(dioProvider);
  return AuthRemoteDataSourceImpl(dio);
}

/// Provides the AuthLocalDataSource
@Riverpod(keepAlive: true)
AuthLocalDataSource authLocalDataSource(AuthLocalDataSourceRef ref) {
  final secureStorage = ref.watch(secureStorageProvider);
  final hiveStorage = ref.watch(hiveStorageProvider);
  return AuthLocalDataSourceImpl(
    secureStorage: secureStorage,
    hiveStorage: hiveStorage,
  );
}

/// Provides the AuthRepository implementation
@Riverpod(keepAlive: true)
AuthRepository authRepository(AuthRepositoryRef ref) {
  final remoteDataSource = ref.watch(authRemoteDataSourceProvider);
  final localDataSource = ref.watch(authLocalDataSourceProvider);
  final networkInfo = ref.watch(networkInfoProvider);

  return AuthRepositoryImpl(
    remoteDataSource: remoteDataSource,
    localDataSource: localDataSource,
    networkInfo: networkInfo,
  );
}

/// Auth state notifier that manages authentication state.
/// Handles login, registration, logout, and session management.
@Riverpod(keepAlive: true)
class AuthNotifier extends _$AuthNotifier {
  @override
  AuthState build() {
    // Start as unauthenticated - don't call async here
    // Call initialize() from app startup instead
    return const AuthState.unauthenticated();
  }

  AuthRepository get _repository => ref.read(authRepositoryProvider);

  /// Initialize authentication - call this once from app startup
  Future<void> initialize() async {
    // Don't re-initialize if already checking or authenticated
    if (state != const AuthState.unauthenticated()) return;

    state = const AuthState.loading();

    try {
      final repository = _repository;
      final isLoggedIn = await repository.isLoggedIn();

      if (!isLoggedIn) {
        state = const AuthState.unauthenticated();
        return;
      }

      // Try to get current user
      final result = await repository.getCurrentUser();

      result.fold(
        (failure) {
          debugPrint('Auth check failed: ${failure.message}');
          state = const AuthState.unauthenticated();
        },
        (user) {
          state = AuthState.authenticated(user: user);
        },
      );
    } catch (e) {
      debugPrint('Auth check error: $e');
      state = const AuthState.unauthenticated();
    }
  }

  /// Login with email and password
  Future<void> login({
    required String email,
    required String password,
  }) async {
    debugPrint('[AUTH_PROVIDER] ========== LOGIN START ==========');
    debugPrint('[AUTH_PROVIDER] login() called for: $email');
    debugPrint('[AUTH_PROVIDER] Current state before: $state');
    state = const AuthState.loading();
    debugPrint('[AUTH_PROVIDER] State set to loading: $state');

    try {
      debugPrint('[AUTH_PROVIDER] Calling repository.login()...');
      final repository = _repository;
      final result = await repository.login(
        email: email,
        password: password,
      );

      debugPrint('[AUTH_PROVIDER] Repository returned result');
      debugPrint('[AUTH_PROVIDER] Result type: ${result.runtimeType}');
      debugPrint('[AUTH_PROVIDER] Result isRight: ${result.isRight()}');
      debugPrint('[AUTH_PROVIDER] Result isLeft: ${result.isLeft()}');

      result.fold(
        (failure) {
          debugPrint('[AUTH_PROVIDER] ===== LOGIN FAILED =====');
          debugPrint('[AUTH_PROVIDER] Failure type: ${failure.runtimeType}');
          debugPrint('[AUTH_PROVIDER] Failure message: ${failure.message}');
          final errorMsg = _getErrorMessage(failure);
          debugPrint('[AUTH_PROVIDER] Error message: $errorMsg');
          state = AuthState.error(message: errorMsg);
          debugPrint('[AUTH_PROVIDER] State after error: $state');
        },
        (user) {
          debugPrint('[AUTH_PROVIDER] ===== LOGIN SUCCESS =====');
          debugPrint('[AUTH_PROVIDER] User: ${user.email}');
          debugPrint('[AUTH_PROVIDER] User id: ${user.id}');
          state = AuthState.authenticated(user: user);
          debugPrint('[AUTH_PROVIDER] State after authenticated: $state');
        },
      );
    } catch (e, stackTrace) {
      debugPrint('[AUTH_PROVIDER] ===== LOGIN EXCEPTION =====');
      debugPrint('[AUTH_PROVIDER] Exception type: ${e.runtimeType}');
      debugPrint('[AUTH_PROVIDER] Exception: $e');
      debugPrint('[AUTH_PROVIDER] StackTrace: $stackTrace');
      state = AuthState.error(message: 'EXCEPTION: ${e.runtimeType}: ${e.toString()}');
    }

    debugPrint('[AUTH_PROVIDER] ========== LOGIN END ==========');
    debugPrint('[AUTH_PROVIDER] Final state: $state');
    debugPrint('[AUTH_PROVIDER] Final state type: ${state.runtimeType}');
  }

  /// Register a new user
  Future<void> register({
    required String email,
    required String password,
    required String displayName,
  }) async {
    debugPrint('[AUTH_PROVIDER] ========== REGISTER START ==========');
    debugPrint('[AUTH_PROVIDER] register() called for: $email');
    debugPrint('[AUTH_PROVIDER] Current state before: $state');
    state = const AuthState.loading();
    debugPrint('[AUTH_PROVIDER] State set to loading: $state');

    try {
      debugPrint('[AUTH_PROVIDER] Calling repository.register()...');
      final repository = _repository;
      final result = await repository.register(
        email: email,
        password: password,
        displayName: displayName,
      );

      debugPrint('[AUTH_PROVIDER] Repository returned result');
      debugPrint('[AUTH_PROVIDER] Result type: ${result.runtimeType}');
      debugPrint('[AUTH_PROVIDER] Result isRight: ${result.isRight()}');
      debugPrint('[AUTH_PROVIDER] Result isLeft: ${result.isLeft()}');

      result.fold(
        (failure) {
          debugPrint('[AUTH_PROVIDER] ===== REGISTER FAILED =====');
          debugPrint('[AUTH_PROVIDER] Failure type: ${failure.runtimeType}');
          debugPrint('[AUTH_PROVIDER] Failure message: ${failure.message}');
          final errorMsg = _getErrorMessage(failure);
          debugPrint('[AUTH_PROVIDER] Error message: $errorMsg');
          state = AuthState.error(message: errorMsg);
          debugPrint('[AUTH_PROVIDER] State after error: $state');
        },
        (user) {
          debugPrint('[AUTH_PROVIDER] ===== REGISTER SUCCESS =====');
          debugPrint('[AUTH_PROVIDER] User: ${user.email}');
          debugPrint('[AUTH_PROVIDER] User id: ${user.id}');
          state = AuthState.authenticated(user: user);
          debugPrint('[AUTH_PROVIDER] State after authenticated: $state');
        },
      );
    } catch (e, stackTrace) {
      debugPrint('[AUTH_PROVIDER] ===== REGISTER EXCEPTION =====');
      debugPrint('[AUTH_PROVIDER] Exception type: ${e.runtimeType}');
      debugPrint('[AUTH_PROVIDER] Exception: $e');
      debugPrint('[AUTH_PROVIDER] StackTrace: $stackTrace');
      state = AuthState.error(message: 'EXCEPTION: ${e.runtimeType}: ${e.toString()}');
    }

    debugPrint('[AUTH_PROVIDER] ========== REGISTER END ==========');
    debugPrint('[AUTH_PROVIDER] Final state: $state');
    debugPrint('[AUTH_PROVIDER] Final state type: ${state.runtimeType}');
  }

  /// Logout current user
  Future<void> logout() async {
    state = const AuthState.loading();

    final repository = _repository;
    await repository.logout();
    state = const AuthState.unauthenticated();
  }

  /// Refresh user data from server
  Future<void> refreshUser() async {
    if (!state.isAuthenticated) return;

    final repository = _repository;
    final result = await repository.getCurrentUser();

    result.fold(
      (failure) {
        // If session expired, logout
        if (failure is AuthFailure) {
          state = const AuthState.unauthenticated();
        }
        // Otherwise keep current state
      },
      (user) {
        state = AuthState.authenticated(user: user);
      },
    );
  }

  /// Update user profile
  Future<bool> updateProfile({
    String? displayName,
    String? username,
    String? avatarUrl,
    bool? isProfilePublic,
  }) async {
    final currentUser = state.user;
    if (currentUser == null) return false;

    final repository = _repository;
    final result = await repository.updateProfile(
      displayName: displayName,
      username: username,
      avatarUrl: avatarUrl,
      isProfilePublic: isProfilePublic,
    );

    return result.fold(
      (failure) => false,
      (user) {
        state = AuthState.authenticated(user: user);
        return true;
      },
    );
  }

  /// Change user password
  Future<Either<String, void>> changePassword({
    required String currentPassword,
    required String newPassword,
  }) async {
    final repository = _repository;
    final result = await repository.changePassword(
      currentPassword: currentPassword,
      newPassword: newPassword,
    );

    return result.fold(
      (failure) => Left(_getErrorMessage(failure)),
      (_) => const Right(null),
    );
  }

  /// Use a streak freeze
  Future<bool> useStreakFreeze() async {
    final repository = _repository;
    final result = await repository.useStreakFreeze();

    return result.fold(
      (failure) => false,
      (user) {
        state = AuthState.authenticated(user: user);
        return true;
      },
    );
  }

  /// Clear error state and return to unauthenticated
  void clearError() {
    if (state is AuthStateError) {
      state = const AuthState.unauthenticated();
    }
  }

  /// Get user-friendly error message from failure
  String _getErrorMessage(Failure failure) {
    if (failure is AuthFailure) {
      switch (failure.code) {
        case 'INVALID_CREDENTIALS':
          return 'Email hoặc mật khẩu không đúng';
        case 'SESSION_EXPIRED':
          return 'Phiên đăng nhập đã hết hạn';
        case 'EMAIL_EXISTS':
          return 'Email đã được đăng ký';
        case 'ACCOUNT_DISABLED':
          return 'Tài khoản đã bị vô hiệu hóa';
        default:
          return failure.message;
      }
    }

    if (failure is NetworkFailure) {
      return 'Không có kết nối mạng. Vui lòng kiểm tra lại.';
    }

    if (failure is ValidationFailure) {
      // Return first field error or general message
      for (final errors in failure.fieldErrors.values) {
        if (errors.isNotEmpty) {
          return errors.first;
        }
      }
      return failure.message;
    }

    if (failure is ServerFailure) {
      if (failure.statusCode == 429) {
        return 'Quá nhiều yêu cầu. Vui lòng thử lại sau.';
      }
      return failure.message;
    }

    return failure.message;
  }
}

/// Convenience providers for accessing auth state

/// Provider that returns the current authenticated user, or null
@Riverpod(keepAlive: true)
User? currentUser(CurrentUserRef ref) {
  final authState = ref.watch(authNotifierProvider);
  return authState.user;
}

/// Provider that returns whether the user is authenticated
@Riverpod(keepAlive: true)
bool isAuthenticated(IsAuthenticatedRef ref) {
  final authState = ref.watch(authNotifierProvider);
  return authState.isAuthenticated;
}

/// Provider that returns whether auth is loading
@Riverpod(keepAlive: true)
bool isAuthLoading(IsAuthLoadingRef ref) {
  final authState = ref.watch(authNotifierProvider);
  return authState.isLoading;
}

/// Provider that returns the auth error message, if any
@Riverpod(keepAlive: true)
String? authError(AuthErrorRef ref) {
  final authState = ref.watch(authNotifierProvider);
  return authState.mapOrNull(error: (e) => e.message);
}
