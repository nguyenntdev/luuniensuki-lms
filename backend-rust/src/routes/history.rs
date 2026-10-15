//! Public history endpoints (/api/v1/history/*).

use axum::{
    extract::{Path, Query, State},
    http::StatusCode,
    response::IntoResponse,
    Json,
};
use serde::Deserialize;
use uuid::Uuid;

use crate::error::AppError;
use crate::models::history::{
    ClaimListResponse, EntityListResponse, SearchHistoryResponse, SourceListResponse,
};
use crate::routes::auth::AuthState;
use crate::routes::route_helpers::require_pool;
use crate::services::history_service;

// ---------------------------------------------------------------------------
// Query Parameters
// ---------------------------------------------------------------------------

#[derive(Debug, Deserialize)]
pub struct ListEntitiesQuery {
    pub entity_type: Option<String>,
    pub publication_status: Option<String>,
    pub search: Option<String>,
    pub offset: Option<i64>,
    pub limit: Option<i64>,
}

#[derive(Debug, Deserialize)]
pub struct ListClaimsQuery {
    pub verification_status: Option<String>,
    pub claim_type: Option<String>,
    pub offset: Option<i64>,
    pub limit: Option<i64>,
}

#[derive(Debug, Deserialize)]
pub struct ListRelationsQuery {
    pub offset: Option<i64>,
    pub limit: Option<i64>,
}

#[derive(Debug, Deserialize)]
pub struct ListSourcesQuery {
    pub source_type: Option<String>,
    pub search: Option<String>,
    pub query: Option<String>,
    pub offset: Option<i64>,
    pub limit: Option<i64>,
}

#[derive(Debug, Deserialize)]
pub struct SearchHistoryQuery {
    pub q: Option<String>,
    pub query: Option<String>,
    pub types: Option<String>,
    pub limit: Option<i64>,
}

// ---------------------------------------------------------------------------
// Route Handlers
// ---------------------------------------------------------------------------

/// GET /api/v1/history/entities
pub async fn list_entities(
    State(state): State<AuthState>,
    Query(q): Query<ListEntitiesQuery>,
) -> Result<impl IntoResponse, AppError> {
    let pool = require_pool(&state.pool)?;
    let limit = q.limit.unwrap_or(50).clamp(1, 200);
    let offset = q.offset.unwrap_or(0).max(0);

    let (items, total) =
        history_service::list_entities(pool, q.entity_type.as_deref(), limit, offset).await?;

    Ok(Json(EntityListResponse {
        items,
        total,
        offset,
        limit,
    }))
}

/// GET /api/v1/history/entities/:id
pub async fn get_entity_by_id(
    State(state): State<AuthState>,
    Path(id): Path<Uuid>,
) -> Result<impl IntoResponse, AppError> {
    let pool = require_pool(&state.pool)?;
    let entity = history_service::get_entity_by_id(pool, id)
        .await?
        .ok_or_else(|| AppError::Domain {
            status: StatusCode::NOT_FOUND,
            code: "HISTORY_ENTITY_NOT_FOUND".to_string(),
            message: "Historical entity not found".to_string(),
            details: serde_json::json!({}),
        })?;

    Ok(Json(entity))
}

/// GET /api/v1/history/entities/by-slug/:slug
pub async fn get_entity_by_slug(
    State(state): State<AuthState>,
    Path(slug): Path<String>,
) -> Result<impl IntoResponse, AppError> {
    let pool = require_pool(&state.pool)?;
    let entity = history_service::get_entity_by_slug(pool, &slug)
        .await?
        .ok_or_else(|| AppError::Domain {
            status: StatusCode::NOT_FOUND,
            code: "HISTORY_ENTITY_NOT_FOUND".to_string(),
            message: "Historical entity not found".to_string(),
            details: serde_json::json!({}),
        })?;

    Ok(Json(entity))
}

/// GET /api/v1/history/entities/:id/claims
pub async fn list_entity_claims(
    State(state): State<AuthState>,
    Path(id): Path<Uuid>,
    Query(q): Query<ListClaimsQuery>,
) -> Result<impl IntoResponse, AppError> {
    let pool = require_pool(&state.pool)?;
    let limit = q.limit.unwrap_or(50).clamp(1, 200);
    let offset = q.offset.unwrap_or(0).max(0);

    let claims = history_service::get_entity_claims(pool, id).await?;
    let total = claims.len() as i64;
    let paginated = claims
        .into_iter()
        .skip(offset as usize)
        .take(limit as usize)
        .collect();

    Ok(Json(ClaimListResponse {
        items: paginated,
        total,
        offset,
        limit,
    }))
}

/// GET /api/v1/history/entities/:id/relations
pub async fn list_entity_relations(
    State(state): State<AuthState>,
    Path(id): Path<Uuid>,
    Query(_q): Query<ListRelationsQuery>,
) -> Result<impl IntoResponse, AppError> {
    let pool = require_pool(&state.pool)?;
    let _entity = history_service::get_entity_by_id(pool, id)
        .await?
        .ok_or_else(|| AppError::Domain {
            status: StatusCode::NOT_FOUND,
            code: "HISTORY_ENTITY_NOT_FOUND".to_string(),
            message: "Historical entity not found".to_string(),
            details: serde_json::json!({}),
        })?;

    let relations = history_service::get_entity_relations(pool, id).await?;
    Ok(Json(relations))
}

/// GET /api/v1/history/urns
pub async fn list_urns(State(state): State<AuthState>) -> Result<impl IntoResponse, AppError> {
    let pool = require_pool(&state.pool)?;
    let urns = history_service::get_urns(pool).await?;
    let total = urns.len();
    Ok(Json(serde_json::json!({
        "items": urns,
        "total": total,
    })))
}

/// GET /api/v1/history/urns/:slug
pub async fn get_urn_by_slug(
    State(state): State<AuthState>,
    Path(slug): Path<String>,
) -> Result<impl IntoResponse, AppError> {
    let pool = require_pool(&state.pool)?;
    let entity = history_service::get_entity_by_slug(pool, &slug).await?;
    match entity {
        Some(e) if e.entity_type == "urn" => Ok(Json(e)),
        _ => Err(AppError::Domain {
            status: StatusCode::NOT_FOUND,
            code: "HISTORY_ENTITY_NOT_FOUND".to_string(),
            message: "Urn not found".to_string(),
            details: serde_json::json!({}),
        }),
    }
}

/// GET /api/v1/history/reliefs
pub async fn list_reliefs(
    State(state): State<AuthState>,
    Query(q): Query<ListEntitiesQuery>,
) -> Result<impl IntoResponse, AppError> {
    let pool = require_pool(&state.pool)?;
    let limit = q.limit.unwrap_or(50).clamp(1, 200);
    let offset = q.offset.unwrap_or(0).max(0);

    let (items, total) =
        history_service::list_entities(pool, Some("relief"), limit, offset).await?;

    Ok(Json(EntityListResponse {
        items,
        total,
        offset,
        limit,
    }))
}

/// GET /api/v1/history/sources
pub async fn list_sources(
    State(state): State<AuthState>,
    Query(q): Query<ListSourcesQuery>,
) -> Result<impl IntoResponse, AppError> {
    let pool = require_pool(&state.pool)?;
    let limit = q.limit.unwrap_or(50).clamp(1, 200);
    let offset = q.offset.unwrap_or(0).max(0);
    let query_term = q.query.as_deref().or(q.search.as_deref());

    let (items, total) = history_service::list_sources_paginated(
        pool,
        query_term,
        q.source_type.as_deref(),
        limit,
        offset,
    )
    .await?;

    Ok(Json(SourceListResponse {
        items,
        total,
        offset,
        limit,
    }))
}

/// GET /api/v1/history/sources/:id
pub async fn get_source_by_id(
    State(state): State<AuthState>,
    Path(id): Path<Uuid>,
) -> Result<impl IntoResponse, AppError> {
    let pool = require_pool(&state.pool)?;
    let source = history_service::get_source_by_id(pool, id)
        .await?
        .ok_or_else(|| AppError::Domain {
            status: StatusCode::NOT_FOUND,
            code: "HISTORY_SOURCE_NOT_FOUND".to_string(),
            message: "Historical source not found".to_string(),
            details: serde_json::json!({}),
        })?;

    Ok(Json(source))
}

/// GET /api/v1/history/search
pub async fn search_history(
    State(state): State<AuthState>,
    Query(q): Query<SearchHistoryQuery>,
) -> Result<impl IntoResponse, AppError> {
    let pool = require_pool(&state.pool)?;
    let search_term = q.q.as_deref().or(q.query.as_deref()).unwrap_or("");
    let limit = q.limit.unwrap_or(20).clamp(1, 50);

    let items =
        history_service::search_history(pool, search_term, q.types.as_deref(), limit).await?;
    let total = items.len();

    Ok(Json(SearchHistoryResponse {
        query: search_term.to_string(),
        items,
        total,
    }))
}
