"""
VAD endpointing policy for the real-time conversational AI teacher (Path B).

# Wave 0 Task 2 — pure, I/O-free voice-activity-detection (VAD) endpointing.

This module owns *only* the decision logic that turns a stream of voice-activity
frames into turn-taking events. It does no audio decoding, no network calls, and
touches no database — exactly like the sibling pure module ``live_turn.py``. The
realtime audio bridge (Wave 2) is responsible for producing the frames (one per
fixed-size audio chunk, typically ~20ms) from a real VAD and for acting on the
events this policy returns.

What it decides:
    * when a learner *starts* talking after a period of idle/silence
      (``"speech_start"``), so the turn machine can move ``idle -> listening``;
    * when a learner has *finished* their turn (``"endpoint"``), detected as a
      run of trailing continuous silence of at least ``END_SILENCE_MS`` that
      follows at least ``MIN_SPEECH_MS`` of accumulated speech in the current
      utterance, so the turn machine can move ``listening -> thinking``.

Guards baked into the policy:
    * a minimum-speech guard (``MIN_SPEECH_MS``) so short blips — coughs, a
      single "uh", keyboard noise classified as speech — never produce an
      ``"endpoint"``; such blips reset the detector quietly back to idle;
    * exactly-once semantics: ``"speech_start"`` fires once per utterance and
      ``"endpoint"`` fires once per trailing-silence window, after which the
      detector resets to idle so the next utterance is detected independently.

Frame duration is derived from consecutive ``ts_ms`` deltas (the gap between a
frame and the previous one). For the very first frame seen — when only one frame
exists so far and there is no delta — a default of ``20ms`` is assumed.

Also exposed: :func:`partial_flush_due`, a pure helper that decides when a long
monologue should be committed incrementally to STT (so very long turns still get
partial transcripts) based on elapsed time or accumulated character count.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


# --- Tunable policy constants (milliseconds / characters) --------------------

# Trailing continuous silence required to declare end-of-turn.
END_SILENCE_MS = 700
# Minimum accumulated speech in an utterance before an endpoint can fire; guards
# against blips (coughs, single syllables, transient noise).
MIN_SPEECH_MS = 300
# Force a partial STT commit after this much wall-clock time in one turn.
PARTIAL_FLUSH_MS = 4000
# ...or after this many accumulated characters, whichever comes first.
PARTIAL_FLUSH_CHARS = 160

# Assumed frame duration when only a single frame has been seen (no delta yet).
_DEFAULT_FRAME_MS = 20


@dataclass(frozen=True)
class VadFrame:
    """A single voice-activity frame from the upstream VAD.

    Attributes:
        ts_ms:     monotonically increasing timestamp (milliseconds) of this
                   frame; deltas between consecutive frames give frame duration.
        is_speech: whether the VAD classified this frame as speech.
        energy:    raw frame energy/level (informational; not used by the
                   endpoint rule, but carried for telemetry/tuning).
    """

    ts_ms: int
    is_speech: bool
    energy: float


class EndpointDetector:
    """Consumes :class:`VadFrame` objects in order and emits turn events.

    Call :meth:`push` once per frame, in timestamp order. It returns:
        * ``None``            — no event for this frame;
        * ``"speech_start"``  — first speech frame after idle (once per utterance);
        * ``"endpoint"``      — end-of-turn detected (once per trailing-silence
                                window); the detector resets to idle afterwards.

    The detector is a small finite state with two phases: ``idle`` (waiting for
    speech) and "in utterance" (accumulating speech, watching trailing silence).
    """

    def __init__(
        self,
        *,
        end_silence_ms: int = END_SILENCE_MS,
        min_speech_ms: int = MIN_SPEECH_MS,
    ) -> None:
        self.end_silence_ms = end_silence_ms
        self.min_speech_ms = min_speech_ms

        # Whether we are waiting for speech to begin.
        self._idle: bool = True
        # Accumulated speech duration in the current utterance (ms).
        self._speech_ms: int = 0
        # Trailing *continuous* silence since the last speech frame (ms).
        self._silence_ms: int = 0
        # Timestamp of the previous frame, for delta-based duration. None until
        # the first frame is seen.
        self._last_ts: Optional[int] = None

    # -- internal helpers -----------------------------------------------------

    def _frame_duration(self, ts_ms: int) -> int:
        """Duration attributed to the current frame, from the ts delta."""
        if self._last_ts is None:
            return _DEFAULT_FRAME_MS
        delta = ts_ms - self._last_ts
        # Frames arrive in order; clamp any non-positive delta to 0 defensively.
        return delta if delta > 0 else 0

    def _reset_to_idle(self) -> None:
        """Return to the idle phase; preserves ``_last_ts`` for future deltas."""
        self._idle = True
        self._speech_ms = 0
        self._silence_ms = 0

    # -- public API -----------------------------------------------------------

    def push(self, frame: VadFrame) -> Optional[str]:
        """Feed one frame; return the event it triggers (or ``None``)."""
        duration = self._frame_duration(frame.ts_ms)
        self._last_ts = frame.ts_ms

        if frame.is_speech:
            event: Optional[str] = None
            if self._idle:
                # Speech begins after idle: start a fresh utterance and announce
                # it exactly once.
                self._idle = False
                self._speech_ms = 0
                self._silence_ms = 0
                event = "speech_start"
            self._speech_ms += duration
            # Any speech breaks a run of trailing silence.
            self._silence_ms = 0
            return event

        # Silence frame.
        if self._idle:
            # Silence while idle is the steady state; nothing to do.
            return None

        self._silence_ms += duration
        if self._silence_ms >= self.end_silence_ms:
            if self._speech_ms >= self.min_speech_ms:
                # Genuine end-of-turn: enough speech, then enough trailing
                # silence. Emit once, then reset for the next utterance.
                self._reset_to_idle()
                return "endpoint"
            # The utterance was only a blip (< MIN_SPEECH_MS). Discard it
            # quietly without signalling an endpoint.
            self._reset_to_idle()
        return None

    def reset(self) -> None:
        """Fully reset the detector to its initial idle state."""
        self._idle = True
        self._speech_ms = 0
        self._silence_ms = 0
        self._last_ts = None


def partial_flush_due(
    elapsed_ms: int,
    chars: int,
    *,
    max_ms: int = PARTIAL_FLUSH_MS,
    max_chars: int = PARTIAL_FLUSH_CHARS,
) -> bool:
    """Whether a long turn should be flushed to STT for a partial commit.

    Returns ``True`` once the turn has run for at least ``max_ms`` milliseconds
    or has accumulated at least ``max_chars`` characters, whichever comes first.
    Pure boundary check — no state, no I/O.
    """
    return elapsed_ms >= max_ms or chars >= max_chars
