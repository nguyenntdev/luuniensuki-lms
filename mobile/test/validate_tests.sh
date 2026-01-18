#!/bin/bash
# Test validation script for quiz and spaced repetition tests

echo "================================"
echo "Test File Validation"
echo "================================"
echo ""

# Check if test files exist
echo "✓ Checking test files..."
if [ -f "test/features/quiz/domain/quiz_models_test.dart" ]; then
    echo "  ✅ quiz_models_test.dart exists"
else
    echo "  ❌ quiz_models_test.dart NOT FOUND"
    exit 1
fi

if [ -f "test/features/practice/domain/services/spaced_repetition_service_test.dart" ]; then
    echo "  ✅ spaced_repetition_service_test.dart exists"
else
    echo "  ❌ spaced_repetition_service_test.dart NOT FOUND"
    exit 1
fi

echo ""
echo "✓ Checking source files..."
if [ -f "lib/features/quiz/domain/quiz_models.dart" ]; then
    echo "  ✅ quiz_models.dart exists"
else
    echo "  ❌ quiz_models.dart NOT FOUND"
fi

if [ -f "lib/features/practice/domain/services/spaced_repetition_service.dart" ]; then
    echo "  ✅ spaced_repetition_service.dart exists"
else
    echo "  ❌ spaced_repetition_service.dart NOT FOUND"
fi

if [ -f "lib/features/practice/domain/models/review_item.dart" ]; then
    echo "  ✅ review_item.dart exists"
else
    echo "  ❌ review_item.dart NOT FOUND"
fi

echo ""
echo "✓ Test file statistics..."
quiz_tests=$(grep -c "test(" test/features/quiz/domain/quiz_models_test.dart)
sr_tests=$(grep -c "test(" test/features/practice/domain/services/spaced_repetition_service_test.dart)

echo "  📊 Quiz models tests: $quiz_tests"
echo "  📊 Spaced repetition tests: $sr_tests"
echo "  📊 Total tests: $((quiz_tests + sr_tests))"

echo ""
echo "✓ Test groups..."
quiz_groups=$(grep -c "group(" test/features/quiz/domain/quiz_models_test.dart)
sr_groups=$(grep -c "group(" test/features/practice/domain/services/spaced_repetition_service_test.dart)

echo "  📦 Quiz test groups: $quiz_groups"
echo "  📦 Spaced repetition groups: $sr_groups"

echo ""
echo "================================"
echo "Validation Complete!"
echo "================================"
echo ""
echo "To run the tests, use:"
echo "  flutter test test/features/quiz/domain/quiz_models_test.dart"
echo "  flutter test test/features/practice/domain/services/spaced_repetition_service_test.dart"
echo ""
echo "Or run all tests:"
echo "  flutter test"

