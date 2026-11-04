"""In-memory observability metrics for live AI session flows."""

from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass
from datetime import datetime, timezone
from threading import Lock
from typing import Any

from ..config import settings


@dataclass
class _Point:
    ts: datetime
    session_id: str | None
    operation: str
    provider: str
    latency_ms: float
    ok: bool
    drop: bool
    tokens_in: int
    tokens_out: int
    provider_mode: str = "live"
    guardrail_status: str = "passed"
    is_fallback: bool = False
    is_synthetic: bool = False


_LOCK = Lock()
_POINTS: deque[_Point] = deque(maxlen=max(500, int(settings.live_ai_observability_max_points or 5000)))


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def record_point(
    *,
    session_id: str | None,
    operation: str,
    provider: str,
    latency_ms: float,
    ok: bool,
    drop: bool = False,
    tokens_in: int = 0,
    tokens_out: int = 0,
    provider_mode: str = "live",
    guardrail_status: str = "passed",
    is_fallback: bool = False,
    is_synthetic: bool = False,
) -> None:
    if not bool(settings.live_ai_enable_observability):
        return

    prov = str(provider or "unknown").strip() or "unknown"
    resolved_mode = str(provider_mode or "live").strip() or "live"
    if (
        is_fallback
        or is_synthetic
        or prov in ("fallback_policy", "guardrail", "mock", "demo")
    ) and resolved_mode == "live":
        resolved_mode = "guardrail" if prov == "guardrail" else "fallback"

    point = _Point(
        ts=_utcnow(),
        session_id=(str(session_id).strip() or None) if session_id else None,
        operation=str(operation or "unknown").strip() or "unknown",
        provider=prov,
        latency_ms=max(0.0, float(latency_ms or 0.0)),
        ok=bool(ok),
        drop=bool(drop),
        tokens_in=max(0, int(tokens_in or 0)),
        tokens_out=max(0, int(tokens_out or 0)),
        provider_mode=resolved_mode,
        guardrail_status=str(guardrail_status or "passed").strip() or "passed",
        is_fallback=bool(is_fallback),
        is_synthetic=bool(is_synthetic),
    )

    with _LOCK:
        _POINTS.append(point)


def snapshot(*, session_id: str | None = None) -> dict[str, Any]:
    with _LOCK:
        points = list(_POINTS)

    sid = str(session_id).strip() if session_id else None
    if sid:
        points = [item for item in points if item.session_id == sid]

    total = len(points)
    if total == 0:
        return {
            "total_requests": 0,
            "success_rate": 1.0,
            "error_budget": 1.0,
            "drop_rate": 0.0,
            "p95_latency_ms": 0.0,
            "avg_latency_ms": 0.0,
            "token_usage": {"input": 0, "output": 0, "total": 0},
            "by_operation": {},
            "by_provider": {},
            "by_provider_mode": {},
            "guardrail_stats": {"passed": 0, "blocked": 0, "bypassed": 0, "not_evaluated": 0},
            "fallback_count": 0,
            "synthetic_count": 0,
            "generated_at": _utcnow().isoformat(),
        }

    latencies = sorted(item.latency_ms for item in points)
    p95_index = max(0, min(len(latencies) - 1, int(round(len(latencies) * 0.95)) - 1))
    ok_count = sum(1 for item in points if item.ok)
    drop_count = sum(1 for item in points if item.drop)

    op_stats: dict[str, dict[str, float | int]] = defaultdict(
        lambda: {"count": 0, "ok": 0, "drop": 0, "latency_ms": 0.0}
    )
    provider_stats: dict[str, dict[str, int]] = defaultdict(
        lambda: {"count": 0, "ok": 0, "drop": 0}
    )
    mode_stats: dict[str, dict[str, int]] = defaultdict(
        lambda: {"count": 0, "ok": 0, "drop": 0}
    )
    guardrail_counts = {"passed": 0, "blocked": 0, "bypassed": 0, "not_evaluated": 0}
    fallback_total = 0
    synthetic_total = 0

    token_in = 0
    token_out = 0
    for item in points:
        op = op_stats[item.operation]
        op["count"] += 1
        op["ok"] += 1 if item.ok else 0
        op["drop"] += 1 if item.drop else 0
        op["latency_ms"] += float(item.latency_ms)

        prov = provider_stats[item.provider]
        prov["count"] += 1
        prov["ok"] += 1 if item.ok else 0
        prov["drop"] += 1 if item.drop else 0

        mode_entry = mode_stats[item.provider_mode]
        mode_entry["count"] += 1
        mode_entry["ok"] += 1 if item.ok else 0
        mode_entry["drop"] += 1 if item.drop else 0

        g_status = item.guardrail_status or "passed"
        guardrail_counts[g_status] = guardrail_counts.get(g_status, 0) + 1

        if item.is_fallback:
            fallback_total += 1
        if item.is_synthetic:
            synthetic_total += 1

        token_in += item.tokens_in
        token_out += item.tokens_out

    for op_data in op_stats.values():
        count = int(op_data["count"] or 0)
        op_data["avg_latency_ms"] = round(
            (float(op_data["latency_ms"]) / count) if count else 0.0,
            2,
        )
        op_data.pop("latency_ms", None)

    return {
        "total_requests": total,
        "success_rate": round(ok_count / total, 4),
        "error_budget": round((total - (total - ok_count)) / total, 4),
        "drop_rate": round(drop_count / total, 4),
        "p95_latency_ms": round(latencies[p95_index], 2),
        "avg_latency_ms": round(sum(latencies) / total, 2),
        "token_usage": {
            "input": token_in,
            "output": token_out,
            "total": token_in + token_out,
        },
        "by_operation": dict(op_stats),
        "by_provider": dict(provider_stats),
        "by_provider_mode": dict(mode_stats),
        "guardrail_stats": guardrail_counts,
        "fallback_count": fallback_total,
        "synthetic_count": synthetic_total,
        "generated_at": _utcnow().isoformat(),
    }
