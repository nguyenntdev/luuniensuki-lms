from typing import Any

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
        details: dict = None,
    ):
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details or {}


async def app_exception_handler(request: Request, exc: AppError):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {"code": exc.code, "message": exc.message, "details": exc.details}
        },
    )


async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"code": "HTTP_ERROR", "message": exc.detail, "details": {}}},
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


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    # Serialize errors, converting any bytes to strings
    errors = _serialize_error_value(exc.errors())

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
