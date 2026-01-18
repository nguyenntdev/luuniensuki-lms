import 'package:dartz/dartz.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:luuniensuki_lms/core/errors/exceptions.dart';
import 'package:luuniensuki_lms/core/errors/failures.dart';
import 'package:luuniensuki_lms/core/network/network_info.dart';
import 'package:luuniensuki_lms/features/auth/data/datasources/auth_local_datasource.dart';
import 'package:luuniensuki_lms/features/auth/data/datasources/auth_remote_datasource.dart';
import 'package:luuniensuki_lms/features/auth/data/models/auth_dtos.dart';
import 'package:luuniensuki_lms/features/auth/data/repositories/auth_repository_impl.dart';
import 'package:luuniensuki_lms/features/auth/domain/entities/user.dart';
import 'package:mocktail/mocktail.dart';

// Mock classes
class MockAuthRemoteDataSource extends Mock implements AuthRemoteDataSource {}
class MockAuthLocalDataSource extends Mock implements AuthLocalDataSource {}
class MockNetworkInfo extends Mock implements NetworkInfo {}

void main() {
  late AuthRepositoryImpl repository;
  late MockAuthRemoteDataSource mockRemoteDataSource;
  late MockAuthLocalDataSource mockLocalDataSource;
  late MockNetworkInfo mockNetworkInfo;

  setUp(() {
    mockRemoteDataSource = MockAuthRemoteDataSource();
    mockLocalDataSource = MockAuthLocalDataSource();
    mockNetworkInfo = MockNetworkInfo();
    repository = AuthRepositoryImpl(
      remoteDataSource: mockRemoteDataSource,
      localDataSource: mockLocalDataSource,
      networkInfo: mockNetworkInfo,
    );
  });

  // Test data
  const tEmail = 'test@example.com';
  const tPassword = 'password123';
  const tDisplayName = 'Test User';

  final tUserDto = UserDto(
    id: '1',
    email: tEmail,
    displayName: tDisplayName,
    role: 'learner',
    totalXp: 100,
  );

  final tStatsDto = StatsDto(
    totalXp: 100,
    rank: const RankDto(level: 1, name: 'Lính Mới', xp: 0),
    xpToNextRank: 0,
  );

  final tLoginResponse = LoginResponseDto(
    user: tUserDto,
    stats: tStatsDto,
    accessToken: 'access_token',
    refreshToken: 'refresh_token',
  );

  final tAuthResponse = AuthResponseDto(
    user: tUserDto,
    stats: tStatsDto,
  );

  group('login', () {
    test('should return User when login is successful', () async {
      // arrange
      when(() => mockNetworkInfo.isConnected).thenAnswer((_) async => true);
      when(() => mockRemoteDataSource.login(
            email: any(named: 'email'),
            password: any(named: 'password'),
          )).thenAnswer((_) async => tLoginResponse);
      when(() => mockLocalDataSource.saveAccessToken(any()))
          .thenAnswer((_) async => {});
      when(() => mockLocalDataSource.saveRefreshToken(any()))
          .thenAnswer((_) async => {});
      when(() => mockLocalDataSource.cacheUser(any()))
          .thenAnswer((_) async => {});

      // act
      final result = await repository.login(
        email: tEmail,
        password: tPassword,
      );

      // assert
      expect(result, isA<Right<Failure, User>>());
      result.fold(
        (failure) => fail('Should not return failure'),
        (user) {
          expect(user.email, tEmail);
          expect(user.displayName, tDisplayName);
        },
      );

      verify(() => mockNetworkInfo.isConnected).called(1);
      verify(() => mockRemoteDataSource.login(
            email: tEmail,
            password: tPassword,
          )).called(1);
      verify(() => mockLocalDataSource.saveAccessToken('access_token'))
          .called(1);
      verify(() => mockLocalDataSource.saveRefreshToken('refresh_token'))
          .called(1);
      verify(() => mockLocalDataSource.cacheUser(tUserDto)).called(1);
    });

    test('should return NetworkFailure when there is no internet connection',
        () async {
      // arrange
      when(() => mockNetworkInfo.isConnected).thenAnswer((_) async => false);

      // act
      final result = await repository.login(
        email: tEmail,
        password: tPassword,
      );

      // assert
      expect(result, isA<Left<NetworkFailure, User>>());
      result.fold(
        (failure) {
          expect(failure, isA<NetworkFailure>());
          expect(failure.message, 'Không có kết nối mạng');
        },
        (user) => fail('Should not return user'),
      );

      verify(() => mockNetworkInfo.isConnected).called(1);
      verifyNever(() => mockRemoteDataSource.login(
            email: any(named: 'email'),
            password: any(named: 'password'),
          ));
    });

    test('should return AuthFailure when credentials are invalid', () async {
      // arrange
      when(() => mockNetworkInfo.isConnected).thenAnswer((_) async => true);
      when(() => mockRemoteDataSource.login(
            email: any(named: 'email'),
            password: any(named: 'password'),
          )).thenThrow(const AuthException(
        'Email hoặc mật khẩu không đúng',
        code: 'INVALID_CREDENTIALS',
      ));

      // act
      final result = await repository.login(
        email: tEmail,
        password: tPassword,
      );

      // assert
      expect(result, isA<Left<AuthFailure, User>>());
      result.fold(
        (failure) {
          expect(failure, isA<AuthFailure>());
          expect(failure.code, 'INVALID_CREDENTIALS');
        },
        (user) => fail('Should not return user'),
      );
    });

    test('should return ServerFailure when server error occurs', () async {
      // arrange
      when(() => mockNetworkInfo.isConnected).thenAnswer((_) async => true);
      when(() => mockRemoteDataSource.login(
            email: any(named: 'email'),
            password: any(named: 'password'),
          )).thenThrow(const ServerException(
        message: 'Internal server error',
        code: 'SERVER_ERROR',
        statusCode: 500,
      ));

      // act
      final result = await repository.login(
        email: tEmail,
        password: tPassword,
      );

      // assert
      expect(result, isA<Left<ServerFailure, User>>());
      result.fold(
        (failure) {
          expect(failure, isA<ServerFailure>());
          final serverFailure = failure as ServerFailure;
          expect(serverFailure.statusCode, 500);
        },
        (user) => fail('Should not return user'),
      );
    });

    test('should return ValidationFailure when validation error occurs',
        () async {
      // arrange
      when(() => mockNetworkInfo.isConnected).thenAnswer((_) async => true);
      when(() => mockRemoteDataSource.login(
            email: any(named: 'email'),
            password: any(named: 'password'),
          )).thenThrow(const ValidationException(
        'Validation failed',
        fieldErrors: {
          'email': ['Email is required'],
          'password': ['Password must be at least 8 characters'],
        },
      ));

      // act
      final result = await repository.login(
        email: tEmail,
        password: tPassword,
      );

      // assert
      expect(result, isA<Left<ValidationFailure, User>>());
      result.fold(
        (failure) {
          expect(failure, isA<ValidationFailure>());
          final validationFailure = failure as ValidationFailure;
          expect(validationFailure.fieldErrors.containsKey('email'), true);
          expect(validationFailure.fieldErrors.containsKey('password'), true);
        },
        (user) => fail('Should not return user'),
      );
    });
  });

  group('register', () {
    test('should return User when registration is successful', () async {
      // arrange
      when(() => mockNetworkInfo.isConnected).thenAnswer((_) async => true);
      when(() => mockRemoteDataSource.register(
            email: any(named: 'email'),
            password: any(named: 'password'),
            displayName: any(named: 'displayName'),
          )).thenAnswer((_) async => tLoginResponse);
      when(() => mockLocalDataSource.saveAccessToken(any()))
          .thenAnswer((_) async => {});
      when(() => mockLocalDataSource.saveRefreshToken(any()))
          .thenAnswer((_) async => {});
      when(() => mockLocalDataSource.cacheUser(any()))
          .thenAnswer((_) async => {});

      // act
      final result = await repository.register(
        email: tEmail,
        password: tPassword,
        displayName: tDisplayName,
      );

      // assert
      expect(result, isA<Right<Failure, User>>());
      result.fold(
        (failure) => fail('Should not return failure'),
        (user) {
          expect(user.email, tEmail);
          expect(user.displayName, tDisplayName);
        },
      );

      verify(() => mockRemoteDataSource.register(
            email: tEmail,
            password: tPassword,
            displayName: tDisplayName,
          )).called(1);
    });

    test('should return AuthFailure when email already exists', () async {
      // arrange
      when(() => mockNetworkInfo.isConnected).thenAnswer((_) async => true);
      when(() => mockRemoteDataSource.register(
            email: any(named: 'email'),
            password: any(named: 'password'),
            displayName: any(named: 'displayName'),
          )).thenThrow(const ServerException(
        message: 'Email already exists',
        code: 'EMAIL_EXISTS',
        statusCode: 409,
      ));

      // act
      final result = await repository.register(
        email: tEmail,
        password: tPassword,
        displayName: tDisplayName,
      );

      // assert
      expect(result, isA<Left<AuthFailure, User>>());
      result.fold(
        (failure) {
          expect(failure, isA<AuthFailure>());
          expect(failure.code, 'EMAIL_EXISTS');
          expect(failure.message, 'Email đã được đăng ký');
        },
        (user) => fail('Should not return user'),
      );
    });

    test('should return ValidationFailure when validation fails', () async {
      // arrange
      when(() => mockNetworkInfo.isConnected).thenAnswer((_) async => true);
      when(() => mockRemoteDataSource.register(
            email: any(named: 'email'),
            password: any(named: 'password'),
            displayName: any(named: 'displayName'),
          )).thenThrow(const ValidationException(
        'Validation failed',
        fieldErrors: {'email': ['Invalid email format']},
      ));

      // act
      final result = await repository.register(
        email: tEmail,
        password: tPassword,
        displayName: tDisplayName,
      );

      // assert
      expect(result, isA<Left<ValidationFailure, User>>());
      result.fold(
        (failure) {
          expect(failure, isA<ValidationFailure>());
          final validationFailure = failure as ValidationFailure;
          expect(validationFailure.fieldErrors.containsKey('email'), true);
        },
        (user) => fail('Should not return user'),
      );
    });
  });

  group('logout', () {
    test('should clear local data and return success', () async {
      // arrange
      when(() => mockNetworkInfo.isConnected).thenAnswer((_) async => true);
      when(() => mockRemoteDataSource.logout()).thenAnswer((_) async => {});
      when(() => mockLocalDataSource.clearAll()).thenAnswer((_) async => {});

      // act
      final result = await repository.logout();

      // assert
      expect(result, const Right(null));
      verify(() => mockRemoteDataSource.logout()).called(1);
      verify(() => mockLocalDataSource.clearAll()).called(1);
    });

    test('should still clear local data even when server logout fails',
        () async {
      // arrange
      when(() => mockNetworkInfo.isConnected).thenAnswer((_) async => true);
      when(() => mockRemoteDataSource.logout()).thenThrow(
        const ServerException(
          message: 'Server error',
          statusCode: 500,
        ),
      );
      when(() => mockLocalDataSource.clearAll()).thenAnswer((_) async => {});

      // act
      final result = await repository.logout();

      // assert
      expect(result, const Right(null));
      verify(() => mockLocalDataSource.clearAll()).called(1);
    });

    test('should still return success when offline', () async {
      // arrange
      when(() => mockNetworkInfo.isConnected).thenAnswer((_) async => false);
      when(() => mockLocalDataSource.clearAll()).thenAnswer((_) async => {});

      // act
      final result = await repository.logout();

      // assert
      expect(result, const Right(null));
      verify(() => mockLocalDataSource.clearAll()).called(1);
      verifyNever(() => mockRemoteDataSource.logout());
    });
  });

  group('getCurrentUser', () {
    test('should return User from remote when online', () async {
      // arrange
      when(() => mockNetworkInfo.isConnected).thenAnswer((_) async => true);
      when(() => mockRemoteDataSource.getCurrentUser())
          .thenAnswer((_) async => tAuthResponse);
      when(() => mockLocalDataSource.cacheUser(any()))
          .thenAnswer((_) async => {});

      // act
      final result = await repository.getCurrentUser();

      // assert
      expect(result, isA<Right<Failure, User>>());
      result.fold(
        (failure) => fail('Should not return failure'),
        (user) {
          expect(user.email, tEmail);
        },
      );

      verify(() => mockNetworkInfo.isConnected).called(1);
      verify(() => mockRemoteDataSource.getCurrentUser()).called(1);
      verify(() => mockLocalDataSource.cacheUser(tUserDto)).called(1);
    });

    test('should return cached User when offline', () async {
      // arrange
      when(() => mockNetworkInfo.isConnected).thenAnswer((_) async => false);
      when(() => mockLocalDataSource.getCachedUser())
          .thenAnswer((_) async => tUserDto);

      // act
      final result = await repository.getCurrentUser();

      // assert
      expect(result, isA<Right<Failure, User>>());
      result.fold(
        (failure) => fail('Should not return failure'),
        (user) {
          expect(user.email, tEmail);
        },
      );

      verify(() => mockLocalDataSource.getCachedUser()).called(1);
      verifyNever(() => mockRemoteDataSource.getCurrentUser());
    });

    test('should fall back to cache when network error occurs', () async {
      // arrange
      when(() => mockNetworkInfo.isConnected).thenAnswer((_) async => true);
      when(() => mockRemoteDataSource.getCurrentUser()).thenThrow(
        const NetworkException('Connection failed'),
      );
      when(() => mockLocalDataSource.getCachedUser())
          .thenAnswer((_) async => tUserDto);

      // act
      final result = await repository.getCurrentUser();

      // assert
      expect(result, isA<Right<Failure, User>>());
      result.fold(
        (failure) => fail('Should not return failure'),
        (user) {
          expect(user.email, tEmail);
        },
      );

      verify(() => mockLocalDataSource.getCachedUser()).called(1);
    });

    test('should return AuthFailure when no cached user and offline', () async {
      // arrange
      when(() => mockNetworkInfo.isConnected).thenAnswer((_) async => false);
      when(() => mockLocalDataSource.getCachedUser())
          .thenAnswer((_) async => null);

      // act
      final result = await repository.getCurrentUser();

      // assert
      expect(result, isA<Left<AuthFailure, User>>());
      result.fold(
        (failure) {
          expect(failure, isA<AuthFailure>());
        },
        (user) => fail('Should not return user'),
      );
    });
  });
}

