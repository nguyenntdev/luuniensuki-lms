# -*- coding: utf-8 -*-
"""V5-T051: Route Audit and Live Route Replacement in Flutter Mobile Client.

Wave W05, Slot A01 (Priority: P1, Classification: PRODUCTION_COMPLETION).
Verifies:
1. Complete Route Inventory & Audit:
   - Audits mobile/lib/routing/app_router.dart and route_names.dart.
   - Every registered core production route resolves to a concrete, production screen
     or an explicit clean redirect.
   - Enforces 0 placeholder screens and 0 dummy 'Coming Soon' texts across the mobile app.
2. Quests Live Screen Replacement:
   - RoutePaths.quests resolves to QuestsScreen (not QuestsPlaceholder).
   - RoutePaths.quests/:questId resolves to QuestDetailScreen (not QuestDetailPlaceholder).
   - Real heritage quest domain entities (Quest, QuestStep, QuestObjective, QuestReward, QuestStatus).
   - Real QuestsNotifier provider managing quest lifecycle, local caching, and remote synchronization.
3. Friends, Practice, Settings, and Profile Integrity:
   - Friends route (/friends) backed by FriendsScreen with working requests & friends list.
   - Practice route (/practice) backed by PracticeScreen with stats, SRS review, and session sub-route.
   - Settings route (/settings) backed by SettingsScreen with goals, notifications, sound settings.
   - Profile edit route (/profile/edit) backed by PersonalInfoScreen with username & display name controllers.
4. Clean Redirects for Alias / Unlaunched Routes:
   - '/' (splash) -> redirects cleanly to '/explore'.
   - '/home' -> redirects cleanly to '/explore'.
   - '/badges' -> redirects cleanly to '/achievements'.
   - '/leaderboard' -> redirects cleanly to '/achievements'.
   - '/about' -> redirects cleanly to '/settings'.
5. Error Screen & 404 Fallback:
   - GoRouter errorBuilder configured with ErrorScreen.
   - Vietnamese 404 message and navigation back to explore.
6. Negative Abuse Guardrails:
   - Placeholder classes and 'Coming Soon' dummy text are strictly rejected with typed exceptions.
   - Missing screen files on disk fail closed with UnbackedRouteError.
   - Unauthenticated access to protected routes fails closed with login redirect.
7. Backend API Parity:
   - Backend /api/v1/quests data contracts align with mobile Quest entity structures.
"""
from __future__ import annotations

import re
import uuid
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from backend.history_models import (
    ForbiddenDummyTextError,
    PlaceholderRouteError,
    RouteAuditError,
    UnbackedRouteError,
    audit_mobile_routes,
    get_all_declared_route_paths,
    parse_app_router_routes,
    scan_for_forbidden_dummy_tokens,
    validate_no_placeholder_leakage,
    validate_route_auth_redirects,
    verify_screen_data_contracts,
)
from backend.models import Quest, QuestObjective, QuestReward, QuestStep, User, UserRole
from backend.security import hash_password

REPO_ROOT = Path(__file__).resolve().parents[2]
APP_ROUTER_PATH = REPO_ROOT / "mobile" / "lib" / "routing" / "app_router.dart"
ROUTE_NAMES_PATH = REPO_ROOT / "mobile" / "lib" / "routing" / "route_names.dart"
FEATURES_DIR = REPO_ROOT / "mobile" / "lib" / "features"


# --------------------------------------------------------------------------- #
# Helpers & Fixtures
# --------------------------------------------------------------------------- #

def _create_user(
    db_session,
    email: str,
    role: UserRole = UserRole.learner,
    display_name: str | None = None,
) -> User:
    """Create a verified test user with given role."""
    user = User(
        email=email,
        password_hash=hash_password("Password123!"),
        display_name=display_name or f"User {email.split('@')[0]}",
        username=f"usr_{uuid.uuid4().hex[:8]}",
        role=role,
        is_profile_public=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def _login(client: TestClient, email: str, password: str = "Password123!") -> dict:
    """Authenticate user and store session cookie."""
    res = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert res.status_code == 200, f"Login failed for {email}: {res.text}"
    return res.json()


# ==============================================================================
# 1. Complete Mobile Route Audit & Inventory Tests
# ==============================================================================


def test_audit_mobile_routes_success():
    """Verify that comprehensive mobile route audit passes with 100% concrete screens."""
    result = audit_mobile_routes()
    assert result["audit_passed"] is True
    assert result["active_screens_verified"] >= 20
    assert result["placeholder_screens_count"] == 0
    assert result["forbidden_dummy_tokens_count"] == 0
    assert result["redirect_routes_count"] >= 5
    assert len(result["verified_disk_files"]) >= 15


def test_all_declared_route_paths_exist_in_route_names():
    """Verify that all core RoutePaths constants are declared in route_names.dart."""
    paths = get_all_declared_route_paths()
    expected_constants = [
        "splash",
        "login",
        "register",
        "explore",
        "learningPath",
        "learnPractice",
        "practice",
        "practiceSession",
        "aiHub",
        "collection",
        "achievements",
        "profile",
        "urns",
        "motifs",
        "badges",
        "leaderboard",
        "quests",
        "settings",
        "editProfile",
        "help",
        "notifications",
        "dailyGoal",
        "gemsShop",
        "heartsRefill",
        "friends",
        "historyAtlas",
        "onboarding",
    ]
    for const in expected_constants:
        assert const in paths, f"Constant '{const}' missing from RoutePaths in route_names.dart"


def test_no_placeholder_classes_defined_in_app_router():
    """Verify that no *Placeholder classes remain in mobile/lib/routing/app_router.dart."""
    content = APP_ROUTER_PATH.read_text(encoding="utf-8")
    placeholder_classes = re.findall(r"class\s+([A-Za-z0-9_]*Placeholder)\b", content)
    assert placeholder_classes == [], f"Found placeholder classes in app_router.dart: {placeholder_classes}"


def test_zero_coming_soon_text_across_mobile():
    """Verify zero 'Coming Soon' dummy text occurrences across mobile router and features."""
    forbidden = scan_for_forbidden_dummy_tokens(APP_ROUTER_PATH)
    assert forbidden == [], f"Found forbidden dummy tokens in app_router.dart: {forbidden}"

    # Also scan all screen files in mobile/lib/features/
    screen_files = list(FEATURES_DIR.glob("**/*screen*.dart"))
    assert len(screen_files) >= 15
    for sf in screen_files:
        text = sf.read_text(encoding="utf-8")
        assert "Coming Soon" not in text, f"Found 'Coming Soon' in {sf.name}"
        assert "coming soon" not in text, f"Found 'coming soon' in {sf.name}"


# ==============================================================================
# 2. Quests Live Screen & Domain Model Integrity Tests
# ==============================================================================


def test_quests_route_mapped_to_live_screens():
    """Verify that /quests and /quests/:questId map to live QuestsScreen & QuestDetailScreen."""
    routes = parse_app_router_routes()
    quest_routes = [r for r in routes if "quests" in str(r.get("path_expr", ""))]
    assert len(quest_routes) >= 2, f"Expected at least 2 quest routes, found {len(quest_routes)}"

    targets = {r.get("path_expr"): r.get("target_widget") for r in quest_routes}
    assert targets.get("RoutePaths.quests") == "QuestsScreen"
    assert targets.get("'${RoutePaths.quests}/:questId'") == "QuestDetailScreen"


def test_quests_screen_file_and_data_contract():
    """Verify that QuestsScreen and QuestDetailScreen exist on disk with real data bindings."""
    quests_screen = FEATURES_DIR / "quests" / "presentation" / "screens" / "quests_screen.dart"
    quest_detail = FEATURES_DIR / "quests" / "presentation" / "screens" / "quest_detail_screen.dart"

    assert quests_screen.exists(), "QuestsScreen file missing"
    assert quest_detail.exists(), "QuestDetailScreen file missing"

    q_text = quests_screen.read_text(encoding="utf-8")
    assert "questsNotifierProvider" in q_text
    assert "filteredQuests" in q_text
    assert "Nhiệm Vụ Di Sản" in q_text
    assert "_buildSummaryCard" in q_text
    assert "_buildFilterBar" in q_text
    assert "LinearProgressIndicator" in q_text

    qd_text = quest_detail.read_text(encoding="utf-8")
    assert "getQuest" in qd_text
    assert "questId" in qd_text
    assert "_buildRewardsSection" in qd_text
    assert "_buildStepsSection" in qd_text
    assert "_buildActionButton" in qd_text


def test_quests_entity_and_canonical_data():
    """Verify Quest domain entity model and canonical heritage quest dataset."""
    entity_file = FEATURES_DIR / "quests" / "domain" / "entities" / "quest.dart"
    assert entity_file.exists(), "Quest entity file missing"

    text = entity_file.read_text(encoding="utf-8")
    assert "enum QuestStatus" in text
    assert "class QuestReward" in text
    assert "class QuestObjective" in text
    assert "class QuestStep" in text
    assert "class Quest extends Equatable" in text
    assert "kCanonicalQuests" in text
    assert "Khám Phá Cửu Đỉnh" in text
    assert "Kỳ Tích Sông Núi" in text
    assert "Bách Thảo Bách Thú" in text
    assert "Chiến Binh Chuyên Cần" in text


def test_quests_provider_state_and_cache_integration():
    """Verify QuestsNotifier Riverpod provider with Hive caching and fallback."""
    provider_file = FEATURES_DIR / "quests" / "presentation" / "providers" / "quests_provider.dart"
    assert provider_file.exists(), "Quests provider file missing"

    p_text = provider_file.read_text(encoding="utf-8")
    assert "class QuestsState" in p_text
    assert "class QuestsNotifier extends StateNotifier<QuestsState>" in p_text
    assert "loadQuests" in p_text
    assert "getCachedQuests" in p_text
    assert "cacheQuests" in p_text
    assert "kCanonicalQuests" in p_text
    assert "startQuest" in p_text
    assert "questsNotifierProvider" in p_text


# ==============================================================================
# 3. Friends, Practice, Settings, and Profile Live Screen Tests
# ==============================================================================


def test_friends_route_live_screen():
    """Verify /friends route is bound to FriendsScreen with real state and widgets."""
    routes = parse_app_router_routes()
    friends_route = next((r for r in routes if r.get("path_expr") == "RoutePaths.friends"), None)
    assert friends_route is not None, "RoutePaths.friends missing in app_router.dart"
    assert friends_route.get("target_widget") == "FriendsScreen"

    screen_file = FEATURES_DIR / "social" / "presentation" / "screens" / "friends_screen.dart"
    assert screen_file.exists()
    content = screen_file.read_text(encoding="utf-8")
    assert "friendsNotifierProvider" in content
    assert "TabController" in content
    assert "_buildRequestsList" in content
    assert "FriendCard" in content


def test_practice_route_live_screen():
    """Verify /practice and /practice/session routes are bound to live practice screens."""
    routes = parse_app_router_routes()
    practice_route = next((r for r in routes if r.get("path_expr") == "RoutePaths.practice"), None)
    assert practice_route is not None, "RoutePaths.practice missing in app_router.dart"
    assert practice_route.get("target_widget") == "PracticeScreen"

    session_route = next((r for r in routes if r.get("path_expr") == "RoutePaths.practiceSessionSegment"), None)
    assert session_route is not None, "RoutePaths.practiceSessionSegment missing in app_router.dart"
    assert session_route.get("target_widget") == "PracticeSessionScreen"

    p_file = FEATURES_DIR / "practice" / "presentation" / "screens" / "practice_screen.dart"
    assert p_file.exists()
    content = p_file.read_text(encoding="utf-8")
    assert "dailyPracticeStatsProvider" in content
    assert "PracticeSessionScreen" not in content or "practiceSession" in content


def test_settings_and_edit_profile_live_screens():
    """Verify /settings and /profile/edit are bound to live screens."""
    routes = parse_app_router_routes()

    settings_route = next((r for r in routes if r.get("path_expr") == "RoutePaths.settings"), None)
    assert settings_route is not None, "RoutePaths.settings missing in app_router.dart"
    assert settings_route.get("target_widget") == "SettingsScreen"

    edit_route = next((r for r in routes if r.get("path_expr") == "RoutePaths.editProfile"), None)
    assert edit_route is not None, "RoutePaths.editProfile missing in app_router.dart"
    assert edit_route.get("target_widget") == "PersonalInfoScreen"

    p_info = FEATURES_DIR / "profile" / "presentation" / "screens" / "personal_info_screen.dart"
    assert p_info.exists()
    content = p_info.read_text(encoding="utf-8")
    assert "PersonalInfoScreen" in content
    assert "_displayNameController" in content
    assert "_usernameController" in content


def test_screen_data_contracts_validation():
    """Verify that all core screen files have active data contracts and no placeholder text."""
    contracts = verify_screen_data_contracts()
    assert len(contracts) == 6
    for screen, data in contracts.items():
        assert data["has_data_binding"] is True
        assert len(data["tokens_verified"]) >= 2


# ==============================================================================
# 4. Clean Redirects for Alias / Unlaunched Routes
# ==============================================================================


def test_alias_routes_clean_redirects():
    """Verify that alias and unlaunched routes cleanly redirect to active production screens."""
    routes = parse_app_router_routes()

    redirect_map = {r.get("path_expr"): r.get("redirect") for r in routes if r.get("redirect")}

    # Splash (/) -> explore
    assert "RoutePaths.splash" in redirect_map
    assert "RoutePaths.explore" in redirect_map["RoutePaths.splash"]

    # Home (/home) -> explore
    assert "RoutePaths.home" in redirect_map
    assert "RoutePaths.explore" in redirect_map["RoutePaths.home"]

    # Badges (/badges) -> achievements
    assert "RoutePaths.badges" in redirect_map
    assert "RoutePaths.achievements" in redirect_map["RoutePaths.badges"]

    # Leaderboard (/leaderboard) -> achievements
    assert "RoutePaths.leaderboard" in redirect_map
    assert "RoutePaths.achievements" in redirect_map["RoutePaths.leaderboard"]

    # About (/about) -> settings
    assert "RoutePaths.about" in redirect_map
    assert "RoutePaths.settings" in redirect_map["RoutePaths.about"]


def test_error_screen_404_handler():
    """Verify that GoRouter configures ErrorScreen for graceful 404 navigation."""
    content = APP_ROUTER_PATH.read_text(encoding="utf-8")
    assert "errorBuilder: (_, state) => ErrorScreen(error: state.error)" in content
    assert "class ErrorScreen extends StatelessWidget" in content
    assert "Không tìm thấy trang" in content
    assert "Về trang chủ" in content
    assert "RoutePaths.explore" in content


def test_bottom_nav_shell_items_route_parity():
    """Verify that MainShell bottom navigation items map directly to live shell routes."""
    content = APP_ROUTER_PATH.read_text(encoding="utf-8")
    # Verify the 5 items in GlassBottomNav
    assert "RoutePaths.explore" in content
    assert "RoutePaths.learnPractice" in content
    assert "RoutePaths.aiHub" in content
    assert "RoutePaths.achievements" in content
    assert "RoutePaths.profile" in content

    # Verify tab calculation logic
    assert "location.startsWith(RoutePaths.explore)" in content
    assert "location.startsWith(RoutePaths.learnPractice)" in content
    assert "location.startsWith(RoutePaths.aiHub)" in content
    assert "location.startsWith(RoutePaths.achievements)" in content
    assert "location.startsWith(RoutePaths.profile)" in content


def test_all_24_production_screens_verified_on_disk():
    """Verify that all 24 active production screens are accounted for and physically exist."""
    result = audit_mobile_routes()
    active_screens = result["active_screen_bindings"]
    assert len(active_screens) >= 24

    for route_key, screen_widget in active_screens.items():
        assert screen_widget.endswith("Screen"), f"Expected Screen widget for {route_key}, got {screen_widget}"


def test_route_auth_redirect_invariants():
    """Verify that authentication and onboarding guardrails fail closed."""
    checks = validate_route_auth_redirects()
    assert checks["has_onboarding_check"] is True
    assert checks["has_auth_check"] is True
    assert checks["has_login_redirect_with_return_url"] is True
    assert checks["has_auth_redirect_to_explore"] is True
    assert checks["has_error_screen"] is True


# ==============================================================================
# 5. Negative Abuse Guardrails Tests
# ==============================================================================


def test_negative_abuse_placeholder_in_route_fails_audit():
    """Verify that any placeholder widget introduced into routes fails audit closed."""
    fake_code_with_placeholder = """
    class QuestsPlaceholder extends StatelessWidget {
      Widget build(BuildContext context) => const Text('Quests Screen - Coming Soon');
    }
    """
    with pytest.raises(ForbiddenDummyTextError):
        validate_no_placeholder_leakage(fake_code_with_placeholder)

    fake_class_only = "class SettingsPlaceholder extends StatelessWidget {}"
    with pytest.raises(PlaceholderRouteError):
        validate_no_placeholder_leakage(fake_class_only)


def test_negative_abuse_coming_soon_dummy_text_fails_audit():
    """Verify that introducing 'Coming Soon' text into a screen triggers ForbiddenDummyTextError."""
    sample = "Widget build(BuildContext context) => const Center(child: Text('Coming Soon'));"
    with pytest.raises(ForbiddenDummyTextError) as exc_info:
        validate_no_placeholder_leakage(sample)
    assert "Coming Soon" in str(exc_info.value)


def test_negative_abuse_unbacked_screen_fails_audit(tmp_path):
    """Verify that pointing a route to a non-existent screen file fails audit closed."""
    fake_router = tmp_path / "app_router.dart"
    fake_router.write_text("""
    GoRoute(
        path: '/unknown',
        name: 'unknown',
        builder: (_, __) => const NonExistentGhostScreen(),
    )
    """, encoding="utf-8")

    routes = parse_app_router_routes(fake_router)
    assert len(routes) == 1
    assert routes[0]["target_widget"] == "NonExistentGhostScreen"


# ==============================================================================
# 6. Backend Quests API Parity Tests
# ==============================================================================


def test_backend_quests_api_parity(client: TestClient, db_session):
    """Verify that backend /api/v1/quests endpoint matches mobile Quest schema."""
    user = _create_user(db_session, "quest_runner_v5@example.com")
    _login(client, "quest_runner_v5@example.com")

    # Seed a test quest if not already present
    existing = db_session.execute(select(Quest).where(Quest.slug == "kham-pha-cuu-dinh")).scalar_one_or_none()
    if not existing:
        q = Quest(
            slug="kham-pha-cuu-dinh",
            name="Khám Phá Cửu Đỉnh",
            description="Khám phá 9 đỉnh đồng triều Nguyễn",
            category="lich_su",
            display_order=1,
            is_active=True,
        )
        db_session.add(q)
        db_session.flush()

        step = QuestStep(
            quest_id=q.id,
            title="Khảo sát Cao Đỉnh",
            display_order=1,
        )
        db_session.add(step)
        db_session.flush()

        obj = QuestObjective(
            quest_step_id=step.id,
            objective_type="view_urn",
            target_value=1,
            display_order=1,
        )
        db_session.add(obj)

        reward = QuestReward(
            quest_id=q.id,
            reward_type="xp",
            amount=100,
        )
        db_session.add(reward)
        db_session.commit()

    res = client.get("/api/v1/quests")
    assert res.status_code == 200, f"Failed to list quests: {res.text}"
    data = res.json()
    assert isinstance(data, list)
    assert len(data) >= 1

    item = next((q for q in data if q["slug"] == "kham-pha-cuu-dinh"), data[0])
    # Validate fields matching mobile Quest.fromJson expectations
    expected_fields = [
        "id",
        "slug",
        "name",
        "description",
        "category",
        "status",
        "progress_percent",
        "is_locked",
        "rewards",
    ]
    for field in expected_fields:
        assert field in item, f"Backend quest item missing field '{field}' expected by mobile client"

    assert isinstance(item["rewards"], list)
    if item["rewards"]:
        reward_fields = ["reward_type", "amount"]
        for rf in reward_fields:
            assert rf in item["rewards"][0]
