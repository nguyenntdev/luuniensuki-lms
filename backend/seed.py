from __future__ import annotations

import argparse
import difflib
import json
import os
import re
import sys
import unicodedata
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, TypeVar
from urllib.parse import quote

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker

if __package__ in (None, ""):
    REPO_ROOT = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(REPO_ROOT))

    from backend.models import (
        Badge,
        BadgeCategory,
        Base,
        ClassMember,
        Classroom,
        LessonContent,
        Motif,
        MotifCategory,
        MotifRarity,
        Quest,
        QuestionType,
        QuestObjective,
        QuestReward,
        QuestStep,
        QuizQuestion,
        Urn,
        UrnExam,
        User,
        UserRole,
    )
    from backend.security import hash_password
else:
    from .models import (
        Badge,
        BadgeCategory,
        Base,
        ClassMember,
        Classroom,
        LessonContent,
        Motif,
        MotifCategory,
        MotifRarity,
        Quest,
        QuestionType,
        QuestObjective,
        QuestReward,
        QuestStep,
        QuizQuestion,
        Urn,
        UrnExam,
        User,
        UserRole,
    )
    from .security import hash_password


URN_ORDER: dict[str, int] = {
    "cao-dinh": 1,
    "nhan-dinh": 2,
    "chuong-dinh": 3,
    "anh-dinh": 4,
    "nghi-dinh": 5,
    "thuan-dinh": 6,
    "tuyen-dinh": 7,
    "du-dinh": 8,
    "huyen-dinh": 9,
}

# Remote GLB filenames currently available on store.histolab.icu (proxied via Nginx under /assets/models/).
URN_MODEL_FILENAMES: dict[str, str] = {
    "cao-dinh": "CAO-DINH-v1.glb",
    "chuong-dinh": "CHUONG-DINH-v1.glb",
    "huyen-dinh": "HUYEN-DINH-v1.glb",
    "nghi-dinh": "NGHI-DINH-v1.glb",
    "thuan-dinh": "THUAN-DINH-v1.glb",
    "tuyen-dinh": "TUYEN-DINH-v1.glb",
    # Models not yet available on store.histolab.icu:
    # "nhan-dinh": "NHAN-DINH-v1.glb",
    # "anh-dinh": "ANH-DINH-v1.glb",
    # "du-dinh": "DU-DINH-v1.glb",
}

# Manual fallbacks for known naming mismatches between seed data and image filenames.
# Keyed by (urn_slug, motif_slug_from_seed) -> motif_slug_from_images
IMAGE_SLUG_ALIASES: dict[tuple[str, str], str] = {
    ("chuong-dinh", "ngu-tinh"): "moc-tinh-hoa-tinh-tho-tinh-kim-tinh-thuy-tinh",
    # ban-duc-noi/NHAN DINH contains "HUƠU GIANG.jpg" but seed uses "Hương Giang".
    ("nhan-dinh", "huong-giang"): "huou-giang",
}

COMPOSITE_NAME_SPLIT_RE = re.compile(r"\s*(?:,|;|\s+[\-–—]\s+)\s*")


DEFAULT_BADGES: list[dict[str, Any]] = [
    {
        "slug": "first-discovery",
        "name": "Khai Môn",
        "name_en": "First Discovery",
        "description": "Mở khóa họa tiết đầu tiên.",
        "icon_url": "🎯",
        "category": BadgeCategory.achievement,
        "xp_bonus": 100,
        "unlock_criteria": {"type": "first_discovery"},
        "is_secret": False,
    },
    {
        "slug": "first-mastered",
        "name": "Bậc Thầy Đầu Tiên",
        "name_en": "First Mastery",
        "description": "Hoàn thành (mastered) họa tiết đầu tiên.",
        "icon_url": "🏆",
        "category": BadgeCategory.achievement,
        "xp_bonus": 200,
        "unlock_criteria": {"type": "first_mastered"},
        "is_secret": False,
    },
    {
        "slug": "streak-7",
        "name": "Thất Nhật Liên Tiếp",
        "name_en": "7-Day Streak",
        "description": "Duy trì streak 7 ngày liên tiếp.",
        "icon_url": "🔥",
        "category": BadgeCategory.achievement,
        "xp_bonus": 150,
        "unlock_criteria": {"type": "streak", "days": 7},
        "is_secret": False,
    },
    {
        "slug": "collector-10",
        "name": "Nhà Sưu Tầm Tập Sự",
        "name_en": "Collector (10)",
        "description": "Thu thập 10 họa tiết.",
        "icon_url": "📦",
        "category": BadgeCategory.collection,
        "xp_bonus": 150,
        "unlock_criteria": {"type": "motif_discovered_count", "count": 10},
        "is_secret": False,
    },
    {
        "slug": "collector-50",
        "name": "Nhà Sưu Tầm Lão Luyện",
        "name_en": "Collector (50)",
        "description": "Thu thập 50 họa tiết.",
        "icon_url": "💎",
        "category": BadgeCategory.collection,
        "xp_bonus": 500,
        "unlock_criteria": {"type": "motif_discovered_count", "count": 50},
        "is_secret": False,
    },
    {
        "slug": "explorer-all-urns",
        "name": "Chinh Phục Cửu Đỉnh",
        "name_en": "Explore All Urns",
        "description": "Khám phá tất cả 9 đỉnh.",
        "icon_url": "🗺️",
        "category": BadgeCategory.quest,
        "xp_bonus": 300,
        "unlock_criteria": {"type": "urns_explored_count", "count": 9},
        "is_secret": False,
    },
    {
        "slug": "quiz-master",
        "name": "Bậc Thầy Quiz",
        "name_en": "Quiz Master",
        "description": "Hoàn thành 10 quiz với điểm tối đa.",
        "icon_url": "🎓",
        "category": BadgeCategory.achievement,
        "xp_bonus": 400,
        "unlock_criteria": {"type": "quiz_max_score_count", "count": 10},
        "is_secret": False,
    },
    {
        "slug": "speed-demon",
        "name": "Thần Tốc",
        "name_en": "Speed Demon",
        "description": "Hoàn thành quiz trong 30 giây.",
        "icon_url": "⚡",
        "category": BadgeCategory.achievement,
        "xp_bonus": 200,
        "unlock_criteria": {"type": "quiz_complete_under_seconds", "seconds": 30},
        "is_secret": False,
    },
    {
        "slug": "perfect-score",
        "name": "Điểm Tuyệt Đối",
        "name_en": "Perfect Score",
        "description": "Đạt 100% trong quiz.",
        "icon_url": "💯",
        "category": BadgeCategory.achievement,
        "xp_bonus": 150,
        "unlock_criteria": {"type": "quiz_percentage", "percentage": 100},
        "is_secret": False,
    },
    {
        "slug": "early-bird",
        "name": "Chim Sớm",
        "name_en": "Early Bird",
        "description": "Đăng nhập trước 6 giờ sáng.",
        "icon_url": "🌅",
        "category": BadgeCategory.special,
        "xp_bonus": 100,
        "unlock_criteria": {"type": "login_before_hour", "hour": 6},
        "is_secret": False,
    },
]

DEFAULT_QUESTS: list[dict[str, Any]] = [
    {
        "slug": "dat-mua-mang",
        "name": "Đất & Mùa Màng",
        "description": "Khám phá họa tiết về nông nghiệp và mùa vụ.",
        "category": "nong_nghiep",
        "display_order": 1,
        "prerequisite_slug": None,
        "steps": [
            {
                "title": "Dấu ấn nông nghiệp",
                "description": "Mở khóa các họa tiết nông nghiệp cơ bản.",
                "objectives": [
                    {
                        "objective_type": "discover_category",
                        "target_value": 3,
                        "params": {"category": "nong_nghiep"},
                    },
                    {
                        "objective_type": "discover_category",
                        "target_value": 3,
                        "params": {"category": "thao_moc"},
                    },
                ],
            },
            {
                "title": "Kiểm tra mùa màng",
                "description": "Vượt qua các câu hỏi liên quan nông nghiệp.",
                "objectives": [
                    {
                        "objective_type": "quiz_pass_count",
                        "target_value": 2,
                        "params": {"category": "nong_nghiep"},
                    }
                ],
            },
        ],
        "rewards": [{"reward_type": "xp", "amount": 200}],
    },
    {
        "slug": "linh-thu",
        "name": "Linh Thú & Động Vật",
        "description": "Thu thập dấu tích của linh thú và động vật trên các đỉnh.",
        "category": "linh_thu",
        "display_order": 2,
        "prerequisite_slug": "dat-mua-mang",
        "steps": [
            {
                "title": "Tìm linh thú",
                "objectives": [
                    {
                        "objective_type": "discover_category",
                        "target_value": 3,
                        "params": {"category": "linh_thu"},
                    },
                    {
                        "objective_type": "discover_category",
                        "target_value": 3,
                        "params": {"category": "dong_vat"},
                    },
                ],
            },
            {
                "title": "Thử thách linh thú",
                "objectives": [
                    {
                        "objective_type": "quiz_pass_count",
                        "target_value": 2,
                        "params": {"category": "dong_vat"},
                    }
                ],
            },
        ],
        "rewards": [{"reward_type": "xp", "amount": 250}],
    },
    {
        "slug": "son-ha-xa-tac",
        "name": "Sơn Hà Xã Tắc",
        "description": "Khám phá các họa tiết về địa lý, núi sông.",
        "category": "dia_ly",
        "display_order": 3,
        "prerequisite_slug": "dat-mua-mang",
        "steps": [
            {
                "title": "Địa lý Việt Nam",
                "objectives": [
                    {
                        "objective_type": "discover_category",
                        "target_value": 4,
                        "params": {"category": "dia_ly"},
                    }
                ],
            },
            {
                "title": "Kiểm tra địa danh",
                "objectives": [
                    {
                        "objective_type": "quiz_pass_count",
                        "target_value": 1,
                        "params": {"category": "dia_ly"},
                    }
                ],
            },
        ],
        "rewards": [{"reward_type": "xp", "amount": 200}],
    },
    {
        "slug": "cuu-dinh-thu-thach",
        "name": "Thử Thách Cửu Đỉnh",
        "description": "Vượt qua kỳ kiểm tra Cửu Đỉnh để nhận chứng nhận.",
        "category": "tong-hop",
        "display_order": 4,
        "prerequisite_slug": "son-ha-xa-tac",
        "steps": [
            {
                "title": "Thi chứng nhận",
                "objectives": [
                    {
                        "objective_type": "urn_exam_pass",
                        "target_value": 1,
                        "params": {},
                    }
                ],
            }
        ],
        "rewards": [{"reward_type": "xp", "amount": 300}],
    },
]

DEMO_USER_PASSWORD_ENV = "DEMO_USER_PASSWORD"
DEFAULT_DEMO_PASSWORD = "Demo12345"

DEMO_USERS: list[dict[str, Any]] = [
    {
        "email": "teacher@luuniensuki.local",
        "display_name": "Teacher Demo",
        "role": UserRole.teacher,
    },
    {
        "email": "admin@luuniensuki.local",
        "display_name": "Admin Demo",
        "role": UserRole.admin,
    },
    {
        "email": "superadmin@luuniensuki.local",
        "display_name": "Super Admin",
        "role": UserRole.super_admin,
    },
    {
        "email": "learner@luuniensuki.local",
        "display_name": "Learner Demo",
        "role": UserRole.learner,
    },
]

EnumT = TypeVar("EnumT", bound=Enum)


def slugify(value: str) -> str:
    value = value.strip().lower()
    value = unicodedata.normalize("NFKD", value)
    value = "".join(ch for ch in value if not unicodedata.combining(ch))
    value = value.replace("đ", "d")
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return value.strip("-")


def coerce_difficulty(raw: Any, default: int = 1) -> tuple[int, bool]:
    if raw is None or isinstance(raw, bool):
        return default, False
    try:
        value = int(raw)
    except (TypeError, ValueError):
        return default, False

    if 1 <= value <= 3:
        return value, True

    return min(3, max(1, value)), False


def coerce_enum(enum_cls: type[EnumT], raw: Any, default: EnumT) -> tuple[EnumT, bool]:
    if isinstance(raw, enum_cls):
        return raw, True

    if raw is None:
        return default, False

    value = raw.strip() if isinstance(raw, str) else str(raw).strip()
    if not value:
        return default, False

    normalized = value.lower().replace("-", "_").replace(" ", "_")
    normalized = re.sub(r"_+", "_", normalized).strip("_")
    slug = slugify(value).replace("-", "_")

    candidates = [value, normalized, slug]
    for candidate in candidates:
        if not candidate:
            continue
        try:
            return enum_cls(candidate), True
        except ValueError:
            pass
        try:
            return enum_cls[candidate], True
        except KeyError:
            pass

    return default, False


def extract_json_array_from_markdown(markdown: str) -> list[dict[str, Any]]:
    match = re.search(
        r"```json\s*(\[.*?\])\s*```", markdown, flags=re.IGNORECASE | re.DOTALL
    )
    if not match:
        raise ValueError("No ```json ... ``` array block found in seed markdown file.")
    data = json.loads(match.group(1))
    if not isinstance(data, list):
        raise ValueError("Expected top-level JSON array in seed file.")
    if not all(isinstance(item, dict) for item in data):
        raise ValueError("Expected JSON array of objects in seed file.")
    return data


def process_file(file_path: Path) -> list[dict[str, Any]]:
    suffix = file_path.suffix.lower()
    if suffix == ".json":
        data = json.loads(file_path.read_text(encoding="utf-8"))
        if not isinstance(data, list):
            raise ValueError(f"Expected JSON array in {file_path}")
        if not all(isinstance(item, dict) for item in data):
            raise ValueError(f"Expected JSON array of objects in {file_path}")
        return data

    if suffix in {".md", ".markdown"}:
        markdown = file_path.read_text(encoding="utf-8")
        return extract_json_array_from_markdown(markdown)

    raise ValueError(f"Unsupported seed file type: {file_path}")


def parse_display_order(raw_id: Any) -> int | None:
    if not isinstance(raw_id, str) or not raw_id:
        return None
    match = re.search(r"_(\d+)$", raw_id)
    if not match:
        return None
    try:
        return int(match.group(1))
    except ValueError:
        return None


def slug_variants(value: str) -> list[str]:
    variants: list[str] = [slugify(value)]
    parts = [p for p in COMPOSITE_NAME_SPLIT_RE.split(value) if p.strip()]
    if len(parts) > 1:
        part_slugs = [slugify(part) for part in parts]
        variants.append("-".join(sorted(part_slugs)))
    return list(dict.fromkeys(variants))


def resolve_thumbnail_url(
    image_map: dict[tuple[str, str], str], *, urn_slug: str, name_vi: str
) -> str | None:
    target_slug = slugify(name_vi)

    alias = IMAGE_SLUG_ALIASES.get((urn_slug, target_slug))
    if alias:
        url = image_map.get((urn_slug, alias))
        if url:
            return url

    for candidate_slug in slug_variants(name_vi):
        url = image_map.get((urn_slug, candidate_slug))
        if url:
            return url

    candidates = [motif_slug for (u, motif_slug) in image_map.keys() if u == urn_slug]
    matches = difflib.get_close_matches(target_slug, candidates, n=2, cutoff=0.85)
    if not matches:
        return None

    if len(matches) == 1:
        return image_map.get((urn_slug, matches[0]))

    ratio_best = difflib.SequenceMatcher(None, target_slug, matches[0]).ratio()
    ratio_second = difflib.SequenceMatcher(None, target_slug, matches[1]).ratio()
    if ratio_best - ratio_second >= 0.05:
        return image_map.get((urn_slug, matches[0]))

    return None


@dataclass(frozen=True)
class SeedConfig:
    database_url: str
    seed_path: Path
    model_base_url: str


def upsert_urn(
    session: Session,
    *,
    name: str,
    model_base_url: str,
    thumbnail_url: str | None = None,
) -> Urn:
    slug = slugify(name)
    display_order = URN_ORDER.get(slug, 0)
    is_demo = slug == "cao-dinh"
    model_filename = URN_MODEL_FILENAMES.get(slug)
    model_url = (
        f"{model_base_url.rstrip('/')}/{model_filename}" if model_filename else ""
    )

    urn = session.execute(select(Urn).where(Urn.slug == slug)).scalar_one_or_none()
    if urn is None:
        urn = Urn(
            slug=slug,
            name=name,
            model_url=model_url,
            thumbnail_url=thumbnail_url,
            display_order=display_order,
            is_demo=is_demo,
        )
        session.add(urn)
        session.flush()
        return urn

    urn.name = name
    urn.model_url = model_url
    if thumbnail_url:
        urn.thumbnail_url = thumbnail_url
    urn.display_order = display_order or urn.display_order
    urn.is_demo = is_demo
    session.flush()
    return urn


def upsert_badge(
    session: Session,
    *,
    slug: str,
    name: str,
    name_en: str | None,
    description: str | None,
    icon_url: str,
    category: BadgeCategory,
    xp_bonus: int,
    unlock_criteria: Any,
    is_secret: bool,
) -> Badge:
    badge = session.execute(
        select(Badge).where(Badge.slug == slug)
    ).scalar_one_or_none()
    if badge is None:
        badge = Badge(
            slug=slug,
            name=name,
            name_en=name_en,
            description=description,
            icon_url=icon_url,
            category=category,
            xp_bonus=xp_bonus,
            unlock_criteria=unlock_criteria,
            is_secret=is_secret,
            is_active=True,
        )
        session.add(badge)
        session.flush()
        return badge

    badge.name = name
    badge.name_en = name_en
    badge.description = description
    badge.icon_url = icon_url
    badge.category = category
    badge.xp_bonus = xp_bonus
    badge.unlock_criteria = unlock_criteria
    badge.is_secret = is_secret
    badge.is_active = True
    session.flush()
    return badge


def seed_quests(session: Session) -> None:
    quest_by_slug: dict[str, Quest] = {}
    for quest_def in DEFAULT_QUESTS:
        slug = str(quest_def["slug"])
        quest = session.execute(
            select(Quest).where(Quest.slug == slug)
        ).scalar_one_or_none()
        if quest is None:
            quest = Quest(
                slug=slug,
                name=str(quest_def["name"]),
                description=quest_def.get("description"),
                category=quest_def.get("category"),
                display_order=int(quest_def.get("display_order") or 0),
                is_active=True,
            )
            session.add(quest)
        else:
            quest.name = str(quest_def["name"])
            quest.description = quest_def.get("description")
            quest.category = quest_def.get("category")
            quest.display_order = int(
                quest_def.get("display_order") or quest.display_order or 0
            )
            quest.is_active = True
        session.flush()
        quest_by_slug[slug] = quest

    for quest_def in DEFAULT_QUESTS:
        slug = str(quest_def["slug"])
        quest = quest_by_slug.get(slug)
        if quest is None:
            continue
        prereq_slug = quest_def.get("prerequisite_slug")
        quest.prerequisite_id = (
            quest_by_slug.get(prereq_slug).id if prereq_slug else None
        )
        session.flush()

        existing_steps = (
            session.execute(select(QuestStep.id).where(QuestStep.quest_id == quest.id))
            .scalars()
            .all()
        )
        if existing_steps:
            session.execute(
                QuestObjective.__table__.delete().where(
                    QuestObjective.quest_step_id.in_(existing_steps)
                )
            )
            session.execute(
                QuestStep.__table__.delete().where(QuestStep.id.in_(existing_steps))
            )
        session.execute(
            QuestReward.__table__.delete().where(QuestReward.quest_id == quest.id)
        )

        steps = quest_def.get("steps") or []
        for step_index, step_def in enumerate(steps, start=1):
            step = QuestStep(
                quest_id=quest.id,
                title=str(step_def.get("title") or f"Bước {step_index}"),
                description=step_def.get("description"),
                display_order=int(step_def.get("display_order") or step_index),
            )
            session.add(step)
            session.flush()

            objectives = step_def.get("objectives") or []
            for obj_index, obj_def in enumerate(objectives, start=1):
                session.add(
                    QuestObjective(
                        quest_step_id=step.id,
                        objective_type=str(obj_def.get("objective_type") or ""),
                        target_value=int(obj_def.get("target_value") or 1),
                        params=obj_def.get("params")
                        if isinstance(obj_def.get("params"), dict)
                        else None,
                        display_order=int(obj_def.get("display_order") or obj_index),
                    )
                )

        for reward_def in quest_def.get("rewards") or []:
            session.add(
                QuestReward(
                    quest_id=quest.id,
                    reward_type=str(reward_def.get("reward_type") or "xp"),
                    amount=reward_def.get("amount"),
                    badge_slug=reward_def.get("badge_slug"),
                    metadata_payload=reward_def.get("metadata")
                    if isinstance(reward_def.get("metadata"), dict)
                    else None,
                )
            )


def seed_demo_users(session: Session) -> None:
    demo_password = os.getenv(DEMO_USER_PASSWORD_ENV, DEFAULT_DEMO_PASSWORD)
    password_hash = hash_password(demo_password)

    for spec in DEMO_USERS:
        email = str(spec["email"])
        user = session.execute(
            select(User).where(User.email == email)
        ).scalar_one_or_none()
        if user is None:
            user = User(
                email=email,
                password_hash=password_hash,
                display_name=str(spec["display_name"]),
                role=spec["role"],
            )
            session.add(user)
        else:
            user.display_name = str(spec["display_name"])
            user.role = spec["role"]
        session.flush()

    teacher = session.execute(
        select(User).where(User.email == "teacher@luuniensuki.local")
    ).scalar_one_or_none()
    learner = session.execute(
        select(User).where(User.email == "learner@luuniensuki.local")
    ).scalar_one_or_none()
    if teacher and learner:
        classroom = session.execute(
            select(Classroom).where(Classroom.name == "Lớp Demo")
        ).scalar_one_or_none()
        if classroom is None:
            classroom = Classroom(
                name="Lớp Demo",
                description="Lớp học mẫu cho giáo viên.",
                teacher_id=teacher.id,
            )
            session.add(classroom)
            session.flush()
        existing_member = session.execute(
            select(ClassMember).where(
                ClassMember.class_id == classroom.id,
                ClassMember.user_id == learner.id,
            )
        ).scalar_one_or_none()
        if existing_member is None:
            session.add(
                ClassMember(
                    class_id=classroom.id,
                    user_id=learner.id,
                    role="learner",
                )
            )


def scan_images(image_path: Path) -> dict[tuple[str, str], str]:
    """
    Scans the image directory and returns a mapping of (urn_slug, motif_slug) -> image_url.
    Assumes structure: image_path / Urn_Name / Motif_Name.jpg
    """
    if not image_path.exists():
        print(f"Warning: Image path {image_path} does not exist.")
        return {}

    image_extensions = {".jpg", ".jpeg", ".png", ".webp", ".gif"}
    base_url = f"/assets/{image_path.name}".rstrip("/")

    candidates: dict[tuple[str, str], list[str]] = {}
    files = sorted(
        p
        for p in image_path.rglob("*")
        if p.is_file() and p.suffix.lower() in image_extensions
    )
    print(f"Scanning images in {image_path}... ({len(files)} files)")

    for img_file in files:
        rel = img_file.relative_to(image_path)
        if len(rel.parts) < 2:
            continue

        urn_dir_name = rel.parts[0]
        urn_slug = slugify(urn_dir_name)
        motif_slug = slugify(img_file.stem)
        key = (urn_slug, motif_slug)
        image_url = f"{base_url}/{quote(rel.as_posix(), safe='/')}"
        candidates.setdefault(key, []).append(image_url)

    image_map: dict[tuple[str, str], str] = {}
    duplicates = 0
    for key, urls in candidates.items():
        image_map[key] = urls[0]
        if len(urls) > 1:
            duplicates += len(urls) - 1
            print(
                f"Warning: Multiple images match {key}: using {urls[0]} (ignored {len(urls) - 1})"
            )

    print(f"Found {len(image_map)} image mappings ({duplicates} duplicates).")
    return image_map


def _collect_coordinate_files(coords_path: Path | None) -> list[Path]:
    if coords_path is None:
        return []
    if coords_path.is_file():
        return [coords_path]
    if coords_path.is_dir():
        return sorted(coords_path.glob("motif-coordinates-*.json"))
    return []


def seed_coordinates(session: Session, coords_path: Path | None) -> None:
    files = _collect_coordinate_files(coords_path)
    if not files:
        return

    total_updated = 0
    total_skipped = 0
    for file_path in files:
        try:
            raw = json.loads(file_path.read_text(encoding="utf-8"))
        except Exception as exc:
            print(f"Warning: Failed to read coordinates from {file_path}: {exc}")
            continue

        if not isinstance(raw, list):
            print(f"Warning: Coordinates file {file_path} must be a list; skipping.")
            continue

        for item in raw:
            if not isinstance(item, dict):
                total_skipped += 1
                continue

            urn_slug = str(item.get("urn_slug") or "").strip()
            motif_name = str(item.get("motif_name") or "").strip()
            if not urn_slug or not motif_name:
                total_skipped += 1
                continue

            urn = session.execute(
                select(Urn).where(Urn.slug == urn_slug)
            ).scalar_one_or_none()
            if urn is None:
                total_skipped += 1
                continue

            target_slug = slugify(motif_name)
            motifs = (
                session.execute(select(Motif).where(Motif.urn_id == urn.id))
                .scalars()
                .all()
            )
            motif = next((m for m in motifs if slugify(m.name) == target_slug), None)
            if motif is None:
                total_skipped += 1
                continue

            for field in ("pos_x", "pos_y", "pos_z", "bounding_radius"):
                if field not in item:
                    continue
                value = item.get(field)
                if value is None:
                    continue
                try:
                    setattr(motif, field, float(value))
                except (TypeError, ValueError):
                    total_skipped += 1
                    break
            else:
                total_updated += 1

    if total_updated or total_skipped:
        print(f"Applied {total_updated} coordinate updates ({total_skipped} skipped).")


def upsert_motif(
    session: Session,
    *,
    urn: Urn,
    mesh_name: str,
    name_vi: str,
    name_en: str | None,
    category: MotifCategory,
    rarity: MotifRarity,
    display_order: int | None,
    thumbnail_url: str | None = None,
) -> Motif:
    motif = session.execute(
        select(Motif).where(Motif.mesh_name == mesh_name)
    ).scalar_one_or_none()
    if motif is None:
        motif = Motif(
            urn_id=urn.id,
            mesh_name=mesh_name,
            name=name_vi,
            name_en=name_en,
            category=category,
            rarity=rarity,
            pos_x=0.0,
            pos_y=0.0,
            pos_z=0.0,
            bounding_radius=1.0,
            is_demo=urn.is_demo,
            display_order=display_order,
            thumbnail_url=thumbnail_url,
        )
        session.add(motif)
        session.flush()
        return motif

    motif.urn_id = urn.id
    motif.name = name_vi
    motif.name_en = name_en
    motif.category = category
    motif.rarity = rarity
    motif.is_demo = urn.is_demo
    motif.display_order = display_order
    # Always update thumbnail_url if a new value is provided (or clear if None)
    if thumbnail_url is not None:
        motif.thumbnail_url = thumbnail_url
    session.flush()
    return motif


def upsert_lesson(
    session: Session,
    *,
    motif: Motif,
    intro_text: str | None,
    description: str,
    historical_context: str | None = None,
    symbolism: str | None = None,
    fun_fact: str | None = None,
    is_ai_generated: bool = False,
) -> LessonContent:
    lesson = session.execute(
        select(LessonContent).where(LessonContent.motif_id == motif.id)
    ).scalar_one_or_none()
    if lesson is None:
        lesson = LessonContent(
            motif_id=motif.id,
            intro_text=intro_text,
            description=description,
            historical_context=historical_context,
            symbolism=symbolism,
            fun_fact=fun_fact,
            is_ai_generated=is_ai_generated,
        )
        session.add(lesson)
        session.flush()
        return lesson

    lesson.intro_text = intro_text
    lesson.description = description
    lesson.historical_context = historical_context
    lesson.symbolism = symbolism
    lesson.fun_fact = fun_fact
    lesson.is_ai_generated = is_ai_generated
    session.flush()
    return lesson


def upsert_quiz_question(
    session: Session,
    *,
    motif: Motif,
    question_type: QuestionType = QuestionType.multiple_choice,
    question_text: str,
    options: list[str] | None,
    correct_answer: str,
    difficulty: int = 1,
    explanation: str | None = None,
) -> QuizQuestion:
    existing = session.execute(
        select(QuizQuestion).where(
            QuizQuestion.motif_id == motif.id,
            QuizQuestion.question_text == question_text,
        )
    ).scalar_one_or_none()

    if existing is None:
        existing = QuizQuestion(
            motif_id=motif.id,
            question_type=question_type,
            question_text=question_text,
            options=options,
            correct_answer=correct_answer,
            difficulty=difficulty,
            explanation=explanation,
            is_active=True,
        )
        session.add(existing)
        session.flush()
        return existing

    existing.question_type = question_type
    existing.options = options
    existing.correct_answer = correct_answer
    existing.difficulty = difficulty
    existing.explanation = explanation
    existing.is_active = True
    session.flush()
    return existing


def upsert_urn_exam(
    session: Session,
    *,
    urn: Urn,
    questions: list[dict[str, Any]],
    passing_score: int | None = None,
    xp_reward: int | None = None,
) -> UrnExam:
    existing = (
        session.execute(select(UrnExam).where(UrnExam.urn_id == urn.id))
        .scalars()
        .first()
    )

    if existing is None:
        exam = UrnExam(
            urn_id=urn.id,
            questions=questions,
        )
        if passing_score is not None:
            exam.passing_score = passing_score
        if xp_reward is not None:
            exam.xp_reward = xp_reward
        session.add(exam)
        session.flush()
        return exam

    existing.questions = questions
    if passing_score is not None:
        existing.passing_score = passing_score
    if xp_reward is not None:
        existing.xp_reward = xp_reward
    session.flush()
    return existing


def seed_urn_exams(session: Session, *, exams_path: Path) -> None:
    if not exams_path.exists():
        print(f"Warning: Urn exam seed path {exams_path} does not exist.")
        return

    exam_files = sorted(exams_path.glob("*.json"))
    if not exam_files:
        print(f"Warning: No urn exam JSON files found in {exams_path}.")
        return

    for file_path in exam_files:
        stem = file_path.stem
        for suffix in ("_exam", "-exam"):
            if stem.endswith(suffix):
                stem = stem[: -len(suffix)]
                break
        urn_slug = slugify(stem)

        urn = session.execute(
            select(Urn).where(Urn.slug == urn_slug)
        ).scalar_one_or_none()
        if urn is None:
            print(
                f"Warning: No urn found for urn exam file {file_path} (expected slug={urn_slug!r})."
            )
            continue

        try:
            payload = json.loads(file_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            print(f"Warning: Failed to parse urn exam JSON {file_path}: {exc}")
            continue

        passing_score: int | None = None
        xp_reward: int | None = None
        questions_raw: Any = payload

        if isinstance(payload, dict):
            questions_raw = payload.get("questions")
            if "passing_score" in payload:
                try:
                    passing_score = int(payload["passing_score"])
                except (TypeError, ValueError):
                    print(
                        f"Warning: Invalid passing_score in {file_path}: {payload.get('passing_score')!r}"
                    )
            if "xp_reward" in payload:
                try:
                    xp_reward = int(payload["xp_reward"])
                except (TypeError, ValueError):
                    print(
                        f"Warning: Invalid xp_reward in {file_path}: {payload.get('xp_reward')!r}"
                    )

        if not isinstance(questions_raw, list):
            print(
                f"Warning: Expected JSON array (or object with 'questions' array) in {file_path}"
            )
            continue

        questions: list[dict[str, Any]] = []
        for idx, raw in enumerate(questions_raw, start=1):
            if not isinstance(raw, dict):
                print(f"Warning: Skipping non-object question #{idx} in {file_path}")
                continue

            question_text = raw.get("question_text") or raw.get("question")
            correct_answer = raw.get("correct_answer")
            if not question_text or correct_answer is None:
                print(
                    f"Warning: Skipping invalid question #{idx} in {file_path} (missing text/answer)"
                )
                continue

            q_type_raw = raw.get("question_type") or raw.get("type")
            q_type, q_type_ok = coerce_enum(
                QuestionType, q_type_raw, QuestionType.multiple_choice
            )
            if q_type_raw is not None and str(q_type_raw).strip() and not q_type_ok:
                print(
                    f"Warning: Unknown question type {q_type_raw!r} in {file_path} question #{idx}; "
                    f"defaulting to {q_type.value!r}"
                )

            options = raw.get("options")
            if options is not None and not isinstance(options, list):
                print(
                    f"Warning: Skipping invalid options in {file_path} question #{idx}"
                )
                continue
            if isinstance(options, list):
                options = [str(opt) for opt in options]

            explanation_raw = raw.get("explanation")
            explanation = (
                explanation_raw.strip() if isinstance(explanation_raw, str) else None
            )
            if explanation == "":
                explanation = None

            normalized: dict[str, Any] = {
                "question_text": str(question_text),
                "question_type": q_type.value,
                "correct_answer": str(correct_answer),
            }
            if options is not None:
                normalized["options"] = options
            if explanation is not None:
                normalized["explanation"] = explanation

            difficulty_raw = raw.get("difficulty")
            if difficulty_raw is not None:
                difficulty, difficulty_ok = coerce_difficulty(difficulty_raw, default=1)
                normalized["difficulty"] = difficulty
                if str(difficulty_raw).strip() and not difficulty_ok:
                    print(
                        f"Warning: Invalid difficulty {difficulty_raw!r} in {file_path} question #{idx}; using {difficulty}"
                    )

            questions.append(normalized)

        if not questions:
            print(
                f"Warning: No valid questions found in {file_path}; skipping urn exam seed."
            )
            continue

        upsert_urn_exam(
            session,
            urn=urn,
            questions=questions,
            passing_score=passing_score,
            xp_reward=xp_reward,
        )


def run_seed(
    config: SeedConfig,
    image_path: Path | None = None,
    coords_path: Path | None = None,
) -> None:
    engine = create_engine(config.database_url, pool_pre_ping=True)
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

    files_to_process = []
    if config.seed_path.is_file():
        files_to_process.append(config.seed_path)
    elif config.seed_path.is_dir():
        files_to_process.extend(sorted(config.seed_path.glob("*.json")))
        files_to_process.extend(sorted(config.seed_path.glob("*.md")))
    else:
        print(f"Warning: Seed path {config.seed_path} not found.")
        return

    # Load image map
    image_map = {}
    urn_thumbnail_map: dict[str, str] = {}
    if image_path:
        image_map = scan_images(image_path)
        for urn_slug in URN_ORDER.keys():
            url = image_map.get((urn_slug, urn_slug))
            if url:
                urn_thumbnail_map[urn_slug] = url

    all_items = []
    for file_path in files_to_process:
        try:
            items = process_file(file_path)
            all_items.extend(items)
            print(f"Loaded {len(items)} items from {file_path}")
        except Exception as e:
            print(f"Error processing {file_path}: {e}")

    with SessionLocal() as session:
        for badge in DEFAULT_BADGES:
            upsert_badge(
                session,
                slug=str(badge["slug"]),
                name=str(badge["name"]),
                name_en=(str(badge["name_en"]) if badge.get("name_en") else None),
                description=(
                    str(badge["description"]) if badge.get("description") else None
                ),
                icon_url=str(badge["icon_url"]),
                category=badge["category"],
                xp_bonus=int(badge.get("xp_bonus") or 0),
                unlock_criteria=badge.get("unlock_criteria") or {},
                is_secret=bool(badge.get("is_secret") or False),
            )

        for idx, item in enumerate(all_items, start=1):
            urn_name = str(item["urn_location"])
            urn = upsert_urn(
                session,
                name=urn_name,
                model_base_url=config.model_base_url,
                thumbnail_url=urn_thumbnail_map.get(slugify(urn_name)),
            )

            mesh_name = str(item["3d_mesh_id"])
            name_vi = str(item["name_vi"])

            # Prefer scanned images over explicit thumbnail_url from seed
            thumbnail_url = None
            if image_map:
                thumbnail_url = resolve_thumbnail_url(
                    image_map, urn_slug=urn.slug, name_vi=name_vi
                )
                if not thumbnail_url:
                    print(
                        f"Warning: No thumbnail match for urn={urn.slug!r} motif={name_vi!r}"
                    )
            # Fallback to explicit thumbnail_url from seed data if no image match
            if not thumbnail_url:
                thumbnail_url_raw = item.get("thumbnail_url")
                thumbnail_url = (
                    str(thumbnail_url_raw).strip()
                    if isinstance(thumbnail_url_raw, str)
                    else None
                )

            display_order = parse_display_order(item.get("id")) or idx

            category_raw = item.get("category")
            category_raw_text = (
                str(category_raw).strip() if category_raw is not None else ""
            )
            category, category_ok = coerce_enum(
                MotifCategory, category_raw, MotifCategory.thao_moc
            )
            if not category_raw_text:
                print(
                    f"Warning: Missing category for motif mesh_name={mesh_name!r}; "
                    f"defaulting to {category.value!r}"
                )
            elif not category_ok:
                print(
                    f"Warning: Unknown category {category_raw!r} for motif mesh_name={mesh_name!r}; "
                    f"defaulting to {category.value!r}"
                )

            rarity_raw = item.get("rarity")
            rarity_raw_text = str(rarity_raw).strip() if rarity_raw is not None else ""
            rarity, rarity_ok = coerce_enum(MotifRarity, rarity_raw, MotifRarity.common)
            if not rarity_raw_text:
                print(
                    f"Warning: Missing rarity for motif mesh_name={mesh_name!r}; "
                    f"defaulting to {rarity.value!r}"
                )
            elif not rarity_ok:
                print(
                    f"Warning: Unknown rarity {rarity_raw!r} for motif mesh_name={mesh_name!r}; "
                    f"defaulting to {rarity.value!r}"
                )

            motif = upsert_motif(
                session,
                urn=urn,
                mesh_name=mesh_name,
                name_vi=name_vi,
                name_en=item.get("name_en"),
                category=category,
                rarity=rarity,
                display_order=display_order,
                thumbnail_url=thumbnail_url,
            )

            description_short = item.get("description_short")
            description_educational = (
                item.get("description_educational") or description_short
            )
            if not description_educational:
                print(f"Warning: Missing description for motif mesh_name={mesh_name!r}")
                continue

            upsert_lesson(
                session,
                motif=motif,
                intro_text=description_short,
                description=str(description_educational),
                historical_context=item.get("historical_context"),
                symbolism=item.get("symbolism"),
                fun_fact=item.get("fun_fact"),
                is_ai_generated=item.get("is_ai_generated", False),
            )

            # Support both old format (quiz_question) and new format (quiz_questions)
            quiz_questions = item.get("quiz_questions", [])
            if not quiz_questions:
                # Fallback to old single question format
                quiz = item.get("quiz_question")
                if isinstance(quiz, dict):
                    quiz_questions = [quiz]

            for quiz in quiz_questions:
                if not isinstance(quiz, dict):
                    continue
                question_text = quiz.get("question")
                correct_answer = quiz.get("correct_answer")
                if not question_text or not correct_answer:
                    print(
                        f"Warning: Invalid quiz question for motif mesh_name={mesh_name!r}"
                    )
                    continue

                options = quiz.get("options")
                if options is not None and not isinstance(options, list):
                    print(
                        f"Warning: Invalid quiz question options for motif mesh_name={mesh_name!r}"
                    )
                    continue
                if isinstance(options, list):
                    options = [str(opt) for opt in options]

                # Map question type string to enum
                q_type_raw = quiz.get("type")
                q_type, q_type_ok = coerce_enum(
                    QuestionType, q_type_raw, QuestionType.multiple_choice
                )
                if q_type_raw is not None and str(q_type_raw).strip() and not q_type_ok:
                    print(
                        f"Warning: Unknown question type {q_type_raw!r} for motif mesh_name={mesh_name!r}; "
                        f"defaulting to {q_type.value!r}"
                    )

                difficulty_raw = quiz.get("difficulty")
                difficulty, difficulty_ok = coerce_difficulty(difficulty_raw, default=1)
                if (
                    difficulty_raw is not None
                    and str(difficulty_raw).strip()
                    and not difficulty_ok
                ):
                    print(
                        f"Warning: Invalid difficulty {difficulty_raw!r} for motif mesh_name={mesh_name!r}; "
                        f"using {difficulty}"
                    )

                explanation_raw = quiz.get("explanation")
                explanation = (
                    explanation_raw.strip()
                    if isinstance(explanation_raw, str)
                    else None
                )
                if explanation == "":
                    explanation = None

                upsert_quiz_question(
                    session,
                    motif=motif,
                    question_type=q_type,
                    question_text=str(question_text),
                    options=options,
                    correct_answer=str(correct_answer),
                    difficulty=difficulty,
                    explanation=explanation,
                )

        seed_root = (
            config.seed_path if config.seed_path.is_dir() else config.seed_path.parent
        )
        seed_urn_exams(session, exams_path=seed_root / "urn_exams")
        seed_coordinates(session, coords_path)
        seed_quests(session)
        seed_demo_users(session)

        session.commit()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Seed Luuniensuki PostgreSQL database from JSON/Markdown files"
    )
    parser.add_argument(
        "--seed-path",
        default="data",
        help="Path to a file or directory containing seed data (JSON or Markdown)",
    )
    parser.add_argument(
        "--image-path",
        default="ban-duc-noi",
        help="Path to the directory containing embossed images (e.g., ban-duc-noi)",
    )
    parser.add_argument(
        "--coords-path",
        default=".",
        help="Path to coordinates JSON file or a directory containing motif-coordinates-*.json",
    )
    args = parser.parse_args()

    database_url = os.getenv(
        "DATABASE_URL",
        "postgresql+psycopg://postgres:postgres@localhost:5432/luuniensuki",
    )
    model_base_url = os.getenv("MODEL_BASE_URL", "/assets/models")

    run_seed(
        SeedConfig(
            database_url=database_url,
            seed_path=Path(args.seed_path),
            model_base_url=model_base_url,
        ),
        image_path=Path(args.image_path) if args.image_path else None,
        coords_path=Path(args.coords_path) if args.coords_path else None,
    )


if __name__ == "__main__":
    main()
