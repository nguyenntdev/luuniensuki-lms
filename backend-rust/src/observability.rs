//! Observability: structured JSON tracing + request_id middleware.
//!
//! Task 1.3: configure `tracing-subscriber` with JSON formatter and the
//! field set `request_id, method, path, status, latency_ms, mode`.
//! Build a `request_id` layer that reads or mints `X-Request-Id`.

use axum::{
    extract::Request,
    http::HeaderValue,
    middleware::Next,
    response::Response,
};
use std::time::Instant;
use uuid::Uuid;

/// Header name for the request identifier.
pub const REQUEST_ID_HEADER: &str = "x-request-id";

/// Initialize the global tracing subscriber with JSON output and env filter.
pub fn init() {
    use tracing_subscriber::{fmt, EnvFilter};

    let _ = fmt()
        .json()
        .with_env_filter(
            EnvFilter::try_from_default_env().unwrap_or_else(|_| EnvFilter::new("info")),
        )
        .try_init();
}

/// Middleware that:
/// 1. Reads `X-Request-Id` from the incoming request or mints a UUID.
/// 2. Records the request_id in the current tracing span.
/// 3. Measures latency.
/// 4. Emits a structured log line with method, path, status, latency_ms, mode.
/// 5. Writes `X-Request-Id` to the response.
pub async fn request_id_and_logging(mut req: Request, next: Next) -> Response {
    let start = Instant::now();

    // Extract or mint request_id
    let request_id = req
        .headers()
        .get(REQUEST_ID_HEADER)
        .and_then(|v| v.to_str().ok())
        .map(|s| s.to_string())
        .unwrap_or_else(|| Uuid::new_v4().to_string());

    // Insert request_id header so downstream handlers can read it
    req.headers_mut().insert(
        REQUEST_ID_HEADER,
        HeaderValue::from_str(&request_id).unwrap_or_else(|_| HeaderValue::from_static("unknown")),
    );

    let method = req.method().to_string();
    let path = req.uri().path().to_string();

    let response = next.run(req).await;

    let latency_ms = start.elapsed().as_millis() as u64;
    let status = response.status().as_u16();

    // Determine mode from a custom response extension or header
    // (set by the dispatcher in task 1.5; default to "native" for now)
    let mode = response
        .headers()
        .get("x-serve-mode")
        .and_then(|v| v.to_str().ok())
        .unwrap_or("native");

    if status >= 500 {
        tracing::error!(
            request_id = %request_id,
            method = %method,
            path = %path,
            status = status,
            latency_ms = latency_ms,
            mode = %mode,
            "request completed with server error"
        );
    } else {
        tracing::info!(
            request_id = %request_id,
            method = %method,
            path = %path,
            status = status,
            latency_ms = latency_ms,
            mode = %mode,
            "request completed"
        );
    }

    // Add request_id to response headers
    let mut response = response;
    response.headers_mut().insert(
        REQUEST_ID_HEADER,
        HeaderValue::from_str(&request_id).unwrap_or_else(|_| HeaderValue::from_static("unknown")),
    );

    response
}
