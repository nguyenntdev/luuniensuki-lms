# Plan: Real-Time Conversational AI Teacher (speech-to-speech)

## Goal

The AI teacher should converse like a human in the virtual classroom: it **listens
continuously**, **detects when a learner finishes speaking**, **responds with low
latency in natural speech**, and can be **interrupted mid-sentence** (barge-in).
Target perceived latency: **< 1.5 s** from "learner stops talking" to "AI starts
talking" (vs. the current 3–8 s polling pipeline).

## Honest assessment of the current state

Today's flow is **turn-based and polled**, not conversational:

```
browser records clip → POST audio → STT (voice API) → write ai_voice_request event
   → [worker polls live_events every 1s] → DeepSeek (text) → write ai_voice_ready event
   → [browser polls events] → fetch TTS audio → play
```

Limitations that make it feel non-human:
1. **Polling latency** — 1 s worker poll + frontend poll cadence stack up.
2. **No continuous listening** — the learner must push-to-talk / send a clip.
3. **No barge-in** — you can't interrupt the AI while it's speaking.
4. **No turn detection** — no VAD/endpointing; the client decides when a turn ends.
5. **Audio is out-of-band** — TTS is fetched over HTTP and played, not a live
   media track. The new Janus media plane is not yet used by the AI.

What we already have and will reuse:
- **DeepSeek** streaming chat (`_call_deepseek_chat_stream`) + pedagogy policy,
  guardrails, citations, rubric, cost ceiling, circuit breaker (in
  `live_ai_teacher`, `realtime_worker.py`). **Keep this — it's the "brain".**
- **STT/TTS** helpers (`live_voice.transcribe_audio_bytes`,
  `synthesize_speech_bytes`) with a voice API + edge-tts/gtts fallback.
- **Janus VideoRoom** media plane (deployed, passive) + Rust signaling broker.
- The `ai-teacher-<id16>` participant identity + AI hook boundary.

## Two realistic architectures

### Path A — Realtime speech-to-speech API (recommended)

Bridge a **dedicated realtime model** (OpenAI Realtime API or Gemini Live — both
are WebSocket, audio-in/audio-out, with built-in VAD/turn-detection and barge-in)
between the learner's audio and the room. The AI worker becomes an **audio bridge**:

```
learner mic ──WebRTC audio──> Janus ──(RTP)──> AI worker (subscribes to learner feed)
   AI worker ──PCM frames──> Realtime API (WS, server-VAD) ──audio out──> AI worker
   AI worker ──publishes TTS audio track──> Janus ──> all participants hear the AI
```

- **Pros:** genuine ~500 ms latency, barge-in + turn detection handled by the
  model, single dependency, far less glue code.
- **Cons:** new external dependency + cost; DeepSeek (current LLM) has no realtime
  audio API, so the "brain" model changes for the live path (text DeepSeek can
  still own async tasks like rubric/summary). Needs an API that supports realtime
  audio (OpenAI `gpt-4o-realtime`, Gemini Live, or similar).

### Path B — Self-assembled streaming pipeline

Keep DeepSeek as the brain; assemble realtime from parts:

```
Janus learner audio → AI worker → streaming STT (Deepgram/Whisper-streaming) + VAD
   → endpoint detection → DeepSeek stream → sentence-chunk → streaming TTS
   → publish audio track to Janus ; cancel on barge-in
```

- **Pros:** keeps DeepSeek; full control of pedagogy; provider-swappable.
- **Cons:** we build VAD, endpointing, barge-in cancellation, and audio jitter
  buffering ourselves — materially more work and more latency than Path A.

**Recommendation:** Path A for the live voice loop (quality + speed), keep DeepSeek
for the non-realtime pedagogy artifacts (rubric, citations, summary, cost
accounting). Make the realtime provider pluggable so Path B remains an option.

## Architecture (Path A)

```mermaid
graph TD
    subgraph Browser
      MIC[mic] --> PC[WebRTC PeerConnection]
      SPK[speaker] --- PC
    end
    subgraph Rust[Rust control/signaling]
      SIG[WS signaling broker]
      REST[/api/v1/live-sessions/*]
    end
    subgraph Janus[Janus VideoRoom]
      ROOM[(room feeds)]
    end
    subgraph Py[Python AI worker — realtime bridge]
      SUB[subscribe learner audio]
      RT[Realtime API client WS]
      PUB[publish ai-teacher audio track]
      PED[DeepSeek async: rubric/citation/summary]
    end
    PC <-->|SDP/ICE via Rust| SIG
    PC <-->|RTP audio| ROOM
    SUB --> ROOM
    PUB --> ROOM
    SUB --> RT --> PUB
    RT --> PED
```

The Rust control plane is unchanged (it already issues the AI-teacher credential
and fires lifecycle hooks). The change is **inside the Python worker**: it stops
polling `ai_voice_request` text events and instead joins the room as a real audio
participant that streams to/from a realtime model.

## Implementation phases

### Phase 1 — AI joins the room as a real audio participant
- AI worker requests an AI-teacher join credential from Rust
  (`POST /api/v1/live-sessions/:id/ai-teacher/credential`, already built) and
  attaches to Janus as `ai-teacher-<id16>` via a Janus client
  (`aiortc` for Python WebRTC, or a thin Janus WS client).
- Subscribe to each learner publisher feed; publish one AI audio track.
- **Exit criteria:** AI appears in the roster with a live (silent) audio track;
  learners can see/hear the AI track placeholder.

### Phase 2 — Realtime provider client (pluggable)
- Add `services/live_realtime.py` with a `RealtimeSession` interface:
  `send_audio(pcm)`, `on_audio(cb)`, `on_transcript(cb)`, `commit_turn()`,
  `cancel()` (barge-in). Implement an OpenAI-Realtime / Gemini-Live adapter
  behind a `LIVE_REALTIME_PROVIDER` flag; mock adapter for tests.
- Pin deps + record footprint in `docs/build-budget.md`.
- **Exit criteria:** unit tests drive the mock provider through a full turn.

### Phase 3 — Audio bridge + turn-taking
- Resample/transcode Janus Opus ↔ realtime PCM (16 kHz) both directions.
- Use the provider's **server-side VAD** for endpointing; on detected end of the
  learner's turn, let the model respond; stream the model's audio out to Janus.
- **Barge-in:** when the learner starts speaking while the AI is talking, call
  `cancel()` and stop the outbound track immediately.
- **Exit criteria:** measured stop-to-start latency < 1.5 s; interrupting the AI
  stops its speech within ~300 ms.

### Phase 4 — Pedagogy + safety in the loop
- Feed the system prompt (grade level, heritage cluster, hint-first policy) into
  the realtime session instructions (reuse `live_ai_teacher.build_system_prompt`).
- Run guardrails on the streaming transcript; on unsafe content, `cancel()` and
  emit the existing safety response.
- Keep DeepSeek async tasks (rubric, citations, checkpoints, summary, cost
  accounting) driven off the realtime transcript so reporting stays intact.
- **Exit criteria:** guardrail block interrupts speech; rubric/citation/cost
  events still recorded; cost ceiling enforced (realtime audio cost model added
  to `live_reporting`).

### Phase 5 — Frontend live audio UX
- Replace push-to-talk + event polling with: continuous mic capture over the
  existing WebRTC PeerConnection, a "listening / thinking / speaking" indicator,
  live captions from transcript events, and a visible interrupt affordance.
- **Exit criteria:** a learner can hold a spoken back-and-forth with the AI with
  no button-pushing; captions track speech.

### Phase 6 — Cutover + cost/limits
- Gate behind `LIVE_VOICE_MODE = legacy | realtime` per classroom (canary).
- Add per-session realtime minute budget + the existing rate-limit buckets.
- Keep the legacy polled path as fallback when the realtime provider is down
  (circuit breaker → fall back to STT→DeepSeek→TTS turn-based).
- **Exit criteria:** canary classroom runs realtime; flip back is a flag.

## Correctness properties (for later PBT / integration tests)
1. **Turn endpointing:** AI never starts responding while the learner is still
   speaking (no overlap except intentional backchannel).
2. **Barge-in:** learner speech during AI playback cancels AI audio within a
   bounded time; the cancelled turn records a `barge_in` event.
3. **One AI audio track:** exactly one `ai-teacher` publisher per session.
4. **Guardrail interrupt:** unsafe content stops outbound audio and emits the
   safety event; no unsafe audio is published.
5. **Cost ceiling:** realtime minutes are metered; exceeding the ceiling ends the
   AI voice loop with a graceful spoken notice.
6. **Fallback:** when the realtime provider is unavailable, the session degrades
   to the legacy turn-based loop without dropping the session.

## Key risks / decisions to confirm
- **Provider:** OpenAI Realtime vs Gemini Live vs self-assembled (affects cost,
  latency, and whether DeepSeek stays the live brain). **Needs your call.**
- **Python WebRTC:** `aiortc` adds a non-trivial dependency on the constrained
  host (it pulls `av`/ffmpeg). Measure RSS before committing; the 512 MB Janus
  cap plus an aiortc bridge needs headroom on the 33 GB/90%-full box.
- **Cost:** realtime audio APIs are billed per audio-minute (input+output) — much
  higher than text DeepSeek. The existing cost-ceiling machinery must extend to
  audio-minutes before enabling for real classrooms.

## What this plan deliberately does NOT change
- The Rust control plane / signaling / Janus migration (already built/deployed).
- The AI-teacher identity, lifecycle hooks, roster, moderation, event log.
- The legacy turn-based path stays as a tested fallback.
