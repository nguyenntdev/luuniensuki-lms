//! Prometheus-compatible metrics endpoint.
//!
//! Task 1.17: Exposes `GET /metrics` returning per-request counters and
//! latency observations in Prometheus text exposition format.
//!
//! This implementation uses zero external dependencies (atomic counters)
//! to stay within the build-host memory budget. Full per-route histograms
//! with `axum-prometheus` will be added in a later task when the build
//! host has more headroom.
//!
//! **Validates:** Req 12.5; Property 19

use axum::http::header;
use axum::response::{IntoResponse, Response};
use std::sync::atomic::{AtomicU64, Ordering};

/// Global request counter — incremented by the observability middleware.
pub static REQUEST_COUNT: AtomicU64 = AtomicU64::new(0);

/// Global error counter (5xx responses) — incremented by the observability middleware.
pub static ERROR_COUNT: AtomicU64 = AtomicU64::new(0);

/// Global gateway-mode request counter.
pub static GATEWAY_COUNT: AtomicU64 = AtomicU64::new(0);

/// Global native-mode request counter.
pub static NATIVE_COUNT: AtomicU64 = AtomicU64::new(0);

/// Global cumulative latency in milliseconds (for computing average).
pub static LATENCY_SUM_MS: AtomicU64 = AtomicU64::new(0);

/// `GET /metrics` handler — returns Prometheus text exposition format.
pub async fn metrics() -> Response {
    let requests = REQUEST_COUNT.load(Ordering::Relaxed);
    let errors = ERROR_COUNT.load(Ordering::Relaxed);
    let gateway = GATEWAY_COUNT.load(Ordering::Relaxed);
    let native = NATIVE_COUNT.load(Ordering::Relaxed);
    let latency_sum = LATENCY_SUM_MS.load(Ordering::Relaxed);

    let body = format!(
        "# HELP http_requests_total Total HTTP requests served.\n\
         # TYPE http_requests_total counter\n\
         http_requests_total {requests}\n\
         \n\
         # HELP http_errors_total Total HTTP 5xx responses.\n\
         # TYPE http_errors_total counter\n\
         http_errors_total {errors}\n\
         \n\
         # HELP http_requests_by_mode_total Requests segmented by serving mode.\n\
         # TYPE http_requests_by_mode_total counter\n\
         http_requests_by_mode_total{{mode=\"native\"}} {native}\n\
         http_requests_by_mode_total{{mode=\"gateway\"}} {gateway}\n\
         \n\
         # HELP http_request_duration_milliseconds_sum Cumulative request latency in ms.\n\
         # TYPE http_request_duration_milliseconds_sum counter\n\
         http_request_duration_milliseconds_sum {latency_sum}\n"
    );

    (
        [(header::CONTENT_TYPE, "text/plain; version=0.0.4; charset=utf-8")],
        body,
    )
        .into_response()
}
