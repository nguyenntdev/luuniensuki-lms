//! Shared route helpers: token extraction, pool guard, auth checks.
//!
//! These were duplicated across ~10 route modules. Centralising them
//! removes drift risk (one bug fix → all routes) and saves a few
//! hundred lines.

use axum::http::{header, HeaderMap, StatusCode};
use sqlx::PgPool;
use uuid::Uuid;

use crate::auth;
use crate::config::Settings;
use crate::error::AppError;

/// Pull a JWT access token from `Authorization: Bearer …` first, then from
/// the `luuniensuki_access` cookie.
pub fn extract_access_token(headers: &HeaderMap) -> Option<String> {
    if let Some(h) = headers.get(header::AUTHORIZATION) {
        if let Ok(s) = h.to_str() {
            if let Some(t) = s.strip_prefix("Bearer ") {
                return Some(t.to_string());
            }
        }
    }
    if let Some(c) = headers.get(header::COOKIE) {
        if let Ok(s) = c.to_str() {
            for part in s.split(';') {
                if let Some(v) = part.trim().strip_prefix("luuniensuki_access=") {
                    return Some(v.to_string());
                }
            }
        }
    }
    None
}

/// Return the pool or a 503 `AppError`.
pub fn require_pool(pool: &Option<PgPool>) -> Result<&PgPool, AppError> {
    pool.as_ref().ok_or_else(|| AppError::Http {
        status: StatusCode::SERVICE_UNAVAILABLE,
        message: "Database unavailable".to_string(),
    })
}

/// Authenticate the request and return the user id. Errors map to 401.
pub fn authenticate(headers: &HeaderMap, settings: &Settings) -> Result<Uuid, AppError> {
    let token = extract_access_token(headers).ok_or(AppError::Unauthorized)?;
    let claims = auth::verify_access_token(&token, &settings.jwt_secret_key)
        .map_err(|_| AppError::Unauthorized)?;
    claims.sub.parse().map_err(|_| AppError::Unauthorized)
}

/// Authenticate and additionally require `role = 'admin'`.
pub fn require_admin(headers: &HeaderMap, settings: &Settings) -> Result<Uuid, AppError> {
    let token = extract_access_token(headers).ok_or(AppError::Unauthorized)?;
    let claims = auth::verify_access_token(&token, &settings.jwt_secret_key)
        .map_err(|_| AppError::Unauthorized)?;
    if claims.role != "admin" {
        return Err(AppError::Http {
            status: StatusCode::FORBIDDEN,
            message: "Admin access required".to_string(),
        });
    }
    claims.sub.parse().map_err(|_| AppError::Unauthorized)
}

/// Authenticate and require `role = 'teacher'` or `'admin'`.
pub fn require_teacher(headers: &HeaderMap, settings: &Settings) -> Result<Uuid, AppError> {
    let token = extract_access_token(headers).ok_or(AppError::Unauthorized)?;
    let claims = auth::verify_access_token(&token, &settings.jwt_secret_key)
        .map_err(|_| AppError::Unauthorized)?;
    if claims.role != "teacher" && claims.role != "admin" {
        return Err(AppError::Http {
            status: StatusCode::FORBIDDEN,
            message: "Teacher access required".to_string(),
        });
    }
    claims.sub.parse().map_err(|_| AppError::Unauthorized)
}

#[cfg(test)]
mod tests {
    use super::*;
    use axum::http::{HeaderName, HeaderValue};

    fn header_map(values: &[(&'static str, &str)]) -> HeaderMap {
        let mut h = HeaderMap::new();
        for (k, v) in values {
            let name = HeaderName::from_static(k);
            h.insert(name, HeaderValue::from_str(v).unwrap());
        }
        h
    }

    #[test]
    fn extract_token_from_authorization_bearer() {
        let h = header_map(&[("authorization", "Bearer abc.def.ghi")]);
        assert_eq!(extract_access_token(&h).as_deref(), Some("abc.def.ghi"));
    }

    #[test]
    fn extract_token_from_cookie() {
        let h = header_map(&[("cookie", "foo=bar; luuniensuki_access=tok123; baz=qux")]);
        assert_eq!(extract_access_token(&h).as_deref(), Some("tok123"));
    }

    #[test]
    fn extract_token_prefers_authorization_over_cookie() {
        let h = header_map(&[
            ("authorization", "Bearer header_tok"),
            ("cookie", "luuniensuki_access=cookie_tok"),
        ]);
        assert_eq!(extract_access_token(&h).as_deref(), Some("header_tok"));
    }

    #[test]
    fn extract_token_returns_none_when_absent() {
        let h = header_map(&[]);
        assert!(extract_access_token(&h).is_none());
    }

    #[test]
    fn extract_token_skips_non_bearer_authorization() {
        let h = header_map(&[("authorization", "Basic abc")]);
        assert!(extract_access_token(&h).is_none());
    }

    #[test]
    fn extract_token_handles_cookie_with_equals_in_value() {
        let h = header_map(&[("cookie", "luuniensuki_access=eyJ0eXAi=")]);
        assert_eq!(extract_access_token(&h).as_deref(), Some("eyJ0eXAi="));
    }
}
