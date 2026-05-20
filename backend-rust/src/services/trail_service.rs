//! Heritage Trail Mode business logic.
//!
//! Spec: `.kiro/specs/heritage-trail-mode/`

use axum::http::StatusCode;
use chrono::{DateTime, Duration, Utc};
use serde_json::json;
use sha2::{Digest, Sha256};
use sqlx::PgPool;
use uuid::Uuid;

use crate::error::AppError;
use crate::models::trail::{
    CertificateVerifyOut, CheckpointResponse, CheckpointSubmitRequest, CreateTeacherTrailRequest,
    CreateTrailRequest, Pace, SetPaceRequest, SkippedCheckpointOut, StepCompleteResponse,
    StepMotif, TrailAnalyticsOut, TrailDetailOut, TrailListResponse, TrailOut, TrailRow,
    TrailStartResponse, UpdateTrailRequest, UserTrailProgressOut,
};

const MIN_STEPS: usize = 5;
const MAX_STEPS: usize = 15;

// ---------------------------------------------------------------------------
// Admin
// ---------------------------------------------------------------------------

pub async fn create_trail(
    pool: &PgPool,
    creator_id: Uuid,
    payload: &CreateTrailRequest,
) -> Result<TrailOut, AppError> {
    let mut tx = pool
        .begin()
        .await
        .map_err(|e| AppError::Internal(e.into()))?;

    let row: TrailRow = sqlx::query_as(
        r#"
        INSERT INTO trails
            (slug, title_vi, title_en, description_vi, description_en,
             narrator_intro, narrator_outro, difficulty, estimated_minutes,
             created_by_user_id, status, visibility)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, 'draft', 'public')
        RETURNING id, slug, title_vi, title_en, description_vi, description_en,
                  narrator_intro, narrator_outro, difficulty, estimated_minutes,
                  created_by_user_id, status, visibility, classroom_id,
                  published_at, created_at, updated_at
        "#,
    )
    .bind(&payload.slug)
    .bind(&payload.title_vi)
    .bind(&payload.title_en)
    .bind(&payload.description_vi)
    .bind(&payload.description_en)
    .bind(&payload.narrator_intro)
    .bind(&payload.narrator_outro)
    .bind(&payload.difficulty)
    .bind(payload.estimated_minutes)
    .bind(creator_id)
    .fetch_one(&mut *tx)
    .await
    .map_err(|e| AppError::Internal(e.into()))?;

    insert_steps_and_checkpoints(&mut tx, row.id, &payload.steps, &payload.checkpoints).await?;
    tx.commit().await.map_err(|e| AppError::Internal(e.into()))?;

    fetch_trail_out(pool, row.id).await
}

pub async fn update_trail(
    pool: &PgPool,
    trail_id: Uuid,
    payload: &UpdateTrailRequest,
) -> Result<TrailOut, AppError> {
    // Apply optional patches.
    sqlx::query(
        r#"
        UPDATE trails SET
            title_vi          = COALESCE($2, title_vi),
            title_en          = COALESCE($3, title_en),
            description_vi    = COALESCE($4, description_vi),
            description_en    = COALESCE($5, description_en),
            narrator_intro    = COALESCE($6, narrator_intro),
            narrator_outro    = COALESCE($7, narrator_outro),
            difficulty        = COALESCE($8, difficulty),
            estimated_minutes = COALESCE($9, estimated_minutes),
            updated_at = NOW()
        WHERE id = $1
        "#,
    )
    .bind(trail_id)
    .bind(&payload.title_vi)
    .bind(&payload.title_en)
    .bind(&payload.description_vi)
    .bind(&payload.description_en)
    .bind(&payload.narrator_intro)
    .bind(&payload.narrator_outro)
    .bind(&payload.difficulty)
    .bind(payload.estimated_minutes)
    .execute(pool)
    .await
    .map_err(|e| AppError::Internal(e.into()))?;

    if let Some(target) = payload.status.as_deref() {
        match target {
            "published" => publish_trail_inner(pool, trail_id).await?,
            "archived" => {
                sqlx::query("UPDATE trails SET status = 'archived', updated_at = NOW() WHERE id = $1")
                    .bind(trail_id)
                    .execute(pool)
                    .await
                    .map_err(|e| AppError::Internal(e.into()))?;
            }
            "draft" => {
                sqlx::query("UPDATE trails SET status = 'draft', updated_at = NOW() WHERE id = $1")
                    .bind(trail_id)
                    .execute(pool)
                    .await
                    .map_err(|e| AppError::Internal(e.into()))?;
            }
            _ => {
                return Err(AppError::Validation {
                    details: json!({"status": "must be one of: published, draft, archived"}),
                });
            }
        }
    }

    fetch_trail_out(pool, trail_id).await
}

pub async fn promote_trail(pool: &PgPool, trail_id: Uuid) -> Result<TrailOut, AppError> {
    let current_status: Option<String> =
        sqlx::query_scalar("SELECT status FROM trails WHERE id = $1")
            .bind(trail_id)
            .fetch_optional(pool)
            .await
            .map_err(|e| AppError::Internal(e.into()))?;
    let status = current_status.ok_or_else(|| AppError::Http {
        status: StatusCode::NOT_FOUND,
        message: "Trail not found".to_string(),
    })?;
    if status != "pending_review" {
        return Err(AppError::Domain {
            status: StatusCode::CONFLICT,
            code: "INVALID_STATE_TRANSITION".to_string(),
            message: "Trail must be in pending_review status to promote".to_string(),
            details: json!({"current_status": status}),
        });
    }
    sqlx::query(
        "UPDATE trails SET status = 'published', visibility = 'public', \
         published_at = COALESCE(published_at, NOW()), updated_at = NOW() WHERE id = $1",
    )
    .bind(trail_id)
    .execute(pool)
    .await
    .map_err(|e| AppError::Internal(e.into()))?;
    fetch_trail_out(pool, trail_id).await
}

async fn publish_trail_inner(pool: &PgPool, trail_id: Uuid) -> Result<(), AppError> {
    let trail: Option<TrailRow> = sqlx::query_as(
        r#"
        SELECT id, slug, title_vi, title_en, description_vi, description_en,
               narrator_intro, narrator_outro, difficulty, estimated_minutes,
               created_by_user_id, status, visibility, classroom_id,
               published_at, created_at, updated_at
        FROM trails WHERE id = $1
        "#,
    )
    .bind(trail_id)
    .fetch_optional(pool)
    .await
    .map_err(|e| AppError::Internal(e.into()))?;
    let trail = trail.ok_or_else(|| AppError::Http {
        status: StatusCode::NOT_FOUND,
        message: "Trail not found".to_string(),
    })?;

    let step_count: i64 =
        sqlx::query_scalar("SELECT COUNT(*)::bigint FROM trail_steps WHERE trail_id = $1")
            .bind(trail_id)
            .fetch_one(pool)
            .await
            .map_err(|e| AppError::Internal(e.into()))?;

    let mut errors = Vec::new();
    if (step_count as usize) < MIN_STEPS {
        errors.push(format!("must have at least {} steps", MIN_STEPS));
    }
    if (step_count as usize) > MAX_STEPS {
        errors.push(format!("must have at most {} steps", MAX_STEPS));
    }
    if trail.narrator_intro.as_deref().unwrap_or("").trim().is_empty() {
        errors.push("narrator_intro must not be empty".to_string());
    }
    if trail.narrator_outro.as_deref().unwrap_or("").trim().is_empty() {
        errors.push("narrator_outro must not be empty".to_string());
    }
    if !errors.is_empty() {
        return Err(AppError::Domain {
            status: StatusCode::UNPROCESSABLE_ENTITY,
            code: "TRAIL_VALIDATION".to_string(),
            message: "Trail does not meet publish requirements".to_string(),
            details: json!({"errors": errors, "step_count": step_count}),
        });
    }

    sqlx::query(
        "UPDATE trails SET status = 'published', published_at = COALESCE(published_at, NOW()), \
         updated_at = NOW() WHERE id = $1",
    )
    .bind(trail_id)
    .execute(pool)
    .await
    .map_err(|e| AppError::Internal(e.into()))?;
    Ok(())
}

async fn insert_steps_and_checkpoints(
    tx: &mut sqlx::Transaction<'_, sqlx::Postgres>,
    trail_id: Uuid,
    steps: &[crate::models::trail::TrailStepInput],
    checkpoints: &[crate::models::trail::TrailCheckpointInput],
) -> Result<(), AppError> {
    for s in steps {
        sqlx::query(
            "INSERT INTO trail_steps (trail_id, motif_id, position) VALUES ($1, $2, $3) \
             ON CONFLICT (trail_id, position) DO UPDATE SET motif_id = EXCLUDED.motif_id",
        )
        .bind(trail_id)
        .bind(s.motif_id)
        .bind(s.position)
        .execute(&mut **tx)
        .await
        .map_err(|e| AppError::Internal(e.into()))?;
    }
    for c in checkpoints {
        sqlx::query(
            "INSERT INTO trail_checkpoints (trail_id, after_position, prompt_vi, prompt_en) \
             VALUES ($1, $2, $3, $4) \
             ON CONFLICT (trail_id, after_position) DO UPDATE \
             SET prompt_vi = EXCLUDED.prompt_vi, prompt_en = EXCLUDED.prompt_en",
        )
        .bind(trail_id)
        .bind(c.after_position)
        .bind(&c.prompt_vi)
        .bind(&c.prompt_en)
        .execute(&mut **tx)
        .await
        .map_err(|e| AppError::Internal(e.into()))?;
    }
    Ok(())
}

async fn fetch_trail_out(pool: &PgPool, trail_id: Uuid) -> Result<TrailOut, AppError> {
    let row: Option<TrailRow> = sqlx::query_as(
        r#"
        SELECT id, slug, title_vi, title_en, description_vi, description_en,
               narrator_intro, narrator_outro, difficulty, estimated_minutes,
               created_by_user_id, status, visibility, classroom_id,
               published_at, created_at, updated_at
        FROM trails WHERE id = $1
        "#,
    )
    .bind(trail_id)
    .fetch_optional(pool)
    .await
    .map_err(|e| AppError::Internal(e.into()))?;
    let row = row.ok_or_else(|| AppError::Http {
        status: StatusCode::NOT_FOUND,
        message: "Trail not found".to_string(),
    })?;
    let step_count: i64 =
        sqlx::query_scalar("SELECT COUNT(*)::bigint FROM trail_steps WHERE trail_id = $1")
            .bind(trail_id)
            .fetch_one(pool)
            .await
            .map_err(|e| AppError::Internal(e.into()))?;
    let checkpoint_count: i64 =
        sqlx::query_scalar("SELECT COUNT(*)::bigint FROM trail_checkpoints WHERE trail_id = $1")
            .bind(trail_id)
            .fetch_one(pool)
            .await
            .map_err(|e| AppError::Internal(e.into()))?;
    Ok(row_to_out(row, step_count, checkpoint_count))
}

fn row_to_out(row: TrailRow, step_count: i64, checkpoint_count: i64) -> TrailOut {
    TrailOut {
        id: row.id,
        slug: row.slug,
        title_vi: row.title_vi,
        title_en: row.title_en,
        description_vi: row.description_vi,
        description_en: row.description_en,
        narrator_intro: row.narrator_intro,
        narrator_outro: row.narrator_outro,
        difficulty: row.difficulty,
        estimated_minutes: row.estimated_minutes,
        status: row.status,
        visibility: row.visibility,
        step_count,
        checkpoint_count,
        created_at: row.created_at,
        published_at: row.published_at,
    }
}

// ---------------------------------------------------------------------------
// Public
// ---------------------------------------------------------------------------

pub async fn list_trails(
    pool: &PgPool,
    page: i64,
    per_page: i64,
) -> Result<TrailListResponse, AppError> {
    let page = page.max(1);
    let per_page = per_page.clamp(1, 100);
    let offset = (page - 1) * per_page;

    let trails: Vec<TrailRow> = sqlx::query_as(
        r#"
        SELECT id, slug, title_vi, title_en, description_vi, description_en,
               narrator_intro, narrator_outro, difficulty, estimated_minutes,
               created_by_user_id, status, visibility, classroom_id,
               published_at, created_at, updated_at
        FROM trails
        WHERE status = 'published' AND visibility = 'public'
        ORDER BY published_at DESC NULLS LAST
        LIMIT $1 OFFSET $2
        "#,
    )
    .bind(per_page)
    .bind(offset)
    .fetch_all(pool)
    .await
    .map_err(|e| AppError::Internal(e.into()))?;

    let total: i64 = sqlx::query_scalar(
        "SELECT COUNT(*)::bigint FROM trails WHERE status = 'published' AND visibility = 'public'",
    )
    .fetch_one(pool)
    .await
    .map_err(|e| AppError::Internal(e.into()))?;

    let mut outs = Vec::with_capacity(trails.len());
    for row in trails {
        let step_count: i64 =
            sqlx::query_scalar("SELECT COUNT(*)::bigint FROM trail_steps WHERE trail_id = $1")
                .bind(row.id)
                .fetch_one(pool)
                .await
                .map_err(|e| AppError::Internal(e.into()))?;
        let checkpoint_count: i64 = sqlx::query_scalar(
            "SELECT COUNT(*)::bigint FROM trail_checkpoints WHERE trail_id = $1",
        )
        .bind(row.id)
        .fetch_one(pool)
        .await
        .map_err(|e| AppError::Internal(e.into()))?;
        outs.push(row_to_out(row, step_count, checkpoint_count));
    }

    Ok(TrailListResponse {
        trails: outs,
        page,
        per_page,
        total,
    })
}

pub async fn get_trail_detail(
    pool: &PgPool,
    slug: &str,
    user_id: Uuid,
) -> Result<TrailDetailOut, AppError> {
    let trail: Option<TrailRow> = sqlx::query_as(
        r#"
        SELECT id, slug, title_vi, title_en, description_vi, description_en,
               narrator_intro, narrator_outro, difficulty, estimated_minutes,
               created_by_user_id, status, visibility, classroom_id,
               published_at, created_at, updated_at
        FROM trails WHERE slug = $1
        "#,
    )
    .bind(slug)
    .fetch_optional(pool)
    .await
    .map_err(|e| AppError::Internal(e.into()))?;
    let row = trail.ok_or_else(|| AppError::Http {
        status: StatusCode::NOT_FOUND,
        message: "Trail not found".to_string(),
    })?;
    let trail_id = row.id;
    let step_count: i64 =
        sqlx::query_scalar("SELECT COUNT(*)::bigint FROM trail_steps WHERE trail_id = $1")
            .bind(trail_id)
            .fetch_one(pool)
            .await
            .map_err(|e| AppError::Internal(e.into()))?;
    let checkpoint_count: i64 =
        sqlx::query_scalar("SELECT COUNT(*)::bigint FROM trail_checkpoints WHERE trail_id = $1")
            .bind(trail_id)
            .fetch_one(pool)
            .await
            .map_err(|e| AppError::Internal(e.into()))?;
    let progress = fetch_progress(pool, user_id, trail_id).await?;
    Ok(TrailDetailOut {
        trail: row_to_out(row, step_count, checkpoint_count),
        progress,
    })
}

async fn fetch_progress(
    pool: &PgPool,
    user_id: Uuid,
    trail_id: Uuid,
) -> Result<Option<UserTrailProgressOut>, AppError> {
    let row: Option<(i32, DateTime<Utc>, Option<DateTime<Utc>>, Option<String>, Option<DateTime<Utc>>)> =
        sqlx::query_as(
            "SELECT current_position, started_at, completed_at, pace, next_reminder_at \
             FROM user_trail_progress WHERE user_id = $1 AND trail_id = $2",
        )
        .bind(user_id)
        .bind(trail_id)
        .fetch_optional(pool)
        .await
        .map_err(|e| AppError::Internal(e.into()))?;
    Ok(row.map(|(pos, started, completed, pace, reminder)| UserTrailProgressOut {
        current_position: pos,
        started_at: started,
        completed_at: completed,
        pace: pace.unwrap_or_else(|| "daily".to_string()),
        next_reminder_at: reminder,
    }))
}

// ---------------------------------------------------------------------------
// Progression
// ---------------------------------------------------------------------------

pub async fn start_trail(
    pool: &PgPool,
    slug: &str,
    user_id: Uuid,
) -> Result<TrailStartResponse, AppError> {
    let trail: Option<(Uuid, String, Option<String>)> = sqlx::query_as(
        "SELECT id, status, narrator_intro FROM trails WHERE slug = $1 AND status = 'published'",
    )
    .bind(slug)
    .fetch_optional(pool)
    .await
    .map_err(|e| AppError::Internal(e.into()))?;
    let (trail_id, _status, intro) = trail.ok_or_else(|| AppError::Http {
        status: StatusCode::NOT_FOUND,
        message: "Trail not found or not published".to_string(),
    })?;

    let mut tx = pool
        .begin()
        .await
        .map_err(|e| AppError::Internal(e.into()))?;

    sqlx::query("SELECT pg_advisory_xact_lock(hashtextextended($1::text || $2::text, 0))")
        .bind(user_id)
        .bind(trail_id)
        .execute(&mut *tx)
        .await
        .map_err(|e| AppError::Internal(e.into()))?;

    let row: (i32, DateTime<Utc>, Option<DateTime<Utc>>, Option<String>, Option<DateTime<Utc>>) =
        sqlx::query_as(
            r#"
            INSERT INTO user_trail_progress
                (user_id, trail_id, current_position, started_at, last_activity_at)
            VALUES ($1, $2, 1, NOW(), NOW())
            ON CONFLICT (user_id, trail_id) DO UPDATE
            SET last_activity_at = NOW()
            RETURNING current_position, started_at, completed_at, pace, next_reminder_at
            "#,
        )
        .bind(user_id)
        .bind(trail_id)
        .fetch_one(&mut *tx)
        .await
        .map_err(|e| AppError::Internal(e.into()))?;
    let (pos, started, completed, pace, reminder) = row;

    let first_motif = fetch_step_motif(pool, trail_id, pos).await?;

    tx.commit().await.map_err(|e| AppError::Internal(e.into()))?;

    let _ = sqlx::query(
        "INSERT INTO analytics_events (id, event_type, user_id, payload, created_at) \
         VALUES (gen_random_uuid(), 'trail_started', $1, $2::jsonb, NOW())",
    )
    .bind(user_id)
    .bind(json!({"trail_id": trail_id}).to_string())
    .execute(pool)
    .await;

    Ok(TrailStartResponse {
        progress: UserTrailProgressOut {
            current_position: pos,
            started_at: started,
            completed_at: completed,
            pace: pace.unwrap_or_else(|| "daily".to_string()),
            next_reminder_at: reminder,
        },
        first_motif,
        narrator_intro: intro,
    })
}

async fn fetch_step_motif(
    pool: &PgPool,
    trail_id: Uuid,
    position: i32,
) -> Result<Option<StepMotif>, AppError> {
    let row: Option<(Uuid, i32, Option<String>, Option<String>, Option<String>)> = sqlx::query_as(
        r#"
        SELECT ts.motif_id, ts.position, m.name, m.thumbnail_url, m.description
        FROM trail_steps ts
        LEFT JOIN motifs m ON m.id = ts.motif_id
        WHERE ts.trail_id = $1 AND ts.position = $2
        "#,
    )
    .bind(trail_id)
    .bind(position)
    .fetch_optional(pool)
    .await
    .map_err(|e| AppError::Internal(e.into()))?;
    Ok(row.map(|(motif_id, position, name, thumb, desc)| StepMotif {
        motif_id,
        position,
        motif_name: name,
        thumbnail_url: thumb,
        description: desc,
    }))
}

pub async fn complete_step(
    pool: &PgPool,
    slug: &str,
    position: i32,
    user_id: Uuid,
    uploads_dir: Option<&std::path::Path>,
) -> Result<StepCompleteResponse, AppError> {
    let trail: Option<(Uuid, Option<String>)> = sqlx::query_as(
        "SELECT id, narrator_outro FROM trails WHERE slug = $1 AND status = 'published'",
    )
    .bind(slug)
    .fetch_optional(pool)
    .await
    .map_err(|e| AppError::Internal(e.into()))?;
    let (trail_id, outro) = trail.ok_or_else(|| AppError::Http {
        status: StatusCode::NOT_FOUND,
        message: "Trail not found or not published".to_string(),
    })?;

    let mut tx = pool
        .begin()
        .await
        .map_err(|e| AppError::Internal(e.into()))?;

    sqlx::query("SELECT pg_advisory_xact_lock(hashtextextended($1::text || $2::text, 0))")
        .bind(user_id)
        .bind(trail_id)
        .execute(&mut *tx)
        .await
        .map_err(|e| AppError::Internal(e.into()))?;

    let progress: Option<(i32, Option<DateTime<Utc>>)> = sqlx::query_as(
        "SELECT current_position, completed_at FROM user_trail_progress \
         WHERE user_id = $1 AND trail_id = $2 FOR UPDATE",
    )
    .bind(user_id)
    .bind(trail_id)
    .fetch_optional(&mut *tx)
    .await
    .map_err(|e| AppError::Internal(e.into()))?;

    let (current_pos, completed_at) = progress.ok_or_else(|| AppError::Domain {
        status: StatusCode::CONFLICT,
        code: "TRAIL_NOT_STARTED".to_string(),
        message: "Trail must be started before completing steps".to_string(),
        details: json!({}),
    })?;

    if completed_at.is_some() {
        return Err(AppError::Domain {
            status: StatusCode::CONFLICT,
            code: "TRAIL_ALREADY_COMPLETED".to_string(),
            message: "Trail is already completed".to_string(),
            details: json!({}),
        });
    }

    if current_pos != position {
        return Err(AppError::Domain {
            status: StatusCode::CONFLICT,
            code: "TRAIL_POSITION_MISMATCH".to_string(),
            message: format!(
                "Cannot complete step {}, current position is {}",
                position, current_pos
            ),
            details: json!({"current_position": current_pos, "requested": position}),
        });
    }

    // Check whether a checkpoint follows this position.
    let checkpoint: Option<(Uuid, Option<String>, Option<String>)> = sqlx::query_as(
        "SELECT id, prompt_vi, prompt_en FROM trail_checkpoints \
         WHERE trail_id = $1 AND after_position = $2",
    )
    .bind(trail_id)
    .bind(position)
    .fetch_optional(&mut *tx)
    .await
    .map_err(|e| AppError::Internal(e.into()))?;

    // Has the user already responded to this checkpoint?
    let response_exists = match checkpoint {
        Some((cp_id, _, _)) => {
            let n: i64 = sqlx::query_scalar(
                "SELECT COUNT(*)::bigint FROM user_trail_checkpoint_responses \
                 WHERE user_id = $1 AND checkpoint_id = $2",
            )
            .bind(user_id)
            .bind(cp_id)
            .fetch_one(&mut *tx)
            .await
            .map_err(|e| AppError::Internal(e.into()))?;
            n > 0
        }
        None => true,
    };

    // If a checkpoint exists and the user hasn't answered it yet, surface it.
    if let Some((cp_id, prompt_vi, prompt_en)) = checkpoint.clone() {
        if !response_exists {
            tx.commit()
                .await
                .map_err(|e| AppError::Internal(e.into()))?;
            return Ok(StepCompleteResponse::Checkpoint {
                checkpoint_id: cp_id,
                after_position: position,
                prompt_vi: prompt_vi.unwrap_or_default(),
                prompt_en,
            });
        }
    }

    // Advance position.
    let new_pos = position + 1;
    let total_steps: i64 =
        sqlx::query_scalar("SELECT COUNT(*)::bigint FROM trail_steps WHERE trail_id = $1")
            .bind(trail_id)
            .fetch_one(&mut *tx)
            .await
            .map_err(|e| AppError::Internal(e.into()))?;

    if (new_pos as i64) > total_steps {
        // Trail completed.
        sqlx::query(
            "UPDATE user_trail_progress SET completed_at = NOW(), \
             current_position = $3, last_activity_at = NOW() \
             WHERE user_id = $1 AND trail_id = $2",
        )
        .bind(user_id)
        .bind(trail_id)
        .bind(new_pos)
        .execute(&mut *tx)
        .await
        .map_err(|e| AppError::Internal(e.into()))?;

        // Generate certificate.
        let now = Utc::now();
        let hash = generate_certificate_hash(user_id, trail_id, now.timestamp());
        // Render PDF best-effort. If rendering fails, the certificate row is
        // still created with a NULL pdf_url so the user record is durable.
        let mut pdf_url: Option<String> = None;
        if let Some(dir) = uploads_dir {
            let user_name: Option<String> = sqlx::query_scalar(
                "SELECT display_name FROM users WHERE id = $1",
            )
            .bind(user_id)
            .fetch_optional(&mut *tx)
            .await
            .map_err(|e| AppError::Internal(e.into()))?;
            let trail_title: Option<String> = sqlx::query_scalar(
                "SELECT title_vi FROM trails WHERE id = $1",
            )
            .bind(trail_id)
            .fetch_optional(&mut *tx)
            .await
            .map_err(|e| AppError::Internal(e.into()))?;
            pdf_url = crate::services::certificate_pdf::render_to_disk(
                dir,
                &hash,
                user_name.as_deref().unwrap_or(""),
                trail_title.as_deref().unwrap_or(""),
                now,
            );
        }
        let _ = sqlx::query(
            "INSERT INTO trail_certificates (user_id, trail_id, hash, issued_at, pdf_url) \
             VALUES ($1, $2, $3, $4, $5) ON CONFLICT (user_id, trail_id) DO NOTHING",
        )
        .bind(user_id)
        .bind(trail_id)
        .bind(&hash)
        .bind(now)
        .bind(pdf_url.as_deref())
        .execute(&mut *tx)
        .await;

        tx.commit()
            .await
            .map_err(|e| AppError::Internal(e.into()))?;

        let _ = sqlx::query(
            "INSERT INTO analytics_events (id, event_type, user_id, payload, created_at) \
             VALUES (gen_random_uuid(), 'trail_completed', $1, $2::jsonb, NOW())",
        )
        .bind(user_id)
        .bind(json!({"trail_id": trail_id, "hash": hash}).to_string())
        .execute(pool)
        .await;

        return Ok(StepCompleteResponse::Completed {
            outro,
            certificate_hash: Some(hash),
            certificate_url: pdf_url,
        });
    }

    sqlx::query(
        "UPDATE user_trail_progress SET current_position = $3, last_activity_at = NOW() \
         WHERE user_id = $1 AND trail_id = $2",
    )
    .bind(user_id)
    .bind(trail_id)
    .bind(new_pos)
    .execute(&mut *tx)
    .await
    .map_err(|e| AppError::Internal(e.into()))?;

    let next = fetch_step_motif(pool, trail_id, new_pos)
        .await?
        .ok_or_else(|| AppError::Internal(anyhow::anyhow!("missing next motif row")))?;

    tx.commit()
        .await
        .map_err(|e| AppError::Internal(e.into()))?;

    let _ = sqlx::query(
        "INSERT INTO analytics_events (id, event_type, user_id, payload, created_at) \
         VALUES (gen_random_uuid(), 'trail_step_completed', $1, $2::jsonb, NOW())",
    )
    .bind(user_id)
    .bind(json!({"trail_id": trail_id, "position": position}).to_string())
    .execute(pool)
    .await;

    Ok(StepCompleteResponse::NextMotif {
        position: new_pos,
        motif: next,
    })
}

pub async fn submit_checkpoint(
    pool: &PgPool,
    slug: &str,
    after_position: i32,
    user_id: Uuid,
    body: &CheckpointSubmitRequest,
    uploads_dir: Option<&std::path::Path>,
) -> Result<CheckpointResponse, AppError> {
    let trail_id: Option<Uuid> =
        sqlx::query_scalar("SELECT id FROM trails WHERE slug = $1 AND status = 'published'")
            .bind(slug)
            .fetch_optional(pool)
            .await
            .map_err(|e| AppError::Internal(e.into()))?;
    let trail_id = trail_id.ok_or_else(|| AppError::Http {
        status: StatusCode::NOT_FOUND,
        message: "Trail not found or not published".to_string(),
    })?;

    let cp_id: Option<Uuid> = sqlx::query_scalar(
        "SELECT id FROM trail_checkpoints WHERE trail_id = $1 AND after_position = $2",
    )
    .bind(trail_id)
    .bind(after_position)
    .fetch_optional(pool)
    .await
    .map_err(|e| AppError::Internal(e.into()))?;
    let cp_id = cp_id.ok_or_else(|| AppError::Http {
        status: StatusCode::NOT_FOUND,
        message: "Checkpoint not found".to_string(),
    })?;

    sqlx::query(
        "INSERT INTO user_trail_checkpoint_responses (user_id, checkpoint_id, response_text) \
         VALUES ($1, $2, $3) ON CONFLICT (user_id, checkpoint_id) DO UPDATE \
         SET response_text = EXCLUDED.response_text",
    )
    .bind(user_id)
    .bind(cp_id)
    .bind(&body.response)
    .execute(pool)
    .await
    .map_err(|e| AppError::Internal(e.into()))?;

    let _ = sqlx::query(
        "INSERT INTO analytics_events (id, event_type, user_id, payload, created_at) \
         VALUES (gen_random_uuid(), 'trail_checkpoint_responded', $1, $2::jsonb, NOW())",
    )
    .bind(user_id)
    .bind(json!({"trail_id": trail_id, "checkpoint_id": cp_id}).to_string())
    .execute(pool)
    .await;

    // Now advance through complete_step.
    let next = complete_step(pool, slug, after_position, user_id, uploads_dir).await?;
    let current = match &next {
        StepCompleteResponse::NextMotif { position, .. } => *position,
        StepCompleteResponse::Checkpoint { after_position, .. } => *after_position,
        StepCompleteResponse::Completed { .. } => -1,
    };
    Ok(CheckpointResponse {
        current_position: current,
        next,
    })
}

pub async fn set_pace(
    pool: &PgPool,
    user_id: Uuid,
    trail_id: Uuid,
    body: &SetPaceRequest,
) -> Result<UserTrailProgressOut, AppError> {
    let pace = Pace::parse(&body.pace).ok_or_else(|| AppError::Validation {
        details: json!({"pace": "must be one of: daily, 2x_week, weekly"}),
    })?;
    let next_reminder = Utc::now() + Duration::hours(pace.reminder_hours());
    let row: Option<(i32, DateTime<Utc>, Option<DateTime<Utc>>, Option<String>, Option<DateTime<Utc>>)> =
        sqlx::query_as(
            r#"
            UPDATE user_trail_progress
            SET pace = $3, next_reminder_at = $4, last_activity_at = NOW()
            WHERE user_id = $1 AND trail_id = $2
            RETURNING current_position, started_at, completed_at, pace, next_reminder_at
            "#,
        )
        .bind(user_id)
        .bind(trail_id)
        .bind(pace.as_str())
        .bind(next_reminder)
        .fetch_optional(pool)
        .await
        .map_err(|e| AppError::Internal(e.into()))?;
    let row = row.ok_or_else(|| AppError::Http {
        status: StatusCode::NOT_FOUND,
        message: "User has not started this trail".to_string(),
    })?;
    Ok(UserTrailProgressOut {
        current_position: row.0,
        started_at: row.1,
        completed_at: row.2,
        pace: row.3.unwrap_or_else(|| pace.as_str().to_string()),
        next_reminder_at: row.4,
    })
}

// ---------------------------------------------------------------------------
// Teacher
// ---------------------------------------------------------------------------

pub async fn create_teacher_trail(
    pool: &PgPool,
    teacher_id: Uuid,
    payload: &CreateTeacherTrailRequest,
) -> Result<TrailOut, AppError> {
    // Verify the teacher owns the classroom.
    let owner: Option<Uuid> =
        sqlx::query_scalar("SELECT owner_id FROM classrooms WHERE id = $1")
            .bind(payload.classroom_id)
            .fetch_optional(pool)
            .await
            .map_err(|e| AppError::Internal(e.into()))?;
    let owner = owner.ok_or_else(|| AppError::Http {
        status: StatusCode::NOT_FOUND,
        message: "Classroom not found".to_string(),
    })?;
    if owner != teacher_id {
        return Err(AppError::Http {
            status: StatusCode::FORBIDDEN,
            message: "You do not own this classroom".to_string(),
        });
    }

    let mut tx = pool
        .begin()
        .await
        .map_err(|e| AppError::Internal(e.into()))?;

    let row: TrailRow = sqlx::query_as(
        r#"
        INSERT INTO trails
            (slug, title_vi, title_en, description_vi, description_en,
             narrator_intro, narrator_outro, difficulty, estimated_minutes,
             created_by_user_id, status, visibility, classroom_id)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, 'draft', 'classroom', $11)
        RETURNING id, slug, title_vi, title_en, description_vi, description_en,
                  narrator_intro, narrator_outro, difficulty, estimated_minutes,
                  created_by_user_id, status, visibility, classroom_id,
                  published_at, created_at, updated_at
        "#,
    )
    .bind(&payload.slug)
    .bind(&payload.title_vi)
    .bind(&payload.title_en)
    .bind(&payload.description_vi)
    .bind(&payload.description_en)
    .bind(&payload.narrator_intro)
    .bind(&payload.narrator_outro)
    .bind(&payload.difficulty)
    .bind(payload.estimated_minutes)
    .bind(teacher_id)
    .bind(payload.classroom_id)
    .fetch_one(&mut *tx)
    .await
    .map_err(|e| AppError::Internal(e.into()))?;

    insert_steps_and_checkpoints(&mut tx, row.id, &payload.steps, &payload.checkpoints).await?;
    tx.commit().await.map_err(|e| AppError::Internal(e.into()))?;

    fetch_trail_out(pool, row.id).await
}

pub async fn submit_for_promotion(
    pool: &PgPool,
    teacher_id: Uuid,
    trail_id: Uuid,
) -> Result<TrailOut, AppError> {
    let row: Option<(Uuid, String)> =
        sqlx::query_as("SELECT created_by_user_id, status FROM trails WHERE id = $1")
            .bind(trail_id)
            .fetch_optional(pool)
            .await
            .map_err(|e| AppError::Internal(e.into()))?;
    let (created_by, status) = row.ok_or_else(|| AppError::Http {
        status: StatusCode::NOT_FOUND,
        message: "Trail not found".to_string(),
    })?;
    if created_by != teacher_id {
        return Err(AppError::Http {
            status: StatusCode::FORBIDDEN,
            message: "You do not own this trail".to_string(),
        });
    }
    if status != "draft" {
        return Err(AppError::Domain {
            status: StatusCode::CONFLICT,
            code: "INVALID_STATE_TRANSITION".to_string(),
            message: "Trail must be in draft status to submit for promotion".to_string(),
            details: json!({"current_status": status}),
        });
    }
    sqlx::query(
        "UPDATE trails SET status = 'pending_review', updated_at = NOW() WHERE id = $1",
    )
    .bind(trail_id)
    .execute(pool)
    .await
    .map_err(|e| AppError::Internal(e.into()))?;
    fetch_trail_out(pool, trail_id).await
}

// ---------------------------------------------------------------------------
// Certificates
// ---------------------------------------------------------------------------

pub fn generate_certificate_hash(user_id: Uuid, trail_id: Uuid, completed_at_unix: i64) -> String {
    let input = format!("{}:{}:{}", user_id, trail_id, completed_at_unix);
    let mut hasher = Sha256::new();
    hasher.update(input.as_bytes());
    hex_encode(&hasher.finalize())
}

fn hex_encode(bytes: &[u8]) -> String {
    let mut s = String::with_capacity(bytes.len() * 2);
    for b in bytes {
        use std::fmt::Write;
        let _ = write!(s, "{:02x}", b);
    }
    s
}

pub async fn verify_certificate(
    pool: &PgPool,
    hash: &str,
) -> Result<CertificateVerifyOut, AppError> {
    let row: Option<(Uuid, Uuid, DateTime<Utc>)> = sqlx::query_as(
        "SELECT user_id, trail_id, issued_at FROM trail_certificates WHERE hash = $1",
    )
    .bind(hash)
    .fetch_optional(pool)
    .await
    .map_err(|e| AppError::Internal(e.into()))?;
    let (user_id, trail_id, issued_at) = row.ok_or_else(|| AppError::Http {
        status: StatusCode::NOT_FOUND,
        message: "Certificate not found".to_string(),
    })?;

    let display_name: Option<String> =
        sqlx::query_scalar("SELECT display_name FROM users WHERE id = $1")
            .bind(user_id)
            .fetch_optional(pool)
            .await
            .map_err(|e| AppError::Internal(e.into()))?;
    let trail_title: Option<String> =
        sqlx::query_scalar("SELECT title_vi FROM trails WHERE id = $1")
            .bind(trail_id)
            .fetch_optional(pool)
            .await
            .map_err(|e| AppError::Internal(e.into()))?;

    Ok(CertificateVerifyOut {
        valid: true,
        user_display_name: display_name.unwrap_or_default(),
        trail_title: trail_title.unwrap_or_default(),
        issued_at,
    })
}

// ---------------------------------------------------------------------------
// Analytics
// ---------------------------------------------------------------------------

pub async fn get_trail_analytics(
    pool: &PgPool,
    trail_id: Uuid,
) -> Result<TrailAnalyticsOut, AppError> {
    let unique_starts: i64 = sqlx::query_scalar(
        "SELECT COUNT(DISTINCT user_id)::bigint FROM user_trail_progress WHERE trail_id = $1",
    )
    .bind(trail_id)
    .fetch_one(pool)
    .await
    .map_err(|e| AppError::Internal(e.into()))?;

    let completed: i64 = sqlx::query_scalar(
        "SELECT COUNT(*)::bigint FROM user_trail_progress \
         WHERE trail_id = $1 AND completed_at IS NOT NULL",
    )
    .bind(trail_id)
    .fetch_one(pool)
    .await
    .map_err(|e| AppError::Internal(e.into()))?;

    let avg_days: Option<f64> = sqlx::query_scalar(
        "SELECT AVG(EXTRACT(EPOCH FROM (completed_at - started_at)) / 86400.0)::float8 \
         FROM user_trail_progress \
         WHERE trail_id = $1 AND completed_at IS NOT NULL",
    )
    .bind(trail_id)
    .fetch_one(pool)
    .await
    .ok()
    .flatten();

    let completion_rate = if unique_starts == 0 {
        0.0
    } else {
        (completed as f64) / (unique_starts as f64)
    };

    let skipped: Vec<SkippedCheckpointOut> = sqlx::query_as(
        r#"
        SELECT
            c.id           AS checkpoint_id,
            c.after_position,
            c.prompt_vi,
            (
                SELECT COUNT(*)::bigint
                FROM user_trail_progress p
                WHERE p.trail_id = c.trail_id
                  AND p.current_position > c.after_position
                  AND NOT EXISTS (
                    SELECT 1 FROM user_trail_checkpoint_responses r
                    WHERE r.checkpoint_id = c.id AND r.user_id = p.user_id
                  )
            ) AS null_response_count
        FROM trail_checkpoints c
        WHERE c.trail_id = $1
        ORDER BY null_response_count DESC
        LIMIT 5
        "#,
    )
    .bind(trail_id)
    .fetch_all(pool)
    .await
    .map_err(|e| AppError::Internal(e.into()))?;

    Ok(TrailAnalyticsOut {
        unique_starts,
        completed,
        completion_rate,
        average_days_to_complete: avg_days,
        top_skipped_checkpoints: skipped,
    })
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn certificate_hash_is_deterministic() {
        let u = Uuid::new_v4();
        let t = Uuid::new_v4();
        let h1 = generate_certificate_hash(u, t, 12345);
        let h2 = generate_certificate_hash(u, t, 12345);
        assert_eq!(h1, h2);
        assert_eq!(h1.len(), 64);
    }

    #[test]
    fn certificate_hash_distinguishes_inputs() {
        let u = Uuid::new_v4();
        let t = Uuid::new_v4();
        let h1 = generate_certificate_hash(u, t, 12345);
        let h2 = generate_certificate_hash(u, t, 12346);
        assert_ne!(h1, h2);
    }

    #[test]
    fn pace_reminder_hours() {
        assert_eq!(Pace::Daily.reminder_hours(), 24);
        assert_eq!(Pace::TwiceWeek.reminder_hours(), 84);
        assert_eq!(Pace::Weekly.reminder_hours(), 168);
    }

    #[test]
    fn pace_parse_validates() {
        assert_eq!(Pace::parse("daily"), Some(Pace::Daily));
        assert_eq!(Pace::parse("2x_week"), Some(Pace::TwiceWeek));
        assert_eq!(Pace::parse("weekly"), Some(Pace::Weekly));
        assert_eq!(Pace::parse("hourly"), None);
    }
}


#[cfg(test)]
mod property_tests {
    //! Loop-based property tests for trail certificate hashing and pace.
    //!
    //! Mirrors Properties 7, 8, 9 from
    //! `.kiro/specs/heritage-trail-mode/design.md`.

    use super::*;

    /// Property 9: hash is deterministic and distinguishes distinct inputs.
    #[test]
    fn property_certificate_hash_uniqueness() {
        let mut hashes = std::collections::HashSet::new();
        for i in 0..200 {
            let u = Uuid::new_v4();
            let t = Uuid::new_v4();
            let h = generate_certificate_hash(u, t, i);
            // determinism
            assert_eq!(h, generate_certificate_hash(u, t, i));
            assert_eq!(h.len(), 64);
            assert!(hashes.insert(h), "hash collision on iteration {i}");
        }
    }

    /// Property 8: pace cadence is exactly the documented hours.
    #[test]
    fn property_pace_reminder_hours() {
        for (input, expected) in [
            ("daily", 24),
            ("2x_week", 84),
            ("weekly", 168),
        ] {
            let p = Pace::parse(input).unwrap();
            assert_eq!(p.reminder_hours(), expected);
        }
    }

    /// Property 7: pace parser accepts only the three valid values.
    #[test]
    fn property_pace_only_accepts_valid_values() {
        let valid = ["daily", "2x_week", "weekly"];
        for v in valid {
            assert!(Pace::parse(v).is_some());
        }
        let invalid = ["", "Daily", "monthly", "1x_week", "3x_week", "hourly"];
        for v in invalid {
            assert!(Pace::parse(v).is_none(), "{v} should not parse");
        }
    }
}
