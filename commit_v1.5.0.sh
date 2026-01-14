#!/bin/bash

# Commit script cho v1.5.0 - Gamification & UX Release

set -e

echo "📝 Committing v1.5.0 changes..."

# Stage all changes
git add -A

# Commit with detailed message
git commit -m "feat(mobile): Implement Gamification & UX improvements v1.5.0

🎮 NEW FEATURES:
- Onboarding Screen với 4 slides và animations
- Sound Effects System (7 sounds + haptic fallback)
- Shimmer Loading Skeletons cho Explore/Collection
- Enhanced Achievements/Badges (13 badges, 4 tiers)
- Quiz Hint System (5 gems, loại bỏ 2 đáp án sai)
- Quiz Progress Auto-Save với resume dialog

🐛 BUG FIXES:
- Memory leak trong urn_viewer_screen.dart (Timer fix)
- Null safety trong quiz_screen.dart (_startTime)
- Race condition trong main.dart (await initialize)
- Navigation consistency (GoRouter only)
- Text overflow trong profile_screen.dart
- Haptic feedback cho GlassButton

📊 ANALYSIS:
- UX/User Flow analysis complete
- UI Components deep dive
- Duolingo gamification research
- 26 bugs identified & 6 critical fixed

📁 FILES:
- 40+ files created
- 6 files modified
- 30+ documentation files

Co-authored-by: AI Assistant <assistant@anthropic.com>"

echo "✅ Committed successfully!"
echo ""
echo "To push, run: git push origin main"

