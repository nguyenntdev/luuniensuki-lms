//! FSRS scheduling service.
//!
//! Wraps the pure algo (`fsrs_algo`) with database I/O against
//! `spaced_repetition_cards`, `user_fsrs_params`, and `fsrs_cohort_params`.
//!
//! Spec: `.kiro/specs/fsrs-spaced-repetition/`

use axum::http::StatusCode;
use chrono::{DateTime, Duration, Utc};
use serde_json::json;
use sqlx::PgPool;
use uuid::Uuid;

use crate::error::AppError;
use crate::models::fsrs::{
    CardState, DueCardOut, DueReviewsResponse, FsrsRating, FsrsSettingsResponse, RateCardResponse,
};
use crate::services::cohort_service::assign_cohort;
use crate::services::fsrs_algo::{schedule, DEFAULT_W};

const PERSONAL_PARAMS_THRESHOLD: i64 = 50;

/// `GET /api/v1/reviews/due`
pub async fn get_due_cards(
    pool: &PgPool,
    user_id: Uuid,
    page: u32,
    page_size: u32,
) -> Result<DueReviewsResponse, AppError> {
    let page = page.max(1);
    let page_size = page_size.clamp(1, 100);
    let offset = ((page - 1) * page_size) as i64;

    let rows: Vec<(
        Uuid,
        Uuid,
        Option<String>,
        Option<f64>,
        Option<f64>,
        Option<DateTime<Utc>>,
        Option<String>,
    )> = sqlx::query_as(
        r#"
            SELECT c.id,
                   c.motif_id,
                   m.name AS motif_name,
                   c.fsrs_stability,
                   c.fsrs_difficulty,
                   c.fsrs_due_date,
                   c.fsrs_state
            FROM spaced_repetition_cards c
            LEFT JOIN motifs m ON m.id = c.motif_id
            WHERE c.user_id = $1
              AND COALESCE(c.fsrs_due_date, c.next_review_at) <= NOW()
            ORDER BY COALESCE(c.fsrs_due_date, c.next_review_at) ASC
            LIMIT $2 OFFSET $3
            "#,
    )
    .bind(user_id)
    .bind(page_size as i64)
    .bind(offset)
    .fetch_all(pool)
    .await
    .map_err(|e| AppError::Internal(e.into()))?;

    let total: i64 = sqlx::query_scalar::<_, i64>(
        "SELECT COUNT(*)::bigint FROM spaced_repetition_cards \
         WHERE user_id = $1 AND COALESCE(fsrs_due_date, next_review_at) <= NOW()",
    )
    .bind(user_id)
    .fetch_one(pool)
    .await
    .map_err(|e| AppError::Internal(e.into()))?;

    let cards = rows
        .into_iter()
        .map(|(id, motif_id, name, stab, diff, due, state)| DueCardOut {
            card_id: id,
            motif_id,
            motif_name: name,
            fsrs_due_date: due.unwrap_or_else(Utc::now),
            fsrs_stability: stab,
            fsrs_difficulty: diff,
            fsrs_state: state,
        })
        .collect();

    Ok(DueReviewsResponse {
        cards,
        total,
        page,
        page_size,
    })
}

/// `POST /api/v1/reviews/:card_id/rate`
pub async fn rate_card(
    pool: &PgPool,
    user_id: Uuid,
    card_id: Uuid,
    rating: FsrsRating,
) -> Result<RateCardResponse, AppError> {
    // 1. Verify ownership and load existing state.
    let row: Option<(
        Uuid,
        Option<String>,
        Option<f64>,
        Option<f64>,
        Option<DateTime<Utc>>,
        Option<DateTime<Utc>>,
    )> = sqlx::query_as(
        "SELECT user_id, fsrs_state, fsrs_difficulty, fsrs_stability, \
                fsrs_due_date, fsrs_last_review \
         FROM spaced_repetition_cards \
         WHERE id = $1",
    )
    .bind(card_id)
    .fetch_optional(pool)
    .await
    .map_err(|e| AppError::Internal(e.into()))?;

    let (owner_id, state_str, difficulty, stability, _due, last_review) =
        row.ok_or_else(|| AppError::Domain {
            status: StatusCode::NOT_FOUND,
            code: "CARD_NOT_FOUND".to_string(),
            message: "Review card not found".to_string(),
            details: json!({}),
        })?;

    if owner_id != user_id {
        return Err(AppError::Domain {
            status: StatusCode::FORBIDDEN,
            code: "FORBIDDEN".to_string(),
            message: "You do not own this card".to_string(),
            details: json!({}),
        });
    }

    // 2. Determine cohort and load parameters.
    let cohort = assign_cohort(&user_id);
    let (params, optimal_retention) = load_params(pool, user_id).await?;

    // 3. Compute schedule.
    let state = state_str
        .as_deref()
        .map(CardState::parse)
        .unwrap_or(CardState::New);
    let now = Utc::now();
    let delta_t = match last_review {
        Some(t) => (now - t).num_seconds() as f64 / 86_400.0,
        None => 0.0,
    };
    let result = schedule(
        state,
        difficulty,
        stability,
        delta_t,
        rating,
        &params,
        optimal_retention,
    );

    // 4. Persist state.
    let due_date = now + Duration::seconds((result.interval_days * 86_400.0) as i64);
    sqlx::query(
        r#"
        UPDATE spaced_repetition_cards
        SET fsrs_state      = $2,
            fsrs_difficulty = $3,
            fsrs_stability  = $4,
            fsrs_due_date   = $5,
            fsrs_last_review= NOW(),
            interval_days   = GREATEST(1, $6),
            next_review_at  = $5,
            last_reviewed_at= NOW(),
            updated_at      = NOW()
        WHERE id = $1
        "#,
    )
    .bind(card_id)
    .bind(result.state.as_str())
    .bind(result.difficulty)
    .bind(result.stability)
    .bind(due_date)
    .bind(result.interval_days as i32)
    .execute(pool)
    .await
    .map_err(|e| AppError::Internal(e.into()))?;

    // 5. Log analytics event. Failure is logged but does not surface to the
    //    user — losing one analytics row should not fail an otherwise-
    //    successful review submission.
    if let Err(err) = sqlx::query(
        r#"
        INSERT INTO analytics_events (id, event_type, user_id, payload, created_at)
        VALUES (gen_random_uuid(), 'review_completed', $1, $2::jsonb, NOW())
        "#,
    )
    .bind(user_id)
    .bind(
        json!({
            "card_id": card_id,
            "rating": rating.as_str(),
            "cohort": cohort.name(),
            "stability": result.stability,
            "difficulty": result.difficulty,
        })
        .to_string(),
    )
    .execute(pool)
    .await
    {
        tracing::warn!(
            feature = "fsrs_review",
            user_id = %user_id,
            error = %err,
            "analytics insert failed",
        );
    }

    crate::routes::metrics::FSRS_REVIEWS_TOTAL.fetch_add(1, std::sync::atomic::Ordering::Relaxed);

    Ok(RateCardResponse {
        card_id,
        fsrs_due_date: due_date,
        fsrs_stability: result.stability,
        fsrs_difficulty: result.difficulty,
        fsrs_state: result.state.as_str().to_string(),
        interval_days: result.interval_days,
        cohort: cohort.name().to_string(),
    })
}

/// `GET /api/v1/users/me/fsrs-settings`
pub async fn get_settings(pool: &PgPool, user_id: Uuid) -> Result<FsrsSettingsResponse, AppError> {
    let cohort = assign_cohort(&user_id);

    let row: Option<(Vec<f64>, f64, Option<DateTime<Utc>>)> = sqlx::query_as(
        "SELECT parameters, optimal_retention, last_optimized_at \
         FROM user_fsrs_params WHERE user_id = $1",
    )
    .bind(user_id)
    .fetch_optional(pool)
    .await
    .map_err(|e| AppError::Internal(e.into()))?;

    let review_count: i64 = sqlx::query_scalar::<_, i64>(
        "SELECT COUNT(*)::bigint FROM spaced_repetition_cards \
         WHERE user_id = $1 AND fsrs_last_review IS NOT NULL",
    )
    .bind(user_id)
    .fetch_one(pool)
    .await
    .map_err(|e| AppError::Internal(e.into()))?;

    let (optimal_retention, last_optimized_at, has_personal) = match row {
        Some((params, ret, opt)) => (ret, opt, !params.is_empty()),
        None => (0.9, None, false),
    };

    let using_personal_params = has_personal && review_count >= PERSONAL_PARAMS_THRESHOLD;

    Ok(FsrsSettingsResponse {
        optimal_retention,
        recommended_range: [0.75, 0.97],
        last_optimized_at,
        review_count,
        using_personal_params,
        cohort: cohort.name().to_string(),
    })
}

/// `PUT /api/v1/users/me/fsrs-settings`
pub async fn update_settings(
    pool: &PgPool,
    user_id: Uuid,
    optimal_retention: f64,
) -> Result<FsrsSettingsResponse, AppError> {
    if !(0.70..=0.97).contains(&optimal_retention) {
        return Err(AppError::Domain {
            status: StatusCode::BAD_REQUEST,
            code: "INVALID_RETENTION".to_string(),
            message: "Optimal retention must be between 0.70 and 0.97".to_string(),
            details: json!({"received": optimal_retention}),
        });
    }

    sqlx::query(
        r#"
        INSERT INTO user_fsrs_params (user_id, parameters, optimal_retention)
        VALUES ($1, '{}'::double precision[], $2)
        ON CONFLICT (user_id) DO UPDATE
        SET optimal_retention = EXCLUDED.optimal_retention,
            updated_at = NOW()
        "#,
    )
    .bind(user_id)
    .bind(optimal_retention)
    .execute(pool)
    .await
    .map_err(|e| AppError::Internal(e.into()))?;

    get_settings(pool, user_id).await
}

/// Load weights + retention for a user, falling back to cohort defaults.
async fn load_params(pool: &PgPool, user_id: Uuid) -> Result<([f64; 21], f64), AppError> {
    let row: Option<(Vec<f64>, f64)> = sqlx::query_as(
        "SELECT parameters, optimal_retention FROM user_fsrs_params WHERE user_id = $1",
    )
    .bind(user_id)
    .fetch_optional(pool)
    .await
    .map_err(|e| AppError::Internal(e.into()))?;

    if let Some((params, ret)) = row {
        if params.len() == 21 {
            let mut w = [0.0; 21];
            for (i, v) in params.into_iter().enumerate() {
                w[i] = v;
            }
            return Ok((w, ret));
        }
        // user row exists but has empty/invalid parameters — fall through to
        // cohort defaults but use the user's retention slider.
        let (cohort_w, _) = load_cohort_defaults(pool).await?;
        return Ok((cohort_w, ret));
    }
    load_cohort_defaults(pool).await
}

async fn load_cohort_defaults(pool: &PgPool) -> Result<([f64; 21], f64), AppError> {
    let row: Option<(Vec<f64>, f64)> = sqlx::query_as(
        "SELECT parameters, optimal_retention FROM fsrs_cohort_params \
         WHERE cohort_name = 'default'",
    )
    .fetch_optional(pool)
    .await
    .map_err(|e| AppError::Internal(e.into()))?;

    match row {
        Some((params, ret)) if params.len() == 21 => {
            let mut w = [0.0; 21];
            for (i, v) in params.into_iter().enumerate() {
                w[i] = v;
            }
            Ok((w, ret))
        }
        _ => Ok((DEFAULT_W, 0.9)),
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn cohort_assignment_works() {
        let _ = assign_cohort(&Uuid::new_v4());
    }
}
