"""
Sentence chunker for streaming TTS in the real-time AI teacher (Path B).

Pure, I/O-free logic so it is fully unit-testable without a TTS backend, audio,
or network. The realtime loop (Wave 2) feeds DeepSeek token deltas into a
:class:`SentenceChunker` and forwards each emitted chunk to streaming TTS, so
speech synthesis can start on the first finished sentence instead of waiting for
the whole answer to be generated — lower time-to-first-audio.

Boundary rule:
    A chunk is emitted when the accumulated buffer reaches a sentence boundary
    (one of ``.  ?  !  :``  or a newline) and the trimmed content is at least
    ``min_chars`` long. Short fragments are merged until that threshold is met.
    If no boundary appears and the buffer grows past ``max_chars``, the buffer is
    hard-split at the last whitespace before ``max_chars`` (else at ``max_chars``)
    so a runaway monologue still streams out.

Invariants (guaranteed by construction):
    * ``"".join(<every emitted chunk>) + flush() == "".join(<every fed delta>)``
      — no text is ever lost, reordered, or duplicated.
    * A chunk is never empty or whitespace-only. (``flush()`` MAY be empty or
      whitespace; it returns the raw remainder, it is not an emitted chunk.)
"""

from __future__ import annotations

#: Characters that terminate a sentence for TTS-chunking purposes. A newline is
#: included because LLMs use it to separate list items / paragraphs.
SENTENCE_BOUNDARIES: frozenset[str] = frozenset({".", "?", "!", ":", "\n"})


class SentenceChunker:
    """Accumulate streaming token deltas and emit TTS-ready sentence chunks.

    Stateful but pure: every byte fed in is either returned by :meth:`feed` as
    part of a chunk or held in the buffer until a later :meth:`feed`/:meth:`flush`.
    """

    def __init__(self, *, min_chars: int = 20, max_chars: int = 240) -> None:
        if min_chars < 0:
            raise ValueError("min_chars must be >= 0")
        if max_chars < 1:
            raise ValueError("max_chars must be >= 1")
        self.min_chars = min_chars
        self.max_chars = max_chars
        self._buf: str = ""

    def feed(self, delta: str) -> list[str]:
        """Append ``delta`` to the buffer and return the chunks completed now.

        A single ``feed`` may complete zero, one, or several chunks (e.g. a delta
        that contains multiple sentence boundaries). Anything not yet ready to
        emit stays buffered for the next call.
        """
        if delta:
            self._buf += delta
        emitted: list[str] = []
        while True:
            chunk = self._take_chunk()
            if chunk is None:
                break
            emitted.append(chunk)
        return emitted

    def flush(self) -> str:
        """Return and clear the buffered remainder (may be ``""``).

        Call this once the LLM stream ends to drain the trailing partial
        sentence. The returned text completes the concatenation invariant.
        """
        remainder, self._buf = self._buf, ""
        return remainder

    def pending(self) -> str:
        """Return the current (un-emitted) buffer contents. For tests/telemetry."""
        return self._buf

    # -- internals ---------------------------------------------------------

    def _take_chunk(self) -> str | None:
        """Pop the next ready chunk off the buffer, or ``None`` if not ready."""
        cut = self._sentence_cut()
        if cut is None and len(self._buf) >= self.max_chars:
            cut = self._hard_cut()
        if cut is None:
            return None
        chunk = self._buf[:cut]
        if not chunk.strip():
            # Defensive: the cut logic already avoids whitespace-only chunks, so
            # bail rather than ever emit one (and never advance into a loop).
            return None
        self._buf = self._buf[cut:]
        return chunk

    def _sentence_cut(self) -> int | None:
        """Index just past the earliest sentence boundary that satisfies
        ``min_chars`` (counting trimmed content from the buffer start), or
        ``None``. Boundaries whose chunk would be blank are skipped so short
        leading fragments merge into the following sentence.
        """
        buf = self._buf
        for i, ch in enumerate(buf):
            if ch in SENTENCE_BOUNDARIES:
                cut = i + 1
                trimmed = len(buf[:cut].strip())
                if trimmed >= self.min_chars and trimmed >= 1:
                    return cut
        return None

    def _hard_cut(self) -> int | None:
        """Index for a forced split when the buffer overruns ``max_chars`` with
        no usable sentence boundary. Prefers the last whitespace before the
        limit so words stay intact; falls back to a mid-word split at the limit.
        Returns ``None`` only when the whole window is whitespace.
        """
        limit = self.max_chars
        window = self._buf[:limit]
        for i in range(len(window) - 1, -1, -1):
            if window[i].isspace() and window[: i + 1].strip():
                return i + 1
        if window.strip():
            return limit
        return None
