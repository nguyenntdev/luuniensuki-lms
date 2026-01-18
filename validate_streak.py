#!/usr/bin/env python3
"""
Validation script for P0-HAB-03 Streak System.

This script validates that all required files are present and correctly structured.
"""

import os
import sys
from pathlib import Path


def check_file_exists(filepath: str, description: str) -> bool:
    """Check if a file exists and print result."""
    exists = Path(filepath).exists()
    status = "✓" if exists else "✗"
    print(f"{status} {description}: {filepath}")
    return exists


def check_string_in_file(filepath: str, search_str: str, description: str) -> bool:
    """Check if a string exists in a file."""
    try:
        with open(filepath, 'r') as f:
            content = f.read()
            found = search_str in content
            status = "✓" if found else "✗"
            print(f"{status} {description}")
            return found
    except Exception as e:
        print(f"✗ Error reading {filepath}: {e}")
        return False


def main():
    """Run validation checks."""
    print("=" * 70)
    print("P0-HAB-03 Streak System Implementation Validation")
    print("=" * 70)
    
    all_pass = True
    
    # Check file existence
    print("\n📁 File Existence Checks:")
    all_pass &= check_file_exists(
        "backend/services/streak.py",
        "Streak service"
    )
    all_pass &= check_file_exists(
        "backend/models.py",
        "Models file"
    )
    all_pass &= check_file_exists(
        "backend/main.py",
        "Main API file"
    )
    all_pass &= check_file_exists(
        "migrations/versions/0014_streak_rewards.py",
        "Streak rewards migration"
    )
    all_pass &= check_file_exists(
        "P0_HAB_03_IMPLEMENTATION.md",
        "Implementation documentation"
    )
    
    # Check model definition
    print("\n🗄️  Model Checks:")
    all_pass &= check_string_in_file(
        "backend/models.py",
        "class StreakReward(Base):",
        "StreakReward model defined"
    )
    all_pass &= check_string_in_file(
        "backend/models.py",
        '"streak_rewards"',
        "StreakReward table name"
    )
    
    # Check service functions
    print("\n⚙️  Service Checks:")
    all_pass &= check_string_in_file(
        "backend/services/streak.py",
        "def calculate_current_streak",
        "calculate_current_streak function"
    )
    all_pass &= check_string_in_file(
        "backend/services/streak.py",
        "def is_streak_maintained_today",
        "is_streak_maintained_today function"
    )
    all_pass &= check_string_in_file(
        "backend/services/streak.py",
        "def award_milestone_rewards",
        "award_milestone_rewards function"
    )
    all_pass &= check_string_in_file(
        "backend/services/streak.py",
        "STREAK_MILESTONES",
        "STREAK_MILESTONES configuration"
    )
    
    # Check API endpoints
    print("\n🌐 API Endpoint Checks:")
    all_pass &= check_string_in_file(
        "backend/main.py",
        '"/api/v1/streak"',
        "GET /api/v1/streak endpoint"
    )
    all_pass &= check_string_in_file(
        "backend/main.py",
        '"/api/v1/streak/claim-daily"',
        "POST /api/v1/streak/claim-daily endpoint"
    )
    all_pass &= check_string_in_file(
        "backend/main.py",
        '"/api/v1/streak/use-freeze"',
        "POST /api/v1/streak/use-freeze endpoint"
    )
    
    # Check badge definitions
    print("\n🏆 Badge Checks:")
    all_pass &= check_string_in_file(
        "backend/seed.py",
        '"streak-7"',
        "7-day streak badge"
    )
    all_pass &= check_string_in_file(
        "backend/seed.py",
        '"streak-30-days"',
        "30-day streak badge"
    )
    all_pass &= check_string_in_file(
        "backend/seed.py",
        '"streak-100-days"',
        "100-day streak badge"
    )
    
    # Check imports
    print("\n📦 Import Checks:")
    all_pass &= check_string_in_file(
        "backend/main.py",
        "StreakReward",
        "StreakReward imported in main.py"
    )
    all_pass &= check_string_in_file(
        "backend/main.py",
        'BADGE_STREAK_30 = "streak-30-days"',
        "BADGE_STREAK_30 constant defined"
    )
    all_pass &= check_string_in_file(
        "backend/main.py",
        'BADGE_STREAK_100 = "streak-100-days"',
        "BADGE_STREAK_100 constant defined"
    )
    
    # Check migration
    print("\n🔄 Migration Checks:")
    all_pass &= check_string_in_file(
        "migrations/versions/0014_streak_rewards.py",
        'revision = "0014_streak_rewards"',
        "Migration revision ID"
    )
    all_pass &= check_string_in_file(
        "migrations/versions/0014_streak_rewards.py",
        '"streak_rewards"',
        "Creates streak_rewards table"
    )
    
    # Summary
    print("\n" + "=" * 70)
    if all_pass:
        print("✅ All validation checks passed!")
        print("\nNext steps:")
        print("1. Run database migration: docker compose exec api alembic upgrade head")
        print("2. Seed badges: docker compose exec api python -m backend.seed")
        print("3. Test endpoints with API client")
    else:
        print("❌ Some validation checks failed!")
        print("Please review the errors above and fix any issues.")
    print("=" * 70)
    
    return 0 if all_pass else 1


if __name__ == "__main__":
    sys.exit(main())

