"""
Cooperative cancellation for the real-time conversational AI teacher (Path B).

When a learner barges in while the AI is speaking, the in-flight turn must stop
promptly: the DeepSeek token stream and the streaming TTS for that ``request_id``
should abort instead of running to completion. This module provides the small,
self-contained primitives for that — plus pure event-payload builders for the
``barge_in`` and ``ai_turn_state`` live_events.

Everything here is I/O-free and dependency-free (stdlib ``threading`` only), so
it is fully unit-testable without audio, network, or a DB. The realtime worker /
audio bridge (later tasks) wires these in:

    registry = CancellationRegistry()
    token = registry.token(request_id)          # before starting a turn
    for delta in cancellable(deepseek_stream, token):
        ...                                      # stops as soon as cancelled
    # on barge-in (possibly from another thread):
    registry.cancel(request_id)                  # aborts the loop above
    # when the turn finishes (normally or cancelled):
    registry.clear(request_id)

Cancellation is *cooperative*: a token being cancelled does not forcibly kill a
thread; the producing/consuming code checks the token (directly, via
:func:`cancellable`, or via :meth:`CancelToken.raise_if_cancelled`) and bails.
"""

from __future__ import annotations

import threading
from typing import Any, Iterable, Iterator, Optional, TypeVar

T = TypeVar("T")


class Cancelled(Exception):
    """Raised by :meth:`CancelToken.raise_if_cancelled` when cancelled."""

    def __init__(self, request_id: Optional[str] = None) -> None:
        self.request_id = request_id
        super().__init__(
            f"cancelled: {request_id}" if request_id is not None else "cancelled"
        )


class CancelToken:
    """A one-shot, thread-safe cancellation flag.

    Backed by :class:`threading.Event` so it is safe to set from a barge-in
    callback on one thread while the worker thread reads it. Once cancelled it
    stays cancelled (one-shot).
    """

    def __init__(self, request_id: Optional[str] = None) -> None:
        self.request_id = request_id
        self._event = threading.Event()

    @property
    def cancelled(self) -> bool:
        """Whether this token has been cancelled."""
        return self._event.is_set()

    def cancel(self) -> None:
        """Mark this token cancelled. Idempotent."""
        self._event.set()

    def raise_if_cancelled(self) -> None:
        """Raise :class:`Cancelled` if this token has been cancelled."""
        if self._event.is_set():
            raise Cancelled(self.request_id)


class CancellationRegistry:
    """Thread-safe map of ``request_id -> CancelToken``.

    The worker creates/looks up a token per in-flight turn; a barge-in handler
    cancels by ``request_id`` without needing a direct reference to the token.
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._tokens: dict[str, CancelToken] = {}

    def token(self, request_id: str) -> CancelToken:
        """Get the existing token for ``request_id`` or create one.

        Returns the same :class:`CancelToken` instance for repeated calls with
        the same ``request_id`` (until :meth:`clear` removes it).
        """
        with self._lock:
            tok = self._tokens.get(request_id)
            if tok is None:
                tok = CancelToken(request_id)
                self._tokens[request_id] = tok
            return tok

    def cancel(self, request_id: str) -> bool:
        """Cancel the token for ``request_id``.

        Returns ``True`` if a token existed (and was cancelled), ``False`` if no
        token was registered for ``request_id``.
        """
        with self._lock:
            tok = self._tokens.get(request_id)
        if tok is None:
            return False
        tok.cancel()
        return True

    def is_cancelled(self, request_id: str) -> bool:
        """Whether a token exists for ``request_id`` and has been cancelled."""
        with self._lock:
            tok = self._tokens.get(request_id)
        return tok is not None and tok.cancelled

    def clear(self, request_id: str) -> None:
        """Remove the token for ``request_id`` (call when a turn finishes).

        No-op if no token is registered.
        """
        with self._lock:
            self._tokens.pop(request_id, None)


def cancellable(stream_iter: Iterable[T], token: CancelToken) -> Iterator[T]:
    """Yield items from ``stream_iter`` until ``token`` is cancelled.

    Wraps an iterator/generator (e.g. the DeepSeek ``_call_deepseek_chat_stream``
    generator) so it aborts promptly on barge-in: the token is checked *before*
    each item is yielded, so once cancelled no further items are produced. The
    underlying iterator is closed if it supports ``close()`` (generators do), so
    the producer can run its ``finally`` cleanup.
    """
    iterator = iter(stream_iter)
    try:
        for item in iterator:
            if token.cancelled:
                return
            yield item
            # Re-check after yielding so a cancel that arrives while the
            # consumer is processing this item stops the next iteration.
            if token.cancelled:
                return
    finally:
        close = getattr(iterator, "close", None)
        if callable(close):
            close()


# --------------------------------------------------------------------------- #
# Pure event-payload builders (return plain dicts; no I/O).
# --------------------------------------------------------------------------- #


def build_barge_in_payload(
    request_id: str, source_event_id: Optional[str] = None
) -> dict[str, Any]:
    """Payload for a ``barge_in`` live_event.

    Records that the in-flight AI turn ``request_id`` was interrupted by the
    learner. ``source_event_id`` optionally links the triggering event (e.g. the
    learner's speech-start / partial transcript event).
    """
    payload: dict[str, Any] = {"request_id": request_id}
    if source_event_id is not None:
        payload["source_event_id"] = source_event_id
    return payload


def build_turn_state_payload(request_id: str, state: str) -> dict[str, Any]:
    """Payload for an ``ai_turn_state`` live_event.

    ``state`` is the turn FSM state string (e.g. ``idle``/``listening``/
    ``thinking``/``speaking`` from :mod:`backend.services.live_turn`).
    """
    return {"request_id": request_id, "state": state}
