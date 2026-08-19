//! History service logic for history-first domain models.

use sqlx::PgPool;
use uuid::Uuid;

use crate::error::AppError;
use crate::models::history::{
    EntityRelationRow, HistoricalClaimRow, HistoricalEntityRow, HistoricalSourceRow,
    SearchResultItem, UrnSummaryItem,
};

/// Fetch a historical entity by slug.
pub async fn get_entity_by_slug(
    pool: &PgPool,
    slug: &str,
) -> Result<Option<HistoricalEntityRow>, AppError> {
    let row = sqlx::query_as::<_, HistoricalEntityRow>(
        r#"
        SELECT id, entity_type, slug, name_vi, name_en, name_han_nom, alternative_names,
               summary_vi, summary_en, start_date, end_date, date_precision, latitude, longitude,
               geo_precision, thumbnail_asset_id, publication_status, content_version,
               created_by, updated_by, created_at, updated_at, deleted_at
        FROM historical_entities
        WHERE slug = $1 AND deleted_at IS NULL
        "#,
    )
    .bind(slug)
    .fetch_optional(pool)
    .await
    .map_err(|e| AppError::Internal(e.into()))?;

    Ok(row)
}

/// Fetch a historical entity by ID.
pub async fn get_entity_by_id(
    pool: &PgPool,
    id: Uuid,
) -> Result<Option<HistoricalEntityRow>, AppError> {
    let row = sqlx::query_as::<_, HistoricalEntityRow>(
        r#"
        SELECT id, entity_type, slug, name_vi, name_en, name_han_nom, alternative_names,
               summary_vi, summary_en, start_date, end_date, date_precision, latitude, longitude,
               geo_precision, thumbnail_asset_id, publication_status, content_version,
               created_by, updated_by, created_at, updated_at, deleted_at
        FROM historical_entities
        WHERE id = $1 AND deleted_at IS NULL
        "#,
    )
    .bind(id)
    .fetch_optional(pool)
    .await
    .map_err(|e| AppError::Internal(e.into()))?;

    Ok(row)
}

/// List historical entities with optional type filtering and pagination.
pub async fn list_entities(
    pool: &PgPool,
    entity_type: Option<&str>,
    limit: i64,
    offset: i64,
) -> Result<(Vec<HistoricalEntityRow>, i64), AppError> {
    let (rows, total) = match entity_type {
        Some(etype) if !etype.trim().is_empty() => {
            let count: (i64,) = sqlx::query_as(
                "SELECT COUNT(*) FROM historical_entities WHERE entity_type = $1 AND deleted_at IS NULL",
            )
            .bind(etype)
            .fetch_one(pool)
            .await
            .map_err(|e| AppError::Internal(e.into()))?;

            let items = sqlx::query_as::<_, HistoricalEntityRow>(
                r#"
                SELECT id, entity_type, slug, name_vi, name_en, name_han_nom, alternative_names,
                       summary_vi, summary_en, start_date, end_date, date_precision, latitude, longitude,
                       geo_precision, thumbnail_asset_id, publication_status, content_version,
                       created_by, updated_by, created_at, updated_at, deleted_at
                FROM historical_entities
                WHERE entity_type = $1 AND deleted_at IS NULL
                ORDER BY created_at DESC
                LIMIT $2 OFFSET $3
                "#,
            )
            .bind(etype)
            .bind(limit)
            .bind(offset)
            .fetch_all(pool)
            .await
            .map_err(|e| AppError::Internal(e.into()))?;

            (items, count.0)
        }
        _ => {
            let count: (i64,) = sqlx::query_as(
                "SELECT COUNT(*) FROM historical_entities WHERE deleted_at IS NULL",
            )
            .fetch_one(pool)
            .await
            .map_err(|e| AppError::Internal(e.into()))?;

            let items = sqlx::query_as::<_, HistoricalEntityRow>(
                r#"
                SELECT id, entity_type, slug, name_vi, name_en, name_han_nom, alternative_names,
                       summary_vi, summary_en, start_date, end_date, date_precision, latitude, longitude,
                       geo_precision, thumbnail_asset_id, publication_status, content_version,
                       created_by, updated_by, created_at, updated_at, deleted_at
                FROM historical_entities
                WHERE deleted_at IS NULL
                ORDER BY created_at DESC
                LIMIT $1 OFFSET $2
                "#,
            )
            .bind(limit)
            .bind(offset)
            .fetch_all(pool)
            .await
            .map_err(|e| AppError::Internal(e.into()))?;

            (items, count.0)
        }
    };

    Ok((rows, total))
}

/// Fetch claims associated with a historical entity.
pub async fn get_entity_claims(
    pool: &PgPool,
    entity_id: Uuid,
) -> Result<Vec<HistoricalClaimRow>, AppError> {
    let rows = sqlx::query_as::<_, HistoricalClaimRow>(
        r#"
        SELECT id, entity_id, claim_key, claim_type, statement_vi, statement_en, valid_from, valid_to,
               date_precision, confidence, verification_status, origin, risk_level, review_notes,
               created_by, reviewed_by, reviewed_at, verified_by, verified_at, created_at, updated_at,
               supersedes_claim_id, is_current
        FROM historical_claims
        WHERE entity_id = $1
        ORDER BY created_at DESC
        "#,
    )
    .bind(entity_id)
    .fetch_all(pool)
    .await
    .map_err(|e| AppError::Internal(e.into()))?;

    Ok(rows)
}

/// Fetch relations where the given entity is subject or object.
pub async fn get_entity_relations(
    pool: &PgPool,
    entity_id: Uuid,
) -> Result<Vec<EntityRelationRow>, AppError> {
    let rows = sqlx::query_as::<_, EntityRelationRow>(
        r#"
        SELECT id, subject_entity_id, predicate, object_entity_id, claim_id, source_id,
               confidence, verification_status, valid_from, valid_to, created_by, created_at, updated_at
        FROM historical_entity_relations
        WHERE subject_entity_id = $1 OR object_entity_id = $1
        ORDER BY created_at DESC
        "#,
    )
    .bind(entity_id)
    .fetch_all(pool)
    .await
    .map_err(|e| AppError::Internal(e.into()))?;

    Ok(rows)
}

/// List historical sources by query string.
pub async fn list_sources(
    pool: &PgPool,
    query: Option<&str>,
) -> Result<Vec<HistoricalSourceRow>, AppError> {
    let (items, _) = list_sources_paginated(pool, query, None, 50, 0).await?;
    Ok(items)
}

/// List historical sources with optional query, source_type, limit, and offset.
pub async fn list_sources_paginated(
    pool: &PgPool,
    query: Option<&str>,
    source_type: Option<&str>,
    limit: i64,
    offset: i64,
) -> Result<(Vec<HistoricalSourceRow>, i64), AppError> {
    let q_pattern = query.filter(|q| !q.trim().is_empty()).map(|q| format!("%{}%", q));
    let st_filter = source_type.filter(|s| !s.trim().is_empty());

    let (rows, total) = match (q_pattern, st_filter) {
        (Some(pattern), Some(st)) => {
            let count: (i64,) = sqlx::query_as(
                "SELECT COUNT(*) FROM historical_sources WHERE source_type = $1 AND (title ILIKE $2 OR author_text ILIKE $2 OR publisher ILIKE $2)",
            )
            .bind(st)
            .bind(&pattern)
            .fetch_one(pool)
            .await
            .map_err(|e| AppError::Internal(e.into()))?;

            let items = sqlx::query_as::<_, HistoricalSourceRow>(
                r#"
                SELECT id, source_type, title, subtitle, author_text, editor_text, publisher, publication_year,
                       publication_date, edition, volume, issue, pages, isbn, issn, doi, url, archive_url,
                       repository_identifier, language, citation_text, rights_status, license, attribution_text,
                       public_display_allowed, derivative_allowed, verification_status, accessed_at, created_by,
                       created_at, updated_at
                FROM historical_sources
                WHERE source_type = $1 AND (title ILIKE $2 OR author_text ILIKE $2 OR publisher ILIKE $2)
                ORDER BY created_at DESC
                LIMIT $3 OFFSET $4
                "#,
            )
            .bind(st)
            .bind(&pattern)
            .bind(limit)
            .bind(offset)
            .fetch_all(pool)
            .await
            .map_err(|e| AppError::Internal(e.into()))?;

            (items, count.0)
        }
        (Some(pattern), None) => {
            let count: (i64,) = sqlx::query_as(
                "SELECT COUNT(*) FROM historical_sources WHERE (title ILIKE $1 OR author_text ILIKE $1 OR publisher ILIKE $1)",
            )
            .bind(&pattern)
            .fetch_one(pool)
            .await
            .map_err(|e| AppError::Internal(e.into()))?;

            let items = sqlx::query_as::<_, HistoricalSourceRow>(
                r#"
                SELECT id, source_type, title, subtitle, author_text, editor_text, publisher, publication_year,
                       publication_date, edition, volume, issue, pages, isbn, issn, doi, url, archive_url,
                       repository_identifier, language, citation_text, rights_status, license, attribution_text,
                       public_display_allowed, derivative_allowed, verification_status, accessed_at, created_by,
                       created_at, updated_at
                FROM historical_sources
                WHERE (title ILIKE $1 OR author_text ILIKE $1 OR publisher ILIKE $1)
                ORDER BY created_at DESC
                LIMIT $2 OFFSET $3
                "#,
            )
            .bind(&pattern)
            .bind(limit)
            .bind(offset)
            .fetch_all(pool)
            .await
            .map_err(|e| AppError::Internal(e.into()))?;

            (items, count.0)
        }
        (None, Some(st)) => {
            let count: (i64,) = sqlx::query_as(
                "SELECT COUNT(*) FROM historical_sources WHERE source_type = $1",
            )
            .bind(st)
            .fetch_one(pool)
            .await
            .map_err(|e| AppError::Internal(e.into()))?;

            let items = sqlx::query_as::<_, HistoricalSourceRow>(
                r#"
                SELECT id, source_type, title, subtitle, author_text, editor_text, publisher, publication_year,
                       publication_date, edition, volume, issue, pages, isbn, issn, doi, url, archive_url,
                       repository_identifier, language, citation_text, rights_status, license, attribution_text,
                       public_display_allowed, derivative_allowed, verification_status, accessed_at, created_by,
                       created_at, updated_at
                FROM historical_sources
                WHERE source_type = $1
                ORDER BY created_at DESC
                LIMIT $2 OFFSET $3
                "#,
            )
            .bind(st)
            .bind(limit)
            .bind(offset)
            .fetch_all(pool)
            .await
            .map_err(|e| AppError::Internal(e.into()))?;

            (items, count.0)
        }
        (None, None) => {
            let count: (i64,) = sqlx::query_as("SELECT COUNT(*) FROM historical_sources")
                .fetch_one(pool)
                .await
                .map_err(|e| AppError::Internal(e.into()))?;

            let items = sqlx::query_as::<_, HistoricalSourceRow>(
                r#"
                SELECT id, source_type, title, subtitle, author_text, editor_text, publisher, publication_year,
                       publication_date, edition, volume, issue, pages, isbn, issn, doi, url, archive_url,
                       repository_identifier, language, citation_text, rights_status, license, attribution_text,
                       public_display_allowed, derivative_allowed, verification_status, accessed_at, created_by,
                       created_at, updated_at
                FROM historical_sources
                ORDER BY created_at DESC
                LIMIT $1 OFFSET $2
                "#,
            )
            .bind(limit)
            .bind(offset)
            .fetch_all(pool)
            .await
            .map_err(|e| AppError::Internal(e.into()))?;

            (items, count.0)
        }
    };

    Ok((rows, total))
}

/// Fetch a historical source by ID.
pub async fn get_source_by_id(
    pool: &PgPool,
    id: Uuid,
) -> Result<Option<HistoricalSourceRow>, AppError> {
    let row = sqlx::query_as::<_, HistoricalSourceRow>(
        r#"
        SELECT id, source_type, title, subtitle, author_text, editor_text, publisher, publication_year,
               publication_date, edition, volume, issue, pages, isbn, issn, doi, url, archive_url,
               repository_identifier, language, citation_text, rights_status, license, attribution_text,
               public_display_allowed, derivative_allowed, verification_status, accessed_at, created_by,
               created_at, updated_at
        FROM historical_sources
        WHERE id = $1
        "#,
    )
    .bind(id)
    .fetch_optional(pool)
    .await
    .map_err(|e| AppError::Internal(e.into()))?;

    Ok(row)
}

/// Search historical entities by query term, optional comma-separated types, and limit.
pub async fn search_history(
    pool: &PgPool,
    query: &str,
    types: Option<&str>,
    limit: i64,
) -> Result<Vec<SearchResultItem>, AppError> {
    let pattern = format!("%{}%", query);
    let rows = match types {
        Some(t_str) if !t_str.trim().is_empty() => {
            let type_list: Vec<String> = t_str.split(',').map(|s| s.trim().to_string()).collect();
            sqlx::query_as::<_, HistoricalEntityRow>(
                r#"
                SELECT id, entity_type, slug, name_vi, name_en, name_han_nom, alternative_names,
                       summary_vi, summary_en, start_date, end_date, date_precision, latitude, longitude,
                       geo_precision, thumbnail_asset_id, publication_status, content_version,
                       created_by, updated_by, created_at, updated_at, deleted_at
                FROM historical_entities
                WHERE deleted_at IS NULL
                  AND (name_vi ILIKE $1 OR name_en ILIKE $1 OR slug ILIKE $1 OR summary_vi ILIKE $1)
                  AND entity_type = ANY($2)
                ORDER BY name_vi ASC
                LIMIT $3
                "#,
            )
            .bind(&pattern)
            .bind(&type_list)
            .bind(limit)
            .fetch_all(pool)
            .await
            .map_err(|e| AppError::Internal(e.into()))?
        }
        _ => {
            sqlx::query_as::<_, HistoricalEntityRow>(
                r#"
                SELECT id, entity_type, slug, name_vi, name_en, name_han_nom, alternative_names,
                       summary_vi, summary_en, start_date, end_date, date_precision, latitude, longitude,
                       geo_precision, thumbnail_asset_id, publication_status, content_version,
                       created_by, updated_by, created_at, updated_at, deleted_at
                FROM historical_entities
                WHERE deleted_at IS NULL
                  AND (name_vi ILIKE $1 OR name_en ILIKE $1 OR slug ILIKE $1 OR summary_vi ILIKE $1)
                ORDER BY name_vi ASC
                LIMIT $2
                "#,
            )
            .bind(&pattern)
            .bind(limit)
            .fetch_all(pool)
            .await
            .map_err(|e| AppError::Internal(e.into()))?
        }
    };

    let items = rows
        .into_iter()
        .map(|e| SearchResultItem {
            id: e.id,
            entity_type: e.entity_type,
            slug: e.slug,
            name_vi: e.name_vi,
            name_en: e.name_en,
            summary_vi: e.summary_vi,
            publication_status: e.publication_status,
            matched_on: Some("name_or_summary".to_string()),
        })
        .collect();

    Ok(items)
}

/// Fetch all urn entities with their associated relief count.
pub async fn get_urns(pool: &PgPool) -> Result<Vec<UrnSummaryItem>, AppError> {
    let urns = sqlx::query_as::<_, HistoricalEntityRow>(
        r#"
        SELECT id, entity_type, slug, name_vi, name_en, name_han_nom, alternative_names,
               summary_vi, summary_en, start_date, end_date, date_precision, latitude, longitude,
               geo_precision, thumbnail_asset_id, publication_status, content_version,
               created_by, updated_by, created_at, updated_at, deleted_at
        FROM historical_entities
        WHERE entity_type = 'urn' AND deleted_at IS NULL
        ORDER BY slug ASC
        "#,
    )
    .fetch_all(pool)
    .await
    .map_err(|e| AppError::Internal(e.into()))?;

    let mut result = Vec::with_capacity(urns.len());
    for urn in urns {
        let count: (i64,) = sqlx::query_as(
            r#"
            SELECT COUNT(*)
            FROM historical_entity_relations
            WHERE predicate = 'located_on' AND object_entity_id = $1
            "#,
        )
        .bind(urn.id)
        .fetch_one(pool)
        .await
        .map_err(|e| AppError::Internal(e.into()))?;

        result.push(UrnSummaryItem {
            id: urn.id,
            slug: urn.slug,
            name_vi: urn.name_vi,
            name_en: urn.name_en,
            summary_vi: urn.summary_vi,
            publication_status: urn.publication_status,
            relief_count: count.0,
        });
    }

    Ok(result)
}
