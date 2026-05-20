//! Heritage Time-Lapse routes.
//!
//! Spec: `.kiro/specs/heritage-time-lapse/`

use axum::{
    extract::{Query, State},
    http::{header, HeaderMap, HeaderValue, StatusCode},
    response::{IntoResponse, Response},
    Json,
};

use crate::error::AppError;
use crate::models::timeline::{
    CompareQuery, CreateEraRequest, CreateEventRequest, MotifsByEraQuery, TimelineEventsQuery,
};
use crate::routes::auth::AuthState;
use crate::routes::route_helpers::{authenticate, require_admin, require_pool};
use crate::services::timeline_service;

// ---------------------------------------------------------------------------
// Public routes
// ---------------------------------------------------------------------------

pub async fn get_timeline_events(
    State(state): State<AuthState>,
    Query(q): Query<TimelineEventsQuery>,
) -> Result<Response, AppError> {
    let pool = require_pool(&state.pool)?;
    let resp = timeline_service::list_events(pool, q.from, q.to).await?;
    let mut response = Json(resp).into_response();
    response.headers_mut().insert(
        header::CACHE_CONTROL,
        HeaderValue::from_static("public, max-age=300"),
    );
    Ok(response)
}

pub async fn get_timeline_motifs(
    State(state): State<AuthState>,
    Query(q): Query<MotifsByEraQuery>,
) -> Result<impl IntoResponse, AppError> {
    let pool = require_pool(&state.pool)?;
    let era = q.era.ok_or_else(|| AppError::Validation {
        details: serde_json::json!({"era": "Query parameter 'era' is required"}),
    })?;
    let resp = timeline_service::list_motifs_by_era(pool, &era).await?;
    Ok(Json(resp))
}

pub async fn compare_motifs(
    State(state): State<AuthState>,
    Query(q): Query<CompareQuery>,
    headers: HeaderMap,
) -> Result<impl IntoResponse, AppError> {
    let pool = require_pool(&state.pool)?;
    let _user_id = authenticate(&headers, &state.settings)?;
    let resp = timeline_service::compare_motifs(pool, &q.ids).await?;
    Ok(Json(resp))
}

// ---------------------------------------------------------------------------
// Admin routes
// ---------------------------------------------------------------------------

pub async fn create_era(
    State(state): State<AuthState>,
    headers: HeaderMap,
    Json(payload): Json<CreateEraRequest>,
) -> Result<impl IntoResponse, AppError> {
    let pool = require_pool(&state.pool)?;
    let _admin = require_admin(&headers, &state.settings)?;
    let row = timeline_service::create_era(pool, &payload).await?;
    Ok((StatusCode::CREATED, Json(row)))
}

pub async fn create_event(
    State(state): State<AuthState>,
    headers: HeaderMap,
    Json(payload): Json<CreateEventRequest>,
) -> Result<impl IntoResponse, AppError> {
    let pool = require_pool(&state.pool)?;
    let _admin = require_admin(&headers, &state.settings)?;
    let row = timeline_service::create_event(pool, &payload).await?;
    Ok((StatusCode::CREATED, Json(serde_json::json!({
        "id": row.id,
        "slug": row.slug,
        "name_vi": row.name_vi,
        "name_en": row.name_en,
        "occurred_on": row.occurred_on,
        "importance": row.importance,
        "era_id": row.era_id,
        "motif_id": row.motif_id,
        "urn_id": row.urn_id,
    }))))
}

pub async fn get_timeline_stats(
    State(state): State<AuthState>,
    headers: HeaderMap,
) -> Result<impl IntoResponse, AppError> {
    let pool = require_pool(&state.pool)?;
    let _admin = require_admin(&headers, &state.settings)?;
    let resp = timeline_service::get_timeline_stats(pool).await?;
    Ok(Json(resp))
}
