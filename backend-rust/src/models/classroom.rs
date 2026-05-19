//! Classroom & Membership DTOs.
//!
//! Phase 8 (Tasks 9.1–9.4): Classrooms & Memberships migration.

use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};
use uuid::Uuid;

// ---------------------------------------------------------------------------
// Classroom DTOs
// ---------------------------------------------------------------------------

/// Request body for POST /api/v1/classrooms.
#[derive(Debug, Deserialize)]
pub struct CreateClassroomRequest {
    pub name: String,
    pub description: Option<String>,
    pub max_members: Option<i32>,
}

/// Request body for PATCH /api/v1/classrooms/{id}.
#[derive(Debug, Deserialize)]
pub struct UpdateClassroomRequest {
    pub name: Option<String>,
    pub description: Option<String>,
    pub max_members: Option<i32>,
}

/// Classroom in list/detail responses.
#[derive(Debug, Serialize)]
pub struct ClassroomOut {
    pub id: Uuid,
    pub name: String,
    pub description: Option<String>,
    pub owner_id: Uuid,
    pub max_members: i32,
    pub member_count: i32,
    pub created_at: DateTime<Utc>,
    pub is_archived: bool,
}

// ---------------------------------------------------------------------------
// Membership DTOs
// ---------------------------------------------------------------------------

/// Request body for POST /api/v1/classrooms/{id}/members.
#[derive(Debug, Deserialize)]
pub struct AddMemberRequest {
    pub user_id: Uuid,
    pub role: Option<String>, // "student" or "teacher"
}

/// A classroom member.
#[derive(Debug, Serialize)]
pub struct ClassroomMemberOut {
    pub user_id: Uuid,
    pub display_name: String,
    pub role: String,
    pub joined_at: DateTime<Utc>,
}

// ---------------------------------------------------------------------------
// Classroom Lessons DTOs
// ---------------------------------------------------------------------------

/// Request body for POST /api/v1/classrooms/{id}/lessons.
#[derive(Debug, Deserialize)]
pub struct AssignLessonRequest {
    pub motif_id: Uuid,
    pub due_date: Option<DateTime<Utc>>,
}

/// A lesson assigned to a classroom.
#[derive(Debug, Serialize)]
pub struct ClassroomLessonOut {
    pub id: Uuid,
    pub motif_id: Uuid,
    pub motif_name: String,
    pub assigned_at: DateTime<Utc>,
    pub due_date: Option<DateTime<Utc>>,
    pub completed_count: i32,
    pub total_members: i32,
}

// ---------------------------------------------------------------------------
// Classroom Analytics DTOs
// ---------------------------------------------------------------------------

/// Response for GET /api/v1/classrooms/{id}/analytics.
#[derive(Debug, Serialize)]
pub struct ClassroomAnalyticsOut {
    pub classroom_id: Uuid,
    pub total_members: i32,
    pub active_members_7d: i32,
    pub total_lessons_completed: i32,
    pub average_quiz_score: f64,
    pub total_xp_earned: i64,
    pub top_performers: Vec<ClassroomPerformer>,
}

/// A top performer in classroom analytics.
#[derive(Debug, Serialize)]
pub struct ClassroomPerformer {
    pub user_id: Uuid,
    pub display_name: String,
    pub xp_earned: i32,
    pub lessons_completed: i32,
}

// ---------------------------------------------------------------------------
// DB Row types
// ---------------------------------------------------------------------------

#[derive(Debug, sqlx::FromRow)]
pub struct ClassroomRow {
    pub id: Uuid,
    pub name: String,
    pub description: Option<String>,
    pub owner_id: Uuid,
    pub max_members: i32,
    pub member_count: i32,
    pub created_at: DateTime<Utc>,
    pub is_archived: bool,
}

#[derive(Debug, sqlx::FromRow)]
pub struct ClassroomMemberRow {
    pub user_id: Uuid,
    pub display_name: String,
    pub role: String,
    pub joined_at: DateTime<Utc>,
}

#[derive(Debug, sqlx::FromRow)]
pub struct ClassroomLessonRow {
    pub id: Uuid,
    pub motif_id: Uuid,
    pub motif_name: String,
    pub assigned_at: DateTime<Utc>,
    pub due_date: Option<DateTime<Utc>>,
    pub completed_count: i32,
    pub total_members: i32,
}

#[derive(Debug, sqlx::FromRow)]
pub struct ClassroomPerformerRow {
    pub user_id: Uuid,
    pub display_name: String,
    pub xp_earned: i32,
    pub lessons_completed: i32,
}

#[derive(Debug, sqlx::FromRow)]
pub struct MemberRoleRow {
    pub role: String,
}
