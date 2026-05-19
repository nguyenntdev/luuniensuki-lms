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
mod models;
mod observability;
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
    let user_routes: Router = Router::new()
        .route("/api/v1/users/me", patch(routes::users::update_profile))
        .route("/api/v1/users/me/change-password", post(routes::users::change_password))
        .route("/api/v1/users/me/starting-path", post(routes::users::set_starting_path))
        .route("/api/v1/users/me/avatar", post(routes::users::upload_avatar))
        .route("/api/v1/onboarding/goals", post(routes::users::save_onboarding_goal))
        .route("/api/v1/onboarding/status", get(routes::users::get_onboarding_status))
        .route("/api/v1/onboarding/complete", post(routes::users::complete_onboarding))
        .route("/api/v1/users/:user_id/public", get(routes::users::get_user_public_profile))
        .route("/api/v1/u/:identifier", get(routes::users::get_user_by_identifier))
        .with_state(auth_state);

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
    }
}
