//! DTOs for the Heritage Trail Mode feature.
//!
//! Spec: `.kiro/specs/heritage-trail-mode/`

use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};
use uuid::Uuid;

// ---------------------------------------------------------------------------
// Enums
// ---------------------------------------------------------------------------

#[derive(Debug, Clone, Copy, Serialize, Deserialize, PartialEq)]
#[serde(rename_all = "snake_case")]
pub enum TrailStatus {
    Draft,
    Published,
    PendingReview,
    Archived,
}

#[derive(Debug, Clone, Copy, Serialize, Deserialize, PartialEq)]
#[serde(rename_all = "snake_case")]
pub enum TrailVisibility {
    Public,
    Classroom,
    Private,
}

#[derive(Debug, Clone, Copy, Serialize, Deserialize, PartialEq)]
pub enum Pace {
    #[serde(rename = "daily")]
    Daily,
    #[serde(rename = "2x_week")]
    TwiceWeek,
    #[serde(rename = "weekly")]
    Weekly,
}

impl Pace {
    pub fn as_str(&self) -> &'static str {
        match self {
            Pace::Daily => "daily",
            Pace::TwiceWeek => "2x_week",
            Pace::Weekly => "weekly",
        }
    }

    pub fn parse(input: &str) -> Option<Self> {
        match input {
            "daily" => Some(Pace::Daily),
            "2x_week" => Some(Pace::TwiceWeek),
            "weekly" => Some(Pace::Weekly),
            _ => None,
        }
    }

    /// Hours added to compute the next reminder time.
    pub fn reminder_hours(&self) -> i64 {
        match self {
            Pace::Daily => 24,
            Pace::TwiceWeek => 84,
            Pace::Weekly => 168,
        }
    }
}

// ---------------------------------------------------------------------------
// Request DTOs
// ---------------------------------------------------------------------------

#[derive(Debug, Deserialize)]
pub struct TrailStepInput {
    pub motif_id: Uuid,
    pub position: i32,
}

#[derive(Debug, Deserialize)]
pub struct TrailCheckpointInput {
    pub after_position: i32,
    pub prompt_vi: String,
    pub prompt_en: Option<String>,
}

#[derive(Debug, Deserialize)]
pub struct CreateTrailRequest {
    pub slug: String,
    pub title_vi: String,
    pub title_en: String,
    pub description_vi: Option<String>,
    pub description_en: Option<String>,
    pub narrator_intro: Option<String>,
    pub narrator_outro: Option<String>,
    #[serde(default = "default_difficulty")]
    pub difficulty: String,
    #[serde(default = "default_estimated_minutes")]
    pub estimated_minutes: i32,
    #[serde(default)]
    pub steps: Vec<TrailStepInput>,
    #[serde(default)]
    pub checkpoints: Vec<TrailCheckpointInput>,
}

fn default_difficulty() -> String {
    "beginner".to_string()
}

fn default_estimated_minutes() -> i32 {
    30
}

#[derive(Debug, Deserialize)]
pub struct UpdateTrailRequest {
    pub title_vi: Option<String>,
    pub title_en: Option<String>,
    pub description_vi: Option<String>,
    pub description_en: Option<String>,
    pub narrator_intro: Option<String>,
    pub narrator_outro: Option<String>,
    pub difficulty: Option<String>,
    pub estimated_minutes: Option<i32>,
    pub status: Option<String>,
}

#[derive(Debug, Deserialize)]
pub struct CreateTeacherTrailRequest {
    pub slug: String,
    pub title_vi: String,
    pub title_en: String,
    pub description_vi: Option<String>,
    pub description_en: Option<String>,
    pub narrator_intro: Option<String>,
    pub narrator_outro: Option<String>,
    #[serde(default = "default_difficulty")]
    pub difficulty: String,
    #[serde(default = "default_estimated_minutes")]
    pub estimated_minutes: i32,
    pub classroom_id: Uuid,
    #[serde(default)]
    pub steps: Vec<TrailStepInput>,
    #[serde(default)]
    pub checkpoints: Vec<TrailCheckpointInput>,
}

#[derive(Debug, Deserialize)]
pub struct SetPaceRequest {
    pub pace: String,
}

#[derive(Debug, Deserialize)]
pub struct CheckpointSubmitRequest {
    pub response: String,
}

// ---------------------------------------------------------------------------
// Response DTOs
// ---------------------------------------------------------------------------

#[derive(Debug, sqlx::FromRow)]
pub struct TrailRow {
    pub id: Uuid,
    pub slug: String,
    pub title_vi: String,
    pub title_en: String,
    pub description_vi: Option<String>,
    pub description_en: Option<String>,
    pub narrator_intro: Option<String>,
    pub narrator_outro: Option<String>,
    pub difficulty: String,
    pub estimated_minutes: i32,
    pub created_by_user_id: Uuid,
    pub status: String,
    pub visibility: String,
    pub classroom_id: Option<Uuid>,
    pub published_at: Option<DateTime<Utc>>,
    pub created_at: DateTime<Utc>,
    pub updated_at: DateTime<Utc>,
}

#[derive(Debug, Serialize)]
pub struct TrailOut {
    pub id: Uuid,
    pub slug: String,
    pub title_vi: String,
    pub title_en: String,
    pub description_vi: Option<String>,
    pub description_en: Option<String>,
    pub narrator_intro: Option<String>,
    pub narrator_outro: Option<String>,
    pub difficulty: String,
    pub estimated_minutes: i32,
    pub status: String,
    pub visibility: String,
    pub step_count: i64,
    pub checkpoint_count: i64,
    pub created_at: DateTime<Utc>,
    pub published_at: Option<DateTime<Utc>>,
}

#[derive(Debug, Serialize)]
pub struct UserTrailProgressOut {
    pub current_position: i32,
    pub started_at: DateTime<Utc>,
    pub completed_at: Option<DateTime<Utc>>,
    pub pace: String,
    pub next_reminder_at: Option<DateTime<Utc>>,
}

#[derive(Debug, Serialize)]
pub struct TrailDetailOut {
    pub trail: TrailOut,
    pub progress: Option<UserTrailProgressOut>,
}

#[derive(Debug, Serialize)]
pub struct TrailListResponse {
    pub trails: Vec<TrailOut>,
    pub page: i64,
    pub per_page: i64,
    pub total: i64,
}

#[derive(Debug, Serialize)]
pub struct StepMotif {
    pub motif_id: Uuid,
    pub position: i32,
    pub motif_name: Option<String>,
    pub thumbnail_url: Option<String>,
    pub description: Option<String>,
}

#[derive(Debug, Serialize)]
pub struct TrailStartResponse {
    pub progress: UserTrailProgressOut,
    pub first_motif: Option<StepMotif>,
    pub narrator_intro: Option<String>,
}

#[derive(Debug, Serialize)]
#[serde(tag = "type")]
pub enum StepCompleteResponse {
    #[serde(rename = "next_motif")]
    NextMotif { position: i32, motif: StepMotif },
    #[serde(rename = "checkpoint")]
    Checkpoint {
        checkpoint_id: Uuid,
        after_position: i32,
        prompt_vi: String,
        prompt_en: Option<String>,
    },
    #[serde(rename = "completed")]
    Completed {
        outro: Option<String>,
        certificate_hash: Option<String>,
        certificate_url: Option<String>,
    },
}

#[derive(Debug, Serialize)]
pub struct CheckpointResponse {
    pub current_position: i32,
    pub next: StepCompleteResponse,
}

#[derive(Debug, Serialize)]
pub struct CertificateVerifyOut {
    pub valid: bool,
    pub user_display_name: String,
    pub trail_title: String,
    pub issued_at: DateTime<Utc>,
}

#[derive(Debug, Serialize, sqlx::FromRow)]
pub struct SkippedCheckpointOut {
    pub checkpoint_id: Uuid,
    pub after_position: i32,
    pub prompt_vi: String,
    pub null_response_count: i64,
}

#[derive(Debug, Serialize)]
pub struct TrailAnalyticsOut {
    pub unique_starts: i64,
    pub completed: i64,
    pub completion_rate: f64,
    pub average_days_to_complete: Option<f64>,
    pub top_skipped_checkpoints: Vec<SkippedCheckpointOut>,
}
