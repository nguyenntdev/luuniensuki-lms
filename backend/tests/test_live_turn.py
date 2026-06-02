"""Tests for the turn-taking state machine (Task 1.3).

Covers the pure, I/O-free turn state graph in ``backend/services/live_turn.py``:
every legal transition lands on its documented next state, illegal transitions
are rejected, the barge-in rule fires only while speaking, ``TurnMachine``
behaves correctly, and a property-style fuzz never escapes the legal graph.

Validates: Requirements (Task 1.3 — state only advances through legal
transitions; barge-in only fires while speaking).
"""

from __future__ import annotations

import random
import sys
from pathlib import Path

import pytest

# Mirror the repo's existing test bootstrap: make the repo root importable so
# ``backend.services`` resolves regardless of the pytest invocation cwd.
REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from backend.services.live_turn import (  # noqa: E402
    IllegalTransition,
    TurnEvent,
    TurnMachine,
    TurnStateValue,
    can_apply,
    next_state,
    should_barge_in,
)


# The documented legal graph: (state, event) -> next state.
LEGAL_TRANSITIONS: dict[
    tuple[TurnStateValue, TurnEvent], TurnStateValue
] = {
    (TurnStateValue.idle, TurnEvent.on_speech_start): TurnStateValue.listening,
    (TurnStateValue.listening, TurnEvent.on_endpoint): TurnStateValue.thinking,
    (TurnStateValue.listening, TurnEvent.on_silence_reset): TurnStateValue.idle,
    (TurnStateValue.thinking, TurnEvent.on_llm_first_token): TurnStateValue.speaking,
    (TurnStateValue.speaking, TurnEvent.on_tts_done): TurnStateValue.idle,
    (TurnStateValue.speaking, TurnEvent.on_barge_in): TurnStateValue.listening,
}

ALL_STATES = list(TurnStateValue)
ALL_EVENTS = list(TurnEvent)

# Every (state, event) pair that is NOT in the legal graph.
ILLEGAL_PAIRS = [
    (state, event)
    for state in ALL_STATES
    for event in ALL_EVENTS
    if (state, event) not in LEGAL_TRANSITIONS
]


# --------------------------------------------------------------------------- #
# Legal transitions
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize(
    ("state", "event", "expected"),
    [(s, e, nxt) for (s, e), nxt in LEGAL_TRANSITIONS.items()],
)
def test_legal_transition_produces_documented_next_state(
    state: TurnStateValue, event: TurnEvent, expected: TurnStateValue
) -> None:
    assert next_state(state, event) == expected
    assert can_apply(state, event) is True


def test_happy_path_cycle() -> None:
    # idle -> listening -> thinking -> speaking -> idle
    s = TurnStateValue.idle
    s = next_state(s, TurnEvent.on_speech_start)
    assert s == TurnStateValue.listening
    s = next_state(s, TurnEvent.on_endpoint)
    assert s == TurnStateValue.thinking
    s = next_state(s, TurnEvent.on_llm_first_token)
    assert s == TurnStateValue.speaking
    s = next_state(s, TurnEvent.on_tts_done)
    assert s == TurnStateValue.idle


def test_barge_in_transition_returns_to_listening() -> None:
    assert (
        next_state(TurnStateValue.speaking, TurnEvent.on_barge_in)
        == TurnStateValue.listening
    )


def test_silence_reset_transition_returns_to_idle() -> None:
    assert (
        next_state(TurnStateValue.listening, TurnEvent.on_silence_reset)
        == TurnStateValue.idle
    )


# --------------------------------------------------------------------------- #
# Illegal transitions
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize(("state", "event"), ILLEGAL_PAIRS)
def test_illegal_transition_raises(state: TurnStateValue, event: TurnEvent) -> None:
    assert can_apply(state, event) is False
    with pytest.raises(IllegalTransition):
        next_state(state, event)


def test_illegal_pairs_are_nonempty() -> None:
    # Sanity guard: there should be illegal pairs to exercise (12 states*events
    # combos minus 6 legal ones = 18).
    assert len(ILLEGAL_PAIRS) == len(ALL_STATES) * len(ALL_EVENTS) - len(
        LEGAL_TRANSITIONS
    )
    assert len(ILLEGAL_PAIRS) > 0


# --------------------------------------------------------------------------- #
# should_barge_in: true ONLY when speaking AND learner_speaking
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize("state", ALL_STATES)
@pytest.mark.parametrize("learner_speaking", [True, False])
def test_should_barge_in_only_while_speaking_and_learner_speaking(
    state: TurnStateValue, learner_speaking: bool
) -> None:
    expected = state == TurnStateValue.speaking and learner_speaking
    assert should_barge_in(state, learner_speaking) is expected


def test_should_barge_in_true_case() -> None:
    assert should_barge_in(TurnStateValue.speaking, True) is True


# --------------------------------------------------------------------------- #
# TurnMachine
# --------------------------------------------------------------------------- #


def test_machine_defaults_to_idle() -> None:
    m = TurnMachine()
    assert m.state == TurnStateValue.idle
    assert m.history == []
    assert m.is_speaking() is False


def test_machine_apply_advances_and_records_history() -> None:
    m = TurnMachine()
    result = m.apply(TurnEvent.on_speech_start)
    assert result == TurnStateValue.listening
    assert m.state == TurnStateValue.listening
    assert m.history == [
        (TurnStateValue.idle, TurnEvent.on_speech_start, TurnStateValue.listening)
    ]


def test_machine_apply_illegal_raises_and_keeps_state() -> None:
    m = TurnMachine()
    with pytest.raises(IllegalTransition):
        m.apply(TurnEvent.on_tts_done)
    assert m.state == TurnStateValue.idle
    assert m.history == []


def test_machine_try_apply_legal_returns_true_and_advances() -> None:
    m = TurnMachine()
    assert m.try_apply(TurnEvent.on_speech_start) is True
    assert m.state == TurnStateValue.listening
    assert m.history == [
        (TurnStateValue.idle, TurnEvent.on_speech_start, TurnStateValue.listening)
    ]


def test_machine_try_apply_illegal_returns_false_and_no_change() -> None:
    m = TurnMachine()
    assert m.try_apply(TurnEvent.on_endpoint) is False
    assert m.state == TurnStateValue.idle
    assert m.history == []


def test_machine_is_speaking_true_after_reaching_speaking() -> None:
    m = TurnMachine()
    m.apply(TurnEvent.on_speech_start)
    m.apply(TurnEvent.on_endpoint)
    m.apply(TurnEvent.on_llm_first_token)
    assert m.is_speaking() is True


def test_machine_reset_returns_to_idle() -> None:
    m = TurnMachine()
    m.apply(TurnEvent.on_speech_start)
    assert m.state == TurnStateValue.listening
    m.reset()
    assert m.state == TurnStateValue.idle


def test_machine_full_cycle_history() -> None:
    m = TurnMachine()
    for event in (
        TurnEvent.on_speech_start,
        TurnEvent.on_endpoint,
        TurnEvent.on_llm_first_token,
        TurnEvent.on_tts_done,
    ):
        m.apply(event)
    assert m.state == TurnStateValue.idle
    # History pairs the prev/next correctly for every step.
    for prev, event, nxt in m.history:
        assert LEGAL_TRANSITIONS[(prev, event)] == nxt


# --------------------------------------------------------------------------- #
# Property-style fuzz: random event sequences via try_apply never escape the
# legal graph and never raise.
# --------------------------------------------------------------------------- #


def test_property_random_sequences_stay_in_legal_graph() -> None:
    rng = random.Random(1234)  # deterministic for reproducibility
    for _ in range(2000):
        # Start from an arbitrary reachable state.
        start = rng.choice(ALL_STATES)
        m = TurnMachine(state=start)
        seq_len = rng.randint(0, 30)
        for _ in range(seq_len):
            event = rng.choice(ALL_EVENTS)
            prev = m.state
            applied = m.try_apply(event)  # must never raise

            # State is always a valid member of the enum.
            assert m.state in ALL_STATES

            if applied:
                # A legal step must match the documented transition table.
                assert (prev, event) in LEGAL_TRANSITIONS
                assert m.state == LEGAL_TRANSITIONS[(prev, event)]
            else:
                # An illegal step leaves the state untouched.
                assert m.state == prev
                assert (prev, event) not in LEGAL_TRANSITIONS

        # Every recorded history entry is a documented legal transition.
        for prev, event, nxt in m.history:
            assert LEGAL_TRANSITIONS[(prev, event)] == nxt
