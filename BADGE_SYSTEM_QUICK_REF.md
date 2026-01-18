# Badge System Quick Reference

## Usage Examples

### Load Badges in Screen
```dart
// In initState or onMount
ref.read(badgeNotifierProvider.notifier).loadBadges();

// Force refresh
ref.read(badgeNotifierProvider.notifier).refresh();
```

### Watch Badges in Widget
```dart
final badgesAsync = ref.watch(badgeNotifierProvider);

badgesAsync.when(
  loading: () => CircularProgressIndicator(),
  error: (err, stack) => ErrorWidget(err),
  data: (badges) => BadgeGrid(badges),
);
```

### Get Earned Badges Count
```dart
final earnedCount = ref.watch(earnedBadgesCountProvider);
// Returns: int
```

### Get Only Earned Badges
```dart
final earnedBadges = ref.watch(earnedBadgesProvider);
// Returns: List<BadgeDto>
```

### Show Badge Details
```dart
BadgeDetailSheet.show(context, badge);
```

## Badge Categories

| Category | Vietnamese | Icon |
|----------|-----------|------|
| discovery | Khám Phá | visibility |
| learning | Học Tập | school |
| mastery | Thành Thạo | star |
| streak | Chuỗi Ngày | local_fire_department |
| collection | Sưu Tập | collections |
| achievement | Thành Tích | workspace_premium |

## API Endpoints

```
GET /api/v1/badges
Response: [
  {
    "id": "badge_id",
    "slug": "first_discovery",
    "name": "Người Khám Phá Đầu Tiên",
    "name_en": "First Discovery",
    "description": "Khám phá văn hóa đầu tiên",
    "icon_url": null,
    "category": "discovery",
    "xp_bonus": 50
  }
]

GET /api/v1/users/me/badges
Response: [
  {
    "badge_id": "badge_id",
    "earned_at": "2024-01-15T10:30:00Z"
  }
]
```

## Badge DTO Structure

```dart
BadgeDto(
  id: String,
  slug: String,
  name: String,
  nameEn: String?,
  description: String?,
  iconUrl: String?,
  category: String,
  xpBonus: int,
  earnedAt: String?,  // null = not earned
)
```

## File Locations

```
mobile/lib/features/achievements/
├── data/models/
│   ├── badge_dto.dart
│   ├── badge_dto.freezed.dart
│   └── badge_dto.g.dart
├── presentation/
│   ├── providers/
│   │   └── badge_provider.dart
│   ├── screens/
│   │   └── achievements_screen.dart
│   └── widgets/
│       └── badge_detail_sheet.dart
```

## Common Tasks

### Add New Badge Category
1. Update backend to return new category
2. Add case to `_getBadgeIcon()` in `achievements_screen.dart`
3. Add case to `_getCategoryIcon()` in `badge_detail_sheet.dart`
4. Add Vietnamese name to `_getCategoryName()` in `badge_detail_sheet.dart`

### Change Cache Duration
```dart
// In badge_provider.dart
static const Duration _cacheMaxAge = Duration(hours: 1); // Change here
```

### Add Badge Filter
```dart
final filteredBadges = ref.watch(badgeNotifierProvider).whenData(
  (badges) => badges.where((b) => b.category == 'discovery').toList()
);
```

## Troubleshooting

**Badges not loading?**
- Check network connection
- Verify API endpoints in `api_constants.dart`
- Check authentication token is valid

**Cache not working?**
- Verify Hive is initialized in `main.dart`
- Check cache validation logic in provider

**Icons not showing?**
- Verify category value from API
- Check `_getBadgeIcon()` mapping

**Build errors?**
- Run: `flutter pub run build_runner build --delete-conflicting-outputs`

## Performance Tips

- Use `earnedBadgesCountProvider` instead of filtering list manually
- Cache is checked automatically, don't fetch on every build
- Use `forceRefresh: true` only when needed (pull-to-refresh)

