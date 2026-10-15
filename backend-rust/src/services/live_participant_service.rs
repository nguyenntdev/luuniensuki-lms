//! Live participant roster service (Task 9).
//!
//! Ports roster management from `backend/services/live_sessions.py`:
//! `upsert_participant_join`, `mark_participant_left`,
//! `ensure_ai_teacher_participant`, `update_participant_role`,
//! `participant_identity_for_user`, and `ai_teacher_identity_for_session`, plus
//! the Janus feed-binding / reconcile helpers used by the Rust + Janus path.
//!
//! Uses sqlx runtime queries (`query`, `query_as`) — NOT the compile-time
//! `query!` macro — matching the other service modules in this crate.
//!
//! `live_participants` columns (struct order — used verbatim in every
//! SELECT / RETURNING list so `query_as::<_, LiveParticipant>` lines up):
//!   id UUID, live_session_id UUID, user_id UUID NULL,
//!   participant_identity TEXT, display_name TEXT NULL, role TEXT,
//!   is_ai BOOL, joined_at TIMESTAMPTZ, left_at TIMESTAMPTZ NULL,
//!   connection_metadata JSONB, janus_feed_id BIGINT NULL,
//!   janus_handle_id BIGINT NULL
//!
//! The table carries UNIQUE constraints on both `(live_session_id,
//! participant_identity)` and `(live_session_id, user_id)`. Because a user's
//! identity is deterministic (`identity_for_user` → `user-<uuid>`), upserting on
//! the `(session, identity)` conflict target keeps both invariants in sync: one
//! row per identity is also one row per user.

use std::collections::BTreeSet;

use axum::http::StatusCode;
use sqlx::PgPool;
use uuid::Uuid;

use crate::error::AppError;
use crate::models::live::LiveParticipant;

/// Full column list (struct order) reused by every SELECT / RETURNING clause.
const PARTICIPANT_COLUMNS: &str = "\
    id, live_session_id, user_id, participant_identity, display_name, \
    role, is_ai, joined_at, left_at, connection_metadata, \
    janus_feed_id, janus_handle_id";

// ---------------------------------------------------------------------------
// Pure identity helpers
// ---------------------------------------------------------------------------

/// Deterministic participant identity for a real user account.
///
/// Mirrors Python `participant_identity_for_user` → `f"user-{user.id}"`.
pub fn identity_for_user(user_id: Uuid) -> String {
    format!("user-{}", user_id)
}

/// Deterministic AI-teacher identity for a session.
///
/// Mirrors Python `ai_teacher_identity_for_session`, which strips the dashes
/// from the UUID and keeps the first 16 hex characters
/// (`f"ai-teacher-{compact[:16]}"`).
///
/// `Uuid::simple()` renders the dash-free, 32-character lowercase hex form, so
/// `[..16]` takes the first 16 hex digits. Because that form is always exactly
/// 32 ASCII bytes, slicing at byte index 16 can never split a UTF-8 boundary
/// and therefore never panics.
pub fn ai_teacher_identity(session_id: Uuid) -> String {
    format!("ai-teacher-{}", &session_id.simple().to_string()[..16])
}

// ---------------------------------------------------------------------------
// Roster mutations
// ---------------------------------------------------------------------------

/// Insert or revive a participant on join.
///
/// On first join this inserts a fresh row (`is_ai = false`, empty connection
/// metadata, `joined_at = now()`). On a repeat join — detected via the
/// `(live_session_id, participant_identity)` unique constraint — it clears
/// `left_at`, refreshes `display_name`, and bumps `joined_at`. The existing
/// `role` is intentionally preserved across re-joins (matching the Python
/// upsert, which only re-computes role for brand-new rows).
pub async fn upsert_join(
    pool: &PgPool,
    session_id: Uuid,
    user_id: Option<Uuid>,
    identity: &str,
    display_name: Option<&str>,
    role: &str,
) -> Result<LiveParticipant, AppError> {
    let sql = format!(
        r#"
        INSERT INTO live_participants (
            id, live_session_id, user_id, participant_identity, display_name,
            role, is_ai, joined_at, left_at, connection_metadata,
            janus_feed_id, janus_handle_id
        )
        VALUES ($1, $2, $3, $4, $5, $6, false, now(), NULL, '{{}}'::jsonb, NULL, NULL)
        ON CONFLICT (live_session_id, participant_identity)
        DO UPDATE SET
            left_at = NULL,
            display_name = EXCLUDED.display_name,
            joined_at = now()
        RETURNING {cols}
        "#,
        cols = PARTICIPANT_COLUMNS
    );

    let participant = sqlx::query_as::<_, LiveParticipant>(&sql)
        .bind(Uuid::new_v4())
        .bind(session_id)
        .bind(user_id)
        .bind(identity)
        .bind(display_name)
        .bind(role)
        .fetch_one(pool)
        .await
        .map_err(|e| AppError::Internal(e.into()))?;

    Ok(participant)
}

/// Mark a participant as having left (`left_at = now()`).
///
/// Matches on `participant_identity` when supplied (preferred), otherwise on
/// `user_id`; when both are provided either may match (mirrors the Python `OR`).
/// Only active rows (`left_at IS NULL`) are eligible. Returns `None` when no
/// active participant matches. The inner subquery deterministically selects the
/// most recently joined match so the `UPDATE` touches exactly one row.
pub async fn mark_left(
    pool: &PgPool,
    session_id: Uuid,
    user_id: Option<Uuid>,
    identity: Option<&str>,
) -> Result<Option<LiveParticipant>, AppError> {
    let sql = format!(
        r#"
        UPDATE live_participants
        SET left_at = now()
        WHERE id = (
            SELECT id FROM live_participants
            WHERE live_session_id = $1
              AND left_at IS NULL
              AND (
                    ($2::text IS NOT NULL AND participant_identity = $2)
                 OR ($3::uuid IS NOT NULL AND user_id = $3)
              )
            ORDER BY joined_at DESC
            LIMIT 1
        )
        RETURNING {cols}
        "#,
        cols = PARTICIPANT_COLUMNS
    );

    let participant = sqlx::query_as::<_, LiveParticipant>(&sql)
        .bind(session_id)
        .bind(identity)
        .bind(user_id)
        .fetch_optional(pool)
        .await
        .map_err(|e| AppError::Internal(e.into()))?;

    Ok(participant)
}

/// Idempotently ensure the AI-teacher roster row exists for a session.
///
/// The identity is derived from [`ai_teacher_identity`], so repeat calls collide
/// on the `(live_session_id, participant_identity)` unique constraint. The
/// insert uses `ON CONFLICT DO NOTHING` (creating the row at most once) and the
/// row is then read back. `display_name` defaults to `"AI Teacher"`.
pub async fn ensure_ai_teacher(
    pool: &PgPool,
    session_id: Uuid,
    display_name: Option<&str>,
) -> Result<LiveParticipant, AppError> {
    let identity = ai_teacher_identity(session_id);
    let name = display_name.unwrap_or("AI Teacher");

    sqlx::query(
        r#"
        INSERT INTO live_participants (
            id, live_session_id, user_id, participant_identity, display_name,
            role, is_ai, joined_at, left_at, connection_metadata,
            janus_feed_id, janus_handle_id
        )
        VALUES ($1, $2, NULL, $3, $4, 'ai_teacher', true, now(), NULL, '{}'::jsonb, NULL, NULL)
        ON CONFLICT (live_session_id, participant_identity) DO NOTHING
        "#,
    )
    .bind(Uuid::new_v4())
    .bind(session_id)
    .bind(&identity)
    .bind(name)
    .execute(pool)
    .await
    .map_err(|e| AppError::Internal(e.into()))?;

    let sql = format!(
        r#"
        SELECT {cols}
        FROM live_participants
        WHERE live_session_id = $1 AND participant_identity = $2
        "#,
        cols = PARTICIPANT_COLUMNS
    );

    let participant = sqlx::query_as::<_, LiveParticipant>(&sql)
        .bind(session_id)
        .bind(&identity)
        .fetch_one(pool)
        .await
        .map_err(|e| AppError::Internal(e.into()))?;

    Ok(participant)
}

/// Update a participant's role, keyed by `(session, participant_identity)`.
///
/// Returns a 404 [`AppError::Http`] when no matching participant exists.
pub async fn update_role(
    pool: &PgPool,
    session_id: Uuid,
    participant_identity: &str,
    role: &str,
) -> Result<LiveParticipant, AppError> {
    let sql = format!(
        r#"
        UPDATE live_participants
        SET role = $3
        WHERE live_session_id = $1 AND participant_identity = $2
        RETURNING {cols}
        "#,
        cols = PARTICIPANT_COLUMNS
    );

    let participant = sqlx::query_as::<_, LiveParticipant>(&sql)
        .bind(session_id)
        .bind(participant_identity)
        .bind(role)
        .fetch_optional(pool)
        .await
        .map_err(|e| AppError::Internal(e.into()))?;

    participant.ok_or_else(|| AppError::Http {
        status: StatusCode::NOT_FOUND,
        message: "Participant not found".to_string(),
    })
}

/// Persist the Janus VideoRoom feed/handle binding for a participant row.
pub async fn persist_feed_binding(
    pool: &PgPool,
    participant_id: Uuid,
    feed_id: i64,
    handle_id: i64,
) -> Result<(), AppError> {
    sqlx::query(
        r#"
        UPDATE live_participants
        SET janus_feed_id = $2, janus_handle_id = $3
        WHERE id = $1
        "#,
    )
    .bind(participant_id)
    .bind(feed_id)
    .bind(handle_id)
    .execute(pool)
    .await
    .map_err(|e| AppError::Internal(e.into()))?;

    Ok(())
}

/// Count active (not-yet-left) participants in a session — used for
/// `participant_count` on the session DTO.
pub async fn count_active(pool: &PgPool, session_id: Uuid) -> Result<i64, AppError> {
    let row: (i64,) = sqlx::query_as(
        r#"
        SELECT COUNT(*)
        FROM live_participants
        WHERE live_session_id = $1 AND left_at IS NULL
        "#,
    )
    .bind(session_id)
    .fetch_one(pool)
    .await
    .map_err(|e| AppError::Internal(e.into()))?;

    Ok(row.0)
}

// ---------------------------------------------------------------------------
// Roster ↔ Janus reconciliation
// ---------------------------------------------------------------------------

/// Difference between the broker's view of bound feeds and Janus's live feeds.
///
/// `only_in_broker` lists feed ids the broker still has bound that Janus no
/// longer reports (rendered as strings); `only_in_janus` lists feed ids Janus is
/// publishing that the broker has not bound to an active participant.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct RosterDiff {
    pub only_in_broker: Vec<String>,
    pub only_in_janus: Vec<i64>,
}

/// Pure set-difference between two feed-id lists.
///
/// Extracted so the diff logic is unit-testable without a database.
/// `BTreeSet` de-duplicates inputs and yields deterministic (ascending) output
/// ordering on both sides.
pub fn compute_diff(broker_feed_ids: &[i64], janus_feed_ids: &[i64]) -> RosterDiff {
    let broker: BTreeSet<i64> = broker_feed_ids.iter().copied().collect();
    let janus: BTreeSet<i64> = janus_feed_ids.iter().copied().collect();

    let only_in_broker = broker.difference(&janus).map(|id| id.to_string()).collect();
    let only_in_janus = janus.difference(&broker).copied().collect();

    RosterDiff {
        only_in_broker,
        only_in_janus,
    }
}

/// Reconcile the DB roster against a Janus-provided feed-id list.
///
/// Reads the bound `janus_feed_id`s of active, non-AI participants and diffs
/// them against `janus_feed_ids` (which the caller fetches from `JanusAdmin`).
/// Kept pure-DB + [`compute_diff`] so the comparison stays testable.
pub async fn reconcile_with_janus(
    pool: &PgPool,
    session_id: Uuid,
    janus_feed_ids: &[i64],
) -> Result<RosterDiff, AppError> {
    let rows: Vec<(i64,)> = sqlx::query_as(
        r#"
        SELECT janus_feed_id
        FROM live_participants
        WHERE live_session_id = $1
          AND left_at IS NULL
          AND is_ai = false
          AND janus_feed_id IS NOT NULL
        "#,
    )
    .bind(session_id)
    .fetch_all(pool)
    .await
    .map_err(|e| AppError::Internal(e.into()))?;

    let broker_feed_ids: Vec<i64> = rows.into_iter().map(|r| r.0).collect();
    Ok(compute_diff(&broker_feed_ids, janus_feed_ids))
}

// ---------------------------------------------------------------------------
// Unit tests (pure functions only)
// ---------------------------------------------------------------------------

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn identity_for_user_formats_with_prefix() {
        let id = Uuid::parse_str("00000000-0000-0000-0000-000000000001").unwrap();
        assert_eq!(
            identity_for_user(id),
            "user-00000000-0000-0000-0000-000000000001"
        );
    }

    #[test]
    fn ai_teacher_identity_is_16_hex_suffixed_and_stable() {
        let id = Uuid::parse_str("1234abcd-5678-90ef-fedc-ba9876543210").unwrap();

        let a = ai_teacher_identity(id);
        let b = ai_teacher_identity(id);

        // Stable for the same session id.
        assert_eq!(a, b);

        // Prefixed and 16-hex-char suffix.
        assert!(a.starts_with("ai-teacher-"));
        let suffix = a.strip_prefix("ai-teacher-").unwrap();
        assert_eq!(suffix.len(), 16);
        assert!(suffix.chars().all(|c| c.is_ascii_hexdigit()));

        // First 16 hex chars of the dash-free UUID.
        assert_eq!(suffix, "1234abcd567890ef");
    }

    #[test]
    fn compute_diff_disjoint_returns_each_side_whole() {
        let diff = compute_diff(&[1, 2, 3], &[4, 5, 6]);
        assert_eq!(diff.only_in_broker, vec!["1", "2", "3"]);
        assert_eq!(diff.only_in_janus, vec![4, 5, 6]);
    }

    #[test]
    fn compute_diff_equal_sets_are_empty() {
        // Same elements, different order / duplicates -> no difference.
        let diff = compute_diff(&[1, 2, 3, 3], &[3, 2, 1]);
        assert!(diff.only_in_broker.is_empty());
        assert!(diff.only_in_janus.is_empty());
    }

    #[test]
    fn compute_diff_partial_overlap() {
        let diff = compute_diff(&[1, 2, 3], &[2, 3, 4]);
        assert_eq!(diff.only_in_broker, vec!["1"]);
        assert_eq!(diff.only_in_janus, vec![4]);
    }
}
