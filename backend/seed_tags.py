"""
Seed script for content tags.

This script creates initial tags for the Luuniensuki LMS content tagging system.
Run this after applying the 0013_content_tagging migration.

Usage:
    python backend/seed_tags.py
"""

import uuid
from datetime import datetime, timezone
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.config import settings
from backend.models import Tag

# Initial tags to create
INITIAL_TAGS = [
    # Topic tags
    {
        "slug": "architecture",
        "name": "Kiến trúc (Architecture)",
        "tag_type": "topic",
        "description": "Architectural elements and structures on Vietnamese urns",
    },
    {
        "slug": "mythology",
        "name": "Thần thoại (Mythology)",
        "tag_type": "topic",
        "description": "Mythological creatures and stories",
    },
    {
        "slug": "nature",
        "name": "Thiên nhiên (Nature)",
        "tag_type": "topic",
        "description": "Natural elements: plants, animals, landscapes",
    },
    {
        "slug": "daily-life",
        "name": "Đời sống (Daily Life)",
        "tag_type": "topic",
        "description": "Scenes from everyday Vietnamese life",
    },
    {
        "slug": "symbolism",
        "name": "Biểu tượng (Symbolism)",
        "tag_type": "topic",
        "description": "Symbolic meanings and cultural significance",
    },
    {
        "slug": "religion",
        "name": "Tôn giáo (Religion)",
        "tag_type": "topic",
        "description": "Religious themes and Buddhist elements",
    },
    {
        "slug": "royal-court",
        "name": "Hoàng tộc (Royal Court)",
        "tag_type": "topic",
        "description": "Imperial and royal themes",
    },
    
    # Difficulty tags
    {
        "slug": "beginner",
        "name": "Cơ bản (Beginner)",
        "tag_type": "difficulty",
        "description": "Suitable for beginners and new learners",
    },
    {
        "slug": "intermediate",
        "name": "Trung cấp (Intermediate)",
        "tag_type": "difficulty",
        "description": "For learners with some background knowledge",
    },
    {
        "slug": "advanced",
        "name": "Nâng cao (Advanced)",
        "tag_type": "difficulty",
        "description": "Advanced topics requiring deeper understanding",
    },
    {
        "slug": "expert",
        "name": "Chuyên gia (Expert)",
        "tag_type": "difficulty",
        "description": "Expert-level content for researchers and specialists",
    },
    
    # Audience tags
    {
        "slug": "students",
        "name": "Học sinh (Students)",
        "tag_type": "audience",
        "description": "Content designed for students",
    },
    {
        "slug": "teachers",
        "name": "Giáo viên (Teachers)",
        "tag_type": "audience",
        "description": "Resources for educators",
    },
    {
        "slug": "researchers",
        "name": "Nhà nghiên cứu (Researchers)",
        "tag_type": "audience",
        "description": "Academic and research content",
    },
    {
        "slug": "general-public",
        "name": "Công chúng (General Public)",
        "tag_type": "audience",
        "description": "Accessible to general audiences",
    },
    
    # Era tags
    {
        "slug": "nguyen-dynasty",
        "name": "Nhà Nguyễn (Nguyen Dynasty)",
        "tag_type": "era",
        "description": "1802-1945, the last Vietnamese dynasty",
    },
    {
        "slug": "19th-century",
        "name": "Thế kỷ 19 (19th Century)",
        "tag_type": "era",
        "description": "Content from the 19th century period",
    },
    {
        "slug": "20th-century",
        "name": "Thế kỷ 20 (20th Century)",
        "tag_type": "era",
        "description": "Early 20th century content",
    },
    {
        "slug": "minh-mang",
        "name": "Minh Mạng",
        "tag_type": "era",
        "description": "Minh Mang Emperor period (1820-1841)",
    },
    {
        "slug": "tu-duc",
        "name": "Tự Đức",
        "tag_type": "era",
        "description": "Tu Duc Emperor period (1847-1883)",
    },
    
    # Style tags
    {
        "slug": "ornate",
        "name": "Hoa văn cầu kỳ (Ornate)",
        "tag_type": "style",
        "description": "Elaborate and decorative style",
    },
    {
        "slug": "minimalist",
        "name": "Tối giản (Minimalist)",
        "tag_type": "style",
        "description": "Simple and understated design",
    },
    {
        "slug": "traditional",
        "name": "Truyền thống (Traditional)",
        "tag_type": "style",
        "description": "Traditional Vietnamese artistic style",
    },
    {
        "slug": "court-style",
        "name": "Phong cách hoàng gia (Court Style)",
        "tag_type": "style",
        "description": "Imperial court artistic traditions",
    },
]


def seed_tags():
    """Create initial tags in the database."""
    # Create database connection
    engine = create_engine(settings.database_url)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    
    try:
        created_count = 0
        skipped_count = 0
        
        for tag_data in INITIAL_TAGS:
            # Check if tag already exists
            existing = db.query(Tag).filter(Tag.slug == tag_data["slug"]).first()
            
            if existing:
                print(f"⏭️  Skipping existing tag: {tag_data['slug']}")
                skipped_count += 1
                continue
            
            # Create new tag
            tag = Tag(
                id=uuid.uuid4(),
                slug=tag_data["slug"],
                name=tag_data["name"],
                tag_type=tag_data["tag_type"],
                description=tag_data.get("description"),
                is_active=True,
                created_at=datetime.now(timezone.utc),
            )
            db.add(tag)
            print(f"✅ Created tag: {tag_data['name']} ({tag_data['slug']})")
            created_count += 1
        
        db.commit()
        
        print(f"\n📊 Summary:")
        print(f"   Created: {created_count} tags")
        print(f"   Skipped: {skipped_count} tags")
        print(f"   Total: {len(INITIAL_TAGS)} tags")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    print("🏷️  Seeding content tags...\n")
    seed_tags()
    print("\n✅ Done!")

