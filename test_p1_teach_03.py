#!/usr/bin/env python3
"""
Quick validation script for P1-TEACH-03 implementation.
Tests that all components are importable and have correct structure.
"""

import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

def test_models():
    """Test that StudentProgressSnapshot model is defined."""
    from backend.models import StudentProgressSnapshot
    print("✅ StudentProgressSnapshot model imported successfully")
    
    # Check that model has expected columns
    expected_columns = [
        'id', 'student_id', 'classroom_id', 'snapshot_date',
        'lessons_completed', 'quizzes_passed', 'average_quiz_score',
        'motifs_discovered', 'current_streak', 'xp_earned',
        'time_spent_minutes', 'created_at'
    ]
    
    model_columns = [c.name for c in StudentProgressSnapshot.__table__.columns]
    
    for col in expected_columns:
        if col in model_columns:
            print(f"  ✅ Column '{col}' present")
        else:
            print(f"  ❌ Column '{col}' MISSING")
            return False
    
    return True


def test_service():
    """Test that service functions are defined."""
    from backend.services import student_progress
    
    print("✅ student_progress service imported successfully")
    
    expected_functions = [
        'get_student_progress',
        'get_class_progress_summary',
        'get_class_leaderboard',
        'calculate_time_spent'
    ]
    
    for func_name in expected_functions:
        if hasattr(student_progress, func_name):
            print(f"  ✅ Function '{func_name}' present")
        else:
            print(f"  ❌ Function '{func_name}' MISSING")
            return False
    
    return True


def test_schemas():
    """Test that schemas are defined."""
    from backend import schemas
    
    print("✅ schemas module imported successfully")
    
    expected_schemas = [
        'LessonStatsOut',
        'QuizStatsOut',
        'EngagementStatsOut',
        'StudentProgressOut',
        'ClassProgressAveragesOut',
        'ClassProgressSummaryOut',
        'LeaderboardEntryOut',
        'LeaderboardOut'
    ]
    
    for schema_name in expected_schemas:
        if hasattr(schemas, schema_name):
            print(f"  ✅ Schema '{schema_name}' present")
        else:
            print(f"  ❌ Schema '{schema_name}' MISSING")
            return False
    
    return True


def test_migration():
    """Test that migration file exists."""
    migration_file = Path(__file__).parent / "migrations" / "versions" / "0030_student_progress_snapshots.py"
    
    if migration_file.exists():
        print("✅ Migration file exists")
        
        # Check content
        content = migration_file.read_text()
        if 'student_progress_snapshots' in content:
            print("  ✅ Migration creates student_progress_snapshots table")
        else:
            print("  ❌ Migration doesn't create expected table")
            return False
            
        return True
    else:
        print("❌ Migration file MISSING")
        return False


def main():
    """Run all tests."""
    print("=" * 60)
    print("P1-TEACH-03 Implementation Validation")
    print("=" * 60)
    print()
    
    tests = [
        ("Models", test_models),
        ("Service", test_service),
        ("Schemas", test_schemas),
        ("Migration", test_migration),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n--- Testing {test_name} ---")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ Error in {test_name}: {e}")
            results.append((test_name, False))
    
    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    all_passed = all(result for _, result in results)
    
    if all_passed:
        print("\n🎉 All tests passed! Implementation is ready.")
        return 0
    else:
        print("\n⚠️  Some tests failed. Please review the output above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())

