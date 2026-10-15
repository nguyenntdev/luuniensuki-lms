//! Typed application errors mapped to stable JSON responses.
//!
//! Task 1.9: implements the error envelope matching `backend/errors.py`.
//! Body shape: `{"error": {"code": "...", "message": "...", "details": {}}}`

use axum::{
    http::{HeaderValue, StatusCode},
    response::{IntoResponse, Response},
    Json,
};
use serde_json::{json, Value};

/// Application error enum. Each variant maps to a specific HTTP status
/// and JSON envelope matching what the Python FastAPI backend returns.
#[derive(Debug, thiserror::Error)]
pub enum AppError {
    /// 422 — validation error (mirrors FastAPI/Pydantic shape).
    #[error("validation error")]
    Validation { details: Value },

    /// Generic HTTP error (mirrors `http_exception_handler`).
    #[error("{message}")]
    Http { status: StatusCode, message: String },

    /// Domain-specific error with custom code.
    #[error("{message}")]
    Domain {
        status: StatusCode,
        code: String,
        message: String,
        details: Value,
    },

    /// 401 — authentication failure.
    /// Body exactly matches Python's `Could not validate credentials`.
    #[error("unauthorized")]
    Unauthorized,

    /// 502 — upstream service unreachable.
    #[error("upstream unavailable")]
    UpstreamUnavailable,

    /// 500 — unexpected internal error.
    #[error("internal error: {0}")]
    Internal(#[from] anyhow::Error),
}

impl IntoResponse for AppError {
    fn into_response(self) -> Response {
        match self {
            AppError::Validation { details } => {
                let body = json!({
                    "error": {
                        "code": "VALIDATION_ERROR",
                        "message": "Validation error",
                        "details": details
                    }
                });
                (StatusCode::UNPROCESSABLE_ENTITY, Json(body)).into_response()
            }

            AppError::Http { status, message } => {
                let body = json!({
                    "error": {
                        "code": "HTTP_ERROR",
                        "message": message,
                        "details": {}
                    }
                });
                (status, Json(body)).into_response()
            }

            AppError::Domain {
                status,
                code,
                message,
                details,
            } => {
                let body = json!({
                    "error": {
                        "code": code,
                        "message": message,
                        "details": details
                    }
                });
                (status, Json(body)).into_response()
            }

            AppError::Unauthorized => {
                let body = json!({
                    "error": {
                        "code": "HTTP_ERROR",
                        "message": "Could not validate credentials",
                        "details": {}
                    }
                });
                let mut resp = (StatusCode::UNAUTHORIZED, Json(body)).into_response();
                resp.headers_mut()
                    .insert("www-authenticate", HeaderValue::from_static("Bearer"));
                resp
            }

            AppError::UpstreamUnavailable => {
                let body = json!({
                    "error": {
                        "code": "UPSTREAM_UNAVAILABLE",
                        "message": "Upstream service unavailable",
                        "details": {}
                    }
                });
                (StatusCode::BAD_GATEWAY, Json(body)).into_response()
            }

            AppError::Internal(e) => {
                tracing::error!(error = %e, "internal server error");
                let body = json!({
                    "error": {
                        "code": "INTERNAL_SERVER_ERROR",
                        "message": "Internal server error",
                        "details": {}
                    }
                });
                (StatusCode::INTERNAL_SERVER_ERROR, Json(body)).into_response()
            }
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use axum::body::to_bytes;

    #[tokio::test]
    async fn unauthorized_matches_python_shape() {
        let resp = AppError::Unauthorized.into_response();

        assert_eq!(resp.status(), StatusCode::UNAUTHORIZED);
        assert_eq!(resp.headers().get("www-authenticate").unwrap(), "Bearer");

        let body = to_bytes(resp.into_body(), 4096).await.unwrap();
        let parsed: Value = serde_json::from_slice(&body).unwrap();
        assert_eq!(parsed["error"]["code"], "HTTP_ERROR");
        assert_eq!(parsed["error"]["message"], "Could not validate credentials");
    }

    #[tokio::test]
    async fn upstream_unavailable_returns_standard_envelope() {
        let resp = AppError::UpstreamUnavailable.into_response();

        assert_eq!(resp.status(), StatusCode::BAD_GATEWAY);

        let body = to_bytes(resp.into_body(), 4096).await.unwrap();
        let parsed: Value = serde_json::from_slice(&body).unwrap();
        assert_eq!(parsed["error"]["code"], "UPSTREAM_UNAVAILABLE");
        assert_eq!(parsed["error"]["message"], "Upstream service unavailable");
        assert_eq!(parsed["error"]["details"], json!({}));
    }

    #[tokio::test]
    async fn validation_error_shape() {
        let resp = AppError::Validation {
            details: json!({"errors": [{"field": "email", "msg": "required"}]}),
        }
        .into_response();

        assert_eq!(resp.status(), StatusCode::UNPROCESSABLE_ENTITY);

        let body = to_bytes(resp.into_body(), 4096).await.unwrap();
        let parsed: Value = serde_json::from_slice(&body).unwrap();
        assert_eq!(parsed["error"]["code"], "VALIDATION_ERROR");
    }
}
