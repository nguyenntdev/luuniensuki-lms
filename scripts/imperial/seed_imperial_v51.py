#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Idempotent database seeder for STTT Imperial City V5.1 dataset (Lưu Niên — Đại Nội Huế).

Populates:
1. Verified art details (with claim sources & questions)
2. Learning media assets & interactive hotspots (with normalized UV coordinates)
3. Heritage Detective clues (riddles with progressive hint steps)
4. Gamified interactive questions (deep comprehension, matching, hotspot discovery)

Ref: Luu Nien STTTNND Follow-On SPEC V5.1
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from uuid import NAMESPACE_DNS, UUID, uuid5

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from backend.imperial_models import CONTENT_SCOPE_IMPERIAL, ImperialSite
from backend.models import User
from backend.imperial_v51_models import (
    ImperialArtDetail,
    ImperialArtDetailClaimSource,
    ImperialArtDetailQuestion,
    ImperialClue,
    ImperialLearningMedia,
    ImperialMediaHotspot,
    ImperialQuestion,
)

DEFAULT_DB_URL = "postgresql+psycopg://postgres:postgres@localhost:5432/luuniensuki"


def seed_imperial_v51_data(db_url: str | None = None) -> dict[str, int]:
    """Execute idempotent seeding of V5.1 art details, clues, and questions."""
    url = db_url or os.environ.get("DATABASE_URL") or DEFAULT_DB_URL
    engine = create_engine(url, pool_pre_ping=True)
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

    data_path = REPO_ROOT / "data" / "imperial" / "v51_art_details_and_clues.json"
    if not data_path.exists():
        raise FileNotFoundError(f"Missing {data_path}")

    v51_data = json.loads(data_path.read_text(encoding="utf-8"))

    stats = {
        "art_details_seeded": 0,
        "claim_sources_seeded": 0,
        "detail_questions_seeded": 0,
        "learning_media_seeded": 0,
        "media_hotspots_seeded": 0,
        "clues_seeded": 0,
        "game_questions_seeded": 0,
    }

    with SessionLocal() as session:
        # Build site mapping: slug -> ImperialSite
        sites = session.execute(
            select(ImperialSite).where(ImperialSite.content_scope == CONTENT_SCOPE_IMPERIAL)
        ).scalars().all()
        site_map: dict[str, ImperialSite] = {s.slug: s for s in sites}

        # ------------------------------------------------------------------- #
        # 1. Art Details
        # ------------------------------------------------------------------- #
        art_detail_map: dict[str, ImperialArtDetail] = {}
        for d in v51_data.get("art_details", []):
            slug = d["slug"]
            site_slug = d["site_slug"]
            site = site_map.get(site_slug)
            if not site:
                continue

            detail_id = uuid5(NAMESPACE_DNS, f"imperial_art_detail:{slug}")
            detail = session.get(ImperialArtDetail, detail_id)
            if not detail:
                detail = session.execute(
                    select(ImperialArtDetail).where(
                        ImperialArtDetail.content_scope == CONTENT_SCOPE_IMPERIAL,
                        ImperialArtDetail.slug == slug,
                    )
                ).scalar_one_or_none()

            if detail:
                detail.title = d["title"]
                detail.kind = d.get("kind", "carving")
                detail.motif = d.get("motif")
                detail.material = d.get("material")
                detail.technique = d.get("technique")
                detail.description_observation = d.get("description_observation")
                detail.story_body = d.get("story_body")
                detail.story_type = d.get("story_type", "documented_event")
                detail.meaning_body = d.get("meaning_body")
                detail.historical_value_body = d.get("historical_value_body")
                detail.cultural_value_body = d.get("cultural_value_body")
                detail.art_value_body = d.get("art_value_body")
                detail.review_status = "published"
            else:
                detail = ImperialArtDetail(
                    id=detail_id,
                    content_scope=CONTENT_SCOPE_IMPERIAL,
                    site_id=site.id,
                    slug=slug,
                    title=d["title"],
                    kind=d.get("kind", "carving"),
                    motif=d.get("motif"),
                    material=d.get("material"),
                    technique=d.get("technique"),
                    description_observation=d.get("description_observation"),
                    story_body=d.get("story_body"),
                    story_type=d.get("story_type", "documented_event"),
                    meaning_body=d.get("meaning_body"),
                    historical_value_body=d.get("historical_value_body"),
                    cultural_value_body=d.get("cultural_value_body"),
                    art_value_body=d.get("art_value_body"),
                    review_status="published",
                    content_revision=1,
                    row_version=1,
                )
                session.add(detail)
                stats["art_details_seeded"] += 1

            art_detail_map[slug] = detail
            session.flush()

            # Claim sources for detail
            for cs in d.get("claim_sources", []):
                cs_id = uuid5(NAMESPACE_DNS, f"art_claim:{slug}:{cs['section']}")
                claim = session.get(ImperialArtDetailClaimSource, cs_id)
                if not claim:
                    claim = ImperialArtDetailClaimSource(
                        id=cs_id,
                        content_scope=CONTENT_SCOPE_IMPERIAL,
                        detail_id=detail.id,
                        section=cs["section"],
                        claim_text=cs["claim_text"],
                        source_title=cs["source_title"],
                        source_locator=cs.get("source_locator"),
                        evidence_strength=cs.get("evidence_strength", "verified"),
                    )
                    session.add(claim)
                    stats["claim_sources_seeded"] += 1

            # Questions for detail
            for idx, q in enumerate(d.get("questions", [])):
                q_id = uuid5(NAMESPACE_DNS, f"detail_q:{slug}:{idx}")
                question = session.get(ImperialArtDetailQuestion, q_id)
                if not question:
                    question = ImperialArtDetailQuestion(
                        id=q_id,
                        content_scope=CONTENT_SCOPE_IMPERIAL,
                        detail_id=detail.id,
                        question_type=q.get("question_type", "multiple_choice"),
                        prompt=q["prompt"],
                        options=q.get("options", []),
                        answer_key=str(q.get("answer_key", "0")),
                        explanation=q.get("explanation"),
                        display_order=idx + 1,
                    )
                    session.add(question)
                    stats["detail_questions_seeded"] += 1

        session.commit()

        # ------------------------------------------------------------------- #
        # 2. Learning Media & Hotspots
        # ------------------------------------------------------------------- #
        for m in v51_data.get("learning_media", []):
            site_slug = m.get("site_slug")
            site = site_map.get(site_slug) if site_slug else None
            if not site:
                continue

            media_id = uuid5(NAMESPACE_DNS, f"imperial_media:{m.get('id', site_slug)}")
            media = session.get(ImperialLearningMedia, media_id)
            if not media:
                media = ImperialLearningMedia(
                    id=media_id,
                    content_scope=CONTENT_SCOPE_IMPERIAL,
                    site_id=site.id,
                    kind=m.get("kind", "image"),
                    media_url=m["media_url"],
                    thumbnail_url=m.get("thumbnail_url"),
                    asset_revision=1,
                    width_px=m.get("width_px", 2048),
                    height_px=m.get("height_px", 1024),
                    license_status="approved",
                    review_status="published",
                    alt_text=m.get("title_vi"),
                    credit_text=m.get("credit_text", "Lưu Niên — Đại Nội Huế"),
                    asset_context=m.get("asset_context", "extant"),
                    row_version=1,
                )
                session.add(media)
                stats["learning_media_seeded"] += 1
                session.flush()

            for h in m.get("hotspots", []):
                h_id = uuid5(NAMESPACE_DNS, f"imperial_hotspot:{h.get('id', h['title'])}")
                hotspot = session.get(ImperialMediaHotspot, h_id)
                detail_slug = h.get("detail_slug")
                target_detail = art_detail_map.get(detail_slug) if detail_slug else None

                if not hotspot:
                    hotspot = ImperialMediaHotspot(
                        id=h_id,
                        content_scope=CONTENT_SCOPE_IMPERIAL,
                        media_id=media.id,
                        point_kind=h.get("point_kind", "point"),
                        u=h["u"],
                        v=h["v"],
                        position_payload=h.get("position_payload"),
                        title=h["title"],
                        description=h.get("description"),
                        detail_id=target_detail.id if target_detail else None,
                        review_status="published",
                        row_version=1,
                    )
                    session.add(hotspot)
                    stats["media_hotspots_seeded"] += 1

        session.commit()

        # ------------------------------------------------------------------- #
        # 3. Heritage Detective Clues
        # ------------------------------------------------------------------- #
        for c in v51_data.get("clues", []):
            clue_slug = c.get("id") or c["title"]
            clue_id = uuid5(NAMESPACE_DNS, f"imperial_clue:{clue_slug}")
            clue = session.get(ImperialClue, clue_id)

            target_type = c.get("target_type", "site")
            target_slug = c.get("target_slug")
            target_id = None
            if target_type == "site" and target_slug in site_map:
                target_id = site_map[target_slug].id
            elif target_type == "art_detail" and target_slug in art_detail_map:
                target_id = art_detail_map[target_slug].id
            else:
                # Default to first site if not found
                target_id = next(iter(site_map.values())).id if site_map else clue_id

            if clue:
                clue.title = c["title"]
                clue.clue_text = c["clue_text"]
                clue.target_type = target_type
                clue.target_id = target_id
                clue.hint_steps = c.get("hint_steps", [])
                clue.difficulty = c.get("difficulty", "medium")
                clue.review_status = "published"
            else:
                clue = ImperialClue(
                    id=clue_id,
                    content_scope=CONTENT_SCOPE_IMPERIAL,
                    title=c["title"],
                    clue_text=c["clue_text"],
                    target_type=target_type,
                    target_id=target_id,
                    hint_steps=c.get("hint_steps", []),
                    grade_level="Lớp 10 THPT",
                    difficulty=c.get("difficulty", "medium"),
                    review_status="published",
                    row_version=1,
                )
                session.add(clue)
                stats["clues_seeded"] += 1

        session.commit()

        # ------------------------------------------------------------------- #
        # 4. Interactive Game Questions
        # ------------------------------------------------------------------- #
        for idx, gq in enumerate(v51_data.get("game_questions", [])):
            q_slug = gq.get("id") or f"game-q-{idx}"
            q_id = uuid5(NAMESPACE_DNS, f"imperial_game_q:{q_slug}")
            question = session.get(ImperialQuestion, q_id)

            site_slug = gq.get("site_slug")
            site = site_map.get(site_slug) if site_slug else None

            if question:
                question.prompt = gq["prompt"]
                question.options = gq.get("options", [])
                question.answer_key = str(gq.get("answer_key", "0"))
                question.explanation_why = gq.get("explanation_why")
                question.source_citation = gq.get("source_citation")
                question.review_status = "published"
            else:
                question = ImperialQuestion(
                    id=q_id,
                    content_scope=CONTENT_SCOPE_IMPERIAL,
                    site_id=site.id if site else None,
                    question_type=gq.get("question_type", "multiple_choice"),
                    prompt=gq["prompt"],
                    options=gq.get("options", []),
                    answer_key=str(gq.get("answer_key", "0")),
                    explanation_why=gq.get("explanation_why"),
                    source_citation=gq.get("source_citation"),
                    review_status="published",
                    row_version=1,
                )
                session.add(question)
                stats["game_questions_seeded"] += 1

        session.commit()

    return stats


def main():
    parser = argparse.ArgumentParser(description="Seed Imperial City V5.1 dataset")
    parser.add_argument("--db-url", type=str, default=None, help="Database connection URL")
    args = parser.parse_args()

    print("[*] Seeding STTT Imperial City V5.1 data...")
    try:
        stats = seed_imperial_v51_data(args.db_url)
        print(f"[✓] V5.1 Seeding complete: {stats}")
    except Exception as e:
        print(f"[!] Error seeding V5.1 data: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
