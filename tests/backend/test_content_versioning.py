"""
Test suite for content versioning functionality.

Tests the P0-CMS-03 implementation including:
- LessonContent versioning metadata
- ContentVersion model
- Version history API endpoints
- Content revert functionality
"""

import pytest
from datetime import datetime, timezone
from uuid import uuid4

from backend.models import LessonContent, ContentVersion, User, Motif, Urn, UserRole
from backend.main import _create_content_snapshot


@pytest.fixture
def test_user(db_session):
    """Create a test admin user."""
    user = User(
        id=uuid4(),
        email="test_admin@example.com",
        password_hash="hashed",
        display_name="Test Admin",
        role=UserRole.admin,
    )
    db_session.add(user)
    db_session.commit()
    return user


@pytest.fixture
def test_urn(db_session):
    """Create a test urn."""
    urn = Urn(
        id=uuid4(),
        slug="test-urn",
        name="Test Urn",
        model_url="https://example.com/model.glb",
        display_order=1,
    )
    db_session.add(urn)
    db_session.commit()
    return urn


@pytest.fixture
def test_motif(db_session, test_urn):
    """Create a test motif."""
    motif = Motif(
        id=uuid4(),
        urn_id=test_urn.id,
        mesh_name="test_mesh",
        name="Test Motif",
        category="dong_vat",
        rarity="common",
        pos_x=0.0,
        pos_y=0.0,
        pos_z=0.0,
        bounding_radius=1.0,
    )
    db_session.add(motif)
    db_session.commit()
    return motif


@pytest.fixture
def test_lesson(db_session, test_motif, test_user):
    """Create a test lesson with versioning metadata."""
    lesson = LessonContent(
        id=uuid4(),
        motif_id=test_motif.id,
        description="Test lesson description",
        is_published=False,
        version=1,
        last_editor_id=test_user.id,
    )
    db_session.add(lesson)
    db_session.commit()
    return lesson


class TestLessonContentVersioning:
    """Test LessonContent versioning fields."""

    def test_lesson_has_version_field(self, test_lesson):
        """Test that lesson has version field with default value."""
        assert test_lesson.version == 1

    def test_lesson_has_last_editor(self, test_lesson, test_user):
        """Test that lesson tracks last editor."""
        assert test_lesson.last_editor_id == test_user.id
        assert test_lesson.last_editor is not None
        assert test_lesson.last_editor.email == test_user.email

    def test_lesson_published_at_nullable(self, test_lesson):
        """Test that published_at is nullable."""
        assert test_lesson.published_at is None

    def test_lesson_publish_note_nullable(self, test_lesson):
        """Test that publish_note is nullable."""
        assert test_lesson.publish_note is None

    def test_lesson_version_increment(self, db_session, test_lesson):
        """Test that version can be incremented."""
        test_lesson.version += 1
        db_session.commit()
        db_session.refresh(test_lesson)
        assert test_lesson.version == 2


class TestContentVersionModel:
    """Test ContentVersion model functionality."""

    def test_create_content_version(self, db_session, test_lesson, test_user):
        """Test creating a content version snapshot."""
        version_data = {
            "description": test_lesson.description,
            "is_published": test_lesson.is_published,
        }
        
        content_version = ContentVersion(
            content_type="lesson",
            content_id=test_lesson.id,
            version=1,
            data=version_data,
            editor_id=test_user.id,
            change_note="Initial version",
        )
        db_session.add(content_version)
        db_session.commit()

        assert content_version.id is not None
        assert content_version.content_type == "lesson"
        assert content_version.version == 1
        assert content_version.data == version_data
        assert content_version.editor_id == test_user.id

    def test_content_version_has_created_at(self, db_session, test_lesson, test_user):
        """Test that content version has created_at timestamp."""
        content_version = ContentVersion(
            content_type="lesson",
            content_id=test_lesson.id,
            version=1,
            data={"description": "test"},
            editor_id=test_user.id,
        )
        db_session.add(content_version)
        db_session.commit()

        assert content_version.created_at is not None
        assert isinstance(content_version.created_at, datetime)


class TestVersionSnapshotHelper:
    """Test _create_content_snapshot helper function."""

    def test_create_snapshot_for_lesson(self, db_session, test_lesson, test_user):
        """Test creating a snapshot for lesson content."""
        _create_content_snapshot(
            db_session,
            "lesson",
            test_lesson.id,
            test_lesson.version,
            test_user.id,
            "Test snapshot",
        )
        db_session.commit()

        # Query the created snapshot
        snapshot = db_session.query(ContentVersion).filter_by(
            content_type="lesson",
            content_id=test_lesson.id,
            version=test_lesson.version,
        ).first()

        assert snapshot is not None
        assert snapshot.data["description"] == test_lesson.description
        assert snapshot.change_note == "Test snapshot"

    def test_snapshot_handles_invalid_content_type(self, db_session, test_user):
        """Test that snapshot handles invalid content types gracefully."""
        # Should not raise an error, just return
        _create_content_snapshot(
            db_session,
            "invalid_type",
            uuid4(),
            1,
            test_user.id,
            "Test",
        )
        db_session.commit()

        # No snapshot should be created
        count = db_session.query(ContentVersion).filter_by(
            content_type="invalid_type"
        ).count()
        assert count == 0

