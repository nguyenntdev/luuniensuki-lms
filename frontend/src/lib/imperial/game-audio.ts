/**
 * Web Audio API Synthetic Sound Engine for Imperial Heritage Games.
 * Provides authentic, lightweight audio-visual feedback:
 * - Success chime (correct answer / clue solved)
 * - Gentle error tone (supportive retry cue)
 * - Hint reveal bell
 * - Tactile wooden click (button / tile interactions)
 * - Victory celebration fanfare (round completion)
 *
 * 100% offline, zero asset downloads, SSR-safe.
 */

let sharedAudioContext: AudioContext | null = null;

function getAudioContext(): AudioContext | null {
  if (typeof window === "undefined") {
    return null;
  }

  const AudioCtx =
    window.AudioContext ||
    // @ts-expect-error - WebKit prefix support for legacy Safari
    window.webkitAudioContext;

  if (!AudioCtx) {
    return null;
  }

  if (!sharedAudioContext || sharedAudioContext.state === "closed") {
    try {
      sharedAudioContext = new AudioCtx();
    } catch {
      return null;
    }
  }

  if (sharedAudioContext.state === "suspended") {
    sharedAudioContext.resume().catch(() => {
      // AudioContext resumed on next interaction
    });
  }

  return sharedAudioContext;
}

/**
 * Plays a bright, pleasant ascending pentatonic chime for correct responses.
 */
export async function playGameSuccessSound(): Promise<boolean> {
  const ctx = getAudioContext();
  if (!ctx) return false;

  try {
    const now = ctx.currentTime;
    const notes = [523.25, 659.25, 783.99, 1046.5]; // C5, E5, G5, C6
    const masterGain = ctx.createGain();
    masterGain.gain.setValueAtTime(0.3, now);
    masterGain.connect(ctx.destination);

    notes.forEach((freq, idx) => {
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();
      const noteStart = now + idx * 0.08;
      const noteDuration = 0.35;

      osc.type = "sine";
      osc.frequency.setValueAtTime(freq, noteStart);

      gain.gain.setValueAtTime(0.001, noteStart);
      gain.gain.linearRampToValueAtTime(0.25, noteStart + 0.02);
      gain.gain.exponentialRampToValueAtTime(0.001, noteStart + noteDuration);

      osc.connect(gain);
      gain.connect(masterGain);

      osc.start(noteStart);
      osc.stop(noteStart + noteDuration + 0.05);
    });

    return true;
  } catch {
    return false;
  }
}

/**
 * Plays a gentle, warm wooden double-tap low tone for incorrect attempts.
 * Avoids harsh jarring buzzers to encourage educational resilience.
 */
export async function playGameErrorSound(): Promise<boolean> {
  const ctx = getAudioContext();
  if (!ctx) return false;

  try {
    const now = ctx.currentTime;
    const masterGain = ctx.createGain();
    masterGain.gain.setValueAtTime(0.25, now);
    masterGain.connect(ctx.destination);

    const osc = ctx.createOscillator();
    const gain = ctx.createGain();
    const filter = ctx.createBiquadFilter();

    osc.type = "triangle";
    osc.frequency.setValueAtTime(180, now);
    osc.frequency.exponentialRampToValueAtTime(110, now + 0.18);

    filter.type = "lowpass";
    filter.frequency.setValueAtTime(350, now);

    gain.gain.setValueAtTime(0.001, now);
    gain.gain.linearRampToValueAtTime(0.35, now + 0.015);
    gain.gain.exponentialRampToValueAtTime(0.001, now + 0.22);

    osc.connect(filter);
    filter.connect(gain);
    gain.connect(masterGain);

    osc.start(now);
    osc.stop(now + 0.25);

    return true;
  } catch {
    return false;
  }
}

/**
 * Plays a delicate crystal bell shimmer when revealing progressive hints.
 */
export async function playGameHintSound(): Promise<boolean> {
  const ctx = getAudioContext();
  if (!ctx) return false;

  try {
    const now = ctx.currentTime;
    const osc = ctx.createOscillator();
    const gain = ctx.createGain();

    osc.type = "sine";
    osc.frequency.setValueAtTime(880, now); // A5
    osc.frequency.exponentialRampToValueAtTime(1318.51, now + 0.15); // E6

    gain.gain.setValueAtTime(0.001, now);
    gain.gain.linearRampToValueAtTime(0.2, now + 0.02);
    gain.gain.exponentialRampToValueAtTime(0.001, now + 0.35);

    osc.connect(gain);
    gain.connect(ctx.destination);

    osc.start(now);
    osc.stop(now + 0.4);
    return true;
  } catch {
    return false;
  }
}

/**
 * Plays a short, crisp wooden click when tapping options or reordering cards.
 */
export async function playGameClickSound(): Promise<boolean> {
  const ctx = getAudioContext();
  if (!ctx) return false;

  try {
    const now = ctx.currentTime;
    const osc = ctx.createOscillator();
    const gain = ctx.createGain();

    osc.type = "triangle";
    osc.frequency.setValueAtTime(360, now);
    osc.frequency.exponentialRampToValueAtTime(80, now + 0.035);

    gain.gain.setValueAtTime(0.001, now);
    gain.gain.linearRampToValueAtTime(0.25, now + 0.004);
    gain.gain.exponentialRampToValueAtTime(0.001, now + 0.035);

    osc.connect(gain);
    gain.connect(ctx.destination);

    osc.start(now);
    osc.stop(now + 0.04);
    return true;
  } catch {
    return false;
  }
}

/**
 * Plays a regal victory fanfare with gong resonance on game completion.
 */
export async function playGameVictorySound(): Promise<boolean> {
  const ctx = getAudioContext();
  if (!ctx) return false;

  try {
    const now = ctx.currentTime;
    // Layer 1: Royal Gong resonance
    const gongOsc = ctx.createOscillator();
    const gongGain = ctx.createGain();
    gongOsc.type = "sine";
    gongOsc.frequency.setValueAtTime(329.63, now); // E4
    gongOsc.frequency.exponentialRampToValueAtTime(325.0, now + 1.2);
    gongGain.gain.setValueAtTime(0.001, now);
    gongGain.gain.linearRampToValueAtTime(0.4, now + 0.02);
    gongGain.gain.exponentialRampToValueAtTime(0.0001, now + 1.4);
    gongOsc.connect(gongGain);
    gongGain.connect(ctx.destination);
    gongOsc.start(now);
    gongOsc.stop(now + 1.5);

    // Layer 2: Celebratory Arpeggio
    const fanfareNotes = [392.0, 523.25, 659.25, 783.99, 1046.5];
    fanfareNotes.forEach((freq, idx) => {
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();
      const noteStart = now + 0.15 + idx * 0.1;
      const noteDuration = 0.4;

      osc.type = "triangle";
      osc.frequency.setValueAtTime(freq, noteStart);

      gain.gain.setValueAtTime(0.001, noteStart);
      gain.gain.linearRampToValueAtTime(0.2, noteStart + 0.02);
      gain.gain.exponentialRampToValueAtTime(0.001, noteStart + noteDuration);

      osc.connect(gain);
      gain.connect(ctx.destination);

      osc.start(noteStart);
      osc.stop(noteStart + noteDuration + 0.05);
    });

    return true;
  } catch {
    return false;
  }
}
