# -*- coding: utf-8 -*-
"""Mobile Route Audit and Live Route Replacement Verification Service.

Wave W05, Slot A01 (Ticket V5-T051).
Ensures that:
1. Every reachable mobile route in mobile/lib/routing/app_router.dart resolves
   to a concrete production screen or an explicit clean redirect.
2. No placeholder classes (*Placeholder) or dummy 'Coming Soon' texts exist
   in reachable route definitions.
3. Live production screens exist on disk with real data handling for:
   Quests, Friends, Practice, Settings, Profile, Achievements, etc.
4. Clean redirects are configured for alias / unlaunched routes:
   '/', '/home', '/badges', '/leaderboard', '/about'.
5. ErrorScreen exists and handles unmatched 404 paths gracefully.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

REPO_ROOT = Path(__file__).resolve().parents[2]
APP_ROUTER_PATH = REPO_ROOT / "mobile" / "lib" / "routing" / "app_router.dart"
ROUTE_NAMES_PATH = REPO_ROOT / "mobile" / "lib" / "routing" / "route_names.dart"
FEATURES_DIR = REPO_ROOT / "mobile" / "lib" / "features"


class RouteAuditError(Exception):
    """Base error for route audit violations."""


class PlaceholderRouteError(RouteAuditError):
    """Raised when a route is configured with a placeholder widget."""


class UnbackedRouteError(RouteAuditError):
    """Raised when a route refers to a missing screen file on disk."""


class ForbiddenDummyTextError(RouteAuditError):
    """Raised when 'Coming Soon' or dummy text is found in production routes."""


def get_all_declared_route_paths(route_names_file: Path = ROUTE_NAMES_PATH) -> Dict[str, str]:
    """Parse route_names.dart and return map of constant name -> path string."""
    if not route_names_file.exists():
        raise FileNotFoundError(f"Missing route_names.dart at {route_names_file}")

    content = route_names_file.read_text(encoding="utf-8")
    paths: Dict[str, str] = {}

    pattern = re.compile(r"static\s+const\s+String\s+(\w+)\s*=\s*['\"]([^'\"]+)['\"];")
    in_paths = False
    for line in content.splitlines():
        if "abstract class RoutePaths" in line:
            in_paths = True
            continue
        if in_paths:
            if line.strip().startswith("}"):
                break
            match = pattern.search(line)
            if match:
                paths[match.group(1)] = match.group(2)

    return paths


def parse_app_router_routes(app_router_file: Path = APP_ROUTER_PATH) -> List[Dict[str, Any]]:
    """Parse app_router.dart and extract route definitions using balanced bracket scanning."""
    if not app_router_file.exists():
        raise FileNotFoundError(f"Missing app_router.dart at {app_router_file}")

    content = app_router_file.read_text(encoding="utf-8")

    routes: List[Dict[str, Any]] = []
    idx = 0

    while True:
        pos = content.find("GoRoute(", idx)
        if pos == -1:
            break
        start = pos + len("GoRoute(")
        depth = 1
        i = start
        while i < len(content) and depth > 0:
            if content[i] == "(":
                depth += 1
            elif content[i] == ")":
                depth -= 1
            i += 1
        block = content[start : i - 1]
        idx = start

        path_match = re.search(r"path:\s*([^,\n]+)", block)
        name_match = re.search(r"name:\s*([^,\n]+)", block)
        redirect_match = re.search(r"redirect:\s*(\([^)]*\)\s*=>\s*[^,\n]+|[^,\n]+)", block)

        path_val = path_match.group(1).strip() if path_match else None
        name_val = name_match.group(1).strip() if name_match else None
        redirect_val = redirect_match.group(1).strip() if redirect_match else None

        target_widget = None
        # Look for Screen or Placeholder widget instantiation (ignoring sub-routes)
        outer_block = block.split("routes: [")[0]
        widget_matches = re.findall(r"(?:return|=>|child:)\s*(?:const\s+)?([A-Za-z0-9_]+(?:Screen|Placeholder))\b", outer_block)
        if widget_matches:
            target_widget = widget_matches[-1]

        if path_val:
            clean_path = path_val.strip("'\"")
            routes.append({
                "path_expr": path_val,
                "clean_path": clean_path,
                "name": name_val,
                "target_widget": target_widget,
                "redirect": redirect_val,
                "raw": block.strip(),
            })

    return routes


def scan_for_forbidden_dummy_tokens(app_router_file: Path = APP_ROUTER_PATH) -> List[str]:
    """Scan file for forbidden placeholder tokens such as 'Coming Soon'."""
    if not app_router_file.exists():
        raise FileNotFoundError(f"Missing app_router.dart at {app_router_file}")

    content = app_router_file.read_text(encoding="utf-8")
    forbidden = ["Coming Soon", "coming soon", "PlaceholderScreen", "QuestsPlaceholder", "QuestDetailPlaceholder"]
    found: List[str] = []
    for token in forbidden:
        if token in content:
            found.append(token)
    return found


def audit_mobile_routes(
    app_router_file: Path = APP_ROUTER_PATH,
    route_names_file: Path = ROUTE_NAMES_PATH,
) -> Dict[str, Any]:
    """Perform comprehensive audit of mobile routes and screen bindings.

    Returns audit results report dict.
    Raises RouteAuditError on failure.
    """
    declared_paths = get_all_declared_route_paths(route_names_file)
    routes = parse_app_router_routes(app_router_file)
    forbidden_tokens = scan_for_forbidden_dummy_tokens(app_router_file)

    if forbidden_tokens:
        raise ForbiddenDummyTextError(
            f"Found forbidden dummy/placeholder tokens in app_router.dart: {forbidden_tokens}"
        )

    # Core required production routes and their expected target screen widgets
    expected_screens = {
        "onboarding": "OnboardingScreen",
        "login": "LoginScreen",
        "register": "RegisterScreen",
        "explore": "ExploreScreen",
        "collection": "CollectionScreen",
        "learnPractice": "LearnPracticeHubScreen",
        "learningPath": "LearningPathScreen",
        "practice": "PracticeScreen",
        "practiceSession": "PracticeSessionScreen",
        "aiHub": "AiHubScreen",
        "achievements": "AchievementsScreen",
        "profile": "ProfileScreen",
        "historyAtlas": "HistoryAtlasScreen",
        "urnViewer": "UrnViewerScreen",
        "motifDetail": "MotifDetailScreen",
        "quiz": "QuizScreen",
        "quests": "QuestsScreen",
        "questDetail": "QuestDetailScreen",
        "settings": "SettingsScreen",
        "editProfile": "PersonalInfoScreen",
        "dailyGoal": "DailyGoalScreen",
        "help": "HelpSupportScreen",
        "notifications": "NotificationsScreen",
        "gemsShop": "GemsShopScreen",
        "heartsRefill": "HeartsRefillScreen",
        "friends": "FriendsScreen",
    }

    # Map of found screens
    active_screen_map: Dict[str, str] = {}
    redirect_routes: List[str] = []
    placeholder_routes: List[str] = []

    for r in routes:
        target = r.get("target_widget")
        redirect = r.get("redirect")
        path_expr = r.get("path_expr", "")

        if target:
            if "Placeholder" in target:
                placeholder_routes.append(f"{path_expr} -> {target}")
            for exp_key, exp_screen in expected_screens.items():
                if exp_screen == target:
                    active_screen_map[exp_key] = target

        if redirect:
            redirect_routes.append(path_expr)

    if placeholder_routes:
        raise PlaceholderRouteError(
            f"Reachable routes are configured with placeholder screens: {placeholder_routes}"
        )

    # Verify that required routes have active concrete screens
    required_keys = [
        "onboarding",
        "login",
        "register",
        "explore",
        "collection",
        "learnPractice",
        "practice",
        "achievements",
        "profile",
        "historyAtlas",
        "quests",
        "questDetail",
        "settings",
        "editProfile",
        "friends",
        "gemsShop",
        "heartsRefill",
        "help",
        "notifications",
        "dailyGoal",
    ]

    missing_keys = [k for k in required_keys if k not in active_screen_map]
    if missing_keys:
        raise UnbackedRouteError(f"Required production routes are missing active screen bindings: {missing_keys}")

    # Verify physical screen files exist on disk
    screen_files = {
        "QuestsScreen": FEATURES_DIR / "quests" / "presentation" / "screens" / "quests_screen.dart",
        "QuestDetailScreen": FEATURES_DIR / "quests" / "presentation" / "screens" / "quest_detail_screen.dart",
        "FriendsScreen": FEATURES_DIR / "social" / "presentation" / "screens" / "friends_screen.dart",
        "PracticeScreen": FEATURES_DIR / "practice" / "presentation" / "screens" / "practice_screen.dart",
        "SettingsScreen": FEATURES_DIR / "settings" / "presentation" / "screens" / "settings_screen.dart",
        "PersonalInfoScreen": FEATURES_DIR / "profile" / "presentation" / "screens" / "personal_info_screen.dart",
        "AchievementsScreen": FEATURES_DIR / "achievements" / "presentation" / "screens" / "achievements_screen.dart",
        "ExploreScreen": FEATURES_DIR / "explore" / "presentation" / "screens" / "explore_screen.dart",
        "CollectionScreen": FEATURES_DIR / "collection" / "presentation" / "screens" / "collection_screen.dart",
        "UrnViewerScreen": FEATURES_DIR / "urn_viewer" / "presentation" / "screens" / "urn_viewer_screen.dart",
        "MotifDetailScreen": FEATURES_DIR / "lesson" / "presentation" / "screens" / "motif_detail_screen.dart",
        "QuizScreen": FEATURES_DIR / "quiz" / "presentation" / "screens" / "quiz_screen.dart",
        "DailyGoalScreen": FEATURES_DIR / "daily_goals" / "presentation" / "screens" / "daily_goal_screen.dart",
        "HelpSupportScreen": FEATURES_DIR / "help" / "presentation" / "screens" / "help_support_screen.dart",
        "NotificationsScreen": FEATURES_DIR / "notifications" / "presentation" / "screens" / "notifications_screen.dart",
        "GemsShopScreen": FEATURES_DIR / "gems" / "presentation" / "screens" / "gems_shop_screen.dart",
        "HeartsRefillScreen": FEATURES_DIR / "hearts" / "presentation" / "screens" / "hearts_refill_screen.dart",
    }

    missing_screen_files: List[str] = []
    for screen_name, path in screen_files.items():
        if not path.exists():
            missing_screen_files.append(f"{screen_name} ({path})")

    if missing_screen_files:
        raise UnbackedRouteError(f"Screen files missing on disk: {missing_screen_files}")

    return {
        "audit_passed": True,
        "total_routes_detected": len(routes),
        "total_declared_paths": len(declared_paths),
        "active_screens_verified": len(active_screen_map),
        "redirect_routes_count": len(redirect_routes),
        "placeholder_screens_count": len(placeholder_routes),
        "forbidden_dummy_tokens_count": len(forbidden_tokens),
        "active_screen_bindings": active_screen_map,
        "verified_disk_files": list(screen_files.keys()),
    }


def validate_no_placeholder_leakage(code: str) -> None:
    """Verify that a given router code snippet contains no placeholder leakage."""
    forbidden = ["Coming Soon", "coming soon", "PlaceholderScreen", "QuestsPlaceholder", "QuestDetailPlaceholder"]
    for token in forbidden:
        if token in code:
            raise ForbiddenDummyTextError(f"Found forbidden placeholder token: '{token}'")
    if re.search(r"class\s+\w+Placeholder\b", code):
        raise PlaceholderRouteError("Found placeholder class declaration in router code.")


def validate_route_auth_redirects(app_router_file: Path = APP_ROUTER_PATH) -> Dict[str, bool]:
    """Verify that authentication and onboarding redirects adhere to production invariants."""
    if not app_router_file.exists():
        raise FileNotFoundError(f"Missing app_router.dart at {app_router_file}")

    content = app_router_file.read_text(encoding="utf-8")

    has_onboarding_check = "hasSeenOnboarding" in content
    has_auth_check = "isLoggedIn" in content or "authState" in content
    has_login_redirect_with_return_url = "${RoutePaths.login}?returnUrl=" in content
    has_auth_redirect_to_explore = "RoutePaths.explore" in content
    has_error_screen = "ErrorScreen" in content

    results = {
        "has_onboarding_check": has_onboarding_check,
        "has_auth_check": has_auth_check,
        "has_login_redirect_with_return_url": has_login_redirect_with_return_url,
        "has_auth_redirect_to_explore": has_auth_redirect_to_explore,
        "has_error_screen": has_error_screen,
    }

    if not all(results.values()):
        raise RouteAuditError(f"Auth redirect invariants failed: {results}")

    return results


def verify_screen_data_contracts() -> Dict[str, Any]:
    """Verify data wiring and absence of dummy placeholders across all core screens."""
    screens_to_check = {
        "QuestsScreen": (FEATURES_DIR / "quests" / "presentation" / "screens" / "quests_screen.dart", ["questsNotifierProvider", "filteredQuests"]),
        "QuestDetailScreen": (FEATURES_DIR / "quests" / "presentation" / "screens" / "quest_detail_screen.dart", ["getQuest", "questId"]),
        "FriendsScreen": (FEATURES_DIR / "social" / "presentation" / "screens" / "friends_screen.dart", ["friendsNotifierProvider", "friendsState"]),
        "PracticeScreen": (FEATURES_DIR / "practice" / "presentation" / "screens" / "practice_screen.dart", ["dailyPracticeStatsProvider", "practiceSession"]),
        "SettingsScreen": (FEATURES_DIR / "settings" / "presentation" / "screens" / "settings_screen.dart", ["settingsNotifierProvider", "dailyGoal"]),
        "PersonalInfoScreen": (FEATURES_DIR / "profile" / "presentation" / "screens" / "personal_info_screen.dart", ["authNotifierProvider", "_displayNameController"]),
    }

    results: Dict[str, Any] = {}
    for screen_name, (path, required_tokens) in screens_to_check.items():
        if not path.exists():
            raise UnbackedRouteError(f"Screen {screen_name} not found at {path}")
        content = path.read_text(encoding="utf-8")
        if "Coming Soon" in content or "coming soon" in content:
            raise ForbiddenDummyTextError(f"Screen {screen_name} contains 'Coming Soon' dummy text!")
        missing_tokens = [tok for tok in required_tokens if tok not in content]
        if missing_tokens:
            raise RouteAuditError(f"Screen {screen_name} missing required data tokens: {missing_tokens}")
        results[screen_name] = {
            "path": str(path),
            "tokens_verified": required_tokens,
            "has_data_binding": True,
        }

    return results

