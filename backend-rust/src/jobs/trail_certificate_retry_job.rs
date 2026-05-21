//! Trail certificate PDF retry worker.
//!
//! Periodically scans `trail_certificates` for rows with `pdf_url IS NULL`
//! and attempts to render the PDF on disk. On success, attaches the URL.
//!
//! Bounded retry: each row is retried at most `MAX_ATTEMPTS` times. We
//! track the attempt count via the `notes` column (cheap, no schema change
//! needed). After the cap, the row is left as-is and a follow-up admin
//! action can clear `notes` to reset the counter.
//!
//! Spec: `.kiro/specs/heritage-trail-mode/` (Requirement 5, graceful
//! PDF rendering with retry).

use chrono::{DateTime, Utc};
use sqlx::PgPool;
use std::path::PathBuf;
use tokio::time::{self, MissedTickBehavior};
use uuid::Uuid;

const POLL_INTERVAL_SECONDS: u64 = 15 * 60; // 15 min
const BATCH_SIZE: i64 = 50;
const MAX_ATTEMPTS: i32 = 3;

pub async fn run(pool: PgPool, uploads_dir: PathBuf) {
    // First pass after a short warm-up so the API is up before the worker
    // starts hammering it.
    let mut ticker = time::interval_at(
        time::Instant::now() + time::Duration::from_secs(60),
        time::Duration::from_secs(POLL_INTERVAL_SECONDS),
    );
    ticker.set_missed_tick_behavior(MissedTickBehavior::Skip);

    loop {
        ticker.tick().await;
        match run_pass(&pool, &uploads_dir).await {
            Ok(stats) if stats.attempted > 0 => {
                tracing::info!(
                    feature = "trail_certificate_retry",
                    attempted = stats.attempted,
                    succeeded = stats.succeeded,
                    failed = stats.failed,
                    capped = stats.capped,
                    "retry pass finished",
                );
            }
            Ok(_) => {} // nothing to do
            Err(err) => {
                tracing::warn!(
                    feature = "trail_certificate_retry",
                    error = %err,
                    "retry pass failed",
                );
            }
        }
    }
}

#[derive(Default, Debug)]
struct PassStats {
    attempted: i64,
    succeeded: i64,
    failed: i64,
    capped: i64,
}

async fn run_pass(pool: &PgPool, uploads_dir: &PathBuf) -> Result<PassStats, sqlx::Error> {
    let mut stats = PassStats::default();

    // Fetch a bounded batch of NULL-pdf rows. We rely on `notes` to encode
    // the attempt counter as `pdf_attempts:N`; the cap check happens in
    // Rust after the read so we don't need a stored function in the DB.
    let rows: Vec<(Uuid, String, Uuid, Uuid, DateTime<Utc>, Option<String>)> = sqlx::query_as(
        r#"
        SELECT c.id, c.hash, c.user_id, c.trail_id, c.issued_at, c.notes
        FROM trail_certificates c
        WHERE c.pdf_url IS NULL
        ORDER BY c.issued_at ASC
        LIMIT $1
        "#,
    )
    .bind(BATCH_SIZE)
    .fetch_all(pool)
    .await?;

    for (cert_id, hash, user_id, trail_id, issued_at, notes) in rows {
        // Determine attempt count from notes.
        let attempts = parse_attempts(notes.as_deref());
        if attempts >= MAX_ATTEMPTS {
            stats.capped += 1;
            continue;
        }
        stats.attempted += 1;

        // Look up the names for the PDF copy.
        let user_name: Option<String> = sqlx::query_scalar(
            "SELECT display_name FROM users WHERE id = $1",
        )
        .bind(user_id)
        .fetch_optional(pool)
        .await
        .ok()
        .flatten();
        let trail_title: Option<String> = sqlx::query_scalar(
            "SELECT title_vi FROM trails WHERE id = $1",
        )
        .bind(trail_id)
        .fetch_optional(pool)
        .await
        .ok()
        .flatten();

        // Render PDF off the runtime thread.
        let dir = uploads_dir.clone();
        let hash_clone = hash.clone();
        let name = user_name.unwrap_or_default();
        let title = trail_title.unwrap_or_default();
        let render_result = tokio::task::spawn_blocking(move || {
            crate::services::certificate_pdf::render_to_disk(
                &dir,
                &hash_clone,
                &name,
                &title,
                issued_at,
            )
        })
        .await;

        let pdf_url = match render_result {
            Ok(Some(url)) => Some(url),
            _ => None,
        };

        // Update DB.
        let new_attempts = attempts + 1;
        if let Some(url) = pdf_url {
            let _ = sqlx::query(
                "UPDATE trail_certificates SET pdf_url = $2, notes = NULL \
                 WHERE id = $1 AND pdf_url IS NULL",
            )
            .bind(cert_id)
            .bind(&url)
            .execute(pool)
            .await;
            stats.succeeded += 1;
        } else {
            let _ = sqlx::query(
                "UPDATE trail_certificates SET notes = $2 WHERE id = $1",
            )
            .bind(cert_id)
            .bind(format!("pdf_attempts:{}", new_attempts))
            .execute(pool)
            .await;
            stats.failed += 1;
        }
    }

    Ok(stats)
}

/// Parse `pdf_attempts:N` out of the `notes` column. Returns 0 for any
/// other shape including NULL.
fn parse_attempts(notes: Option<&str>) -> i32 {
    notes
        .and_then(|s| s.strip_prefix("pdf_attempts:"))
        .and_then(|n| n.parse::<i32>().ok())
        .unwrap_or(0)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn attempts_parses_well_formed_notes() {
        assert_eq!(parse_attempts(Some("pdf_attempts:1")), 1);
        assert_eq!(parse_attempts(Some("pdf_attempts:42")), 42);
    }

    #[test]
    fn attempts_returns_zero_for_other_notes() {
        assert_eq!(parse_attempts(None), 0);
        assert_eq!(parse_attempts(Some("")), 0);
        assert_eq!(parse_attempts(Some("admin grant: please")), 0);
        assert_eq!(parse_attempts(Some("pdf_attempts:abc")), 0);
    }
}
