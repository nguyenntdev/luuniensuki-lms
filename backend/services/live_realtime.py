"""
Real-time conversation orchestrator for the AI teacher (Path B, Wave 1 Task 5).

Composes the pure Wave-0/1 building blocks into one driver that turns a stream of
VAD frames + audio chunks into turn events, an endpointed learner transcript, a
cancellable LLM→TTS response, and barge-in handling — WITHOUT any audio/network
dependency. The audio transport (aiortc/Janus, Wave 2) and the actual DeepSeek
call are injected as callables, so this orchestrator is fully unit-testable with
fakes and can be wired into the worker once the audio bridge exists.

Pieces composed:
    * live_turn.TurnMachine        — idle→listening→thinking→speaking FSM
    * live_vad.EndpointDetector    — speech_start / endpoint detection
    * live_stt_stream.StreamingSTT — interim/final transcript
    * live_tts_chunk.SentenceChunker — sentence-boundary chunks for TTS
    * live_cancel.CancelToken      — cooperative barge-in cancellation

The orchestrator emits structured "actions" (plain dicts) describing what the
transport layer should do (speak a chunk, stop speaking, emit an event). It does
not perform I/O itself, which keeps it deterministic and testable.
"""

from __future__ import annotations

from typing import Any, Callable, Iterable, Iterator, Optional

from backend.services.live_cancel import CancelToken, cancellable
from backend.services.live_stt_stream import StreamingSTT
from backend.services.live_tts_chunk import SentenceChunker
from backend.services.live_turn import TurnEvent, TurnMachine, TurnStateValue, should_barge_in
from backend.services.live_vad import EndpointDetector, VadFrame

# An LLM response is produced as a stream of text deltas for a given prompt.
LlmStreamFn = Callable[[str], Iterable[str]]


class RealtimeOrchestrator:
    """Drives one live AI-teacher conversation turn-by-turn.

    Construct with the composed components and an ``llm_stream`` callable that,
    given the learner's final utterance, yields response text deltas (e.g. the
    DeepSeek streaming generator). The transport layer feeds VAD frames and audio
    chunks in and consumes the yielded action dicts.
    """

    def __init__(
        self,
        *,
        request_id: str,
        stt: StreamingSTT,
        llm_stream: LlmStreamFn,
        endpoint: Optional[EndpointDetector] = None,
        chunker: Optional[SentenceChunker] = None,
        turn: Optional[TurnMachine] = None,
    ) -> None:
        self.request_id = request_id
        self.stt = stt
        self.llm_stream = llm_stream
        self.endpoint = endpoint or EndpointDetector()
        self.chunker = chunker or SentenceChunker()
        self.turn = turn or TurnMachine()
        # Cancellation token for the in-flight AI response (barge-in target).
        self._token: Optional[CancelToken] = None

    # -- helpers --------------------------------------------------------------

    def _action(self, kind: str, **fields: Any) -> dict[str, Any]:
        return {"type": kind, "request_id": self.request_id, **fields}

    @property
    def state(self) -> TurnStateValue:
        return self.turn.state

    # -- learner audio in -----------------------------------------------------

    def on_vad_frame(self, frame: VadFrame) -> list[dict[str, Any]]:
        """Feed one VAD frame. Returns any actions triggered.

        Drives the turn FSM from endpoint-detector events. If the learner starts
        speaking while the AI is talking, a barge-in is emitted and the in-flight
        response token is cancelled.
        """
        actions: list[dict[str, Any]] = []
        event = self.endpoint.push(frame)

        if event == "speech_start":
            if should_barge_in(self.turn.state, learner_speaking=True):
                # Interrupt the AI: cancel the in-flight response and stop audio.
                if self._token is not None:
                    self._token.cancel()
                self.turn.try_apply(TurnEvent.on_barge_in)
                actions.append(self._action("stop_speaking"))
                actions.append(self._action("barge_in"))
            else:
                self.turn.try_apply(TurnEvent.on_speech_start)
                actions.append(self._action("turn_state", state=self.turn.state.value))
        elif event == "endpoint":
            if self.turn.try_apply(TurnEvent.on_endpoint):
                actions.append(self._action("turn_state", state=self.turn.state.value))
                # The learner's turn is over; the transport should now call
                # `respond()` with the final transcript.
                actions.append(self._action("endpoint"))
        return actions

    def on_audio_chunk(self, chunk: bytes) -> None:
        """Forward a learner audio chunk to the streaming STT buffer."""
        self.stt.feed(chunk)

    # -- AI response out ------------------------------------------------------

    def respond(self, token: CancelToken) -> Iterator[dict[str, Any]]:
        """Produce the AI response for the just-ended learner turn.

        Commits the STT buffer to a final transcript, streams the LLM response,
        and yields ``speak`` actions per sentence chunk. Honors ``token`` for
        barge-in: if cancelled mid-stream, stops emitting and yields a
        ``cancelled`` action. Drives the FSM thinking→speaking→idle.
        """
        self._token = token
        final_text = self.stt.final()
        yield self._action("user_final", text=final_text)

        # thinking: waiting for the first token.
        produced_any = False
        stream = self.llm_stream(final_text)
        for delta in cancellable(stream, token):
            if not produced_any:
                # First token → speaking.
                self.turn.try_apply(TurnEvent.on_llm_first_token)
                produced_any = True
            for chunk in self.chunker.feed(delta):
                if token.cancelled:
                    break
                yield self._action("speak", text=chunk)
            if token.cancelled:
                break

        if token.cancelled:
            yield self._action("cancelled")
            return

        tail = self.chunker.flush()
        if tail:
            yield self._action("speak", text=tail)

        # Done speaking → idle.
        self.turn.try_apply(TurnEvent.on_tts_done)
        yield self._action("turn_done")
