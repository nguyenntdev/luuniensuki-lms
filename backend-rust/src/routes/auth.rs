//! Auth route handlers and DTOs.
//!
//! Tasks 3.1–3.4: module skeleton with request/response DTOs and handlers.
//! Implements auth extractor, login, register, refresh, logout,
//! forgot-password, reset-password, and age-verify.

use axum::{
    extract::State,
    http::{header, HeaderMap, StatusCode},
    response::{IntoResponse, Response},
    Json,
};
use chrono::Utc;
use serde::{Deserialize, Serialize};
use serde_json::json;
use sqlx::PgPool;
use uuid::Uuid;
use validator::Validate;

use crate::auth;
use crate::config::Settings;
use crate::error::AppError;

// ---------------------------------------------------------------------------
// Shared auth state
// ---------------------------------------------------------------------------

/// Combined state for auth routes: DB pool + settings.
#[derive(Clone)]
pub struct AuthState {
    pub pool: Option<PgPool>,
    pub settings: Settings,
}

// ---------------------------------------------------------------------------
// Request/Response DTOs
// ---------------------------------------------------------------------------

/// POST /api/v1/auth/login request body.
#[derive(Debug, Deserialize, Validate)]
pub struct LoginRequest {
    #[validate(email)]
    pub email: String,
    #[validate(length(min = 1))]
    pub password: String,
}

/// POST /api/v1/auth/register request body.
#[derive(Debug, Deserialize, Validate)]
pub struct RegisterRequest {
    #[validate(email)]
    pub email: String,
    #[validate(length(min = 8))]
    pub password: String,
    #[validate(length(min = 1, max = 100))]
    pub display_name: String,
}

/// POST /api/v1/auth/forgot-password request body.
#[derive(Debug, Deserialize, Validate)]
pub struct ForgotPasswordRequest {
    #[validate(email)]
    pub email: String,
}

/// POST /api/v1/auth/reset-password request body.
#[derive(Debug, Deserialize, Validate)]
pub struct ResetPasswordRequest {
    pub token: String,
    #[validate(length(min = 8))]
    pub new_password: String,
}

/// POST /api/v1/auth/age-verify request body.
#[derive(Debug, Deserialize)]
pub struct AgeVerifyRequest {
    pub birth_year: i32,
}

/// User object inside `AuthMeResponse` — mirrors Python's `UserOut`.
#[derive(Debug, Serialize, Clone)]
pub struct UserOut {
    pub id: String,
    pub email: String,
    pub display_name: String,
    pub avatar_url: Option<String>,
    pub username: Option<String>,
    pub role: String,
    pub total_xp: i32,
    pub starting_urn_id: Option<String>,
    pub is_profile_public: bool,
    pub ai_personalization_enabled: bool,
}

/// A single XP rank — mirrors Python's `RankOut`.
#[derive(Debug, Serialize, Clone)]
pub struct RankOut {
    pub level: i32,
    pub name: String,
    pub xp: i32,
}

/// User stats block inside `AuthMeResponse` — mirrors Python's `UserStatsOut`.
#[derive(Debug, Serialize, Clone)]
pub struct UserStatsOut {
    pub total_xp: i32,
    pub rank: RankOut,
    pub xp_to_next_rank: i32,
    pub next_rank: Option<RankOut>,
}

/// GET /api/v1/auth/me response body.
/// Matches Python's `AuthMeResponse` shape: `{ "user": UserOut, "stats": UserStatsOut }`.
#[derive(Debug, Serialize, Clone)]
pub struct AuthMeResponse {
    pub user: UserOut,
    pub stats: UserStatsOut,
}

/// XP rank table — mirrors `backend/main.py::XP_RANKS`.
const XP_RANKS: &[(i32, &str, i32)] = &[
    (1, "Lính Mới", 0),
    (2, "Thư Sinh", 500),
    (3, "Tú Tài", 1500),
    (4, "Cử Nhân", 3500),
    (5, "Tiến Sĩ", 7000),
    (6, "Thám Hoa", 12000),
    (7, "Bảng Nhãn", 20000),
    (8, "Trạng Nguyên", 35000),
    (9, "Hàn Lâm", 55000),
    (10, "Sử Quan", 80000),
];

/// Compute (current_rank, next_rank, xp_to_next) — mirrors `_compute_rank`.
fn compute_rank(total_xp: i32) -> (RankOut, Option<RankOut>, i32) {
    let to_rank = |&(level, name, xp): &(i32, &str, i32)| RankOut {
        level,
        name: name.to_string(),
        xp,
    };

    let mut current = &XP_RANKS[0];
    for r in XP_RANKS {
        if total_xp >= r.2 {
            current = r;
        } else {
            break;
        }
    }

    let next = XP_RANKS.iter().find(|r| r.2 > current.2);
    let current_rank = to_rank(current);
    match next {
        None => (current_rank, None, 0),
        Some(n) => {
            let next_rank = to_rank(n);
            let xp_to_next = (n.2 - total_xp).max(0);
            (current_rank, Some(next_rank), xp_to_next)
        }
    }
}

/// Build the wrapped `AuthMeResponse` from a user's fields.
fn build_auth_me_response(
    id: Uuid,
    email: String,
    display_name: String,
    avatar_url: Option<String>,
    username: Option<String>,
    role: String,
    total_xp: i32,
    starting_urn_id: Option<Uuid>,
    is_profile_public: bool,
    ai_personalization_enabled: bool,
) -> AuthMeResponse {
    let (rank, next_rank, xp_to_next) = compute_rank(total_xp);
    AuthMeResponse {
        user: UserOut {
            id: id.to_string(),
            email,
            display_name,
            avatar_url,
            username,
            role,
            total_xp,
            starting_urn_id: starting_urn_id.map(|u| u.to_string()),
            is_profile_public,
            ai_personalization_enabled,
        },
        stats: UserStatsOut {
            total_xp,
            rank,
            xp_to_next_rank: xp_to_next,
            next_rank,
        },
    }
}

/// POST /api/v1/auth/forgot-password response body.
#[derive(Debug, Serialize)]
pub struct ForgotPasswordResponse {
    pub message: String,
}

/// POST /api/v1/auth/reset-password response body.
#[derive(Debug, Serialize)]
pub struct ResetPasswordResponse {
    pub message: String,
}

/// POST /api/v1/auth/logout response body.
#[derive(Debug, Serialize)]
pub struct LogoutResponse {
    pub success: bool,
}

/// Age verification response body (matches Python's AgeVerificationOut).
#[derive(Debug, Serialize)]
pub struct AgeVerifyResponse {
    pub age_verified: bool,
    pub birth_year: i32,
    pub current_age: i32,
}

// ---------------------------------------------------------------------------
// Cookie helpers
// ---------------------------------------------------------------------------

/// Cookie name for the access token.
const ACCESS_COOKIE_NAME: &str = "luuniensuki_access";
/// Cookie name for the refresh token.
const REFRESH_COOKIE_NAME: &str = "luuniensuki_refresh";

/// Build a Set-Cookie header value for an auth cookie.
fn build_cookie(name: &str, value: &str, max_age_secs: i64, secure: bool) -> String {
    let mut cookie = format!(
        "{}={}; HttpOnly; SameSite=Lax; Path=/; Max-Age={}",
        name, value, max_age_secs
    );
    if secure {
        cookie.push_str("; Secure");
    }
    cookie
}

/// Build a Set-Cookie header that clears (expires) a cookie.
fn build_clear_cookie(name: &str, secure: bool) -> String {
    build_cookie(name, "", 0, secure)
}

/// Determine if cookies should be Secure (true in production).
fn is_secure() -> bool {
    std::env::var("COOKIE_SECURE")
        .map(|v| v == "true" || v == "1")
        .unwrap_or(false)
}

// ---------------------------------------------------------------------------
// Auth extractor: extract Claims from request
// ---------------------------------------------------------------------------

/// Extract JWT claims from the request.
/// Checks Authorization: Bearer header first, then the access cookie.
fn extract_token_from_headers(headers: &HeaderMap) -> Option<String> {
    // 1. Try Authorization: Bearer <token>
    if let Some(auth_header) = headers.get(header::AUTHORIZATION) {
        if let Ok(auth_str) = auth_header.to_str() {
            if let Some(token) = auth_str.strip_prefix("Bearer ") {
                return Some(token.to_string());
            }
        }
    }

    // 2. Try luuniensuki_access cookie
    if let Some(cookie_header) = headers.get(header::COOKIE) {
        if let Ok(cookie_str) = cookie_header.to_str() {
            for part in cookie_str.split(';') {
                let trimmed = part.trim();
                if let Some(value) = trimmed.strip_prefix("luuniensuki_access=") {
                    return Some(value.to_string());
                }
            }
        }
    }

    None
}

/// Extract the refresh token from the cookie header.
fn extract_refresh_token_from_headers(headers: &HeaderMap) -> Option<String> {
    if let Some(cookie_header) = headers.get(header::COOKIE) {
        if let Ok(cookie_str) = cookie_header.to_str() {
            for part in cookie_str.split(';') {
                let trimmed = part.trim();
                if let Some(value) = trimmed.strip_prefix("luuniensuki_refresh=") {
                    return Some(value.to_string());
                }
            }
        }
    }
    None
}

/// Require a valid DB pool or return 503.
fn require_pool(pool: &Option<PgPool>) -> Result<&PgPool, AppError> {
    pool.as_ref().ok_or_else(|| AppError::Http {
        status: StatusCode::SERVICE_UNAVAILABLE,
        message: "Database unavailable".to_string(),
    })
}

// ---------------------------------------------------------------------------
// Handlers
// ---------------------------------------------------------------------------

/// GET /api/v1/auth/me — return current authenticated user.
pub async fn me(
    headers: HeaderMap,
    State(state): State<AuthState>,
) -> Result<impl IntoResponse, AppError> {
    let token = extract_token_from_headers(&headers).ok_or(AppError::Unauthorized)?;
    let claims =
        auth::verify_access_token(&token, &state.settings.jwt_secret_key, state.settings.jwt_validate_new_claims, &state.settings.jwt_issuer, &state.settings.jwt_audience)
            .map_err(|_| AppError::Unauthorized)?;

    let pool = require_pool(&state.pool)?;


    let user_id: Uuid = claims.sub.parse().map_err(|_| AppError::Unauthorized)?;

    let row = sqlx::query_as::<_, UserRow>(
        "SELECT id, email, display_name, role::text AS role, avatar_url, username, total_xp, \
         starting_urn_id, is_profile_public, ai_personalization_enabled, age_verified, created_at \
         FROM users WHERE id = $1",
    )
    .bind(user_id)
    .fetch_optional(pool)
    .await
    .map_err(|e| AppError::Internal(e.into()))?
    .ok_or(AppError::Unauthorized)?;

    Ok(Json(row.into_auth_me_response()))
}

/// POST /api/v1/auth/login — authenticate with email + password.
pub async fn login(
    State(state): State<AuthState>,
    Json(payload): Json<LoginRequest>,
) -> Result<Response, AppError> {
    if let Err(e) = payload.validate() {
        return Err(AppError::Validation {
            details: serde_json::to_value(e).unwrap_or(json!({})),
        });
    }

    let pool = require_pool(&state.pool)?;

    let row = sqlx::query_as::<_, UserRowWithPassword>(
        "SELECT id, email, display_name, role::text AS role, password_hash, avatar_url, \
         username, total_xp, starting_urn_id, is_profile_public, ai_personalization_enabled, \
         age_verified, created_at FROM users WHERE email = $1",
    )
    .bind(&payload.email)
    .fetch_optional(pool)
    .await
    .map_err(|e| AppError::Internal(e.into()))?
    .ok_or(AppError::Unauthorized)?;

    // Verify password
    let valid = auth::verify_password(&payload.password, &row.password_hash)
        .map_err(|_| AppError::Unauthorized)?;
    if !valid {
        return Err(AppError::Unauthorized);
    }

    let user_id_str = row.id.to_string();
    let access_token = auth::issue_access_token(
        &user_id_str,
        &row.role,
        &state.settings.jwt_secret_key,
        state.settings.access_token_expire_minutes,
        &state.settings.jwt_issuer,
        &state.settings.jwt_audience,
    )
    .map_err(|e| AppError::Internal(anyhow::anyhow!("{}", e)))?;

    let refresh_token = auth::issue_refresh_token(
        &user_id_str,
        &row.role,
        &state.settings.jwt_secret_key,
        state.settings.refresh_token_expire_days,
        &state.settings.jwt_issuer,
        &state.settings.jwt_audience,
    )
    .map_err(|e| AppError::Internal(anyhow::anyhow!("{}", e)))?;

    let body = row.into_auth_me_response();
    let mut response = Json(body).into_response();
    append_auth_cookies(&mut response, &access_token, &refresh_token, &state.settings);
    response
        .headers_mut()
        .insert(header::CACHE_CONTROL, "no-store".parse().unwrap());
    Ok(response)
}

/// POST /api/v1/auth/register — create a new user account.
pub async fn register(
    State(state): State<AuthState>,
    Json(payload): Json<RegisterRequest>,
) -> Result<Response, AppError> {
    if let Err(e) = payload.validate() {
        return Err(AppError::Validation {
            details: serde_json::to_value(e).unwrap_or(json!({})),
        });
    }

    let pool = require_pool(&state.pool)?;

    // Check if email already taken
    let existing: Option<(Uuid,)> =
        sqlx::query_as("SELECT id FROM users WHERE email = $1")
            .bind(&payload.email)
            .fetch_optional(pool)
            .await
            .map_err(|e| AppError::Internal(e.into()))?;

    if existing.is_some() {
        return Err(AppError::Domain {
            status: StatusCode::CONFLICT,
            code: "EMAIL_ALREADY_REGISTERED".to_string(),
            message: "Email already registered".to_string(),
            details: json!({}),
        });
    }

    // Hash password (bcrypt cost 12)
    let password_hash = auth::hash_password(&payload.password).map_err(|e| {
        if matches!(e, auth::AuthError::PasswordTooLong) {
            AppError::Domain {
                status: StatusCode::BAD_REQUEST,
                code: "PASSWORD_TOO_LONG".to_string(),
                message: "Password too long".to_string(),
                details: json!({}),
            }
        } else {
            AppError::Internal(anyhow::anyhow!("{}", e))
        }
    })?;

    let new_id = Uuid::new_v4();
    let row = sqlx::query_as::<_, UserRow>(
        "INSERT INTO users (id, email, display_name, password_hash, role, created_at, updated_at) \
         VALUES ($1, $2, $3, $4, 'user', NOW(), NOW()) \
         RETURNING id, email, display_name, role::text AS role, avatar_url, username, total_xp, \
         starting_urn_id, is_profile_public, ai_personalization_enabled, age_verified, created_at",
    )
    .bind(new_id)
    .bind(&payload.email)
    .bind(&payload.display_name)
    .bind(&password_hash)
    .fetch_one(pool)
    .await
    .map_err(|e| {
        // Handle unique constraint violation (race condition)
        if let Some(db_err) = e.as_database_error() {
            if db_err.code().as_deref() == Some("23505") {
                return AppError::Domain {
                    status: StatusCode::CONFLICT,
                    code: "EMAIL_ALREADY_REGISTERED".to_string(),
                    message: "Email already registered".to_string(),
                    details: json!({}),
                };
            }
        }
        AppError::Internal(e.into())
    })?;

    let user_id_str = row.id.to_string();
    let access_token = auth::issue_access_token(
        &user_id_str,
        &row.role,
        &state.settings.jwt_secret_key,
        state.settings.access_token_expire_minutes,
        &state.settings.jwt_issuer,
        &state.settings.jwt_audience,
    )
    .map_err(|e| AppError::Internal(anyhow::anyhow!("{}", e)))?;

    let refresh_token = auth::issue_refresh_token(
        &user_id_str,
        &row.role,
        &state.settings.jwt_secret_key,
        state.settings.refresh_token_expire_days,
        &state.settings.jwt_issuer,
        &state.settings.jwt_audience,
    )
    .map_err(|e| AppError::Internal(anyhow::anyhow!("{}", e)))?;

    let body = row.into_auth_me_response();
    let mut response = (StatusCode::CREATED, Json(body)).into_response();
    append_auth_cookies(&mut response, &access_token, &refresh_token, &state.settings);
    response
        .headers_mut()
        .insert(header::CACHE_CONTROL, "no-store".parse().unwrap());
    Ok(response)
}

/// POST /api/v1/auth/refresh — rotate tokens using the refresh cookie.
pub async fn refresh(
    headers: HeaderMap,
    State(state): State<AuthState>,
) -> Result<Response, AppError> {
    let raw_token =
        extract_refresh_token_from_headers(&headers).ok_or(AppError::Unauthorized)?;

    let claims = auth::verify_refresh_token(&raw_token, &state.settings.jwt_secret_key, state.settings.jwt_validate_new_claims, &state.settings.jwt_issuer, &state.settings.jwt_audience)
        .map_err(|_| AppError::Unauthorized)?;

    let pool = require_pool(&state.pool)?;

    let user_id: Uuid = claims.sub.parse().map_err(|_| AppError::Unauthorized)?;

    let row = sqlx::query_as::<_, UserRow>(
        "SELECT id, email, display_name, role::text AS role, avatar_url, username, total_xp, \
         starting_urn_id, is_profile_public, ai_personalization_enabled, age_verified, created_at \
         FROM users WHERE id = $1",
    )
    .bind(user_id)
    .fetch_optional(pool)
    .await
    .map_err(|e| AppError::Internal(e.into()))?
    .ok_or(AppError::Unauthorized)?;

    let user_id_str = row.id.to_string();
    let access_token = auth::issue_access_token(
        &user_id_str,
        &row.role,
        &state.settings.jwt_secret_key,
        state.settings.access_token_expire_minutes,
        &state.settings.jwt_issuer,
        &state.settings.jwt_audience,
    )
    .map_err(|e| AppError::Internal(anyhow::anyhow!("{}", e)))?;

    let refresh_token = auth::issue_refresh_token(
        &user_id_str,
        &row.role,
        &state.settings.jwt_secret_key,
        state.settings.refresh_token_expire_days,
        &state.settings.jwt_issuer,
        &state.settings.jwt_audience,
    )
    .map_err(|e| AppError::Internal(anyhow::anyhow!("{}", e)))?;

    let body = row.into_auth_me_response();
    let mut response = Json(body).into_response();
    append_auth_cookies(&mut response, &access_token, &refresh_token, &state.settings);
    response
        .headers_mut()
        .insert(header::CACHE_CONTROL, "no-store".parse().unwrap());
    Ok(response)
}

/// POST /api/v1/auth/logout — clear auth cookies.
pub async fn logout() -> Response {
    let secure = is_secure();
    let mut response = Json(LogoutResponse { success: true }).into_response();
    response.headers_mut().append(
        header::SET_COOKIE,
        build_clear_cookie(ACCESS_COOKIE_NAME, secure).parse().unwrap(),
    );
    response.headers_mut().append(
        header::SET_COOKIE,
        build_clear_cookie(REFRESH_COOKIE_NAME, secure).parse().unwrap(),
    );
    response
        .headers_mut()
        .insert(header::CACHE_CONTROL, "no-store".parse().unwrap());
    response
}

/// POST /api/v1/auth/forgot-password — request a password reset token.
pub async fn forgot_password(
    State(state): State<AuthState>,
    Json(payload): Json<ForgotPasswordRequest>,
) -> Result<Json<ForgotPasswordResponse>, AppError> {
    if let Err(e) = payload.validate() {
        return Err(AppError::Validation {
            details: serde_json::to_value(e).unwrap_or(json!({})),
        });
    }

    let pool = require_pool(&state.pool)?;

    // Look up user — don't reveal if email exists
    let user: Option<(Uuid,)> =
        sqlx::query_as("SELECT id FROM users WHERE email = $1")
            .bind(&payload.email)
            .fetch_optional(pool)
            .await
            .map_err(|e| AppError::Internal(e.into()))?;

    if let Some((user_id,)) = user {
        // Generate a random reset token
        let token_value = Uuid::new_v4().to_string();
        let token_hash = sha256_hex(&token_value);
        let expires_at = Utc::now() + chrono::Duration::minutes(30);

        // Invalidate existing tokens for this user
        let _ = sqlx::query(
            "UPDATE password_reset_tokens SET used_at = NOW() \
             WHERE user_id = $1 AND used_at IS NULL AND expires_at > NOW()",
        )
        .bind(user_id)
        .execute(pool)
        .await;

        // Insert new reset token
        let _ = sqlx::query(
            "INSERT INTO password_reset_tokens (id, user_id, token_hash, expires_at, created_at) \
             VALUES ($1, $2, $3, $4, NOW())",
        )
        .bind(Uuid::new_v4())
        .bind(user_id)
        .bind(&token_hash)
        .bind(expires_at)
        .execute(pool)
        .await;
    }

    // Always return the same message to prevent account enumeration
    Ok(Json(ForgotPasswordResponse {
        message: "If an account exists for this email, a password reset instruction has been generated.".to_string(),
    }))
}

/// POST /api/v1/auth/reset-password — reset password using a valid token.
pub async fn reset_password(
    State(state): State<AuthState>,
    Json(payload): Json<ResetPasswordRequest>,
) -> Result<Json<ResetPasswordResponse>, AppError> {
    if let Err(e) = payload.validate() {
        return Err(AppError::Validation {
            details: serde_json::to_value(e).unwrap_or(json!({})),
        });
    }

    let pool = require_pool(&state.pool)?;

    let token_hash = sha256_hex(&payload.token);

    // Look up valid, unused, non-expired token
    let reset_row: Option<(Uuid, Uuid)> = sqlx::query_as(
        "SELECT id, user_id FROM password_reset_tokens \
         WHERE token_hash = $1 AND used_at IS NULL AND expires_at > NOW() \
         ORDER BY created_at DESC LIMIT 1",
    )
    .bind(&token_hash)
    .fetch_optional(pool)
    .await
    .map_err(|e| AppError::Internal(e.into()))?;

    let (token_id, user_id) = reset_row.ok_or_else(|| AppError::Domain {
        status: StatusCode::BAD_REQUEST,
        code: "INVALID_OR_EXPIRED_RESET_TOKEN".to_string(),
        message: "Invalid or expired password reset token".to_string(),
        details: json!({}),
    })?;

    // Hash new password
    let new_hash = auth::hash_password(&payload.new_password).map_err(|e| {
        if matches!(e, auth::AuthError::PasswordTooLong) {
            AppError::Domain {
                status: StatusCode::BAD_REQUEST,
                code: "PASSWORD_TOO_LONG".to_string(),
                message: "Password too long".to_string(),
                details: json!({}),
            }
        } else {
            AppError::Internal(anyhow::anyhow!("{}", e))
        }
    })?;

    // Update user's password
    sqlx::query("UPDATE users SET password_hash = $1, updated_at = NOW() WHERE id = $2")
        .bind(&new_hash)
        .bind(user_id)
        .execute(pool)
        .await
        .map_err(|e| AppError::Internal(e.into()))?;

    // Mark token as used
    sqlx::query("UPDATE password_reset_tokens SET used_at = NOW() WHERE id = $1")
        .bind(token_id)
        .execute(pool)
        .await
        .map_err(|e| AppError::Internal(e.into()))?;

    Ok(Json(ResetPasswordResponse {
        message: "Password has been reset successfully.".to_string(),
    }))
}

/// POST /api/v1/users/me/age-verify — verify user's age.
pub async fn age_verify(
    headers: HeaderMap,
    State(state): State<AuthState>,
    Json(payload): Json<AgeVerifyRequest>,
) -> Result<impl IntoResponse, AppError> {
    let token = extract_token_from_headers(&headers).ok_or(AppError::Unauthorized)?;
    let claims =
        auth::verify_access_token(&token, &state.settings.jwt_secret_key, state.settings.jwt_validate_new_claims, &state.settings.jwt_issuer, &state.settings.jwt_audience)
            .map_err(|_| AppError::Unauthorized)?;

    let pool = require_pool(&state.pool)?;

    let user_id: Uuid = claims.sub.parse().map_err(|_| AppError::Unauthorized)?;

    // Validate birth year
    let current_year = Utc::now().format("%Y").to_string().parse::<i32>().unwrap();
    if payload.birth_year < 1900 || payload.birth_year > current_year {
        return Err(AppError::Domain {
            status: StatusCode::BAD_REQUEST,
            code: "INVALID_BIRTH_YEAR".to_string(),
            message: format!(
                "Birth year must be between 1900 and {}",
                current_year
            ),
            details: json!({}),
        });
    }

    // Update user's age verification
    sqlx::query(
        "UPDATE users SET age_verified = true, birth_year = $1, \
         age_verified_at = NOW(), updated_at = NOW() WHERE id = $2",
    )
    .bind(payload.birth_year)
    .bind(user_id)
    .execute(pool)
    .await
    .map_err(|e| AppError::Internal(e.into()))?;

    let age = current_year - payload.birth_year;

    Ok(Json(AgeVerifyResponse {
        age_verified: true,
        birth_year: payload.birth_year,
        current_age: age,
    }))
}

// ---------------------------------------------------------------------------
// Internal helpers
// ---------------------------------------------------------------------------

/// Append Set-Cookie headers for access and refresh tokens.
fn append_auth_cookies(
    response: &mut Response,
    access_token: &str,
    refresh_token: &str,
    settings: &Settings,
) {
    let secure = is_secure();
    let access_max_age = settings.access_token_expire_minutes * 60;
    let refresh_max_age = settings.refresh_token_expire_days * 24 * 60 * 60;

    response.headers_mut().append(
        header::SET_COOKIE,
        build_cookie(ACCESS_COOKIE_NAME, access_token, access_max_age, secure)
            .parse()
            .unwrap(),
    );
    response.headers_mut().append(
        header::SET_COOKIE,
        build_cookie(REFRESH_COOKIE_NAME, refresh_token, refresh_max_age, secure)
            .parse()
            .unwrap(),
    );
}

/// Compute SHA-256 hex digest of a string (for token hashing).
fn sha256_hex(input: &str) -> String {
    use sha2::{Digest, Sha256};
    let mut hasher = Sha256::new();
    hasher.update(input.as_bytes());
    let result = hasher.finalize();
    hex_encode(&result)
}

/// Encode bytes as lowercase hex string.
fn hex_encode(bytes: &[u8]) -> String {
    use std::fmt::Write;
    let mut s = String::with_capacity(bytes.len() * 2);
    for b in bytes {
        write!(s, "{:02x}", b).unwrap();
    }
    s
}

// ---------------------------------------------------------------------------
// Database row types
// ---------------------------------------------------------------------------

/// Row returned by user queries (without password).
#[derive(Debug, sqlx::FromRow)]
struct UserRow {
    pub id: Uuid,
    pub email: String,
    pub display_name: String,
    pub role: String,
    pub avatar_url: Option<String>,
    pub username: Option<String>,
    pub total_xp: i32,
    pub starting_urn_id: Option<Uuid>,
    pub is_profile_public: bool,
    pub ai_personalization_enabled: bool,
    pub age_verified: bool,
    pub created_at: chrono::DateTime<Utc>,
}

impl UserRow {
    fn into_auth_me_response(self) -> AuthMeResponse {
        let _ = (self.age_verified, self.created_at);
        build_auth_me_response(
            self.id,
            self.email,
            self.display_name,
            self.avatar_url,
            self.username,
            self.role,
            self.total_xp,
            self.starting_urn_id,
            self.is_profile_public,
            self.ai_personalization_enabled,
        )
    }
}

/// Row returned by user queries (with password hash for login).
#[derive(Debug, sqlx::FromRow)]
struct UserRowWithPassword {
    pub id: Uuid,
    pub email: String,
    pub display_name: String,
    pub role: String,
    pub password_hash: String,
    pub avatar_url: Option<String>,
    pub username: Option<String>,
    pub total_xp: i32,
    pub starting_urn_id: Option<Uuid>,
    pub is_profile_public: bool,
    pub ai_personalization_enabled: bool,
    pub age_verified: bool,
    pub created_at: chrono::DateTime<Utc>,
}

impl UserRowWithPassword {
    fn into_auth_me_response(self) -> AuthMeResponse {
        let _ = (self.age_verified, self.created_at);
        build_auth_me_response(
            self.id,
            self.email,
            self.display_name,
            self.avatar_url,
            self.username,
            self.role,
            self.total_xp,
            self.starting_urn_id,
            self.is_profile_public,
            self.ai_personalization_enabled,
        )
    }
}

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

#[cfg(test)]
mod tests {
    use super::*;
    use axum::{
        body::{to_bytes, Body},
        http::Request,
        routing::{get, post},
        Router,
    };
    use serde_json::Value;
    use tower::ServiceExt;

    fn test_auth_state() -> AuthState {
        let settings = crate::config::Settings::from_env().unwrap();
        AuthState {
            pool: None,
            settings,
        }
    }

    fn test_router() -> Router {
        let state = test_auth_state();
        Router::new()
            .route("/api/v1/auth/me", get(me))
            .route("/api/v1/auth/login", post(login))
            .route("/api/v1/auth/register", post(register))
            .route("/api/v1/auth/refresh", post(refresh))
            .route("/api/v1/auth/logout", post(logout))
            .route("/api/v1/auth/forgot-password", post(forgot_password))
            .route("/api/v1/auth/reset-password", post(reset_password))
            .route("/api/v1/users/me/age-verify", post(age_verify))
            .with_state(state)
    }

    #[tokio::test]
    async fn me_returns_401_without_token() {
        let app = test_router();
        let resp = app
            .oneshot(
                Request::builder()
                    .uri("/api/v1/auth/me")
                    .body(Body::empty())
                    .unwrap(),
            )
            .await
            .unwrap();
        assert_eq!(resp.status(), StatusCode::UNAUTHORIZED);
    }

    #[tokio::test]
    async fn me_returns_401_for_expired_token() {
        let state = test_auth_state();
        // Create an expired token
        let now = chrono::Utc::now().timestamp();
        let claims = crate::auth::Claims {
            sub: "00000000-0000-0000-0000-000000000001".to_string(),
            iat: now - 7200,
            exp: now - 3600, // expired 1 hour ago
            role: "user".to_string(),
            token_type: "access".to_string(),
            iss: state.settings.jwt_issuer.clone(),
            aud: state.settings.jwt_audience.clone(),
            jti: String::new(),
        };
        let token = jsonwebtoken::encode(
            &jsonwebtoken::Header::default(),
            &claims,
            &jsonwebtoken::EncodingKey::from_secret(
                state.settings.jwt_secret_key.as_bytes(),
            ),
        )
        .unwrap();

        let app = test_router();
        let resp = app
            .oneshot(
                Request::builder()
                    .uri("/api/v1/auth/me")
                    .header("Authorization", format!("Bearer {}", token))
                    .body(Body::empty())
                    .unwrap(),
            )
            .await
            .unwrap();
        assert_eq!(resp.status(), StatusCode::UNAUTHORIZED);
    }

    #[tokio::test]
    async fn me_returns_401_for_refresh_token() {
        let state = test_auth_state();
        // A refresh token should not work for /auth/me
        let token = crate::auth::issue_refresh_token(
            "00000000-0000-0000-0000-000000000001",
            "user",
            &state.settings.jwt_secret_key,
            7,
            &state.settings.jwt_issuer,
            &state.settings.jwt_audience,
        )
        .unwrap();

        let app = test_router();
        let resp = app
            .oneshot(
                Request::builder()
                    .uri("/api/v1/auth/me")
                    .header("Authorization", format!("Bearer {}", token))
                    .body(Body::empty())
                    .unwrap(),
            )
            .await
            .unwrap();
        assert_eq!(resp.status(), StatusCode::UNAUTHORIZED);
    }

    #[tokio::test]
    async fn me_returns_503_when_pool_is_none() {
        let state = test_auth_state();
        // Create a valid access token
        let token = crate::auth::issue_access_token(
            "00000000-0000-0000-0000-000000000001",
            "user",
            &state.settings.jwt_secret_key,
            60,
            &state.settings.jwt_issuer,
            &state.settings.jwt_audience,
        )
        .unwrap();

        let app = test_router();
        let resp = app
            .oneshot(
                Request::builder()
                    .uri("/api/v1/auth/me")
                    .header("Authorization", format!("Bearer {}", token))
                    .body(Body::empty())
                    .unwrap(),
            )
            .await
            .unwrap();
        // With pool=None, the handler returns 503
        assert_eq!(resp.status(), StatusCode::SERVICE_UNAVAILABLE);
    }

    #[tokio::test]
    async fn login_returns_503_when_pool_is_none() {
        let app = test_router();
        let resp = app
            .oneshot(
                Request::builder()
                    .method("POST")
                    .uri("/api/v1/auth/login")
                    .header("content-type", "application/json")
                    .body(Body::from(
                        r#"{"email":"test@example.com","password":"password123"}"#,
                    ))
                    .unwrap(),
            )
            .await
            .unwrap();
        assert_eq!(resp.status(), StatusCode::SERVICE_UNAVAILABLE);
    }

    #[tokio::test]
    async fn register_returns_503_when_pool_is_none() {
        let app = test_router();
        let resp = app
            .oneshot(
                Request::builder()
                    .method("POST")
                    .uri("/api/v1/auth/register")
                    .header("content-type", "application/json")
                    .body(Body::from(
                        r#"{"email":"test@example.com","password":"password123","display_name":"Test"}"#,
                    ))
                    .unwrap(),
            )
            .await
            .unwrap();
        assert_eq!(resp.status(), StatusCode::SERVICE_UNAVAILABLE);
    }

    #[tokio::test]
    async fn logout_clears_cookies() {
        let app = test_router();
        let resp = app
            .oneshot(
                Request::builder()
                    .method("POST")
                    .uri("/api/v1/auth/logout")
                    .body(Body::empty())
                    .unwrap(),
            )
            .await
            .unwrap();
        assert_eq!(resp.status(), StatusCode::OK);

        // Check Set-Cookie headers clear both cookies
        let cookies: Vec<&str> = resp
            .headers()
            .get_all(header::SET_COOKIE)
            .iter()
            .map(|v| v.to_str().unwrap())
            .collect();
        assert_eq!(cookies.len(), 2);
        assert!(cookies.iter().any(|c| c.contains("luuniensuki_access=")));
        assert!(cookies.iter().any(|c| c.contains("luuniensuki_refresh=")));
        assert!(cookies.iter().all(|c| c.contains("Max-Age=0")));

        let body = to_bytes(resp.into_body(), 1024).await.unwrap();
        let parsed: Value = serde_json::from_slice(&body).unwrap();
        assert_eq!(parsed["success"], true);
    }

    #[tokio::test]
    async fn refresh_returns_401_without_cookie() {
        let app = test_router();
        let resp = app
            .oneshot(
                Request::builder()
                    .method("POST")
                    .uri("/api/v1/auth/refresh")
                    .body(Body::empty())
                    .unwrap(),
            )
            .await
            .unwrap();
        assert_eq!(resp.status(), StatusCode::UNAUTHORIZED);
    }

    #[tokio::test]
    async fn forgot_password_returns_503_when_pool_is_none() {
        let app = test_router();
        let resp = app
            .oneshot(
                Request::builder()
                    .method("POST")
                    .uri("/api/v1/auth/forgot-password")
                    .header("content-type", "application/json")
                    .body(Body::from(r#"{"email":"test@example.com"}"#))
                    .unwrap(),
            )
            .await
            .unwrap();
        assert_eq!(resp.status(), StatusCode::SERVICE_UNAVAILABLE);
    }

    #[tokio::test]
    async fn reset_password_returns_503_when_pool_is_none() {
        let app = test_router();
        let resp = app
            .oneshot(
                Request::builder()
                    .method("POST")
                    .uri("/api/v1/auth/reset-password")
                    .header("content-type", "application/json")
                    .body(Body::from(
                        r#"{"token":"some-token-value-here","new_password":"newpass123"}"#,
                    ))
                    .unwrap(),
            )
            .await
            .unwrap();
        assert_eq!(resp.status(), StatusCode::SERVICE_UNAVAILABLE);
    }

    #[tokio::test]
    async fn age_verify_returns_401_without_token() {
        let app = test_router();
        let resp = app
            .oneshot(
                Request::builder()
                    .method("POST")
                    .uri("/api/v1/users/me/age-verify")
                    .header("content-type", "application/json")
                    .body(Body::from(r#"{"birth_year":1990}"#))
                    .unwrap(),
            )
            .await
            .unwrap();
        assert_eq!(resp.status(), StatusCode::UNAUTHORIZED);
    }

    #[test]
    fn extract_token_from_bearer_header() {
        let mut headers = HeaderMap::new();
        headers.insert(
            header::AUTHORIZATION,
            "Bearer my-jwt-token".parse().unwrap(),
        );
        assert_eq!(
            extract_token_from_headers(&headers),
            Some("my-jwt-token".to_string())
        );
    }

    #[test]
    fn extract_token_from_cookie() {
        let mut headers = HeaderMap::new();
        headers.insert(
            header::COOKIE,
            "other=val; luuniensuki_access=cookie-token; foo=bar"
                .parse()
                .unwrap(),
        );
        assert_eq!(
            extract_token_from_headers(&headers),
            Some("cookie-token".to_string())
        );
    }

    #[test]
    fn extract_token_returns_none_when_missing() {
        let headers = HeaderMap::new();
        assert_eq!(extract_token_from_headers(&headers), None);
    }

    #[test]
    fn sha256_hex_produces_correct_hash() {
        // Known SHA-256 of "hello"
        let hash = sha256_hex("hello");
        assert_eq!(
            hash,
            "2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824"
        );
    }
}
