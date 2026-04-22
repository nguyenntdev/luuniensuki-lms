#!/usr/bin/env python3
"""
Realtime AI Teacher worker.

Responsibilities:
- Keep one AI Teacher participant present for active live sessions.
- Consume `ai_voice_request` events from `live_events`.
- Generate answer via DeepSeek (or fallback pedagogy policy).
- Emit `ai_transcript_chunk` and `ai_voice_ready` events.

This worker is intentionally DB/event-driven so it can run independently
from the API process and still cooperate with existing frontend polling.
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
import time
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request as UrlRequest
from urllib.request import urlopen

from sqlalchemy import and_, create_engine, select
from sqlalchemy.orm import Session, sessionmaker

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from backend.config import settings  # noqa: E402
from backend.models import LiveEvent, LiveSession, LiveSessionStatus  # noqa: E402
from backend.services import live_ai_teacher as live_ai_teacher_service  # noqa: E402
from backend.services import live_sessions as live_session_service  # noqa: E402

logger = logging.getLogger("ai_teacher_realtime_worker")


def _deepseek_chat_url() -> str:
    base = settings.deepseek_base_url.rstrip("/")
    if base.endswith("/v1"):
        return f"{base}/chat/completions"
    return f"{base}/v1/chat/completions"


def _call_deepseek_chat(
    messages: list[dict[str, str]],
    *,
    temperature: float = 0.25,
) -> str:
    if not settings.deepseek_api_key:
        raise RuntimeError("Deepseek API key not configured")

    payload = {
        "model": settings.deepseek_model,
        "messages": messages,
        "temperature": temperature,
    }
    request = UrlRequest(
        _deepseek_chat_url(),
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {settings.deepseek_api_key}",
        },
    )

    max_retries = max(0, int(settings.deepseek_max_retries or 0))
    retryable_codes = {429, 500, 502, 503, 504}
    body: str | None = None

    for attempt in range(max_retries + 1):
        try:
            with urlopen(request, timeout=settings.deepseek_timeout_seconds) as response:
                body = response.read().decode("utf-8")
            break
        except HTTPError as exc:
            if attempt < max_retries and exc.code in retryable_codes:
                time.sleep(0.5 * (attempt + 1))
                continue
            raise RuntimeError(f"Deepseek request failed: {exc}") from exc
        except URLError as exc:
            if attempt < max_retries:
                time.sleep(0.5 * (attempt + 1))
                continue
            raise RuntimeError(f"Deepseek request failed: {exc}") from exc

    if not body:
        raise RuntimeError("Deepseek response was empty")
    try:
        parsed = json.loads(body)
    except json.JSONDecodeError as exc:
        raise RuntimeError("Deepseek response was not valid JSON") from exc

    answer = (
        parsed.get("choices", [{}])[0].get("message", {}).get("content", "").strip()
    )
    if not answer:
        raise RuntimeError("Deepseek response content is empty")
    return answer


def _call_deepseek_chat_stream(
    messages: list[dict[str, str]],
    *,
    temperature: float = 0.25,
):
    if not settings.deepseek_api_key:
        raise RuntimeError("Deepseek API key not configured")

    payload = {
        "model": settings.deepseek_model,
        "messages": messages,
        "temperature": temperature,
        "stream": True,
    }
    request = UrlRequest(
        _deepseek_chat_url(),
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {settings.deepseek_api_key}",
        },
    )

    try:
        with urlopen(request, timeout=settings.deepseek_timeout_seconds) as response:
            for line in response:
                line_str = line.decode("utf-8").strip()
                if not line_str:
                    continue
                if line_str == "data: [DONE]":
                    break
                if not line_str.startswith("data: "):
                    continue
                try:
                    chunk_data = json.loads(line_str[6:])
                except json.JSONDecodeError:
                    continue
                delta = (
                    chunk_data.get("choices", [{}])[0]
                    .get("delta", {})
                    .get("content", "")
                )
                if delta:
                    yield delta
    except (HTTPError, URLError) as exc:
        raise RuntimeError(f"Deepseek streaming request failed: {exc}") from exc


def _extract_question(payload: dict[str, Any]) -> str:
    for key in ("text", "message", "question", "utterance"):
        value = str(payload.get(key, "")).strip()
        if value:
            return value
    return ""


def _event_payload_dict(event: LiveEvent) -> dict[str, Any]:
    if isinstance(event.payload, dict):
        return dict(event.payload)
    return {}


def _mark_event_done(
    db: Session,
    *,
    event_id: Any,
    status: str,
    detail: str | None = None,
) -> None:
    event = db.get(LiveEvent, event_id)
    if event is None:
        return
    payload = _event_payload_dict(event)
    payload["_ai_worker_done"] = True
    payload["_ai_worker_status"] = status
    payload["_ai_worker_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    if detail:
        payload["_ai_worker_detail"] = detail[:400]
    event.payload = payload
    db.commit()


def _build_history_from_recent_events(
    db: Session,
    *,
    live_session_id: Any,
    limit: int = 8,
) -> list[dict[str, str]]:
    rows = (
        db.execute(
            select(LiveEvent)
            .where(
                and_(
                    LiveEvent.live_session_id == live_session_id,
                    LiveEvent.event_type.in_(
                        [
                            "ai_teacher_user_message",
                            "ai_teacher_reply",
                            "voice_user_final",
                            "ai_voice_ready",
                        ]
                    ),
                )
            )
            .order_by(LiveEvent.created_at.desc())
            .limit(max(2, limit * 3))
        )
        .scalars()
        .all()
    )

    messages: list[dict[str, str]] = []
    for row in reversed(rows):
        payload = _event_payload_dict(row)
        text = (
            str(payload.get("message") or payload.get("text") or payload.get("answer") or "")
            .strip()
        )
        if not text:
            continue
        if row.event_type in {"ai_teacher_reply", "ai_voice_ready"}:
            messages.append({"role": "assistant", "content": text[:3000]})
        else:
            messages.append({"role": "user", "content": text[:3000]})
    return messages[-limit:]


def _emit_partial_chunk(
    db: Session,
    *,
    live_session: LiveSession,
    ai_identity: str,
    request_id: str,
    source_event_id: str,
    mode: str,
    cluster: str,
    text: str,
    delta: str,
    seq: int,
    provider: str,
    model: str,
) -> None:
    live_session_service.record_live_event(
        db,
        live_session_id=live_session.id,
        event_type="ai_transcript_chunk",
        event_source="ai_agent",
        participant_identity=ai_identity,
        participant_user_id=None,
        payload={
            "request_id": request_id,
            "source_event_id": source_event_id,
            "mode": mode,
            "cluster": cluster,
            "partial": True,
            "seq": seq,
            "delta": delta,
            "text": text,
            "provider": provider,
            "model": model,
        },
    )


def _answer_one_voice_request(
    db: Session,
    *,
    live_session: LiveSession,
    event: LiveEvent,
) -> None:
    payload = _event_payload_dict(event)
    if payload.get("_ai_worker_done") is True:
        return

    question = _extract_question(payload)
    if not question:
        _mark_event_done(
            db,
            event_id=event.id,
            status="skipped",
            detail="empty_question",
        )
        return

    mode = live_ai_teacher_service.normalize_mode(str(payload.get("mode") or "hint-first"))
    request_id = str(payload.get("request_id") or event.id)

    ai_participant = live_session_service.ensure_ai_teacher_participant(
        db,
        live_session=live_session,
        display_name="AI Teacher",
        event_source="ai_agent",
    )

    cluster = live_ai_teacher_service.infer_heritage_cluster(
        message=question,
        session_title=live_session.title,
    )
    references = live_ai_teacher_service.collect_reference_sources(
        db,
        query=question,
        limit=3,
    )
    references_prompt = live_ai_teacher_service.format_reference_context(references)
    system_prompt = live_ai_teacher_service.build_system_prompt(
        mode=mode,
        session_title=live_session.title,
        learner_message=question,
    )
    if references_prompt:
        system_prompt = (
            f"{system_prompt}\n\n"
            "Nguon tham khao noi bo uu tien (chi dung de doi chieu, khong can gan ma [S#]):\n"
            f"{references_prompt}"
        )
    history = _build_history_from_recent_events(db, live_session_id=live_session.id, limit=8)
    messages = [
        {"role": "system", "content": system_prompt},
        *history,
        {"role": "user", "content": question},
    ]

    used_mock = False
    provider = "deepseek"
    model = settings.deepseek_model
    try:
        answer = ""
        stream_seq = 0
        buffer: list[str] = []
        for delta in _call_deepseek_chat_stream(messages, temperature=0.28):
            if not delta:
                continue
            answer = f"{answer}{delta}"
            buffer.append(delta)
            combined = "".join(buffer)
            should_flush = False
            if len(combined) >= 80:
                should_flush = True
            if len(combined) >= 20 and combined.rstrip().endswith((".", "?", "!", "\n", ":")):
                should_flush = True
            if should_flush:
                stream_seq += 1
                _emit_partial_chunk(
                    db,
                    live_session=live_session,
                    ai_identity=ai_participant.participant_identity,
                    request_id=request_id,
                    source_event_id=str(event.id),
                    mode=mode,
                    cluster=cluster,
                    text=answer,
                    delta=combined,
                    seq=stream_seq,
                    provider=provider,
                    model=model,
                )
                buffer = []

        if buffer:
            stream_seq += 1
            combined = "".join(buffer)
            _emit_partial_chunk(
                db,
                live_session=live_session,
                ai_identity=ai_participant.participant_identity,
                request_id=request_id,
                source_event_id=str(event.id),
                mode=mode,
                cluster=cluster,
                text=answer,
                delta=combined,
                seq=stream_seq,
                provider=provider,
                model=model,
            )

        if not answer.strip():
            answer = _call_deepseek_chat(messages, temperature=0.28)
    except Exception as exc:
        logger.warning(
            "DeepSeek failed for session=%s request=%s: %s",
            live_session.id,
            request_id,
            exc,
        )
        answer = live_ai_teacher_service.fallback_response(mode=mode, question=question)
        provider = "fallback_policy"
        model = "heritage-guidance-v1"
        used_mock = True

    suggested_actions = live_ai_teacher_service.build_suggested_actions(
        question=question,
        mode=mode,
        cluster=cluster,
    )
    checkpoint_prompt: str | None = None
    if live_ai_teacher_service.should_trigger_checkpoint(
        db,
        live_session_id=live_session.id,
        session_started_at=live_session.starts_at,
    ):
        checkpoint_prompt = live_ai_teacher_service.build_checkpoint_prompt(cluster=cluster)
        answer = (
            f"{answer.strip()}\n\n"
            f"Checkpoint nhanh: {checkpoint_prompt}"
        )
        live_session_service.record_live_event(
            db,
            live_session_id=live_session.id,
            event_type=live_ai_teacher_service.CHECKPOINT_EVENT_TYPE,
            event_source="ai_agent",
            participant_identity=ai_participant.participant_identity,
            participant_user_id=None,
            payload={
                "request_id": request_id,
                "cluster": cluster,
                "mode": mode,
                "prompt": checkpoint_prompt,
            },
        )

    common_payload = {
        "request_id": request_id,
        "source_event_id": str(event.id),
        "mode": mode,
        "cluster": cluster,
        "provider": provider,
        "model": model,
        "used_mock": used_mock,
        "text": answer,
        "references": references,
        "suggested_actions": suggested_actions,
        "checkpoint_prompt": checkpoint_prompt,
    }
    live_session_service.record_live_event(
        db,
        live_session_id=live_session.id,
        event_type="ai_transcript_chunk",
        event_source="ai_agent",
        participant_identity=ai_participant.participant_identity,
        participant_user_id=None,
        payload={**common_payload, "partial": False},
    )
    live_session_service.record_live_event(
        db,
        live_session_id=live_session.id,
        event_type="ai_voice_ready",
        event_source="ai_agent",
        participant_identity=ai_participant.participant_identity,
        participant_user_id=None,
        payload=common_payload,
    )

    _mark_event_done(db, event_id=event.id, status="ok")


def _process_live_session(db: Session, live_session: LiveSession) -> None:
    if live_session.status != LiveSessionStatus.live.value:
        return
    if not live_session_service.is_ai_enabled(live_session):
        return

    try:
        live_session_service.ensure_ai_teacher_participant(
            db,
            live_session=live_session,
            display_name="AI Teacher",
            event_source="ai_agent",
        )
    except Exception as exc:
        logger.warning("Cannot ensure AI presence for session=%s: %s", live_session.id, exc)
        return

    pending = (
        db.execute(
            select(LiveEvent)
            .where(
                and_(
                    LiveEvent.live_session_id == live_session.id,
                    LiveEvent.event_type == "ai_voice_request",
                )
            )
            .order_by(LiveEvent.created_at.asc())
            .limit(120)
        )
        .scalars()
        .all()
    )
    for event in pending:
        try:
            _answer_one_voice_request(
                db,
                live_session=live_session,
                event=event,
            )
        except Exception as exc:
            logger.exception(
                "Failed to handle ai_voice_request session=%s event=%s",
                live_session.id,
                event.id,
            )
            _mark_event_done(
                db,
                event_id=event.id,
                status="error",
                detail=str(exc),
            )


def run_worker(*, interval_seconds: float, max_sessions: int) -> None:
    engine = create_engine(settings.database_url, pool_pre_ping=True)
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

    logger.info(
        "AI realtime worker started (interval=%.2fs, deepseek=%s)",
        interval_seconds,
        "enabled" if settings.deepseek_api_key else "fallback_policy",
    )
    while True:
        loop_started = time.time()
        try:
            with SessionLocal() as db:
                sessions = (
                    db.execute(
                        select(LiveSession)
                        .where(LiveSession.status == LiveSessionStatus.live.value)
                        .order_by(LiveSession.created_at.desc())
                        .limit(max(1, max_sessions))
                    )
                    .scalars()
                    .all()
                )
                for live_session in sessions:
                    _process_live_session(db, live_session)
        except KeyboardInterrupt:
            logger.info("AI realtime worker stopped by keyboard interrupt")
            break
        except Exception:
            logger.exception("AI realtime worker loop failed")

        elapsed = time.time() - loop_started
        sleep_time = max(0.05, interval_seconds - elapsed)
        time.sleep(sleep_time)


def main() -> None:
    parser = argparse.ArgumentParser(description="AI Teacher realtime worker")
    parser.add_argument("--interval", type=float, default=1.0, help="Polling interval (seconds)")
    parser.add_argument(
        "--max-sessions",
        type=int,
        default=200,
        help="Max active sessions per loop",
    )
    parser.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
    )
    args = parser.parse_args()

    logging.basicConfig(
        level=getattr(logging, args.log_level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    )

    run_worker(
        interval_seconds=max(0.05, float(args.interval)),
        max_sessions=max(1, int(args.max_sessions)),
    )


if __name__ == "__main__":
    main()
