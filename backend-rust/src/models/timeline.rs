//! DTOs for the Heritage Time-Lapse feature.
//!
//! Spec: `.kiro/specs/heritage-time-lapse/`

use chrono::{DateTime, NaiveDate, Utc};
use serde::{Deserialize, Serialize};
use uuid::Uuid;

// ---------------------------------------------------------------------------
// Heritage Era
// ---------------------------------------------------------------------------

#[derive(Debug, sqlx::FromRow, Serialize)]
pub struct HeritageEraRow {
    pub id: Uuid,
    pub slug: String,
    pub name_vi: String,
    pub name_en: String,
    pub start_year: i32,
    pub end_year: i32,
    pub color_hex: String,
    pub sort_order: i32,
    pub created_at: DateTime<Utc>,
}

#[derive(Debug, Deserialize)]
pub struct CreateEraRequest {
    pub slug: String,
    pub name_vi: String,
    pub name_en: String,
    pub start_year: i32,
    pub end_year: i32,
    pub color_hex: String,
    pub sort_order: Option<i32>,
}

// ---------------------------------------------------------------------------
// Historical Event
// ---------------------------------------------------------------------------

#[derive(Debug, sqlx::FromRow)]
pub struct HistoricalEventRow {
    pub id: Uuid,
    pub era_id: Uuid,
    pub slug: String,
    pub name_vi: String,
    pub name_en: String,
    pub occurred_on: NaiveDate,
    pub description_vi: String,
    pub description_en: String,
    pub motif_id: Option<Uuid>,
    pub urn_id: Option<Uuid>,
    pub importance: i32,
    pub created_at: DateTime<Utc>,
}

#[derive(Debug, Serialize)]
pub struct HistoricalEventOut {
    pub id: Uuid,
    pub slug: String,
    pub name_vi: String,
    pub name_en: String,
    pub occurred_on: NaiveDate,
    pub description_vi: String,
    pub description_en: String,
    pub importance: i32,
    pub era: EraSummary,
    pub motif: Option<MotifSummary>,
    pub urn: Option<UrnSummary>,
}

#[derive(Debug, Serialize)]
pub struct EraSummary {
    pub id: Uuid,
    pub slug: String,
    pub name_vi: String,
    pub color_hex: String,
}

#[derive(Debug, Serialize)]
pub struct MotifSummary {
    pub id: Uuid,
    pub name: String,
    pub thumbnail_url: Option<String>,
}

#[derive(Debug, Serialize)]
pub struct UrnSummary {
    pub id: Uuid,
    pub slug: String,
    pub name: String,
}

#[derive(Debug, Deserialize)]
pub struct CreateEventRequest {
    pub era_id: Uuid,
    pub slug: String,
    pub name_vi: String,
    pub name_en: String,
    pub occurred_on: NaiveDate,
    #[serde(default)]
    pub description_vi: String,
    #[serde(default)]
    pub description_en: String,
    pub motif_id: Option<Uuid>,
    pub urn_id: Option<Uuid>,
    #[serde(default = "default_importance")]
    pub importance: i32,
}

fn default_importance() -> i32 {
    1
}

// ---------------------------------------------------------------------------
// Timeline endpoints
// ---------------------------------------------------------------------------

#[derive(Debug, Deserialize)]
pub struct TimelineEventsQuery {
    pub from: Option<i32>,
    pub to: Option<i32>,
}

#[derive(Debug, Serialize)]
pub struct TimelineEventsMeta {
    pub min_year: Option<i32>,
    pub max_year: Option<i32>,
    pub total_count: i64,
}

#[derive(Debug, Serialize)]
pub struct TimelineEventsResponse {
    pub events: Vec<HistoricalEventOut>,
    pub meta: TimelineEventsMeta,
}

#[derive(Debug, Deserialize)]
pub struct MotifsByEraQuery {
    pub era: Option<String>,
}

#[derive(Debug, Serialize)]
pub struct MotifByEraOut {
    pub id: Uuid,
    pub name: String,
    pub category: Option<String>,
    pub rarity: Option<String>,
    pub thumbnail_url: Option<String>,
    pub urn: Option<UrnSummary>,
}

#[derive(Debug, Serialize)]
pub struct MotifsByEraResponse {
    pub era: HeritageEraRow,
    pub motifs: Vec<MotifByEraOut>,
}

// ---------------------------------------------------------------------------
// Compare endpoint
// ---------------------------------------------------------------------------

#[derive(Debug, Deserialize)]
pub struct CompareQuery {
    pub ids: String,
}

#[derive(Debug, Serialize)]
pub struct ComparedMotif {
    pub id: Uuid,
    pub name: String,
    pub name_en: Option<String>,
    pub description: Option<String>,
    pub category: Option<String>,
    pub rarity: Option<String>,
    pub eras: Vec<EraSummary>,
    pub urn: Option<UrnSummary>,
    pub thumbnail_url: Option<String>,
}

#[derive(Debug, Serialize)]
pub struct CompareResponse {
    pub motifs: Vec<ComparedMotif>,
    pub comparison_axes: Vec<&'static str>,
}

// ---------------------------------------------------------------------------
// Admin stats
// ---------------------------------------------------------------------------

#[derive(Debug, Serialize, sqlx::FromRow)]
pub struct WeeklyView {
    pub week_start: NaiveDate,
    pub count: i64,
}

#[derive(Debug, Serialize)]
pub struct ComparedPair {
    pub motif_a_id: Uuid,
    pub motif_b_id: Uuid,
    pub count: i64,
}

#[derive(Debug, Serialize)]
pub struct TimelineStatsResponse {
    pub weekly_views: Vec<WeeklyView>,
    pub top_compared_pairs: Vec<ComparedPair>,
}
