import 'package:freezed_annotation/freezed_annotation.dart';

part 'auth_dtos.freezed.dart';
part 'auth_dtos.g.dart';

/// Login request DTO
@freezed
class LoginRequestDto with _$LoginRequestDto {
  const factory LoginRequestDto({
    required String email,
    required String password,
  }) = _LoginRequestDto;

  factory LoginRequestDto.fromJson(Map<String, dynamic> json) =>
      _$LoginRequestDtoFromJson(json);
}

/// Register request DTO
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

/// User DTO from API response
@freezed
class UserDto with _$UserDto {
  const factory UserDto({
    required String id,
    required String email,
    @JsonKey(name: 'display_name') required String displayName,
    @JsonKey(name: 'avatar_url') String? avatarUrl,
    String? username,
    required String role,
    @JsonKey(name: 'total_xp') @Default(0) int totalXp,
    @JsonKey(name: 'is_profile_public') @Default(false) bool isProfilePublic,
    @JsonKey(name: 'current_streak') @Default(0) int currentStreak,
    @JsonKey(name: 'longest_streak') @Default(0) int longestStreak,
    @JsonKey(name: 'streak_freezes') @Default(0) int streakFreezes,
    @JsonKey(name: 'created_at') String? createdAt,
    @JsonKey(name: 'last_active_at') String? lastActiveAt,
  }) = _UserDto;

  factory UserDto.fromJson(Map<String, dynamic> json) =>
      _$UserDtoFromJson(json);
}

/// Auth response DTO (returned from /auth/me, login, register)
@freezed
class AuthResponseDto with _$AuthResponseDto {
  const factory AuthResponseDto({
    required UserDto user,
    required StatsDto stats,
  }) = _AuthResponseDto;

  factory AuthResponseDto.fromJson(Map<String, dynamic> json) =>
      _$AuthResponseDtoFromJson(json);
}

/// Stats DTO containing XP and rank information
@freezed
class StatsDto with _$StatsDto {
  const factory StatsDto({
    @JsonKey(name: 'total_xp') @Default(0) int totalXp,
    required RankDto rank,
    @JsonKey(name: 'xp_to_next_rank') @Default(0) int xpToNextRank,
    @JsonKey(name: 'next_rank') RankDto? nextRank,
    @JsonKey(name: 'motifs_discovered') @Default(0) int motifsDiscovered,
    @JsonKey(name: 'motifs_learned') @Default(0) int motifsLearned,
    @JsonKey(name: 'motifs_mastered') @Default(0) int motifsMastered,
    @JsonKey(name: 'badges_earned') @Default(0) int badgesEarned,
    @JsonKey(name: 'quizzes_completed') @Default(0) int quizzesCompleted,
    @JsonKey(name: 'current_streak') @Default(0) int currentStreak,
  }) = _StatsDto;

  factory StatsDto.fromJson(Map<String, dynamic> json) =>
      _$StatsDtoFromJson(json);
}

/// Rank DTO
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

/// Login response DTO (when tokens are returned in body instead of cookies)
@freezed
class LoginResponseDto with _$LoginResponseDto {
  const factory LoginResponseDto({
    @JsonKey(name: 'access_token') String? accessToken,
    @JsonKey(name: 'refresh_token') String? refreshToken,
    @JsonKey(name: 'token_type') @Default('bearer') String tokenType,
    required UserDto user,
    required StatsDto stats,
  }) = _LoginResponseDto;

  factory LoginResponseDto.fromJson(Map<String, dynamic> json) =>
      _$LoginResponseDtoFromJson(json);
}

/// Refresh token response DTO
@freezed
class RefreshTokenResponseDto with _$RefreshTokenResponseDto {
  const factory RefreshTokenResponseDto({
    @JsonKey(name: 'access_token') String? accessToken,
    @JsonKey(name: 'refresh_token') String? refreshToken,
    @JsonKey(name: 'token_type') @Default('bearer') String tokenType,
  }) = _RefreshTokenResponseDto;

  factory RefreshTokenResponseDto.fromJson(Map<String, dynamic> json) =>
      _$RefreshTokenResponseDtoFromJson(json);
}

/// Update profile request DTO
@freezed
class UpdateProfileRequestDto with _$UpdateProfileRequestDto {
  const factory UpdateProfileRequestDto({
    @JsonKey(name: 'display_name') String? displayName,
    String? username,
    @JsonKey(name: 'avatar_url') String? avatarUrl,
    @JsonKey(name: 'is_profile_public') bool? isProfilePublic,
  }) = _UpdateProfileRequestDto;

  factory UpdateProfileRequestDto.fromJson(Map<String, dynamic> json) =>
      _$UpdateProfileRequestDtoFromJson(json);
}

/// Change password request DTO
@freezed
class ChangePasswordRequestDto with _$ChangePasswordRequestDto {
  const factory ChangePasswordRequestDto({
    @JsonKey(name: 'current_password') required String currentPassword,
    @JsonKey(name: 'new_password') required String newPassword,
  }) = _ChangePasswordRequestDto;

  factory ChangePasswordRequestDto.fromJson(Map<String, dynamic> json) =>
      _$ChangePasswordRequestDtoFromJson(json);
}
