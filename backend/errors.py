from typing import Any, Optional

from fastapi import Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException


class AppError(Exception):
    def __init__(
        self,
        code: str,
        message: str,
        status_code: int = status.HTTP_400_BAD_REQUEST,
        details: Optional[dict] = None,
        headers: Optional[dict[str, str]] = None,
    ):
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        self.headers = headers


async def app_exception_handler(request: Request, exc: AppError):
    headers = dict(exc.headers) if exc.headers else {}
    if exc.status_code == status.HTTP_429_TOO_MANY_REQUESTS:
        retry_val = str(exc.details.get("retry_after_seconds", 3600)) if exc.details else "3600"
        headers.setdefault("Retry-After", retry_val)
        headers.setdefault("X-RateLimit-Limit", "5")
        headers.setdefault("X-RateLimit-Remaining", "0")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {"code": exc.code, "message": exc.message, "details": exc.details}
        },
        headers=headers if headers else None,
    )


async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    headers = dict(exc.headers) if getattr(exc, "headers", None) else {}
    if exc.status_code == status.HTTP_429_TOO_MANY_REQUESTS:
        headers.setdefault("Retry-After", "60")
        headers.setdefault("X-RateLimit-Limit", "5")
        headers.setdefault("X-RateLimit-Remaining", "0")
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"code": "HTTP_ERROR", "message": exc.detail, "details": {}}},
        headers=headers if headers else None,
    )


def _serialize_error_value(value: Any) -> Any:
    """Recursively convert bytes and other non-serializable types to strings."""
    if isinstance(value, bytes):
        try:
            return value.decode("utf-8")
        except UnicodeDecodeError:
            return value.decode("latin-1")
    elif isinstance(value, dict):
        return {k: _serialize_error_value(v) for k, v in value.items()}
    elif isinstance(value, list):
        return [_serialize_error_value(item) for item in value]
    elif isinstance(value, tuple):
        return tuple(_serialize_error_value(item) for item in value)
    else:
        return value


# Fields whose presence in an error location indicates sensitive submitted data.
# When a validation error targets one of these fields, even the human-readable
# message is replaced so it cannot reflect the submitted value.
SENSITIVE_FIELDS = {"password", "new_password", "current_password", "token", "secret"}


def _sanitize_validation_errors(raw_errors: Any) -> list:
    """Build a sanitized error list that exposes only field locations and messages.

    Never includes the submitted input values: the ``input`` and ``ctx`` keys
    produced by pydantic/FastAPI are explicitly dropped. When the failing field
    is sensitive, the message is replaced with a generic value so it cannot leak
    submitted data.
    """
    sanitized = []
    for error in raw_errors:
        loc = error.get("loc", ())
        # Normalize the location into a list of strings (tuple → list).
        loc_list = [str(_serialize_error_value(part)) for part in loc]

        is_sensitive = len(loc_list) > 0 and loc_list[-1] in SENSITIVE_FIELDS
        message = "invalid value" if is_sensitive else str(error.get("msg", ""))

        sanitized.append(
            {
                "loc": loc_list,
                "msg": message,
                "type": str(error.get("type", "")),
            }
        )
    return sanitized


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    # Only expose field locations, messages, and types — never submitted input.
    errors = _sanitize_validation_errors(exc.errors())

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Invalid request parameters",
                "details": {"errors": errors},
            }
        },
    )
