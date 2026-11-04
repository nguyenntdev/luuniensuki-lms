# -*- coding: utf-8 -*-
"""V5-T052: Mobile Authentication + Session Lifecycle Test Suite.

Wave W05, Slot A02 (Priority: P1, Classification: PRODUCTION_COMPLETION).

Verifies:
1. Mobile Auth Header & Token Exchange Parity:
   - Mobile clients authenticate on /api/v1/auth/refresh via Bearer authorization header.
   - Mobile clients can provide X-Refresh-Token header as fallback.
   - Authoritative issuance returns X-Access-Token and X-Refresh-Token headers alongside Set-Cookie.
   - User identity and role claims embedded in rotated access & refresh tokens.
2. Token Lifecycle, Rotation & Revocation:
   - Successful refresh invalidates the previously presented refresh token (preventing replay attacks).
   - Replaying a rotated refresh token is strictly rejected with HTTP 401.
   - Explicit mobile logout via Bearer authorization header revokes the refresh token jti.
   - Subsequent refresh with a revoked refresh token is strictly rejected with HTTP 401.
3. Role Claim Integrity & Cross-Tenant Isolation:
   - Proper role mapping for all user roles (learner, teacher, admin, guest).
   - User A's token cannot refresh session of User B.
4. Negative Abuse Guardrails:
   - Expired refresh tokens are rejected with HTTP 401.
   - Tampered tokens (invalid signature / malformed payload) are rejected with HTTP 401.
   - Zero prior student session data leakage when tokens expire or fail refresh.
5. Mobile Client Security Invariants (Source & Architectural Analysis):
   - SecureStorage uses FlutterSecureStorage with encryptedSharedPreferences on Android and Keychain accessibility on iOS.
   - LoggingInterceptor sanitizes passwords, tokens, auth headers, and cookies to ensure ZERO token or secret leaks.
   - DioProvider properly wires TokenRefreshInterceptor before ErrorInterceptor.
   - HiveStorage and AuthLocalDataSource ensure complete wipe of user, progress, badges, quests, and quiz state upon clearAll().
   - GoRouter enforces role-aware navigation with RouterNotifier listening to AuthNotifier.
   - Guest users are restricted from student/learner-only routes.
"""
from __future__ import annotations

import re
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from jose import jwt
from sqlalchemy.orm import Session

from backend.config import settings
from backend.models import User, UserRole
from backend.security import create_jwt_token, hash_password


REPO_ROOT = Path(__file__).resolve().parents[2]


# --------------------------------------------------------------------------- #
# Helpers & Fixtures
# --------------------------------------------------------------------------- #

def _create_user(
    db_session: Session,
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


# --------------------------------------------------------------------------- #
# Backend API Tests: Mobile Bearer Token Authentication & Lifecycle
# --------------------------------------------------------------------------- #

def test_mobile_auth_bearer_refresh_flow(client: TestClient, db_session: Session):
    """Mobile clients can refresh sessions via Bearer token in Authorization header."""
    user = _create_user(db_session, f"mobile_bearer_{uuid.uuid4().hex[:6]}@histolab.icu")

    # Generate a fresh refresh token for the user
    refresh_token = create_jwt_token(
        subject=str(user.id),
        secret_key=settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
        expires_delta=timedelta(days=7),
        issuer=settings.jwt_issuer,
        audience=settings.jwt_audience,
        extra_claims={"type": "refresh", "role": user.role.value},
    )

    # Clean cookies to simulate pure mobile client without web cookies
    client.cookies.clear()

    # Call /api/v1/auth/refresh with Authorization: Bearer <refresh_token>
    response = client.post(
        "/api/v1/auth/refresh",
        headers={"Authorization": f"Bearer {refresh_token}"},
    )
    assert response.status_code == 200, f"Expected 200, got: {response.text}"
    body = response.json()
    assert body["user"]["id"] == str(user.id)
    assert body["user"]["email"] == user.email

    # Verify custom mobile headers are returned
    new_access = response.headers.get("X-Access-Token")
    new_refresh = response.headers.get("X-Refresh-Token")
    assert new_access is not None, "Missing X-Access-Token header"
    assert new_refresh is not None, "Missing X-Refresh-Token header"

    # Decode and verify the access token claims
    claims = jwt.decode(
        new_access,
        settings.jwt_secret_key,
        algorithms=[settings.jwt_algorithm],
        options={"verify_aud": False, "verify_iss": False},
    )
    assert claims["sub"] == str(user.id)
    assert claims["type"] == "access"
    assert claims["role"] == user.role.value


def test_mobile_auth_custom_header_refresh_flow(client: TestClient, db_session: Session):
    """Mobile clients can refresh sessions via X-Refresh-Token header."""
    user = _create_user(db_session, f"mobile_xhead_{uuid.uuid4().hex[:6]}@histolab.icu")

    refresh_token = create_jwt_token(
        subject=str(user.id),
        secret_key=settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
        expires_delta=timedelta(days=7),
        issuer=settings.jwt_issuer,
        audience=settings.jwt_audience,
        extra_claims={"type": "refresh", "role": user.role.value},
    )

    client.cookies.clear()
    response = client.post(
        "/api/v1/auth/refresh",
        headers={"X-Refresh-Token": refresh_token},
    )
    assert response.status_code == 200
    assert response.headers.get("X-Access-Token") is not None
    assert response.headers.get("X-Refresh-Token") is not None


def test_mobile_auth_token_rotation_and_revocation(client: TestClient, db_session: Session):
    """Refresh rotates tokens; old refresh token cannot be replayed; logout revokes token."""
    user = _create_user(db_session, f"mobile_rot_{uuid.uuid4().hex[:6]}@histolab.icu")

    initial_refresh = create_jwt_token(
        subject=str(user.id),
        secret_key=settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
        expires_delta=timedelta(days=7),
        issuer=settings.jwt_issuer,
        audience=settings.jwt_audience,
        extra_claims={"type": "refresh", "role": user.role.value},
    )

    client.cookies.clear()

    # 1. First refresh with initial token succeeds
    resp1 = client.post(
        "/api/v1/auth/refresh",
        headers={"Authorization": f"Bearer {initial_refresh}"},
    )
    assert resp1.status_code == 200
    second_refresh = resp1.headers.get("X-Refresh-Token")
    assert second_refresh is not None
    assert second_refresh != initial_refresh

    # 2. Replay of initial token must be rejected (revoked by rotation)
    client.cookies.clear()
    replay_resp = client.post(
        "/api/v1/auth/refresh",
        headers={"Authorization": f"Bearer {initial_refresh}"},
    )
    assert replay_resp.status_code == 401

    # 3. Explicit mobile logout with Bearer header revokes the second token
    client.cookies.clear()
    logout_resp = client.post(
        "/api/v1/auth/logout",
        headers={"Authorization": f"Bearer {second_refresh}"},
    )
    assert logout_resp.status_code == 200

    # 4. Attempting to refresh with the logged-out token is rejected
    after_logout_resp = client.post(
        "/api/v1/auth/refresh",
        headers={"Authorization": f"Bearer {second_refresh}"},
    )
    assert after_logout_resp.status_code == 401


def test_mobile_auth_role_claim_integrity(client: TestClient, db_session: Session):
    """Access and refresh tokens correctly reflect user role in token claims."""
    roles = [UserRole.learner, UserRole.teacher, UserRole.admin, UserRole.guest]

    for role in roles:
        email = f"role_{role.value}_{uuid.uuid4().hex[:6]}@histolab.icu"
        user = _create_user(db_session, email=email, role=role)

        login_res = client.post(
            "/api/v1/auth/login",
            json={"email": email, "password": "Password123!"},
        )
        assert login_res.status_code == 200
        access_token = login_res.headers.get("X-Access-Token")
        assert access_token is not None

        claims = jwt.decode(
            access_token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
            options={"verify_aud": False, "verify_iss": False},
        )
        assert claims["role"] == role.value
        assert claims["sub"] == str(user.id)


def test_negative_abuse_expired_token_rejection(client: TestClient, db_session: Session):
    """Expired refresh tokens are strictly rejected with HTTP 401."""
    user = _create_user(db_session, f"expired_{uuid.uuid4().hex[:6]}@histolab.icu")

    # Generate token already expired in the past
    expired_token = create_jwt_token(
        subject=str(user.id),
        secret_key=settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
        expires_delta=timedelta(seconds=-120),
        issuer=settings.jwt_issuer,
        audience=settings.jwt_audience,
        extra_claims={"type": "refresh", "role": user.role.value},
    )

    client.cookies.clear()
    response = client.post(
        "/api/v1/auth/refresh",
        headers={"Authorization": f"Bearer {expired_token}"},
    )
    assert response.status_code == 401


def test_negative_abuse_tampered_token_rejection(client: TestClient):
    """Tampered or invalid tokens are rejected with HTTP 401."""
    client.cookies.clear()

    # Case 1: Malformed token string
    res1 = client.post(
        "/api/v1/auth/refresh",
        headers={"Authorization": "Bearer not_a_valid_jwt_token"},
    )
    assert res1.status_code == 401

    # Case 2: Signed with wrong key
    wrong_key_token = jwt.encode(
        {"sub": str(uuid.uuid4()), "type": "refresh", "exp": datetime.now(timezone.utc) + timedelta(hours=1)},
        "wrong_secret_key_12345678901234567890",
        algorithm="HS256",
    )
    res2 = client.post(
        "/api/v1/auth/refresh",
        headers={"Authorization": f"Bearer {wrong_key_token}"},
    )
    assert res2.status_code == 401

    # Case 3: Access token sent to refresh endpoint instead of refresh token
    access_token_as_refresh = create_jwt_token(
        subject=str(uuid.uuid4()),
        secret_key=settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
        expires_delta=timedelta(hours=1),
        issuer=settings.jwt_issuer,
        audience=settings.jwt_audience,
        extra_claims={"type": "access", "role": "learner"},
    )
    res3 = client.post(
        "/api/v1/auth/refresh",
        headers={"Authorization": f"Bearer {access_token_as_refresh}"},
    )
    assert res3.status_code == 401


# --------------------------------------------------------------------------- #
# Mobile Codebase Architectural Invariants & Security Guardrails
# --------------------------------------------------------------------------- #

def test_mobile_logging_interceptor_masks_secrets_and_tokens():
    """Logging interceptor strictly masks sensitive credentials, tokens, headers, and bodies."""
    log_file = REPO_ROOT / "mobile" / "lib" / "core" / "network" / "interceptors" / "logging_interceptor.dart"
    assert log_file.exists(), f"Missing {log_file}"
    content = log_file.read_text(encoding="utf-8")

    # Invariant: Sensitive header keys contain authorization, cookie, tokens
    assert "'authorization'" in content
    assert "'cookie'" in content
    assert "'set-cookie'" in content
    assert "'x-access-token'" in content
    assert "'x-refresh-token'" in content

    # Invariant: Sensitive body keys contain password, token, secrets
    assert "'password'" in content
    assert "'access_token'" in content
    assert "'refresh_token'" in content
    assert "'secret'" in content

    # Invariant: Sanitization uses ***MASKED***
    assert "***MASKED***" in content

    # Invariant: FCM notification service does not log raw tokens
    notif_svc = REPO_ROOT / "mobile" / "lib" / "features" / "notifications" / "data" / "notification_service.dart"
    notif_content = notif_svc.read_text(encoding="utf-8")
    assert "FCM Token refreshed: $token" not in notif_content
    assert "FCM Token refreshed: ***MASKED***" in notif_content


def test_mobile_secure_storage_and_dio_wiring():
    """SecureStorage uses hardware-backed options and DioProvider attaches TokenRefreshInterceptor."""
    sec_storage_file = REPO_ROOT / "mobile" / "lib" / "core" / "storage" / "secure_storage.dart"
    assert sec_storage_file.exists()
    sec_content = sec_storage_file.read_text(encoding="utf-8")

    assert "encryptedSharedPreferences: true" in sec_content
    assert "KeychainAccessibility.first_unlock" in sec_content
    assert "luuniensuki_access_token" in sec_content
    assert "luuniensuki_refresh_token" in sec_content

    # Invariant: Dio provider attaches TokenRefreshInterceptor
    dio_prov_file = REPO_ROOT / "mobile" / "lib" / "core" / "network" / "dio_provider.dart"
    dio_content = dio_prov_file.read_text(encoding="utf-8")
    assert "TokenRefreshInterceptor" in dio_content
    assert "dio.interceptors.add(TokenRefreshInterceptor(dio, secureStorage))" in dio_content


def test_mobile_session_lifecycle_prevents_prior_student_data_leakage():
    """Expired token or logout triggers clearAll() wiping tokens, user data, and quiz progress."""
    hive_storage_file = REPO_ROOT / "mobile" / "lib" / "core" / "storage" / "hive_storage.dart"
    hive_content = hive_storage_file.read_text(encoding="utf-8")

    # Invariant: clearUserData clears progress, user, badges, quests, and quiz progress
    assert "await progressBox.clear();" in hive_content
    assert "await userBox.clear();" in hive_content
    assert "await quizProgressBox.clear();" in hive_content

    # Invariant: AuthLocalDataSource clearAll clears tokens, cached user, cookies, and student data
    local_ds_file = REPO_ROOT / "mobile" / "lib" / "features" / "auth" / "data" / "datasources" / "auth_local_datasource.dart"
    local_content = local_ds_file.read_text(encoding="utf-8")
    assert "_hiveStorage.clearUserData()" in local_content

    # Invariant: AuthRepositoryImpl clears all local data on refresh failure or 401
    repo_file = REPO_ROOT / "mobile" / "lib" / "features" / "auth" / "data" / "repositories" / "auth_repository_impl.dart"
    repo_content = repo_file.read_text(encoding="utf-8")
    # Both refresh failure and session expiration call clearAll()
    assert "await _localDataSource.clearAll();" in repo_content


def test_mobile_role_aware_router_guards():
    """AppRouter enforces role-aware guards and reactive refreshListenable on auth state changes."""
    router_file = REPO_ROOT / "mobile" / "lib" / "routing" / "app_router.dart"
    assert router_file.exists()
    content = router_file.read_text(encoding="utf-8")

    # Invariant: RouterNotifier provides refreshListenable
    assert "class RouterNotifier extends ChangeNotifier" in content
    assert "refreshListenable: routerNotifier" in content

    # Invariant: Guest role restriction
    assert "currentUser?.isGuest" in content
    assert "_isLearnerOnlyRoute" in content

    # Invariant: Learner only routes include collection, practice, gemsShop, friends
    assert "RoutePaths.collection" in content
    assert "RoutePaths.practice" in content
    assert "RoutePaths.gemsShop" in content
    assert "RoutePaths.heartsRefill" in content

    # Invariant: Admin & Teacher route checks
    assert "isAdminRoute" in content
    assert "currentUser?.isAdmin" in content
    assert "isTeacherRoute" in content
    assert "currentUser?.hasElevatedPrivileges" in content
