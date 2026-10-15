//! Quiz & Adaptive business logic.
//!
//! Phase 5 (Tasks 6.1–6.4): Quizzes & Adaptive migration.

use sqlx::PgPool;
use uuid::Uuid;

use crate::error::AppError;
use crate::models::quiz::*;

const QUIZ_PASS_THRESHOLD: f64 = 0.7;
const QUIZ_XP_PER_CORRECT: i32 = 10;

#[derive(Debug, sqlx::FromRow)]
struct QuizProgressRow {
    status: String,
    quiz_attempts: i32,
    quiz_best_score: i32,
    #[allow(dead_code)]
    xp_earned: i32,
    mastered_at: Option<chrono::DateTime<chrono::Utc>>,
}

/// GET /api/v1/quizzes/{quiz_id} — fetch quiz with questions.
/// Here quiz_id is treated as motif_id (the quiz is per-motif).
pub async fn get_quiz(
    pool: &PgPool,
    quiz_id: Uuid,
    _user_id: Uuid,
) -> Result<QuizDetailOut, AppError> {
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
        SELECT id, motif_id, question_type::text AS question_type, question_text, options,
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
        SELECT id, motif_id, question_type::text AS question_type, question_text, options,
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
                    let user_val = ans
                        .selected_option
                        .as_deref()
                        .or(ans.selected_mesh.as_deref())
                        .unwrap_or("");
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

    let percentage = if total > 0 {
        (score as f64) / (total as f64) * 100.0
    } else {
        0.0
    };
    let passed = percentage >= (QUIZ_PASS_THRESHOLD * 100.0);

    // Update user progress
    let now = chrono::Utc::now();
    let mut tx = pool
        .begin()
        .await
        .map_err(|e| AppError::Internal(e.into()))?;

    // Check existing progress with FOR UPDATE to prevent race conditions and compute delta score
    let existing_progress = sqlx::query_as::<_, QuizProgressRow>(
        r#"
        SELECT status::text AS status, quiz_attempts, quiz_best_score, xp_earned, mastered_at
        FROM user_progress
        WHERE user_id = $1 AND motif_id = $2
        FOR UPDATE
        "#,
    )
    .bind(user_id)
    .bind(quiz_id)
    .fetch_optional(&mut *tx)
    .await
    .map_err(|e| AppError::Internal(e.into()))?;

    let xp_awarded = match &existing_progress {
        Some(p) => {
            let prev_best = p.quiz_best_score;
            let delta = (score - prev_best).max(0);
            let xp = delta * QUIZ_XP_PER_CORRECT;
            let new_best = prev_best.max(score);

            let new_status = if passed && (p.status == "discovered" || p.status == "learned") {
                "mastered"
            } else {
                p.status.as_str()
            };

            let new_mastered_at = if passed
                && (p.status == "discovered" || p.status == "learned")
                && p.mastered_at.is_none()
            {
                Some(now)
            } else {
                p.mastered_at
            };

            sqlx::query(
                r#"
                UPDATE user_progress
                SET quiz_attempts = quiz_attempts + 1,
                    quiz_best_score = $1,
                    xp_earned = xp_earned + $2,
                    status = $3,
                    mastered_at = $4
                WHERE user_id = $5 AND motif_id = $6
                "#,
            )
            .bind(new_best)
            .bind(xp)
            .bind(new_status)
            .bind(new_mastered_at)
            .bind(user_id)
            .bind(quiz_id)
            .execute(&mut *tx)
            .await
            .map_err(|e| AppError::Internal(e.into()))?;

            xp
        }
        None => {
            let xp = score * QUIZ_XP_PER_CORRECT;
            let final_status = if passed { "mastered" } else { "discovered" };
            let final_mastered_at = if passed { Some(now) } else { None };

            sqlx::query(
                r#"
                INSERT INTO user_progress (
                    id, user_id, motif_id, status, discovered_at,
                    quiz_attempts, quiz_best_score, xp_earned, mastered_at
                )
                VALUES ($1, $2, $3, $4, $5, 1, $6, $7, $8)
                "#,
            )
            .bind(Uuid::new_v4())
            .bind(user_id)
            .bind(quiz_id)
            .bind(final_status)
            .bind(now)
            .bind(score)
            .bind(xp)
            .bind(final_mastered_at)
            .execute(&mut *tx)
            .await
            .map_err(|e| AppError::Internal(e.into()))?;

            xp
        }
    };

    // Award incremental XP to user
    if xp_awarded > 0 {
        sqlx::query("UPDATE users SET total_xp = total_xp + $1, last_active_at = $2 WHERE id = $3")
            .bind(xp_awarded)
            .bind(now)
            .bind(user_id)
            .execute(&mut *tx)
            .await
            .map_err(|e| AppError::Internal(e.into()))?;
    } else {
        sqlx::query("UPDATE users SET last_active_at = $1 WHERE id = $2")
            .bind(now)
            .bind(user_id)
            .execute(&mut *tx)
            .await
            .map_err(|e| AppError::Internal(e.into()))?;
    }

    tx.commit()
        .await
        .map_err(|e| AppError::Internal(e.into()))?;

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
            SELECT id, motif_id, question_type::text AS question_type, question_text, options,
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
            SELECT qq.id, qq.motif_id, qq.question_type::text AS question_type, qq.question_text, qq.options,
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
            SELECT qq.id, qq.motif_id, qq.question_type::text AS question_type, qq.question_text, qq.options,
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
pub async fn get_quiz_hints(
    pool: &PgPool,
    quiz_id: Uuid,
    _user_id: Uuid,
) -> Result<QuizHintsResponse, AppError> {
    // Verify quiz/motif exists
    let _motif: (Uuid,) =
        sqlx::query_as("SELECT id FROM motifs WHERE id = $1 AND is_active = true")
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
        SELECT id, motif_id, question_type::text AS question_type, question_text, options,
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

    Ok(QuizHintsResponse { quiz_id, hints })
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn quiz_delta_xp_calculation() {
        let calc_xp = |score: i32, prev_best: i32| -> i32 {
            let delta = (score - prev_best).max(0);
            delta * QUIZ_XP_PER_CORRECT
        };

        // First attempt with score 3: gets 30 XP
        assert_eq!(calc_xp(3, 0), 30);
        // Repeat attempt with same score: 0 XP
        assert_eq!(calc_xp(3, 3), 0);
        // Worse attempt: 0 XP
        assert_eq!(calc_xp(2, 3), 0);
        // Improved attempt with score 5: gets (5 - 3) * 10 = 20 XP
        assert_eq!(calc_xp(5, 3), 20);
        // Perfect score repeated: 0 XP
        assert_eq!(calc_xp(5, 5), 0);
    }
}
