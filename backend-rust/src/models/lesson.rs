//! Lesson, Motif, and Urn domain DTOs.
//!
//! Phase 4 (Tasks 5.1–5.5): Lessons & Content migration.

use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};
use uuid::Uuid;

// ---------------------------------------------------------------------------
// Urn DTOs
// ---------------------------------------------------------------------------

/// Item in the urn list response (GET /api/v1/urns).
#[derive(Debug, Serialize)]
pub struct UrnListItem {
    pub id: Uuid,
    pub slug: String,
    pub name: String,
    pub model_url: String,
    pub thumbnail_url: Option<String>,
    pub display_order: i32,
    pub is_demo: bool,
    pub motif_count: i64,
    pub discovered_count: i64,
    pub learned_count: i64,
    pub mastered_count: i64,
}

/// Urn detail (GET /api/v1/urns/{urn_slug}).
#[derive(Debug, Serialize)]
pub struct UrnDetailOut {
    pub id: Uuid,
    pub slug: String,
    pub name: String,
    pub name_han: Option<String>,
    pub represents: Option<String>,
    pub description: Option<String>,
    pub model_url: String,
    pub thumbnail_url: Option<String>,
    pub display_order: i32,
    pub is_demo: bool,
}

/// Full urn detail response with motifs.
#[derive(Debug, Serialize)]
pub struct UrnDetailResponse {
    pub urn: UrnDetailOut,
    pub motifs: Vec<MotifOut>,
}

/// Urn summary used inside motif detail.
#[derive(Debug, Serialize)]
pub struct UrnOut {
    pub id: Uuid,
    pub slug: String,
    pub name: String,
    pub model_url: String,
    pub thumbnail_url: Option<String>,
}

// ---------------------------------------------------------------------------
// Motif DTOs
// ---------------------------------------------------------------------------

/// Motif item in list responses.
#[derive(Debug, Serialize)]
pub struct MotifOut {
    pub id: Uuid,
    pub urn_id: Uuid,
    pub mesh_name: String,
    pub name: String,
    pub name_en: Option<String>,
    pub category: String,
    pub rarity: String,
    pub pos_x: Option<f64>,
    pub pos_y: Option<f64>,
    pub pos_z: Option<f64>,
    pub bounding_radius: Option<f64>,
    pub thumbnail_url: Option<String>,
    pub silhouette_url: Option<String>,
    pub is_demo: bool,
    pub display_order: Option<i32>,
    pub lesson_intro: Option<String>,
}

/// Response for GET /motifs/{urn_name}.
#[derive(Debug, Serialize)]
pub struct MotifsByUrnResponse {
    pub urn: UrnOut,
    pub motifs: Vec<MotifOut>,
}

/// Lesson content embedded in motif detail.
#[derive(Debug, Serialize)]
pub struct LessonContentOut {
    pub intro_text: Option<String>,
    pub description: String,
    pub historical_context: Option<String>,
    pub symbolism: Option<String>,
    pub fun_fact: Option<String>,
    pub is_ai_generated: bool,
    pub audio_narration_url: Option<String>,
    pub additional_images: Option<serde_json::Value>,
    pub video_url: Option<String>,
}

/// Quiz question in motif detail.
#[derive(Debug, Serialize)]
pub struct MotifQuizQuestionOut {
    pub id: Uuid,
    pub question_type: String,
    pub question_text: String,
    pub options: Option<serde_json::Value>,
    pub target_mesh_name: Option<String>,
    pub difficulty: i32,
    pub explanation: Option<String>,
    pub image_url: Option<String>,
}

/// User progress for a specific motif.
#[derive(Debug, Serialize)]
pub struct UserProgressDetailOut {
    pub id: Uuid,
    pub user_id: Uuid,
    pub motif_id: Uuid,
    pub status: String,
    pub discovered_at: Option<DateTime<Utc>>,
    pub learned_at: Option<DateTime<Utc>>,
    pub mastered_at: Option<DateTime<Utc>>,
    pub xp_earned: i32,
    pub quiz_best_score: Option<i32>,
}

/// Full motif detail response (GET /api/v1/motifs/{motif_id}).
#[derive(Debug, Serialize)]
pub struct MotifDetailOut {
    pub id: Uuid,
    pub urn: UrnOut,
    pub mesh_name: String,
    pub name: String,
    pub name_en: Option<String>,
    pub category: String,
    pub rarity: String,
    pub thumbnail_url: Option<String>,
    pub silhouette_url: Option<String>,
    pub image_url: Option<String>,
    pub is_demo: bool,
    pub display_order: Option<i32>,
    pub lesson: Option<LessonContentOut>,
    pub quiz_question_count: usize,
    pub quiz_questions: Vec<MotifQuizQuestionOut>,
    pub progress: Option<UserProgressDetailOut>,
}

// ---------------------------------------------------------------------------
// Urn Progress DTOs
// ---------------------------------------------------------------------------

/// Per-motif progress in urn progress response.
#[derive(Debug, Serialize)]
pub struct MotifProgressOut {
    pub motif_id: Uuid,
    pub status: String,
    pub discovered_at: Option<DateTime<Utc>>,
    pub lesson_viewed_at: Option<DateTime<Utc>>,
    pub learned_at: Option<DateTime<Utc>>,
    pub mastered_at: Option<DateTime<Utc>>,
    pub quiz_attempts: i32,
    pub quiz_best_score: i32,
    pub xp_earned: i32,
}

/// Response for GET /api/v1/urns/{urn_slug}/progress.
#[derive(Debug, Serialize)]
pub struct UrnProgressResponse {
    pub urn_id: Uuid,
    pub urn_slug: String,
    pub motifs: Vec<MotifProgressOut>,
}

// ---------------------------------------------------------------------------
// Lesson Complete DTOs
// ---------------------------------------------------------------------------

/// Response for POST /api/v1/motifs/{motif_id}/complete-lesson.
#[derive(Debug, Serialize)]
pub struct LessonCompleteResponse {
    pub user_id: Uuid,
    pub motif_id: Uuid,
    pub status: String,
    pub lesson_viewed_at: Option<DateTime<Utc>>,
    pub learned_at: Option<DateTime<Utc>>,
    pub xp_awarded: i32,
    pub total_xp: i32,
}

// ---------------------------------------------------------------------------
// Lesson Cache DTOs
// ---------------------------------------------------------------------------

/// File info in cache manifest.
#[derive(Debug, Serialize)]
pub struct CacheFileInfo {
    pub url: String,
    #[serde(rename = "type")]
    pub file_type: String,
    pub size_bytes: i64,
}

/// Single lesson in cache manifest.
#[derive(Debug, Serialize)]
pub struct CacheManifestItem {
    pub lesson_id: Uuid,
    pub motif_id: Uuid,
    pub motif_name: String,
    pub title: String,
    pub version: i32,
    pub file_urls: Vec<CacheFileInfo>,
    pub total_size_bytes: i64,
    pub priority: i32,
}

/// Full cache manifest response.
#[derive(Debug, Serialize)]
pub struct CacheManifestOut {
    pub lessons: Vec<CacheManifestItem>,
    pub total_size_bytes: i64,
    pub recommended_cache_size_bytes: i64,
}

/// Request body for POST /api/v1/lessons/{lesson_id}/cache.
#[derive(Debug, Deserialize)]
pub struct LessonCacheIn {
    pub file_size_bytes: i64,
    #[serde(default = "default_cache_version")]
    pub cache_version: i32,
}

fn default_cache_version() -> i32 {
    1
}

/// Response for lesson cache operations.
#[derive(Debug, Serialize)]
pub struct LessonCacheOut {
    pub id: Uuid,
    pub user_id: Uuid,
    pub lesson_id: Uuid,
    pub cached_at: DateTime<Utc>,
    pub cache_version: i32,
    pub file_size_bytes: i64,
    pub is_valid: bool,
    pub expires_at: Option<DateTime<Utc>>,
}

// ---------------------------------------------------------------------------
// Lesson Sequence & Prerequisites DTOs
// ---------------------------------------------------------------------------

/// Info about a prerequisite lesson.
#[derive(Debug, Serialize)]
pub struct PrerequisiteLessonInfo {
    pub id: Uuid,
    pub motif_id: Uuid,
    pub motif_name: String,
    pub motif_slug: String,
    pub difficulty_level: Option<i32>,
    pub estimated_time_minutes: Option<i32>,
    pub is_strict: bool,
    pub is_completed: bool,
}

/// Response for GET /api/v1/lessons/{lesson_id}/prerequisites.
#[derive(Debug, Serialize)]
pub struct LessonPrerequisitesOut {
    pub lesson_id: Uuid,
    pub prerequisites: Vec<PrerequisiteLessonInfo>,
    pub all_prerequisites_met: bool,
}

/// Response for GET /api/v1/lessons/{lesson_id}/is-unlocked.
#[derive(Debug, Serialize)]
pub struct LessonUnlockStatusOut {
    pub lesson_id: Uuid,
    pub is_unlocked: bool,
    pub missing_prerequisites: Vec<PrerequisiteLessonInfo>,
    pub recommended_prerequisites: Vec<PrerequisiteLessonInfo>,
}

/// Response for GET /api/v1/lessons/next.
#[derive(Debug, Serialize)]
pub struct NextLessonOut {
    pub lesson_id: Option<Uuid>,
    pub motif_id: Option<Uuid>,
    pub motif_name: Option<String>,
    pub motif_slug: Option<String>,
    pub urn_id: Option<Uuid>,
    pub urn_name: Option<String>,
    pub difficulty_level: Option<i32>,
    pub estimated_time_minutes: Option<i32>,
    pub reason: String,
    pub has_prerequisites: bool,
    pub progress_status: Option<String>,
}

/// A single lesson in the learning sequence.
#[derive(Debug, Serialize)]
pub struct LessonSequenceItem {
    pub lesson_id: Uuid,
    pub motif_id: Uuid,
    pub motif_name: Option<String>,
    pub motif_slug: Option<String>,
    pub urn_id: Option<Uuid>,
    pub urn_name: Option<String>,
    pub difficulty_level: Option<i32>,
    pub estimated_time_minutes: Option<i32>,
    pub is_unlocked: bool,
    pub is_completed: bool,
    pub progress_status: Option<String>,
    pub position: i32,
}

/// Response for GET /api/v1/lessons/sequence.
#[derive(Debug, Serialize)]
pub struct LessonSequenceOut {
    pub urn_id: Option<Uuid>,
    pub urn_name: Option<String>,
    pub total_lessons: i32,
    pub completed_lessons: i32,
    pub current_position: i32,
    pub sequence: Vec<LessonSequenceItem>,
}
