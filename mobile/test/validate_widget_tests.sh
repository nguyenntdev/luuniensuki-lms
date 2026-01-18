#!/bin/bash
# Widget Test Validation Script

echo "========================================"
echo "Widget Tests Validation"
echo "========================================"
echo ""

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if test files exist
echo "✓ Checking test files..."
test_files=(
    "test/features/auth/presentation/widgets/login_form_test.dart"
    "test/features/lesson/presentation/widgets/progress_stepper_test.dart"
    "test/features/quiz/presentation/widgets/question_card_test.dart"
)

all_exist=true
for file in "${test_files[@]}"; do
    if [ -f "$file" ]; then
        echo -e "  ${GREEN}✅${NC} $file"
    else
        echo -e "  ${RED}❌${NC} $file NOT FOUND"
        all_exist=false
    fi
done

echo ""

# Check if widget files exist
echo "✓ Checking widget files..."
widget_files=(
    "lib/features/auth/presentation/widgets/login_form.dart"
    "lib/features/lesson/presentation/widgets/progress_stepper.dart"
    "lib/features/quiz/presentation/widgets/question_card.dart"
)

for file in "${widget_files[@]}"; do
    if [ -f "$file" ]; then
        echo -e "  ${GREEN}✅${NC} $file"
    else
        echo -e "  ${YELLOW}⚠${NC}  $file NOT FOUND"
    fi
done

echo ""

# Test file statistics
echo "✓ Test file statistics..."
for file in "${test_files[@]}"; do
    if [ -f "$file" ]; then
        test_count=$(grep -c "testWidgets(" "$file" 2>/dev/null || echo "0")
        group_count=$(grep -c "group(" "$file" 2>/dev/null || echo "0")
        echo "  📊 $(basename $file): $test_count tests, $group_count groups"
    fi
done

echo ""

# Calculate totals
total_tests=0
total_groups=0
for file in "${test_files[@]}"; do
    if [ -f "$file" ]; then
        count=$(grep -c "testWidgets(" "$file" 2>/dev/null || echo "0")
        total_tests=$((total_tests + count))
        
        gcount=$(grep -c "group(" "$file" 2>/dev/null || echo "0")
        total_groups=$((total_groups + gcount))
    fi
done

echo "  📊 Total widget tests: $total_tests"
echo "  📊 Total test groups: $total_groups"

echo ""
echo "========================================"
if [ "$all_exist" = true ]; then
    echo -e "${GREEN}✅ Validation Complete!${NC}"
else
    echo -e "${RED}❌ Some files are missing${NC}"
fi
echo "========================================"
echo ""

# Show run commands
echo "To run the widget tests:"
echo ""
echo "  # Run all tests"
echo "  flutter test"
echo ""
echo "  # Run specific widget tests"
echo "  flutter test test/features/auth/presentation/widgets/login_form_test.dart"
echo "  flutter test test/features/lesson/presentation/widgets/progress_stepper_test.dart"
echo "  flutter test test/features/quiz/presentation/widgets/question_card_test.dart"
echo ""
echo "  # Run with coverage"
echo "  flutter test --coverage"
echo ""

