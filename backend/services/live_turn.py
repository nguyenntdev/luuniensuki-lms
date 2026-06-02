"""
Turn-taking state machine for the real-time conversational AI teacher (Path B).

Pure, I/O-free logic so it is fully unit-testable without audio, network, or a
DB. The realtime audio bridge (Wave 2) drives this machine from VAD/STT/LLM/TTS
events; this module only owns the legal state graph and the barge-in rule.

States:
    idle      — no active turn
    listening — learner is speaking; we are capturing/transcribing
    thinking  — learner finished; waiting for the first LLM token
    speaking  — AI is producing/streaming TTS audio

Legal transitions:
    idle      --on_speech_start-->   listening
    listening --on_endpoint-->       thinking
    thinking  --on_llm_first_token-> speaking
    speaking  --on_tts_done-->       idle
    speaking  --on_barge_in-->       listening   (learner interrupts the AI)
    listening --on_silence_reset-->  idle        (false-start blip, no real speech)

Any other (state, event) pair is illegal and raises ``IllegalTransition``.
"""

from __future__ import annotations

from enum import Enum


class TurnStateValue(str, Enum):
    idle = "idle"
    listening = "listening"
    thinking = "thinking"
    speaking = "speaking"


class TurnEvent(str, Enum):
    on_speech_start = "on_speech_start"
    on_endpoint = "on_endpoint"
    on_llm_first_token = "on_llm_first_token"
    on_tts_done = "on_tts_done"
    on_barge_in = "on_barge_in"
    on_silence_reset = "on_silence_reset"


class IllegalTransition(Exception):
    """Raised when an event is not valid for the current state."""


# (state, event) -> next state. Anything absent is illegal.
_TRANSITIONS: dict[tuple[TurnStateValue, TurnEvent], TurnStateValue] = {
    (TurnStateValue.idle, TurnEvent.on_speech_start): TurnStateValue.listening,
    (TurnStateValue.listening, TurnEvent.on_endpoint): TurnStateValue.thinking,
    (TurnStateValue.listening, TurnEvent.on_silence_reset): TurnStateValue.idle,
    (TurnStateValue.thinking, TurnEvent.on_llm_first_token): TurnStateValue.speaking,
    (TurnStateValue.speaking, TurnEvent.on_tts_done): TurnStateValue.idle,
    (TurnStateValue.speaking, TurnEvent.on_barge_in): TurnStateValue.listening,
}


def next_state(state: TurnStateValue, event: TurnEvent) -> TurnStateValue:
    """Return the state after applying ``event`` to ``state``.

    Raises :class:`IllegalTransition` if the transition is not allowed.
    """
    try:
        return _TRANSITIONS[(state, event)]
    except KeyError as exc:
        raise IllegalTransition(
            f"illegal transition: {state.value} --{event.value}-->"
        ) from exc


def can_apply(state: TurnStateValue, event: TurnEvent) -> bool:
    """Whether ``event`` is legal in ``state`` (no exception)."""
    return (state, event) in _TRANSITIONS


def should_barge_in(state: TurnStateValue, learner_speaking: bool) -> bool:
    """Barge-in fires only while the AI is ``speaking`` and the learner starts
    speaking. In every other state, learner speech is normal turn-taking, not an
    interruption.
    """
    return state == TurnStateValue.speaking and learner_speaking


class TurnMachine:
    """Tiny stateful wrapper around :func:`next_state`.

    Holds the current state and applies events, recording a short history for
    debugging/telemetry. Still pure (no external I/O).
    """

    def __init__(self, state: TurnStateValue = TurnStateValue.idle) -> None:
        self.state = state
        self.history: list[tuple[TurnStateValue, TurnEvent, TurnStateValue]] = []

    def apply(self, event: TurnEvent) -> TurnStateValue:
        prev = self.state
        self.state = next_state(self.state, event)
        self.history.append((prev, event, self.state))
        return self.state

    def try_apply(self, event: TurnEvent) -> bool:
        """Apply ``event`` if legal; return whether it was applied. Never raises."""
        if not can_apply(self.state, event):
            return False
        self.apply(event)
        return True

    def is_speaking(self) -> bool:
        return self.state == TurnStateValue.speaking

    def reset(self) -> None:
        self.state = TurnStateValue.idle
