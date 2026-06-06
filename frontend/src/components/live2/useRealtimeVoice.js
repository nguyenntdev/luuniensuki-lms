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

// VAD tuning (mirror backend live_vad defaults).
const END_SILENCE_MS = 900; // trailing silence that ends a turn (give the speaker room)
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

function rms(timeDomain) {
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
function cleanForTts(value) {
  return String(value || "")
    .replace(/\[[A-Za-z]{0,2}\d+\]/g, " ") // [S1] [R2]
    .replace(/[*_`#>]/g, " ") // markdown emphasis / headings / quotes
    .replace(/^\s*[-•]\s+/gm, " ") // bullet markers
    .replace(/\s+/g, " ")
    .trim();
}

// Pull complete sentences out of a growing buffer. Returns the speakable
// chunks plus the unconsumed remainder (kept until more text arrives).
function takeSentences(buf) {
  const chunks = [];
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
  onStreamDelta, // (fullText) => void  (live partial AI text while streaming)
  transcribe, // async ({ sessionId, file }) => { transcript }
  askTeacher, // async ({ sessionId, message }) => { text, ... }
  streamAsk, // optional async ({ sessionId, message, mode, onDelta }) => { answer }
  synthesize, // async ({ sessionId, text, signal }) => Blob | ArrayBuffer
}) {
  const [state, setState] = useState(TURN.IDLE);
  const [listening, setListening] = useState(false);
  const [error, setError] = useState("");
  const [level, setLevel] = useState(0); // 0..1 mic energy, for the UI meter
  const [outputLevel, setOutputLevel] = useState(0); // 0..1 AI speech amplitude (lip-sync)

  const stateRef = useRef(TURN.IDLE);
  const streamRef = useRef(null);
  const audioCtxRef = useRef(null);
  const analyserRef = useRef(null);
  const recorderRef = useRef(null);
  const chunksRef = useRef([]);
  const vadTimerRef = useRef(null);
  const speechMsRef = useRef(0);
  const silenceMsRef = useRef(0);
  const inUtteranceRef = useRef(false);
  const utteranceMsRef = useRef(0);
  const bargeMsRef = useRef(0); // sustained loud-speech accumulator for barge-in
  const ttsAudioRef = useRef(null);
  const ttsSourceRef = useRef(null); // Web Audio BufferSource (preferred playback)
  const ttsAnalyserRef = useRef(null); // analyser on the TTS output (lip-sync)
  const outRafRef = useRef(null); // rAF id for the output-amplitude loop
  const ttsAbortRef = useRef(null);
  const closingRef = useRef(false);
  // Sentence-streaming TTS queue.
  const ttsQueueRef = useRef([]); // pending sentence strings to synthesize
  const ttsPumpActiveRef = useRef(false); // is the synth/play pump running
  const streamFinishedRef = useRef(false); // producer finished enqueuing
  const clipResolveRef = useRef(null); // resolve() of the in-flight clip's end promise
  const turnSeqRef = useRef(0); // monotonic id; invalidates a turn's producer on interrupt

  const setTurn = useCallback((next) => {
    stateRef.current = next;
    setState(next);
  }, []);

  const stopPlayback = useCallback(() => {
    // Invalidate the current speaking turn so a still-arriving SSE stream stops
    // enqueueing sentences, and drop any queued/streaming sentences.
    turnSeqRef.current += 1;
    ttsQueueRef.current = [];
    streamFinishedRef.current = true;
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
    async (audioBlob) => {
      if (!audioBlob || audioBlob.size === 0) return false;
      const ctx = audioCtxRef.current;
      if (ctx) {
        try {
          if (ctx.state === "suspended") await ctx.resume().catch(() => {});
          const arrayBuf = await audioBlob.arrayBuffer();
          const audioBuffer = await new Promise((resolve, reject) => {
            const p = ctx.decodeAudioData(arrayBuf.slice(0), resolve, reject);
            if (p && typeof p.then === "function") p.then(resolve, reject);
          });
          if (closingRef.current || stateRef.current !== TURN.SPEAKING) return false;
          return await new Promise((resolve) => {
            let done = false;
            const finish = (ok) => {
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
              src.connect(analyser);
              analyser.connect(ctx.destination);
              ttsAnalyserRef.current = analyser;
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
      return await new Promise((resolve) => {
        let done = false;
        const finish = (ok) => {
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
    async (text, signal) => {
      const audioData = await synthesize({ sessionId, text, signal });
      if (audioData instanceof Blob) return audioData;
      if (audioData?.blob instanceof Blob) return audioData.blob;
      if (audioData instanceof ArrayBuffer) return new Blob([audioData], { type: "audio/mpeg" });
      if (audioData?.arrayBuffer || ArrayBuffer.isView(audioData)) return new Blob([audioData], { type: "audio/mpeg" });
      return null;
    },
    [sessionId, synthesize],
  );

  // Single consumer: drains the sentence queue, synthesizing + playing each
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
    (sentence) => {
      const s = String(sentence || "").trim();
      if (!s) return;
      ttsQueueRef.current.push(s);
      if (stateRef.current !== TURN.SPEAKING) setTurn(TURN.SPEAKING);
      if (!ttsPumpActiveRef.current) pumpTtsQueue();
    },
    [pumpTtsQueue, setTurn],
  );

  // ---- speak an AI reply for a given user text (shared by voice + quick-actions)
  const respond = useCallback(
    async (userText, { mode, echoUser = false } = {}) => {
      if (closingRef.current) return;
      const text = String(userText || "").trim();
      if (!text) {
        setTurn(TURN.LISTENING);
        return;
      }
      setTurn(TURN.THINKING);
      if (echoUser) onTranscript?.({ speaker: "user", text });

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
            onDelta: (delta) => {
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
          answer = String(result?.answer || acc || "").trim();
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
          answer = String(reply?.text || reply?.answer || "").trim();
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
    [askTeacher, streamAsk, onStreamDelta, onTranscript, enqueueTts, sessionId, setTurn],
  );

  // ---- end of a user turn: STT -> respond ----------------------------------
  const handleUtterance = useCallback(
    async (blob) => {
      if (closingRef.current) return;
      setTurn(TURN.THINKING);
      try {
        const file = new File([blob], "utterance.webm", { type: blob.type || "audio/webm" });
        const sttRes = await transcribe({ sessionId, file });
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
          if (err?.status === 422) {
            setTurn(TURN.LISTENING);
            return;
          }
          setError(String(err?.message || err || "voice loop error"));
          setTurn(TURN.LISTENING);
        }
      }
    },
    [onTranscript, respond, sessionId, setTurn, transcribe],
  );

  // ---- imperative quick-action ask (text prompt + chosen mode) -------------
  const ask = useCallback(
    async ({ message, mode } = {}) => {
      if (closingRef.current) return;
      try {
        stopPlayback();
        await respond(message, { mode, echoUser: true });
      } catch (err) {
        if (!closingRef.current) {
          setError(String(err?.message || err || "voice loop error"));
          setTurn(TURN.LISTENING);
        }
      }
    },
    [respond, setTurn, stopPlayback],
  );

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
        // Start a fresh recording for this utterance.
        try {
          chunksRef.current = [];
          const rec = recorderRef.current;
          if (rec && rec.state === "inactive") rec.start();
        } catch {}
      }
      speechMsRef.current += FRAME_MS;
      silenceMsRef.current = 0;
      utteranceMsRef.current += FRAME_MS;
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
      if (silenceMsRef.current >= END_SILENCE_MS) {
        if (speechMsRef.current >= MIN_SPEECH_MS) {
          inUtteranceRef.current = false;
          flushUtterance(); // endpoint -> process turn
        } else {
          // blip: discard
          inUtteranceRef.current = false;
          speechMsRef.current = 0;
          silenceMsRef.current = 0;
          try {
            const rec = recorderRef.current;
            if (rec && rec.state === "recording") rec.stop();
            chunksRef.current = [];
          } catch {}
        }
      }
    }
  }, [flushUtterance, setTurn, stopPlayback]);

  // ---- start / stop --------------------------------------------------------
  const start = useCallback(async () => {
    if (streamRef.current) return;
    setError("");
    closingRef.current = false;
    try {
      const constraints = {
        audio: micDeviceId && micDeviceId !== "default" ? { deviceId: { exact: micDeviceId } } : true,
      };
      const stream = await navigator.mediaDevices.getUserMedia(constraints);
      streamRef.current = stream;

      const AudioCtx = window.AudioContext || window.webkitAudioContext;
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

      const mime = MediaRecorder.isTypeSupported("audio/webm;codecs=opus")
        ? "audio/webm;codecs=opus"
        : "audio/webm";
      const recorder = new MediaRecorder(stream, { mimeType: mime });
      recorder.ondataavailable = (e) => {
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
      setError(String(err?.message || err || "Không truy cập được micro"));
      setListening(false);
      setTurn(TURN.IDLE);
    }
  }, [handleUtterance, micDeviceId, setTurn, vadTick]);

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
      streamRef.current?.getTracks().forEach((t) => t.stop());
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
