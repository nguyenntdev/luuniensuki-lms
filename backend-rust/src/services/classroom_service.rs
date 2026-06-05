//! Classroom & Membership business logic.
//!
//! Phase 8 (Tasks 9.1–9.4): Classrooms & Memberships migration.

use chrono::Utc;
use sqlx::PgPool;
use uuid::Uuid;

use crate::error::AppError;
use crate::models::classroom::*;

/// Verify user is owner or teacher of the classroom.
async fn require_classroom_admin(
    pool: &PgPool,
    classroom_id: Uuid,
    user_id: Uuid,
) -> Result<(), AppError> {
    // Check if owner
    let owner: Option<(Uuid,)> = sqlx::query_as(
        "SELECT teacher_id AS owner_id FROM classes WHERE id = $1 AND teacher_id = $2",
    )
    .bind(classroom_id)
    .bind(user_id)
    .fetch_optional(pool)
    .await
    .map_err(|e| AppError::Internal(e.into()))?;

    if owner.is_some() {
        return Ok(());
    }

    // Check if teacher member
    let member = sqlx::query_as::<_, MemberRoleRow>(
        "SELECT role FROM class_members WHERE class_id = $1 AND user_id = $2",
    )
    .bind(classroom_id)
    .bind(user_id)
    .fetch_optional(pool)
    .await
    .map_err(|e| AppError::Internal(e.into()))?;

    match member {
        Some(m) if m.role == "teacher" => Ok(()),
        _ => Err(AppError::Http {
            status: axum::http::StatusCode::FORBIDDEN,
            message: "You do not have permission to manage this classroom".to_string(),
        }),
    }
}

/// Verify user is a member (any role) or owner of the classroom.
async fn require_classroom_member(
    pool: &PgPool,
    classroom_id: Uuid,
    user_id: Uuid,
) -> Result<(), AppError> {
    let owner: Option<(Uuid,)> = sqlx::query_as(
        "SELECT teacher_id AS owner_id FROM classes WHERE id = $1 AND teacher_id = $2",
    )
    .bind(classroom_id)
    .bind(user_id)
    .fetch_optional(pool)
    .await
    .map_err(|e| AppError::Internal(e.into()))?;

    if owner.is_some() {
        return Ok(());
    }

    let member: Option<(Uuid,)> = sqlx::query_as(
        "SELECT user_id FROM class_members WHERE class_id = $1 AND user_id = $2",
    )
    .bind(classroom_id)
    .bind(user_id)
    .fetch_optional(pool)
    .await
    .map_err(|e| AppError::Internal(e.into()))?;

    if member.is_some() {
        return Ok(());
    }

    Err(AppError::Http {
        status: axum::http::StatusCode::FORBIDDEN,
        message: "You are not a member of this classroom".to_string(),
    })
}

/// POST /api/v1/classrooms — create classroom.
pub async fn create_classroom(
    pool: &PgPool,
    user_id: Uuid,
    payload: &CreateClassroomRequest,
) -> Result<ClassroomOut, AppError> {
    let now = Utc::now();
    let max_members = payload.max_members.unwrap_or(30);
    // classes.class_code is required; generate a short unique-ish join code.
    let class_code: String = Uuid::new_v4().simple().to_string()[..8].to_uppercase();

    let row = sqlx::query_as::<_, ClassroomRow>(
        r#"
        INSERT INTO classes (id, name, description, teacher_id, max_students, class_code, created_at, is_archived)
        VALUES ($1, $2, $3, $4, $5, $7, $6, false)
        RETURNING id, name, description, teacher_id AS owner_id, max_students AS max_members,
                  0 AS member_count, created_at, is_archived
        "#,
    )
    .bind(Uuid::new_v4())
    .bind(&payload.name)
    .bind(&payload.description)
    .bind(user_id)
    .bind(max_members)
    .bind(now)
    .bind(&class_code)
    .fetch_one(pool)
    .await
    .map_err(|e| AppError::Internal(e.into()))?;

    Ok(ClassroomOut {
        id: row.id,
        name: row.name,
        description: row.description,
        owner_id: row.owner_id,
        max_members: row.max_members,
        member_count: row.member_count,
        created_at: row.created_at,
        is_archived: row.is_archived,
    })
}

/// GET /api/v1/classrooms — list classrooms for user.
pub async fn list_classrooms(pool: &PgPool, user_id: Uuid) -> Result<Vec<ClassroomOut>, AppError> {
    let rows = sqlx::query_as::<_, ClassroomRow>(
        r#"
        SELECT c.id, c.name, c.description, c.teacher_id AS owner_id, c.max_students AS max_members,
               (SELECT COUNT(*)::int FROM class_members cmc WHERE cmc.class_id = c.id) AS member_count,
               c.created_at, c.is_archived
        FROM classes c
        WHERE c.is_archived = false
          AND (c.teacher_id = $1 OR EXISTS (
              SELECT 1 FROM class_members cm WHERE cm.class_id = c.id AND cm.user_id = $1
          ))
        ORDER BY c.created_at DESC
        "#,
    )
    .bind(user_id)
    .fetch_all(pool)
    .await
    .map_err(|e| AppError::Internal(e.into()))?;

    Ok(rows
        .into_iter()
        .map(|r| ClassroomOut {
            id: r.id,
            name: r.name,
            description: r.description,
            owner_id: r.owner_id,
            max_members: r.max_members,
            member_count: r.member_count,
            created_at: r.created_at,
            is_archived: r.is_archived,
        })
        .collect())
}

/// GET /api/v1/classrooms/{id} — classroom detail.
pub async fn get_classroom(
    pool: &PgPool,
    classroom_id: Uuid,
    user_id: Uuid,
) -> Result<ClassroomOut, AppError> {
    require_classroom_member(pool, classroom_id, user_id).await?;

    let row = sqlx::query_as::<_, ClassroomRow>(
        r#"
        SELECT id, name, description, teacher_id AS owner_id, max_students AS max_members,
               (SELECT COUNT(*)::int FROM class_members WHERE class_id = $1) AS member_count, created_at, is_archived
        FROM classes WHERE id = $1
        "#,
    )
    .bind(classroom_id)
    .fetch_optional(pool)
    .await
    .map_err(|e| AppError::Internal(e.into()))?
    .ok_or_else(|| AppError::Http {
        status: axum::http::StatusCode::NOT_FOUND,
        message: "Classroom not found".to_string(),
    })?;

    Ok(ClassroomOut {
        id: row.id,
        name: row.name,
        description: row.description,
        owner_id: row.owner_id,
        max_members: row.max_members,
        member_count: row.member_count,
        created_at: row.created_at,
        is_archived: row.is_archived,
    })
}

/// PATCH /api/v1/classrooms/{id} — update classroom.
pub async fn update_classroom(
    pool: &PgPool,
    classroom_id: Uuid,
    user_id: Uuid,
    payload: &UpdateClassroomRequest,
) -> Result<ClassroomOut, AppError> {
    require_classroom_admin(pool, classroom_id, user_id).await?;

    // Build dynamic update
    let row = sqlx::query_as::<_, ClassroomRow>(
        r#"
        UPDATE classes SET
            name = COALESCE($2, name),
            description = COALESCE($3, description),
            max_students = COALESCE($4, max_students)
        WHERE id = $1
        RETURNING id, name, description, teacher_id AS owner_id, max_students AS max_members,
                  (SELECT COUNT(*)::int FROM class_members WHERE class_id = classes.id) AS member_count,
                  created_at, is_archived
        "#,
    )
    .bind(classroom_id)
    .bind(&payload.name)
    .bind(&payload.description)
    .bind(payload.max_members)
    .fetch_optional(pool)
    .await
    .map_err(|e| AppError::Internal(e.into()))?
    .ok_or_else(|| AppError::Http {
        status: axum::http::StatusCode::NOT_FOUND,
        message: "Classroom not found".to_string(),
    })?;

    Ok(ClassroomOut {
        id: row.id,
        name: row.name,
        description: row.description,
        owner_id: row.owner_id,
        max_members: row.max_members,
        member_count: row.member_count,
        created_at: row.created_at,
        is_archived: row.is_archived,
    })
}

/// DELETE /api/v1/classrooms/{id} — archive classroom.
pub async fn archive_classroom(
    pool: &PgPool,
    classroom_id: Uuid,
    user_id: Uuid,
) -> Result<(), AppError> {
    require_classroom_admin(pool, classroom_id, user_id).await?;

    let result = sqlx::query("UPDATE classes SET is_archived = true WHERE id = $1")
        .bind(classroom_id)
        .execute(pool)
        .await
        .map_err(|e| AppError::Internal(e.into()))?;

    if result.rows_affected() == 0 {
        return Err(AppError::Http {
            status: axum::http::StatusCode::NOT_FOUND,
            message: "Classroom not found".to_string(),
        });
    }
    Ok(())
}

/// GET /api/v1/classrooms/{id}/members — list members.
pub async fn list_members(
    pool: &PgPool,
    classroom_id: Uuid,
    user_id: Uuid,
) -> Result<Vec<ClassroomMemberOut>, AppError> {
    require_classroom_member(pool, classroom_id, user_id).await?;

    let rows = sqlx::query_as::<_, ClassroomMemberRow>(
        r#"
        SELECT cm.user_id, u.display_name, cm.role, cm.joined_at
        FROM class_members cm
        JOIN users u ON u.id = cm.user_id
        WHERE cm.class_id = $1
        ORDER BY cm.joined_at
        "#,
    )
    .bind(classroom_id)
    .fetch_all(pool)
    .await
    .map_err(|e| AppError::Internal(e.into()))?;

    Ok(rows
        .into_iter()
        .map(|r| ClassroomMemberOut {
            user_id: r.user_id,
            display_name: r.display_name,
            role: r.role,
            joined_at: r.joined_at,
        })
        .collect())
}

/// POST /api/v1/classrooms/{id}/members — add member.
pub async fn add_member(
    pool: &PgPool,
    classroom_id: Uuid,
    user_id: Uuid,
    payload: &AddMemberRequest,
) -> Result<ClassroomMemberOut, AppError> {
    require_classroom_admin(pool, classroom_id, user_id).await?;

    let role = payload.role.as_deref().unwrap_or("student");
    let now = Utc::now();

    // Check capacity
    let classroom = sqlx::query_as::<_, ClassroomRow>(
        "SELECT id, name, description, teacher_id AS owner_id, max_students AS max_members, (SELECT COUNT(*)::int FROM class_members WHERE class_id = $1) AS member_count, created_at, is_archived FROM classes WHERE id = $1",
    )
    .bind(classroom_id)
    .fetch_optional(pool)
    .await
    .map_err(|e| AppError::Internal(e.into()))?
    .ok_or_else(|| AppError::Http {
        status: axum::http::StatusCode::NOT_FOUND,
        message: "Classroom not found".to_string(),
    })?;

    if classroom.member_count >= classroom.max_members {
        return Err(AppError::Domain {
            status: axum::http::StatusCode::BAD_REQUEST,
            code: "CLASSROOM_FULL".to_string(),
            message: "Classroom has reached maximum capacity".to_string(),
            details: serde_json::json!({}),
        });
    }

    // Get user display name
    let user_row: (String,) = sqlx::query_as("SELECT display_name FROM users WHERE id = $1")
        .bind(payload.user_id)
        .fetch_optional(pool)
        .await
        .map_err(|e| AppError::Internal(e.into()))?
        .ok_or_else(|| AppError::Http {
            status: axum::http::StatusCode::NOT_FOUND,
            message: "User not found".to_string(),
        })?;

    // Insert member (conflict = already a member)
    sqlx::query(
        r#"
        INSERT INTO class_members (id, class_id, user_id, role, joined_at)
        VALUES ($1, $2, $3, $4, $5)
        "#,
    )
    .bind(Uuid::new_v4())
    .bind(classroom_id)
    .bind(payload.user_id)
    .bind(role)
    .bind(now)
    .execute(pool)
    .await
    .map_err(|e| {
        if let Some(db_err) = e.as_database_error() {
            if db_err.code().as_deref() == Some("23505") {
                return AppError::Domain {
                    status: axum::http::StatusCode::CONFLICT,
                    code: "ALREADY_MEMBER".to_string(),
                    message: "User is already a member of this classroom".to_string(),
                    details: serde_json::json!({}),
                };
            }
        }
        AppError::Internal(e.into())
    })?;

    // Update member count
    sqlx::query("UPDATE classes SET updated_at = NOW() WHERE id = $1")
        .bind(classroom_id)
        .execute(pool)
        .await
        .map_err(|e| AppError::Internal(e.into()))?;

    Ok(ClassroomMemberOut {
        user_id: payload.user_id,
        display_name: user_row.0,
        role: role.to_string(),
        joined_at: now,
    })
}

/// DELETE /api/v1/classrooms/{id}/members/{user_id} — remove member.
pub async fn remove_member(
    pool: &PgPool,
    classroom_id: Uuid,
    requesting_user_id: Uuid,
    target_user_id: Uuid,
) -> Result<(), AppError> {
    require_classroom_admin(pool, classroom_id, requesting_user_id).await?;

    let result = sqlx::query(
        "DELETE FROM class_members WHERE class_id = $1 AND user_id = $2",
    )
    .bind(classroom_id)
    .bind(target_user_id)
    .execute(pool)
    .await
    .map_err(|e| AppError::Internal(e.into()))?;

    if result.rows_affected() == 0 {
        return Err(AppError::Http {
            status: axum::http::StatusCode::NOT_FOUND,
            message: "Member not found".to_string(),
        });
    }

    // Update member count
    sqlx::query("UPDATE classes SET updated_at = NOW() WHERE id = $1")
        .bind(classroom_id)
        .execute(pool)
        .await
        .map_err(|e| AppError::Internal(e.into()))?;

    Ok(())
}

/// GET /api/v1/classrooms/{id}/lessons — classroom lessons.
pub async fn list_classroom_lessons(
    pool: &PgPool,
    classroom_id: Uuid,
    user_id: Uuid,
) -> Result<Vec<ClassroomLessonOut>, AppError> {
    require_classroom_member(pool, classroom_id, user_id).await?;

    let rows = sqlx::query_as::<_, ClassroomLessonRow>(
        r#"
        SELECT cl.id, cl.motif_id, m.name AS motif_name, cl.assigned_at,
               cl.due_date, COALESCE(cl.completed_count, 0) AS completed_count,
               (SELECT COUNT(*)::int FROM class_members WHERE class_id = cl.classroom_id) AS total_members
        FROM classroom_lessons cl
        JOIN motifs m ON m.id = cl.motif_id
        WHERE cl.classroom_id = $1
        ORDER BY cl.assigned_at DESC
        "#,
    )
    .bind(classroom_id)
    .fetch_all(pool)
    .await
    .map_err(|e| AppError::Internal(e.into()))?;

    Ok(rows
        .into_iter()
        .map(|r| ClassroomLessonOut {
            id: r.id,
            motif_id: r.motif_id,
            motif_name: r.motif_name,
            assigned_at: r.assigned_at,
            due_date: r.due_date,
            completed_count: r.completed_count,
            total_members: r.total_members,
        })
        .collect())
}

/// POST /api/v1/classrooms/{id}/lessons — assign lesson.
pub async fn assign_lesson(
    pool: &PgPool,
    classroom_id: Uuid,
    user_id: Uuid,
    payload: &AssignLessonRequest,
) -> Result<ClassroomLessonOut, AppError> {
    require_classroom_admin(pool, classroom_id, user_id).await?;

    let now = Utc::now();

    // Verify motif exists
    let motif_name: (String,) = sqlx::query_as("SELECT name FROM motifs WHERE id = $1 AND is_active = true")
        .bind(payload.motif_id)
        .fetch_optional(pool)
        .await
        .map_err(|e| AppError::Internal(e.into()))?
        .ok_or_else(|| AppError::Http {
            status: axum::http::StatusCode::NOT_FOUND,
            message: "Motif not found".to_string(),
        })?;

    let member_count: (i32,) = sqlx::query_as("SELECT (SELECT COUNT(*)::int FROM class_members WHERE class_id = $1)")
        .bind(classroom_id)
        .fetch_one(pool)
        .await
        .map_err(|e| AppError::Internal(e.into()))?;

    let id = Uuid::new_v4();
    sqlx::query(
        r#"
        INSERT INTO classroom_lessons (id, classroom_id, motif_id, assigned_at, due_date, completed_count)
        VALUES ($1, $2, $3, $4, $5, 0)
        "#,
    )
    .bind(id)
    .bind(classroom_id)
    .bind(payload.motif_id)
    .bind(now)
    .bind(payload.due_date)
    .execute(pool)
    .await
    .map_err(|e| AppError::Internal(e.into()))?;

    Ok(ClassroomLessonOut {
        id,
        motif_id: payload.motif_id,
        motif_name: motif_name.0,
        assigned_at: now,
        due_date: payload.due_date,
        completed_count: 0,
        total_members: member_count.0,
    })
}

/// GET /api/v1/classrooms/{id}/analytics — classroom analytics.
pub async fn get_classroom_analytics(
    pool: &PgPool,
    classroom_id: Uuid,
    user_id: Uuid,
) -> Result<ClassroomAnalyticsOut, AppError> {
    require_classroom_admin(pool, classroom_id, user_id).await?;

    let classroom = sqlx::query_as::<_, ClassroomRow>(
        "SELECT id, name, description, teacher_id AS owner_id, max_students AS max_members, (SELECT COUNT(*)::int FROM class_members WHERE class_id = $1) AS member_count, created_at, is_archived FROM classes WHERE id = $1",
    )
    .bind(classroom_id)
    .fetch_optional(pool)
    .await
    .map_err(|e| AppError::Internal(e.into()))?
    .ok_or_else(|| AppError::Http {
        status: axum::http::StatusCode::NOT_FOUND,
        message: "Classroom not found".to_string(),
    })?;

    // Active members in last 7 days
    let active_7d: (i64,) = sqlx::query_as(
        r#"
        SELECT COUNT(DISTINCT cm.user_id)
        FROM class_members cm
        JOIN users u ON u.id = cm.user_id
        WHERE cm.class_id = $1 AND u.last_active_at > NOW() - INTERVAL '7 days'
        "#,
    )
    .bind(classroom_id)
    .fetch_one(pool)
    .await
    .map_err(|e| AppError::Internal(e.into()))?;

    // Aggregate stats
    let stats: Option<(i64, f64, i64)> = sqlx::query_as(
        r#"
        SELECT
            COUNT(CASE WHEN up.status IN ('learned', 'mastered') THEN 1 END) AS lessons_completed,
            COALESCE(AVG(up.quiz_best_score), 0.0) AS avg_quiz_score,
            COALESCE(SUM(up.xp_earned), 0) AS total_xp
        FROM class_members cm
        JOIN user_progress up ON up.user_id = cm.user_id
        WHERE cm.class_id = $1
        "#,
    )
    .bind(classroom_id)
    .fetch_optional(pool)
    .await
    .map_err(|e| AppError::Internal(e.into()))?;

    let (lessons_completed, avg_quiz, total_xp) = stats.unwrap_or((0, 0.0, 0));

    // Top performers
    let performers = sqlx::query_as::<_, ClassroomPerformerRow>(
        r#"
        SELECT cm.user_id, u.display_name,
               COALESCE(SUM(up.xp_earned), 0)::int AS xp_earned,
               COUNT(CASE WHEN up.status IN ('learned', 'mastered') THEN 1 END)::int AS lessons_completed
        FROM class_members cm
        JOIN users u ON u.id = cm.user_id
        LEFT JOIN user_progress up ON up.user_id = cm.user_id
        WHERE cm.class_id = $1
        GROUP BY cm.user_id, u.display_name
        ORDER BY xp_earned DESC
        LIMIT 5
        "#,
    )
    .bind(classroom_id)
    .fetch_all(pool)
    .await
    .map_err(|e| AppError::Internal(e.into()))?;

    Ok(ClassroomAnalyticsOut {
        classroom_id,
        total_members: classroom.member_count,
        active_members_7d: active_7d.0 as i32,
        total_lessons_completed: lessons_completed as i32,
        average_quiz_score: avg_quiz,
        total_xp_earned: total_xp,
        top_performers: performers
            .into_iter()
            .map(|p| ClassroomPerformer {
                user_id: p.user_id,
                display_name: p.display_name,
                xp_earned: p.xp_earned,
                lessons_completed: p.lessons_completed,
            })
            .collect(),
    })
}
