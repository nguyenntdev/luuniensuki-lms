//! JWT authentication extractor.
//!
//! Task 1.16: extracts and verifies JWT tokens from Authorization header
//! or cookie. Uses `jsonwebtoken` crate with HS256.

use axum::{
    extract::{FromRequestParts, State},
    http::request::Parts,
};
use jsonwebtoken::{decode, DecodingKey, Validation, Algorithm};
use serde::{Deserialize, Serialize};
use uuid::Uuid;

use crate::error::AppError;

/// JWT claims matching Python's `backend/security.py::create_jwt_token`.
#[derive(Debug, Serialize, Deserialize)]
pub struct Claims {
    pub sub: String,
    pub iat: i64,
    pub exp: i64,
    #[serde(default)]
    pub role: Option<String>,
    #[serde(default, rename = "type")]
    pub token_type: Option<String>,
}

/// Authenticated user extracted from JWT.
#[derive(Debug, Clone)]
pub struct AuthUser {
    pub user_id: Uuid,
}

/// Extract the JWT token from the request (Authorization header or cookie).
fn extract_token(parts: &Parts) -> Option<String> {
    // Try Authorization: Bearer <token>
    if let Some(auth_header) = parts.headers.get("authorization") {
        if let Ok(value) = auth_header.to_str() {
            if let Some(token) = value.strip_prefix("Bearer ") {
                return Some(token.to_string());
            }
        }
    }

    // Try cookie: luuniensuki_access=<token>
    if let Some(cookie_header) = parts.headers.get("cookie") {
        if let Ok(cookies) = cookie_header.to_str() {
            for cookie in cookies.split(';') {
                let cookie = cookie.trim();
                if let Some(token) = cookie.strip_prefix("luuniensuki_access=") {
                    return Some(token.to_string());
                }
            }
        }
    }

    None
}

/// Verify a JWT token and return the claims.
pub fn verify_token(token: &str, secret: &str) -> Result<Claims, AppError> {
    let mut validation = Validation::new(Algorithm::HS256);
    validation.validate_exp = true;
    validation.required_spec_claims.clear();
    validation.required_spec_claims.insert("exp".to_string());
    validation.required_spec_claims.insert("sub".to_string());

    let key = DecodingKey::from_secret(secret.as_bytes());

    let token_data = decode::<Claims>(token, &key, &validation)
        .map_err(|_| AppError::Unauthorized)?;

    Ok(token_data.claims)
}

/// Axum extractor that validates the JWT and provides `AuthUser`.
/// Use as a handler parameter: `auth: AuthUser`.
impl<S> FromRequestParts<S> for AuthUser
where
    S: Send + Sync,
    crate::routes::AppState: FromRef<S>,
{
    type Rejection = AppError;

    async fn from_request_parts(parts: &mut Parts, state: &S) -> Result<Self, Self::Rejection> {
        let app_state = crate::routes::AppState::from_ref(state);

        let token = extract_token(parts).ok_or(AppError::Unauthorized)?;
        let claims = verify_token(&token, &app_state.jwt_secret)?;

        let user_id = Uuid::parse_str(&claims.sub).map_err(|_| AppError::Unauthorized)?;

        Ok(AuthUser { user_id })
    }
}

/// Re-export FromRef for use in the extractor impl.
use axum::extract::FromRef;

#[cfg(test)]
mod tests {
    use super::*;
    use jsonwebtoken::{encode, EncodingKey, Header};
    use chrono::Utc;

    fn make_token(secret: &str, exp_offset_secs: i64) -> String {
        let now = Utc::now().timestamp();
        let claims = Claims {
            sub: "550e8400-e29b-41d4-a716-446655440000".to_string(),
            iat: now,
            exp: now + exp_offset_secs,
            role: Some("user".to_string()),
            token_type: Some("access".to_string()),
        };
        encode(
            &Header::new(Algorithm::HS256),
            &claims,
            &EncodingKey::from_secret(secret.as_bytes()),
        )
        .unwrap()
    }

    #[test]
    fn verify_valid_token() {
        let secret = "test-secret-key";
        let token = make_token(secret, 3600);
        let claims = verify_token(&token, secret).unwrap();
        assert_eq!(claims.sub, "550e8400-e29b-41d4-a716-446655440000");
    }

    #[test]
    fn verify_expired_token_fails() {
        let secret = "test-secret-key";
        let token = make_token(secret, -3600);
        assert!(verify_token(&token, secret).is_err());
    }

    #[test]
    fn verify_wrong_secret_fails() {
        let token = make_token("correct-secret", 3600);
        assert!(verify_token(&token, "wrong-secret").is_err());
    }
}
