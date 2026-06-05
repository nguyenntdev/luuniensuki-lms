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
const END_SILENCE_MS = 700; // trailing silence that ends a turn
const MIN_SPEECH_MS = 300; // ignore sub-300ms blips
const SPEECH_RMS_THRESHOLD = 0.018; // energy above this = speech
const FRAME_MS = 50; // VAD evaluation cadence
const MAX_UTTERANCE_MS = 15000; // hard cap on a single utterance

function rms(timeDomain) {
  let sum = 0;
  for (let i = 0; i < timeDomain.length; i += 1) {
    const v = (timeDomain[i] - 128) / 128;
    sum += v * v;
  }
  return Math.sqrt(sum / timeDomain.length);
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
  const ttsAudioRef = useRef(null);
  const ttsSourceRef = useRef(null); // Web Audio BufferSource (preferred playback)
  const ttsAnalyserRef = useRef(null); // analyser on the TTS output (lip-sync)
  const outRafRef = useRef(null); // rAF id for the output-amplitude loop
  const ttsAbortRef = useRef(null);
  const closingRef = useRef(false);

  const setTurn = useCallback((next) => {
    stateRef.current = next;
    setState(next);
  }, []);

  const stopPlayback = useCallback(() => {
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

  // Play TTS audio bytes. Prefer the Web Audio API through the AudioContext that
  // was unlocked by the user's "join" gesture — this bypasses the browser
  // autoplay policy that silently blocks `new Audio().play()` after the long
  // STT->LLM->TTS async gap. Falls back to an HTMLAudioElement if decoding
  // fails (e.g. Safari mp3 quirks). Returns true if playback started.
  const playTtsBuffer = useCallback(
    async (audioBlob) => {
      const ctx = audioCtxRef.current;
      // Try Web Audio playback first.
      if (ctx) {
        try {
          if (ctx.state === "suspended") {
            await ctx.resume().catch(() => {});
          }
          const arrayBuf = await audioBlob.arrayBuffer();
          const audioBuffer = await new Promise((resolve, reject) => {
            // decodeAudioData supports both promise and callback forms.
            const p = ctx.decodeAudioData(arrayBuf.slice(0), resolve, reject);
            if (p && typeof p.then === "function") p.then(resolve, reject);
          });
          if (closingRef.current || stateRef.current !== TURN.SPEAKING) return false;
          const src = ctx.createBufferSource();
          src.buffer = audioBuffer;
          // Insert an analyser between the source and the destination so we can
          // drive the avatar's mouth from the AI's actual speech amplitude.
          let analyser = null;
          try {
            analyser = ctx.createAnalyser();
            analyser.fftSize = 256;
            src.connect(analyser);
            analyser.connect(ctx.destination);
            ttsAnalyserRef.current = analyser;
            const buf = new Uint8Array(analyser.fftSize);
            const tick = () => {
              if (!ttsAnalyserRef.current) return;
              ttsAnalyserRef.current.getByteTimeDomainData(buf);
              const lvl = rms(buf);
              // Scale up; speech RMS is small. Clamp to 0..1.
              setOutputLevel(Math.min(1, lvl * 3.2));
              outRafRef.current = requestAnimationFrame(tick);
            };
            outRafRef.current = requestAnimationFrame(tick);
          } catch {
            src.connect(ctx.destination);
          }
          src.onended = () => {
            if (ttsSourceRef.current === src) ttsSourceRef.current = null;
            if (outRafRef.current) {
              try {
                cancelAnimationFrame(outRafRef.current);
              } catch {}
              outRafRef.current = null;
            }
            ttsAnalyserRef.current = null;
            setOutputLevel(0);
            if (!closingRef.current && stateRef.current === TURN.SPEAKING) {
              setTurn(TURN.LISTENING);
            }
          };
          ttsSourceRef.current = src;
          src.start(0);
          return true;
        } catch {
          // Fall through to HTMLAudio.
        }
      }

      // Fallback: HTMLAudioElement.
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
          if (!closingRef.current && stateRef.current === TURN.SPEAKING) {
            setTurn(TURN.LISTENING);
          }
        };
        audio.onerror = () => {
          if (!closingRef.current && stateRef.current === TURN.SPEAKING) setTurn(TURN.LISTENING);
        };
        await audio.play();
        return true;
      } catch {
        return false;
      }
    },
    [setTurn],
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

      // Prefer SSE streaming so the caption appears live; fall back to the
      // non-streaming ask on any transport error so the room never stalls.
      let answer = "";
      let streamed = false;
      if (typeof streamAsk === "function") {
        try {
          let acc = "";
          const result = await streamAsk({
            sessionId,
            message: text,
            mode,
            onDelta: (delta) => {
              if (closingRef.current) return;
              acc += String(delta || "");
              onStreamDelta?.(acc);
            },
          });
          answer = String(result?.answer || acc || "").trim();
          streamed = true;
        } catch {
          streamed = false;
          answer = "";
        }
      }
      if (!answer) {
        const reply = await askTeacher({ sessionId, message: text, mode });
        answer = String(reply?.text || reply?.answer || "").trim();
      }
      if (!answer) {
        onStreamDelta?.("");
        setTurn(TURN.LISTENING);
        return;
      }
      // Commit the final assistant turn to the captions feed and clear the
      // live streaming buffer (if any).
      onStreamDelta?.("");
      onTranscript?.({ speaker: "assistant", text: answer });

      setTurn(TURN.SPEAKING);
      const controller = new AbortController();
      ttsAbortRef.current = controller;
      const audioData = await synthesize({ sessionId, text: answer, signal: controller.signal });
      if (closingRef.current || stateRef.current !== TURN.SPEAKING) return;
      let audioBlob;
      if (audioData instanceof Blob) audioBlob = audioData;
      else if (audioData?.blob instanceof Blob) audioBlob = audioData.blob;
      else if (audioData instanceof ArrayBuffer) audioBlob = new Blob([audioData], { type: "audio/mpeg" });
      else if (audioData?.arrayBuffer || ArrayBuffer.isView(audioData)) audioBlob = new Blob([audioData], { type: "audio/mpeg" });
      else {
        setTurn(TURN.LISTENING);
        return;
      }
      if (!audioBlob || audioBlob.size === 0) {
        setTurn(TURN.LISTENING);
        return;
      }
      const started = await playTtsBuffer(audioBlob);
      if (!started && !closingRef.current) setTurn(TURN.LISTENING);
    },
    [askTeacher, streamAsk, onStreamDelta, onTranscript, playTtsBuffer, sessionId, setTurn, synthesize],
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

    // Barge-in: speaking + user speech -> stop AI, go listen.
    if (cur === TURN.SPEAKING && isSpeech) {
      stopPlayback();
      inUtteranceRef.current = false;
      speechMsRef.current = 0;
      silenceMsRef.current = 0;
      utteranceMsRef.current = 0;
      setTurn(TURN.LISTENING);
      return;
    }

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
        // Require a minimum payload so we don't ship sub-300ms noise blips to
        // STT (tiny/quiet clips make the recognizer hallucinate filler text in
        // the wrong language). ~2.5KB of webm/opus ≈ a few hundred ms of speech.
        if (blob.size > 2500) handleUtterance(blob);
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
