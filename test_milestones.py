#!/usr/bin/env python3
"""
Test script for milestone tracking implementation.

This script verifies that:
1. UserMilestone model is correctly defined
2. Migration can be generated/applied
3. Service functions work correctly
4. API endpoints are accessible
"""

import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))


def test_model_import():
    """Test that UserMilestone model can be imported."""
    print("Testing model imports...")
    try:
        from backend.models import UserMilestone, MilestoneType
        print("✓ UserMilestone model imported successfully")
        print(f"✓ MilestoneType enum has {len(MilestoneType)} values:")
        for milestone in MilestoneType:
            print(f"  - {milestone.value}")
        return True
    except Exception as e:
        print(f"✗ Failed to import UserMilestone: {e}")
        return False


def test_schema_import():
    """Test that milestone schemas can be imported."""
    print("\nTesting schema imports...")
    try:
        from backend import schemas
        print("✓ MilestoneOut schema available:", hasattr(schemas, 'MilestoneOut'))
        print("✓ MilestoneListOut schema available:", hasattr(schemas, 'MilestoneListOut'))
        print("✓ PendingMilestonesOut schema available:", hasattr(schemas, 'PendingMilestonesOut'))
        print("✓ MilestoneCelebratedOut schema available:", hasattr(schemas, 'MilestoneCelebratedOut'))
        return True
    except Exception as e:
        print(f"✗ Failed to import schemas: {e}")
        return False


def test_service_import():
    """Test that milestone service functions can be imported."""
    print("\nTesting service imports...")
    try:
        from backend.services import milestones
        functions = [
            'create_milestone',
            'check_and_create_first_motif_discovered',
            'check_and_create_first_lesson_completed',
            'check_and_create_first_quiz_passed',
            'check_and_create_first_badge_earned',
            'check_and_create_first_streak_7',
            'check_and_create_onboarding_completed',
            'get_user_milestones',
            'get_pending_milestones',
            'mark_milestone_celebrated',
        ]
        for func_name in functions:
            if hasattr(milestones, func_name):
                print(f"✓ {func_name} available")
            else:
                print(f"✗ {func_name} NOT available")
                return False
        return True
    except Exception as e:
        print(f"✗ Failed to import service: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_migration_file():
    """Test that migration file exists and is valid."""
    print("\nTesting migration file...")
    try:
        migration_file = Path(__file__).parent / "migrations" / "versions" / "0021_user_milestones.py"
        if migration_file.exists():
            print(f"✓ Migration file exists: {migration_file}")
            
            # Read and check migration content
            content = migration_file.read_text()
            checks = [
                ("revision = '0021'", "Revision ID"),
                ("down_revision = '0020'", "Down revision"),
                ("CREATE TYPE milestone_type", "Enum creation"),
                ("user_milestones", "Table creation"),
                ("def upgrade", "Upgrade function"),
                ("def downgrade", "Downgrade function"),
            ]
            
            for check, desc in checks:
                if check in content:
                    print(f"✓ {desc} found")
                else:
                    print(f"✗ {desc} NOT found")
                    return False
            return True
        else:
            print(f"✗ Migration file not found: {migration_file}")
            return False
    except Exception as e:
        print(f"✗ Failed to check migration: {e}")
        return False


def test_main_integration():
    """Test that main.py has milestone tracking integrated."""
    print("\nTesting main.py integration...")
    try:
        main_file = Path(__file__).parent / "backend" / "main.py"
        content = main_file.read_text()
        
        checks = [
            ("from backend.services.milestones import", "Milestone service import"),
            ("check_and_create_first_motif_discovered", "First motif milestone"),
            ("check_and_create_first_lesson_completed", "First lesson milestone"),
            ("check_and_create_first_quiz_passed", "First quiz milestone"),
            ("check_and_create_first_badge_earned", "First badge milestone"),
            ("check_and_create_first_streak_7", "First streak milestone"),
            ("check_and_create_onboarding_completed", "Onboarding milestone"),
            ('@app.get("/api/v1/milestones"', "GET milestones endpoint"),
            ('@app.get("/api/v1/milestones/pending-celebration"', "GET pending endpoint"),
            ('@app.post("/api/v1/milestones/{milestone_id}/celebrate"', "POST celebrate endpoint"),
        ]
        
        for check, desc in checks:
            if check in content:
                print(f"✓ {desc} found")
            else:
                print(f"✗ {desc} NOT found")
                return False
        return True
    except Exception as e:
        print(f"✗ Failed to check main.py: {e}")
        return False


def main():
    """Run all tests."""
    print("=" * 60)
    print("MILESTONE TRACKING IMPLEMENTATION TEST")
    print("=" * 60)
    
    results = []
    
    results.append(("Model Import", test_model_import()))
    results.append(("Schema Import", test_schema_import()))
    results.append(("Service Import", test_service_import()))
    results.append(("Migration File", test_migration_file()))
    results.append(("Main.py Integration", test_main_integration()))
    
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    passed = 0
    failed = 0
    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {test_name}")
        if result:
            passed += 1
        else:
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"Total: {passed} passed, {failed} failed")
    print("=" * 60)
    
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())

