# -*- coding: utf-8 -*-
"""Correlation and Request ID propagation middleware.

Ticket V5-T086 / Wave W08-A06.
Ensures every request has a correlation_id and request_id propagated
through ContextVars, request state, and response headers.
"""
from __future__ import annotations

import uuid
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from ..logging_config import (
    reset_correlation_id,
    reset_request_id,
    set_correlation_id,
    set_request_id,
)

CORRELATION_ID_HEADER = "x-correlation-id"
REQUEST_ID_HEADER = "x-request-id"


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    """Propagates or mints correlation_id and request_id across the request lifecycle."""

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        # Extract headers (case-insensitive lookup via starlette headers)
        incoming_correlation_id = (
            request.headers.get("x-correlation-id")
            or request.headers.get("x-correlation-id".lower())
            or ""
        ).strip()

        incoming_request_id = (
            request.headers.get("x-request-id")
            or request.headers.get("x-request-id".lower())
            or ""
        ).strip()

        # Derive IDs with fallback to UUID4
        if incoming_correlation_id:
            correlation_id = incoming_correlation_id
            request_id = incoming_request_id or f"req-{uuid.uuid4().hex[:12]}"
        elif incoming_request_id:
            request_id = incoming_request_id
            correlation_id = incoming_request_id
        else:
            shared_id = uuid.uuid4().hex
            correlation_id = f"corr-{shared_id[:12]}"
            request_id = f"req-{shared_id[12:24]}"

        # Establish async context variables
        token_cid = set_correlation_id(correlation_id)
        token_rid = set_request_id(request_id)

        # Attach to request state for handler access
        request.state.correlation_id = correlation_id
        request.state.request_id = request_id

        try:
            response = await call_next(request)
            response.headers["X-Correlation-ID"] = correlation_id
            response.headers["X-Request-ID"] = request_id
            return response
        finally:
            reset_correlation_id(token_cid)
            reset_request_id(token_rid)
