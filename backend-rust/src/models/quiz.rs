//! Quiz & Adaptive domain DTOs.
//!
//! Phase 5 (Tasks 6.1–6.4): Quizzes & Adaptive migration.

use serde::{Deserialize, Serialize};
use uuid::Uuid;

// ---------------------------------------------------------------------------
// Quiz DTOs
// ---------------------------------------------------------------------------

/// A quiz question in the full quiz response.
#[derive(Debug, Serialize)]
pub struct QuizQuestionOut {
    pub id: Uuid,
    pub question_type: String,
    pub question_text: String,
    pub options: Option<serde_json::Value>,
    pub target_mesh_name: Option<String>,
    pub difficulty: i32,
    pub explanation: Option<String>,
    pub image_url: Option<String>,
}

/// Full quiz response (GET /api/v1/quizzes/{quiz_id}).
#[derive(Debug, Serialize)]
pub struct QuizDetailOut {
    pub quiz_id: Uuid,
    pub motif_id: Uuid,
    pub motif_name: String,
    pub questions: Vec<QuizQuestionOut>,
    pub total_questions: usize,
    pub time_limit_seconds: Option<i32>,
}

/// Request body for POST /api/v1/quizzes/{quiz_id}/submit.
#[derive(Debug, Deserialize)]
pub struct QuizSubmitRequest {
    pub answers: Vec<QuizAnswer>,
}

/// A single answer in a quiz submission.
#[derive(Debug, Deserialize)]
pub struct QuizAnswer {
    pub question_id: Uuid,
    pub selected_option: Option<String>,
    pub selected_mesh: Option<String>,
}

/// Response for POST /api/v1/quizzes/{quiz_id}/submit.
#[derive(Debug, Serialize)]
pub struct QuizSubmitResponse {
    pub quiz_id: Uuid,
    pub score: i32,
    pub total: i32,
    pub percentage: f64,
    pub passed: bool,
    pub xp_awarded: i32,
    pub results: Vec<QuizQuestionResult>,
}

/// Per-question result in quiz submission response.
#[derive(Debug, Serialize)]
pub struct QuizQuestionResult {
    pub question_id: Uuid,
    pub correct: bool,
    pub correct_answer: Option<String>,
    pub explanation: Option<String>,
}

/// Request body for POST /api/v1/quizzes/adaptive.
#[derive(Debug, Deserialize)]
pub struct AdaptiveQuizRequest {
    pub motif_id: Option<Uuid>,
    pub urn_id: Option<Uuid>,
    pub difficulty: Option<i32>,
    pub question_count: Option<i32>,
}

/// Response for POST /api/v1/quizzes/adaptive.
#[derive(Debug, Serialize)]
pub struct AdaptiveQuizResponse {
    pub quiz_id: Uuid,
    pub questions: Vec<QuizQuestionOut>,
    pub difficulty: i32,
    pub total_questions: usize,
}

/// A hint for a quiz question.
#[derive(Debug, Serialize)]
pub struct QuizHintOut {
    pub question_id: Uuid,
    pub hint_text: String,
    pub hint_level: i32,
    pub cost_hearts: i32,
}

/// Response for GET /api/v1/quizzes/{quiz_id}/hints.
#[derive(Debug, Serialize)]
pub struct QuizHintsResponse {
    pub quiz_id: Uuid,
    pub hints: Vec<QuizHintOut>,
}

// ---------------------------------------------------------------------------
// DB Row types
// ---------------------------------------------------------------------------

#[derive(Debug, sqlx::FromRow)]
pub struct QuizQuestionRow {
    pub id: Uuid,
    pub motif_id: Uuid,
    pub question_type: String,
    pub question_text: String,
    pub options: Option<serde_json::Value>,
    pub correct_answer: Option<String>,
    pub target_mesh_name: Option<String>,
    pub difficulty: Option<i32>,
    pub explanation: Option<String>,
    pub is_active: bool,
}

#[derive(Debug, sqlx::FromRow)]
pub struct MotifNameRow {
    pub id: Uuid,
    pub name: String,
}
