//! Admin render performance dashboard.
//!
//! Gap 4 from `docs/CONFERENCE_PAPER_MATCH_ANALYSIS.md`: validates the paper's
//! claim of "+46% speedup" via 3D model LOD optimization by aggregating the
//! `render_performance` analytics events emitted from `UrnViewer`.
//!
//! Endpoint: `GET /api/v1/admin/analytics/render-performance`
//! Auth:     admin role required (matches the pattern in `routes/admin.rs`).

use axum::{
    extract::{Query, State},
    http::{header, HeaderMap, StatusCode},
    response::IntoResponse,
    Json,
};
use chrono::{DateTime, Duration, Utc};
use serde::Deserialize;
use sqlx::PgPool;

use crate::auth;
use crate::config::Settings;
use crate::error::AppError;
use crate::models::session::{
    Percentiles, RenderPerfAggRow, RenderPerfByLod, RenderPerfResponse, RenderPerfSpeedup,
};
use crate::routes::auth::AuthState;

// ---------------------------------------------------------------------------
// Auth helpers (mirror routes/admin.rs)
// ---------------------------------------------------------------------------

fn extract_token_from_headers(headers: &HeaderMap) -> Option<String> {
    if let Some(auth_header) = headers.get(header::AUTHORIZATION) {
        if let Ok(auth_str) = auth_header.to_str() {
            if let Some(token) = auth_str.strip_prefix("Bearer ") {
                return Some(token.to_string());
            }
        }
    }
    if let Some(cookie_header) = headers.get(header::COOKIE) {
        if let Ok(cookie_str) = cookie_header.to_str() {
            for part in cookie_str.split(';') {
                let trimmed = part.trim();
                if let Some(value) = trimmed.strip_prefix("luuniensuki_access=") {
                    return Some(value.to_string());
                }
            }
        }
    }
    None
}

fn require_pool(pool: &Option<PgPool>) -> Result<&PgPool, AppError> {
    pool.as_ref().ok_or_else(|| AppError::Http {
        status: StatusCode::SERVICE_UNAVAILABLE,
        message: "Database unavailable".to_string(),
    })
}

fn authenticate_admin(headers: &HeaderMap, settings: &Settings) -> Result<(), AppError> {
    let token = extract_token_from_headers(headers).ok_or(AppError::Unauthorized)?;
    let claims = auth::verify_access_token(&token, &settings.jwt_secret_key, settings.jwt_validate_new_claims, &settings.jwt_issuer, &settings.jwt_audience)
        .map_err(|_| AppError::Unauthorized)?;
    if claims.role != "admin" {
        return Err(AppError::Http {
            status: StatusCode::FORBIDDEN,
            message: "Admin access required".to_string(),
        });
    }
    Ok(())
}

// ---------------------------------------------------------------------------
// Query params
// ---------------------------------------------------------------------------

#[derive(Debug, Deserialize)]
pub struct RenderPerfQuery {
    pub from: Option<DateTime<Utc>>,
    pub to: Option<DateTime<Utc>>,
    pub urn_slug: Option<String>,
    pub lod: Option<String>,
}

// ---------------------------------------------------------------------------
// Handler
// ---------------------------------------------------------------------------

/// GET /api/v1/admin/analytics/render-performance
pub async fn get_render_performance(
    headers: HeaderMap,
    State(state): State<AuthState>,
    Query(params): Query<RenderPerfQuery>,
) -> Result<impl IntoResponse, AppError> {
    authenticate_admin(&headers, &state.settings)?;
    let pool = require_pool(&state.pool)?;

    let to = params.to.unwrap_or_else(Utc::now);
    let from = params.from.unwrap_or_else(|| to - Duration::days(7));

    let urn_slug = params.urn_slug.as_deref();
    let lod = params.lod.as_deref();

    // PostgreSQL percentile_cont aggregation, grouped by LOD label.
    // The payload column is jsonb; we cast to numeric for percentiles and to
    // bigint for the file size average.
    let rows = sqlx::query_as::<_, RenderPerfAggRow>(
        r#"
        SELECT
            payload->>'lod_label' AS lod_label,
            COUNT(*) AS sample_count,
            AVG(NULLIF(payload->>'file_size_bytes','')::bigint)::float8 AS avg_file_size_bytes,
            percentile_cont(0.5)  WITHIN GROUP (ORDER BY NULLIF(payload->>'ttf_ms','')::numeric)::float8 AS ttf_p50,
            percentile_cont(0.95) WITHIN GROUP (ORDER BY NULLIF(payload->>'ttf_ms','')::numeric)::float8 AS ttf_p95,
            percentile_cont(0.99) WITHIN GROUP (ORDER BY NULLIF(payload->>'ttf_ms','')::numeric)::float8 AS ttf_p99,
            percentile_cont(0.5)  WITHIN GROUP (ORDER BY NULLIF(payload->>'ttfi_ms','')::numeric)::float8 AS ttfi_p50,
            percentile_cont(0.95) WITHIN GROUP (ORDER BY NULLIF(payload->>'ttfi_ms','')::numeric)::float8 AS ttfi_p95,
            percentile_cont(0.99) WITHIN GROUP (ORDER BY NULLIF(payload->>'ttfi_ms','')::numeric)::float8 AS ttfi_p99,
            percentile_cont(0.5)  WITHIN GROUP (ORDER BY NULLIF(payload->>'avg_fps','')::numeric)::float8 AS fps_p50,
            percentile_cont(0.95) WITHIN GROUP (ORDER BY NULLIF(payload->>'avg_fps','')::numeric)::float8 AS fps_p95,
            percentile_cont(0.99) WITHIN GROUP (ORDER BY NULLIF(payload->>'avg_fps','')::numeric)::float8 AS fps_p99
        FROM analytics_events
        WHERE event_name = 'render_performance'
          AND created_at >= $1
          AND created_at <= $2
          AND payload->>'lod_label' IS NOT NULL
          AND ($3::text IS NULL OR payload->>'urn_slug' = $3)
          AND ($4::text IS NULL OR payload->>'lod_label' = $4)
        GROUP BY payload->>'lod_label'
        ORDER BY payload->>'lod_label'
        "#,
    )
    .bind(from)
    .bind(to)
    .bind(urn_slug)
    .bind(lod)
    .fetch_all(pool)
    .await
    .map_err(|e| AppError::Internal(e.into()))?;

    let by_lod: Vec<RenderPerfByLod> = rows
        .into_iter()
        .filter_map(|r| {
            let label = r.lod_label?;
            Some(RenderPerfByLod {
                lod_label: label,
                sample_count: r.sample_count,
                avg_file_size_bytes: r.avg_file_size_bytes,
                ttf_ms: Percentiles {
                    p50: r.ttf_p50,
                    p95: r.ttf_p95,
                    p99: r.ttf_p99,
                },
                ttfi_ms: Percentiles {
                    p50: r.ttfi_p50,
                    p95: r.ttfi_p95,
                    p99: r.ttfi_p99,
                },
                avg_fps: Percentiles {
                    p50: r.fps_p50,
                    p95: r.fps_p95,
                    p99: r.fps_p99,
                },
            })
        })
        .collect();

    let speedup = compute_speedup_vs_2k(&by_lod);

    Ok(Json(RenderPerfResponse {
        from,
        to,
        by_lod,
        speedup_vs_2k: speedup,
    }))
}

// ---------------------------------------------------------------------------
// Speedup helper
// ---------------------------------------------------------------------------

fn find_p50(by_lod: &[RenderPerfByLod], label: &str) -> Option<f64> {
    by_lod
        .iter()
        .find(|b| b.lod_label.eq_ignore_ascii_case(label))
        .and_then(|b| b.ttf_ms.p50)
}

fn pct_speedup(faster_p50: f64, baseline_p50: f64) -> Option<f64> {
    if baseline_p50 <= 0.0 {
        return None;
    }
    let pct = (baseline_p50 - faster_p50) / baseline_p50 * 100.0;
    Some((pct * 10.0).round() / 10.0)
}

fn compute_speedup_vs_2k(by_lod: &[RenderPerfByLod]) -> RenderPerfSpeedup {
    let baseline = find_p50(by_lod, "2k");
    let p512 = find_p50(by_lod, "512");
    let p1k = find_p50(by_lod, "1k");

    RenderPerfSpeedup {
        k512_vs_2k_ttf_pct: match (p512, baseline) {
            (Some(a), Some(b)) => pct_speedup(a, b),
            _ => None,
        },
        k1k_vs_2k_ttf_pct: match (p1k, baseline) {
            (Some(a), Some(b)) => pct_speedup(a, b),
            _ => None,
        },
    }
}

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

#[cfg(test)]
mod tests {
    use super::*;
    use axum::{body::Body, http::Request, routing::get, Router};
    use tower::ServiceExt;

    fn test_auth_state() -> AuthState {
        let settings = crate::config::Settings::from_env().unwrap();
        AuthState {
            pool: None,
            settings,
        }
    }

    fn test_router() -> Router {
        let state = test_auth_state();
        Router::new()
            .route(
                "/api/v1/admin/analytics/render-performance",
                get(get_render_performance),
            )
            .with_state(state)
    }

    #[tokio::test]
    async fn returns_401_without_token() {
        let app = test_router();
        let resp = app
            .oneshot(
                Request::builder()
                    .uri("/api/v1/admin/analytics/render-performance")
                    .body(Body::empty())
                    .unwrap(),
            )
            .await
            .unwrap();
        assert_eq!(resp.status(), StatusCode::UNAUTHORIZED);
    }

    #[tokio::test]
    async fn returns_403_for_non_admin() {
        let state = test_auth_state();
        let token = crate::auth::issue_access_token(
            "00000000-0000-0000-0000-000000000001",
            "user",
            &state.settings.jwt_secret_key,
            60,
            &state.settings.jwt_issuer,
            &state.settings.jwt_audience,
        )
        .unwrap();
        let app = test_router();
        let resp = app
            .oneshot(
                Request::builder()
                    .uri("/api/v1/admin/analytics/render-performance")
                    .header("Authorization", format!("Bearer {}", token))
                    .body(Body::empty())
                    .unwrap(),
            )
            .await
            .unwrap();
        assert_eq!(resp.status(), StatusCode::FORBIDDEN);
    }

    #[tokio::test]
    async fn returns_503_for_admin_without_pool() {
        let state = test_auth_state();
        let token = crate::auth::issue_access_token(
            "00000000-0000-0000-0000-000000000001",
            "admin",
            &state.settings.jwt_secret_key,
            60,
            &state.settings.jwt_issuer,
            &state.settings.jwt_audience,
        )
        .unwrap();
        let app = test_router();
        let resp = app
            .oneshot(
                Request::builder()
                    .uri("/api/v1/admin/analytics/render-performance")
                    .header("Authorization", format!("Bearer {}", token))
                    .body(Body::empty())
                    .unwrap(),
            )
            .await
            .unwrap();
        assert_eq!(resp.status(), StatusCode::SERVICE_UNAVAILABLE);
    }

    #[test]
    fn speedup_compute_basic() {
        // 2k p50 = 1000ms, 512 p50 = 540ms → (1000-540)/1000 = 46.0%
        let buckets = vec![
            RenderPerfByLod {
                lod_label: "2k".to_string(),
                sample_count: 10,
                avg_file_size_bytes: None,
                ttf_ms: Percentiles {
                    p50: Some(1000.0),
                    p95: None,
                    p99: None,
                },
                ttfi_ms: Percentiles::default(),
                avg_fps: Percentiles::default(),
            },
            RenderPerfByLod {
                lod_label: "512".to_string(),
                sample_count: 10,
                avg_file_size_bytes: None,
                ttf_ms: Percentiles {
                    p50: Some(540.0),
                    p95: None,
                    p99: None,
                },
                ttfi_ms: Percentiles::default(),
                avg_fps: Percentiles::default(),
            },
        ];
        let s = compute_speedup_vs_2k(&buckets);
        assert_eq!(s.k512_vs_2k_ttf_pct, Some(46.0));
        assert_eq!(s.k1k_vs_2k_ttf_pct, None);
    }

    #[test]
    fn speedup_handles_missing_baseline() {
        let buckets = vec![RenderPerfByLod {
            lod_label: "512".to_string(),
            sample_count: 1,
            avg_file_size_bytes: None,
            ttf_ms: Percentiles {
                p50: Some(100.0),
                p95: None,
                p99: None,
            },
            ttfi_ms: Percentiles::default(),
            avg_fps: Percentiles::default(),
        }];
        let s = compute_speedup_vs_2k(&buckets);
        assert!(s.k512_vs_2k_ttf_pct.is_none());
        assert!(s.k1k_vs_2k_ttf_pct.is_none());
    }
}
