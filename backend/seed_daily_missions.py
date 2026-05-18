#!/usr/bin/env python3
"""Seed initial daily mission templates.

This script creates the default daily missions that will be assigned to users each day.
Run this after the 0012_daily_missions migration has been applied.

Usage:
    python3 seed_daily_missions.py
"""

from __future__ import annotations

import os
import sys
import uuid
from datetime import datetime, timezone

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker

# Add backend to path so we can import models
sys.path.insert(0, os.path.dirname(__file__))

from models import Base, DailyMission, MissionType


def seed_daily_missions(db: Session) -> None:
    """Create default daily mission templates."""
    
    # Check if missions already exist
    existing = db.execute(select(DailyMission)).scalars().all()
    if existing:
        print(f"Found {len(existing)} existing missions. Skipping seed.")
        for mission in existing:
            print(f"  - {mission.slug}: {mission.name}")
        return

    # Default mission templates
    missions = [
        {
            "slug": "complete-1-lesson",
            "name": "Học 1 Bài",
            "description": "Hoàn thành 1 bài học hôm nay",
            "mission_type": MissionType.lesson,
            "target_count": 1,
            "xp_reward": 50,
        },
        {
            "slug": "pass-1-quiz",
            "name": "Đạt 1 Bài Kiểm Tra",
            "description": "Vượt qua 1 bài kiểm tra hôm nay",
            "mission_type": MissionType.quiz,
            "target_count": 1,
            "xp_reward": 75,
        },
        {
            "slug": "discover-2-motifs",
            "name": "Khám Phá 2 Họa Tiết",
            "description": "Khám phá 2 họa tiết mới hôm nay",
            "mission_type": MissionType.discovery,
            "target_count": 2,
            "xp_reward": 100,
        },
        {
            "slug": "maintain-streak",
            "name": "Duy Trì Chuỗi",
            "description": "Duy trì chuỗi học tập liên tục",
            "mission_type": MissionType.streak,
            "target_count": 1,
            "xp_reward": 25,
        },
    ]

    created = []
    for mission_data in missions:
        mission = DailyMission(
            id=uuid.uuid4(),
            slug=mission_data["slug"],
            name=mission_data["name"],
            description=mission_data["description"],
            mission_type=mission_data["mission_type"],
            target_count=mission_data["target_count"],
            xp_reward=mission_data["xp_reward"],
            is_active=True,
            created_at=datetime.now(timezone.utc),
        )
        db.add(mission)
        created.append(mission)

    db.commit()

    print(f"✅ Created {len(created)} daily mission templates:")
    for mission in created:
        print(f"  - {mission.slug}: {mission.name} ({mission.xp_reward} XP)")


def main() -> None:
    """Main entry point."""
    database_url = os.getenv(
        "DATABASE_URL",
        "postgresql+psycopg://postgres:postgres@localhost:5432/luuniensuki",
    )

    print(f"Connecting to database: {database_url.split('@')[-1]}")
    engine = create_engine(database_url)
    SessionLocal = sessionmaker(bind=engine)

    with SessionLocal() as db:
        seed_daily_missions(db)


if __name__ == "__main__":
    main()

