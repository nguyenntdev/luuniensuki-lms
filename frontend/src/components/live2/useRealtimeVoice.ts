"use client";

/**
 * useRealtimeVoice — browser-side realtime conversation loop for the AI teacher.
 *
 * Drives a continuous, hands-free voice conversation against the existing
 * turn-based voice endpoints (STT -> ai-teacher/reply -> TTS), but with a
 * client-side turn state machine + energy VAD so it FEELS continuous:
 *
 *   idle -> listening (mic open, VAD watches energy)
 *        -> (silence after speech) -> thinking (STT + LLM)
 *        -> speaking (TTS playback)
 *        -> back to listening
 *
 * Barge-in: if the user starts speaking (energy over threshold) while the AI is
 * speaking, playback is stopped immediately and we return to listening.
 *
 * This deliberately mirrors the backend FSM (live_turn) and VAD (live_vad) so
 * behavior is consistent across client and server. It uses MediaRecorder for
 * capture and the Web Audio API (AnalyserNode) for energy-based VAD — no extra
 * dependencies.
 *
 * State exposed: { state, captions, listening, error, levels } and controls
 * { start, stop, interrupt }.
 */

import { useCallback, useEffect, useRef, useState } from "react";

// Turn states (mirror backend live_turn).
export const TURN = Object.freeze({
  IDLE: "idle",
  LISTENING: "listening",
  THINKING: "thinking",
  SPEAKING: "speaking",
});

/** One of the conversation turn states ("idle" | "listening" | ...). */
export type TurnState = (typeof TURN)[keyof typeof TURN];

/** A live session id (numeric or string form accepted by the API client). */
type SessionId = string | number;

/** Caption entry emitted to the parent for the transcript feed. */
interface TranscriptEntry {
  speaker: "user" | "assistant";
  text: string;
}

/** Minimal shape read from the STT (transcribe) response. */
interface TranscribeResult {
  transcript?: string | null;
  [key: string]: unknown;
}

/** Minimal shape read from a non-streaming ai-teacher reply. */
interface AskTeacherResult {
  text?: string | null;
  answer?: string | null;
  [key: string]: unknown;
}

/** Minimal shape read from a streaming ai-teacher reply. */
interface StreamAskResult {
  answer?: string | null;
  [key: string]: unknown;
}

/**
 * Loose union describing the values a `synthesize()` implementation may return:
 * a Blob, an envelope with a `.blob`, an ArrayBuffer, or an ArrayBufferView.
 * Documented as a union so we don't fall back to `any` for the media payload.
 */
type SynthesizeResult =
  | Blob
  | ArrayBuffer
  | ArrayBufferView
  | { blob?: Blob; arrayBuffer?: unknown }
  | null
  | undefined;

/** Options accepted by {@link useRealtimeVoice}. */
export interface UseRealtimeVoiceOptions {
  sessionId: SessionId;
  enabled: boolean;
  micDeviceId?: string;
  /** Called with each finalized caption (you + AI teacher). */
  onTranscript?: (entry: TranscriptEntry) => void;
  /** Called with the live interim transcript of the user while speaking. */
  onPartialTranscript?: (text: string) => void;
  /** Called with the growing AI text while streaming. */
  onStreamDelta?: (fullText: string) => void;
  transcribe: (args: { sessionId: SessionId; file: File }) => Promise<unknown>;
  askTeacher: (args: { sessionId: SessionId; message: string; mode?: string }) => Promise<unknown>;
  streamAsk?: (args: {
    sessionId: SessionId;
    message: string;
    mode?: string;
    onDelta: (delta: string) => void;
  }) => Promise<unknown>;
  synthesize: (args: { sessionId: SessionId; text: string; signal?: AbortSignal }) => Promise<unknown>;
}

/** Imperative controls + live state returned by {@link useRealtimeVoice}. */
export interface UseRealtimeVoiceResult {
  state: TurnState;
  listening: boolean;
  error: string;
  level: number;
  outputLevel: number;
  start: () => Promise<void>;
  stop: () => void;
  interrupt: () => void;
  ask: (args: { message?: string; mode?: string }) => Promise<void>;
}

// VAD tuning (mirror backend live_vad defaults).
// Adaptive endpointing: a clearly-complete utterance ends fast; a short/hesitant
// one waits longer so we don't cut the speaker off mid-thought ("ờ...", "tức là...").
const END_SILENCE_COMPLETE_MS = 650; // long enough utterance -> end quickly
const END_SILENCE_HESITANT_MS = 1250; // short/hesitant tail -> be patient
const COMPLETE_SPEECH_MS = 1400; // >= this much speech counts as a "complete" turn
const MIN_SPEECH_MS = 500; // require ~0.5s of real speech before we treat it as a turn
const SPEECH_RMS_THRESHOLD = 0.032; // energy above this = speech (raised to ignore room noise)
const FRAME_MS = 50; // VAD evaluation cadence
const MAX_UTTERANCE_MS = 15000; // hard cap on a single utterance

// Barge-in (interrupt the AI while it is speaking) is deliberately LESS
// sensitive than start-of-turn detection: the user must speak clearly AND for a
// sustained moment, otherwise the AI's own TTS bleeding into the mic, a cough,
// or a short background noise would cut it off constantly.
const BARGE_IN_RMS_THRESHOLD = 0.06; // must be noticeably louder than ambient/TTS bleed
const BARGE_IN_MS = 350; // must persist this long before we stop the AI
const DUCK_RMS_THRESHOLD = 0.045; // softer threshold: lower the AI's volume while you talk
const DUCK_GAIN = 0.28; // ducked volume (so a backchannel doesn't force a full stop)

// Streaming STT (Tier 1.3): while the user speaks, periodically transcribe the
// audio captured so far to show a live interim caption. The final transcribe at
// end-of-turn stays authoritative. Bounded cadence to limit STT cost.
const PARTIAL_STT_FIRST_MS = 1500; // don't attempt a partial before this much speech
const PARTIAL_STT_INTERVAL_MS = 1600; // min gap between partial transcribes
const RECORDER_TIMESLICE_MS = 250; // emit data chunks during recording (for partials)

function rms(timeDomain: Uint8Array): number {
  let sum = 0;
  for (let i = 0; i < timeDomain.length; i += 1) {
    const v = (timeDomain[i] - 128) / 128;
    sum += v * v;
  }
  return Math.sqrt(sum / timeDomain.length);
}

// --- Sentence-level TTS streaming (LiveKit-style) -------------------------
// As LLM tokens stream in, we chunk the text into speakable sentences and
// synthesize/play them one after another so the avatar starts talking after
// the FIRST sentence instead of waiting for the whole answer.
const MIN_TTS_CHUNK = 24; // don't speak fragments shorter than this (chars)
const MAX_TTS_BUF = 200; // force-flush if no sentence boundary by here

// Strip markdown / citation tags so TTS doesn't read "asterisk" or "[S1]".
function cleanForTts(value: unknown): string {
  return String(value || "")
    .replace(/\[[A-Za-z]{0,2}\d+\]/g, " ") // [S1] [R2]
    .replace(/[*_`#>]/g, " ") // markdown emphasis / headings / quotes
    .replace(/^\s*[-•]\s+/gm, " ") // bullet markers
    .replace(/\s+/g, " ")
    .trim();
}

// Pull complete sentences out of a growing buffer. Returns the speakable
// chunks plus the unconsumed remainder (kept until more text arrives).
function takeSentences(buf: string): { chunks: string[]; rest: string } {
  const chunks: string[] = [];
  let seg = "";
  let consumed = 0;
  for (let i = 0; i < buf.length; i += 1) {
    const c = buf[i];
    seg += c;
    const isBoundary = c === "." || c === "!" || c === "?" || c === "…" || c === "\n";
    if (!isBoundary) continue;
    // absorb trailing quotes/brackets/spaces so they ride with this sentence
    let j = i + 1;
    while (j < buf.length && /['")\]\s]/.test(buf[j])) {
      seg += buf[j];
      j += 1;
    }
    i = j - 1;
    const trimmed = seg.trim();
    if (trimmed.length >= MIN_TTS_CHUNK || (c === "\n" && trimmed.length >= 8)) {
      chunks.push(trimmed);
      consumed = i + 1;
      seg = "";
    }
  }
  return { chunks, rest: buf.slice(consumed) };
}


export function useRealtimeVoice({
  sessionId,
  enabled,
  micDeviceId,
  onTranscript, // ({ speaker, text }) => void  (for captions feed)
  onPartialTranscript, // (text) => void  live interim transcript of the user while speaking
  onStreamDelta, // (fullText) => void  (live partial AI text while streaming)
  transcribe, // async ({ sessionId, file }) => { transcript }
  askTeacher, // async ({ sessionId, message }) => { text, ... }
  streamAsk, // optional async ({ sessionId, message, mode, onDelta }) => { answer }
  synthesize, // async ({ sessionId, text, signal }) => Blob | ArrayBuffer
}: UseRealtimeVoiceOptions): UseRealtimeVoiceResult {
  const [state, setState] = useState<TurnState>(TURN.IDLE);
  const [listening, setListening] = useState(false);
  const [error, setError] = useState("");
  const [level, setLevel] = useState(0); // 0..1 mic energy, for the UI meter
  const [outputLevel, setOutputLevel] = useState(0); // 0..1 AI speech amplitude (lip-sync)

  const stateRef = useRef<TurnState>(TURN.IDLE);
  const streamRef = useRef<MediaStream | null>(null);
  const audioCtxRef = useRef<AudioContext | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const recorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const vadTimerRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const speechMsRef = useRef(0);
  const silenceMsRef = useRef(0);
  const inUtteranceRef = useRef(false);
  const utteranceMsRef = useRef(0);
  const bargeMsRef = useRef(0); // sustained loud-speech accumulator for barge-in
  const mimeRef = useRef("audio/webm"); // recorder mime (for building partial blobs)
  const partialBusyRef = useRef(false); // a partial transcribe is in flight
  const lastPartialMsRef = useRef(0); // utteranceMs at last partial attempt
  const ttsAudioRef = useRef<HTMLAudioElement | null>(null);
  const ttsSourceRef = useRef<AudioBufferSourceNode | null>(null); // Web Audio BufferSource (preferred playback)
  const ttsAnalyserRef = useRef<AnalyserNode | null>(null); // analyser on the TTS output (lip-sync)
  const ttsGainRef = useRef<GainNode | null>(null); // gain node on TTS output (for ducking on barge-in)
  const outRafRef = useRef<number | null>(null); // rAF id for the output-amplitude loop
  const ttsAbortRef = useRef<AbortController | null>(null);
  const closingRef = useRef(false);
  // Sentence-streaming TTS queue.
  const ttsQueueRef = useRef<string[]>([]); // pending sentence strings to synthesize
  const ttsPumpActiveRef = useRef(false); // is the synth/play pump running
  const streamFinishedRef = useRef(false); // producer finished enqueuing
  const clipResolveRef = useRef<((ok: boolean) => void) | null>(null); // resolve() of the in-flight clip's end promise
  const turnSeqRef = useRef(0); // monotonic id; invalidates a turn's producer on interrupt
  // Thinking-filler: a short "ừm, để cô xem nhé" played during the STT+LLM gap
  // so the avatar isn't dead-silent before the first real sentence.
  const fillerBufferRef = useRef<AudioBuffer | null>(null); // decoded AudioBuffer (cached)
  const fillerSrcRef = useRef<AudioBufferSourceNode | null>(null); // active filler BufferSource
  const fillerTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null); // delay timer before the filler kicks in
  const fillerPrimingRef = useRef(false);

  const setTurn = useCallback((next: TurnState) => {
    stateRef.current = next;
    setState(next);
  }, []);

  const stopPlayback = useCallback(() => {
    // Invalidate the current speaking turn so a still-arriving SSE stream stops
    // enqueueing sentences, and drop any queued/streaming sentences.
    turnSeqRef.current += 1;
    ttsQueueRef.current = [];
    streamFinishedRef.current = true;
    // Stop the thinking-filler too.
    if (fillerTimerRef.current) {
      clearTimeout(fillerTimerRef.current);
      fillerTimerRef.current = null;
    }
    if (fillerSrcRef.current) {
      try {
        fillerSrcRef.current.onended = null;
        fillerSrcRef.current.stop();
      } catch {}
      try {
        fillerSrcRef.current.disconnect();
      } catch {}
      fillerSrcRef.current = null;
    }
    if (clipResolveRef.current) {
      try {
        clipResolveRef.current(false);
      } catch {}
      clipResolveRef.current = null;
    }
    if (ttsAbortRef.current) {
      try {
        ttsAbortRef.current.abort();
      } catch {}
      ttsAbortRef.current = null;
    }
    // Stop the output-amplitude (lip-sync) loop.
    if (outRafRef.current) {
      try {
        cancelAnimationFrame(outRafRef.current);
      } catch {}
      outRafRef.current = null;
    }
    if (ttsAnalyserRef.current) {
      try {
        ttsAnalyserRef.current.disconnect();
      } catch {}
      ttsAnalyserRef.current = null;
    }
    setOutputLevel(0);
    // Web Audio source (preferred path).
    const src = ttsSourceRef.current;
    if (src) {
      try {
        src.onended = null;
        src.stop();
      } catch {}
      try {
        src.disconnect();
      } catch {}
      ttsSourceRef.current = null;
    }
    // HTMLAudioElement fallback path.
    const audio = ttsAudioRef.current;
    if (audio) {
      try {
        audio.pause();
        if (audio.src) URL.revokeObjectURL(audio.src);
      } catch {}
      ttsAudioRef.current = null;
    }
  }, []);

  // Play ONE audio clip and resolve when it finishes (or fails). Prefers the
  // Web Audio API through the AudioContext unlocked by the join gesture (so the
  // browser autoplay policy doesn't silently block playback after the async
  // STT->LLM->TTS gap), with an HTMLAudio fallback. Does NOT change turn state —
  // the sentence pump owns the idle/speaking transitions.
  const playClip = useCallback(
    async (audioBlob: Blob | null | undefined): Promise<boolean> => {
      if (!audioBlob || audioBlob.size === 0) return false;
      const ctx = audioCtxRef.current;
      if (ctx) {
        try {
          if (ctx.state === "suspended") await ctx.resume().catch(() => {});
          const arrayBuf = await audioBlob.arrayBuffer();
          const audioBuffer = await new Promise<AudioBuffer>((resolve, reject) => {
            const p = ctx.decodeAudioData(arrayBuf.slice(0), resolve, reject);
            if (p && typeof p.then === "function") p.then(resolve, reject);
          });
          if (closingRef.current || stateRef.current !== TURN.SPEAKING) return false;
          return await new Promise<boolean>((resolve) => {
            let done = false;
            const finish = (ok: boolean) => {
              if (done) return;
              done = true;
              if (clipResolveRef.current === finish) clipResolveRef.current = null;
              if (outRafRef.current) {
                try {
                  cancelAnimationFrame(outRafRef.current);
                } catch {}
                outRafRef.current = null;
              }
              if (ttsAnalyserRef.current) {
                try {
                  ttsAnalyserRef.current.disconnect();
                } catch {}
                ttsAnalyserRef.current = null;
              }
              if (ttsGainRef.current) {
                try {
                  ttsGainRef.current.disconnect();
                } catch {}
                ttsGainRef.current = null;
              }
              setOutputLevel(0);
              resolve(ok);
            };
            clipResolveRef.current = finish;
            const src = ctx.createBufferSource();
            src.buffer = audioBuffer;
            // Analyser between source and destination -> drives avatar lip-sync.
            try {
              const analyser = ctx.createAnalyser();
              analyser.fftSize = 256;
              const gain = ctx.createGain();
              gain.gain.value = 1;
              src.connect(analyser);
              analyser.connect(gain);
              gain.connect(ctx.destination);
              ttsAnalyserRef.current = analyser;
              ttsGainRef.current = gain;
              const buf = new Uint8Array(analyser.fftSize);
              const tick = () => {
                if (!ttsAnalyserRef.current) return;
                ttsAnalyserRef.current.getByteTimeDomainData(buf);
                setOutputLevel(Math.min(1, rms(buf) * 3.2));
                outRafRef.current = requestAnimationFrame(tick);
              };
              outRafRef.current = requestAnimationFrame(tick);
            } catch {
              src.connect(ctx.destination);
            }
            src.onended = () => {
              if (ttsSourceRef.current === src) ttsSourceRef.current = null;
              finish(true);
            };
            ttsSourceRef.current = src;
            try {
              src.start(0);
            } catch {
              finish(false);
            }
          });
        } catch {
          // fall through to HTMLAudio
        }
      }
      // Fallback: HTMLAudioElement.
      return await new Promise<boolean>((resolve) => {
        let done = false;
        const finish = (ok: boolean) => {
          if (done) return;
          done = true;
          if (clipResolveRef.current === finish) clipResolveRef.current = null;
          resolve(ok);
        };
        clipResolveRef.current = finish;
        try {
          const url = URL.createObjectURL(audioBlob);
          const audio = new Audio(url);
          ttsAudioRef.current = audio;
          audio.onended = () => {
            if (ttsAudioRef.current === audio) {
              try {
                URL.revokeObjectURL(url);
              } catch {}
              ttsAudioRef.current = null;
            }
            finish(true);
          };
          audio.onerror = () => finish(false);
          audio.play().catch(() => finish(false));
        } catch {
          finish(false);
        }
      });
    },
    [setOutputLevel],
  );

  // Normalize a synthesize() result into a playable Blob.
  const synthesizeBlob = useCallback(
    async (text: string, signal?: AbortSignal): Promise<Blob | null> => {
      const audioData = (await synthesize({ sessionId, text, signal })) as SynthesizeResult;
      if (audioData instanceof Blob) return audioData;
      if (audioData && !ArrayBuffer.isView(audioData) && !(audioData instanceof ArrayBuffer) && audioData.blob instanceof Blob) {
        return audioData.blob;
      }
      if (audioData instanceof ArrayBuffer) return new Blob([audioData], { type: "audio/mpeg" });
      if (ArrayBuffer.isView(audioData)) return new Blob([audioData as BlobPart], { type: "audio/mpeg" });
      if (audioData && "arrayBuffer" in audioData && audioData.arrayBuffer) {
        return new Blob([audioData as BlobPart], { type: "audio/mpeg" });
      }
      return null;
    },
    [sessionId, synthesize],
  );

  // Stop any in-flight thinking-filler clip immediately.
  const stopFiller = useCallback(() => {
    if (fillerTimerRef.current) {
      clearTimeout(fillerTimerRef.current);
      fillerTimerRef.current = null;
    }
    const src = fillerSrcRef.current;
    if (src) {
      try {
        src.onended = null;
        src.stop();
      } catch {}
      try {
        src.disconnect();
      } catch {}
      fillerSrcRef.current = null;
    }
  }, []);

  // Lazily synthesize + cache the filler clip so it's ready before it's needed.
  const primeFiller = useCallback(async () => {
    if (fillerBufferRef.current || fillerPrimingRef.current) return;
    const ctx = audioCtxRef.current;
    if (!ctx) return;
    fillerPrimingRef.current = true;
    try {
      const blob = await synthesizeBlob("Ừm, để cô xem nhé.");
      if (!blob) return;
      const arrayBuf = await blob.arrayBuffer();
      const audioBuffer = await new Promise<AudioBuffer>((resolve, reject) => {
        const p = ctx.decodeAudioData(arrayBuf.slice(0), resolve, reject);
        if (p && typeof p.then === "function") p.then(resolve, reject);
      });
      fillerBufferRef.current = audioBuffer;
    } catch {
      /* filler is best-effort */
    } finally {
      fillerPrimingRef.current = false;
    }
  }, [synthesizeBlob]);

  // Play the cached filler once, but only while still THINKING (no real audio yet).
  const playFiller = useCallback(() => {
    const ctx = audioCtxRef.current;
    const audioBuffer = fillerBufferRef.current;
    if (!ctx || !audioBuffer || closingRef.current) return;
    if (stateRef.current !== TURN.THINKING) return;
    try {
      const src = ctx.createBufferSource();
      src.buffer = audioBuffer;
      const gain = ctx.createGain();
      gain.gain.value = 0.7; // a touch quieter than the real answer
      src.connect(gain);
      gain.connect(ctx.destination);
      src.onended = () => {
        if (fillerSrcRef.current === src) fillerSrcRef.current = null;
      };
      fillerSrcRef.current = src;
      src.start(0);
    } catch {
      /* ignore */
    }
  }, []);


  // clip back-to-back so the AI keeps talking as later sentences arrive.
  const pumpTtsQueue = useCallback(async () => {
    if (ttsPumpActiveRef.current) return;
    ttsPumpActiveRef.current = true;
    try {
      while (!closingRef.current && stateRef.current === TURN.SPEAKING) {
        if (ttsQueueRef.current.length === 0) {
          if (streamFinishedRef.current) break;
          await new Promise((r) => setTimeout(r, 60)); // wait for more tokens
          continue;
        }
        const sentence = ttsQueueRef.current.shift();
        const speakText = cleanForTts(sentence);
        if (!speakText) continue;
        const controller = new AbortController();
        ttsAbortRef.current = controller;
        let blob = null;
        try {
          blob = await synthesizeBlob(speakText, controller.signal);
        } catch {
          blob = null;
        }
        if (closingRef.current || stateRef.current !== TURN.SPEAKING) break;
        if (blob) await playClip(blob);
      }
    } finally {
      ttsPumpActiveRef.current = false;
      if (
        !closingRef.current &&
        stateRef.current === TURN.SPEAKING &&
        ttsQueueRef.current.length === 0 &&
        streamFinishedRef.current
      ) {
        setTurn(TURN.LISTENING);
      }
    }
  }, [playClip, synthesizeBlob, setTurn]);

  // Enqueue a sentence for speech; flips to SPEAKING and starts the pump.
  const enqueueTts = useCallback(
    (sentence: string) => {
      const s = String(sentence || "").trim();
      if (!s) return;
      stopFiller(); // real speech is ready — kill the thinking filler
      ttsQueueRef.current.push(s);
      if (stateRef.current !== TURN.SPEAKING) setTurn(TURN.SPEAKING);
      if (!ttsPumpActiveRef.current) pumpTtsQueue();
    },
    [pumpTtsQueue, setTurn, stopFiller],
  );

  // ---- speak an AI reply for a given user text (shared by voice + quick-actions)
  const respond = useCallback(
    async (
      userText: string | undefined,
      { mode, echoUser = false }: { mode?: string; echoUser?: boolean } = {},
    ) => {
      if (closingRef.current) return;
      const text = String(userText || "").trim();
      if (!text) {
        setTurn(TURN.LISTENING);
        return;
      }
      setTurn(TURN.THINKING);
      if (echoUser) onTranscript?.({ speaker: "user", text });

      // Arm the thinking-filler: if no real sentence has started speaking within
      // a short window, play a brief "ừm, để cô xem nhé" so we're not silent.
      stopFiller();
      fillerTimerRef.current = setTimeout(() => {
        if (!closingRef.current && stateRef.current === TURN.THINKING) playFiller();
      }, 700);

      // Reset the TTS pipeline for this turn.
      ttsQueueRef.current = [];
      streamFinishedRef.current = false;
      const myTurn = ++turnSeqRef.current;

      // Prefer SSE streaming: chunk tokens into sentences and start speaking the
      // first sentence immediately (LiveKit-style), falling back to a single
      // non-streaming ask on any transport error so the room never stalls.
      let answer = "";
      if (typeof streamAsk === "function") {
        try {
          let acc = "";
          let pending = "";
          const result = await streamAsk({
            sessionId,
            message: text,
            mode,
            onDelta: (delta: string) => {
              if (closingRef.current || turnSeqRef.current !== myTurn) return;
              const d = String(delta || "");
              acc += d;
              onStreamDelta?.(acc);
              pending += d;
              const { chunks, rest } = takeSentences(pending);
              pending = rest;
              for (const c of chunks) enqueueTts(c);
            },
          });
          if (turnSeqRef.current !== myTurn) return; // interrupted mid-stream
          answer = String((result as StreamAskResult)?.answer || acc || "").trim();
          if (pending.trim()) enqueueTts(pending); // flush trailing partial sentence
        } catch {
          answer = "";
          ttsQueueRef.current = [];
        }
      }
      if (turnSeqRef.current !== myTurn) return; // interrupted

      if (!answer) {
        // Non-streaming fallback (or stream failed) — still chunk for low latency.
        try {
          const reply = await askTeacher({ sessionId, message: text, mode });
          answer = String((reply as AskTeacherResult)?.text || (reply as AskTeacherResult)?.answer || "").trim();
        } catch {
          answer = "";
        }
        if (turnSeqRef.current !== myTurn) return; // interrupted during fallback
        if (!answer) {
          onStreamDelta?.("");
          streamFinishedRef.current = true;
          if (stateRef.current !== TURN.SPEAKING) setTurn(TURN.LISTENING);
          return;
        }
        onStreamDelta?.("");
        onTranscript?.({ speaker: "assistant", text: answer });
        const { chunks, rest } = takeSentences(`${answer}\n`);
        for (const c of chunks) enqueueTts(c);
        if (rest.trim()) enqueueTts(rest);
        streamFinishedRef.current = true;
        if (!ttsPumpActiveRef.current && ttsQueueRef.current.length === 0 && stateRef.current !== TURN.SPEAKING) {
          setTurn(TURN.LISTENING);
        }
        return;
      }

      // Streaming succeeded: commit caption + mark producer done so the pump
      // transitions back to LISTENING once the last sentence finishes.
      onStreamDelta?.("");
      onTranscript?.({ speaker: "assistant", text: answer });
      streamFinishedRef.current = true;
      if (!ttsPumpActiveRef.current && ttsQueueRef.current.length === 0 && stateRef.current !== TURN.SPEAKING) {
        // Nothing ever got enqueued (e.g. empty after cleaning) — don't hang.
        const whole = cleanForTts(answer);
        if (whole) enqueueTts(whole);
        else setTurn(TURN.LISTENING);
      }
    },
    [askTeacher, streamAsk, onStreamDelta, onTranscript, enqueueTts, sessionId, setTurn, stopFiller, playFiller],
  );

  // ---- end of a user turn: STT -> respond ----------------------------------
  const handleUtterance = useCallback(
    async (blob: Blob) => {
      if (closingRef.current) return;
      setTurn(TURN.THINKING);
      onPartialTranscript?.(""); // interim caption done; final transcript follows
      try {
        const file = new File([blob], "utterance.webm", { type: blob.type || "audio/webm" });
        const sttRes = (await transcribe({ sessionId, file })) as TranscribeResult;
        const userText = String(sttRes?.transcript || "").trim();
        if (!userText) {
          setTurn(TURN.LISTENING);
          return;
        }
        onTranscript?.({ speaker: "user", text: userText });
        await respond(userText, {});
      } catch (err) {
        if (!closingRef.current) {
          // 422 = "no speech detected" — benign, keep listening quietly.
          if ((err as { status?: number })?.status === 422) {
            setTurn(TURN.LISTENING);
            return;
          }
          setError(String((err as { message?: string })?.message || err || "voice loop error"));
          setTurn(TURN.LISTENING);
        }
      }
    },
    [onTranscript, onPartialTranscript, respond, sessionId, setTurn, transcribe],
  );

  // ---- imperative quick-action ask (text prompt + chosen mode) -------------
  const ask = useCallback(
    async ({ message, mode }: { message?: string; mode?: string } = {}) => {
      if (closingRef.current) return;
      try {
        stopPlayback();
        await respond(message, { mode, echoUser: true });
      } catch (err) {
        if (!closingRef.current) {
          setError(String((err as { message?: string })?.message || err || "voice loop error"));
          setTurn(TURN.LISTENING);
        }
      }
    },
    [respond, setTurn, stopPlayback],
  );

  // ---- streaming STT: transcribe audio-so-far for a live interim caption ----
  const runPartialTranscribe = useCallback(async () => {
    if (partialBusyRef.current || closingRef.current) return;
    const parts = chunksRef.current.slice();
    if (parts.length === 0) return;
    const blob = new Blob(parts, { type: mimeRef.current });
    if (blob.size < 4000) return; // too little audio to be meaningful
    partialBusyRef.current = true;
    try {
      const file = new File([blob], "partial.webm", { type: mimeRef.current });
      const res = (await transcribe({ sessionId, file })) as TranscribeResult;
      const txt = String(res?.transcript || "").trim();
      // Only surface if we're still in the same listening utterance.
      if (txt && !closingRef.current && stateRef.current === TURN.LISTENING && inUtteranceRef.current) {
        onPartialTranscript?.(txt);
      }
    } catch {
      /* partials are best-effort */
    } finally {
      partialBusyRef.current = false;
    }
  }, [transcribe, sessionId, onPartialTranscript]);

  // ---- capture one utterance with MediaRecorder ----------------------------
  const flushUtterance = useCallback(() => {
    const recorder = recorderRef.current;
    if (recorder && recorder.state === "recording") {
      recorder.stop(); // ondataavailable -> handleUtterance
    }
  }, []);

  // ---- VAD frame loop ------------------------------------------------------
  const vadTick = useCallback(() => {
    const analyser = analyserRef.current;
    if (!analyser) return;
    const buf = new Uint8Array(analyser.fftSize);
    analyser.getByteTimeDomainData(buf);
    const energy = rms(buf);
    setLevel(Math.min(1, energy / 0.15));

    const isSpeech = energy >= SPEECH_RMS_THRESHOLD;
    const cur = stateRef.current;

    // Barge-in: only interrupt the AI when the user speaks clearly (higher
    // threshold) AND sustains it for BARGE_IN_MS. This prevents the AI's own
    // TTS bleeding into the mic, coughs, or brief noises from cutting it off.
    if (cur === TURN.SPEAKING) {
      // Soft ducking: as soon as the user starts talking, lower the AI's volume
      // (like a person trailing off). Only a sustained, clearly-louder voice
      // escalates to a full stop — a short "ừ"/"vâng" backchannel just ducks.
      const gain = ttsGainRef.current;
      if (energy >= DUCK_RMS_THRESHOLD) {
        if (gain) gain.gain.value = DUCK_GAIN;
      } else if (gain && gain.gain.value !== 1) {
        gain.gain.value = 1; // user paused -> AI returns to full voice
      }
      if (energy >= BARGE_IN_RMS_THRESHOLD) {
        bargeMsRef.current += FRAME_MS;
      } else {
        bargeMsRef.current = Math.max(0, bargeMsRef.current - FRAME_MS * 2);
      }
      if (bargeMsRef.current >= BARGE_IN_MS) {
        stopPlayback();
        inUtteranceRef.current = false;
        speechMsRef.current = 0;
        silenceMsRef.current = 0;
        utteranceMsRef.current = 0;
        bargeMsRef.current = 0;
        setTurn(TURN.LISTENING);
      }
      return;
    }
    bargeMsRef.current = 0;

    if (cur !== TURN.LISTENING) return; // only run VAD turns while listening

    if (isSpeech) {
      if (!inUtteranceRef.current) {
        inUtteranceRef.current = true;
        speechMsRef.current = 0;
        silenceMsRef.current = 0;
        utteranceMsRef.current = 0;
        lastPartialMsRef.current = 0;
        onPartialTranscript?.(""); // clear any stale interim caption
        // Start a fresh recording for this utterance (timeslice so partial
        // transcripts can be built from audio captured so far).
        try {
          chunksRef.current = [];
          const rec = recorderRef.current;
          if (rec && rec.state === "inactive") rec.start(RECORDER_TIMESLICE_MS);
        } catch {}
      }
      speechMsRef.current += FRAME_MS;
      silenceMsRef.current = 0;
      utteranceMsRef.current += FRAME_MS;
      // Streaming STT: fire a bounded interim transcribe for a live caption.
      if (
        utteranceMsRef.current >= PARTIAL_STT_FIRST_MS &&
        utteranceMsRef.current - lastPartialMsRef.current >= PARTIAL_STT_INTERVAL_MS &&
        !partialBusyRef.current
      ) {
        lastPartialMsRef.current = utteranceMsRef.current;
        runPartialTranscribe();
      }
      if (utteranceMsRef.current >= MAX_UTTERANCE_MS) {
        inUtteranceRef.current = false;
        flushUtterance();
      }
      return;
    }

    // silence
    if (inUtteranceRef.current) {
      silenceMsRef.current += FRAME_MS;
      utteranceMsRef.current += FRAME_MS;
      // Adaptive endpointing: end fast after a clearly-complete utterance, but
      // wait longer when the speaker has only said a little (likely mid-thought).
      const endSilenceNeeded =
        speechMsRef.current >= COMPLETE_SPEECH_MS ? END_SILENCE_COMPLETE_MS : END_SILENCE_HESITANT_MS;
      if (silenceMsRef.current >= endSilenceNeeded) {
        if (speechMsRef.current >= MIN_SPEECH_MS) {
          inUtteranceRef.current = false;
          flushUtterance(); // endpoint -> process turn
        } else {
          // blip: discard
          inUtteranceRef.current = false;
          speechMsRef.current = 0;
          silenceMsRef.current = 0;
          onPartialTranscript?.("");
          try {
            const rec = recorderRef.current;
            if (rec && rec.state === "recording") rec.stop();
            chunksRef.current = [];
          } catch {}
        }
      }
    }
  }, [flushUtterance, setTurn, stopPlayback, runPartialTranscribe, onPartialTranscript]);

  // ---- start / stop --------------------------------------------------------
  const start = useCallback(async () => {
    if (streamRef.current) return;
    setError("");
    closingRef.current = false;
    try {
      const constraints: MediaStreamConstraints = {
        audio:
          micDeviceId && micDeviceId !== "default"
            ? {
                deviceId: { exact: micDeviceId },
                echoCancellation: true,
                noiseSuppression: true,
                autoGainControl: true,
              }
            : {
                echoCancellation: true,
                noiseSuppression: true,
                autoGainControl: true,
              },
      };
      const stream = await navigator.mediaDevices.getUserMedia(constraints);
      streamRef.current = stream;

      const AudioCtx: typeof AudioContext =
        window.AudioContext ||
        (window as unknown as { webkitAudioContext: typeof AudioContext }).webkitAudioContext;
      const ctx = new AudioCtx();
      audioCtxRef.current = ctx;
      // Unlock the context within the user-initiated flow so later TTS playback
      // through it is not blocked by the browser autoplay policy.
      if (ctx.state === "suspended") {
        try {
          await ctx.resume();
        } catch {}
      }
      const source = ctx.createMediaStreamSource(stream);
      const analyser = ctx.createAnalyser();
      analyser.fftSize = 1024;
      source.connect(analyser);
      analyserRef.current = analyser;
      // Pre-synthesize the thinking-filler so it's instantly available later.
      primeFiller();

      const mime = MediaRecorder.isTypeSupported("audio/webm;codecs=opus")
        ? "audio/webm;codecs=opus"
        : "audio/webm";
      mimeRef.current = mime;
      const recorder = new MediaRecorder(stream, { mimeType: mime });
      recorder.ondataavailable = (e: BlobEvent) => {
        if (e.data && e.data.size > 0) chunksRef.current.push(e.data);
      };
      recorder.onstop = () => {
        const parts = chunksRef.current;
        chunksRef.current = [];
        if (parts.length === 0) return;
        const blob = new Blob(parts, { type: mime });
        // Require a minimum payload so we don't ship sub-second noise blips to
        // STT (tiny/quiet clips make the recognizer hallucinate filler text in
        // the wrong language). ~6KB of webm/opus ≈ ~0.6-0.8s of real speech.
        if (blob.size > 6000) handleUtterance(blob);
        else if (stateRef.current === TURN.LISTENING) {
          /* too small, ignore */
        }
      };
      recorderRef.current = recorder;

      setListening(true);
      setTurn(TURN.LISTENING);
      vadTimerRef.current = setInterval(vadTick, FRAME_MS);
    } catch (err) {
      setError(String((err as { message?: string })?.message || err || "Không truy cập được micro"));
      setListening(false);
      setTurn(TURN.IDLE);
    }
  }, [handleUtterance, micDeviceId, setTurn, vadTick, primeFiller]);

  const stop = useCallback(() => {
    closingRef.current = true;
    if (vadTimerRef.current) {
      clearInterval(vadTimerRef.current);
      vadTimerRef.current = null;
    }
    stopPlayback();
    try {
      const rec = recorderRef.current;
      if (rec && rec.state === "recording") rec.stop();
    } catch {}
    recorderRef.current = null;
    chunksRef.current = [];
    try {
      streamRef.current?.getTracks().forEach((t: MediaStreamTrack) => t.stop());
    } catch {}
    streamRef.current = null;
    try {
      audioCtxRef.current?.close();
    } catch {}
    audioCtxRef.current = null;
    analyserRef.current = null;
    inUtteranceRef.current = false;
    speechMsRef.current = 0;
    silenceMsRef.current = 0;
    bargeMsRef.current = 0;
    fillerBufferRef.current = null; // tied to the closing AudioContext
    setListening(false);
    setLevel(0);
    setTurn(TURN.IDLE);
  }, [setTurn, stopPlayback]);

  const interrupt = useCallback(() => {
    if (stateRef.current === TURN.SPEAKING) {
      stopPlayback();
      setTurn(TURN.LISTENING);
    }
  }, [setTurn, stopPlayback]);

  // Auto start/stop with `enabled`.
  useEffect(() => {
    if (enabled) start();
    return () => stop();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [enabled, micDeviceId]);

  return { state, listening, error, level, outputLevel, start, stop, interrupt, ask };
}
