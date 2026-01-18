import 'package:dartz/dartz.dart';
import 'package:flutter/foundation.dart';

import '../errors/failures.dart';
import '../errors/exceptions.dart';
import '../network/network_info.dart';
import '../storage/hive_storage.dart';

abstract class OfflineFirstRepository<T> {
  final NetworkInfo networkInfo;
  final HiveStorage hiveStorage;

  OfflineFirstRepository({
    required this.networkInfo,
    required this.hiveStorage,
  });

  Future<Either<Failure, T>> executeOfflineFirst({
    required Future<T> Function() networkCall,
    required Future<T?> Function() getCached,
    required Future<void> Function(T data) saveCache,
    String? operationName,
    Duration? cacheMaxAge,
    bool forceNetwork = false,
  }) async {
    final opName = operationName ?? 'Operation';
    
    if (!forceNetwork) {
      final isConnected = await networkInfo.isConnected;
      
      if (!isConnected) {
        debugPrint('[$opName] Offline - attempting cache fallback');
        return _getCachedOrFail(getCached, opName);
      }
    }

    try {
      debugPrint('[$opName] Network available - fetching fresh data');
      final result = await networkCall();
      
      try {
        await saveCache(result);
        debugPrint('[$opName] Data cached successfully');
      } catch (cacheError) {
        debugPrint('[$opName] Failed to cache data: $cacheError');
      }
      
      return Right(result);
    } on NetworkException catch (e) {
      debugPrint('[$opName] Network error: ${e.message} - falling back to cache');
      return _getCachedOrFail(getCached, opName);
    } on ServerException catch (e) {
      if (e.statusCode == 401) {
        return Left(AuthFailure.sessionExpired());
      }
      
      debugPrint('[$opName] Server error (${e.statusCode}): ${e.message} - trying cache');
      final cachedResult = await _getCachedOrFail(getCached, opName);
      
      return cachedResult.fold(
        (failure) => Left(ServerFailure(e.message, code: e.code, statusCode: e.statusCode)),
        (data) => Right(data),
      );
    } on AuthException catch (e) {
      if (e.shouldLogout || e.code == 'SESSION_EXPIRED') {
        return Left(AuthFailure.sessionExpired());
      }
      return Left(AuthFailure(e.message, code: e.code));
    } catch (e) {
      debugPrint('[$opName] Unexpected error: $e - trying cache');
      return _getCachedOrFail(getCached, opName);
    }
  }

  Future<Either<Failure, T>> _getCachedOrFail(
    Future<T?> Function() getCached,
    String operationName,
  ) async {
    try {
      final cached = await getCached();
      if (cached != null) {
        debugPrint('[$operationName] Using cached data');
        return Right(cached);
      }
      debugPrint('[$operationName] No cached data available');
      return Left(CacheFailure('No cached data available'));
    } on CacheException catch (e) {
      return Left(CacheFailure(e.message));
    } catch (e) {
      return Left(CacheFailure('Failed to retrieve cached data: $e'));
    }
  }

  Future<Either<Failure, T>> executeCacheFirst({
    required Future<T> Function() networkCall,
    required Future<T?> Function() getCached,
    required Future<void> Function(T data) saveCache,
    required bool Function()? isCacheValid,
    String? operationName,
  }) async {
    final opName = operationName ?? 'Operation';
    
    if (isCacheValid != null && isCacheValid()) {
      debugPrint('[$opName] Cache is valid - returning cached data');
      final cached = await getCached();
      if (cached != null) {
        _refreshInBackground(networkCall, saveCache, opName);
        return Right(cached);
      }
    }

    final isConnected = await networkInfo.isConnected;
    if (!isConnected) {
      debugPrint('[$opName] Offline - using cache');
      return _getCachedOrFail(getCached, opName);
    }

    return executeOfflineFirst(
      networkCall: networkCall,
      getCached: getCached,
      saveCache: saveCache,
      operationName: opName,
    );
  }

  void _refreshInBackground(
    Future<T> Function() networkCall,
    Future<void> Function(T data) saveCache,
    String operationName,
  ) {
    networkInfo.isConnected.then((isConnected) {
      if (isConnected) {
        networkCall().then((result) {
          saveCache(result);
          debugPrint('[$operationName] Background refresh completed');
        }).catchError((error) {
          debugPrint('[$operationName] Background refresh failed: $error');
        });
      }
    });
  }

  Future<Either<Failure, R>> executeWriteOperation<R>({
    required Future<R> Function() networkCall,
    Future<void> Function()? onSuccess,
    String? operationName,
  }) async {
    final opName = operationName ?? 'Write Operation';
    final isConnected = await networkInfo.isConnected;

    if (!isConnected) {
      debugPrint('[$opName] Offline - operation will be queued for sync');
      return Left(NetworkFailure('No internet connection. Changes will be synced when online.'));
    }

    try {
      debugPrint('[$opName] Executing write operation');
      final result = await networkCall();
      
      if (onSuccess != null) {
        await onSuccess();
      }
      
      return Right(result);
    } on NetworkException catch (e) {
      return Left(NetworkFailure(e.message));
    } on ServerException catch (e) {
      return Left(ServerFailure(e.message, code: e.code, statusCode: e.statusCode));
    } on AuthException catch (e) {
      return Left(AuthFailure(e.message, code: e.code));
    } catch (e) {
      return Left(UnexpectedFailure('Write operation failed: $e'));
    }
  }
}

