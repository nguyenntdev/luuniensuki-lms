#!/bin/bash

# Navigate to project root
cd "$(dirname "$0")"

# Add all changes
git add .

# Create commit with conventional commits format
git commit -m "fix(mobile): Fix motif images, detail DTO, explore race condition, navbar width (v1.4.0)

## Bug Fixes

### Collection Screen - Motif Images
- Replace hardcoded placeholder icon with CachedNetworkImage
- Actually load motif thumbnails from API

### Motif Detail Error
- Fix 'type null is not a subtype of type String' error
- Create new UrnInfoDto class to match backend's nested urn object
- Change MotifDetailDto from 'urn_id: String' to 'urn: UrnInfoDto'
- Make LessonContentDto 'id' and 'motif_id' fields optional (backend doesn't send them)

### Explore Screen Blank
- Fix race condition with auth state
- Add fireImmediately: true to ref.listenManual
- Properly store and dispose ProviderSubscription
- Ensure loadUrns() is called regardless of auth timing

### Navbar Indicator Width
- Widen gold background pill from 50% to 70% of item width

## Files Changed
- mobile/lib/features/collection/presentation/screens/collection_screen.dart
- mobile/lib/features/urn_viewer/data/models/urn_dtos.dart
- mobile/lib/features/urn_viewer/data/mappers/urn_mappers.dart
- mobile/lib/features/explore/presentation/screens/explore_screen.dart
- mobile/lib/shared/widgets/glass/glass_bottom_nav.dart
- mobile/pubspec.yaml (version bump to 1.4.0+5)
- Generated files (.g.dart, .freezed.dart)

BREAKING CHANGE: None"

# Show commit result
echo ""
echo "✅ Commit created successfully!"
echo ""
git log -1 --pretty=format:"%h - %s" --no-color
echo ""
echo ""
echo "To push this commit, run: git push origin main"

