"""Lightweight circuit breaker for live AI providers."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from threading import Lock

from ..config import settings


@dataclass
class _ProviderState:
    failures: int = 0
    open_until: datetime | None = None
    last_error: str | None = None


_LOCK = Lock()
_STATES: dict[str, _ProviderState] = {}


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _state(provider: str) -> _ProviderState:
    key = str(provider or "unknown").strip().lower() or "unknown"
    if key not in _STATES:
        _STATES[key] = _ProviderState()
    return _STATES[key]


def assert_provider_available(provider: str) -> None:
    now = _utcnow()
    with _LOCK:
        item = _state(provider)
        if item.open_until and item.open_until > now:
            wait_seconds = int((item.open_until - now).total_seconds())
            raise RuntimeError(
                f"Provider {provider} is temporarily unavailable "
                f"(circuit open, retry in {max(1, wait_seconds)}s)"
            )
        if item.open_until and item.open_until <= now:
            item.open_until = None
            item.failures = 0
            item.last_error = None


def record_success(provider: str) -> None:
    with _LOCK:
        item = _state(provider)
        item.failures = 0
        item.open_until = None
        item.last_error = None


def record_failure(provider: str, error: str | None = None) -> None:
    threshold = max(1, int(settings.live_ai_circuit_breaker_failures or 5))
    recovery_seconds = max(5, int(settings.live_ai_circuit_breaker_recovery_seconds or 45))
    with _LOCK:
        item = _state(provider)
        item.failures += 1
        item.last_error = (str(error or "").strip() or None)
        if item.failures >= threshold:
            item.open_until = _utcnow() + timedelta(seconds=recovery_seconds)


def snapshot() -> dict[str, dict[str, str | int | None]]:
    now = _utcnow()
    with _LOCK:
        result: dict[str, dict[str, str | int | None]] = {}
        for provider, item in _STATES.items():
            result[provider] = {
                "failures": item.failures,
                "open_until": item.open_until.isoformat() if item.open_until else None,
                "is_open": bool(item.open_until and item.open_until > now),
                "last_error": item.last_error,
            }
        return result
