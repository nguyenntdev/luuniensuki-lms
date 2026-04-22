"""
Seed script for weekly quests.

This script populates the weekly_quests table with default recurring weekly quests.
"""

from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker

from backend.config import settings
from backend.models import QuestCategory, WeeklyQuest

# Create database engine and session
engine = create_engine(str(settings.database_url))
SessionLocal = sessionmaker(bind=engine)


def seed_weekly_quests():
    """Seed default weekly quests."""
    db = SessionLocal()

    try:
        # Define default weekly quests
        weekly_quests_data = [
            # Exploration Quests
            {
                "slug": "weekly-explorer",
                "name": "Weekly Explorer",
                "description": "Discover 10 new motifs this week",
                "category": QuestCategory.exploration,
                "target_count": 10,
                "xp_reward": 150,
                "badge_slug": None,
                "is_recurring": True,
                "is_active": True,
            },
            {
                "slug": "weekly-collector",
                "name": "Weekly Collector",
                "description": "Explore 3 different urns this week",
                "category": QuestCategory.exploration,
                "target_count": 3,
                "xp_reward": 200,
                "badge_slug": None,
                "is_recurring": True,
                "is_active": True,
            },
            # Mastery Quests
            {
                "slug": "weekly-master",
                "name": "Weekly Master",
                "description": "Master 5 motifs this week",
                "category": QuestCategory.mastery,
                "target_count": 5,
                "xp_reward": 250,
                "badge_slug": None,
                "is_recurring": True,
                "is_active": True,
            },
            {
                "slug": "weekly-lesson-champion",
                "name": "Weekly Lesson Champion",
                "description": "Complete 20 lessons this week",
                "category": QuestCategory.mastery,
                "target_count": 20,
                "xp_reward": 300,
                "badge_slug": None,
                "is_recurring": True,
                "is_active": True,
            },
            # Quiz Champion Quests
            {
                "slug": "weekly-quiz-master",
                "name": "Weekly Quiz Master",
                "description": "Pass 10 quizzes this week",
                "category": QuestCategory.quiz_champion,
                "target_count": 10,
                "xp_reward": 200,
                "badge_slug": None,
                "is_recurring": True,
                "is_active": True,
            },
            {
                "slug": "weekly-perfect-score",
                "name": "Weekly Perfect Score",
                "description": "Get 100% on 3 quizzes this week",
                "category": QuestCategory.quiz_champion,
                "target_count": 3,
                "xp_reward": 350,
                "badge_slug": "quiz-perfectionist",
                "is_recurring": True,
                "is_active": True,
            },
            # Streak Master Quests
            {
                "slug": "weekly-dedication",
                "name": "Weekly Dedication",
                "description": "Maintain your streak for 7 days",
                "category": QuestCategory.streak_master,
                "target_count": 7,
                "xp_reward": 400,
                "badge_slug": "dedicated-learner",
                "is_recurring": True,
                "is_active": True,
            },
        ]

        # Check existing quests
        existing_slugs = set(
            db.execute(select(WeeklyQuest.slug)).scalars().all()
        )

        # Insert new quests
        new_count = 0
        for quest_data in weekly_quests_data:
            if quest_data["slug"] not in existing_slugs:
                quest = WeeklyQuest(
                    id=uuid4(),
                    **quest_data,
                    week_number=None,
                    year=None,
                    created_at=datetime.now(timezone.utc),
                )
                db.add(quest)
                new_count += 1
                print(f"✓ Added weekly quest: {quest_data['name']}")
            else:
                print(f"- Skipped existing quest: {quest_data['name']}")

        db.commit()
        print(f"\n✅ Seeded {new_count} new weekly quests")
        print(f"📊 Total weekly quests: {len(existing_slugs) + new_count}")

    except Exception as e:
        db.rollback()
        print(f"❌ Error seeding weekly quests: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    print("🌱 Seeding weekly quests...")
    seed_weekly_quests()

