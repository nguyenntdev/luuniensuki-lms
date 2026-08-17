"""History Story Engine tests (Phase 10, Spec section 30).

Covers: staff CRUD, public list serves only published stories, block-type /
referenced-entity validation, draft hides from the public slug endpoint, and
learners are rejected from mutations.
"""
from sqlalchemy import select

from backend.models import (
    HistoricalEntity,
    HistoricalSource,
    HistoryStory,
    QuizQuestion,
    QuestionType,
    User,
    UserRole,
)


def _register(client, email, display_name):
    res = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "password123", "display_name": display_name},
    )
    assert res.status_code == 201, res.text
    return res


def _make_staff(client, db_session, email, display_name, role=UserRole.admin):
    _register(client, email, display_name)
    user = db_session.execute(select(User).where(User.email == email)).scalar_one()
    user.role = role
    db_session.commit()
    client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "password123"},
    )
    return user


def _seed_story(db_session, **overrides):
    data = {
        "slug": "cuu-dinh-hinh-bong-dat-nuoc",
        "title_vi": "Cửu Đỉnh: Hình bóng đất nước",
        "summary_vi": "Chín chiếc đỉnh đồng là tấm bản đồ thu nhỏ của đất nước.",
        "status": "published",
        "publication_status": "unreviewed",
        "featured": False,
        "blocks": [],
    }
    data.update(overrides)
    story = HistoryStory(**data)
    db_session.add(story)
    db_session.flush()
    return story


# --------------------------------------------------------------------------- #
# Public read — published only
# --------------------------------------------------------------------------- #
def test_public_list_returns_only_published(client, db_session):
    _seed_story(db_session, slug="truyen-da-xuat-ban", status="published")
    _seed_story(db_session, slug="truyen-ban-nhap", status="draft")
    db_session.commit()

    res = client.get("/api/v1/history/stories")
    assert res.status_code == 200, res.text
    slugs = [s["slug"] for s in res.json()["items"]]
    assert "truyen-da-xuat-ban" in slugs
    assert "truyen-ban-nhap" not in slugs


def test_public_list_featured_only(client, db_session):
    _seed_story(db_session, slug="truyen-noi-bat", status="published", featured=True)
    _seed_story(db_session, slug="truyen-thuong", status="published", featured=False)
    db_session.commit()

    res = client.get("/api/v1/history/stories", params={"featured_only": "true"})
    assert res.status_code == 200, res.text
    slugs = [s["slug"] for s in res.json()["items"]]
    assert slugs == ["truyen-noi-bat"]


def test_public_get_published_story(client, db_session):
    story = _seed_story(db_session, slug="truyen-chi-tiet", status="published")
    db_session.commit()

    res = client.get("/api/v1/history/stories/truyen-chi-tiet")
    assert res.status_code == 200, res.text
    assert res.json()["title_vi"] == story.title_vi
    assert res.json()["status"] == "published"


def test_public_get_draft_returns_404(client, db_session):
    _seed_story(db_session, slug="truyen-bi-an", status="draft")
    db_session.commit()

    res = client.get("/api/v1/history/stories/truyen-bi-an")
    assert res.status_code == 404, res.text


# --------------------------------------------------------------------------- #
# Staff CRUD
# --------------------------------------------------------------------------- #
def test_staff_create_update_publish_story(client, db_session):
    _make_staff(client, db_session, "storyadmin@example.com", "Story Admin")

    res = client.post(
        "/api/v1/history/stories",
        json={
            "slug": "song-ngoi-tren-cuu-dinh",
            "title_vi": "Sông ngòi trên Cửu Đỉnh",
            "summary_vi": "Những dòng sông được khắc trên đỉnh đồng.",
            "blocks": [{"type": "text", "body": "Nội dung mở đầu."}],
        },
    )
    assert res.status_code == 200, res.text
    story_id = res.json()["id"]
    assert res.json()["status"] == "draft"

    res = client.patch(
        f"/api/v1/history/stories/{story_id}",
        json={
            "featured": True,
            "blocks": [
                {"type": "text", "body": "Nội dung mở đầu."},
                {"type": "callout", "body": "Lưu ý: chờ kiểm chứng."},
            ],
        },
    )
    assert res.status_code == 200, res.text
    assert res.json()["featured"] is True
    assert len(res.json()["blocks"]) == 2

    res = client.post(f"/api/v1/history/stories/{story_id}/publish")
    assert res.status_code == 200, res.text
    assert res.json()["status"] == "published"
    assert res.json()["published_at"] is not None

    public = client.get("/api/v1/history/stories/song-ngoi-tren-cuu-dinh")
    assert public.status_code == 200, public.text
    assert public.json()["featured"] is True


def test_staff_create_duplicate_slug_rejected(client, db_session):
    _make_staff(client, db_session, "storydup@example.com", "Story Dup")
    _seed_story(db_session, slug="trung-slug", status="draft")
    db_session.commit()

    res = client.post(
        "/api/v1/history/stories",
        json={"slug": "trung-slug", "title_vi": "Trùng slug"},
    )
    assert res.status_code == 409, res.text


def test_staff_update_missing_story_404(client, db_session):
    _make_staff(client, db_session, "storymiss@example.com", "Story Miss")
    res = client.patch(
        "/api/v1/history/stories/00000000-0000-0000-0000-000000000000",
        json={"title_vi": "Không tồn tại"},
    )
    assert res.status_code == 404, res.text


# --------------------------------------------------------------------------- #
# Block validation
# --------------------------------------------------------------------------- #
def test_staff_create_rejects_invalid_block_type(client, db_session):
    _make_staff(client, db_session, "storytype@example.com", "Story Type")
    res = client.post(
        "/api/v1/history/stories",
        json={
            "slug": "sai-loai-block",
            "title_vi": "Truyện sai loại block",
            "blocks": [{"type": "not_a_real_block", "body": "x"}],
        },
    )
    assert res.status_code == 422, res.text
    assert res.json()["error"]["code"] == "HISTORY_STORY_INVALID_BLOCKS"


def test_staff_create_rejects_missing_required_field(client, db_session):
    _make_staff(client, db_session, "storyfield@example.com", "Story Field")
    res = client.post(
        "/api/v1/history/stories",
        json={
            "slug": "thieu-truong",
            "title_vi": "Truyện thiếu trường",
            "blocks": [{"type": "quote"}],
        },
    )
    assert res.status_code == 422, res.text


def test_staff_create_rejects_missing_entity(client, db_session):
    _make_staff(client, db_session, "storyent@example.com", "Story Ent")
    res = client.post(
        "/api/v1/history/stories",
        json={
            "slug": "thieu-thuc-the",
            "title_vi": "Truyện thiếu thực thể",
            "blocks": [
                {
                    "type": "relief_focus",
                    "entity_id": "00000000-0000-0000-0000-000000000000",
                }
            ],
        },
    )
    assert res.status_code == 422, res.text
    assert res.json()["error"]["code"] == "HISTORY_STORY_INVALID_BLOCKS"


def test_staff_create_rejects_missing_source(client, db_session):
    _make_staff(client, db_session, "storysrc@example.com", "Story Src")
    res = client.post(
        "/api/v1/history/stories",
        json={
            "slug": "thieu-nguon",
            "title_vi": "Truyện thiếu nguồn",
            "blocks": [
                {
                    "type": "source_excerpt",
                    "source_id": "00000000-0000-0000-0000-000000000000",
                }
            ],
        },
    )
    assert res.status_code == 422, res.text


def test_staff_create_accepts_existing_entity_and_source(client, db_session):
    _make_staff(client, db_session, "storyok@example.com", "Story OK")
    entity = HistoricalEntity(
        entity_type="relief", slug="dong-hai", name_vi="Đông Hải"
    )
    db_session.add(entity)
    source = HistoricalSource(
        source_type="royal_record",
        title="Khâm định Đại Nam hội điển sự lệ",
        verification_status="metadata_verified",
    )
    db_session.add(source)
    db_session.commit()

    res = client.post(
        "/api/v1/history/stories",
        json={
            "slug": "truyen-hop-le",
            "title_vi": "Truyện hợp lệ",
            "blocks": [
                {"type": "relief_focus", "entity_id": str(entity.id)},
                {"type": "source_excerpt", "source_id": str(source.id)},
            ],
        },
    )
    assert res.status_code == 200, res.text
    assert len(res.json()["blocks"]) == 2


def test_staff_create_rejects_non_relief_for_relief_focus(client, db_session):
    _make_staff(client, db_session, "storyrel@example.com", "Story Rel")
    entity = HistoricalEntity(
        entity_type="person", slug="gia-long", name_vi="Gia Long"
    )
    db_session.add(entity)
    db_session.commit()

    res = client.post(
        "/api/v1/history/stories",
        json={
            "slug": "sai-loai-thuc-the",
            "title_vi": "Sai loại thực thể",
            "blocks": [{"type": "relief_focus", "entity_id": str(entity.id)}],
        },
    )
    assert res.status_code == 422, res.text


# --------------------------------------------------------------------------- #
# Service-level validation
# --------------------------------------------------------------------------- #
def test_validate_story_blocks_returns_error_list(db_session):
    from backend.services.history_stories import validate_story_blocks

    errors = validate_story_blocks(
        [
            {"type": "text", "body": "ok"},
            {"type": "bogus"},
        ],
        db_session,
    )
    assert any("unknown block type" in e for e in errors)


# --------------------------------------------------------------------------- #
# Role guard
# --------------------------------------------------------------------------- #
def test_learner_cannot_mutate_stories(client, db_session):
    _make_staff(
        client, db_session, "storylearner@example.com", "Story Learner", UserRole.learner
    )
    res = client.post(
        "/api/v1/history/stories", json={"slug": "x", "title_vi": "X"}
    )
    assert res.status_code == 403, res.text

    res = client.patch(
        "/api/v1/history/stories/00000000-0000-0000-0000-000000000000",
        json={"title_vi": "Y"},
    )
    assert res.status_code == 403, res.text