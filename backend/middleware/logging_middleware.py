# -*- coding: utf-8 -*-
"""Structured Request Logging Middleware.

Ticket V5-T086 / Wave W08-A06.
Emits structured JSON access logs with correlation ID, request ID,
latency, status, and zero PII.
"""
from __future__ import annotations

import logging
import time
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from ..logging_config import AlertRouter, get_correlation_id, get_request_id

logger = logging.getLogger("luuniensuki.api.access")


class StructuredLoggingMiddleware(BaseHTTPMiddleware):
    """Logs HTTP request lifecycle with timing, status, and trace correlation."""

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        start_time = time.time()
        method = request.method
        path = request.url.path

        # Determine client IP safely without raw PII leak
        client_ip = "unknown"
        if request.client and request.client.host:
            client_ip = request.client.host

        response: Response
        try:
            response = await call_next(request)
        except Exception as exc:
            duration_ms = round((time.time() - start_time) * 1000, 2)
            corr_id = get_correlation_id()
            req_id = get_request_id()

            logger.error(
                "Unhandled server error processing request: %s %s (%s)",
                method,
                path,
                str(exc),
                extra={
                    "method": method,
                    "path": path,
                    "status_code": 500,
                    "duration_ms": duration_ms,
                    "client_ip": client_ip,
                    "correlation_id": corr_id,
                    "request_id": req_id,
                },
                exc_info=True,
            )

            # Trigger alert routing for unhandled 5xx
            AlertRouter.get_instance().route_alert(
                level="CRITICAL",
                event_type="unhandled_exception",
                message=f"500 Internal Server Error: {method} {path}",
                details={
                    "method": method,
                    "path": path,
                    "duration_ms": duration_ms,
                    "error": str(exc),
                },
                correlation_id=corr_id,
                request_id=req_id,
            )
            raise

        duration_ms = round((time.time() - start_time) * 1000, 2)
        status_code = response.status_code
        corr_id = get_correlation_id()
        req_id = get_request_id()

        extra_info = {
            "method": method,
            "path": path,
            "status_code": status_code,
            "duration_ms": duration_ms,
            "client_ip": client_ip,
            "correlation_id": corr_id,
            "request_id": req_id,
        }

        if status_code >= 500:
            logger.error(
                "Request completed with server error: %s %s [%d] (%sms)",
                method,
                path,
                status_code,
                duration_ms,
                extra=extra_info,
            )
        elif status_code >= 400:
            logger.warning(
                "Request completed with client error: %s %s [%d] (%sms)",
                method,
                path,
                status_code,
                duration_ms,
                extra=extra_info,
            )
        else:
            logger.info(
                "Request completed: %s %s [%d] (%sms)",
                method,
                path,
                status_code,
                duration_ms,
                extra=extra_info,
            )

        return response
