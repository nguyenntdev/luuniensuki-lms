//! JWT token issuance/verification and password hashing/verification.
//!
//! Task 3.1: implements auth foundations matching `backend/security.py`.
//! - HS256 JWT with claims `{sub, iat, exp, role, type}`.
//! - Password verification dispatching on hash prefix (bcrypt / argon2).
//! - New password hashing uses bcrypt with cost 12 (matching Python's passlib).

use chrono::Utc;
use jsonwebtoken::{decode, encode, DecodingKey, EncodingKey, Header, Validation};
use serde::{Deserialize, Serialize};

/// JWT claims matching `backend/security.py::create_jwt_token`.
///
/// Both Python and Rust services share the same JWT secret and produce
/// tokens with identical claim shapes so that tokens issued by either
/// service are accepted by the other (Req 5.1, 5.2).
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct Claims {
    /// User UUID as string (matches Python's `sub` field).
    pub sub: String,
    /// Issued-at timestamp (unix seconds).
    pub iat: i64,
    /// Expiry timestamp (unix seconds).
    pub exp: i64,
    /// User role: "user", "admin", "teacher".
    pub role: String,
    /// Token type: "access" or "refresh".
    #[serde(rename = "type")]
    pub token_type: String,
}

/// Auth-specific errors.
#[derive(Debug, thiserror::Error)]
pub enum AuthError {
    #[error("JWT error: {0}")]
    Jwt(#[from] jsonwebtoken::errors::Error),

    #[error("invalid token type: expected {expected}, got {actual}")]
    WrongTokenType { expected: String, actual: String },

    #[error("invalid or unsupported password hash format")]
    InvalidHash,

    #[error("bcrypt error: {0}")]
    Bcrypt(#[from] bcrypt::BcryptError),

    #[error("password too long (max 72 bytes for bcrypt)")]
    PasswordTooLong,
}

/// Maximum password length in bytes (bcrypt limitation).
const MAX_BCRYPT_PASSWORD_BYTES: usize = 72;

/// Issue an access token with HS256.
///
/// Claims match Python's `create_jwt_token` with `extra_claims={"type": "access", "role": role}`.
pub fn issue_access_token(
    user_id: &str,
    role: &str,
    secret: &str,
    expire_minutes: i64,
) -> Result<String, AuthError> {
    let now = Utc::now().timestamp();
    let claims = Claims {
        sub: user_id.to_string(),
        iat: now,
        exp: now + (expire_minutes * 60),
        role: role.to_string(),
        token_type: "access".to_string(),
    };
    let token = encode(
        &Header::default(), // HS256 is the default
        &claims,
        &EncodingKey::from_secret(secret.as_bytes()),
    )?;
    Ok(token)
}

/// Issue a refresh token with HS256.
///
/// Claims match Python's `create_jwt_token` with `extra_claims={"type": "refresh", "role": role}`.
pub fn issue_refresh_token(
    user_id: &str,
    role: &str,
    secret: &str,
    expire_days: i64,
) -> Result<String, AuthError> {
    let now = Utc::now().timestamp();
    let claims = Claims {
        sub: user_id.to_string(),
        iat: now,
        exp: now + (expire_days * 24 * 60 * 60),
        role: role.to_string(),
        token_type: "refresh".to_string(),
    };
    let token = encode(
        &Header::default(),
        &claims,
        &EncodingKey::from_secret(secret.as_bytes()),
    )?;
    Ok(token)
}

/// Verify an access token. Rejects tokens whose `type` is not `"access"`.
pub fn verify_access_token(token: &str, secret: &str) -> Result<Claims, AuthError> {
    let mut validation = Validation::default();
    validation.validate_exp = true;
    validation.required_spec_claims.clear();

    let token_data = decode::<Claims>(
        token,
        &DecodingKey::from_secret(secret.as_bytes()),
        &validation,
    )?;

    let claims = token_data.claims;
    if claims.token_type != "access" {
        return Err(AuthError::WrongTokenType {
            expected: "access".to_string(),
            actual: claims.token_type,
        });
    }

    Ok(claims)
}

/// Verify a refresh token. Rejects tokens whose `type` is not `"refresh"`.
pub fn verify_refresh_token(token: &str, secret: &str) -> Result<Claims, AuthError> {
    let mut validation = Validation::default();
    validation.validate_exp = true;
    validation.required_spec_claims.clear();

    let token_data = decode::<Claims>(
        token,
        &DecodingKey::from_secret(secret.as_bytes()),
        &validation,
    )?;

    let claims = token_data.claims;
    if claims.token_type != "refresh" {
        return Err(AuthError::WrongTokenType {
            expected: "refresh".to_string(),
            actual: claims.token_type,
        });
    }

    Ok(claims)
}

/// Verify a password against a stored hash.
///
/// Dispatches on hash prefix:
/// - `$2a$`, `$2b$`, `$2y$` → bcrypt
/// - `$argon2id$`, `$argon2i$` → argon2
///
/// Never rehashes on success (Req 5.3).
pub fn verify_password(password: &str, hash: &str) -> Result<bool, AuthError> {
    if hash.starts_with("$2a$") || hash.starts_with("$2b$") || hash.starts_with("$2y$") {
        // bcrypt verification
        Ok(bcrypt::verify(password, hash)?)
    } else if hash.starts_with("$argon2id$") || hash.starts_with("$argon2i$") {
        // argon2 verification
        use argon2::{Argon2, PasswordHash, PasswordVerifier};
        let parsed = PasswordHash::new(hash).map_err(|_| AuthError::InvalidHash)?;
        Ok(Argon2::default()
            .verify_password(password.as_bytes(), &parsed)
            .is_ok())
    } else {
        Err(AuthError::InvalidHash)
    }
}

/// Hash a password using bcrypt with cost 12 (matching Python's passlib default).
///
/// This is used for new registrations (Req 5.4).
pub fn hash_password(password: &str) -> Result<String, AuthError> {
    let password_bytes = password.as_bytes();
    if password_bytes.len() > MAX_BCRYPT_PASSWORD_BYTES {
        return Err(AuthError::PasswordTooLong);
    }
    Ok(bcrypt::hash(password, 12)?)
}

#[cfg(test)]
mod tests {
    use super::*;

    const TEST_SECRET: &str = "test-secret-key-for-unit-tests";

    #[test]
    fn issue_and_verify_access_token_roundtrip() {
        let token = issue_access_token("user-123", "admin", TEST_SECRET, 60).unwrap();
        let claims = verify_access_token(&token, TEST_SECRET).unwrap();

        assert_eq!(claims.sub, "user-123");
        assert_eq!(claims.role, "admin");
        assert_eq!(claims.token_type, "access");
        assert!(claims.exp > claims.iat);
        assert_eq!(claims.exp - claims.iat, 60 * 60); // 60 minutes
    }

    #[test]
    fn issue_and_verify_refresh_token_roundtrip() {
        let token = issue_refresh_token("user-456", "teacher", TEST_SECRET, 7).unwrap();
        let claims = verify_refresh_token(&token, TEST_SECRET).unwrap();

        assert_eq!(claims.sub, "user-456");
        assert_eq!(claims.role, "teacher");
        assert_eq!(claims.token_type, "refresh");
        assert!(claims.exp > claims.iat);
        assert_eq!(claims.exp - claims.iat, 7 * 24 * 60 * 60); // 7 days
    }

    #[test]
    fn verify_access_token_rejects_expired() {
        // Manually create an expired token
        let now = Utc::now().timestamp();
        let claims = Claims {
            sub: "user-789".to_string(),
            iat: now - 7200,
            exp: now - 3600, // expired 1 hour ago
            role: "user".to_string(),
            token_type: "access".to_string(),
        };
        let token = encode(
            &Header::default(),
            &claims,
            &EncodingKey::from_secret(TEST_SECRET.as_bytes()),
        )
        .unwrap();

        let result = verify_access_token(&token, TEST_SECRET);
        assert!(result.is_err());
        match result.unwrap_err() {
            AuthError::Jwt(e) => {
                assert!(e.to_string().contains("ExpiredSignature"));
            }
            other => panic!("expected Jwt error, got: {:?}", other),
        }
    }

    #[test]
    fn verify_access_token_rejects_refresh_token() {
        let token = issue_refresh_token("user-111", "user", TEST_SECRET, 7).unwrap();
        let result = verify_access_token(&token, TEST_SECRET);
        assert!(result.is_err());
        match result.unwrap_err() {
            AuthError::WrongTokenType { expected, actual } => {
                assert_eq!(expected, "access");
                assert_eq!(actual, "refresh");
            }
            other => panic!("expected WrongTokenType, got: {:?}", other),
        }
    }

    #[test]
    fn verify_refresh_token_rejects_access_token() {
        let token = issue_access_token("user-222", "user", TEST_SECRET, 60).unwrap();
        let result = verify_refresh_token(&token, TEST_SECRET);
        assert!(result.is_err());
        match result.unwrap_err() {
            AuthError::WrongTokenType { expected, actual } => {
                assert_eq!(expected, "refresh");
                assert_eq!(actual, "access");
            }
            other => panic!("expected WrongTokenType, got: {:?}", other),
        }
    }

    #[test]
    fn verify_access_token_rejects_wrong_secret() {
        let token = issue_access_token("user-333", "user", TEST_SECRET, 60).unwrap();
        let result = verify_access_token(&token, "wrong-secret");
        assert!(result.is_err());
    }

    #[test]
    fn verify_password_bcrypt() {
        let password = "my-secure-password";
        let hash = hash_password(password).unwrap();

        // Hash should start with bcrypt prefix
        assert!(
            hash.starts_with("$2b$") || hash.starts_with("$2a$") || hash.starts_with("$2y$")
        );

        // Correct password verifies
        assert!(verify_password(password, &hash).unwrap());

        // Wrong password does not verify
        assert!(!verify_password("wrong-password", &hash).unwrap());
    }

    #[test]
    fn verify_password_argon2id() {
        // Pre-computed argon2id hash for "test-password"
        // Generated with: argon2::hash_encoded(b"test-password", salt, &config)
        use argon2::{password_hash::SaltString, Argon2, PasswordHasher};
        let salt = SaltString::generate(&mut argon2::password_hash::rand_core::OsRng);
        let argon2 = Argon2::default();
        let hash = argon2
            .hash_password(b"test-password", &salt)
            .unwrap()
            .to_string();

        assert!(hash.starts_with("$argon2id$"));

        // Correct password verifies
        assert!(verify_password("test-password", &hash).unwrap());

        // Wrong password does not verify
        assert!(!verify_password("wrong-password", &hash).unwrap());
    }

    #[test]
    fn verify_password_rejects_unknown_hash_format() {
        let result = verify_password("password", "$unknown$hash");
        assert!(result.is_err());
        match result.unwrap_err() {
            AuthError::InvalidHash => {}
            other => panic!("expected InvalidHash, got: {:?}", other),
        }
    }

    #[test]
    fn hash_password_produces_verifiable_bcrypt() {
        let password = "another-password-123";
        let hash = hash_password(password).unwrap();

        // Should be bcrypt with cost 12
        assert!(hash.starts_with("$2b$12$"));

        // Should be verifiable
        assert!(verify_password(password, &hash).unwrap());
    }

    #[test]
    fn hash_password_rejects_too_long() {
        let long_password = "a".repeat(73);
        let result = hash_password(&long_password);
        assert!(result.is_err());
        match result.unwrap_err() {
            AuthError::PasswordTooLong => {}
            other => panic!("expected PasswordTooLong, got: {:?}", other),
        }
    }
}
