//! Quiz & Adaptive business logic.
//!
//! Phase 5 (Tasks 6.1–6.4): Quizzes & Adaptive migration.

use sqlx::PgPool;
use uuid::Uuid;

use crate::error::AppError;
use crate::models::quiz::*;

const QUIZ_PASS_THRESHOLD: f64 = 0.7;
const QUIZ_XP_PER_CORRECT: i32 = 10;

/// GET /api/v1/quizzes/{quiz_id} — fetch quiz with questions.
/// Here quiz_id is treated as motif_id (the quiz is per-motif).
pub async fn get_quiz(pool: &PgPool, quiz_id: Uuid, _user_id: Uuid) -> Result<QuizDetailOut, AppError> {
    // Get motif name
    let motif = sqlx::query_as::<_, MotifNameRow>(
        "SELECT id, name FROM motifs WHERE id = $1 AND is_active = true",
    )
    .bind(quiz_id)
    .fetch_optional(pool)
    .await
    .map_err(|e| AppError::Internal(e.into()))?
    .ok_or_else(|| AppError::Http {
        status: axum::http::StatusCode::NOT_FOUND,
        message: "Quiz not found".to_string(),
    })?;

    let rows = sqlx::query_as::<_, QuizQuestionRow>(
        r#"
        SELECT id, motif_id, question_type, question_text, options,
               correct_answer, target_mesh_name, difficulty, explanation, is_active
        FROM quiz_questions
        WHERE motif_id = $1 AND is_active = true AND is_published = true
        ORDER BY difficulty NULLS LAST, id
        "#,
    )
    .bind(quiz_id)
    .fetch_all(pool)
    .await
    .map_err(|e| AppError::Internal(e.into()))?;

    let questions: Vec<QuizQuestionOut> = rows
        .into_iter()
        .map(|q| QuizQuestionOut {
            id: q.id,
            question_type: q.question_type,
            question_text: q.question_text,
            options: q.options,
            target_mesh_name: q.target_mesh_name,
            difficulty: q.difficulty.unwrap_or(1),
            explanation: None, // Don't reveal explanation before answering
            image_url: None,
        })
        .collect();

    let total = questions.len();
    Ok(QuizDetailOut {
        quiz_id,
        motif_id: motif.id,
        motif_name: motif.name,
        questions,
        total_questions: total,
        time_limit_seconds: None,
    })
}

/// POST /api/v1/quizzes/{quiz_id}/submit — submit quiz answers.
pub async fn submit_quiz(
    pool: &PgPool,
    quiz_id: Uuid,
    user_id: Uuid,
    payload: &QuizSubmitRequest,
) -> Result<QuizSubmitResponse, AppError> {
    // Fetch correct answers
    let rows = sqlx::query_as::<_, QuizQuestionRow>(
        r#"
        SELECT id, motif_id, question_type, question_text, options,
               correct_answer, target_mesh_name, difficulty, explanation, is_active
        FROM quiz_questions
        WHERE motif_id = $1 AND is_active = true AND is_published = true
        "#,
    )
    .bind(quiz_id)
    .fetch_all(pool)
    .await
    .map_err(|e| AppError::Internal(e.into()))?;

    let mut score = 0i32;
    let total = rows.len() as i32;
    let mut results = Vec::new();

    for q in &rows {
        let user_answer = payload.answers.iter().find(|a| a.question_id == q.id);
        let correct = if let Some(ans) = user_answer {
            match &q.correct_answer {
                Some(correct_val) => {
                    let user_val = ans.selected_option.as_deref().or(ans.selected_mesh.as_deref()).unwrap_or("");
                    user_val.eq_ignore_ascii_case(correct_val)
                }
                None => false,
            }
        } else {
            false
        };

        if correct {
            score += 1;
        }

        results.push(QuizQuestionResult {
            question_id: q.id,
            correct,
            correct_answer: q.correct_answer.clone(),
            explanation: q.explanation.clone(),
        });
    }

    let percentage = if total > 0 { (score as f64) / (total as f64) * 100.0 } else { 0.0 };
    let passed = percentage >= (QUIZ_PASS_THRESHOLD * 100.0);
    let xp_awarded = score * QUIZ_XP_PER_CORRECT;

    // Update user progress
    let now = chrono::Utc::now();
    let mut tx = pool.begin().await.map_err(|e| AppError::Internal(e.into()))?;

    // Update quiz attempts and best score
    sqlx::query(
        r#"
        INSERT INTO user_progress (id, user_id, motif_id, status, discovered_at, quiz_attempts, quiz_best_score, xp_earned)
        VALUES ($1, $2, $3, 'discovered', $4, 1, $5, $6)
        ON CONFLICT (user_id, motif_id)
        DO UPDATE SET
            quiz_attempts = user_progress.quiz_attempts + 1,
            quiz_best_score = GREATEST(user_progress.quiz_best_score, $5),
            xp_earned = user_progress.xp_earned + $6,
            status = CASE
                WHEN $7 AND user_progress.status IN ('discovered', 'learned') THEN 'mastered'
                ELSE user_progress.status
            END,
            mastered_at = CASE
                WHEN $7 AND user_progress.status IN ('discovered', 'learned') AND user_progress.mastered_at IS NULL THEN $4
                ELSE user_progress.mastered_at
            END
        "#,
    )
    .bind(Uuid::new_v4())
    .bind(user_id)
    .bind(quiz_id)
    .bind(now)
    .bind(score)
    .bind(xp_awarded)
    .bind(passed)
    .execute(&mut *tx)
    .await
    .map_err(|e| AppError::Internal(e.into()))?;

    // Award XP to user
    if xp_awarded > 0 {
        sqlx::query("UPDATE users SET total_xp = total_xp + $1, last_active_at = $2 WHERE id = $3")
            .bind(xp_awarded)
            .bind(now)
            .bind(user_id)
            .execute(&mut *tx)
            .await
            .map_err(|e| AppError::Internal(e.into()))?;
    }

    tx.commit().await.map_err(|e| AppError::Internal(e.into()))?;

    Ok(QuizSubmitResponse {
        quiz_id,
        score,
        total,
        percentage,
        passed,
        xp_awarded,
        results,
    })
}

/// POST /api/v1/quizzes/adaptive — generate an adaptive quiz.
pub async fn generate_adaptive_quiz(
    pool: &PgPool,
    user_id: Uuid,
    payload: &AdaptiveQuizRequest,
) -> Result<AdaptiveQuizResponse, AppError> {
    let difficulty = payload.difficulty.unwrap_or(1);
    let count = payload.question_count.unwrap_or(5).min(20);

    // Build query based on filters
    let rows = if let Some(motif_id) = payload.motif_id {
        sqlx::query_as::<_, QuizQuestionRow>(
            r#"
            SELECT id, motif_id, question_type, question_text, options,
                   correct_answer, target_mesh_name, difficulty, explanation, is_active
            FROM quiz_questions
            WHERE motif_id = $1 AND is_active = true AND is_published = true
              AND COALESCE(difficulty, 1) <= $2
            ORDER BY RANDOM()
            LIMIT $3
            "#,
        )
        .bind(motif_id)
        .bind(difficulty + 1)
        .bind(count as i64)
        .fetch_all(pool)
        .await
    } else if let Some(urn_id) = payload.urn_id {
        sqlx::query_as::<_, QuizQuestionRow>(
            r#"
            SELECT qq.id, qq.motif_id, qq.question_type, qq.question_text, qq.options,
                   qq.correct_answer, qq.target_mesh_name, qq.difficulty, qq.explanation, qq.is_active
            FROM quiz_questions qq
            JOIN motifs m ON m.id = qq.motif_id
            WHERE m.urn_id = $1 AND qq.is_active = true AND qq.is_published = true
              AND COALESCE(qq.difficulty, 1) <= $2
            ORDER BY RANDOM()
            LIMIT $3
            "#,
        )
        .bind(urn_id)
        .bind(difficulty + 1)
        .bind(count as i64)
        .fetch_all(pool)
        .await
    } else {
        // Global adaptive: pick from motifs user has discovered but not mastered
        sqlx::query_as::<_, QuizQuestionRow>(
            r#"
            SELECT qq.id, qq.motif_id, qq.question_type, qq.question_text, qq.options,
                   qq.correct_answer, qq.target_mesh_name, qq.difficulty, qq.explanation, qq.is_active
            FROM quiz_questions qq
            JOIN user_progress up ON up.motif_id = qq.motif_id AND up.user_id = $1
            WHERE qq.is_active = true AND qq.is_published = true
              AND up.status IN ('discovered', 'learned')
              AND COALESCE(qq.difficulty, 1) <= $2
            ORDER BY RANDOM()
            LIMIT $3
            "#,
        )
        .bind(user_id)
        .bind(difficulty + 1)
        .bind(count as i64)
        .fetch_all(pool)
        .await
    }
    .map_err(|e| AppError::Internal(e.into()))?;

    let questions: Vec<QuizQuestionOut> = rows
        .into_iter()
        .map(|q| QuizQuestionOut {
            id: q.id,
            question_type: q.question_type,
            question_text: q.question_text,
            options: q.options,
            target_mesh_name: q.target_mesh_name,
            difficulty: q.difficulty.unwrap_or(1),
            explanation: None,
            image_url: None,
        })
        .collect();

    let total = questions.len();
    Ok(AdaptiveQuizResponse {
        quiz_id: Uuid::new_v4(), // Generated quiz gets a fresh ID
        questions,
        difficulty,
        total_questions: total,
    })
}

/// GET /api/v1/quizzes/{quiz_id}/hints — get hints for quiz questions.
pub async fn get_quiz_hints(pool: &PgPool, quiz_id: Uuid, _user_id: Uuid) -> Result<QuizHintsResponse, AppError> {
    // Verify quiz/motif exists
    let _motif: (Uuid,) = sqlx::query_as("SELECT id FROM motifs WHERE id = $1 AND is_active = true")
        .bind(quiz_id)
        .fetch_optional(pool)
        .await
        .map_err(|e| AppError::Internal(e.into()))?
        .ok_or_else(|| AppError::Http {
            status: axum::http::StatusCode::NOT_FOUND,
            message: "Quiz not found".to_string(),
        })?;

    // Get questions and generate hints from explanations
    let rows = sqlx::query_as::<_, QuizQuestionRow>(
        r#"
        SELECT id, motif_id, question_type, question_text, options,
               correct_answer, target_mesh_name, difficulty, explanation, is_active
        FROM quiz_questions
        WHERE motif_id = $1 AND is_active = true AND is_published = true
        ORDER BY difficulty NULLS LAST, id
        "#,
    )
    .bind(quiz_id)
    .fetch_all(pool)
    .await
    .map_err(|e| AppError::Internal(e.into()))?;

    let hints: Vec<QuizHintOut> = rows
        .into_iter()
        .filter_map(|q| {
            q.explanation.map(|exp| QuizHintOut {
                question_id: q.id,
                hint_text: exp,
                hint_level: 1,
                cost_hearts: 1,
            })
        })
        .collect();

    Ok(QuizHintsResponse {
        quiz_id,
        hints,
    })
}
