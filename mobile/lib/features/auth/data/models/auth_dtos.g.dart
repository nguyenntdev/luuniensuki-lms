// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'auth_dtos.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

_$LoginRequestDtoImpl _$$LoginRequestDtoImplFromJson(
        Map<String, dynamic> json) =>
    _$LoginRequestDtoImpl(
      email: json['email'] as String,
      password: json['password'] as String,
    );

Map<String, dynamic> _$$LoginRequestDtoImplToJson(
        _$LoginRequestDtoImpl instance) =>
    <String, dynamic>{
      'email': instance.email,
      'password': instance.password,
    };

_$RegisterRequestDtoImpl _$$RegisterRequestDtoImplFromJson(
        Map<String, dynamic> json) =>
    _$RegisterRequestDtoImpl(
      email: json['email'] as String,
      password: json['password'] as String,
      displayName: json['display_name'] as String,
    );

Map<String, dynamic> _$$RegisterRequestDtoImplToJson(
        _$RegisterRequestDtoImpl instance) =>
    <String, dynamic>{
      'email': instance.email,
      'password': instance.password,
      'display_name': instance.displayName,
    };

_$UserDtoImpl _$$UserDtoImplFromJson(Map<String, dynamic> json) =>
    _$UserDtoImpl(
      id: json['id'] as String,
      email: json['email'] as String,
      displayName: json['display_name'] as String,
      avatarUrl: json['avatar_url'] as String?,
      username: json['username'] as String?,
      role: json['role'] as String,
      totalXp: (json['total_xp'] as num?)?.toInt() ?? 0,
      isProfilePublic: json['is_profile_public'] as bool? ?? false,
      currentStreak: (json['current_streak'] as num?)?.toInt() ?? 0,
      longestStreak: (json['longest_streak'] as num?)?.toInt() ?? 0,
      streakFreezes: (json['streak_freezes'] as num?)?.toInt() ?? 0,
      createdAt: json['created_at'] as String?,
      lastActiveAt: json['last_active_at'] as String?,
    );

Map<String, dynamic> _$$UserDtoImplToJson(_$UserDtoImpl instance) =>
    <String, dynamic>{
      'id': instance.id,
      'email': instance.email,
      'display_name': instance.displayName,
      'avatar_url': instance.avatarUrl,
      'username': instance.username,
      'role': instance.role,
      'total_xp': instance.totalXp,
      'is_profile_public': instance.isProfilePublic,
      'current_streak': instance.currentStreak,
      'longest_streak': instance.longestStreak,
      'streak_freezes': instance.streakFreezes,
      'created_at': instance.createdAt,
      'last_active_at': instance.lastActiveAt,
    };

_$AuthResponseDtoImpl _$$AuthResponseDtoImplFromJson(
        Map<String, dynamic> json) =>
    _$AuthResponseDtoImpl(
      user: UserDto.fromJson(json['user'] as Map<String, dynamic>),
      stats: StatsDto.fromJson(json['stats'] as Map<String, dynamic>),
    );

Map<String, dynamic> _$$AuthResponseDtoImplToJson(
        _$AuthResponseDtoImpl instance) =>
    <String, dynamic>{
      'user': instance.user,
      'stats': instance.stats,
    };

_$StatsDtoImpl _$$StatsDtoImplFromJson(Map<String, dynamic> json) =>
    _$StatsDtoImpl(
      totalXp: (json['total_xp'] as num?)?.toInt() ?? 0,
      rank: RankDto.fromJson(json['rank'] as Map<String, dynamic>),
      xpToNextRank: (json['xp_to_next_rank'] as num?)?.toInt() ?? 0,
      nextRank: json['next_rank'] == null
          ? null
          : RankDto.fromJson(json['next_rank'] as Map<String, dynamic>),
      motifsDiscovered: (json['motifs_discovered'] as num?)?.toInt() ?? 0,
      motifsLearned: (json['motifs_learned'] as num?)?.toInt() ?? 0,
      motifsMastered: (json['motifs_mastered'] as num?)?.toInt() ?? 0,
      badgesEarned: (json['badges_earned'] as num?)?.toInt() ?? 0,
      quizzesCompleted: (json['quizzes_completed'] as num?)?.toInt() ?? 0,
      currentStreak: (json['current_streak'] as num?)?.toInt() ?? 0,
    );

Map<String, dynamic> _$$StatsDtoImplToJson(_$StatsDtoImpl instance) =>
    <String, dynamic>{
      'total_xp': instance.totalXp,
      'rank': instance.rank,
      'xp_to_next_rank': instance.xpToNextRank,
      'next_rank': instance.nextRank,
      'motifs_discovered': instance.motifsDiscovered,
      'motifs_learned': instance.motifsLearned,
      'motifs_mastered': instance.motifsMastered,
      'badges_earned': instance.badgesEarned,
      'quizzes_completed': instance.quizzesCompleted,
      'current_streak': instance.currentStreak,
    };

_$RankDtoImpl _$$RankDtoImplFromJson(Map<String, dynamic> json) =>
    _$RankDtoImpl(
      level: (json['level'] as num).toInt(),
      name: json['name'] as String,
      xp: (json['xp'] as num).toInt(),
    );

Map<String, dynamic> _$$RankDtoImplToJson(_$RankDtoImpl instance) =>
    <String, dynamic>{
      'level': instance.level,
      'name': instance.name,
      'xp': instance.xp,
    };

_$LoginResponseDtoImpl _$$LoginResponseDtoImplFromJson(
        Map<String, dynamic> json) =>
    _$LoginResponseDtoImpl(
      accessToken: json['access_token'] as String?,
      refreshToken: json['refresh_token'] as String?,
      tokenType: json['token_type'] as String? ?? 'bearer',
      user: UserDto.fromJson(json['user'] as Map<String, dynamic>),
      stats: StatsDto.fromJson(json['stats'] as Map<String, dynamic>),
    );

Map<String, dynamic> _$$LoginResponseDtoImplToJson(
        _$LoginResponseDtoImpl instance) =>
    <String, dynamic>{
      'access_token': instance.accessToken,
      'refresh_token': instance.refreshToken,
      'token_type': instance.tokenType,
      'user': instance.user,
      'stats': instance.stats,
    };

_$RefreshTokenResponseDtoImpl _$$RefreshTokenResponseDtoImplFromJson(
        Map<String, dynamic> json) =>
    _$RefreshTokenResponseDtoImpl(
      accessToken: json['access_token'] as String?,
      refreshToken: json['refresh_token'] as String?,
      tokenType: json['token_type'] as String? ?? 'bearer',
    );

Map<String, dynamic> _$$RefreshTokenResponseDtoImplToJson(
        _$RefreshTokenResponseDtoImpl instance) =>
    <String, dynamic>{
      'access_token': instance.accessToken,
      'refresh_token': instance.refreshToken,
      'token_type': instance.tokenType,
    };

_$UpdateProfileRequestDtoImpl _$$UpdateProfileRequestDtoImplFromJson(
        Map<String, dynamic> json) =>
    _$UpdateProfileRequestDtoImpl(
      displayName: json['display_name'] as String?,
      username: json['username'] as String?,
      avatarUrl: json['avatar_url'] as String?,
      isProfilePublic: json['is_profile_public'] as bool?,
    );

Map<String, dynamic> _$$UpdateProfileRequestDtoImplToJson(
        _$UpdateProfileRequestDtoImpl instance) =>
    <String, dynamic>{
      'display_name': instance.displayName,
      'username': instance.username,
      'avatar_url': instance.avatarUrl,
      'is_profile_public': instance.isProfilePublic,
    };

_$ChangePasswordRequestDtoImpl _$$ChangePasswordRequestDtoImplFromJson(
        Map<String, dynamic> json) =>
    _$ChangePasswordRequestDtoImpl(
      currentPassword: json['current_password'] as String,
      newPassword: json['new_password'] as String,
    );

Map<String, dynamic> _$$ChangePasswordRequestDtoImplToJson(
        _$ChangePasswordRequestDtoImpl instance) =>
    <String, dynamic>{
      'current_password': instance.currentPassword,
      'new_password': instance.newPassword,
    };
