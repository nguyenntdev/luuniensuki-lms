//! Luu Nien Su Ki Rust API entry point.
//!
//! Task 1.1: replaced the std-lib TCP server with `axum::serve` on
//! `tokio`, wired a graceful-shutdown handler driven by
//! `SIGTERM`/`SIGINT`, and serves a minimal `/health` route.
//!
//! Task 1.2: wired `sqlx::PgPool` via `db` module and extended
//! `config::Settings` with all required fields. The pool is not
//! connected at startup yet — that will happen when routes need it.

mod auth;
mod config;
mod db;
mod dispatcher;
mod error;
mod gateway;
mod inventory;
mod jobs;
mod models;
mod observability;
mod rate_limit;
mod routes;
mod services;

use axum::{middleware, routing::{get, patch, post}, Router};
use sqlx::PgPool;
use tokio::signal;

use crate::dispatcher::Dispatcher;
use crate::gateway::GatewayState;
use crate::inventory::AppState;
use crate::routes::auth::AuthState;

#[tokio::main(flavor = "multi_thread", worker_threads = 2)]
async fn main() -> anyhow::Result<()> {
    observability::init();

    let settings = config::Settings::from_env()?;

    // Load the route-mode dispatcher (hot-reloadable TOML map)
    let dispatcher = Dispatcher::load(&settings.route_modes_path)?;

    // Load route inventory for coverage assertion and the internal endpoint
    let inv = inventory::load_inventory(&settings.route_inventory_path)?;

    // Assert full coverage: every inventory entry must be reachable
    // (via native handler or gateway fallback)
    inventory::assert_full_coverage(&inv, &dispatcher)?;

    let gw_state = GatewayState::new(&settings);
    let app_state = AppState {
        inventory: inv,
        dispatcher,
        gateway: gw_state.clone(),
    };

    // Create the DB pool (connect_lazy — no connection until first query)
    let pool = db::pool(&settings).await.ok();

    // Spawn streak-economy background jobs if a pool is available.
    if let Some(p) = pool.clone() {
        tokio::spawn(jobs::streak_rollover_job::run(p.clone()));
        tokio::spawn(jobs::friend_streak_job::run(p.clone()));
        tokio::spawn(jobs::trail_reminder_job::run(p.clone()));
        tokio::spawn(jobs::trail_certificate_retry_job::run(
            p,
            settings.uploads_dir.clone(),
        ));
    }

    let app = build_router(gw_state, app_state, pool, &settings);

    let listener = tokio::net::TcpListener::bind(settings.bind_addr).await?;
    tracing::info!(addr = %settings.bind_addr, "luuniensuki-api-rust listening");

    axum::serve(listener, app)
        .with_graceful_shutdown(shutdown_signal())
        .await?;

    Ok(())
}

/// Build the top-level Axum router. Kept as a free function so the smoke
/// test can construct the app without spawning a listener.
fn build_router(gw_state: GatewayState, app_state: AppState, pool: Option<PgPool>, settings: &config::Settings) -> Router {
    // Internal routes that need AppState (inventory + dispatcher)
    let internal_routes = Router::new()
        .route(
            "/api/v1/internal/route-coverage",
            get(inventory::route_coverage),
        )
        .with_state(app_state);

    // Routes that need the DB pool (optional — returns 503 when None)
    let db_routes = Router::new()
        .route("/api/v1/internal/db-health", get(routes::health::db_health))
        .route("/api/v1/tags", get(routes::content::tags))
        .route("/api/v1/badges", get(routes::badges::list_badges))
        .with_state(pool.clone());

    // Auth routes (need pool + settings)
    let auth_state = AuthState {
        pool,
        settings: settings.clone(),
    };
    let auth_routes = Router::new()
        .route("/api/v1/auth/me", get(routes::auth::me))
        .route("/api/v1/auth/login", post(routes::auth::login))
        .route("/api/v1/auth/register", post(routes::auth::register))
        .route("/api/v1/auth/refresh", post(routes::auth::refresh))
        .route("/api/v1/auth/logout", post(routes::auth::logout))
        .route("/api/v1/auth/forgot-password", post(routes::auth::forgot_password))
        .route("/api/v1/auth/reset-password", post(routes::auth::reset_password))
        .route("/api/v1/users/me/age-verify", post(routes::auth::age_verify))
        .with_state(auth_state.clone());

    // User profile routes (Phase 3 — need pool + settings via AuthState)
    let user_routes = Router::new()
        .route("/api/v1/users/me", patch(routes::users::update_profile))
        .route("/api/v1/users/me/change-password", post(routes::users::change_password))
        .route("/api/v1/users/me/starting-path", post(routes::users::set_starting_path))
        .route("/api/v1/users/me/avatar", post(routes::users::upload_avatar))
        .route("/api/v1/onboarding/goals", post(routes::users::save_onboarding_goal))
        .route("/api/v1/onboarding/status", get(routes::users::get_onboarding_status))
        .route("/api/v1/onboarding/complete", post(routes::users::complete_onboarding))
        .route("/api/v1/users/:user_id/public", get(routes::users::get_user_public_profile))
        .route("/api/v1/u/:identifier", get(routes::users::get_user_by_identifier))
        .with_state(auth_state.clone());

    // Lesson & content routes (Phase 4 — need pool + settings via AuthState)
    let lesson_routes = Router::new()
        .route("/api/v1/urns", get(routes::lessons::list_urns))
        .route("/api/v1/urns/:urn_slug", get(routes::lessons::get_urn_detail))
        .route("/api/v1/urns/:urn_slug/progress", get(routes::lessons::get_urn_progress))
        .route("/motifs/:urn_name", get(routes::lessons::get_motifs_by_urn))
        .route("/api/v1/motifs/:motif_id", get(routes::lessons::get_motif_detail))
        .route("/api/v1/motifs/:motif_id/complete-lesson", post(routes::lessons::complete_lesson))
        .route("/api/v1/lessons/cache-manifest", get(routes::lessons::get_cache_manifest))
        .route("/api/v1/lessons/next", get(routes::lessons::get_next_lesson))
        .route("/api/v1/lessons/:lesson_id/prerequisites", get(routes::lessons::get_lesson_prerequisites))
        .route("/api/v1/lessons/:lesson_id/is-unlocked", get(routes::lessons::check_lesson_is_unlocked))
        .route("/api/v1/lessons/sequence", get(routes::lessons::get_lesson_sequence))
        .route("/api/v1/lessons/:lesson_id/cache", post(routes::lessons::mark_lesson_cached).delete(routes::lessons::remove_cached_lesson))
        .route("/api/v1/lessons/cached", get(routes::lessons::get_cached_lessons))
        .with_state(auth_state.clone());

    // Quiz routes (Phase 5 — Quizzes & Adaptive)
    let quiz_routes = Router::new()
        .route("/api/v1/quizzes/adaptive", post(routes::quizzes::adaptive_quiz))
        .route("/api/v1/quizzes/:quiz_id", get(routes::quizzes::get_quiz))
        .route("/api/v1/quizzes/:quiz_id/submit", post(routes::quizzes::submit_quiz))
        .route("/api/v1/quizzes/:quiz_id/hints", get(routes::quizzes::get_quiz_hints))
        .with_state(auth_state.clone());

    // Progress & Streak routes (Phase 6)
    let progress_routes = Router::new()
        .route("/api/v1/progress/unlock", post(routes::progress::unlock_motif))
        .route("/api/v1/users/me/streak", get(routes::progress::get_streak).post(routes::progress::update_streak))
        .route("/api/v1/users/me/hearts", get(routes::progress::get_hearts).post(routes::progress::update_hearts))
        .route("/api/v1/users/me/daily-goal", get(routes::progress::get_daily_goal).put(routes::progress::update_daily_goal))
        .route("/api/v1/users/me/milestones", get(routes::progress::get_milestones))
        .with_state(auth_state.clone());

    // Badge, Quest, Achievement routes (Phase 7)
    let quest_routes = Router::new()
        .route("/api/v1/badges/:badge_id/award", post(routes::quests::award_badge))
        .route("/api/v1/quests", get(routes::quests::list_quests))
        .route("/api/v1/quests/weekly", get(routes::quests::get_weekly_quests))
        .route("/api/v1/quests/:quest_slug", get(routes::quests::get_quest_detail))
        .route("/api/v1/quests/:quest_slug/start", post(routes::quests::start_quest))
        .route("/api/v1/users/me/quest-summary", get(routes::quests::get_quest_summary))
        .route("/api/v1/missions/daily", get(routes::quests::get_daily_missions))
        .with_state(auth_state.clone());

    // Classroom routes (Phase 8)
    let classroom_routes = Router::new()
        .route("/api/v1/classrooms", post(routes::classrooms::create_classroom).get(routes::classrooms::list_classrooms))
        .route("/api/v1/classrooms/:id", get(routes::classrooms::get_classroom).patch(routes::classrooms::update_classroom).delete(routes::classrooms::archive_classroom))
        .route("/api/v1/classrooms/:id/members", get(routes::classrooms::list_members).post(routes::classrooms::add_member))
        .route("/api/v1/classrooms/:id/members/:user_id", axum::routing::delete(routes::classrooms::remove_member))
        .route("/api/v1/classrooms/:id/lessons", get(routes::classrooms::list_classroom_lessons).post(routes::classrooms::assign_lesson))
        .route("/api/v1/classrooms/:id/analytics", get(routes::classrooms::get_classroom_analytics))
        .with_state(auth_state.clone());

    // Leaderboard & League routes (Phase 9)
    let leaderboard_routes = Router::new()
        .route("/api/v1/leaderboard", get(routes::leaderboard::get_leaderboard))
        .route("/api/v1/leaderboard/friends", get(routes::leaderboard::get_friends_leaderboard))
        .route("/api/v1/leagues", get(routes::leaderboard::list_leagues))
        .route("/api/v1/leagues/me", get(routes::leaderboard::get_user_league))
        .route("/api/v1/leagues/:league_id", get(routes::leaderboard::get_league_detail))
        .with_state(auth_state.clone());

    // Notification routes (Phase 10)
    let notification_routes = Router::new()
        .route("/api/v1/notifications/settings", get(routes::notifications::get_settings).put(routes::notifications::update_settings))
        .route("/api/v1/notifications/register-push", post(routes::notifications::register_push))
        .route("/api/v1/notifications/unregister-push", axum::routing::delete(routes::notifications::unregister_push))
        .route("/api/v1/notifications/history", get(routes::notifications::get_history))
        .route("/api/v1/notifications/should-prompt-permission", get(routes::notifications::should_prompt_permission))
        .with_state(auth_state.clone());

    // Session & Analytics routes (Phase 11)
    let session_routes = Router::new()
        .route("/api/v1/sessions/heartbeat", post(routes::sessions::heartbeat))
        .route("/api/v1/sessions/end", post(routes::sessions::end_session))
        .route("/api/v1/analytics/events", post(routes::sessions::ingest_events))
        .route("/api/v1/admin/analytics/sessions/active", get(routes::sessions::get_active_sessions))
        .route("/api/v1/admin/analytics/sessions/stats", get(routes::sessions::get_session_stats))
        .with_state(auth_state.clone());

    // Crash Report routes (Phase 12)
    let crash_report_routes = Router::new()
        .route("/api/v1/crash-reports", post(routes::crash_reports::submit_crash_report))
        .with_state(auth_state.clone());

    // Admin routes (Phase 13) — no resolve route (no DB support)
    let admin_routes = Router::new()
        .route("/api/v1/admin/push-notifications/send", post(routes::admin::send_push_notification))
        .route("/api/v1/admin/push-notifications/broadcast", post(routes::admin::broadcast_push_notification))
        .route("/api/v1/admin/push-notifications", get(routes::admin::list_push_notifications))
        .route("/api/v1/admin/crash-reports", get(routes::admin::list_crash_reports))
        .route("/api/v1/admin/crash-reports/stats", get(routes::admin::get_crash_report_stats))
        .route("/api/v1/admin/crash-reports/:report_id", get(routes::admin::get_crash_report))
        .route("/api/v1/admin/analytics/render-performance", get(routes::admin_render::get_render_performance))
        // Phase 13 leftovers (tasks 14.3–14.6): read-only admin listings
        .route("/api/v1/admin/audit", get(routes::admin::list_audit))
        .route("/api/v1/admin/feature-flags", get(routes::admin::list_feature_flags))
        .route("/api/v1/admin/experiments", get(routes::admin::list_experiments))
        .route("/api/v1/admin/motif-coordinates", post(routes::admin::save_motif_coordinates))
        .with_state(auth_state.clone());

    // Streak Repair Economy routes (additive — see .kiro/specs/streak-repair-economy)
    let streak_economy_routes = Router::new()
        // user-facing
        .route("/api/v1/users/me/streak/repair", post(routes::streak_repair::repair))
        .route("/api/v1/users/me/streak/repair-options", get(routes::streak_repair::repair_options))
        .route("/api/v1/users/me/friend-streaks", get(routes::streak_friend::list_my_friend_streaks))
        .route("/api/v1/users/:other_id/friend-streak", get(routes::streak_friend::get_friend_streak))
        .route("/api/v1/users/me/streak/comeback-status", get(routes::streak_comeback::comeback_status))
        .route("/api/v1/users/me/streak-insurance", get(routes::streak_comeback::my_insurance))
        // admin
        .route("/api/v1/admin/streak-repair-events", get(routes::streak_admin::list_repair_events))
        .route("/api/v1/admin/users/:user_id/streak/grant-repair", post(routes::streak_admin::grant_repair))
        .route("/api/v1/admin/streak/big-red-button", post(routes::streak_admin::big_red_button))
        .route("/api/v1/admin/streak/big-red-button/events", get(routes::streak_admin::brb_events))
        .route("/api/v1/admin/streak-economy/stats", get(routes::streak_admin::stats))
        .route(
            "/api/v1/admin/users/:user_id/streak-insurance/grant",
            post(routes::streak_admin::grant_insurance),
        )
        .with_state(auth_state.clone());

    // FSRS Spaced Repetition routes (.kiro/specs/fsrs-spaced-repetition)
    let fsrs_routes = Router::new()
        .route("/api/v1/reviews/due", get(routes::reviews::get_due_reviews))
        .route(
            "/api/v1/reviews/:card_id/rate",
            post(routes::reviews::rate_card),
        )
        .route(
            "/api/v1/users/me/fsrs-settings",
            get(routes::reviews::get_fsrs_settings).put(routes::reviews::update_fsrs_settings),
        )
        .with_state(auth_state.clone());

    // Heritage Time-Lapse routes (.kiro/specs/heritage-time-lapse)
    let timeline_routes = Router::new()
        .route(
            "/api/v1/timeline/events",
            get(routes::timeline::get_timeline_events),
        )
        .route(
            "/api/v1/timeline/motifs",
            get(routes::timeline::get_timeline_motifs),
        )
        .route(
            "/api/v1/motifs/compare",
            get(routes::timeline::compare_motifs),
        )
        .route(
            "/api/v1/admin/heritage-eras",
            post(routes::timeline::create_era),
        )
        .route(
            "/api/v1/admin/historical-events",
            post(routes::timeline::create_event),
        )
        .route(
            "/api/v1/admin/timeline/stats",
            get(routes::timeline::get_timeline_stats),
        )
        .with_state(auth_state.clone());

    // Heritage Trail Mode routes (.kiro/specs/heritage-trail-mode)
    let trail_routes = Router::new()
        // Public + user
        .route("/api/v1/trails", get(routes::trails::list_trails))
        .route("/api/v1/trails/:slug", get(routes::trails::get_trail_detail))
        .route(
            "/api/v1/trails/:slug/start",
            post(routes::trails::start_trail),
        )
        .route(
            "/api/v1/trails/:slug/step/:position/complete",
            post(routes::trails::complete_step),
        )
        .route(
            "/api/v1/trails/:slug/checkpoint/:idx",
            post(routes::trails::submit_checkpoint),
        )
        .route(
            "/api/v1/users/me/trails/:trail_id/pace",
            axum::routing::put(routes::trails::set_pace),
        )
        .route(
            "/api/v1/certificates/:hash/verify",
            get(routes::trails::verify_certificate),
        )
        // Admin
        .route(
            "/api/v1/admin/trails",
            post(routes::trail_admin::create_trail),
        )
        .route(
            "/api/v1/admin/trails/:trail_id",
            patch(routes::trail_admin::update_trail),
        )
        .route(
            "/api/v1/admin/trails/:trail_id/promote",
            post(routes::trail_admin::promote_trail),
        )
        .route(
            "/api/v1/admin/trails/:trail_id/analytics",
            get(routes::trail_admin::get_trail_analytics),
        )
        // Teacher
        .route(
            "/api/v1/teacher/trails",
            post(routes::trail_teacher::create_teacher_trail),
        )
        .route(
            "/api/v1/teacher/trails/:trail_id/submit-for-promotion",
            post(routes::trail_teacher::submit_for_promotion),
        )
        .with_state(auth_state.clone());

    // Misc routes (Phase 15 — preview, collection, leftovers)
    let misc_routes = Router::new()
        .route("/api/v1/preview/lesson", get(routes::misc::get_preview_lesson))
        .route("/api/v1/preview/start", post(routes::misc::start_preview))
        .route("/api/v1/preview/complete", post(routes::misc::complete_preview))
        .route("/api/v1/preview/convert", post(routes::misc::convert_preview))
        .route("/api/v1/users/me/collection", get(routes::misc::get_user_collection))
        .with_state(auth_state.clone());


    // Live virtual-classroom routes (.kiro/specs/live-room-rust-janus-migration)
    // Native control plane + WS signaling. Media plane = Janus (feature-flagged).
    let live_routes = Router::new()
        .route("/api/v1/live-sessions", post(routes::live::create_session).get(routes::live::list_sessions))
        .route("/api/v1/live-sessions/:id", get(routes::live::get_session))
        .route("/api/v1/live-sessions/:id/end", post(routes::live::end_session))
        .route("/api/v1/live-sessions/:id/join", post(routes::live::join_session))
        .route("/api/v1/live-sessions/:id/token", post(routes::live::issue_credential))
        .route("/api/v1/live-sessions/:id/leave", post(routes::live::leave_session))
        .route("/api/v1/live-sessions/:id/participants", get(routes::live::list_participants))
        .route("/api/v1/live-sessions/:id/participants/:pid/role", patch(routes::live::update_participant_role))
        .route("/api/v1/live-sessions/:id/events", get(routes::live::list_events).post(routes::live::append_event))
        .route("/api/v1/live-sessions/:id/host/settings", post(routes::live::update_settings))
        .route("/api/v1/live-sessions/:id/host/mute-all", post(routes::live::mute_all))
        .route("/api/v1/live-sessions/:id/host/remove-participant", post(routes::live::remove_participant))
        .route("/api/v1/live-sessions/:id/ai-teacher/credential", post(routes::live::ai_teacher_credential))
        .route("/api/v1/live-sessions/:id/signal", get(routes::live::signal_ws))
        .with_state(auth_state.clone());

    // Static routes (no state needed)
    let static_routes = Router::new()
        .route("/health", get(routes::health::health))
        .route("/api/v1/content/ratings", get(routes::content::content_ratings))
        .route("/api/v1/ranks", get(routes::content::ranks))
        .route("/metrics", get(routes::metrics::metrics));

    Router::new()
        .merge(static_routes)
        .merge(db_routes)
        .merge(auth_routes)
        .merge(user_routes)
        .merge(lesson_routes)
        .merge(quiz_routes)
        .merge(progress_routes)
        .merge(quest_routes)
        .merge(classroom_routes)
        .merge(leaderboard_routes)
        .merge(notification_routes)
        .merge(session_routes)
        .merge(crash_report_routes)
        .merge(admin_routes)
        .merge(streak_economy_routes)
        .merge(fsrs_routes)
        .merge(timeline_routes)
        .merge(trail_routes)
        .merge(live_routes)
        .merge(misc_routes)
        .merge(internal_routes)
        .fallback(gateway::fallback_to_python)
        .layer(middleware::from_fn(observability::request_id_and_logging))
        .with_state(gw_state)
}

/// Resolve when either `SIGTERM` or `SIGINT` (`Ctrl+C`) is received.
/// `axum::serve(...).with_graceful_shutdown(shutdown_signal())` then
/// stops accepting new connections and lets in-flight requests finish.
async fn shutdown_signal() {
    let ctrl_c = async {
        signal::ctrl_c()
            .await
            .expect("install Ctrl+C signal handler");
    };

    #[cfg(unix)]
    let terminate = async {
        signal::unix::signal(signal::unix::SignalKind::terminate())
            .expect("install SIGTERM handler")
            .recv()
            .await;
    };

    #[cfg(not(unix))]
    let terminate = std::future::pending::<()>();

    tokio::select! {
        _ = ctrl_c => tracing::info!("received SIGINT, starting graceful shutdown"),
        _ = terminate => tracing::info!("received SIGTERM, starting graceful shutdown"),
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use axum::{
        body::{to_bytes, Body},
        http::{Request, StatusCode},
    };
    use tower::ServiceExt;

    fn test_app_state(settings: &config::Settings) -> (GatewayState, AppState) {
        let gw_state = GatewayState::new(settings);
        let dispatcher = Dispatcher::load(&settings.route_modes_path)
            .unwrap_or_else(|_| {
                // Fallback: create a temp file with defaults for tests
                let tmp = std::env::temp_dir().join("test-route-modes.toml");
                std::fs::write(&tmp, "[defaults]\nunknown_routes = \"gateway\"\n").unwrap();
                Dispatcher::load(&tmp).unwrap()
            });
        let inv = inventory::load_inventory(&settings.route_inventory_path)
            .unwrap_or_else(|_| std::sync::Arc::new(Vec::new()));
        let app_state = AppState {
            inventory: inv,
            dispatcher,
            gateway: gw_state.clone(),
        };
        (gw_state, app_state)
    }

    #[tokio::test]
    async fn health_returns_ok_envelope() {
        let settings = config::Settings::from_env().unwrap();
        let (gw_state, app_state) = test_app_state(&settings);
        let app = build_router(gw_state, app_state, None, &settings);

        let response = app
            .oneshot(
                Request::builder()
                    .uri("/health")
                    .body(Body::empty())
                    .unwrap(),
            )
            .await
            .unwrap();

        assert_eq!(response.status(), StatusCode::OK);

        let body = to_bytes(response.into_body(), 1024).await.unwrap();
        let parsed: serde_json::Value = serde_json::from_slice(&body).unwrap();
        assert_eq!(parsed, serde_json::json!({ "status": "ok" }));
    }

    #[tokio::test]
    async fn route_coverage_returns_json() {
        let settings = config::Settings::from_env().unwrap();
        let (gw_state, app_state) = test_app_state(&settings);
        let app = build_router(gw_state, app_state, None, &settings);

        let response = app
            .oneshot(
                Request::builder()
                    .uri("/api/v1/internal/route-coverage")
                    .body(Body::empty())
                    .unwrap(),
            )
            .await
            .unwrap();

        assert_eq!(response.status(), StatusCode::OK);

        let body = to_bytes(response.into_body(), 64 * 1024).await.unwrap();
        let parsed: serde_json::Value = serde_json::from_slice(&body).unwrap();

        // Verify the response has the expected shape
        assert!(parsed.get("routes").is_some());
        assert!(parsed.get("summary").is_some());

        let summary = parsed.get("summary").unwrap();
        assert!(summary.get("total").is_some());
        assert!(summary.get("native").is_some());
        assert!(summary.get("gateway").is_some());
        assert!(summary.get("groups_complete").is_some());
        assert!(summary.get("groups_total").is_some());
        assert!(summary.get("ready_for_cutover").is_some());
    }

    #[tokio::test]
    async fn content_ratings_returns_expected_shape() {
        let settings = config::Settings::from_env().unwrap();
        let (gw_state, app_state) = test_app_state(&settings);
        let app = build_router(gw_state, app_state, None, &settings);

        let response = app
            .oneshot(
                Request::builder()
                    .uri("/api/v1/content/ratings")
                    .body(Body::empty())
                    .unwrap(),
            )
            .await
            .unwrap();

        assert_eq!(response.status(), StatusCode::OK);

        let body = to_bytes(response.into_body(), 4096).await.unwrap();
        let parsed: serde_json::Value = serde_json::from_slice(&body).unwrap();
        let ratings = parsed["ratings"].as_array().unwrap();
        assert_eq!(ratings.len(), 3);
        assert_eq!(ratings[0]["rating"], "everyone");
    }

    #[tokio::test]
    async fn ranks_returns_expected_shape() {
        let settings = config::Settings::from_env().unwrap();
        let (gw_state, app_state) = test_app_state(&settings);
        let app = build_router(gw_state, app_state, None, &settings);

        let response = app
            .oneshot(
                Request::builder()
                    .uri("/api/v1/ranks")
                    .body(Body::empty())
                    .unwrap(),
            )
            .await
            .unwrap();

        assert_eq!(response.status(), StatusCode::OK);

        let body = to_bytes(response.into_body(), 4096).await.unwrap();
        let parsed: serde_json::Value = serde_json::from_slice(&body).unwrap();
        let ranks = parsed["ranks"].as_array().unwrap();
        assert_eq!(ranks.len(), 8);
        assert_eq!(ranks[0]["name"], "Beginner");
    }

    #[tokio::test]
    async fn db_health_without_pool_returns_503() {
        let settings = config::Settings::from_env().unwrap();
        let (gw_state, app_state) = test_app_state(&settings);
        let app = build_router(gw_state, app_state, None, &settings);

        let response = app
            .oneshot(
                Request::builder()
                    .uri("/api/v1/internal/db-health")
                    .body(Body::empty())
                    .unwrap(),
            )
            .await
            .unwrap();

        assert_eq!(response.status(), StatusCode::SERVICE_UNAVAILABLE);
    }

    #[tokio::test]
    async fn badges_without_pool_returns_503() {
        let settings = config::Settings::from_env().unwrap();
        let (gw_state, app_state) = test_app_state(&settings);
        let app = build_router(gw_state, app_state, None, &settings);

        let response = app
            .oneshot(
                Request::builder()
                    .uri("/api/v1/badges")
                    .body(Body::empty())
                    .unwrap(),
            )
            .await
            .unwrap();

        assert_eq!(response.status(), StatusCode::SERVICE_UNAVAILABLE);
    }

    #[tokio::test]
    async fn tags_without_pool_returns_503() {
        let settings = config::Settings::from_env().unwrap();
        let (gw_state, app_state) = test_app_state(&settings);
        let app = build_router(gw_state, app_state, None, &settings);

        let response = app
            .oneshot(
                Request::builder()
                    .uri("/api/v1/tags")
                    .body(Body::empty())
                    .unwrap(),
            )
            .await
            .unwrap();

        assert_eq!(response.status(), StatusCode::SERVICE_UNAVAILABLE);
    }

    #[tokio::test]
    async fn metrics_returns_prometheus_text_format() {
        let settings = config::Settings::from_env().unwrap();
        let (gw_state, app_state) = test_app_state(&settings);
        let app = build_router(gw_state, app_state, None, &settings);

        let response = app
            .oneshot(
                Request::builder()
                    .uri("/metrics")
                    .body(Body::empty())
                    .unwrap(),
            )
            .await
            .unwrap();

        assert_eq!(response.status(), StatusCode::OK);

        let content_type = response
            .headers()
            .get("content-type")
            .unwrap()
            .to_str()
            .unwrap();
        assert!(
            content_type.contains("text/plain"),
            "Expected text/plain content type for Prometheus metrics"
        );

        let body = to_bytes(response.into_body(), 4096).await.unwrap();
        let text = String::from_utf8(body.to_vec()).unwrap();

        // Verify Prometheus exposition format markers
        assert!(text.contains("# HELP http_requests_total"));
        assert!(text.contains("# TYPE http_requests_total counter"));
        assert!(text.contains("http_requests_total"));
        assert!(text.contains("# HELP http_errors_total"));
        assert!(text.contains("# TYPE http_errors_total counter"));
        assert!(text.contains("http_errors_total"));
        assert!(text.contains("http_requests_by_mode_total{mode=\"native\"}"));
        assert!(text.contains("http_requests_by_mode_total{mode=\"gateway\"}"));
        assert!(text.contains("http_request_duration_milliseconds_sum"));

        // Streak Repair Economy counters
        assert!(text.contains("streak_repair_total"));
        assert!(text.contains("streak_brb_invocations_total"));
        assert!(text.contains("friend_streak_increments_total"));
        assert!(text.contains("phoenix_badges_awarded_total"));
    }
}
