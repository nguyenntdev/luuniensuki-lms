import os
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy import event, text
from sqlalchemy.orm import sessionmaker

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from backend.models import Badge
from backend.models import BadgeCategory
from backend.models import Base
from backend.models import LessonContent
from backend.models import Motif
from backend.models import MotifCategory
from backend.models import MotifRarity
from backend.models import QuestionType
from backend.models import QuizQuestion
from backend.models import Urn


os.environ.setdefault(
    "DATABASE_URL",
    "postgresql+psycopg://postgres:postgres@localhost:5432/luuniensuki_test",
)

import backend.history_models  # noqa: F401
import backend.models_rbpc  # noqa: F401
import backend.main as main  # noqa: E402  (DATABASE_URL must be set before importing)


@pytest.fixture(scope="session")
def engine():
    engine = create_engine(os.environ["DATABASE_URL"], pool_pre_ping=True)
    with engine.connect() as conn:
        conn.execute(text("DROP SCHEMA public CASCADE; CREATE SCHEMA public;"))
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS pgcrypto; CREATE EXTENSION IF NOT EXISTS unaccent; CREATE EXTENSION IF NOT EXISTS pg_trgm;"))
        conn.commit()
    Base.metadata.create_all(engine)
    return engine


@pytest.fixture
def db_session(engine):
    connection = engine.connect()
    transaction = connection.begin()
    TestingSessionLocal = sessionmaker(bind=connection, autoflush=False, autocommit=False)
    session = TestingSessionLocal()

    session.begin_nested()

    @event.listens_for(session, "after_transaction_end")
    def _restart_savepoint(sess, trans):
        if trans.nested and not trans._parent.nested:
            sess.begin_nested()

    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()


@pytest.fixture
def client(db_session):
    def override_get_db():
        yield db_session

    main.app.dependency_overrides[main.get_db] = override_get_db
    with TestClient(main.app) as client:
        yield client
    main.app.dependency_overrides.clear()


@pytest.fixture
def seeded_content(db_session):
    for b in [
        Badge(
            slug="first-discovery",
            name="Khai Môn",
            name_en="First Discovery",
            description="Mở khóa họa tiết đầu tiên.",
            icon_url="/assets/badges/first-discovery.svg",
            category=BadgeCategory.achievement,
            xp_bonus=100,
            unlock_criteria={"type": "first_discovery"},
            is_secret=False,
            is_active=True,
        ),
        Badge(
            slug="first-mastered",
            name="Bậc Thầy Đầu Tiên",
            name_en="First Mastery",
            description="Hoàn thành (mastered) họa tiết đầu tiên.",
            icon_url="/assets/badges/first-mastered.svg",
            category=BadgeCategory.achievement,
            xp_bonus=200,
            unlock_criteria={"type": "first_mastered"},
            is_secret=False,
            is_active=True,
        ),
        Badge(
            slug="streak-7",
            name="Thất Nhật Liên Tiếp",
            name_en="7-Day Streak",
            description="Duy trì streak 7 ngày liên tiếp.",
            icon_url="/assets/badges/streak-7.svg",
            category=BadgeCategory.achievement,
            xp_bonus=150,
            unlock_criteria={"type": "streak", "days": 7},
            is_secret=False,
            is_active=True,
        ),
    ]:
        db_session.add(b)

    urn = Urn(
        slug="cao-dinh",
        name="Cao Đỉnh",
        model_url="/assets/models/cao-dinh.glb",
        display_order=1,
        is_demo=True,
    )
    db_session.add(urn)
    db_session.flush()

    motif = Motif(
        urn_id=urn.id,
        mesh_name="mesh_urn_cao_tiger_v1",
        name="Hổ",
        name_en="Tiger",
        category=MotifCategory.dong_vat,
        rarity=MotifRarity.common,
        pos_x=0.0,
        pos_y=0.0,
        pos_z=0.0,
        bounding_radius=1.0,
        thumbnail_url="/assets/ban-duc-noi/CAO%20DINH/H%E1%BB%94.jpg",
        is_demo=True,
        is_active=True,
        display_order=1,
    )
    db_session.add(motif)
    db_session.flush()

    db_session.add(
        LessonContent(
            motif_id=motif.id,
            intro_text="Giới thiệu ngắn.",
            description="Bài học đầy đủ về họa tiết Hổ.",
            historical_context="Bối cảnh lịch sử về họa tiết Hổ.",
            symbolism="Ý nghĩa biểu tượng của họa tiết Hổ.",
            fun_fact="Sự thật thú vị về họa tiết Hổ.",
            is_ai_generated=True,
        )
    )

    question = QuizQuestion(
        motif_id=motif.id,
        question_type=QuestionType.multiple_choice,
        question_text="Họa tiết này là gì?",
        options=["A. Hổ", "B. Rồng"],
        correct_answer="A. Hổ",
        difficulty=1,
        explanation="Đáp án đúng là Hổ: họa tiết mô tả con hổ.",
        is_active=True,
    )
    db_session.add(question)

    db_session.commit()

    return {"urn": urn, "motif": motif, "question": question}
