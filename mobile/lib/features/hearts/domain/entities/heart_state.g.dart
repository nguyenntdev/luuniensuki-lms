// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'heart_state.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

_$HeartStateImpl _$$HeartStateImplFromJson(Map<String, dynamic> json) =>
    _$HeartStateImpl(
      maxHearts: (json['maxHearts'] as num?)?.toInt() ?? 5,
      currentHearts: (json['currentHearts'] as num?)?.toInt() ?? 5,
      lastRefillTime: DateTime.parse(json['lastRefillTime'] as String),
      refillIntervalMinutes:
          (json['refillIntervalMinutes'] as num?)?.toInt() ?? 30,
      isUnlimited: json['isUnlimited'] as bool? ?? false,
    );

Map<String, dynamic> _$$HeartStateImplToJson(_$HeartStateImpl instance) =>
    <String, dynamic>{
      'maxHearts': instance.maxHearts,
      'currentHearts': instance.currentHearts,
      'lastRefillTime': instance.lastRefillTime.toIso8601String(),
      'refillIntervalMinutes': instance.refillIntervalMinutes,
      'isUnlimited': instance.isUnlimited,
    };
