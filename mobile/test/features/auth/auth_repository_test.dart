import 'package:dartz/dartz.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:luuniensuki_lms/core/errors/exceptions.dart';
import 'package:luuniensuki_lms/core/errors/failures.dart';
import 'package:luuniensuki_lms/core/network/network_info.dart';
import 'package:luuniensuki_lms/features/auth/data/datasources/auth_local_datasource.dart';
import 'package:luuniensuki_lms/features/auth/data/datasources/auth_remote_datasource.dart';
import 'package:luuniensuki_lms/features/auth/data/models/auth_response_dto.dart';
import 'package:luuniensuki_lms/features/auth/data/models/login_response_dto.dart';
import 'package:luuniensuki_lms/features/auth/data/models/refresh_token_response_dto.dart';
import 'package:luuniensuki_lms/features/auth/data/models/user_dto.dart';
import 'package:luuniensuki_lms/features/auth/data/repositories/auth_repository_impl.dart';
import 'package:luuniensuki_lms/features/auth/domain/entities/user.dart';
import 'package:mocktail/mocktail.dart';

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

  const tEmail = 'test@example.com';
  const tPassword = 'password123';
  const tDisplayName = 'Test User';
  const tAccessToken = 'access_token_123';
  const tRefreshToken = 'refresh_token_456';

  final tUserDto = UserDto(
    id: '123',
    email: tEmail,
    displayName: tDisplayName,
    role: 'student',
    totalXp: 100,
    currentStreak: 5,
    longestStreak: 10,
    gems: 50,
    hearts: 5,
    streakFreezes: 2,
  );

  final tLoginResponse = LoginResponseDto(
    user: tUserDto,
    accessToken: tAccessToken,
    refreshToken: tRefreshToken,
  );

  final tRefreshTokenResponse = RefreshTokenResponseDto(
    accessToken: tAccessToken,
    refreshToken: tRefreshToken,
  );

  group('T-U1: AuthRepository Tests', () {
    group('login', () {
      test('should return User when login is successful', () async {
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

        final result = await repository.login(
          email: tEmail,
          password: tPassword,
        );

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
        verify(() => mockLocalDataSource.saveAccessToken(tAccessToken))
            .called(1);
        verify(() => mockLocalDataSource.saveRefreshToken(tRefreshToken))
            .called(1);
        verify(() => mockLocalDataSource.cacheUser(tUserDto)).called(1);
      });

      test('should return NetworkFailure when there is no internet connection',
          () async {
        when(() => mockNetworkInfo.isConnected).thenAnswer((_) async => false);

        final result = await repository.login(
          email: tEmail,
          password: tPassword,
        );

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
        when(() => mockNetworkInfo.isConnected).thenAnswer((_) async => true);
        when(() => mockRemoteDataSource.login(
              email: any(named: 'email'),
              password: any(named: 'password'),
            )).thenThrow(
          const AuthException(
            'Email hoặc mật khẩu không đúng',
            code: 'INVALID_CREDENTIALS',
          ),
        );

        final result = await repository.login(
          email: tEmail,
          password: 'wrong_password',
        );

        expect(result, isA<Left<AuthFailure, User>>());
        result.fold(
          (failure) {
            expect(failure, isA<AuthFailure>());
            expect(failure.code, 'INVALID_CREDENTIALS');
          },
          (user) => fail('Should not return user'),
        );
      });
    });

    group('register', () {
      test('should return User when registration is successful', () async {
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

        final result = await repository.register(
          email: tEmail,
          password: tPassword,
          displayName: tDisplayName,
        );

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

      test('should return NetworkFailure when there is no internet connection',
          () async {
        when(() => mockNetworkInfo.isConnected).thenAnswer((_) async => false);

        final result = await repository.register(
          email: tEmail,
          password: tPassword,
          displayName: tDisplayName,
        );

        expect(result, isA<Left<NetworkFailure, User>>());
        result.fold(
          (failure) {
            expect(failure, isA<NetworkFailure>());
          },
          (user) => fail('Should not return user'),
        );
      });

      test('should return AuthFailure when email already exists', () async {
        when(() => mockNetworkInfo.isConnected).thenAnswer((_) async => true);
        when(() => mockRemoteDataSource.register(
              email: any(named: 'email'),
              password: any(named: 'password'),
              displayName: any(named: 'displayName'),
            )).thenThrow(
          const ServerException(
            'Email already exists',
            code: 'EMAIL_EXISTS',
            statusCode: 409,
          ),
        );

        final result = await repository.register(
          email: tEmail,
          password: tPassword,
          displayName: tDisplayName,
        );

        expect(result, isA<Left<AuthFailure, User>>());
        result.fold(
          (failure) {
            expect(failure, isA<AuthFailure>());
            expect(failure.code, 'EMAIL_EXISTS');
          },
          (user) => fail('Should not return user'),
        );
      });
    });

    group('logout', () {
      test('should clear local data when logout is successful', () async {
        when(() => mockNetworkInfo.isConnected).thenAnswer((_) async => true);
        when(() => mockRemoteDataSource.logout()).thenAnswer((_) async => {});
        when(() => mockLocalDataSource.clearAll()).thenAnswer((_) async => {});

        final result = await repository.logout();

        expect(result, isA<Right<Failure, void>>());

        verify(() => mockRemoteDataSource.logout()).called(1);
        verify(() => mockLocalDataSource.clearAll()).called(1);
      });

      test('should clear local data even when remote logout fails', () async {
        when(() => mockNetworkInfo.isConnected).thenAnswer((_) async => true);
        when(() => mockRemoteDataSource.logout())
            .thenThrow(const ServerException('Server error'));
        when(() => mockLocalDataSource.clearAll()).thenAnswer((_) async => {});

        final result = await repository.logout();

        expect(result, isA<Right<Failure, void>>());

        verify(() => mockLocalDataSource.clearAll()).called(1);
      });

      test('should clear local data when offline', () async {
        when(() => mockNetworkInfo.isConnected).thenAnswer((_) async => false);
        when(() => mockLocalDataSource.clearAll()).thenAnswer((_) async => {});

        final result = await repository.logout();

        expect(result, isA<Right<Failure, void>>());

        verify(() => mockLocalDataSource.clearAll()).called(1);
        verifyNever(() => mockRemoteDataSource.logout());
      });
    });

    group('refreshToken', () {
      test('should return true when token refresh is successful', () async {
        when(() => mockNetworkInfo.isConnected).thenAnswer((_) async => true);
        when(() => mockRemoteDataSource.refreshToken())
            .thenAnswer((_) async => tRefreshTokenResponse);
        when(() => mockLocalDataSource.saveAccessToken(any()))
            .thenAnswer((_) async => {});
        when(() => mockLocalDataSource.saveRefreshToken(any()))
            .thenAnswer((_) async => {});

        final result = await repository.refreshToken();

        expect(result, isA<Right<Failure, bool>>());
        result.fold(
          (failure) => fail('Should not return failure'),
          (success) {
            expect(success, true);
          },
        );

        verify(() => mockRemoteDataSource.refreshToken()).called(1);
        verify(() => mockLocalDataSource.saveAccessToken(tAccessToken))
            .called(1);
        verify(() => mockLocalDataSource.saveRefreshToken(tRefreshToken))
            .called(1);
      });

      test('should return NetworkFailure when offline', () async {
        when(() => mockNetworkInfo.isConnected).thenAnswer((_) async => false);

        final result = await repository.refreshToken();

        expect(result, isA<Left<NetworkFailure, bool>>());
        result.fold(
          (failure) {
            expect(failure, isA<NetworkFailure>());
          },
          (success) => fail('Should not return success'),
        );

        verifyNever(() => mockRemoteDataSource.refreshToken());
      });

      test('should clear tokens when refresh fails', () async {
        when(() => mockNetworkInfo.isConnected).thenAnswer((_) async => true);
        when(() => mockRemoteDataSource.refreshToken()).thenThrow(
          const AuthException(
            'Invalid refresh token',
            code: 'INVALID_TOKEN',
          ),
        );
        when(() => mockLocalDataSource.clearTokens())
            .thenAnswer((_) async => {});

        final result = await repository.refreshToken();

        expect(result, isA<Left<AuthFailure, bool>>());

        verify(() => mockLocalDataSource.clearTokens()).called(1);
      });
    });
  });
}

