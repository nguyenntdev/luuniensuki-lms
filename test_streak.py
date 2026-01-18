#!/usr/bin/env python3
"""
Test script for P0-HAB-03 Streak System.

This script tests the streak service and API endpoints.
"""

from datetime import datetime, timedelta, timezone
import sys
from pathlib import Path

# Add backend to path
REPO_ROOT = Path(__file__).resolve().parents[0]
sys.path.insert(0, str(REPO_ROOT))

from backend.models import User, StreakReward
from backend.services.streak import (
    calculate_current_streak,
    is_streak_maintained_today,
    is_streak_at_risk,
    award_milestone_rewards,
    get_next_milestone,
    STREAK_MILESTONES,
)


def test_streak_calculation():
    """Test streak calculation logic."""
    print("Testing streak calculation...")
    
    now = datetime.now(timezone.utc)
    
    # Test 1: New user (no last_active_at)
    user = User(
        email="test@example.com",
        password_hash="hash",
        display_name="Test User",
        current_streak=0,
        longest_streak=0,
        streak_freezes=0,
        last_active_at=None,
    )
    streak = calculate_current_streak(user, now)
    assert streak == 0, f"Expected 0 for new user, got {streak}"
    print("✓ New user has 0 streak")
    
    # Test 2: Active today
    user.last_active_at = now
    user.current_streak = 5
    streak = calculate_current_streak(user, now)
    assert streak == 5, f"Expected 5 for active today, got {streak}"
    assert is_streak_maintained_today(user, now), "Should be maintained today"
    assert not is_streak_at_risk(user, now), "Should not be at risk"
    print("✓ Active today maintains streak")
    
    # Test 3: Active yesterday (streak continues)
    user.last_active_at = now - timedelta(days=1)
    user.current_streak = 5
    streak = calculate_current_streak(user, now)
    assert streak == 5, f"Expected 5 for yesterday, got {streak}"
    assert not is_streak_maintained_today(user, now), "Should not be maintained"
    assert is_streak_at_risk(user, now), "Should be at risk"
    print("✓ Yesterday's activity puts streak at risk")
    
    # Test 4: Missed a day (streak breaks)
    user.last_active_at = now - timedelta(days=2)
    user.current_streak = 5
    streak = calculate_current_streak(user, now)
    assert streak == 0, f"Expected 0 for 2 days ago, got {streak}"
    print("✓ Missing a day breaks streak")


def test_milestone_logic():
    """Test milestone reward logic."""
    print("\nTesting milestone logic...")
    
    # Test next milestone calculation
    milestone = get_next_milestone(0)
    assert milestone["day"] == 7, "First milestone should be 7"
    assert milestone["days_remaining"] == 7, "Should need 7 days"
    print("✓ Next milestone for 0 streak is 7 days")
    
    milestone = get_next_milestone(7)
    assert milestone["day"] == 30, "Second milestone should be 30"
    assert milestone["days_remaining"] == 23, "Should need 23 more days"
    print("✓ Next milestone for 7 streak is 30 days")
    
    milestone = get_next_milestone(50)
    assert milestone["day"] == 100, "Third milestone should be 100"
    assert milestone["days_remaining"] == 50, "Should need 50 more days"
    print("✓ Next milestone for 50 streak is 100 days")
    
    milestone = get_next_milestone(100)
    assert milestone is None, "No milestone after 100"
    print("✓ No milestone after 100 days")


def test_milestone_definitions():
    """Test milestone definitions are correct."""
    print("\nTesting milestone definitions...")
    
    assert len(STREAK_MILESTONES) == 3, "Should have 3 milestones"
    
    # 7-day milestone
    assert STREAK_MILESTONES[7]["xp"] == 100, "7-day XP should be 100"
    assert STREAK_MILESTONES[7]["badge_slug"] == "streak-7", "7-day badge slug"
    assert STREAK_MILESTONES[7]["freeze"] == 0, "7-day freeze should be 0"
    print("✓ 7-day milestone: 100 XP, streak-7 badge, 0 freezes")
    
    # 30-day milestone
    assert STREAK_MILESTONES[30]["xp"] == 500, "30-day XP should be 500"
    assert STREAK_MILESTONES[30]["badge_slug"] == "streak-30-days", "30-day badge"
    assert STREAK_MILESTONES[30]["freeze"] == 0, "30-day freeze should be 0"
    print("✓ 30-day milestone: 500 XP, streak-30-days badge, 0 freezes")
    
    # 100-day milestone
    assert STREAK_MILESTONES[100]["xp"] == 2000, "100-day XP should be 2000"
    assert STREAK_MILESTONES[100]["badge_slug"] == "streak-100-days", "100-day badge"
    assert STREAK_MILESTONES[100]["freeze"] == 1, "100-day freeze should be 1"
    print("✓ 100-day milestone: 2000 XP, streak-100-days badge, 1 freeze")


def main():
    """Run all tests."""
    print("=" * 60)
    print("P0-HAB-03 Streak System Tests")
    print("=" * 60)
    
    try:
        test_streak_calculation()
        test_milestone_logic()
        test_milestone_definitions()
        
        print("\n" + "=" * 60)
        print("✅ All tests passed!")
        print("=" * 60)
        return 0
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        return 1
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())

