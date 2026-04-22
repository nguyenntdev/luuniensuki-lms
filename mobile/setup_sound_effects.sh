#!/bin/bash

# Sound Effects System - Setup Script
# This script sets up the sound effects system

set -e

echo "🎵 Sound Effects System Setup"
echo "================================"
echo ""

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Step 1: Install Flutter dependencies
echo -e "${BLUE}Step 1: Installing Flutter dependencies...${NC}"
if command -v flutter &> /dev/null; then
    cd "$(dirname "$0")"
    flutter pub get
    echo -e "${GREEN}✅ Dependencies installed${NC}"
else
    echo -e "${YELLOW}⚠️  Flutter not found in PATH${NC}"
    echo "Please run manually: cd mobile && flutter pub get"
fi
echo ""

# Step 2: Check for sound files
echo -e "${BLUE}Step 2: Checking for sound files...${NC}"
SOUNDS_DIR="assets/sounds"
SOUND_FILES=("correct.mp3" "wrong.mp3" "tap.mp3" "xp_gain.mp3" "level_up.mp3" "streak_complete.mp3" "lesson_complete.mp3")
MISSING_FILES=0

for file in "${SOUND_FILES[@]}"; do
    if [ -f "$SOUNDS_DIR/$file" ]; then
        echo -e "${GREEN}✅ $file${NC}"
    else
        echo -e "${YELLOW}⚠️  $file (missing)${NC}"
        MISSING_FILES=$((MISSING_FILES + 1))
    fi
done
echo ""

# Step 3: Offer to generate sounds
if [ $MISSING_FILES -gt 0 ]; then
    echo -e "${YELLOW}⚠️  Found $MISSING_FILES missing sound file(s)${NC}"
    echo ""
    echo "You have two options:"
    echo "  1. Generate placeholder sounds using Python script"
    echo "  2. Download professional sounds (see assets/sounds/README.md)"
    echo ""
    echo "To generate placeholder sounds:"
    echo "  cd $SOUNDS_DIR"
    echo "  pip3 install pydub numpy"
    echo "  python3 generate_sounds.py"
    echo ""
else
    echo -e "${GREEN}✅ All sound files present${NC}"
fi

# Step 4: Summary
echo "================================"
echo -e "${GREEN}Setup Summary:${NC}"
echo "  • Sound service: mobile/lib/core/services/sound_service.dart"
echo "  • Helper widgets: mobile/lib/core/widgets/sound_button.dart"
echo "  • Demo screen: mobile/lib/examples/sound_effects_demo_screen.dart"
echo "  • Integration: Quiz screens, XP celebration"
echo "  • Settings: Already integrated"
echo ""
echo -e "${BLUE}Next Steps:${NC}"
echo "  1. Generate or acquire sound files (if needed)"
echo "  2. Run the app and test sound effects"
echo "  3. Check Settings → Sound & Effects to toggle"
echo "  4. See SOUND_EFFECTS_TESTING.md for full test checklist"
echo ""
echo -e "${GREEN}✨ Setup complete!${NC}"

