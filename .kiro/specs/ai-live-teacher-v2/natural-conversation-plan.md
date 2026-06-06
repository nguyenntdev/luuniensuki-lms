# AI Live Teacher — Natural Conversation Plan (Tiers 1–4)

Goal: bring the live AI classroom closer to human-to-human conversation
(low latency, natural turn-taking, emotion, presence, memory).

## Current architecture (baseline)
- **Client** `frontend/src/components/live2/useRealtimeVoice.js`: energy-VAD
  turn machine (idle→listening→thinking→speaking), barge-in, sentence-streaming
  TTS queue, amplitude lip-sync via `outputLevel`.
- **Backend** `backend/main.py`: `/ai-teacher/reply` (sync) + `/ai-teacher/reply/stream`
  (SSE token stream), `/ai-teacher/stt` (batch `gpt-4o-transcribe`),
  `/ai-teacher/tts` (`tts-1` + edge/gtts fallback).
- **Pedagogy** `backend/services/live_ai_teacher.py`; STT/TTS `backend/services/live_voice.py`.

Latency chain today: user stops → (silence 900ms) → upload full clip → batch STT
→ LLM SSE → per-sentence TTS. First audio ≈ silence + STT RTT + first-sentence LLM + TTS.

---

## Tier 1 — Latency & turn-taking (biggest perceived win)

### 1.1 Thinking filler (quick, frontend-only) — DONE-FIRST
While THINKING (STT+LLM gap), play a short prerecorded/synth filler ("Để cô nghĩ chút nhé…")
or an "ừm" so the avatar isn't dead-silent. Cancel filler the instant the first real
sentence is ready.
- File: `useRealtimeVoice.js` (respond/pump). Add a filler clip played if first real
  audio hasn't started within ~600ms of THINKING; stop it before first sentence.

### 1.2 Adaptive endpointing
Replace fixed `END_SILENCE_MS=900` with dynamic silence:
- shorter (~500ms) when the utterance looks complete (ends on falling energy + length),
- longer (~1300ms) when trailing fillers/hesitation detected (very short tail).
- File: `useRealtimeVoice.js` vadTick. Heuristic first; semantic endpointing later.

### 1.3 Streaming STT (backend) — biggest latency cut
Send mic audio in chunks and get partial transcripts instead of one batch upload.
- Option A: keep `gpt-4o-transcribe` but POST overlapping partial clips during speech
  (pseudo-streaming) so final STT is near-instant at end-of-turn.
- Option B: realtime STT websocket (bigger change).
- Files: `backend/services/live_voice.py`, new `/ai-teacher/stt/stream` in `main.py`,
  client capture loop in `useRealtimeVoice.js`.

---

## Tier 2 — Emotion & presence

### 2.1 Expressive TTS
Move from flat `tts-1` to `gpt-4o-mini-tts` with a style/emotion instruction (warm
teacher), or inject SSML-like pacing. Keep edge/gtts fallback.
- Files: `backend/services/live_voice.py` (`synthesize_speech_bytes`), config model name.

### 2.2 Listening backchannels
Avatar nods + occasional "mm-hmm"/eyebrow raise while the student is speaking
(state=LISTENING with mic energy), not just idle.
- Files: `AiAvatar.jsx` (listening micro-motions driven by input `level`).

### 2.3 Viseme-ish lip-sync
Approximate mouth shapes from recent text/energy bands instead of single amplitude.
- Files: `AiAvatar.jsx`, `useRealtimeVoice.js` (expose a coarse viseme hint).

---

## Tier 3 — Echo & smooth barge-in

### 3.1 Mic hygiene + ducking
Enable `echoCancellation/noiseSuppression/autoGainControl` in getUserMedia, and
"duck" (ignore) the mic while TTS is playing so the AI's own voice can't self-trigger.
Lets us lower barge-in threshold safely.
- File: `useRealtimeVoice.js` (start() constraints; vadTick gating during playback).

### 3.2 Contextual barge-in
Distinguish a short backchannel ("vâng", "ừ") from a real interruption: only fully stop
on sustained/long speech; for short interjections, pause briefly then continue.
- File: `useRealtimeVoice.js` (barge-in logic).

---

## Tier 4 — Memory & personalization

### 4.1 Per-student long-term memory
Persist a compact per-student profile (topics learned, frequent mistakes, last session
summary) and feed a short memory line into the system prompt.
- Files: `backend/services/live_ai_teacher.py` (build_system_prompt context), a small
  store (reuse `live_events`/a new table), wired in reply + stream handlers.

---

## Rollout
Each item: implement → `get_diagnostics`/`py_compile` → commit+push → deploy (web for
frontend, api for backend, api_rust only if Rust) → verify. Tier 1 first.

## Status
- [x] 1.1 thinking filler — DONE, deployed
- [x] 1.2 adaptive endpointing — DONE, deployed
- [ ] 1.3 streaming STT — BLOCKED by provider: yescale only serves batch
      `gpt-4o-transcribe` (no realtime/websocket STT). Mitigated via adaptive
      endpointing (1.2) which cut the perceived end-of-turn latency. Revisit when
      a realtime STT provider (OpenAI Realtime / Deepgram) is available.
- [x] 2.1 expressive TTS — code DONE (instructions for gpt-4o-mini-tts) but the
      model is unavailable on yescale (503); edge-tts also blocked (MS 403).
      Shipped a working nudge instead: warmer `shimmer` teacher voice on tts-1.
- [x] 2.2 listening backchannels — DONE, deployed
- [x] 2.3 viseme-ish lip-sync — DONE, deployed
- [x] 3.1 mic hygiene + ducking — DONE, deployed
- [x] 3.2 contextual barge-in (volume duck) — DONE, deployed
- [x] 4.1 per-student memory — DONE, deployed

## Provider constraints (yescale) discovered
- TTS: only `tts-1` works (voices alloy/echo/fable/onyx/nova/shimmer). `gpt-4o-mini-tts` → 503.
- edge-tts (vi-VN-HoaiMyNeural) → Microsoft 403 (token); gTTS robotic fallback only.
- STT: `gpt-4o-transcribe` batch only.
- To unlock true human-likeness (expressive Vietnamese TTS + streaming STT), add a
  provider that serves `gpt-4o-mini-tts`/`gpt-4o-realtime` or Deepgram/ElevenLabs.

