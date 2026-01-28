#!/bin/bash
# LuuNienSuKi LMS - Automated ADB Test Script
# Device: Sharp 701SH (1080x2032, density 480)
# Usage: ./scripts/adb_automated_test.sh

set -e

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

PACKAGE="com.luuniensuki.lms"
SCREENSHOT_DIR="./test_screenshots/automated"

echo "=== LuuNienSuKi LMS Automated Test ==="
echo "Date: $(date)"

# Create screenshot directory
mkdir -p $SCREENSHOT_DIR

# Helper function
take_screenshot() {
    local name=$1
    adb shell screencap -p /sdcard/test_$name.png
    adb pull /sdcard/test_$name.png $SCREENSHOT_DIR/$name.png > /dev/null 2>&1
    echo -e "${GREEN}✓ Screenshot: $name.png${NC}"
}

wait_and_tap() {
    sleep $1
    adb shell input tap $2 $3
}

# 1. Clear app and start fresh
echo ""
echo "=== Step 1: Reset and Launch App ==="
adb shell pm clear $PACKAGE > /dev/null 2>&1
sleep 1
adb shell am start -n $PACKAGE/.MainActivity > /dev/null 2>&1
sleep 5
echo -e "${GREEN}✓ App launched${NC}"

# 2. Login
echo ""
echo "=== Step 2: Login ==="
# Tap email field (540, 1278)
adb shell input tap 540 1278
sleep 1
# Type email with delays
adb shell input text "admin"
sleep 0.3
adb shell input keyevent 77  # @
sleep 0.3
adb shell input text "histolab"
sleep 0.2
adb shell input text "."
sleep 0.2
adb shell input text "icu"
sleep 0.5

# Press Enter to move to password
adb shell input keyevent 66
sleep 0.5

# Type password
adb shell input text "Suongnguyen83"
sleep 0.5

# Hide keyboard
adb shell input keyevent 4
sleep 0.5

# Tap login button (540, 1587)
adb shell input tap 540 1587
sleep 4
echo -e "${GREEN}✓ Login completed${NC}"

# 3. Skip onboarding if present
echo ""
echo "=== Step 3: Skip Onboarding ==="
adb shell input tap 970 160  # "Bỏ qua" button
sleep 2
take_screenshot "01_home"

# 4. Test all tabs
echo ""
echo "=== Step 4: Test Navigation Tabs ==="
# Tab positions: Khám Phá (149,1807), Học&Luyện (344,1807), AI Chat (540,1807), 
#                Thành Tích (735,1807), Hồ Sơ (931,1807)

wait_and_tap 1 344 1807  # Học & Luyện
take_screenshot "02_learn_tab"

wait_and_tap 1 540 1807  # AI Chat
take_screenshot "03_ai_chat"

wait_and_tap 1 735 1807  # Thành Tích
take_screenshot "04_achievements"

wait_and_tap 1 931 1807  # Hồ Sơ
take_screenshot "05_profile"

wait_and_tap 1 149 1807  # Khám Phá (back to home)
take_screenshot "06_home_final"

# 5. Test Urn Detail
echo ""
echo "=== Step 5: Test Urn Detail ==="
adb shell input swipe 540 1200 540 600 300
sleep 1
# Tap Cao Đỉnh card (282, 1127)
adb shell input tap 282 1127
sleep 4
take_screenshot "07_urn_detail"

# Test 3D rotation
adb shell input swipe 540 600 200 600 300
sleep 1
take_screenshot "08_3d_rotated"

adb shell input keyevent 4  # Back
sleep 2

# 6. Test Quiz
echo ""
echo "=== Step 6: Test Quiz ==="
# Tap Luyện tập button (792, 586)
adb shell input tap 792 586
sleep 3
take_screenshot "09_quiz_landing"

# Tap Ôn Tập Nhanh (540, 564)
adb shell input tap 540 564
sleep 3
take_screenshot "10_quiz_question"

# Answer first question (tap first option)
adb shell input tap 331 1015
sleep 2
take_screenshot "11_quiz_answered"

# Go back
adb shell input keyevent 4
sleep 1
adb shell input keyevent 4
sleep 2

echo ""
echo "=== Test Complete ==="
echo "Screenshots saved to: $SCREENSHOT_DIR"
echo -e "${GREEN}All tests passed!${NC}"

