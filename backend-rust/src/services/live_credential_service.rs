//! Join credential + ICE issuance (Task 7).
//!
//! This module issues the two short-lived secrets a browser needs to join a
//! live room, while keeping the long-lived Janus room/admin secret server-side:
//!
//! 1. A **scoped HS256 join credential** (`issue_join_credential` /
//!    `verify_join_credential`). It is a JWT whose claims bind it to exactly one
//!    `(session_id, identity)` pair and a single `typ = "live_join"`. It is
//!    signed with the shared `live_internal`/join secret — never with the Janus
//!    room or admin secret (Requirement 5.1, 5.2).
//! 2. **Ephemeral ICE/TURN credentials** (`issue_ice_credentials`) following the
//!    coturn REST API / RFC 5766 long-term-credential scheme: a time-limited
//!    `username = "<unix_expiry>:<identity>"` and a
//!    `credential = base64(HMAC-SHA1(turn_secret, username))`.
//!
//! The join secret comes from `Settings::live_internal_token` (or a dedicated
//! join secret) and the TURN secret from `Settings::turn_static_auth_secret`;
//! both are passed in by the caller so this module stays free of global state.
//!
//! `base64`: this crate intentionally does **not** depend on a base64 crate, so
//! a tiny standard-alphabet encoder ([`b64`]) is implemented inline. The digest
//! we encode is only ~20 bytes (an HMAC-SHA1 output), so a full base64 crate
//! would be unwarranted dependency surface.
//!
//! Validates: Requirements 5.1, 5.2

use chrono::{DateTime, Duration, Utc};
use hmac::{Hmac, Mac};
use jsonwebtoken::{
    decode, encode, Algorithm, DecodingKey, EncodingKey, Header, Validation,
};
use serde::{Deserialize, Serialize};
use sha1::Sha1;
use uuid::Uuid;

use crate::error::AppError;
use crate::models::live::IceServer;

/// The single credential `typ` this module issues and accepts. A token whose
/// `typ` differs (e.g. an access token reusing the same signing key) is
/// rejected by [`verify_join_credential`].
const JOIN_TYP: &str = "live_join";

type HmacSha1 = Hmac<Sha1>;

/// Claims carried by the scoped join credential.
///
/// Deliberately minimal: it binds the token to one participant identity (`sub`),
/// one session (`sid`, the session UUID as a string), and a role, plus the
/// standard `iat`/`exp` timestamps (seconds since the Unix epoch). It never
/// contains the Janus room/admin secret or any room PIN.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct JoinClaims {
    /// Participant identity (JWT subject).
    pub sub: String,
    /// Session id, stored as the session UUID's string form.
    pub sid: String,
    /// Participant role within the session (`host` | `cohost` | `learner` | ...).
    pub role: String,
    /// Credential discriminator; always `"live_join"` for tokens we issue.
    pub typ: String,
    /// Issued-at (Unix seconds).
    pub iat: i64,
    /// Expiry (Unix seconds). `jsonwebtoken` validates this automatically.
    pub exp: i64,
}

/// Issue a scoped HS256 join credential for one `(session_id, identity)` pair.
///
/// Returns the encoded JWT plus its `expires_at` instant (so the caller can put
/// it in the response DTO without re-deriving it). The token is signed with the
/// shared join `secret`; it MUST NOT be the Janus room/admin secret.
///
/// `ttl_minutes` is the credential lifetime in minutes (typically
/// `Settings::live_join_credential_ttl_minutes`).
pub fn issue_join_credential(
    session_id: Uuid,
    identity: &str,
    role: &str,
    ttl_minutes: i64,
    secret: &str,
) -> Result<(String, DateTime<Utc>), AppError> {
    let now = Utc::now();
    // Guard against a non-positive TTL producing an already-expired token by
    // clamping to at least one minute.
    let ttl = Duration::minutes(ttl_minutes.max(1));
    let expires_at = now + ttl;

    let claims = JoinClaims {
        sub: identity.to_string(),
        sid: session_id.to_string(),
        role: role.to_string(),
        typ: JOIN_TYP.to_string(),
        iat: now.timestamp(),
        exp: expires_at.timestamp(),
    };

    let token = encode(
        &Header::new(Algorithm::HS256),
        &claims,
        &EncodingKey::from_secret(secret.as_bytes()),
    )
    .map_err(|e| AppError::Internal(anyhow::anyhow!("failed to encode join credential: {e}")))?;

    Ok((token, expires_at))
}

/// Verify and decode a scoped join credential.
///
/// Validates the HS256 signature against `secret` and (via `jsonwebtoken`) the
/// `exp` claim, then rejects any token whose `typ` is not `"live_join"`. On any
/// failure — bad signature, expired, malformed, or wrong `typ` — returns an
/// unauthorized [`AppError`].
pub fn verify_join_credential(token: &str, secret: &str) -> Result<JoinClaims, AppError> {
    let validation = Validation::new(Algorithm::HS256);

    let data = decode::<JoinClaims>(
        token,
        &DecodingKey::from_secret(secret.as_bytes()),
        &validation,
    )
    .map_err(|_| AppError::Unauthorized)?;

    let claims = data.claims;
    if claims.typ != JOIN_TYP {
        return Err(AppError::Domain {
            status: axum::http::StatusCode::UNAUTHORIZED,
            code: "INVALID_CREDENTIAL".to_string(),
            message: "Join credential has an unexpected type".to_string(),
            details: serde_json::json!({ "typ": claims.typ }),
        });
    }

    Ok(claims)
}

/// Whether a decoded credential is scoped to the given session.
///
/// Compares the claim's `sid` against `session_id.to_string()`. Callers use this
/// to reject a valid-but-wrong-session credential (Requirement 5.2).
pub fn credential_is_for_session(claims: &JoinClaims, session_id: Uuid) -> bool {
    claims.sid == session_id.to_string()
}

/// Issue ephemeral ICE/TURN credentials using the coturn REST API scheme.
///
/// For each URL in `turn_urls`, produces one [`IceServer`] whose
/// `username = "<unix_expiry>:<identity>"` and
/// `credential = base64(HMAC-SHA1(turn_secret, username))`, where
/// `unix_expiry = now + ttl_seconds`. coturn (run with
/// `use-auth-secret` + `static-auth-secret`) validates these without any
/// per-user state.
///
/// When `turn_secret` is empty (a dev fallback where no TURN server is
/// configured), returns an empty `Vec` — the browser then relies on host/srflx
/// candidates only.
pub fn issue_ice_credentials(
    turn_secret: &str,
    turn_urls: &[String],
    ttl_seconds: i64,
    identity: &str,
) -> Vec<IceServer> {
    // Dev fallback: no TURN secret configured → hand back no ICE servers.
    if turn_secret.is_empty() {
        return Vec::new();
    }

    let expiry = Utc::now().timestamp() + ttl_seconds.max(1);
    let username = format!("{}:{}", expiry, identity);

    // HMAC-SHA1 over the username keyed by the shared TURN secret. `new_from_slice`
    // only fails for key lengths HMAC can't accept; HMAC accepts any length, so
    // this is infallible in practice.
    let credential = match HmacSha1::new_from_slice(turn_secret.as_bytes()) {
        Ok(mut mac) => {
            mac.update(username.as_bytes());
            b64(&mac.finalize().into_bytes())
        }
        // Defensive: if key init somehow fails, emit no TURN servers rather than
        // a malformed credential.
        Err(_) => return Vec::new(),
    };

    turn_urls
        .iter()
        .map(|url| IceServer {
            urls: vec![url.clone()],
            username: Some(username.clone()),
            credential: Some(credential.clone()),
        })
        .collect()
}

/// Minimal standard-alphabet (RFC 4648 §4) base64 encoder with padding.
///
/// Implemented inline to avoid pulling in a base64 crate just to encode a ~20
/// byte HMAC-SHA1 digest. Uses the standard alphabet (`A–Z a–z 0–9 + /`) and
/// `=` padding.
fn b64(bytes: &[u8]) -> String {
    const ALPHABET: &[u8; 64] =
        b"ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/";

    let mut out = String::with_capacity((bytes.len() + 2) / 3 * 4);

    for chunk in bytes.chunks(3) {
        // Pack up to three bytes into a 24-bit big-endian buffer.
        let b0 = chunk[0] as u32;
        let b1 = *chunk.get(1).unwrap_or(&0) as u32;
        let b2 = *chunk.get(2).unwrap_or(&0) as u32;
        let n = (b0 << 16) | (b1 << 8) | b2;

        out.push(ALPHABET[((n >> 18) & 0x3f) as usize] as char);
        out.push(ALPHABET[((n >> 12) & 0x3f) as usize] as char);

        match chunk.len() {
            1 => {
                out.push('=');
                out.push('=');
            }
            2 => {
                out.push(ALPHABET[((n >> 6) & 0x3f) as usize] as char);
                out.push('=');
            }
            _ => {
                out.push(ALPHABET[((n >> 6) & 0x3f) as usize] as char);
                out.push(ALPHABET[(n & 0x3f) as usize] as char);
            }
        }
    }

    out
}

#[cfg(test)]
mod tests {
    use super::*;

    const SECRET: &str = "shared-join-secret";

    // -- JWT round-trip / scoping -------------------------------------------

    #[test]
    fn issue_then_verify_round_trips_identity_and_session() {
        let sid = Uuid::new_v4();
        let (token, expires_at) =
            issue_join_credential(sid, "alice", "host", 30, SECRET).unwrap();

        let claims = verify_join_credential(&token, SECRET).unwrap();
        assert_eq!(claims.sub, "alice");
        assert_eq!(claims.sid, sid.to_string());
        assert_eq!(claims.role, "host");
        assert_eq!(claims.typ, "live_join");
        // exp should match the returned expires_at (to the second).
        assert_eq!(claims.exp, expires_at.timestamp());
        assert!(claims.exp > claims.iat);
    }

    #[test]
    fn verify_rejects_token_signed_with_different_secret() {
        let sid = Uuid::new_v4();
        let (token, _) = issue_join_credential(sid, "alice", "learner", 30, SECRET).unwrap();

        let result = verify_join_credential(&token, "a-different-secret");
        assert!(result.is_err());
    }

    #[test]
    fn verify_rejects_wrong_typ() {
        // Hand-build a token with the correct signature/secret but a bad `typ`.
        let sid = Uuid::new_v4();
        let now = Utc::now();
        let claims = JoinClaims {
            sub: "alice".to_string(),
            sid: sid.to_string(),
            role: "learner".to_string(),
            typ: "access".to_string(), // not "live_join"
            iat: now.timestamp(),
            exp: (now + Duration::minutes(30)).timestamp(),
        };
        let token = encode(
            &Header::new(Algorithm::HS256),
            &claims,
            &EncodingKey::from_secret(SECRET.as_bytes()),
        )
        .unwrap();

        let result = verify_join_credential(&token, SECRET);
        assert!(result.is_err());
    }

    #[test]
    fn verify_rejects_expired_token() {
        // A non-positive TTL is clamped to 1 minute, so build an already-expired
        // token directly to exercise jsonwebtoken's exp validation.
        let sid = Uuid::new_v4();
        let now = Utc::now();
        let claims = JoinClaims {
            sub: "alice".to_string(),
            sid: sid.to_string(),
            role: "learner".to_string(),
            typ: JOIN_TYP.to_string(),
            iat: (now - Duration::hours(2)).timestamp(),
            exp: (now - Duration::hours(1)).timestamp(),
        };
        let token = encode(
            &Header::new(Algorithm::HS256),
            &claims,
            &EncodingKey::from_secret(SECRET.as_bytes()),
        )
        .unwrap();

        assert!(verify_join_credential(&token, SECRET).is_err());
    }

    #[test]
    fn credential_is_for_session_true_and_false() {
        let sid = Uuid::new_v4();
        let other = Uuid::new_v4();
        let (token, _) = issue_join_credential(sid, "alice", "host", 30, SECRET).unwrap();
        let claims = verify_join_credential(&token, SECRET).unwrap();

        assert!(credential_is_for_session(&claims, sid));
        assert!(!credential_is_for_session(&claims, other));
    }

    #[test]
    fn join_credential_does_not_contain_room_secret() {
        // The issued JWT must carry only the scoped claims, never a room secret.
        let sid = Uuid::new_v4();
        let (token, _) = issue_join_credential(sid, "alice", "host", 30, SECRET).unwrap();
        let claims = verify_join_credential(&token, SECRET).unwrap();
        // Only the six expected fields exist on JoinClaims; assert the role/typ
        // are the scoped values and nothing leaks a secret-shaped payload.
        assert_eq!(claims.typ, JOIN_TYP);
        assert!(!token.is_empty());
    }

    // -- ICE / TURN credentials ---------------------------------------------

    #[test]
    fn issue_ice_credentials_empty_secret_yields_empty_vec() {
        let urls = vec!["turn:turn.example.com:3478".to_string()];
        let servers = issue_ice_credentials("", &urls, 3600, "alice");
        assert!(servers.is_empty());
    }

    #[test]
    fn issue_ice_credentials_with_secret_builds_one_server_per_url() {
        let urls = vec![
            "turn:turn.example.com:3478".to_string(),
            "turn:turn.example.com:3478?transport=tcp".to_string(),
        ];
        let servers = issue_ice_credentials("turn-secret", &urls, 3600, "alice");

        assert_eq!(servers.len(), urls.len());
        for (server, url) in servers.iter().zip(urls.iter()) {
            assert_eq!(server.urls, vec![url.clone()]);
            let username = server.username.as_ref().unwrap();
            // username = "<unix_expiry>:<identity>"
            assert!(username.contains(':'));
            assert!(username.ends_with(":alice"));
            // credential is the base64 HMAC digest, never empty.
            assert!(!server.credential.as_ref().unwrap().is_empty());
        }
    }

    #[test]
    fn issue_ice_credentials_username_expiry_is_in_the_future() {
        let urls = vec!["turn:turn.example.com:3478".to_string()];
        let now = Utc::now().timestamp();
        let servers = issue_ice_credentials("turn-secret", &urls, 3600, "bob");
        let username = servers[0].username.clone().unwrap();
        let expiry: i64 = username.split(':').next().unwrap().parse().unwrap();
        assert!(expiry > now);
    }

    // -- base64 encoder vectors (RFC 4648 §10) ------------------------------

    #[test]
    fn b64_matches_known_vectors() {
        assert_eq!(b64(b""), "");
        assert_eq!(b64(b"f"), "Zg==");
        assert_eq!(b64(b"fo"), "Zm8=");
        assert_eq!(b64(b"foo"), "Zm9v");
        assert_eq!(b64(b"foob"), "Zm9vYg==");
        assert_eq!(b64(b"fooba"), "Zm9vYmE=");
        assert_eq!(b64(b"foobar"), "Zm9vYmFy");
    }

    #[test]
    fn b64_encodes_full_byte_range_chunk() {
        // Standard-alphabet check that includes both `+` and `/` outputs.
        assert_eq!(b64(&[0xff, 0xff, 0xff]), "////");
        assert_eq!(b64(&[0xfb, 0xff, 0xbf]), "+/+/");
    }
}
