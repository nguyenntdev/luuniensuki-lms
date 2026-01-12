import 'package:dartz/dartz.dart';
import 'package:flutter/foundation.dart';

import '../../../../core/errors/exceptions.dart';
import '../../../../core/errors/failures.dart';
import '../../../../core/network/network_info.dart';
import '../../domain/entities/user.dart';
import '../../domain/repositories/auth_repository.dart';
import '../datasources/auth_local_datasource.dart';
import '../datasources/auth_remote_datasource.dart';
import '../models/user_mapper.dart';

/// Implementation of AuthRepository.
/// Coordinates between remote and local data sources,
/// handles network errors, and maps DTOs to domain entities.
class AuthRepositoryImpl implements AuthRepository {
  final AuthRemoteDataSource _remoteDataSource;
  final AuthLocalDataSource _localDataSource;
  final NetworkInfo _networkInfo;

  AuthRepositoryImpl({
    required AuthRemoteDataSource remoteDataSource,
    required AuthLocalDataSource localDataSource,
    required NetworkInfo networkInfo,
  })  : _remoteDataSource = remoteDataSource,
        _localDataSource = localDataSource,
        _networkInfo = networkInfo;

  @override
  Future<Either<Failure, User>> login({
    required String email,
    required String password,
  }) async {
    debugPrint('[AUTH_REPO] login() called for: $email');

    if (!await _networkInfo.isConnected) {
      debugPrint('[AUTH_REPO] No network connection');
      return const Left(NetworkFailure('Không có kết nối mạng'));
    }

    try {
      debugPrint('[AUTH_REPO] Calling remote data source...');
      final response = await _remoteDataSource.login(
        email: email,
        password: password,
      );
      debugPrint('[AUTH_REPO] Remote login successful, user: ${response.user.email}');

      // Save tokens if provided in response
      if (response.accessToken != null) {
        debugPrint('[AUTH_REPO] Saving access token');
        await _localDataSource.saveAccessToken(response.accessToken!);
      } else {
        debugPrint('[AUTH_REPO] No access token in response (using cookies)');
      }
      if (response.refreshToken != null) {
        debugPrint('[AUTH_REPO] Saving refresh token');
        await _localDataSource.saveRefreshToken(response.refreshToken!);
      } else {
        debugPrint('[AUTH_REPO] No refresh token in response (using cookies)');
      }

      // Cache user data
      debugPrint('[AUTH_REPO] Caching user data');
      await _localDataSource.cacheUser(response.user);

      // Convert to domain entity
      debugPrint('[AUTH_REPO] Converting to domain entity');
      final user = response.toUserEntity();
      debugPrint('[AUTH_REPO] Login successful! Returning Right(user)');
      return Right(user);
    } on AuthException catch (e) {
      debugPrint('[AUTH_REPO] AuthException: ${e.message}, code: ${e.code}');
      return Left(AuthFailure(e.message, code: e.code));
    } on ServerException catch (e) {
      debugPrint('[AUTH_REPO] ServerException: ${e.message}, code: ${e.code}, status: ${e.statusCode}');
      return Left(ServerFailure(e.message, code: e.code, statusCode: e.statusCode));
    } on NetworkException catch (e) {
      debugPrint('[AUTH_REPO] NetworkException: ${e.message}');
      return Left(NetworkFailure(e.message));
    } on ValidationException catch (e) {
      debugPrint('[AUTH_REPO] ValidationException: ${e.message}');
      return Left(ValidationFailure(e.message, fieldErrors: e.fieldErrors));
    } catch (e, stackTrace) {
      debugPrint('[AUTH_REPO] Unexpected error: $e');
      debugPrint('[AUTH_REPO] StackTrace: $stackTrace');
      return Left(UnexpectedFailure('Đã xảy ra lỗi không mong muốn: $e'));
    }
  }

  @override
  Future<Either<Failure, User>> register({
    required String email,
    required String password,
    required String displayName,
  }) async {
    if (!await _networkInfo.isConnected) {
      return const Left(NetworkFailure('Không có kết nối mạng'));
    }

    try {
      final response = await _remoteDataSource.register(
        email: email,
        password: password,
        displayName: displayName,
      );

      // Save tokens if provided
      if (response.accessToken != null) {
        await _localDataSource.saveAccessToken(response.accessToken!);
      }
      if (response.refreshToken != null) {
        await _localDataSource.saveRefreshToken(response.refreshToken!);
      }

      // Cache user data
      await _localDataSource.cacheUser(response.user);

      // Convert to domain entity
      final user = response.toUserEntity();
      return Right(user);
    } on AuthException catch (e) {
      return Left(AuthFailure(e.message, code: e.code));
    } on ServerException catch (e) {
      // Handle duplicate email
      if (e.statusCode == 409) {
        return Left(AuthFailure(
          'Email đã được đăng ký',
          code: 'EMAIL_EXISTS',
        ));
      }
      return Left(ServerFailure(e.message, code: e.code, statusCode: e.statusCode));
    } on NetworkException catch (e) {
      return Left(NetworkFailure(e.message));
    } on ValidationException catch (e) {
      return Left(ValidationFailure(e.message, fieldErrors: e.fieldErrors));
    } catch (e) {
      return Left(UnexpectedFailure('Đã xảy ra lỗi không mong muốn: $e'));
    }
  }

  @override
  Future<Either<Failure, User>> getCurrentUser() async {
    try {
      // Try network first if connected
      if (await _networkInfo.isConnected) {
        try {
          final response = await _remoteDataSource.getCurrentUser();

          // Update cached user
          await _localDataSource.cacheUser(response.user);

          // Convert to domain entity
          return Right(response.toUserEntity());
        } on AuthException catch (e) {
          // If session expired, clear local data
          if (e.shouldLogout || e.code == 'SESSION_EXPIRED') {
            await _localDataSource.clearAll();
            return Left(AuthFailure.sessionExpired());
          }
          rethrow;
        }
      }

      // Fall back to cached user if offline
      final cachedUser = await _localDataSource.getCachedUser();
      if (cachedUser != null) {
        return Right(cachedUser.toEntitySimple());
      }

      return Left(AuthFailure.unauthenticated());
    } on AuthException catch (e) {
      return Left(AuthFailure(e.message, code: e.code));
    } on ServerException catch (e) {
      if (e.statusCode == 401) {
        await _localDataSource.clearAll();
        return Left(AuthFailure.sessionExpired());
      }
      return Left(ServerFailure(e.message, code: e.code, statusCode: e.statusCode));
    } on NetworkException catch (e) {
      // Try cache on network error
      final cachedUser = await _localDataSource.getCachedUser();
      if (cachedUser != null) {
        return Right(cachedUser.toEntitySimple());
      }
      return Left(NetworkFailure(e.message));
    } on CacheException catch (e) {
      return Left(CacheFailure(e.message));
    } catch (e) {
      return Left(UnexpectedFailure('Đã xảy ra lỗi không mong muốn: $e'));
    }
  }

  @override
  Future<Either<Failure, void>> logout() async {
    try {
      // Try to logout on server (ignore errors)
      if (await _networkInfo.isConnected) {
        try {
          await _remoteDataSource.logout();
        } catch (_) {
          // Ignore server logout errors
        }
      }

      // Always clear local data
      await _localDataSource.clearAll();
      return const Right(null);
    } on CacheException catch (e) {
      return Left(CacheFailure(e.message));
    } catch (e) {
      // Still try to clear local data even if something failed
      try {
        await _localDataSource.clearAll();
      } catch (_) {}
      return const Right(null);
    }
  }

  @override
  Future<Either<Failure, bool>> refreshToken() async {
    if (!await _networkInfo.isConnected) {
      return const Left(NetworkFailure('Không có kết nối mạng'));
    }

    try {
      final response = await _remoteDataSource.refreshToken();

      // Save new tokens
      if (response.accessToken != null) {
        await _localDataSource.saveAccessToken(response.accessToken!);
      }
      if (response.refreshToken != null) {
        await _localDataSource.saveRefreshToken(response.refreshToken!);
      }

      return const Right(true);
    } on AuthException catch (e) {
      // Clear tokens on refresh failure
      await _localDataSource.clearTokens();
      return Left(AuthFailure(e.message, code: e.code));
    } on ServerException catch (e) {
      if (e.statusCode == 401) {
        await _localDataSource.clearAll();
        return Left(AuthFailure.sessionExpired());
      }
      return Left(ServerFailure(e.message, code: e.code, statusCode: e.statusCode));
    } catch (e) {
      return Left(UnexpectedFailure('Làm mới phiên đăng nhập thất bại'));
    }
  }

  @override
  Future<bool> isLoggedIn() async {
    try {
      return await _localDataSource.hasValidSession();
    } catch (_) {
      return false;
    }
  }

  @override
  Future<Either<Failure, User>> updateProfile({
    String? displayName,
    String? username,
    String? avatarUrl,
    bool? isProfilePublic,
  }) async {
    if (!await _networkInfo.isConnected) {
      return const Left(NetworkFailure('Không có kết nối mạng'));
    }

    try {
      final response = await _remoteDataSource.updateProfile(
        displayName: displayName,
        username: username,
        avatarUrl: avatarUrl,
        isProfilePublic: isProfilePublic,
      );

      // Update cached user
      await _localDataSource.cacheUser(response.user);

      return Right(response.toUserEntity());
    } on AuthException catch (e) {
      return Left(AuthFailure(e.message, code: e.code));
    } on ServerException catch (e) {
      return Left(ServerFailure(e.message, code: e.code, statusCode: e.statusCode));
    } on ValidationException catch (e) {
      return Left(ValidationFailure(e.message, fieldErrors: e.fieldErrors));
    } catch (e) {
      return Left(UnexpectedFailure('Cập nhật hồ sơ thất bại: $e'));
    }
  }

  @override
  Future<Either<Failure, void>> changePassword({
    required String currentPassword,
    required String newPassword,
  }) async {
    if (!await _networkInfo.isConnected) {
      return const Left(NetworkFailure('Không có kết nối mạng'));
    }

    try {
      await _remoteDataSource.changePassword(
        currentPassword: currentPassword,
        newPassword: newPassword,
      );
      return const Right(null);
    } on AuthException catch (e) {
      return Left(AuthFailure(e.message, code: e.code));
    } on ServerException catch (e) {
      if (e.statusCode == 400 || e.statusCode == 401) {
        return const Left(AuthFailure(
          'Mật khẩu hiện tại không đúng',
          code: 'INVALID_PASSWORD',
        ));
      }
      return Left(ServerFailure(e.message, code: e.code, statusCode: e.statusCode));
    } catch (e) {
      return Left(UnexpectedFailure('Đổi mật khẩu thất bại: $e'));
    }
  }

  @override
  Future<Either<Failure, void>> deleteAccount() async {
    if (!await _networkInfo.isConnected) {
      return const Left(NetworkFailure('Không có kết nối mạng'));
    }

    try {
      // TODO: Implement delete account API call when available
      // await _remoteDataSource.deleteAccount();

      // Clear local data
      await _localDataSource.clearAll();
      return const Right(null);
    } on ServerException catch (e) {
      return Left(ServerFailure(e.message, code: e.code, statusCode: e.statusCode));
    } catch (e) {
      return Left(UnexpectedFailure('Xóa tài khoản thất bại: $e'));
    }
  }

  @override
  Future<Either<Failure, void>> requestPasswordReset({
    required String email,
  }) async {
    if (!await _networkInfo.isConnected) {
      return const Left(NetworkFailure('Không có kết nối mạng'));
    }

    try {
      await _remoteDataSource.requestPasswordReset(email: email);
      return const Right(null);
    } on ServerException catch (e) {
      return Left(ServerFailure(e.message, code: e.code, statusCode: e.statusCode));
    } catch (e) {
      return Left(UnexpectedFailure('Yêu cầu đặt lại mật khẩu thất bại: $e'));
    }
  }

  @override
  Future<Either<Failure, User>> useStreakFreeze() async {
    if (!await _networkInfo.isConnected) {
      return const Left(NetworkFailure('Không có kết nối mạng'));
    }

    try {
      final response = await _remoteDataSource.useStreakFreeze();

      // Update cached user
      await _localDataSource.cacheUser(response.user);

      return Right(response.toUserEntity());
    } on ServerException catch (e) {
      if (e.statusCode == 400) {
        return const Left(ServerFailure(
          'Không còn lượt đóng băng chuỗi',
          code: 'NO_FREEZES',
        ));
      }
      return Left(ServerFailure(e.message, code: e.code, statusCode: e.statusCode));
    } catch (e) {
      return Left(UnexpectedFailure('Sử dụng đóng băng chuỗi thất bại: $e'));
    }
  }

  @override
  Future<Either<Failure, UserStats>> getUserStats() async {
    if (!await _networkInfo.isConnected) {
      return const Left(NetworkFailure('Không có kết nối mạng'));
    }

    try {
      final statsDto = await _remoteDataSource.getUserStats();

      final stats = UserStats(
        totalXp: statsDto.totalXp,
        motifsDiscovered: statsDto.motifsDiscovered,
        motifsLearned: statsDto.motifsLearned,
        motifsMastered: statsDto.motifsMastered,
        badgesEarned: statsDto.badgesEarned,
        quizzesCompleted: statsDto.quizzesCompleted,
        currentStreak: statsDto.currentStreak,
        longestStreak: 0, // Not in StatsDto, would need separate call
        rank: statsDto.rank.toEntity(),
        xpToNextRank: statsDto.xpToNextRank,
        nextRank: statsDto.nextRank?.toEntity(),
      );

      return Right(stats);
    } on ServerException catch (e) {
      return Left(ServerFailure(e.message, code: e.code, statusCode: e.statusCode));
    } catch (e) {
      return Left(UnexpectedFailure('Lấy thống kê thất bại: $e'));
    }
  }
}
