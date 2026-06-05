//! Lesson, Motif, and Urn business logic.
//!
//! Phase 4 (Tasks 5.1–5.5): Lessons & Content migration.

use chrono::{DateTime, Duration, Utc};
use sqlx::PgPool;
use uuid::Uuid;

use crate::error::AppError;
use crate::models::lesson::*;

// ---------------------------------------------------------------------------
// Constants (matching Python's XP values)
// ---------------------------------------------------------------------------

const DISCOVERY_XP: i32 = 10;
const LESSON_XP: i32 = 25;

// ---------------------------------------------------------------------------
// Urn queries
// ---------------------------------------------------------------------------

/// List all urns with user progress counts.
pub async fn list_urns(pool: &PgPool, user_id: Uuid) -> Result<Vec<UrnListItem>, AppError> {
    let rows = sqlx::query_as::<_, UrnListRow>(
        r#"
        SELECT
            u.id, u.slug, u.name, u.model_url, u.thumbnail_url,
            u.display_order, u.is_demo,
            COALESCE(mc.motif_count, 0) AS motif_count,
            COALESCE(pc.discovered_count, 0) AS discovered_count,
            COALESCE(pc.learned_count, 0) AS learned_count,
            COALESCE(pc.mastered_count, 0) AS mastered_count
        FROM urns u
        LEFT JOIN (
            SELECT urn_id, COUNT(*) AS motif_count
            FROM motifs WHERE is_active = true
            GROUP BY urn_id
        ) mc ON mc.urn_id = u.id
        LEFT JOIN (
            SELECT m.urn_id,
                SUM(CASE WHEN up.status = 'discovered' THEN 1 ELSE 0 END) AS discovered_count,
                SUM(CASE WHEN up.status = 'learned' THEN 1 ELSE 0 END) AS learned_count,
                SUM(CASE WHEN up.status = 'mastered' THEN 1 ELSE 0 END) AS mastered_count
            FROM motifs m
            LEFT JOIN user_progress up ON up.motif_id = m.id AND up.user_id = $1
            WHERE m.is_active = true
            GROUP BY m.urn_id
        ) pc ON pc.urn_id = u.id
        ORDER BY u.display_order, u.name
        "#,
    )
    .bind(user_id)
    .fetch_all(pool)
    .await
    .map_err(|e| AppError::Internal(e.into()))?;

    Ok(rows
        .into_iter()
        .map(|r| UrnListItem {
            id: r.id,
            slug: r.slug,
            name: r.name,
            model_url: r.model_url,
            thumbnail_url: r.thumbnail_url,
            display_order: r.display_order,
            is_demo: r.is_demo,
            motif_count: r.motif_count,
            discovered_count: r.discovered_count,
            learned_count: r.learned_count,
            mastered_count: r.mastered_count,
        })
        .collect())
}

/// Get urn detail with motifs.
pub async fn get_urn_detail(
    pool: &PgPool,
    urn_slug: &str,
    user_id: Uuid,
) -> Result<UrnDetailResponse, AppError> {
    let urn_row = sqlx::query_as::<_, UrnDetailRow>(
        r#"
        SELECT id, slug, name, name_han, represents, description,
               model_url, thumbnail_url, display_order, is_demo
        FROM urns WHERE slug = $1
        "#,
    )
    .bind(urn_slug)
    .fetch_optional(pool)
    .await
    .map_err(|e| AppError::Internal(e.into()))?
    .ok_or_else(|| AppError::Http {
        status: axum::http::StatusCode::NOT_FOUND,
        message: "Urn not found".to_string(),
    })?;

    // Check if user can view drafts (admin/teacher)
    let can_view_drafts = check_can_view_drafts(pool, user_id).await;

    let motifs = sqlx::query_as::<_, MotifWithLessonRow>(
        r#"
        SELECT m.id, m.urn_id, m.mesh_name, m.name, m.name_en,
               m.category::text AS category, m.rarity::text AS rarity, m.pos_x, m.pos_y, m.pos_z,
               m.bounding_radius, m.thumbnail_url, m.silhouette_url,
               m.is_demo, m.display_order,
               lc.intro_text AS lesson_intro,
               lc.is_published AS lesson_published
        FROM motifs m
        LEFT JOIN lesson_content lc ON lc.motif_id = m.id
        WHERE m.urn_id = $1 AND m.is_active = true
        ORDER BY m.display_order NULLS LAST, m.name
        "#,
    )
    .bind(urn_row.id)
    .fetch_all(pool)
    .await
    .map_err(|e| AppError::Internal(e.into()))?;

    let motif_outs: Vec<MotifOut> = motifs
        .into_iter()
        .map(|m| MotifOut {
            id: m.id,
            urn_id: m.urn_id,
            mesh_name: m.mesh_name,
            name: m.name,
            name_en: m.name_en,
            category: m.category,
            rarity: m.rarity,
            pos_x: m.pos_x,
            pos_y: m.pos_y,
            pos_z: m.pos_z,
            bounding_radius: m.bounding_radius,
            thumbnail_url: m.thumbnail_url.clone(),
            silhouette_url: m.silhouette_url,
            is_demo: m.is_demo,
            display_order: m.display_order,
            lesson_intro: if m.lesson_published.unwrap_or(false) || can_view_drafts {
                m.lesson_intro
            } else {
                None
            },
        })
        .collect();

    Ok(UrnDetailResponse {
        urn: UrnDetailOut {
            id: urn_row.id,
            slug: urn_row.slug,
            name: urn_row.name,
            name_han: urn_row.name_han,
            represents: urn_row.represents,
            description: urn_row.description,
            model_url: urn_row.model_url,
            thumbnail_url: urn_row.thumbnail_url,
            display_order: urn_row.display_order,
            is_demo: urn_row.is_demo,
        },
        motifs: motif_outs,
    })
}

/// Get urn progress for a user.
pub async fn get_urn_progress(
    pool: &PgPool,
    urn_slug: &str,
    user_id: Uuid,
) -> Result<UrnProgressResponse, AppError> {
    let urn = sqlx::query_as::<_, UrnIdSlugRow>(
        "SELECT id, slug FROM urns WHERE slug = $1",
    )
    .bind(urn_slug)
    .fetch_optional(pool)
    .await
    .map_err(|e| AppError::Internal(e.into()))?
    .ok_or_else(|| AppError::Http {
        status: axum::http::StatusCode::NOT_FOUND,
        message: "Urn not found".to_string(),
    })?;

    let motif_progress = sqlx::query_as::<_, MotifProgressRow>(
        r#"
        SELECT m.id AS motif_id,
               COALESCE(up.status::text, 'hidden') AS status,
               up.discovered_at,
               up.lesson_viewed_at,
               up.learned_at,
               up.mastered_at,
               COALESCE(up.quiz_attempts, 0) AS quiz_attempts,
               COALESCE(up.quiz_best_score, 0) AS quiz_best_score,
               COALESCE(up.xp_earned, 0) AS xp_earned
        FROM motifs m
        LEFT JOIN user_progress up ON up.motif_id = m.id AND up.user_id = $1
        WHERE m.urn_id = $2 AND m.is_active = true
        "#,
    )
    .bind(user_id)
    .bind(urn.id)
    .fetch_all(pool)
    .await
    .map_err(|e| AppError::Internal(e.into()))?;

    Ok(UrnProgressResponse {
        urn_id: urn.id,
        urn_slug: urn.slug,
        motifs: motif_progress
            .into_iter()
            .map(|p| MotifProgressOut {
                motif_id: p.motif_id,
                status: p.status,
                discovered_at: p.discovered_at,
                lesson_viewed_at: p.lesson_viewed_at,
                learned_at: p.learned_at,
                mastered_at: p.mastered_at,
                quiz_attempts: p.quiz_attempts,
                quiz_best_score: p.quiz_best_score,
                xp_earned: p.xp_earned,
            })
            .collect(),
    })
}

// ---------------------------------------------------------------------------
// Motif queries
// ---------------------------------------------------------------------------

/// List motifs by urn name/slug.
pub async fn list_motifs_by_urn(
    pool: &PgPool,
    urn_name: &str,
    user_id: Uuid,
) -> Result<MotifsByUrnResponse, AppError> {
    let urn_row = sqlx::query_as::<_, UrnOutRow>(
        r#"
        SELECT id, slug, name, model_url, thumbnail_url
        FROM urns WHERE slug = $1 OR LOWER(name) = LOWER($1)
        "#,
    )
    .bind(urn_name)
    .fetch_optional(pool)
    .await
    .map_err(|e| AppError::Internal(e.into()))?
    .ok_or_else(|| AppError::Http {
        status: axum::http::StatusCode::NOT_FOUND,
        message: "Urn not found".to_string(),
    })?;

    let can_view_drafts = check_can_view_drafts(pool, user_id).await;

    let motifs = sqlx::query_as::<_, MotifWithLessonRow>(
        r#"
        SELECT m.id, m.urn_id, m.mesh_name, m.name, m.name_en,
               m.category::text AS category, m.rarity::text AS rarity, m.pos_x, m.pos_y, m.pos_z,
               m.bounding_radius, m.thumbnail_url, m.silhouette_url,
               m.is_demo, m.display_order,
               lc.intro_text AS lesson_intro,
               lc.is_published AS lesson_published
        FROM motifs m
        LEFT JOIN lesson_content lc ON lc.motif_id = m.id
        WHERE m.urn_id = $1 AND m.is_active = true
        ORDER BY m.display_order NULLS LAST, m.name
        "#,
    )
    .bind(urn_row.id)
    .fetch_all(pool)
    .await
    .map_err(|e| AppError::Internal(e.into()))?;

    let motif_outs: Vec<MotifOut> = motifs
        .into_iter()
        .map(|m| MotifOut {
            id: m.id,
            urn_id: m.urn_id,
            mesh_name: m.mesh_name,
            name: m.name,
            name_en: m.name_en,
            category: m.category,
            rarity: m.rarity,
            pos_x: m.pos_x,
            pos_y: m.pos_y,
            pos_z: m.pos_z,
            bounding_radius: m.bounding_radius,
            thumbnail_url: m.thumbnail_url.clone(),
            silhouette_url: m.silhouette_url,
            is_demo: m.is_demo,
            display_order: m.display_order,
            lesson_intro: if m.lesson_published.unwrap_or(false) || can_view_drafts {
                m.lesson_intro
            } else {
                None
            },
        })
        .collect();

    Ok(MotifsByUrnResponse {
        urn: UrnOut {
            id: urn_row.id,
            slug: urn_row.slug,
            name: urn_row.name,
            model_url: urn_row.model_url,
            thumbnail_url: urn_row.thumbnail_url,
        },
        motifs: motif_outs,
    })
}

/// Get motif detail with lesson, quiz questions, and user progress.
pub async fn get_motif_detail(
    pool: &PgPool,
    motif_id: Uuid,
    user_id: Uuid,
) -> Result<MotifDetailOut, AppError> {
    // Fetch motif with urn
    let motif = sqlx::query_as::<_, MotifDetailRow>(
        r#"
        SELECT m.id, m.urn_id, m.mesh_name, m.name, m.name_en,
               m.category::text AS category, m.rarity::text AS rarity, m.thumbnail_url, m.silhouette_url,
               m.is_demo, m.display_order, m.content_rating::text AS content_rating,
               u.id AS urn_id_2, u.slug AS urn_slug, u.name AS urn_name,
               u.model_url AS urn_model_url, u.thumbnail_url AS urn_thumbnail_url
        FROM motifs m
        JOIN urns u ON u.id = m.urn_id
        WHERE m.id = $1 AND m.is_active = true
        "#,
    )
    .bind(motif_id)
    .fetch_optional(pool)
    .await
    .map_err(|e| AppError::Internal(e.into()))?
    .ok_or_else(|| AppError::Http {
        status: axum::http::StatusCode::NOT_FOUND,
        message: "Motif not found".to_string(),
    })?;

    // Check content rating access
    let user_role = get_user_role(pool, user_id).await;
    let allowed_ratings = get_allowed_content_ratings(&user_role);
    if !allowed_ratings.contains(&motif.content_rating.as_str()) {
        return Err(AppError::Http {
            status: axum::http::StatusCode::FORBIDDEN,
            message: "You do not have access to this content. Please verify your age."
                .to_string(),
        });
    }

    let can_view_drafts = user_role == "admin" || user_role == "teacher";

    // Fetch lesson content
    let lesson_row = sqlx::query_as::<_, LessonContentRow>(
        r#"
        SELECT intro_text, description, historical_context, symbolism,
               fun_fact, is_ai_generated, audio_narration_url,
               additional_images, video_url, is_published
        FROM lesson_content WHERE motif_id = $1
        "#,
    )
    .bind(motif_id)
    .fetch_optional(pool)
    .await
    .map_err(|e| AppError::Internal(e.into()))?;

    let lesson_out = lesson_row.and_then(|l| {
        if l.is_published || can_view_drafts {
            Some(LessonContentOut {
                intro_text: l.intro_text,
                description: l.description,
                historical_context: l.historical_context,
                symbolism: l.symbolism,
                fun_fact: l.fun_fact,
                is_ai_generated: l.is_ai_generated,
                audio_narration_url: l.audio_narration_url,
                additional_images: l.additional_images,
                video_url: l.video_url,
            })
        } else {
            None
        }
    });

    // Fetch quiz questions
    let quiz_rows = sqlx::query_as::<_, QuizQuestionRow>(
        r#"
        SELECT id, question_type::text AS question_type, question_text, options,
               target_mesh_name, difficulty, explanation,
               is_active, is_published
        FROM quiz_questions
        WHERE motif_id = $1 AND is_active = true
        "#,
    )
    .bind(motif_id)
    .fetch_all(pool)
    .await
    .map_err(|e| AppError::Internal(e.into()))?;

    let quiz_questions: Vec<MotifQuizQuestionOut> = quiz_rows
        .into_iter()
        .filter(|q| q.is_published || can_view_drafts)
        .map(|q| MotifQuizQuestionOut {
            id: q.id,
            question_type: q.question_type,
            question_text: q.question_text,
            options: q.options,
            target_mesh_name: q.target_mesh_name,
            difficulty: q.difficulty.unwrap_or(1).max(1),
            explanation: q.explanation.and_then(|e| {
                let trimmed = e.trim().to_string();
                if trimmed.is_empty() { None } else { Some(trimmed) }
            }),
            image_url: None,
        })
        .collect();

    // Fetch user progress
    let progress_row = sqlx::query_as::<_, UserProgressRow>(
        r#"
        SELECT id, user_id, motif_id, status::text AS status, discovered_at,
               learned_at, mastered_at, xp_earned, quiz_best_score
        FROM user_progress
        WHERE user_id = $1 AND motif_id = $2
        "#,
    )
    .bind(user_id)
    .bind(motif_id)
    .fetch_optional(pool)
    .await
    .map_err(|e| AppError::Internal(e.into()))?;

    let progress_out = progress_row.map(|p| UserProgressDetailOut {
        id: p.id,
        user_id: p.user_id,
        motif_id: p.motif_id,
        status: p.status,
        discovered_at: p.discovered_at,
        learned_at: p.learned_at,
        mastered_at: p.mastered_at,
        xp_earned: p.xp_earned,
        quiz_best_score: p.quiz_best_score,
    });

    Ok(MotifDetailOut {
        id: motif.id,
        urn: UrnOut {
            id: motif.urn_id,
            slug: motif.urn_slug,
            name: motif.urn_name,
            model_url: motif.urn_model_url,
            thumbnail_url: motif.urn_thumbnail_url,
        },
        mesh_name: motif.mesh_name,
        name: motif.name,
        name_en: motif.name_en,
        category: motif.category,
        rarity: motif.rarity,
        thumbnail_url: motif.thumbnail_url.clone(),
        silhouette_url: motif.silhouette_url,
        image_url: motif.thumbnail_url,
        is_demo: motif.is_demo,
        display_order: motif.display_order,
        lesson: lesson_out,
        quiz_question_count: quiz_questions.len(),
        quiz_questions,
        progress: progress_out,
    })
}

// ---------------------------------------------------------------------------
// Complete lesson (Task 5.5)
// ---------------------------------------------------------------------------

/// Complete a lesson: mark as learned, award XP, update streak atomically.
pub async fn complete_lesson(
    pool: &PgPool,
    motif_id: Uuid,
    user_id: Uuid,
) -> Result<LessonCompleteResponse, AppError> {
    // Verify motif exists and is active
    let motif_row = sqlx::query_as::<_, MotifBasicRow>(
        "SELECT id, is_demo, urn_id FROM motifs WHERE id = $1 AND is_active = true",
    )
    .bind(motif_id)
    .fetch_optional(pool)
    .await
    .map_err(|e| AppError::Internal(e.into()))?
    .ok_or_else(|| AppError::Http {
        status: axum::http::StatusCode::NOT_FOUND,
        message: "Motif not found".to_string(),
    })?;

    // Check user role for guest restriction
    let user_role = get_user_role(pool, user_id).await;
    if user_role == "guest" && !motif_row.is_demo {
        return Err(AppError::Http {
            status: axum::http::StatusCode::FORBIDDEN,
            message: "Guests can only learn demo motifs".to_string(),
        });
    }

    // Check lesson is published (unless admin/teacher)
    let can_view_drafts = user_role == "admin" || user_role == "teacher";
    if !can_view_drafts {
        let lesson_published: Option<(bool,)> = sqlx::query_as(
            "SELECT is_published FROM lesson_content WHERE motif_id = $1",
        )
        .bind(motif_id)
        .fetch_optional(pool)
        .await
        .map_err(|e| AppError::Internal(e.into()))?;

        if let Some((published,)) = lesson_published {
            if !published {
                return Err(AppError::Http {
                    status: axum::http::StatusCode::FORBIDDEN,
                    message: "Lesson not published".to_string(),
                });
            }
        }
    }

    let now = Utc::now();
    let target_xp = DISCOVERY_XP + LESSON_XP;

    // Use a transaction for atomicity
    let mut tx = pool.begin().await.map_err(|e| AppError::Internal(e.into()))?;

    // Check existing progress
    let progress = sqlx::query_as::<_, ProgressUpdateRow>(
        r#"
        SELECT id, status::text AS status, xp_earned, lesson_viewed_at, learned_at, discovered_at
        FROM user_progress
        WHERE user_id = $1 AND motif_id = $2
        FOR UPDATE
        "#,
    )
    .bind(user_id)
    .bind(motif_id)
    .fetch_optional(&mut *tx)
    .await
    .map_err(|e| AppError::Internal(e.into()))?;

    #[allow(unused_assignments)]
    let mut xp_awarded: i32 = 0;
    let final_status: String;
    let final_lesson_viewed_at: Option<DateTime<Utc>>;
    let final_learned_at: Option<DateTime<Utc>>;

    if let Some(p) = progress {
        // Update existing progress
        let new_status = match p.status.as_str() {
            "hidden" | "discovered" => "learned",
            other => other,
        };
        final_status = new_status.to_string();

        let learned_at = if new_status == "learned" && p.learned_at.is_none() {
            Some(now)
        } else {
            p.learned_at
        };
        final_learned_at = learned_at;
        final_lesson_viewed_at = p.lesson_viewed_at.or(Some(now));

        let delta = if p.xp_earned < target_xp {
            target_xp - p.xp_earned
        } else {
            0
        };
        xp_awarded = delta;

        sqlx::query(
            r#"
            UPDATE user_progress
            SET status = $1, learned_at = COALESCE(learned_at, $2),
                discovered_at = COALESCE(discovered_at, $2),
                lesson_viewed_at = COALESCE(lesson_viewed_at, $2),
                xp_earned = GREATEST(xp_earned, $3)
            WHERE user_id = $4 AND motif_id = $5
            "#,
        )
        .bind(&final_status)
        .bind(now)
        .bind(target_xp)
        .bind(user_id)
        .bind(motif_id)
        .execute(&mut *tx)
        .await
        .map_err(|e| AppError::Internal(e.into()))?;
    } else {

        // Create new progress entry
        final_status = "learned".to_string();
        final_learned_at = Some(now);
        final_lesson_viewed_at = Some(now);
        xp_awarded = target_xp;

        sqlx::query(
            r#"
            INSERT INTO user_progress
                (id, user_id, motif_id, status, discovered_at,
                 lesson_viewed_at, learned_at, xp_earned)
            VALUES ($1, $2, $3, 'learned', $4, $4, $4, $5)
            "#,
        )
        .bind(Uuid::new_v4())
        .bind(user_id)
        .bind(motif_id)
        .bind(now)
        .bind(target_xp)
        .execute(&mut *tx)
        .await
        .map_err(|e| AppError::Internal(e.into()))?;
    }

    // Update user XP and streak
    // Apply comeback bonus multiplier if active.
    let xp_awarded = if xp_awarded > 0 {
        crate::services::streak_comeback_service::apply_xp_multiplier(
            &mut tx, user_id, xp_awarded,
        )
        .await?
    } else {
        xp_awarded
    };

    if xp_awarded > 0 {
        sqlx::query(
            "UPDATE users SET total_xp = total_xp + $1, last_active_at = $2 WHERE id = $3",
        )
        .bind(xp_awarded)
        .bind(now)
        .bind(user_id)
        .execute(&mut *tx)
        .await
        .map_err(|e| AppError::Internal(e.into()))?;
    }

    // Update streak
    update_streak(&mut tx, user_id, now).await?;

    tx.commit().await.map_err(|e| AppError::Internal(e.into()))?;

    // Best-effort Phoenix award (outside the transaction so it cannot block
    // the lesson-complete path if it fails).
    let _ = crate::services::streak_comeback_service::award_phoenix_if_eligible(
        pool, user_id,
    )
    .await;

    // Fetch final total_xp
    let total_xp: (i32,) = sqlx::query_as("SELECT total_xp FROM users WHERE id = $1")
        .bind(user_id)
        .fetch_one(pool)
        .await
        .map_err(|e| AppError::Internal(e.into()))?;

    Ok(LessonCompleteResponse {
        user_id,
        motif_id,
        status: final_status,
        lesson_viewed_at: final_lesson_viewed_at,
        learned_at: final_learned_at,
        xp_awarded,
        total_xp: total_xp.0,
    })
}

// ---------------------------------------------------------------------------
// Cache manifest (Task 5.4)
// ---------------------------------------------------------------------------

/// Get cache manifest of lessons available for offline caching.
pub async fn get_cache_manifest(
    pool: &PgPool,
    user_id: Uuid,
) -> Result<CacheManifestOut, AppError> {
    // Get published lessons with motif info
    let lessons = sqlx::query_as::<_, CacheManifestRow>(
        r#"
        SELECT lc.id AS lesson_id, lc.motif_id, m.name AS motif_name,
               lc.version, lc.audio_narration_url, lc.video_url,
               lc.additional_images, m.thumbnail_url, m.silhouette_url
        FROM lesson_content lc
        JOIN motifs m ON m.id = lc.motif_id AND m.is_active = true
        WHERE lc.is_published = true
        ORDER BY lc.updated_at DESC
        "#,
    )
    .fetch_all(pool)
    .await
    .map_err(|e| AppError::Internal(e.into()))?;

    // Get user progress for priority calculation
    let progress_map: std::collections::HashMap<Uuid, String> =
        sqlx::query_as::<_, (Uuid, String)>(
            "SELECT motif_id, status::text AS status FROM user_progress WHERE user_id = $1",
        )
        .bind(user_id)
        .fetch_all(pool)
        .await
        .map_err(|e| AppError::Internal(e.into()))?
        .into_iter()
        .collect();

    let mut items = Vec::new();
    let mut total_size: i64 = 0;

    for lesson in lessons {
        let priority = match progress_map.get(&lesson.motif_id).map(|s| s.as_str()) {
            Some("discovered") | Some("learned") => 1,
            Some("mastered") => 3,
            _ => 2,
        };

        let mut file_urls = Vec::new();
        let mut lesson_size: i64 = 5000; // base content estimate

        if let Some(ref url) = lesson.audio_narration_url {
            file_urls.push(CacheFileInfo {
                url: url.clone(),
                file_type: "audio".to_string(),
                size_bytes: 500_000,
            });
            lesson_size += 500_000;
        }
        if let Some(ref url) = lesson.video_url {
            file_urls.push(CacheFileInfo {
                url: url.clone(),
                file_type: "video".to_string(),
                size_bytes: 5_000_000,
            });
            lesson_size += 5_000_000;
        }
        if let Some(ref imgs) = lesson.additional_images {
            if let Some(arr) = imgs.as_array() {
                for img in arr {
                    if let Some(url) = img.as_str() {
                        file_urls.push(CacheFileInfo {
                            url: url.to_string(),
                            file_type: "image".to_string(),
                            size_bytes: 100_000,
                        });
                        lesson_size += 100_000;
                    }
                }
            }
        }
        if let Some(ref url) = lesson.thumbnail_url {
            file_urls.push(CacheFileInfo {
                url: url.clone(),
                file_type: "image".to_string(),
                size_bytes: 50_000,
            });
            lesson_size += 50_000;
        }
        if let Some(ref url) = lesson.silhouette_url {
            file_urls.push(CacheFileInfo {
                url: url.clone(),
                file_type: "image".to_string(),
                size_bytes: 30_000,
            });
            lesson_size += 30_000;
        }

        total_size += lesson_size;
        items.push(CacheManifestItem {
            lesson_id: lesson.lesson_id,
            motif_id: lesson.motif_id,
            motif_name: lesson.motif_name.clone(),
            title: lesson.motif_name,
            version: lesson.version,
            file_urls,
            total_size_bytes: lesson_size,
            priority,
        });
    }

    // Sort by priority then name
    items.sort_by(|a, b| a.priority.cmp(&b.priority).then(a.motif_name.cmp(&b.motif_name)));

    Ok(CacheManifestOut {
        lessons: items,
        total_size_bytes: total_size,
        recommended_cache_size_bytes: 50 * 1024 * 1024, // 50MB
    })
}

// ---------------------------------------------------------------------------
// Lesson cache CRUD (Task 5.4)
// ---------------------------------------------------------------------------

/// Mark a lesson as cached.
pub async fn mark_lesson_cached(
    pool: &PgPool,
    lesson_id: Uuid,
    user_id: Uuid,
    payload: &LessonCacheIn,
) -> Result<LessonCacheOut, AppError> {
    // Verify lesson exists
    let exists: Option<(Uuid,)> =
        sqlx::query_as("SELECT id FROM lesson_content WHERE id = $1")
            .bind(lesson_id)
            .fetch_optional(pool)
            .await
            .map_err(|e| AppError::Internal(e.into()))?;

    if exists.is_none() {
        return Err(AppError::Http {
            status: axum::http::StatusCode::NOT_FOUND,
            message: "Lesson not found".to_string(),
        });
    }

    let now = Utc::now();
    let expires = now + Duration::days(30);

    // Upsert cache entry
    let row = sqlx::query_as::<_, LessonCacheRow>(
        r#"
        INSERT INTO lesson_caches (id, user_id, lesson_id, cached_at,
            cache_version, file_size_bytes, is_valid, expires_at)
        VALUES ($1, $2, $3, $4, $5, $6, true, $7)
        ON CONFLICT (user_id, lesson_id)
        DO UPDATE SET cached_at = $4, cache_version = $5,
            file_size_bytes = $6, is_valid = true, expires_at = $7
        RETURNING id, user_id, lesson_id, cached_at, cache_version,
            file_size_bytes, is_valid, expires_at
        "#,
    )
    .bind(Uuid::new_v4())
    .bind(user_id)
    .bind(lesson_id)
    .bind(now)
    .bind(payload.cache_version)
    .bind(payload.file_size_bytes)
    .bind(expires)
    .fetch_one(pool)
    .await
    .map_err(|e| AppError::Internal(e.into()))?;

    Ok(LessonCacheOut {
        id: row.id,
        user_id: row.user_id,
        lesson_id: row.lesson_id,
        cached_at: row.cached_at,
        cache_version: row.cache_version,
        file_size_bytes: row.file_size_bytes,
        is_valid: row.is_valid,
        expires_at: row.expires_at,
    })
}

/// Remove a lesson from user's cache.
pub async fn remove_cached_lesson(
    pool: &PgPool,
    lesson_id: Uuid,
    user_id: Uuid,
) -> Result<(), AppError> {
    let result = sqlx::query(
        "DELETE FROM lesson_caches WHERE user_id = $1 AND lesson_id = $2",
    )
    .bind(user_id)
    .bind(lesson_id)
    .execute(pool)
    .await
    .map_err(|e| AppError::Internal(e.into()))?;

    if result.rows_affected() == 0 {
        return Err(AppError::Http {
            status: axum::http::StatusCode::NOT_FOUND,
            message: "Cached lesson not found".to_string(),
        });
    }
    Ok(())
}

/// Get all cached lessons for a user.
pub async fn get_cached_lessons(
    pool: &PgPool,
    user_id: Uuid,
) -> Result<Vec<LessonCacheOut>, AppError> {
    let rows = sqlx::query_as::<_, LessonCacheRow>(
        r#"
        SELECT id, user_id, lesson_id, cached_at, cache_version,
               file_size_bytes, is_valid, expires_at
        FROM lesson_caches
        WHERE user_id = $1
        ORDER BY cached_at DESC
        "#,
    )
    .bind(user_id)
    .fetch_all(pool)
    .await
    .map_err(|e| AppError::Internal(e.into()))?;

    Ok(rows
        .into_iter()
        .map(|r| LessonCacheOut {
            id: r.id,
            user_id: r.user_id,
            lesson_id: r.lesson_id,
            cached_at: r.cached_at,
            cache_version: r.cache_version,
            file_size_bytes: r.file_size_bytes,
            is_valid: r.is_valid,
            expires_at: r.expires_at,
        })
        .collect())
}

// ---------------------------------------------------------------------------
// Next lesson, prerequisites, is-unlocked, sequence (Task 5.4)
// ---------------------------------------------------------------------------

/// Get the next recommended lesson for the user.
pub async fn get_next_lesson(
    pool: &PgPool,
    user_id: Uuid,
    urn_id: Option<Uuid>,
) -> Result<NextLessonOut, AppError> {
    // Find the first lesson the user hasn't completed yet, ordered by difficulty
    let row = sqlx::query_as::<_, NextLessonRow>(
        r#"
        SELECT lc.id AS lesson_id, m.id AS motif_id, m.name AS motif_name,
               m.mesh_name AS motif_slug, u.id AS urn_id, u.name AS urn_name,
               lc.difficulty_level, lc.estimated_time_minutes
        FROM lesson_content lc
        JOIN motifs m ON m.id = lc.motif_id AND m.is_active = true
        JOIN urns u ON u.id = m.urn_id
        LEFT JOIN user_progress up ON up.motif_id = m.id AND up.user_id = $1
        WHERE lc.is_published = true
          AND (up.status IS NULL OR up.status NOT IN ('learned', 'mastered'))
          AND ($2::uuid IS NULL OR m.urn_id = $2)
        ORDER BY lc.difficulty_level NULLS LAST, m.display_order NULLS LAST, m.name
        LIMIT 1
        "#,
    )
    .bind(user_id)
    .bind(urn_id)
    .fetch_optional(pool)
    .await
    .map_err(|e| AppError::Internal(e.into()))?;

    match row {
        Some(r) => {
            // Check if this lesson has prerequisites
            let has_prereqs: (i64,) = sqlx::query_as(
                "SELECT COUNT(*) FROM lesson_prerequisites WHERE lesson_id = $1",
            )
            .bind(r.lesson_id)
            .fetch_one(pool)
            .await
            .map_err(|e| AppError::Internal(e.into()))?;

            Ok(NextLessonOut {
                lesson_id: Some(r.lesson_id),
                motif_id: Some(r.motif_id),
                motif_name: Some(r.motif_name),
                motif_slug: Some(r.motif_slug),
                urn_id: Some(r.urn_id),
                urn_name: Some(r.urn_name),
                difficulty_level: r.difficulty_level,
                estimated_time_minutes: r.estimated_time_minutes,
                reason: "next_in_sequence".to_string(),
                has_prerequisites: has_prereqs.0 > 0,
                progress_status: None,
            })
        }
        None => Ok(NextLessonOut {
            lesson_id: None,
            motif_id: None,
            motif_name: None,
            motif_slug: None,
            urn_id,
            urn_name: None,
            difficulty_level: None,
            estimated_time_minutes: None,
            reason: "no_lessons_available".to_string(),
            has_prerequisites: false,
            progress_status: None,
        }),
    }
}

/// Get prerequisites for a lesson.
pub async fn get_lesson_prerequisites(
    pool: &PgPool,
    lesson_id: Uuid,
    user_id: Uuid,
) -> Result<LessonPrerequisitesOut, AppError> {
    // Verify lesson exists
    let exists: Option<(Uuid,)> =
        sqlx::query_as("SELECT id FROM lesson_content WHERE id = $1")
            .bind(lesson_id)
            .fetch_optional(pool)
            .await
            .map_err(|e| AppError::Internal(e.into()))?;

    if exists.is_none() {
        return Err(AppError::Http {
            status: axum::http::StatusCode::NOT_FOUND,
            message: "Lesson not found".to_string(),
        });
    }

    let prereqs = sqlx::query_as::<_, PrerequisiteRow>(
        r#"
        SELECT lp.prerequisite_lesson_id AS id, lc.motif_id,
               m.name AS motif_name, m.mesh_name AS motif_slug,
               lc.difficulty_level, lc.estimated_time_minutes,
               lp.is_strict,
               CASE WHEN up.status IN ('learned', 'mastered') THEN true
                    ELSE false END AS is_completed
        FROM lesson_prerequisites lp
        JOIN lesson_content lc ON lc.id = lp.prerequisite_lesson_id
        JOIN motifs m ON m.id = lc.motif_id
        LEFT JOIN user_progress up ON up.motif_id = m.id AND up.user_id = $1
        WHERE lp.lesson_id = $2
        "#,
    )
    .bind(user_id)
    .bind(lesson_id)
    .fetch_all(pool)
    .await
    .map_err(|e| AppError::Internal(e.into()))?;

    let all_met = prereqs
        .iter()
        .filter(|p| p.is_strict)
        .all(|p| p.is_completed);

    Ok(LessonPrerequisitesOut {
        lesson_id,
        prerequisites: prereqs
            .into_iter()
            .map(|p| PrerequisiteLessonInfo {
                id: p.id,
                motif_id: p.motif_id,
                motif_name: p.motif_name,
                motif_slug: p.motif_slug,
                difficulty_level: p.difficulty_level,
                estimated_time_minutes: p.estimated_time_minutes,
                is_strict: p.is_strict,
                is_completed: p.is_completed,
            })
            .collect(),
        all_prerequisites_met: all_met,
    })
}

/// Check if a lesson is unlocked for the user.
pub async fn is_lesson_unlocked(
    pool: &PgPool,
    lesson_id: Uuid,
    user_id: Uuid,
) -> Result<LessonUnlockStatusOut, AppError> {
    // Verify lesson exists
    let exists: Option<(Uuid,)> =
        sqlx::query_as("SELECT id FROM lesson_content WHERE id = $1")
            .bind(lesson_id)
            .fetch_optional(pool)
            .await
            .map_err(|e| AppError::Internal(e.into()))?;

    if exists.is_none() {
        return Err(AppError::Http {
            status: axum::http::StatusCode::NOT_FOUND,
            message: "Lesson not found".to_string(),
        });
    }

    // Get strict prerequisites that are NOT completed
    let missing_strict = sqlx::query_as::<_, PrerequisiteRow>(
        r#"
        SELECT lp.prerequisite_lesson_id AS id, lc.motif_id,
               m.name AS motif_name, m.mesh_name AS motif_slug,
               lc.difficulty_level, lc.estimated_time_minutes,
               lp.is_strict,
               false AS is_completed
        FROM lesson_prerequisites lp
        JOIN lesson_content lc ON lc.id = lp.prerequisite_lesson_id
        JOIN motifs m ON m.id = lc.motif_id
        LEFT JOIN user_progress up ON up.motif_id = m.id AND up.user_id = $1
        WHERE lp.lesson_id = $2 AND lp.is_strict = true
          AND (up.status IS NULL OR up.status NOT IN ('learned', 'mastered'))
        "#,
    )
    .bind(user_id)
    .bind(lesson_id)
    .fetch_all(pool)
    .await
    .map_err(|e| AppError::Internal(e.into()))?;

    // Get recommended prerequisites that are NOT completed
    let missing_recommended = sqlx::query_as::<_, PrerequisiteRow>(
        r#"
        SELECT lp.prerequisite_lesson_id AS id, lc.motif_id,
               m.name AS motif_name, m.mesh_name AS motif_slug,
               lc.difficulty_level, lc.estimated_time_minutes,
               lp.is_strict,
               false AS is_completed
        FROM lesson_prerequisites lp
        JOIN lesson_content lc ON lc.id = lp.prerequisite_lesson_id
        JOIN motifs m ON m.id = lc.motif_id
        LEFT JOIN user_progress up ON up.motif_id = m.id AND up.user_id = $1
        WHERE lp.lesson_id = $2 AND lp.is_strict = false
          AND (up.status IS NULL OR up.status NOT IN ('learned', 'mastered'))
        "#,
    )
    .bind(user_id)
    .bind(lesson_id)
    .fetch_all(pool)
    .await
    .map_err(|e| AppError::Internal(e.into()))?;

    let is_unlocked = missing_strict.is_empty();

    Ok(LessonUnlockStatusOut {
        lesson_id,
        is_unlocked,
        missing_prerequisites: missing_strict
            .into_iter()
            .map(|p| PrerequisiteLessonInfo {
                id: p.id,
                motif_id: p.motif_id,
                motif_name: p.motif_name,
                motif_slug: p.motif_slug,
                difficulty_level: p.difficulty_level,
                estimated_time_minutes: p.estimated_time_minutes,
                is_strict: true,
                is_completed: false,
            })
            .collect(),
        recommended_prerequisites: missing_recommended
            .into_iter()
            .map(|p| PrerequisiteLessonInfo {
                id: p.id,
                motif_id: p.motif_id,
                motif_name: p.motif_name,
                motif_slug: p.motif_slug,
                difficulty_level: p.difficulty_level,
                estimated_time_minutes: p.estimated_time_minutes,
                is_strict: false,
                is_completed: false,
            })
            .collect(),
    })
}

/// Get the full learning sequence for the user.
pub async fn get_lesson_sequence(
    pool: &PgPool,
    user_id: Uuid,
    urn_id: Option<Uuid>,
) -> Result<LessonSequenceOut, AppError> {
    // Get urn name if urn_id provided
    let urn_name: Option<String> = if let Some(uid) = urn_id {
        sqlx::query_as::<_, (String,)>("SELECT name FROM urns WHERE id = $1")
            .bind(uid)
            .fetch_optional(pool)
            .await
            .map_err(|e| AppError::Internal(e.into()))?
            .map(|r| r.0)
    } else {
        None
    };

    let sequence_rows = sqlx::query_as::<_, SequenceRow>(
        r#"
        SELECT lc.id AS lesson_id, m.id AS motif_id, m.name AS motif_name,
               m.mesh_name AS motif_slug, u.id AS urn_id, u.name AS urn_name,
               lc.difficulty_level, lc.estimated_time_minutes,
               COALESCE(up.status::text, 'hidden') AS progress_status
        FROM lesson_content lc
        JOIN motifs m ON m.id = lc.motif_id AND m.is_active = true
        JOIN urns u ON u.id = m.urn_id
        LEFT JOIN user_progress up ON up.motif_id = m.id AND up.user_id = $1
        WHERE lc.is_published = true
          AND ($2::uuid IS NULL OR m.urn_id = $2)
        ORDER BY lc.difficulty_level NULLS LAST, m.display_order NULLS LAST, m.name
        "#,
    )
    .bind(user_id)
    .bind(urn_id)
    .fetch_all(pool)
    .await
    .map_err(|e| AppError::Internal(e.into()))?;

    let total_lessons = sequence_rows.len() as i32;
    let mut completed_lessons = 0;
    let mut current_position = 0;
    let mut found_current = false;

    let sequence: Vec<LessonSequenceItem> = sequence_rows
        .into_iter()
        .enumerate()
        .map(|(i, r)| {
            let is_completed =
                r.progress_status == "learned" || r.progress_status == "mastered";
            if is_completed {
                completed_lessons += 1;
            }
            if !is_completed && !found_current {
                current_position = (i + 1) as i32;
                found_current = true;
            }
            LessonSequenceItem {
                lesson_id: r.lesson_id,
                motif_id: r.motif_id,
                motif_name: Some(r.motif_name),
                motif_slug: Some(r.motif_slug),
                urn_id: Some(r.urn_id),
                urn_name: Some(r.urn_name),
                difficulty_level: r.difficulty_level,
                estimated_time_minutes: r.estimated_time_minutes,
                is_unlocked: true, // simplified; full check would query prereqs
                is_completed,
                progress_status: Some(r.progress_status),
                position: (i + 1) as i32,
            }
        })
        .collect();

    if !found_current && total_lessons > 0 {
        current_position = total_lessons + 1; // all completed
    }

    Ok(LessonSequenceOut {
        urn_id,
        urn_name,
        total_lessons,
        completed_lessons,
        current_position,
        sequence,
    })
}

// ---------------------------------------------------------------------------
// Helper functions
// ---------------------------------------------------------------------------

/// Check if user can view draft content (admin or teacher).
async fn check_can_view_drafts(pool: &PgPool, user_id: Uuid) -> bool {
    let role = get_user_role(pool, user_id).await;
    role == "admin" || role == "teacher"
}

/// Get user role from DB.
async fn get_user_role(pool: &PgPool, user_id: Uuid) -> String {
    sqlx::query_as::<_, (String,)>("SELECT role::text FROM users WHERE id = $1")
        .bind(user_id)
        .fetch_optional(pool)
        .await
        .ok()
        .flatten()
        .map(|r| r.0)
        .unwrap_or_else(|| "user".to_string())
}

/// Get allowed content ratings based on user role/age verification.
fn get_allowed_content_ratings(role: &str) -> Vec<&'static str> {
    match role {
        "admin" | "teacher" => vec!["everyone", "teen", "mature"],
        _ => vec!["everyone"],
    }
}

/// Update user streak in a transaction.
///
/// New behavior (streak-repair-economy):
/// - On a multi-day gap, if `streak_freezes > 0`, consume one freeze and
///   preserve `current_streak`.
/// - Otherwise, capture the prior streak into `user_streak_history` and
///   reset `current_streak` to 1 (today counts as the start of a new streak).
async fn update_streak(
    tx: &mut sqlx::Transaction<'_, sqlx::Postgres>,
    user_id: Uuid,
    now: DateTime<Utc>,
) -> Result<(), AppError> {
    // Per-user advisory lock — prevents concurrent double-update or
    // double-reset under request retry.
    sqlx::query("SELECT pg_advisory_xact_lock(hashtextextended($1::text, 0))")
        .bind(user_id)
        .execute(&mut **tx)
        .await
        .map_err(|e| AppError::Internal(e.into()))?;

    let row: Option<(Option<DateTime<Utc>>, i32, i32)> = sqlx::query_as(
        "SELECT last_streak_date, current_streak, COALESCE(streak_freezes, 0) \
         FROM users WHERE id = $1 FOR UPDATE",
    )
    .bind(user_id)
    .fetch_optional(&mut **tx)
    .await
    .map_err(|e| AppError::Internal(e.into()))?;

    if let Some((last_streak_date, current_streak, streak_freezes)) = row {
        let today = now.date_naive();
        let day_diff = match last_streak_date {
            Some(last) => (today - last.date_naive()).num_days(),
            None => i64::MAX, // first-ever activity
        };

        if day_diff == 0 {
            // Already counted today — nothing to do.
            return Ok(());
        }

        if day_diff == 1 {
            // Consecutive day: increment.
            sqlx::query(
                "UPDATE users SET current_streak = current_streak + 1, \
                 last_streak_date = $1, updated_at = NOW() WHERE id = $2",
            )
            .bind(now)
            .bind(user_id)
            .execute(&mut **tx)
            .await
            .map_err(|e| AppError::Internal(e.into()))?;
            return Ok(());
        }

        // Multi-day gap. If a freeze is available AND a streak was running,
        // consume one freeze and preserve the streak. Treat today as a fresh
        // active day.
        if current_streak >= 1 && streak_freezes > 0 {
            sqlx::query(
                "UPDATE users SET streak_freezes = streak_freezes - 1, \
                 last_streak_date = $1, updated_at = NOW() WHERE id = $2",
            )
            .bind(now)
            .bind(user_id)
            .execute(&mut **tx)
            .await
            .map_err(|e| AppError::Internal(e.into()))?;
            return Ok(());
        }

        // No freeze available — capture the loss into history (if any prior
        // streak existed) and start fresh.
        if current_streak >= 1 {
            let started_at = last_streak_date.unwrap_or(now);
            crate::services::streak_rollover_service::capture_streak_loss_to_history(
                tx,
                user_id,
                current_streak,
                started_at,
            )
            .await
            .map_err(|e| AppError::Internal(e.into()))?;
        }

        sqlx::query(
            "UPDATE users SET current_streak = 1, \
             last_streak_date = $1, updated_at = NOW() WHERE id = $2",
        )
        .bind(now)
        .bind(user_id)
        .execute(&mut **tx)
        .await
        .map_err(|e| AppError::Internal(e.into()))?;
    }

    Ok(())
}

// ---------------------------------------------------------------------------
// Database row types (sqlx::FromRow)
// ---------------------------------------------------------------------------

#[derive(Debug, sqlx::FromRow)]
struct UrnListRow {
    id: Uuid,
    slug: String,
    name: String,
    model_url: String,
    thumbnail_url: Option<String>,
    display_order: i32,
    is_demo: bool,
    motif_count: i64,
    discovered_count: i64,
    learned_count: i64,
    mastered_count: i64,
}

#[derive(Debug, sqlx::FromRow)]
struct UrnDetailRow {
    id: Uuid,
    slug: String,
    name: String,
    name_han: Option<String>,
    represents: Option<String>,
    description: Option<String>,
    model_url: String,
    thumbnail_url: Option<String>,
    display_order: i32,
    is_demo: bool,
}

#[derive(Debug, sqlx::FromRow)]
struct UrnIdSlugRow {
    id: Uuid,
    slug: String,
}

#[derive(Debug, sqlx::FromRow)]
struct UrnOutRow {
    id: Uuid,
    slug: String,
    name: String,
    model_url: String,
    thumbnail_url: Option<String>,
}

#[derive(Debug, sqlx::FromRow)]
struct MotifWithLessonRow {
    id: Uuid,
    urn_id: Uuid,
    mesh_name: String,
    name: String,
    name_en: Option<String>,
    category: String,
    rarity: String,
    pos_x: Option<f64>,
    pos_y: Option<f64>,
    pos_z: Option<f64>,
    bounding_radius: Option<f64>,
    thumbnail_url: Option<String>,
    silhouette_url: Option<String>,
    is_demo: bool,
    display_order: Option<i32>,
    lesson_intro: Option<String>,
    lesson_published: Option<bool>,
}

#[derive(Debug, sqlx::FromRow)]
struct MotifDetailRow {
    id: Uuid,
    urn_id: Uuid,
    mesh_name: String,
    name: String,
    name_en: Option<String>,
    category: String,
    rarity: String,
    thumbnail_url: Option<String>,
    silhouette_url: Option<String>,
    is_demo: bool,
    display_order: Option<i32>,
    content_rating: String,
    #[sqlx(rename = "urn_id_2")]
    _urn_id_2: Uuid,
    urn_slug: String,
    urn_name: String,
    urn_model_url: String,
    urn_thumbnail_url: Option<String>,
}

#[derive(Debug, sqlx::FromRow)]
struct MotifProgressRow {
    motif_id: Uuid,
    status: String,
    discovered_at: Option<DateTime<Utc>>,
    lesson_viewed_at: Option<DateTime<Utc>>,
    learned_at: Option<DateTime<Utc>>,
    mastered_at: Option<DateTime<Utc>>,
    quiz_attempts: i32,
    quiz_best_score: i32,
    xp_earned: i32,
}

#[derive(Debug, sqlx::FromRow)]
struct LessonContentRow {
    intro_text: Option<String>,
    description: String,
    historical_context: Option<String>,
    symbolism: Option<String>,
    fun_fact: Option<String>,
    is_ai_generated: bool,
    audio_narration_url: Option<String>,
    additional_images: Option<serde_json::Value>,
    video_url: Option<String>,
    is_published: bool,
}

#[derive(Debug, sqlx::FromRow)]
struct QuizQuestionRow {
    id: Uuid,
    question_type: String,
    question_text: String,
    options: Option<serde_json::Value>,
    target_mesh_name: Option<String>,
    difficulty: Option<i32>,
    explanation: Option<String>,
    #[allow(dead_code)]
    is_active: bool,
    is_published: bool,
}

#[derive(Debug, sqlx::FromRow)]
struct UserProgressRow {
    id: Uuid,
    user_id: Uuid,
    motif_id: Uuid,
    status: String,
    discovered_at: Option<DateTime<Utc>>,
    learned_at: Option<DateTime<Utc>>,
    mastered_at: Option<DateTime<Utc>>,
    xp_earned: i32,
    quiz_best_score: Option<i32>,
}

#[derive(Debug, sqlx::FromRow)]
struct MotifBasicRow {
    #[allow(dead_code)]
    id: Uuid,
    is_demo: bool,
    #[allow(dead_code)]
    urn_id: Uuid,
}

#[derive(Debug, sqlx::FromRow)]
struct ProgressUpdateRow {
    #[allow(dead_code)]
    id: Uuid,
    status: String,
    xp_earned: i32,
    lesson_viewed_at: Option<DateTime<Utc>>,
    learned_at: Option<DateTime<Utc>>,
    #[allow(dead_code)]
    discovered_at: Option<DateTime<Utc>>,
}

#[derive(Debug, sqlx::FromRow)]
struct CacheManifestRow {
    lesson_id: Uuid,
    motif_id: Uuid,
    motif_name: String,
    version: i32,
    audio_narration_url: Option<String>,
    video_url: Option<String>,
    additional_images: Option<serde_json::Value>,
    thumbnail_url: Option<String>,
    silhouette_url: Option<String>,
}

#[derive(Debug, sqlx::FromRow)]
struct LessonCacheRow {
    id: Uuid,
    user_id: Uuid,
    lesson_id: Uuid,
    cached_at: DateTime<Utc>,
    cache_version: i32,
    file_size_bytes: i64,
    is_valid: bool,
    expires_at: Option<DateTime<Utc>>,
}

#[derive(Debug, sqlx::FromRow)]
struct NextLessonRow {
    lesson_id: Uuid,
    motif_id: Uuid,
    motif_name: String,
    motif_slug: String,
    urn_id: Uuid,
    urn_name: String,
    difficulty_level: Option<i32>,
    estimated_time_minutes: Option<i32>,
}

#[derive(Debug, sqlx::FromRow)]
struct PrerequisiteRow {
    id: Uuid,
    motif_id: Uuid,
    motif_name: String,
    motif_slug: String,
    difficulty_level: Option<i32>,
    estimated_time_minutes: Option<i32>,
    is_strict: bool,
    is_completed: bool,
}

#[derive(Debug, sqlx::FromRow)]
struct SequenceRow {
    lesson_id: Uuid,
    motif_id: Uuid,
    motif_name: String,
    motif_slug: String,
    urn_id: Uuid,
    urn_name: String,
    difficulty_level: Option<i32>,
    estimated_time_minutes: Option<i32>,
    progress_status: String,
}
