//! Luu Nien Su Ki Rust API entry point.
//!
//! Task 1.1: replaced the std-lib TCP server with `axum::serve` on
//! `tokio`, wired a graceful-shutdown handler driven by
//! `SIGTERM`/`SIGINT`, and serves a minimal `/health` route.
//!
//! Task 1.2: wired `sqlx::PgPool` via `db` module and extended
//! `config::Settings` with all required fields. The pool is not
//! connected at startup yet — that will happen when routes need it.

mod config;
mod db;

use axum::{routing::get, Json, Router};
use serde_json::{json, Value};
use tokio::signal;

#[tokio::main(flavor = "multi_thread", worker_threads = 2)]
async fn main() -> anyhow::Result<()> {
    init_tracing();

    let settings = config::Settings::from_env()?;
    let app = build_router();

    let listener = tokio::net::TcpListener::bind(settings.bind_addr).await?;
    tracing::info!(addr = %settings.bind_addr, "luuniensuki-api-rust listening");

    axum::serve(listener, app)
        .with_graceful_shutdown(shutdown_signal())
        .await?;

    Ok(())
}

/// Build the top-level Axum router. Kept as a free function so the smoke
/// test can construct the app without spawning a listener.
fn build_router() -> Router {
    Router::new().route("/health", get(health))
}

/// `GET /health` — process liveness probe (Requirement 12.1).
async fn health() -> Json<Value> {
    Json(json!({ "status": "ok" }))
}

/// Initialize a basic JSON-formatted tracing subscriber. Task 1.3 will
/// extend this with the full `request_id`, `mode`, and `latency_ms`
/// field set required by Requirement 12.3.
fn init_tracing() {
    use tracing_subscriber::{fmt, EnvFilter};

    // `try_init` so that integration tests which set up their own
    // subscriber do not panic on a duplicate global.
    let _ = fmt()
        .json()
        .with_env_filter(
            EnvFilter::try_from_default_env().unwrap_or_else(|_| EnvFilter::new("info")),
        )
        .try_init();
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

    #[tokio::test]
    async fn health_returns_ok_envelope() {
        let app = build_router();

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
}
