"""Tests for cooperative cancellation (Task 5.2).

Covers the self-contained primitives in ``backend/services/live_cancel.py``:
the ``CancellationRegistry`` get-or-create / cancel / clear lifecycle, the
``CancelToken`` flag + ``raise_if_cancelled``, the ``cancellable`` generator
wrapper that aborts an in-flight stream on barge-in, the pure event-payload
builders, and a concurrency smoke test proving a cancel from another thread is
observed.

Validates: Requirements (Task 5.2 — make the DeepSeek streaming call cancellable
via a cooperative cancel token keyed by request_id; Task 5.1 — barge_in +
ai_turn_state event payloads).
"""

from __future__ import annotations

import sys
import threading
import time
from pathlib import Path

import pytest

# Mirror the repo's existing test bootstrap: make the repo root importable so
# ``backend.services`` resolves regardless of the pytest invocation cwd.
REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from backend.services.live_cancel import (  # noqa: E402
    Cancelled,
    CancellationRegistry,
    CancelToken,
    build_barge_in_payload,
    build_turn_state_payload,
    cancellable,
)


# --------------------------------------------------------------------------- #
# CancellationRegistry: get-or-create, cancel, is_cancelled, clear
# --------------------------------------------------------------------------- #


def test_token_get_or_create_returns_same_instance() -> None:
    reg = CancellationRegistry()
    a = reg.token("req-1")
    b = reg.token("req-1")
    assert a is b


def test_token_distinct_ids_get_distinct_tokens() -> None:
    reg = CancellationRegistry()
    a = reg.token("req-1")
    b = reg.token("req-2")
    assert a is not b


def test_cancel_existing_token_sets_is_cancelled_and_returns_true() -> None:
    reg = CancellationRegistry()
    tok = reg.token("req-1")
    assert reg.is_cancelled("req-1") is False
    assert tok.cancelled is False

    assert reg.cancel("req-1") is True
    assert reg.is_cancelled("req-1") is True
    assert tok.cancelled is True


def test_cancel_unknown_id_returns_false() -> None:
    reg = CancellationRegistry()
    assert reg.cancel("nope") is False


def test_is_cancelled_unknown_id_is_false() -> None:
    reg = CancellationRegistry()
    assert reg.is_cancelled("nope") is False


def test_clear_removes_token() -> None:
    reg = CancellationRegistry()
    reg.token("req-1")
    reg.clear("req-1")
    assert reg.is_cancelled("req-1") is False
    # After clear, a fresh token is minted (not the cancelled one).
    new_tok = reg.token("req-1")
    assert new_tok.cancelled is False


def test_clear_is_noop_for_unknown_id() -> None:
    reg = CancellationRegistry()
    reg.clear("nope")  # must not raise


def test_clear_then_cancel_returns_false() -> None:
    reg = CancellationRegistry()
    reg.token("req-1")
    reg.clear("req-1")
    assert reg.cancel("req-1") is False


# --------------------------------------------------------------------------- #
# CancelToken: cancelled flag, idempotent cancel, raise_if_cancelled
# --------------------------------------------------------------------------- #


def test_token_starts_uncancelled() -> None:
    tok = CancelToken("req-1")
    assert tok.cancelled is False


def test_token_cancel_is_idempotent() -> None:
    tok = CancelToken("req-1")
    tok.cancel()
    tok.cancel()
    assert tok.cancelled is True


def test_raise_if_cancelled_noop_when_not_cancelled() -> None:
    tok = CancelToken("req-1")
    tok.raise_if_cancelled()  # must not raise


def test_raise_if_cancelled_raises_after_cancel() -> None:
    tok = CancelToken("req-1")
    tok.cancel()
    with pytest.raises(Cancelled) as exc_info:
        tok.raise_if_cancelled()
    assert exc_info.value.request_id == "req-1"


# --------------------------------------------------------------------------- #
# cancellable: yields all when not cancelled; stops early once cancelled
# --------------------------------------------------------------------------- #


def test_cancellable_yields_all_items_when_not_cancelled() -> None:
    tok = CancelToken("req-1")
    items = list(cancellable([1, 2, 3, 4], tok))
    assert items == [1, 2, 3, 4]


def test_cancellable_yields_nothing_if_cancelled_before_iteration() -> None:
    tok = CancelToken("req-1")
    tok.cancel()
    items = list(cancellable([1, 2, 3], tok))
    assert items == []


def test_cancellable_stops_early_when_cancelled_mid_iteration() -> None:
    """Cancel after consuming N items; no further items are produced."""
    tok = CancelToken("req-1")
    produced: list[int] = []

    def source() -> "object":
        for i in range(100):
            produced.append(i)  # records what the producer actually generated
            yield i

    out: list[int] = []
    for value in cancellable(source(), tok):
        out.append(value)
        if value == 2:
            tok.cancel()  # barge-in mid-stream

    # Consumer stopped right after the cancel.
    assert out == [0, 1, 2]
    # The wrapper did not pull the entire upstream generator dry; it stopped
    # promptly rather than producing all 100 items.
    assert produced == [0, 1, 2]


def test_cancellable_closes_underlying_generator() -> None:
    """The wrapped generator's finally/cleanup runs when we stop early."""
    tok = CancelToken("req-1")
    closed = {"value": False}

    def source() -> "object":
        try:
            for i in range(100):
                yield i
        finally:
            closed["value"] = True

    gen = cancellable(source(), tok)
    assert next(gen) == 0
    tok.cancel()
    # Exhaust the wrapper: it should return and close the upstream generator.
    assert list(gen) == []
    assert closed["value"] is True


def test_cancellable_simulated_deepseek_stream_aborts_on_barge_in() -> None:
    """Wrapping a DeepSeek-like token generator aborts promptly on barge-in."""
    tok = CancelToken("req-deepseek")
    deltas = ["Hello", " there", ", how", " can", " I", " help", "?"]

    def deepseek_like():
        for d in deltas:
            yield d

    collected: list[str] = []
    for delta in cancellable(deepseek_like(), tok):
        collected.append(delta)
        if "".join(collected) == "Hello there":
            tok.cancel()  # learner barges in after two deltas

    assert collected == ["Hello", " there"]


# --------------------------------------------------------------------------- #
# Pure event-payload builders
# --------------------------------------------------------------------------- #


def test_build_barge_in_payload_without_source_event() -> None:
    payload = build_barge_in_payload("req-1")
    assert payload == {"request_id": "req-1"}
    assert "source_event_id" not in payload


def test_build_barge_in_payload_with_source_event() -> None:
    payload = build_barge_in_payload("req-1", source_event_id="evt-9")
    assert payload == {"request_id": "req-1", "source_event_id": "evt-9"}


def test_build_turn_state_payload_shape() -> None:
    payload = build_turn_state_payload("req-1", "speaking")
    assert payload == {"request_id": "req-1", "state": "speaking"}


# --------------------------------------------------------------------------- #
# Concurrency smoke test: cancel from another thread is observed
# --------------------------------------------------------------------------- #


def test_cancel_from_another_thread_is_observed() -> None:
    reg = CancellationRegistry()
    tok = reg.token("req-1")
    started = threading.Event()

    def canceller() -> None:
        started.wait(timeout=1.0)
        reg.cancel("req-1")

    t = threading.Thread(target=canceller)
    t.start()
    try:
        assert tok.cancelled is False
        started.set()
        # Spin briefly until the other thread's cancel becomes visible.
        deadline = time.monotonic() + 1.0
        while time.monotonic() < deadline and not reg.is_cancelled("req-1"):
            time.sleep(0.001)
        assert reg.is_cancelled("req-1") is True
        assert tok.cancelled is True
    finally:
        t.join(timeout=1.0)
    assert not t.is_alive()


def test_cancellable_loop_stops_when_cancelled_from_another_thread() -> None:
    """End-to-end: a worker-thread consuming a stream stops when another thread
    cancels via the registry."""
    reg = CancellationRegistry()
    tok = reg.token("req-1")
    consumed: list[int] = []

    def slow_source():
        for i in range(1000):
            time.sleep(0.001)
            yield i

    def worker() -> None:
        for value in cancellable(slow_source(), tok):
            consumed.append(value)

    t = threading.Thread(target=worker)
    t.start()
    # Let a few items flow, then barge in from this thread.
    time.sleep(0.05)
    reg.cancel("req-1")
    t.join(timeout=2.0)

    assert not t.is_alive()
    # It stopped well before exhausting all 1000 items.
    assert len(consumed) < 1000
