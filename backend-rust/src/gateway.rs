//! Gateway proxy: forward requests to the legacy Python API.
//!
//! Implements transparent streaming reverse-proxying with connection pooling.
//! Incoming request bodies and upstream response bodies are streamed end-to-end
//! without buffering in memory, enabling Server-Sent Events (SSE) and large payloads
//! without risk of OOM. Non-hop-by-hop headers (Location, Cache-Control, Set-Cookie, etc.)
//! are forwarded faithfully.

use axum::{
    body::Body,
    extract::{Request, State},
    http::StatusCode,
    response::Response,
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

    pub fn upstream_url(&self, path: &str, query: Option<&str>) -> String {
        let base = format!("http://{}:{}{}", self.legacy_host, self.legacy_port, path);
        match query {
            Some(q) => format!("{}?{}", base, q),
            None => base,
        }
    }
}

/// Hop-by-hop headers per RFC 7230 / RFC 9110 that should not be forwarded across proxy hops.
pub fn is_hop_by_hop(name: &str) -> bool {
    matches!(
        name.to_ascii_lowercase().as_str(),
        "connection"
            | "keep-alive"
            | "proxy-authenticate"
            | "proxy-authorization"
            | "proxy-connection"
            | "te"
            | "trailer"
            | "trailers"
            | "transfer-encoding"
            | "upgrade"
            | "host"
    )
}

/// Extracts tokens listed in `Connection: token1, token2` headers which are also hop-by-hop.
pub fn get_connection_header_tokens(headers: &axum::http::HeaderMap) -> Vec<String> {
    let mut tokens = Vec::new();
    for val in headers.get_all(axum::http::header::CONNECTION) {
        if let Ok(s) = val.to_str() {
            for token in s.split(',') {
                let t = token.trim().to_ascii_lowercase();
                if !t.is_empty() {
                    tokens.push(t);
                }
            }
        }
    }
    tokens
}

/// Axum fallback handler: proxy any unmatched request to the Python API.
pub async fn fallback_to_python(State(gw): State<GatewayState>, req: Request) -> Response {
    proxy_to_python(gw, req).await
}

/// Proxy a request to the legacy Python API and return its response.
pub async fn proxy_to_python(gw: GatewayState, req: Request) -> Response {
    let (parts, body) = req.into_parts();
    let method = parts.method;
    let path = parts.uri.path().to_string();
    let query = parts.uri.query().map(|q| q.to_string());

    let url = gw.upstream_url(&path, query.as_deref());

    let reqwest_method =
        reqwest::Method::from_bytes(method.as_str().as_bytes()).unwrap_or(reqwest::Method::GET);

    // Build the upstream request
    let mut upstream_req = gw.client.request(reqwest_method, &url);

    // Forward non-hop-by-hop request headers
    let conn_tokens = get_connection_header_tokens(&parts.headers);
    for (name, value) in &parts.headers {
        let name_str = name.as_str();
        if !is_hop_by_hop(name_str) && !conn_tokens.iter().any(|t| t.eq_ignore_ascii_case(name_str))
        {
            upstream_req = upstream_req.header(name.as_str(), value.as_bytes());
        }
    }

    // Forward streaming body (avoid buffering full body in RAM)
    let has_body = parts
        .headers
        .contains_key(axum::http::header::CONTENT_LENGTH)
        || parts
            .headers
            .contains_key(axum::http::header::TRANSFER_ENCODING)
        || (method != axum::http::Method::GET && method != axum::http::Method::HEAD);

    if has_body {
        let body_stream = body.into_data_stream();
        upstream_req = upstream_req.body(reqwest::Body::wrap_stream(body_stream));
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
    let status =
        StatusCode::from_u16(upstream_resp.status().as_u16()).unwrap_or(StatusCode::BAD_GATEWAY);

    let mut response_builder = Response::builder().status(status);

    // Forward non-hop-by-hop headers from upstream response (Location, Cache-Control, etc.)
    let resp_conn_tokens = get_connection_header_tokens(upstream_resp.headers());
    for (name, value) in upstream_resp.headers() {
        let name_str = name.as_str();
        if !is_hop_by_hop(name_str)
            && !resp_conn_tokens
                .iter()
                .any(|t| t.eq_ignore_ascii_case(name_str))
        {
            response_builder = response_builder.header(name, value);
        }
    }

    // Mark this response as gateway-served for the observability middleware
    response_builder = response_builder.header("x-serve-mode", "gateway");

    // Stream body bytes back without buffering in RAM (Req 3.4, enables SSE and prevents OOM)
    let body_stream = upstream_resp.bytes_stream();
    let body = Body::from_stream(body_stream);

    response_builder
        .body(body)
        .unwrap_or_else(|_| upstream_unavailable())
}

/// HTTP 502 with standard error envelope `{"error": {"code": "UPSTREAM_UNAVAILABLE", "message": "Upstream service unavailable", "details": {}}}`.
fn upstream_unavailable() -> Response {
    let body = r#"{"error":{"code":"UPSTREAM_UNAVAILABLE","message":"Upstream service unavailable","details":{}}}"#;
    Response::builder()
        .status(StatusCode::BAD_GATEWAY)
        .header("content-type", "application/json")
        .header("x-serve-mode", "gateway")
        .body(Body::from(body))
        .unwrap()
}

#[cfg(test)]
mod tests {
    use super::*;
    use axum::http::HeaderMap;

    #[test]
    fn hop_by_hop_detection() {
        assert!(is_hop_by_hop("connection"));
        assert!(is_hop_by_hop("Connection"));
        assert!(is_hop_by_hop("keep-alive"));
        assert!(is_hop_by_hop("transfer-encoding"));
        assert!(is_hop_by_hop("upgrade"));
        assert!(is_hop_by_hop("host"));

        // End-to-end headers must NOT be flagged as hop-by-hop
        assert!(!is_hop_by_hop("location"));
        assert!(!is_hop_by_hop("cache-control"));
        assert!(!is_hop_by_hop("content-type"));
        assert!(!is_hop_by_hop("content-length"));
        assert!(!is_hop_by_hop("set-cookie"));
        assert!(!is_hop_by_hop("authorization"));
        assert!(!is_hop_by_hop("x-request-id"));
        assert!(!is_hop_by_hop("etag"));
    }

    #[test]
    fn connection_header_token_extraction() {
        let mut headers = HeaderMap::new();
        headers.insert(
            axum::http::header::CONNECTION,
            "close, X-Custom-Hop".parse().unwrap(),
        );

        let tokens = get_connection_header_tokens(&headers);
        assert_eq!(tokens, vec!["close", "x-custom-hop"]);
    }

    #[tokio::test]
    async fn upstream_unavailable_returns_standard_error_envelope() {
        let resp = upstream_unavailable();
        assert_eq!(resp.status(), StatusCode::BAD_GATEWAY);
        let body = axum::body::to_bytes(resp.into_body(), 4096).await.unwrap();
        let parsed: serde_json::Value = serde_json::from_slice(&body).unwrap();
        assert_eq!(parsed["error"]["code"], "UPSTREAM_UNAVAILABLE");
        assert_eq!(parsed["error"]["message"], "Upstream service unavailable");
    }
}
