//! Gateway proxy: forward requests to the legacy Python API.
//!
//! Task 1.7: implements Requirement 3.2–3.5.
//! Uses `reqwest` with connection pooling and streaming bodies.

use axum::{
    body::Body,
    extract::{Request, State},
    http::{HeaderValue, StatusCode},
    response::{IntoResponse, Response},
};
use reqwest::Client;

use crate::config::Settings;

/// Shared state for the gateway proxy.
#[derive(Clone)]
pub struct GatewayState {
    pub client: Client,
    pub legacy_host: String,
    pub legacy_port: u16,
}

impl GatewayState {
    pub fn new(settings: &Settings) -> Self {
        let client = Client::builder()
            .pool_max_idle_per_host(10)
            .timeout(std::time::Duration::from_secs(180))
            .build()
            .expect("build reqwest client");

        Self {
            client,
            legacy_host: settings.legacy_api_host.clone(),
            legacy_port: settings.legacy_api_port,
        }
    }

    fn upstream_url(&self, path: &str, query: Option<&str>) -> String {
        let base = format!("http://{}:{}{}", self.legacy_host, self.legacy_port, path);
        match query {
            Some(q) => format!("{}?{}", base, q),
            None => base,
        }
    }
}

/// Axum fallback handler: proxy any unmatched request to the Python API.
pub async fn fallback_to_python(
    State(gw): State<GatewayState>,
    req: Request,
) -> Response {
    proxy_to_python(gw, req).await
}

/// Proxy a request to the legacy Python API and return its response.
pub async fn proxy_to_python(gw: GatewayState, req: Request) -> Response {
    let method = req.method().clone();
    let path = req.uri().path().to_string();
    let query = req.uri().query().map(|q| q.to_string());

    let url = gw.upstream_url(&path, query.as_deref());

    // Build the upstream request
    let mut upstream_req = gw.client.request(
        reqwest::Method::from_bytes(method.as_str().as_bytes()).unwrap_or(reqwest::Method::GET),
        &url,
    );

    // Forward relevant headers (Req 3.3)
    let headers_to_forward = [
        "authorization",
        "cookie",
        "content-type",
        "accept",
        "x-forwarded-for",
        "x-forwarded-proto",
        "x-forwarded-host",
        "x-request-id",
    ];

    for (name, value) in req.headers() {
        let name_lower = name.as_str().to_lowercase();
        if headers_to_forward.contains(&name_lower.as_str()) {
            if let Ok(v) = value.to_str() {
                upstream_req = upstream_req.header(name.as_str(), v);
            }
        }
    }

    // Forward body
    let body_bytes = match axum::body::to_bytes(req.into_body(), 50 * 1024 * 1024).await {
        Ok(b) => b,
        Err(_) => {
            return upstream_unavailable();
        }
    };

    if !body_bytes.is_empty() {
        upstream_req = upstream_req.body(body_bytes.to_vec());
    }

    // Send to upstream
    let upstream_resp = match upstream_req.send().await {
        Ok(resp) => resp,
        Err(e) => {
            tracing::error!(error = %e, url = %url, "gateway: upstream unavailable");
            return upstream_unavailable();
        }
    };

    // Preserve status (Req 3.4)
    let status = StatusCode::from_u16(upstream_resp.status().as_u16())
        .unwrap_or(StatusCode::BAD_GATEWAY);

    // Build response preserving Content-Type and Content-Length (Req 3.4)
    let mut response_builder = Response::builder().status(status);

    if let Some(ct) = upstream_resp.headers().get("content-type") {
        if let Ok(v) = HeaderValue::from_bytes(ct.as_bytes()) {
            response_builder = response_builder.header("content-type", v);
        }
    }

    if let Some(cl) = upstream_resp.headers().get("content-length") {
        if let Ok(v) = HeaderValue::from_bytes(cl.as_bytes()) {
            response_builder = response_builder.header("content-length", v);
        }
    }

    // Forward Set-Cookie headers from Python (for auth cookies)
    for cookie in upstream_resp.headers().get_all("set-cookie") {
        if let Ok(v) = HeaderValue::from_bytes(cookie.as_bytes()) {
            response_builder = response_builder.header("set-cookie", v);
        }
    }

    // Mark this response as gateway-served for the observability middleware
    response_builder = response_builder.header("x-serve-mode", "gateway");

    // Stream body bytes back (Req 3.4: preserve body bytes)
    let body_bytes = match upstream_resp.bytes().await {
        Ok(b) => b,
        Err(e) => {
            tracing::error!(error = %e, "gateway: failed to read upstream body");
            return upstream_unavailable();
        }
    };

    response_builder
        .body(Body::from(body_bytes.to_vec()))
        .unwrap_or_else(|_| upstream_unavailable())
}

/// HTTP 502 with `{"detail":"upstream unavailable"}` (Req 3.5).
fn upstream_unavailable() -> Response {
    let body = r#"{"detail":"upstream unavailable"}"#;
    Response::builder()
        .status(StatusCode::BAD_GATEWAY)
        .header("content-type", "application/json")
        .header("x-serve-mode", "gateway")
        .body(Body::from(body))
        .unwrap()
}
