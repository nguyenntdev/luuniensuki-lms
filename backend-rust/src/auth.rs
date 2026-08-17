//! JWT token issuance/verification and password hashing/verification.
//!
//! Task 3.1: implements auth foundations matching `backend/security.py`.
//! - HS256 JWT with claims `{sub, iat, exp, role, type}`.
//! - Password verification dispatching on hash prefix (bcrypt / argon2).
//! - New password hashing uses bcrypt with cost 12 (matching Python's passlib).

use chrono::Utc;
use jsonwebtoken::{decode, encode, DecodingKey, EncodingKey, Header, Validation};
use serde::{Deserialize, Serialize};
use uuid::Uuid;

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
    /// Token issuer (Req 26.3). `#[serde(default)]` lets us decode older
    /// tokens issued before this claim existed (they deserialize to ""),
    /// preserving the issue-then-enforce transition (enforcement: Task 6.4).
    #[serde(default)]
    pub iss: String,
    /// Intended audience (Req 26.3). Defaulted for the same transition reason.
    #[serde(default)]
    pub aud: String,
    /// Unique token id, enabling refresh-token revocation (Task 7).
    /// Defaulted so pre-existing tokens without a `jti` still decode.
    #[serde(default)]
    pub jti: String,
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
    issuer: &str,
    audience: &str,
) -> Result<String, AuthError> {
    let now = Utc::now().timestamp();
    let claims = Claims {
        sub: user_id.to_string(),
        iat: now,
        exp: now + (expire_minutes * 60),
        role: role.to_string(),
        token_type: "access".to_string(),
        iss: issuer.to_string(),
        aud: audience.to_string(),
        jti: Uuid::new_v4().to_string(),
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
    issuer: &str,
    audience: &str,
) -> Result<String, AuthError> {
    let now = Utc::now().timestamp();
    let claims = Claims {
        sub: user_id.to_string(),
        iat: now,
        exp: now + (expire_days * 24 * 60 * 60),
        role: role.to_string(),
        token_type: "refresh".to_string(),
        iss: issuer.to_string(),
        aud: audience.to_string(),
        jti: Uuid::new_v4().to_string(),
    };
    let token = encode(
        &Header::default(),
        &claims,
        &EncodingKey::from_secret(secret.as_bytes()),
    )?;
    Ok(token)
}

/// Verify an access token. Rejects tokens whose `type` is not `"access"`.
///
/// `validate_new_claims` gates the issue-then-enforce transition for the
/// `iss`/`aud` identity claims (Req 26.4). When `false` (the transition
/// default) only `exp` is required, so tokens issued before either backend
/// emitted `iss`/`aud` are still accepted. When `true`, both backends are
/// known to issue the new claims, so `iss`/`aud` become required and are
/// validated against the configured `issuer`/`audience`; a mismatch is
/// rejected. The flag MUST only be enabled once both backends issue the
/// claims, otherwise cross-backend auth breaks (Req 26).
pub fn verify_access_token(
    token: &str,
    secret: &str,
    validate_new_claims: bool,
    issuer: &str,
    audience: &str,
) -> Result<Claims, AuthError> {
    let mut validation = Validation::default();
    validation.validate_exp = true;
    if validate_new_claims {
        // Both backends now issue `iss`/`aud`; require and validate them.
        validation.set_required_spec_claims(&["exp", "iss", "aud"]);
        validation.set_issuer(&[issuer]);
        validation.set_audience(&[audience]);
    } else {
        // Transition state: only `exp` is required so tokens lacking
        // `iss`/`aud` are still accepted (previously `required_spec_claims
        // .clear()` allowed never-expiring tokens). jsonwebtoken defaults
        // `validate_aud` to true, so audience validation must be disabled
        // explicitly to mirror the Python verifier's `verify_aud: False`
        // transition behavior — otherwise tokens that carry `aud` are
        // rejected even though the flag is off (cross-backend parity, Req 26.4).
        validation.set_required_spec_claims(&["exp"]);
        validation.validate_aud = false;
    }

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
///
/// `validate_new_claims` gates the issue-then-enforce transition for the
/// `iss`/`aud` identity claims (Req 26.4); see [`verify_access_token`] for
/// the full rationale.
pub fn verify_refresh_token(
    token: &str,
    secret: &str,
    validate_new_claims: bool,
    issuer: &str,
    audience: &str,
) -> Result<Claims, AuthError> {
    let mut validation = Validation::default();
    validation.validate_exp = true;
    if validate_new_claims {
        // Both backends now issue `iss`/`aud`; require and validate them.
        validation.set_required_spec_claims(&["exp", "iss", "aud"]);
        validation.set_issuer(&[issuer]);
        validation.set_audience(&[audience]);
    } else {
        // Transition state: only `exp` is required so tokens lacking
        // `iss`/`aud` are still accepted. `validate_aud` defaults to true in
        // jsonwebtoken; disable it to mirror the Python verifier's
        // `verify_aud: False` transition behavior (cross-backend parity, Req 26.4).
        validation.set_required_spec_claims(&["exp"]);
        validation.validate_aud = false;
    }

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
    const TEST_ISSUER: &str = "luuniensuki";
    const TEST_AUDIENCE: &str = "luuniensuki-app";

    #[test]
    fn issue_and_verify_access_token_roundtrip() {
        let token =
            issue_access_token("user-123", "admin", TEST_SECRET, 60, TEST_ISSUER, TEST_AUDIENCE)
                .unwrap();
        let claims = verify_access_token(&token, TEST_SECRET, false, TEST_ISSUER, TEST_AUDIENCE)
            .unwrap();

        assert_eq!(claims.sub, "user-123");
        assert_eq!(claims.role, "admin");
        assert_eq!(claims.token_type, "access");
        assert_eq!(claims.iss, TEST_ISSUER);
        assert_eq!(claims.aud, TEST_AUDIENCE);
        assert!(!claims.jti.is_empty());
        assert!(claims.exp > claims.iat);
        assert_eq!(claims.exp - claims.iat, 60 * 60); // 60 minutes
    }

    #[test]
    fn issue_and_verify_refresh_token_roundtrip() {
        let token =
            issue_refresh_token("user-456", "teacher", TEST_SECRET, 7, TEST_ISSUER, TEST_AUDIENCE)
                .unwrap();
        let claims = verify_refresh_token(&token, TEST_SECRET, false, TEST_ISSUER, TEST_AUDIENCE)
            .unwrap();

        assert_eq!(claims.sub, "user-456");
        assert_eq!(claims.role, "teacher");
        assert_eq!(claims.token_type, "refresh");
        assert_eq!(claims.iss, TEST_ISSUER);
        assert_eq!(claims.aud, TEST_AUDIENCE);
        assert!(!claims.jti.is_empty());
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
            iss: TEST_ISSUER.to_string(),
            aud: TEST_AUDIENCE.to_string(),
            jti: Uuid::new_v4().to_string(),
        };
        let token = encode(
            &Header::default(),
            &claims,
            &EncodingKey::from_secret(TEST_SECRET.as_bytes()),
        )
        .unwrap();

        let result = verify_access_token(&token, TEST_SECRET, false, TEST_ISSUER, TEST_AUDIENCE);
        assert!(result.is_err());
        match result.unwrap_err() {
            AuthError::Jwt(e) => {
                assert!(e.to_string().contains("ExpiredSignature"));
            }
            other => panic!("expected Jwt error, got: {:?}", other),
        }
    }

    #[test]
    fn verify_access_token_rejects_missing_exp() {
        // Craft a raw token whose claims lack `exp`. Encoding a serde_json map
        // (rather than the `Claims` struct, whose `exp` is non-optional) lets us
        // omit the claim entirely. With `set_required_spec_claims(&["exp"])` the
        // verifier must reject it instead of treating it as never-expiring.
        let now = Utc::now().timestamp();
        let claims = serde_json::json!({
            "sub": "user-no-exp",
            "iat": now,
            "role": "user",
            "type": "access",
        });
        let token = encode(
            &Header::default(),
            &claims,
            &EncodingKey::from_secret(TEST_SECRET.as_bytes()),
        )
        .unwrap();

        let result = verify_access_token(&token, TEST_SECRET, false, TEST_ISSUER, TEST_AUDIENCE);
        assert!(result.is_err(), "token missing exp must be rejected");
    }

    #[test]
    fn verify_refresh_token_rejects_missing_exp() {
        let now = Utc::now().timestamp();
        let claims = serde_json::json!({
            "sub": "user-no-exp",
            "iat": now,
            "role": "user",
            "type": "refresh",
        });
        let token = encode(
            &Header::default(),
            &claims,
            &EncodingKey::from_secret(TEST_SECRET.as_bytes()),
        )
        .unwrap();

        let result = verify_refresh_token(&token, TEST_SECRET, false, TEST_ISSUER, TEST_AUDIENCE);
        assert!(result.is_err(), "token missing exp must be rejected");
    }

    #[test]
    fn verify_access_token_rejects_refresh_token() {
        let token = issue_refresh_token("user-111", "user", TEST_SECRET, 7, TEST_ISSUER, TEST_AUDIENCE).unwrap();
        let result = verify_access_token(&token, TEST_SECRET, false, TEST_ISSUER, TEST_AUDIENCE);
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
        let token = issue_access_token("user-222", "user", TEST_SECRET, 60, TEST_ISSUER, TEST_AUDIENCE).unwrap();
        let result = verify_refresh_token(&token, TEST_SECRET, false, TEST_ISSUER, TEST_AUDIENCE);
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
        let token = issue_access_token("user-333", "user", TEST_SECRET, 60, TEST_ISSUER, TEST_AUDIENCE).unwrap();
        let result = verify_access_token(&token, "wrong-secret", false, TEST_ISSUER, TEST_AUDIENCE);
        assert!(result.is_err());
    }

    #[test]
    fn verify_access_token_validates_new_claims_when_enabled() {
        // With the transition flag ON, a token carrying the correct
        // `iss`/`aud` (as issued by `issue_access_token`) must pass.
        let token =
            issue_access_token("user-444", "user", TEST_SECRET, 60, TEST_ISSUER, TEST_AUDIENCE)
                .unwrap();
        let claims =
            verify_access_token(&token, TEST_SECRET, true, TEST_ISSUER, TEST_AUDIENCE).unwrap();
        assert_eq!(claims.iss, TEST_ISSUER);
        assert_eq!(claims.aud, TEST_AUDIENCE);

        // A token with the wrong issuer must be rejected when enforcement is on.
        let wrong_issuer_token =
            issue_access_token("user-555", "user", TEST_SECRET, 60, "evil-issuer", TEST_AUDIENCE)
                .unwrap();
        let result =
            verify_access_token(&wrong_issuer_token, TEST_SECRET, true, TEST_ISSUER, TEST_AUDIENCE);
        assert!(
            result.is_err(),
            "token with mismatched issuer must be rejected when validate_new_claims is true"
        );
    }

    // --- Task 14.2: JWT decode-contract tests ------------------------------
    // Property 1 (No-forge) and Property 2 (Expiry-required) for the Rust
    // verify path, mirroring tests/backend/test_jwt_contract.py on the Python
    // side. Each case is checked under both transition states so a rejection
    // never passes for the wrong reason. Validates Requirements 8.2, 26.2.

    /// A currently-valid access-token claim set (future `exp`, correct
    /// `iss`/`aud`, `type = access`). Tests mutate fields to build rejections.
    fn valid_access_claims() -> Claims {
        let now = Utc::now().timestamp();
        Claims {
            sub: "contract-user".to_string(),
            iat: now,
            exp: now + 3600,
            role: "user".to_string(),
            token_type: "access".to_string(),
            iss: TEST_ISSUER.to_string(),
            aud: TEST_AUDIENCE.to_string(),
            jti: Uuid::new_v4().to_string(),
        }
    }

    /// Property 1 (No-forge): a token signed with a *different* `EncodingKey`
    /// than the configured secret is rejected, even though every claim is
    /// otherwise valid (so the signature mismatch is the sole cause).
    #[test]
    fn contract_no_forge_wrong_key_rejected() {
        let token = encode(
            &Header::default(),
            &valid_access_claims(),
            &EncodingKey::from_secret(b"a-totally-different-secret-key-not-configured"),
        )
        .unwrap();

        assert!(
            verify_access_token(&token, TEST_SECRET, false, TEST_ISSUER, TEST_AUDIENCE).is_err(),
            "token signed with wrong key must be rejected"
        );
        assert!(
            verify_access_token(&token, TEST_SECRET, true, TEST_ISSUER, TEST_AUDIENCE).is_err(),
            "wrong-key token must be rejected with new-claim enforcement on"
        );
    }

    /// Property 2 (Expiry-required): a correctly-signed token that omits `exp`
    /// is rejected. Encoding a JSON map (not the `Claims` struct, whose `exp`
    /// is non-optional) lets us drop the claim entirely.
    #[test]
    fn contract_expiry_required_missing_exp_rejected() {
        let now = Utc::now().timestamp();
        let claims = serde_json::json!({
            "sub": "contract-user",
            "iat": now,
            "role": "user",
            "type": "access",
            "iss": TEST_ISSUER,
            "aud": TEST_AUDIENCE,
        });
        let token = encode(
            &Header::default(),
            &claims,
            &EncodingKey::from_secret(TEST_SECRET.as_bytes()),
        )
        .unwrap();

        assert!(
            verify_access_token(&token, TEST_SECRET, false, TEST_ISSUER, TEST_AUDIENCE).is_err(),
            "token missing exp must be rejected"
        );
        assert!(
            verify_access_token(&token, TEST_SECRET, true, TEST_ISSUER, TEST_AUDIENCE).is_err(),
            "token missing exp must be rejected with new-claim enforcement on"
        );
    }

    /// Property 2 (Expiry-required): a correctly-signed token whose `exp` is in
    /// the past is rejected, independent of the transition flag.
    #[test]
    fn contract_expiry_required_past_exp_rejected() {
        let now = Utc::now().timestamp();
        let mut claims = valid_access_claims();
        claims.iat = now - 7200;
        claims.exp = now - 3600; // expired one hour ago
        let token = encode(
            &Header::default(),
            &claims,
            &EncodingKey::from_secret(TEST_SECRET.as_bytes()),
        )
        .unwrap();

        assert!(
            verify_access_token(&token, TEST_SECRET, false, TEST_ISSUER, TEST_AUDIENCE).is_err(),
            "token with past exp must be rejected"
        );
        assert!(
            verify_access_token(&token, TEST_SECRET, true, TEST_ISSUER, TEST_AUDIENCE).is_err(),
            "token with past exp must be rejected with new-claim enforcement on"
        );
    }

    // --- Task 14.4: Cross-backend contract test ---------------------------
    // Validates Correctness Property 4 (Cross-backend acceptance): a token
    // issued by one backend under the consistent contract validates in the
    // other, and is rejected whenever standard validation fails. The Python
    // half lives in tests/backend/test_cross_backend_contract.py.
    //
    // A live cross-process test is impossible here (no running Python service),
    // so we simulate a "Python-issued" token by minting a raw token whose claim
    // shape EXACTLY matches `backend/security.py::create_jwt_token`
    // ({sub, iat, exp, jti, iss, aud} plus the access `type`/`role` extra
    // claims), signed with the shared TEST_SECRET, then assert the Rust
    // `verify_access_token` accepts/rejects it per the consistent contract.
    // Validates Requirements 8.2, 26.2.

    /// A claim set matching what the Python `create_jwt_token` emits for an
    /// access token: the shared `{sub, iat, exp, jti, iss, aud}` identity
    /// claims plus `type = "access"` and a `role`. Both backends use the same
    /// `Claims` struct/field names, so this is what a live Python issuer would
    /// produce. Future `exp`, correct `iss`/`aud`.
    fn python_issued_access_claims() -> Claims {
        let now = Utc::now().timestamp();
        Claims {
            sub: "python-contract-user".to_string(),
            iat: now,
            exp: now + 3600,
            role: "user".to_string(),
            token_type: "access".to_string(),
            iss: TEST_ISSUER.to_string(),
            aud: TEST_AUDIENCE.to_string(),
            jti: Uuid::new_v4().to_string(),
        }
    }

    /// Property 4 (acceptance direction): a token built with the Python
    /// issuer's exact claim shape, signed with the shared secret, is accepted
    /// by the Rust verifier under BOTH transition states. With the flag on the
    /// matching `iss`/`aud` are required and validated; with it off they are
    /// simply accepted.
    #[test]
    fn cross_backend_python_issued_token_accepted() {
        let token = encode(
            &Header::default(),
            &python_issued_access_claims(),
            &EncodingKey::from_secret(TEST_SECRET.as_bytes()),
        )
        .unwrap();

        let claims_off =
            verify_access_token(&token, TEST_SECRET, false, TEST_ISSUER, TEST_AUDIENCE)
                .expect("peer-issued token must be accepted with transition flag off");
        assert_eq!(claims_off.sub, "python-contract-user");
        assert_eq!(claims_off.token_type, "access");

        let claims_on =
            verify_access_token(&token, TEST_SECRET, true, TEST_ISSUER, TEST_AUDIENCE)
                .expect("peer-issued token must be accepted with new-claim enforcement on");
        assert_eq!(claims_on.iss, TEST_ISSUER);
        assert_eq!(claims_on.aud, TEST_AUDIENCE);
    }

    /// Property 4 (rejection direction): a peer-issued token is rejected
    /// whenever standard validation fails — here for a wrong signing key and
    /// for a past `exp` — under both transition states.
    #[test]
    fn cross_backend_peer_token_rejected_when_standard_validation_fails() {
        // Wrong-key peer token: otherwise valid claims, signed with a secret
        // the verifier is not configured with.
        let wrong_key_token = encode(
            &Header::default(),
            &python_issued_access_claims(),
            &EncodingKey::from_secret(b"a-totally-different-secret-key-not-configured"),
        )
        .unwrap();
        assert!(
            verify_access_token(&wrong_key_token, TEST_SECRET, false, TEST_ISSUER, TEST_AUDIENCE)
                .is_err(),
            "wrong-key peer token must be rejected (transition flag off)"
        );
        assert!(
            verify_access_token(&wrong_key_token, TEST_SECRET, true, TEST_ISSUER, TEST_AUDIENCE)
                .is_err(),
            "wrong-key peer token must be rejected (new-claim enforcement on)"
        );

        // Past-exp peer token: correctly signed but expired one hour ago.
        let now = Utc::now().timestamp();
        let mut expired = python_issued_access_claims();
        expired.iat = now - 7200;
        expired.exp = now - 3600;
        let expired_token = encode(
            &Header::default(),
            &expired,
            &EncodingKey::from_secret(TEST_SECRET.as_bytes()),
        )
        .unwrap();
        assert!(
            verify_access_token(&expired_token, TEST_SECRET, false, TEST_ISSUER, TEST_AUDIENCE)
                .is_err(),
            "past-exp peer token must be rejected (transition flag off)"
        );
        assert!(
            verify_access_token(&expired_token, TEST_SECRET, true, TEST_ISSUER, TEST_AUDIENCE)
                .is_err(),
            "past-exp peer token must be rejected (new-claim enforcement on)"
        );
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
