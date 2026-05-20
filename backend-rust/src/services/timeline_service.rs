//! Heritage Time-Lapse business logic.
//!
//! Spec: `.kiro/specs/heritage-time-lapse/`

use axum::http::StatusCode;
use chrono::Datelike;
use serde_json::json;
use sqlx::PgPool;
use uuid::Uuid;

use crate::error::AppError;
use crate::models::timeline::{
    ComparedMotif, ComparedPair, CompareResponse, CreateEraRequest, CreateEventRequest,
    EraSummary, HeritageEraRow, HistoricalEventOut, HistoricalEventRow, MotifByEraOut,
    MotifSummary, MotifsByEraResponse, TimelineEventsMeta, TimelineEventsResponse,
    TimelineStatsResponse, UrnSummary, WeeklyView,
};

const COMPARISON_AXES: &[&str] = &["category", "rarity", "era", "urn"];

// ---------------------------------------------------------------------------
// Era CRUD
// ---------------------------------------------------------------------------

pub async fn create_era(
    pool: &PgPool,
    payload: &CreateEraRequest,
) -> Result<HeritageEraRow, AppError> {
    if payload.end_year < payload.start_year {
        return Err(AppError::Validation {
            details: json!({"end_year": "must be >= start_year"}),
        });
    }
    if !is_valid_color_hex(&payload.color_hex) {
        return Err(AppError::Validation {
            details: json!({"color_hex": "must match #RRGGBB"}),
        });
    }
    let row = sqlx::query_as::<_, HeritageEraRow>(
        r#"
        INSERT INTO heritage_eras
            (slug, name_vi, name_en, start_year, end_year, color_hex, sort_order)
        VALUES ($1, $2, $3, $4, $5, $6, COALESCE($7, 0))
        RETURNING id, slug, name_vi, name_en, start_year, end_year, color_hex, sort_order, created_at
        "#,
    )
    .bind(&payload.slug)
    .bind(&payload.name_vi)
    .bind(&payload.name_en)
    .bind(payload.start_year)
    .bind(payload.end_year)
    .bind(&payload.color_hex)
    .bind(payload.sort_order)
    .fetch_one(pool)
    .await
    .map_err(|e| AppError::Internal(e.into()))?;
    Ok(row)
}

pub async fn create_event(
    pool: &PgPool,
    payload: &CreateEventRequest,
) -> Result<HistoricalEventRow, AppError> {
    if !(1..=5).contains(&payload.importance) {
        return Err(AppError::Validation {
            details: json!({"importance": "must be 1-5"}),
        });
    }
    let row = sqlx::query_as::<_, HistoricalEventRow>(
        r#"
        INSERT INTO historical_events
            (era_id, slug, name_vi, name_en, occurred_on,
             description_vi, description_en, motif_id, urn_id, importance)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
        RETURNING id, era_id, slug, name_vi, name_en, occurred_on,
                  description_vi, description_en, motif_id, urn_id, importance, created_at
        "#,
    )
    .bind(payload.era_id)
    .bind(&payload.slug)
    .bind(&payload.name_vi)
    .bind(&payload.name_en)
    .bind(payload.occurred_on)
    .bind(&payload.description_vi)
    .bind(&payload.description_en)
    .bind(payload.motif_id)
    .bind(payload.urn_id)
    .bind(payload.importance)
    .fetch_one(pool)
    .await
    .map_err(|e| AppError::Internal(e.into()))?;
    Ok(row)
}

// ---------------------------------------------------------------------------
// Public listings
// ---------------------------------------------------------------------------

pub async fn list_events(
    pool: &PgPool,
    from_year: Option<i32>,
    to_year: Option<i32>,
) -> Result<TimelineEventsResponse, AppError> {
    #[derive(sqlx::FromRow)]
    struct Row {
        id: Uuid,
        slug: String,
        name_vi: String,
        name_en: String,
        occurred_on: chrono::NaiveDate,
        description_vi: String,
        description_en: String,
        importance: i32,
        era_id: Uuid,
        era_slug: String,
        era_name_vi: String,
        era_color_hex: String,
        motif_id: Option<Uuid>,
        motif_name: Option<String>,
        motif_thumb: Option<String>,
        urn_id: Option<Uuid>,
        urn_slug: Option<String>,
        urn_name: Option<String>,
    }

    let rows: Vec<Row> = sqlx::query_as(
        r#"
        SELECT
            h.id, h.slug, h.name_vi, h.name_en, h.occurred_on,
            h.description_vi, h.description_en, h.importance,
            e.id          AS era_id,
            e.slug        AS era_slug,
            e.name_vi     AS era_name_vi,
            e.color_hex   AS era_color_hex,
            h.motif_id,
            m.name        AS motif_name,
            m.thumbnail_url AS motif_thumb,
            h.urn_id,
            u.slug        AS urn_slug,
            u.name        AS urn_name
        FROM historical_events h
        JOIN heritage_eras e ON e.id = h.era_id
        LEFT JOIN motifs m ON m.id = h.motif_id
        LEFT JOIN urns u ON u.id = h.urn_id
        WHERE ($1::int IS NULL OR EXTRACT(YEAR FROM h.occurred_on)::int >= $1)
          AND ($2::int IS NULL OR EXTRACT(YEAR FROM h.occurred_on)::int <= $2)
        ORDER BY h.occurred_on ASC
        "#,
    )
    .bind(from_year)
    .bind(to_year)
    .fetch_all(pool)
    .await
    .map_err(|e| AppError::Internal(e.into()))?;

    let mut min_year: Option<i32> = None;
    let mut max_year: Option<i32> = None;
    let total = rows.len() as i64;
    let events: Vec<HistoricalEventOut> = rows
        .into_iter()
        .map(|r| {
            let year = r.occurred_on.year();
            min_year = Some(min_year.map_or(year, |m| m.min(year)));
            max_year = Some(max_year.map_or(year, |m| m.max(year)));
            HistoricalEventOut {
                id: r.id,
                slug: r.slug,
                name_vi: r.name_vi,
                name_en: r.name_en,
                occurred_on: r.occurred_on,
                description_vi: r.description_vi,
                description_en: r.description_en,
                importance: r.importance,
                era: EraSummary {
                    id: r.era_id,
                    slug: r.era_slug,
                    name_vi: r.era_name_vi,
                    color_hex: r.era_color_hex,
                },
                motif: r.motif_id.map(|id| MotifSummary {
                    id,
                    name: r.motif_name.unwrap_or_default(),
                    thumbnail_url: r.motif_thumb,
                }),
                urn: r.urn_id.map(|id| UrnSummary {
                    id,
                    slug: r.urn_slug.unwrap_or_default(),
                    name: r.urn_name.unwrap_or_default(),
                }),
            }
        })
        .collect();

    Ok(TimelineEventsResponse {
        events,
        meta: TimelineEventsMeta {
            min_year,
            max_year,
            total_count: total,
        },
    })
}

pub async fn list_motifs_by_era(
    pool: &PgPool,
    era_slug: &str,
) -> Result<MotifsByEraResponse, AppError> {
    let era: Option<HeritageEraRow> = sqlx::query_as(
        "SELECT id, slug, name_vi, name_en, start_year, end_year, color_hex, sort_order, created_at \
         FROM heritage_eras WHERE slug = $1",
    )
    .bind(era_slug)
    .fetch_optional(pool)
    .await
    .map_err(|e| AppError::Internal(e.into()))?;

    let era = era.ok_or_else(|| AppError::Http {
        status: StatusCode::NOT_FOUND,
        message: format!("Era '{}' not found", era_slug),
    })?;

    #[derive(sqlx::FromRow)]
    struct MotifRow {
        id: Uuid,
        name: String,
        category: Option<String>,
        rarity: Option<String>,
        thumbnail_url: Option<String>,
        urn_id: Option<Uuid>,
        urn_slug: Option<String>,
        urn_name: Option<String>,
    }
    let rows: Vec<MotifRow> = sqlx::query_as(
        r#"
        SELECT m.id, m.name, m.category, m.rarity, m.thumbnail_url,
               u.id   AS urn_id,
               u.slug AS urn_slug,
               u.name AS urn_name
        FROM motif_eras me
        JOIN motifs m ON m.id = me.motif_id
        LEFT JOIN urns u ON u.id = m.urn_id
        WHERE me.era_id = $1
        ORDER BY m.name ASC
        "#,
    )
    .bind(era.id)
    .fetch_all(pool)
    .await
    .map_err(|e| AppError::Internal(e.into()))?;

    let motifs = rows
        .into_iter()
        .map(|r| MotifByEraOut {
            id: r.id,
            name: r.name,
            category: r.category,
            rarity: r.rarity,
            thumbnail_url: r.thumbnail_url,
            urn: r.urn_id.map(|id| UrnSummary {
                id,
                slug: r.urn_slug.unwrap_or_default(),
                name: r.urn_name.unwrap_or_default(),
            }),
        })
        .collect();

    Ok(MotifsByEraResponse { era, motifs })
}

// ---------------------------------------------------------------------------
// Compare
// ---------------------------------------------------------------------------

pub async fn compare_motifs(
    pool: &PgPool,
    raw_ids: &str,
) -> Result<CompareResponse, AppError> {
    let parts: Vec<&str> = raw_ids.split(',').filter(|s| !s.is_empty()).collect();
    if parts.len() != 2 {
        return Err(AppError::Domain {
            status: StatusCode::BAD_REQUEST,
            code: "INVALID_COMPARE_PAIR".to_string(),
            message: "Exactly 2 motif IDs are required".to_string(),
            details: json!({"received": parts.len()}),
        });
    }
    let mut ids: Vec<Uuid> = Vec::with_capacity(2);
    for p in parts {
        ids.push(p.trim().parse().map_err(|_| AppError::Domain {
            status: StatusCode::BAD_REQUEST,
            code: "INVALID_COMPARE_PAIR".to_string(),
            message: "ids must be valid UUIDs".to_string(),
            details: json!({}),
        })?);
    }

    #[derive(sqlx::FromRow)]
    struct MRow {
        id: Uuid,
        name: String,
        name_en: Option<String>,
        description: Option<String>,
        category: Option<String>,
        rarity: Option<String>,
        thumbnail_url: Option<String>,
        urn_id: Option<Uuid>,
        urn_slug: Option<String>,
        urn_name: Option<String>,
    }
    let rows: Vec<MRow> = sqlx::query_as(
        r#"
        SELECT m.id, m.name, m.name_en, m.description, m.category, m.rarity,
               m.thumbnail_url,
               u.id   AS urn_id,
               u.slug AS urn_slug,
               u.name AS urn_name
        FROM motifs m
        LEFT JOIN urns u ON u.id = m.urn_id
        WHERE m.id = ANY($1)
        "#,
    )
    .bind(&ids)
    .fetch_all(pool)
    .await
    .map_err(|e| AppError::Internal(e.into()))?;

    if rows.len() != 2 {
        return Err(AppError::Http {
            status: StatusCode::NOT_FOUND,
            message: "One or more motifs not found".to_string(),
        });
    }

    // Fetch eras per motif
    let era_rows: Vec<(Uuid, Uuid, String, String, String)> = sqlx::query_as(
        r#"
        SELECT me.motif_id, e.id, e.slug, e.name_vi, e.color_hex
        FROM motif_eras me
        JOIN heritage_eras e ON e.id = me.era_id
        WHERE me.motif_id = ANY($1)
        "#,
    )
    .bind(&ids)
    .fetch_all(pool)
    .await
    .map_err(|e| AppError::Internal(e.into()))?;

    use std::collections::HashMap;
    let mut eras_by_motif: HashMap<Uuid, Vec<EraSummary>> = HashMap::new();
    for (motif_id, era_id, slug, name_vi, color_hex) in era_rows {
        eras_by_motif
            .entry(motif_id)
            .or_default()
            .push(EraSummary {
                id: era_id,
                slug,
                name_vi,
                color_hex,
            });
    }

    let motifs = rows
        .into_iter()
        .map(|r| ComparedMotif {
            id: r.id,
            name: r.name,
            name_en: r.name_en,
            description: r.description,
            category: r.category,
            rarity: r.rarity,
            eras: eras_by_motif.remove(&r.id).unwrap_or_default(),
            urn: r.urn_id.map(|id| UrnSummary {
                id,
                slug: r.urn_slug.unwrap_or_default(),
                name: r.urn_name.unwrap_or_default(),
            }),
            thumbnail_url: r.thumbnail_url,
        })
        .collect();

    Ok(CompareResponse {
        motifs,
        comparison_axes: COMPARISON_AXES.to_vec(),
    })
}

// ---------------------------------------------------------------------------
// Admin stats
// ---------------------------------------------------------------------------

pub async fn get_timeline_stats(pool: &PgPool) -> Result<TimelineStatsResponse, AppError> {
    let weekly_views: Vec<WeeklyView> = sqlx::query_as(
        r#"
        SELECT date_trunc('week', created_at)::date AS week_start, COUNT(*)::bigint AS count
        FROM analytics_events
        WHERE event_type = 'timeline_viewed'
          AND created_at >= NOW() - INTERVAL '90 days'
        GROUP BY 1
        ORDER BY 1 ASC
        "#,
    )
    .fetch_all(pool)
    .await
    .unwrap_or_default();

    // Top compared pairs from analytics events
    let top: Vec<(Uuid, Uuid, i64)> = sqlx::query_as(
        r#"
        SELECT
            (payload::jsonb -> 'motif_ids' ->> 0)::uuid AS motif_a_id,
            (payload::jsonb -> 'motif_ids' ->> 1)::uuid AS motif_b_id,
            COUNT(*)::bigint AS count
        FROM analytics_events
        WHERE event_type = 'compare_opened'
          AND payload::jsonb -> 'motif_ids' IS NOT NULL
          AND jsonb_array_length(payload::jsonb -> 'motif_ids') >= 2
        GROUP BY 1, 2
        ORDER BY count DESC
        LIMIT 10
        "#,
    )
    .fetch_all(pool)
    .await
    .unwrap_or_default();

    let top_compared_pairs = top
        .into_iter()
        .map(|(a, b, c)| ComparedPair {
            motif_a_id: a,
            motif_b_id: b,
            count: c,
        })
        .collect();

    Ok(TimelineStatsResponse {
        weekly_views,
        top_compared_pairs,
    })
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

fn is_valid_color_hex(s: &str) -> bool {
    s.len() == 7
        && s.starts_with('#')
        && s[1..].chars().all(|c| c.is_ascii_hexdigit())
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn color_hex_validation() {
        assert!(is_valid_color_hex("#D4AF37"));
        assert!(is_valid_color_hex("#000000"));
        assert!(is_valid_color_hex("#abcdef"));
        assert!(!is_valid_color_hex("D4AF37"));
        assert!(!is_valid_color_hex("#GGGGGG"));
        assert!(!is_valid_color_hex("#12345"));
        assert!(!is_valid_color_hex(""));
    }
}
