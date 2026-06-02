"""Tests for the streaming-TTS sentence chunker (``services/live_tts_chunk``).

Pure logic, no I/O — covers the concatenation invariant, sentence-boundary
splitting, the never-empty-chunk guarantee, hard splitting past ``max_chars``,
and ``flush()`` draining the remainder. A Hypothesis property test feeds a long
text in random-sized deltas and asserts the stream reassembles exactly.
"""

from __future__ import annotations

import sys
from pathlib import Path

from hypothesis import given
from hypothesis import settings
from hypothesis import strategies as st

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from backend.services.live_tts_chunk import SentenceChunker


def _feed_all(chunker: SentenceChunker, deltas: list[str]) -> list[str]:
    """Feed every delta in order, returning all emitted chunks (flat)."""
    out: list[str] = []
    for d in deltas:
        out.extend(chunker.feed(d))
    return out


# --- concatenation invariant -------------------------------------------------


def test_concatenation_invariant_over_several_feeds() -> None:
    deltas = [
        "Hello there, ",
        "this is the AI teacher. ",
        "Can you ",
        "hear me? ",
        "Great:\n",
        "let us begin",
    ]
    chunker = SentenceChunker(min_chars=10, max_chars=120)
    emitted = _feed_all(chunker, deltas)
    remainder = chunker.flush()

    assert "".join(emitted) + remainder == "".join(deltas)
    # flush drains everything
    assert chunker.pending() == ""


def test_empty_deltas_do_not_break_invariant() -> None:
    chunker = SentenceChunker(min_chars=5, max_chars=80)
    emitted = _feed_all(chunker, ["", "A short one. ", "", "And more!", ""])
    remainder = chunker.flush()
    assert "".join(emitted) + remainder == "A short one. And more!"


# --- sentence-boundary splitting --------------------------------------------


def test_splits_on_sentence_end() -> None:
    chunker = SentenceChunker(min_chars=5, max_chars=200)
    # Every sentence ends in a boundary char, so all three emit in one feed.
    emitted = chunker.feed("First sentence. Second sentence! Third?")
    assert emitted == ["First sentence.", " Second sentence!", " Third?"]
    assert chunker.pending() == ""


def test_trailing_partial_without_boundary_stays_pending() -> None:
    chunker = SentenceChunker(min_chars=5, max_chars=200)
    emitted = chunker.feed("First sentence. Second one is unfinished")
    assert emitted == ["First sentence."]
    assert chunker.pending() == " Second one is unfinished"


def test_splits_on_colon_and_newline() -> None:
    chunker = SentenceChunker(min_chars=3, max_chars=200)
    assert chunker.feed("Note this:") == ["Note this:"]
    assert chunker.feed(" line one\n") == [" line one\n"]


def test_short_fragment_merges_until_min_chars() -> None:
    # "Hi. " trimmed is 3 chars, below min_chars=10, so it must merge forward.
    chunker = SentenceChunker(min_chars=10, max_chars=200)
    assert chunker.feed("Hi. ") == []
    emitted = chunker.feed("How are you today?")
    assert emitted == ["Hi. How are you today?"]


# --- never emit an empty/whitespace-only chunk ------------------------------


def test_never_emits_empty_chunk() -> None:
    chunker = SentenceChunker(min_chars=1, max_chars=20)
    # Pure boundary/whitespace noise must never produce a blank chunk.
    for delta in ["\n", "  ", "...\n", "   \n  ", "!"]:
        for chunk in chunker.feed(delta):
            assert chunk.strip() != ""
    # Whatever is left is only ever returned via flush(), not as a chunk.
    chunker.flush()


def test_leading_whitespace_never_yields_blank_chunk() -> None:
    chunker = SentenceChunker(min_chars=1, max_chars=200)
    emitted = chunker.feed("   \n  Real content here.")
    for chunk in emitted:
        assert chunk.strip() != ""
    assert "".join(emitted) + chunker.flush() == "   \n  Real content here."


# --- hard split past max_chars ----------------------------------------------


def test_hard_split_when_exceeding_max_chars() -> None:
    chunker = SentenceChunker(min_chars=5, max_chars=20)
    # No sentence boundary anywhere, just words separated by spaces.
    text = "alpha beta gamma delta epsilon zeta eta theta"
    emitted = _feed_all(chunker, [text])
    remainder = chunker.flush()

    assert emitted, "expected at least one hard-split chunk"
    # Each hard-split chunk respects the max_chars ceiling...
    for chunk in emitted:
        assert len(chunk) <= 20
        assert chunk.strip() != ""
    # ...and nothing is lost.
    assert "".join(emitted) + remainder == text


def test_hard_split_breaks_on_whitespace_when_possible() -> None:
    chunker = SentenceChunker(min_chars=1, max_chars=10)
    # "abcd efgh ij" -> last whitespace before index 10 is at index 9.
    emitted = chunker.feed("abcd efgh ij")
    assert emitted[0] == "abcd efgh "
    assert "".join(emitted) + chunker.flush() == "abcd efgh ij"


def test_hard_split_mid_word_when_no_whitespace() -> None:
    chunker = SentenceChunker(min_chars=1, max_chars=8)
    emitted = chunker.feed("abcdefghijklmnop")
    assert emitted[0] == "abcdefgh"
    assert len(emitted[0]) == 8
    assert "".join(emitted) + chunker.flush() == "abcdefghijklmnop"


# --- flush -------------------------------------------------------------------


def test_flush_returns_remainder_and_clears() -> None:
    chunker = SentenceChunker(min_chars=50, max_chars=500)
    chunker.feed("A trailing partial with no boundary")
    remainder = chunker.flush()
    assert remainder == "A trailing partial with no boundary"
    assert chunker.flush() == ""
    assert chunker.pending() == ""


def test_flush_on_empty_returns_empty_string() -> None:
    chunker = SentenceChunker()
    assert chunker.flush() == ""


# --- property: random delta segmentation reassembles exactly ----------------


@settings(max_examples=300)
@given(
    text=st.text(min_size=0, max_size=600),
    cuts=st.lists(st.integers(min_value=0, max_value=600), max_size=80),
)
def test_property_random_deltas_reassemble(text: str, cuts: list[int]) -> None:
    """Splitting any text into arbitrary deltas and streaming it through the
    chunker reassembles the original exactly (chunks + flush == input), and no
    emitted chunk is ever whitespace-only.

    Validates: realtime-tasks 3.1, 3.2 (concatenation + no-empty invariants).
    """
    # Build delta boundaries from the random cut points.
    bounds = sorted({0, len(text)} | {c for c in cuts if 0 <= c <= len(text)})
    deltas = [text[a:b] for a, b in zip(bounds, bounds[1:])]

    chunker = SentenceChunker(min_chars=15, max_chars=64)
    emitted = _feed_all(chunker, deltas)
    remainder = chunker.flush()

    assert "".join(emitted) + remainder == text
    for chunk in emitted:
        assert chunk.strip() != ""
        assert len(chunk) <= 64 or any(b in chunk for b in ".?!:\n")
