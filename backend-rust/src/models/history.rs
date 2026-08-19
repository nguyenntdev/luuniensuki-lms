//! History-First domain models (Phase 1).
//!
//! Entity / claim / source / relation / geography / asset / audit log models.

use chrono::{DateTime, NaiveDate, Utc};
use serde::{Deserialize, Serialize};
use uuid::Uuid;

// ---------------------------------------------------------------------------
// DB Row Structs
// ---------------------------------------------------------------------------

#[derive(Debug, Clone, sqlx::FromRow, Serialize, Deserialize)]
pub struct HistoricalEntityRow {
    pub id: Uuid,
    pub entity_type: String,
    pub slug: String,
    pub name_vi: String,
    pub name_en: Option<String>,
    pub name_han_nom: Option<String>,
    pub alternative_names: serde_json::Value,
    pub summary_vi: Option<String>,
    pub summary_en: Option<String>,
    pub start_date: Option<NaiveDate>,
    pub end_date: Option<NaiveDate>,
    pub date_precision: Option<String>,
    pub latitude: Option<f64>,
    pub longitude: Option<f64>,
    pub geo_precision: Option<String>,
    pub thumbnail_asset_id: Option<Uuid>,
    pub publication_status: String,
    pub content_version: i32,
    pub created_by: Option<Uuid>,
    pub updated_by: Option<Uuid>,
    pub created_at: DateTime<Utc>,
    pub updated_at: DateTime<Utc>,
    pub deleted_at: Option<DateTime<Utc>>,
}

#[derive(Debug, Clone, sqlx::FromRow, Serialize, Deserialize)]
pub struct HistoricalClaimRow {
    pub id: Uuid,
    pub entity_id: Uuid,
    pub claim_key: Option<String>,
    pub claim_type: String,
    pub statement_vi: String,
    pub statement_en: Option<String>,
    pub valid_from: Option<NaiveDate>,
    pub valid_to: Option<NaiveDate>,
    pub date_precision: Option<String>,
    pub confidence: String,
    pub verification_status: String,
    pub origin: String,
    pub risk_level: String,
    pub review_notes: Option<String>,
    pub created_by: Option<Uuid>,
    pub reviewed_by: Option<Uuid>,
    pub reviewed_at: Option<DateTime<Utc>>,
    pub verified_by: Option<Uuid>,
    pub verified_at: Option<DateTime<Utc>>,
    pub created_at: DateTime<Utc>,
    pub updated_at: DateTime<Utc>,
    pub supersedes_claim_id: Option<Uuid>,
    pub is_current: bool,
}

#[derive(Debug, Clone, sqlx::FromRow, Serialize, Deserialize)]
pub struct HistoricalSourceRow {
    pub id: Uuid,
    pub source_type: String,
    pub title: String,
    pub subtitle: Option<String>,
    pub author_text: Option<String>,
    pub editor_text: Option<String>,
    pub publisher: Option<String>,
    pub publication_year: Option<i32>,
    pub publication_date: Option<NaiveDate>,
    pub edition: Option<String>,
    pub volume: Option<String>,
    pub issue: Option<String>,
    pub pages: Option<String>,
    pub isbn: Option<String>,
    pub issn: Option<String>,
    pub doi: Option<String>,
    pub url: Option<String>,
    pub archive_url: Option<String>,
    pub repository_identifier: Option<String>,
    pub language: Option<String>,
    pub citation_text: Option<String>,
    pub rights_status: Option<String>,
    pub license: Option<String>,
    pub attribution_text: Option<String>,
    pub public_display_allowed: Option<bool>,
    pub derivative_allowed: Option<bool>,
    pub verification_status: String,
    pub accessed_at: Option<DateTime<Utc>>,
    pub created_by: Option<Uuid>,
    pub created_at: DateTime<Utc>,
    pub updated_at: DateTime<Utc>,
}

#[derive(Debug, Clone, sqlx::FromRow, Serialize, Deserialize)]
pub struct ClaimSourceRow {
    pub claim_id: Uuid,
    pub source_id: Uuid,
    pub support_type: String,
    pub locator_type: Option<String>,
    pub page_start: Option<String>,
    pub page_end: Option<String>,
    pub chapter: Option<String>,
    pub section: Option<String>,
    pub figure: Option<String>,
    pub folio: Option<String>,
    pub inscription_location: Option<String>,
    pub quotation_excerpt: Option<String>,
    pub quotation_language: Option<String>,
    pub editor_note: Option<String>,
    pub created_by: Option<Uuid>,
    pub created_at: DateTime<Utc>,
}

pub type HistoricalClaimSourceRow = ClaimSourceRow;

#[derive(Debug, Clone, sqlx::FromRow, Serialize, Deserialize)]
pub struct EntityRelationRow {
    pub id: Uuid,
    pub subject_entity_id: Uuid,
    pub predicate: String,
    pub object_entity_id: Uuid,
    pub claim_id: Option<Uuid>,
    pub source_id: Option<Uuid>,
    pub confidence: String,
    pub verification_status: String,
    pub valid_from: Option<NaiveDate>,
    pub valid_to: Option<NaiveDate>,
    pub created_by: Option<Uuid>,
    pub created_at: DateTime<Utc>,
    pub updated_at: DateTime<Utc>,
}

pub type HistoricalEntityRelationRow = EntityRelationRow;

#[derive(Debug, Clone, sqlx::FromRow, Serialize, Deserialize)]
pub struct GeographyRow {
    pub entity_id: Uuid,
    pub historical_name: Option<String>,
    pub modern_name: Option<String>,
    pub historical_geometry: Option<serde_json::Value>,
    pub modern_geometry: Option<serde_json::Value>,
    pub valid_from: Option<NaiveDate>,
    pub valid_to: Option<NaiveDate>,
    pub geo_precision: String,
    pub mapping_status: String,
    pub source_claim_id: Option<Uuid>,
    pub notes: Option<String>,
}

pub type HistoricalGeographyRow = GeographyRow;

#[derive(Debug, Clone, sqlx::FromRow, Serialize, Deserialize)]
pub struct HistoricalAssetRow {
    pub id: Uuid,
    pub asset_type: String,
    pub storage_url: String,
    pub thumbnail_url: Option<String>,
    pub mime_type: Option<String>,
    pub width: Option<i32>,
    pub height: Option<i32>,
    pub duration: Option<f64>,
    pub byte_size: Option<i64>,
    pub sha256: Option<String>,
    pub rights_status: Option<String>,
    pub license: Option<String>,
    pub attribution: Option<String>,
    pub source_origin: Option<String>,
    pub public_display_allowed: Option<bool>,
    pub derivative_allowed: Option<bool>,
    pub entity_id: Option<Uuid>,
    pub created_at: DateTime<Utc>,
}

#[derive(Debug, Clone, sqlx::FromRow, Serialize, Deserialize)]
pub struct AuditLogRow {
    pub id: i64,
    pub actor_id: Option<Uuid>,
    pub action: String,
    pub resource_type: String,
    pub resource_id: Option<Uuid>,
    pub before_json: Option<serde_json::Value>,
    pub after_json: Option<serde_json::Value>,
    pub reason: Option<String>,
    pub request_id: Option<String>,
    pub created_at: DateTime<Utc>,
}

pub type HistoricalContentAuditLogRow = AuditLogRow;

// ---------------------------------------------------------------------------
// Request DTOs
// ---------------------------------------------------------------------------

#[derive(Debug, Clone, Deserialize, Serialize)]
pub struct CreateEntityRequest {
    pub entity_type: String,
    pub slug: String,
    pub name_vi: String,
    pub name_en: Option<String>,
    pub name_han_nom: Option<String>,
    #[serde(default)]
    pub alternative_names: Vec<String>,
    pub summary_vi: Option<String>,
    pub summary_en: Option<String>,
    pub start_date: Option<NaiveDate>,
    pub end_date: Option<NaiveDate>,
    pub date_precision: Option<String>,
    pub latitude: Option<f64>,
    pub longitude: Option<f64>,
    pub geo_precision: Option<String>,
    #[serde(default = "default_publication_status")]
    pub publication_status: String,
    #[serde(default = "default_content_version")]
    pub content_version: i32,
}

fn default_publication_status() -> String {
    "draft".to_string()
}

fn default_content_version() -> i32 {
    1
}

#[derive(Debug, Clone, Deserialize, Serialize)]
pub struct UpdateEntityRequest {
    pub entity_type: Option<String>,
    pub slug: Option<String>,
    pub name_vi: Option<String>,
    pub name_en: Option<String>,
    pub name_han_nom: Option<String>,
    pub alternative_names: Option<Vec<String>>,
    pub summary_vi: Option<String>,
    pub summary_en: Option<String>,
    pub start_date: Option<NaiveDate>,
    pub end_date: Option<NaiveDate>,
    pub date_precision: Option<String>,
    pub latitude: Option<f64>,
    pub longitude: Option<f64>,
    pub geo_precision: Option<String>,
    pub publication_status: Option<String>,
}

#[derive(Debug, Clone, Deserialize, Serialize)]
pub struct CreateClaimRequest {
    pub entity_id: Uuid,
    pub claim_key: Option<String>,
    pub claim_type: String,
    pub statement_vi: String,
    pub statement_en: Option<String>,
    pub valid_from: Option<NaiveDate>,
    pub valid_to: Option<NaiveDate>,
    pub date_precision: Option<String>,
    #[serde(default = "default_unknown")]
    pub confidence: String,
    #[serde(default = "default_unreviewed")]
    pub verification_status: String,
    pub origin: String,
    #[serde(default = "default_normal")]
    pub risk_level: String,
    pub review_notes: Option<String>,
}

fn default_unknown() -> String {
    "unknown".to_string()
}

fn default_unreviewed() -> String {
    "unreviewed".to_string()
}

fn default_normal() -> String {
    "normal".to_string()
}

#[derive(Debug, Clone, Deserialize, Serialize)]
pub struct CreateSourceRequest {
    pub source_type: String,
    pub title: String,
    pub subtitle: Option<String>,
    pub author_text: Option<String>,
    pub editor_text: Option<String>,
    pub publisher: Option<String>,
    pub publication_year: Option<i32>,
    pub publication_date: Option<NaiveDate>,
    pub edition: Option<String>,
    pub volume: Option<String>,
    pub issue: Option<String>,
    pub pages: Option<String>,
    pub isbn: Option<String>,
    pub issn: Option<String>,
    pub doi: Option<String>,
    pub url: Option<String>,
    pub archive_url: Option<String>,
    pub repository_identifier: Option<String>,
    pub language: Option<String>,
    pub citation_text: Option<String>,
    pub rights_status: Option<String>,
    pub license: Option<String>,
    pub attribution_text: Option<String>,
    pub public_display_allowed: Option<bool>,
    pub derivative_allowed: Option<bool>,
    #[serde(default = "default_unreviewed")]
    pub verification_status: String,
}

#[derive(Debug, Clone, Deserialize, Serialize)]
pub struct BindSourceClaimRequest {
    pub source_id: Uuid,
    pub support_type: String,
    pub locator_type: Option<String>,
    pub page_start: Option<String>,
    pub page_end: Option<String>,
    pub chapter: Option<String>,
    pub section: Option<String>,
    pub figure: Option<String>,
    pub folio: Option<String>,
    pub inscription_location: Option<String>,
    pub quotation_excerpt: Option<String>,
    pub quotation_language: Option<String>,
    pub editor_note: Option<String>,
}

#[derive(Debug, Clone, Deserialize, Serialize)]
pub struct CreateRelationRequest {
    pub subject_entity_id: Uuid,
    pub predicate: String,
    pub object_entity_id: Uuid,
    pub claim_id: Option<Uuid>,
    pub source_id: Option<Uuid>,
    #[serde(default = "default_unknown")]
    pub confidence: String,
    #[serde(default = "default_unreviewed")]
    pub verification_status: String,
    pub valid_from: Option<NaiveDate>,
    pub valid_to: Option<NaiveDate>,
}

// ---------------------------------------------------------------------------
// Response DTOs
// ---------------------------------------------------------------------------

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct EntityDetailResponse {
    pub id: Uuid,
    pub entity_type: String,
    pub slug: String,
    pub name_vi: String,
    pub name_en: Option<String>,
    pub name_han_nom: Option<String>,
    pub alternative_names: serde_json::Value,
    pub summary_vi: Option<String>,
    pub summary_en: Option<String>,
    pub start_date: Option<NaiveDate>,
    pub end_date: Option<NaiveDate>,
    pub date_precision: Option<String>,
    pub latitude: Option<f64>,
    pub longitude: Option<f64>,
    pub geo_precision: Option<String>,
    pub publication_status: String,
    pub content_version: i32,
    pub created_at: DateTime<Utc>,
    pub updated_at: DateTime<Utc>,
    pub claims: Option<Vec<ClaimDetailResponse>>,
    pub relations: Option<Vec<EntityRelationRow>>,
    pub geography: Option<GeographyRow>,
}

impl From<HistoricalEntityRow> for EntityDetailResponse {
    fn from(row: HistoricalEntityRow) -> Self {
        Self {
            id: row.id,
            entity_type: row.entity_type,
            slug: row.slug,
            name_vi: row.name_vi,
            name_en: row.name_en,
            name_han_nom: row.name_han_nom,
            alternative_names: row.alternative_names,
            summary_vi: row.summary_vi,
            summary_en: row.summary_en,
            start_date: row.start_date,
            end_date: row.end_date,
            date_precision: row.date_precision,
            latitude: row.latitude,
            longitude: row.longitude,
            geo_precision: row.geo_precision,
            publication_status: row.publication_status,
            content_version: row.content_version,
            created_at: row.created_at,
            updated_at: row.updated_at,
            claims: None,
            relations: None,
            geography: None,
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ClaimDetailResponse {
    pub id: Uuid,
    pub entity_id: Uuid,
    pub claim_key: Option<String>,
    pub claim_type: String,
    pub statement_vi: String,
    pub statement_en: Option<String>,
    pub valid_from: Option<NaiveDate>,
    pub valid_to: Option<NaiveDate>,
    pub date_precision: Option<String>,
    pub confidence: String,
    pub verification_status: String,
    pub origin: String,
    pub risk_level: String,
    pub review_notes: Option<String>,
    pub created_by: Option<Uuid>,
    pub reviewed_by: Option<Uuid>,
    pub reviewed_at: Option<DateTime<Utc>>,
    pub verified_by: Option<Uuid>,
    pub verified_at: Option<DateTime<Utc>>,
    pub created_at: DateTime<Utc>,
    pub updated_at: DateTime<Utc>,
    pub supersedes_claim_id: Option<Uuid>,
    pub is_current: bool,
    pub sources: Option<Vec<SourceDetailResponse>>,
}

impl From<HistoricalClaimRow> for ClaimDetailResponse {
    fn from(row: HistoricalClaimRow) -> Self {
        Self {
            id: row.id,
            entity_id: row.entity_id,
            claim_key: row.claim_key,
            claim_type: row.claim_type,
            statement_vi: row.statement_vi,
            statement_en: row.statement_en,
            valid_from: row.valid_from,
            valid_to: row.valid_to,
            date_precision: row.date_precision,
            confidence: row.confidence,
            verification_status: row.verification_status,
            origin: row.origin,
            risk_level: row.risk_level,
            review_notes: row.review_notes,
            created_by: row.created_by,
            reviewed_by: row.reviewed_by,
            reviewed_at: row.reviewed_at,
            verified_by: row.verified_by,
            verified_at: row.verified_at,
            created_at: row.created_at,
            updated_at: row.updated_at,
            supersedes_claim_id: row.supersedes_claim_id,
            is_current: row.is_current,
            sources: None,
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SourceDetailResponse {
    pub id: Uuid,
    pub source_type: String,
    pub title: String,
    pub subtitle: Option<String>,
    pub author_text: Option<String>,
    pub editor_text: Option<String>,
    pub publisher: Option<String>,
    pub publication_year: Option<i32>,
    pub publication_date: Option<NaiveDate>,
    pub edition: Option<String>,
    pub volume: Option<String>,
    pub issue: Option<String>,
    pub pages: Option<String>,
    pub isbn: Option<String>,
    pub issn: Option<String>,
    pub doi: Option<String>,
    pub url: Option<String>,
    pub archive_url: Option<String>,
    pub repository_identifier: Option<String>,
    pub language: Option<String>,
    pub citation_text: Option<String>,
    pub rights_status: Option<String>,
    pub license: Option<String>,
    pub attribution_text: Option<String>,
    pub public_display_allowed: Option<bool>,
    pub derivative_allowed: Option<bool>,
    pub verification_status: String,
    pub created_at: DateTime<Utc>,
    pub updated_at: DateTime<Utc>,
}

impl From<HistoricalSourceRow> for SourceDetailResponse {
    fn from(row: HistoricalSourceRow) -> Self {
        Self {
            id: row.id,
            source_type: row.source_type,
            title: row.title,
            subtitle: row.subtitle,
            author_text: row.author_text,
            editor_text: row.editor_text,
            publisher: row.publisher,
            publication_year: row.publication_year,
            publication_date: row.publication_date,
            edition: row.edition,
            volume: row.volume,
            issue: row.issue,
            pages: row.pages,
            isbn: row.isbn,
            issn: row.issn,
            doi: row.doi,
            url: row.url,
            archive_url: row.archive_url,
            repository_identifier: row.repository_identifier,
            language: row.language,
            citation_text: row.citation_text,
            rights_status: row.rights_status,
            license: row.license,
            attribution_text: row.attribution_text,
            public_display_allowed: row.public_display_allowed,
            derivative_allowed: row.derivative_allowed,
            verification_status: row.verification_status,
            created_at: row.created_at,
            updated_at: row.updated_at,
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SearchResultItem {
    pub id: Uuid,
    pub entity_type: String,
    pub slug: String,
    pub name_vi: String,
    pub name_en: Option<String>,
    pub summary_vi: Option<String>,
    pub publication_status: String,
    pub matched_on: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct EntityListResponse {
    pub items: Vec<HistoricalEntityRow>,
    pub total: i64,
    pub offset: i64,
    pub limit: i64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ClaimListResponse {
    pub items: Vec<HistoricalClaimRow>,
    pub total: i64,
    pub offset: i64,
    pub limit: i64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SourceListResponse {
    pub items: Vec<HistoricalSourceRow>,
    pub total: i64,
    pub offset: i64,
    pub limit: i64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SearchHistoryResponse {
    pub query: String,
    pub items: Vec<SearchResultItem>,
    pub total: usize,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct UrnSummaryItem {
    pub id: Uuid,
    pub slug: String,
    pub name_vi: String,
    pub name_en: Option<String>,
    pub summary_vi: Option<String>,
    pub publication_status: String,
    pub relief_count: i64,
}
