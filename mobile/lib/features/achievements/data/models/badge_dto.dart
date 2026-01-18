import 'package:freezed_annotation/freezed_annotation.dart';

part 'badge_dto.freezed.dart';
part 'badge_dto.g.dart';

/// Badge DTO for achievements system
/// Note: Backend API doesn't return 'id' field, so we use slug as identifier
@freezed
class BadgeDto with _$BadgeDto {
  const factory BadgeDto({
    /// ID field - uses slug as fallback since API doesn't return id
    @Default('') String id,
    @Default('') String slug,
    @Default('') String name,
    @JsonKey(name: 'name_en') String? nameEn,
    String? description,
    @JsonKey(name: 'icon_url') String? iconUrl,
    @Default('achievement') String category,
    @JsonKey(name: 'xp_bonus') @Default(0) int xpBonus,
    @JsonKey(name: 'earned_at') String? earnedAt,
  }) = _BadgeDto;

  factory BadgeDto.fromJson(Map<String, dynamic> json) =>
      _$BadgeDtoFromJson(json);
}

