from sqlalchemy import select

from backend.models import LessonContent, User, UserRole


def _register_user(client, email, display_name):
    res = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "password123", "display_name": display_name},
    )
    assert res.status_code == 201, res.text
    return res


def test_teacher_publish_blocked(client, db_session, seeded_content):
    _register_user(client, "teacher@example.com", "Teacher")
    teacher = db_session.execute(
        select(User).where(User.email == "teacher@example.com")
    ).scalar_one()
    teacher.role = UserRole.teacher

    lesson = db_session.execute(
        select(LessonContent).where(
            LessonContent.motif_id == seeded_content["motif"].id
        )
    ).scalar_one()
    lesson.is_published = False
    db_session.commit()

    res = client.patch(
        f"/api/v1/admin/lessons/{lesson.id}",
        json={"is_published": True, "description": "Draft update"},
    )
    assert res.status_code == 403, res.text

    _register_user(client, "admin@example.com", "Admin")
    admin = db_session.execute(
        select(User).where(User.email == "admin@example.com")
    ).scalar_one()
    admin.role = UserRole.admin
    db_session.commit()

    login = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@example.com", "password": "password123"},
    )
    assert login.status_code == 200, login.text

    res = client.patch(
        f"/api/v1/admin/lessons/{lesson.id}",
        json={"is_published": True},
    )
    assert res.status_code == 200, res.text
    assert res.json()["is_published"] is True


def test_leaderboard_excludes_guests_and_sorts_by_xp(client, db_session):
    _register_user(client, "learner@example.com", "Learner")
    learner = db_session.execute(
        select(User).where(User.email == "learner@example.com")
    ).scalar_one()
    learner.total_xp = 500

    _register_user(client, "staff@example.com", "Teacher")
    staff = db_session.execute(
        select(User).where(User.email == "staff@example.com")
    ).scalar_one()
    staff.role = UserRole.teacher
    staff.total_xp = 900

    _register_user(client, "admin2@example.com", "Admin")
    admin = db_session.execute(
        select(User).where(User.email == "admin2@example.com")
    ).scalar_one()
    admin.role = UserRole.admin
    admin.total_xp = 1200

    _register_user(client, "guest@example.com", "Guest")
    guest = db_session.execute(
        select(User).where(User.email == "guest@example.com")
    ).scalar_one()
    guest.role = UserRole.guest
    guest.total_xp = 0
    db_session.commit()

    leaderboard = client.get("/api/v1/leaderboard?limit=10")
    assert leaderboard.status_code == 200, leaderboard.text
    entries = leaderboard.json()["entries"]
    # Guest users are excluded (they have no XP); non-guest users (including
    # teacher/admin roles) are ranked by XP descending. This matches the
    # leaderboard contract implemented in both the Python service and the
    # native Rust route.
    names = {entry["display_name"] for entry in entries}
    assert "Learner" in names
    assert "Teacher" in names
    assert "Admin" in names
    assert "Guest" not in names
    xp_list = [entry["total_xp"] for entry in entries]
    assert xp_list == sorted(xp_list, reverse=True)
