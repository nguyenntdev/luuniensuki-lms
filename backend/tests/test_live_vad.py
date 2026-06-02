"""Tests for the pure VAD endpointing policy (Wave 0 Task 2).

Plain pytest functions; no audio, network, or DB. Covers the min-speech guard,
exactly-once endpoint per trailing-silence window, blip suppression, single
speech_start emission, and partial_flush_due boundaries.
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from backend.services.live_vad import (  # noqa: E402
    END_SILENCE_MS,
    MIN_SPEECH_MS,
    PARTIAL_FLUSH_CHARS,
    PARTIAL_FLUSH_MS,
    EndpointDetector,
    VadFrame,
    partial_flush_due,
)


FRAME_MS = 20


def _feed(detector: EndpointDetector, frames):
    """Push a list of frames, returning the list of events produced."""
    return [detector.push(f) for f in frames]


def _make_frames(start_ms: int, count: int, *, is_speech: bool, step_ms: int = FRAME_MS):
    """Build a contiguous run of frames at ``step_ms`` spacing."""
    return [
        VadFrame(ts_ms=start_ms + i * step_ms, is_speech=is_speech, energy=1.0 if is_speech else 0.0)
        for i in range(count)
    ]


# --- no endpoint before MIN_SPEECH -------------------------------------------

def test_no_endpoint_before_min_speech() -> None:
    det = EndpointDetector()
    # Speech shorter than MIN_SPEECH_MS, then a long silence: must NOT endpoint.
    short_speech_frames = (MIN_SPEECH_MS // FRAME_MS) - 2  # safely under the guard
    assert short_speech_frames > 0
    ts = 0
    speech = _make_frames(ts, short_speech_frames, is_speech=True)
    ts = speech[-1].ts_ms + FRAME_MS
    silence = _make_frames(ts, (END_SILENCE_MS // FRAME_MS) + 5, is_speech=False)

    events = _feed(det, speech + silence)
    assert "endpoint" not in events


def test_endpoint_fires_once_min_speech_met() -> None:
    det = EndpointDetector()
    # Enough speech (>= MIN_SPEECH_MS) then enough silence (>= END_SILENCE_MS).
    speech = _make_frames(0, (MIN_SPEECH_MS // FRAME_MS) + 5, is_speech=True)
    ts = speech[-1].ts_ms + FRAME_MS
    silence = _make_frames(ts, (END_SILENCE_MS // FRAME_MS) + 5, is_speech=False)

    events = _feed(det, speech + silence)
    assert events.count("endpoint") == 1


# --- endpoint exactly once per trailing-silence window -----------------------

def test_endpoint_exactly_once_per_silence_window() -> None:
    det = EndpointDetector()
    speech = _make_frames(0, (MIN_SPEECH_MS // FRAME_MS) + 5, is_speech=True)
    ts = speech[-1].ts_ms + FRAME_MS
    # Far more silence than the threshold — endpoint must still fire exactly once.
    silence = _make_frames(ts, (END_SILENCE_MS // FRAME_MS) * 4, is_speech=False)

    events = _feed(det, speech + silence)
    assert events.count("endpoint") == 1
    # Endpoint should land right at the frame crossing END_SILENCE_MS, not later.
    endpoint_index = events.index("endpoint")
    silence_events_after = events[endpoint_index + 1 :]
    assert "endpoint" not in silence_events_after


def test_two_utterances_each_endpoint_once() -> None:
    det = EndpointDetector()
    # First utterance.
    speech1 = _make_frames(0, (MIN_SPEECH_MS // FRAME_MS) + 5, is_speech=True)
    ts = speech1[-1].ts_ms + FRAME_MS
    silence1 = _make_frames(ts, (END_SILENCE_MS // FRAME_MS) + 3, is_speech=False)
    ts = silence1[-1].ts_ms + FRAME_MS
    # Second utterance.
    speech2 = _make_frames(ts, (MIN_SPEECH_MS // FRAME_MS) + 5, is_speech=True)
    ts = speech2[-1].ts_ms + FRAME_MS
    silence2 = _make_frames(ts, (END_SILENCE_MS // FRAME_MS) + 3, is_speech=False)

    events = _feed(det, speech1 + silence1 + speech2 + silence2)
    assert events.count("endpoint") == 2
    assert events.count("speech_start") == 2


# --- blips never endpoint -----------------------------------------------------

def test_blip_then_silence_no_endpoint() -> None:
    det = EndpointDetector()
    # A single short blip well under MIN_SPEECH_MS.
    blip = _make_frames(0, 3, is_speech=True)  # 60ms << 300ms
    ts = blip[-1].ts_ms + FRAME_MS
    silence = _make_frames(ts, (END_SILENCE_MS // FRAME_MS) + 5, is_speech=False)

    events = _feed(det, blip + silence)
    assert "endpoint" not in events
    # The blip still announced speech_start exactly once.
    assert events.count("speech_start") == 1


def test_blip_resets_so_real_utterance_still_detected() -> None:
    det = EndpointDetector()
    blip = _make_frames(0, 3, is_speech=True)
    ts = blip[-1].ts_ms + FRAME_MS
    silence_after_blip = _make_frames(ts, (END_SILENCE_MS // FRAME_MS) + 5, is_speech=False)
    ts = silence_after_blip[-1].ts_ms + FRAME_MS
    # Now a real utterance.
    speech = _make_frames(ts, (MIN_SPEECH_MS // FRAME_MS) + 5, is_speech=True)
    ts = speech[-1].ts_ms + FRAME_MS
    silence = _make_frames(ts, (END_SILENCE_MS // FRAME_MS) + 5, is_speech=False)

    events = _feed(det, blip + silence_after_blip + speech + silence)
    assert events.count("endpoint") == 1
    # speech_start once for the blip, once for the real utterance.
    assert events.count("speech_start") == 2


# --- speech_start fires once --------------------------------------------------

def test_speech_start_fires_once_per_utterance() -> None:
    det = EndpointDetector()
    # Continuous speech: speech_start only on the first frame.
    speech = _make_frames(0, 20, is_speech=True)
    events = _feed(det, speech)
    assert events.count("speech_start") == 1
    assert events[0] == "speech_start"
    assert all(e is None for e in events[1:])


def test_speech_start_not_emitted_during_idle_silence() -> None:
    det = EndpointDetector()
    silence = _make_frames(0, 10, is_speech=False)
    events = _feed(det, silence)
    assert all(e is None for e in events)


# --- partial_flush_due boundaries --------------------------------------------

def test_partial_flush_due_time_boundary() -> None:
    assert partial_flush_due(PARTIAL_FLUSH_MS - 1, 0) is False
    assert partial_flush_due(PARTIAL_FLUSH_MS, 0) is True
    assert partial_flush_due(PARTIAL_FLUSH_MS + 1, 0) is True


def test_partial_flush_due_chars_boundary() -> None:
    assert partial_flush_due(0, PARTIAL_FLUSH_CHARS - 1) is False
    assert partial_flush_due(0, PARTIAL_FLUSH_CHARS) is True
    assert partial_flush_due(0, PARTIAL_FLUSH_CHARS + 1) is True


def test_partial_flush_due_neither_boundary() -> None:
    assert partial_flush_due(0, 0) is False


def test_partial_flush_due_either_triggers() -> None:
    # Time over, chars under -> True.
    assert partial_flush_due(PARTIAL_FLUSH_MS, PARTIAL_FLUSH_CHARS - 1) is True
    # Time under, chars over -> True.
    assert partial_flush_due(PARTIAL_FLUSH_MS - 1, PARTIAL_FLUSH_CHARS) is True


def test_partial_flush_due_custom_limits() -> None:
    assert partial_flush_due(50, 5, max_ms=100, max_chars=10) is False
    assert partial_flush_due(100, 5, max_ms=100, max_chars=10) is True
    assert partial_flush_due(50, 10, max_ms=100, max_chars=10) is True
