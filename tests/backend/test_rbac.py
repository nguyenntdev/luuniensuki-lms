from sqlalchemy import select

from backend.models import (
    LessonContent,
    NotificationStatus,
    NotificationType,
    PushNotification,
    User,
    UserLeaderboardSettings,
    UserRole,
)
from backend.services.leaderboard import get_global_leaderboard


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


def test_global_leaderboard_service_limit_and_privacy(db_session):
    u1 = User(email="u1@example.com", password_hash="hash", display_name="User1", role=UserRole.learner, total_xp=1000, current_streak=5)
    u2 = User(email="u2@example.com", password_hash="hash", display_name="User2", role=UserRole.learner, total_xp=800, current_streak=10)
    u3 = User(email="u3@example.com", password_hash="hash", display_name="User3", role=UserRole.learner, total_xp=600, current_streak=2)
    u4 = User(email="u4@example.com", password_hash="hash", display_name="User4", role=UserRole.learner, total_xp=400, current_streak=1)
    u5 = User(email="u5@example.com", password_hash="hash", display_name="User5", role=UserRole.learner, total_xp=200, current_streak=0)
    u_hidden = User(email="hidden@example.com", password_hash="hash", display_name="UserHidden", role=UserRole.learner, total_xp=9999, current_streak=99)
    u_guest = User(email="guest2@example.com", password_hash="hash", display_name="GuestUser", role=UserRole.guest, total_xp=0, current_streak=0)

    db_session.add_all([u1, u2, u3, u4, u5, u_hidden, u_guest])
    db_session.flush()

    db_session.add(UserLeaderboardSettings(user_id=u_hidden.id, show_on_global=False))
    db_session.commit()

    # Top limit=2 by XP
    entries, rank_u1, total_users = get_global_leaderboard(db_session, current_user_id=u1.id, limit=2, order_by="xp")
    assert len(entries) == 2
    assert entries[0]["user_id"] == u1.id
    assert entries[1]["user_id"] == u2.id
    assert rank_u1 == 1
    assert total_users == 5  # u1-u5 visible, u_hidden and u_guest excluded

    # User outside limit (u4 is rank 4, limit is 2)
    entries_lim2, rank_u4, total_users = get_global_leaderboard(db_session, current_user_id=u4.id, limit=2, order_by="xp")
    assert len(entries_lim2) == 2
    assert rank_u4 == 4
    assert total_users == 5

    # Order by streak (u2 has streak 10, u1 has streak 5)
    entries_streak, rank_u2_streak, _ = get_global_leaderboard(db_session, current_user_id=u2.id, limit=5, order_by="streak")
    assert entries_streak[0]["user_id"] == u2.id
    assert rank_u2_streak == 1
    assert entries_streak[1]["user_id"] == u1.id


def test_admin_list_push_notifications_pagination_and_rbac(client, db_session):
    _register_user(client, "admin_notif@example.com", "Admin Notif")
    admin = db_session.execute(
        select(User).where(User.email == "admin_notif@example.com")
    ).scalar_one()
    admin.role = UserRole.admin

    _register_user(client, "learner_notif@example.com", "Learner Notif")
    learner = db_session.execute(
        select(User).where(User.email == "learner_notif@example.com")
    ).scalar_one()

    # Seed some push notifications
    for i in range(5):
        notif = PushNotification(
            user_id=learner.id,
            title=f"Notification {i}",
            body=f"Body {i}",
            notification_type=NotificationType.system,
            status=NotificationStatus.sent,
        )
        db_session.add(notif)
    db_session.commit()

    # Learner should be forbidden (403)
    login_learner = client.post(
        "/api/v1/auth/login",
        json={"email": "learner_notif@example.com", "password": "password123"},
    )
    assert login_learner.status_code == 200
    res_learner = client.get("/api/v1/admin/push-notifications")
    assert res_learner.status_code == 403

    # Admin should get total count and paginated items
    login_admin = client.post(
        "/api/v1/auth/login",
        json={"email": "admin_notif@example.com", "password": "password123"},
    )
    assert login_admin.status_code == 200

    res = client.get("/api/v1/admin/push-notifications?limit=2&offset=0")
    assert res.status_code == 200, res.text
    data = res.json()
    assert data["total"] == 5
    assert len(data["notifications"]) == 2
    assert data["limit"] == 2
    assert data["offset"] == 0

    # Test filtering by user_id
    res_filter = client.get(f"/api/v1/admin/push-notifications?user_id={learner.id}")
    assert res_filter.status_code == 200
    assert res_filter.json()["total"] == 5
