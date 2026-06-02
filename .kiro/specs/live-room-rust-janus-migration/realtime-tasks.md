# Implementation Plan: Real-Time Conversational AI Teacher — Path B (self-assembled)

Keep **DeepSeek** as the brain. Assemble a low-latency speech-to-speech loop from
parts we control: streaming STT + VAD/endpointing → DeepSeek stream → sentence-
chunked streaming TTS → audio published into the Janus room, with barge-in
cancellation. The legacy polled turn-based path stays as a tested fallback.

Pipeline:
```
learner mic → WebRTC → Janus → AI worker (subscribe) → streaming STT + VAD
   → endpoint → DeepSeek stream → sentence chunker → streaming TTS
   → publish ai-teacher audio track → Janus → everyone hears; cancel on barge-in
```

Test sub-tasks are optional (`*`). Pure-logic tasks come first so they land and
get tested without the heavy WebRTC/audio dependencies; the audio-bridge tasks
that need `aiortc` are gated behind a host-footprint check.

## Tasks

### Wave 0 — Pure realtime logic (no new heavy deps; fully unit-testable)

- [x] 1. Turn-taking state machine (`services/live_turn.py`)
  - [x] 1.1 Implement a pure `TurnState` machine: `idle → listening → thinking → speaking`, with transitions `on_speech_start`, `on_endpoint`, `on_llm_first_token`, `on_tts_done`, `on_barge_in`. No I/O — just state + allowed-transition validation.
  - [x] 1.2 Implement `should_barge_in(state, learner_speaking: bool) -> bool` (true only while AI is `speaking` and the learner starts speaking).
  - [x]* 1.3 Property tests: state only advances through legal transitions; barge-in only fires while speaking.

- [x] 2. VAD endpointing policy (`services/live_vad.py`)
  - [x] 2.1 Implement a pure endpoint detector over a stream of (timestamp, is_speech, energy) frames: end-of-turn when trailing silence ≥ `END_SILENCE_MS` (default 700ms) after detected speech, with a min-utterance guard (`MIN_SPEECH_MS`, 300ms) to ignore blips.
  - [x] 2.2 Implement `partial_flush_due(elapsed_ms, chars)` so long monologues get incremental STT commits.
  - [x]* 2.3 Property tests: no endpoint before MIN_SPEECH; endpoint exactly once per trailing-silence window; blips never endpoint.

- [x] 3. Sentence chunker for streaming TTS (`services/live_tts_chunk.py`)
  - [x] 3.1 Implement `feed(delta) -> list[str]` that accumulates DeepSeek token deltas and emits TTS-ready chunks on sentence boundaries (`. ? ! : \n` or ≥ N chars), so TTS starts before the full answer is generated (lower latency). `flush()` returns the remainder.
  - [x]* 3.2 Property tests: concatenated chunks == full text; never emits an empty chunk; splits on sentence ends.

### Wave 1 — Streaming STT + barge-in events (DB/event layer)

- [ ] 4. Streaming STT adapter (`services/live_stt_stream.py`)
  - [x] 4.1 Wrap the existing `live_voice.transcribe_audio_bytes` into a chunked/streaming interface: accept rolling audio buffers, return interim + final transcripts, provider-pluggable (`LIVE_STT_PROVIDER`), with a mock provider for tests.
  - [ ] 4.2 Emit `voice_user_partial` / `voice_user_final` live_events (the worker already reads `voice_user_final` for history).
  - [x]* 4.3 Tests against the mock provider for interim→final promotion.

- [ ] 5. Barge-in + turn events in the worker
  - [ ] 5.1 Add `barge_in` + `ai_turn_state` live_events; on barge-in cancel the in-flight DeepSeek stream + TTS for that request_id.
  - [x] 5.2 Make the DeepSeek streaming call cancellable (cooperative cancel token keyed by request_id).
  - [x]* 5.3 Test: a barge-in mid-stream stops further `ai_transcript_chunk` emission for that request_id.

### Wave 2 — Audio bridge into Janus (needs aiortc — host-footprint gated)

- [ ] 6. Host footprint check (gate)
  - [ ] 6.1 Measure `aiortc` + `av`/ffmpeg install size and worker RSS on a scratch container; record in `docs/build-budget.md`. If it doesn't fit the constrained host, run the bridge as a separate opt-in service or defer.
  - **GATE:** do not proceed to 7–8 until footprint is acceptable or a separate service is approved.

- [ ] 7. AI audio participant (`services/live_audio_bridge.py`)
  - [ ] 7.1 Join Janus as `ai-teacher-<id16>` via aiortc using the Rust-issued credential; subscribe to learner publisher feeds; publish one AI audio track.
  - [ ] 7.2 Opus↔PCM transcode both directions; feed learner PCM to streaming STT; play TTS audio out the published track.
  - [ ] 7.3 Wire the turn state machine + VAD + chunker + barge-in into the live audio loop.

### Wave 3 — Frontend live audio UX

- [ ] 8. Continuous-conversation UI
  - [ ] 8.1 Replace push-to-talk with continuous mic over the existing WebRTC PC; "listening / thinking / speaking" indicator; live captions from transcript events; visible interrupt.
  - [ ] 8.2 Subscribe to the AI audio track; show barge-in feedback.

### Wave 4 — Safety, cost, cutover

- [ ] 9. Pedagogy + guardrails in the realtime loop (reuse `live_ai_teacher`).
- [ ] 10. Audio-minute cost metering + ceiling (extend `live_reporting`).
- [ ] 11. `LIVE_VOICE_MODE = legacy | realtime` per-classroom flag; circuit-breaker fallback to the legacy polled path.

## Notes
- Waves 0–1 add **no heavy dependencies** and are fully unit-testable; safe to land first.
- Wave 2 (`aiortc`) is gated on a measured footprint on the 90%-full / memory-tight host.
- DeepSeek streaming, guardrails, citations, rubric, cost ceiling, circuit breaker are reused unchanged.
- The legacy turn-based loop remains the fallback throughout.
