# AI Live Teacher & Classroom v2 — Deep Improvement Plan

## Current state (audit summary)
- **Backend**: `backend/services/live_ai_teacher.py` (pedagogy helpers), `services/ai_teacher_agent/realtime_worker.py` (streaming worker), `live_voice.py` (STT `gpt-4o-transcribe`, TTS `tts-1` + edge/gtts fallback), `live_sessions.py`, `live_session_reporting.py` (staff dashboard/summaries). Reply endpoint `/ai-teacher/reply` (non-streaming), `/ai-teacher/stt`, `/ai-teacher/tts`.
- **Frontend**: `frontend/src/components/live2/*` — Meet-style room, hands-free voice loop (`useRealtimeVoice.js`), a CSS **orb** (no avatar), People/Chat side panel.
- **Key gaps**:
  1. AI presence is a CSS orb — **no avatar, no animation, no lip-sync**.
  2. Conversation history is **session-global** → cross-student bleed; no per-student addressing/memory.
  3. Chat/captions are **local-only** (room never polls `/events`) → multi-student chat & shared AI transcript don't work.
  4. **No teacher console** in-room (all host/moderation APIs exist but are unwired).
  5. AI features are heuristic; reply is non-streaming; no live quick-actions (explain simpler / quiz / summarize).

## Goals
1. **Live 3D avatar** with idle/blink/breathing + state animations + audio-driven lip-sync (replaces/augments the orb).
2. **Multi-student**: AI answers many students, addresses them by name, keeps light per-student context; shared transcript/chat/raise-hand visible to all.
3. **Teacher co-pilot**: in-room teacher console — live transcript, question queue, engagement, moderation, AI suggestions, end+summary.
4. **Smarter AI**: streaming replies, quick-action modes (explain simpler / go deeper / quiz me / summarize), proactive engagement.

## Avatar choice
Use a **Ready Player Me GLB** rendered with `@react-three/fiber` (already a dep). Idle breathing + timed blink in code; **amplitude-driven `jawOpen`/viseme morph** from the TTS audio (Web Audio AnalyserNode) for believable lip-sync without phoneme timing. Graceful fallback to the orb if the GLB fails to load. (Reference: met4citizen/TalkingHead `speakAudio` approach.)

## Waves
- **Wave A — Shared room (multi-student)**: FE polls `/events` to render a shared, persisted transcript + chat + raise-hand for everyone. Backend: include speaker display name on AI requests; build per-student rolling history (filter events by asker) + a short shared class-context line. New quick `raise_hand` + `live_chat_message` rendering.
- **Wave B — Live Avatar**: `AiAvatar.jsx` (react-three-fiber) with states idle/listening/thinking/speaking, blink/breath, amplitude lip-sync; `useRealtimeVoice` exposes a live output-amplitude signal during TTS. Toggle avatar/orb.
- **Wave C — Teacher console**: `TeacherConsole.jsx` wiring `getLiveSessionDashboard`, host settings (lock/AI/grade/cost), mute-all, remove, role change, end session, question-queue management, live engagement.
- **Wave D — Smarter AI**: streaming reply endpoint (SSE) + client; quick-action chips (explain simpler / deeper / quiz / summarize); address student by name; proactive nudge when a student is idle.

## Deploy
Backend changes → rebuild api/api_rust + worker; frontend → rebuild web. Commit + push per wave.
