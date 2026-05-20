//! DTOs and SQLx row types for the FSRS spaced repetition feature.
//!
//! Spec: `.kiro/specs/fsrs-spaced-repetition/`
//!
//! Adapted to the actual `spaced_repetition_cards` schema (keyed by
//! `(user_id, motif_id)`), not the hypothetical `user_quiz_review_state` from
//! the spec. New columns extend the existing table.

use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};
use uuid::Uuid;

// ---------------------------------------------------------------------------
// FSRS rating + state enums
// ---------------------------------------------------------------------------

/// User feedback after attempting a card.
#[derive(Debug, Clone, Copy, Serialize, Deserialize, PartialEq, Eq)]
#[serde(rename_all = "PascalCase")]
pub enum FsrsRating {
    Again,
    Hard,
    Good,
    Easy,
}

impl FsrsRating {
    pub fn parse(input: &str) -> Option<Self> {
        match input {
            "Again" | "again" => Some(Self::Again),
            "Hard" | "hard" => Some(Self::Hard),
            "Good" | "good" => Some(Self::Good),
            "Easy" | "easy" => Some(Self::Easy),
            _ => None,
        }
    }

    pub fn as_str(&self) -> &'static str {
        match self {
            Self::Again => "Again",
            Self::Hard => "Hard",
            Self::Good => "Good",
            Self::Easy => "Easy",
        }
    }
}

/// Card lifecycle state.
#[derive(Debug, Clone, Copy, Serialize, Deserialize, PartialEq, Eq)]
#[serde(rename_all = "lowercase")]
pub enum CardState {
    New,
    Learning,
    Review,
    Relearning,
}

impl CardState {
    pub fn as_str(&self) -> &'static str {
        match self {
            Self::New => "new",
            Self::Learning => "learning",
            Self::Review => "review",
            Self::Relearning => "relearning",
        }
    }

    pub fn parse(input: &str) -> Self {
        match input {
            "learning" => Self::Learning,
            "review" => Self::Review,
            "relearning" => Self::Relearning,
            _ => Self::New,
        }
    }
}

// ---------------------------------------------------------------------------
// Row types
// ---------------------------------------------------------------------------

#[derive(Debug, sqlx::FromRow)]
pub struct ReviewStateRow {
    pub id: Uuid,
    pub user_id: Uuid,
    pub motif_id: Uuid,
    pub fsrs_state: Option<String>,
    pub fsrs_difficulty: Option<f64>,
    pub fsrs_stability: Option<f64>,
    pub fsrs_due_date: Option<DateTime<Utc>>,
    pub fsrs_last_review: Option<DateTime<Utc>>,
    pub interval_days: i32,
    pub next_review_at: DateTime<Utc>,
}

#[derive(Debug, sqlx::FromRow)]
pub struct UserFsrsParamsRow {
    pub id: Uuid,
    pub user_id: Uuid,
    pub parameters: Vec<f64>,
    pub optimal_retention: f64,
    pub last_optimized_at: Option<DateTime<Utc>>,
    pub review_count_at_last_optimize: i32,
}

// ---------------------------------------------------------------------------
// API request/response DTOs
// ---------------------------------------------------------------------------

#[derive(Debug, Deserialize)]
pub struct DueReviewsQuery {
    pub page: Option<u32>,
    pub page_size: Option<u32>,
}

#[derive(Debug, Serialize)]
pub struct DueCardOut {
    pub card_id: Uuid,
    pub motif_id: Uuid,
    pub motif_name: Option<String>,
    pub fsrs_due_date: DateTime<Utc>,
    pub fsrs_stability: Option<f64>,
    pub fsrs_difficulty: Option<f64>,
    pub fsrs_state: Option<String>,
}

#[derive(Debug, Serialize)]
pub struct DueReviewsResponse {
    pub cards: Vec<DueCardOut>,
    pub total: i64,
    pub page: u32,
    pub page_size: u32,
}

#[derive(Debug, Deserialize)]
pub struct RateCardRequest {
    pub rating: String,
}

#[derive(Debug, Serialize)]
pub struct RateCardResponse {
    pub card_id: Uuid,
    pub fsrs_due_date: DateTime<Utc>,
    pub fsrs_stability: f64,
    pub fsrs_difficulty: f64,
    pub fsrs_state: String,
    pub interval_days: f64,
    pub cohort: String,
}

#[derive(Debug, Serialize)]
pub struct FsrsSettingsResponse {
    pub optimal_retention: f64,
    pub recommended_range: [f64; 2],
    pub last_optimized_at: Option<DateTime<Utc>>,
    pub review_count: i64,
    pub using_personal_params: bool,
    pub cohort: String,
}

#[derive(Debug, Deserialize)]
pub struct UpdateFsrsSettingsRequest {
    pub optimal_retention: f64,
}

#[derive(Debug, Serialize)]
pub struct CohortStats {
    pub cohort: String,
    pub user_count: i64,
    pub avg_reviews_per_day: f64,
    pub retention_rate_30d: f64,
    pub avg_interval_days: f64,
}

#[derive(Debug, Serialize)]
pub struct FsrsStatsResponse {
    pub cohorts: Vec<CohortStats>,
    pub total_users: i64,
}
