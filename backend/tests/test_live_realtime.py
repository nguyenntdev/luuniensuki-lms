"""Tests for the realtime conversation orchestrator (Path B, Wave 1 Task 5)."""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from backend.services.live_cancel import CancelToken
from backend.services.live_realtime import RealtimeOrchestrator
from backend.services.live_stt_stream import MockStreamingSTT
from backend.services.live_turn import TurnStateValue
from backend.services.live_vad import EndpointDetector, VadFrame


def _frames(pattern, *, step_ms=20, start=0):
    """Build VadFrames from a bool list (True=speech)."""
    out = []
    ts = start
    for is_speech in pattern:
        out.append(VadFrame(ts_ms=ts, is_speech=is_speech, energy=1.0 if is_speech else 0.0))
        ts += step_ms
    return out


def _make(llm_deltas, *, request_id="r1"):
    def llm_stream(_final_text):
        yield from llm_deltas

    return RealtimeOrchestrator(
        request_id=request_id,
        stt=MockStreamingSTT(),
        llm_stream=llm_stream,
        endpoint=EndpointDetector(end_silence_ms=100, min_speech_ms=40),
        turn=None,
    )


def test_speech_start_moves_to_listening():
    orch = _make(["hello."])
    actions = []
    # ~60ms speech then silence to endpoint (>=100ms silence).
    for f in _frames([True, True, True]):
        actions += orch.on_vad_frame(f)
    assert orch.state == TurnStateValue.listening
    assert any(a["type"] == "turn_state" for a in actions)


def test_full_turn_endpoint_then_response_chunks():
    orch = _make(["Xin chao. ", "Day la cau tra loi."])
    # speech (60ms) then silence (>=100ms => 5 silence frames @20ms).
    for f in _frames([True, True, True] + [False] * 6):
        orch.on_vad_frame(f)
    orch.on_audio_chunk(b"hoi cua hoc sinh")
    assert orch.state == TurnStateValue.thinking

    token = CancelToken("r1")
    actions = list(orch.respond(token))
    kinds = [a["type"] for a in actions]
    assert "user_final" in kinds
    assert "speak" in kinds
    assert kinds[-1] == "turn_done"
    # All spoken text concatenated equals the LLM output.
    spoken = "".join(a["text"] for a in actions if a["type"] == "speak")
    assert spoken == "Xin chao. Day la cau tra loi."
    assert orch.state == TurnStateValue.idle


def test_barge_in_cancels_response():
    orch = _make(["a" * 50 + ". ", "b" * 50 + ". ", "c" * 50 + "."])
    # End a first turn to reach speaking.
    for f in _frames([True, True, True] + [False] * 6):
        orch.on_vad_frame(f)
    token = CancelToken("r1")
    gen = orch.respond(token)
    # Pull the first couple of actions (user_final, first speak) → now speaking.
    first = next(gen)
    assert first["type"] == "user_final"
    second = next(gen)
    assert second["type"] == "speak"
    assert orch.state == TurnStateValue.speaking

    # Learner barges in: a new speech_start frame while speaking.
    barge_actions = orch.on_vad_frame(VadFrame(ts_ms=10_000, is_speech=True, energy=1.0))
    kinds = [a["type"] for a in barge_actions]
    assert "stop_speaking" in kinds
    assert "barge_in" in kinds
    assert token.cancelled is True
    assert orch.state == TurnStateValue.listening

    # Draining the generator yields a cancelled action and stops.
    rest = list(gen)
    assert any(a["type"] == "cancelled" for a in rest)


def test_no_barge_in_when_not_speaking():
    orch = _make(["hi."])
    # speech_start while idle is normal listening, not a barge-in.
    actions = orch.on_vad_frame(VadFrame(ts_ms=0, is_speech=True, energy=1.0))
    kinds = [a["type"] for a in actions]
    assert "barge_in" not in kinds
    assert orch.state == TurnStateValue.listening
