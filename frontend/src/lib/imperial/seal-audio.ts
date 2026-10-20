/**
 * Web Audio API Synthetic Royal Seal Sound Generator.
 * SPEC ID: STTT-SPEC-AUDIO-PASSPORT-002 (§3.1)
 *
 * Implements an authentic physical wooden/stone stamp thud sound using
 * dynamic low-pass filtered noise, sub-bass thump, and parchment paper slap.
 *
 * 100% offline, pure Web Audio API, requires 0 external audio file downloads.
 * Safe for SSR (no-ops when AudioContext is unavailable in node/headless environment).
 */

let sharedAudioContext: AudioContext | null = null;

/**
 * Lazily gets or initializes a cross-browser AudioContext.
 * Respects user gesture resume requirements.
 */
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
      // AudioContext cannot be resumed without user interaction; ignore silently
    });
  }

  return sharedAudioContext;
}

export interface SealAudioOptions {
  /** Master volume multiplier between 0.0 and 1.0 (default: 0.85) */
  volume?: number;
  /** Seal material resonance: heavier wood, stone, imperial jade, or solid gold (default: "wood") */
  material?: "wood" | "stone" | "jade" | "gold";
  /** Surface slap strength (default: 1.0) */
  surfaceIntensity?: number;
}

/**
 * Plays an authentic royal seal stamp sound effect with sub-bass impact,
 * filtered wood resonant body, and surface friction slap.
 */
export async function playRoyalSealSound(options: SealAudioOptions = {}): Promise<boolean> {
  const ctx = getAudioContext();
  if (!ctx) return false;

  try {
    const now = ctx.currentTime;
    const masterGain = ctx.createGain();
    const volume = Math.max(0, Math.min(1, options.volume ?? 0.85));
    masterGain.gain.setValueAtTime(volume, now);
    masterGain.connect(ctx.destination);

    const material = options.material ?? "wood";

    // -----------------------------------------------------------------------
    // LAYER 1: Low-frequency wooden/stone body impulse (Sub-thump oscillator)
    // -----------------------------------------------------------------------
    const thumpOsc = ctx.createOscillator();
    const thumpGain = ctx.createGain();

    const startFreq =
      material === "gold"
        ? 210
        : material === "stone"
          ? 160
          : material === "jade"
            ? 180
            : 130;
    const endFreq =
      material === "gold"
        ? 52
        : material === "stone"
          ? 35
          : material === "jade"
            ? 45
            : 30;
    const decayDuration =
      material === "gold"
        ? 0.28
        : material === "stone"
          ? 0.16
          : 0.22;

    thumpOsc.type = "sine";
    thumpOsc.frequency.setValueAtTime(startFreq, now);
    thumpOsc.frequency.exponentialRampToValueAtTime(endFreq, now + decayDuration);

    thumpGain.gain.setValueAtTime(0.001, now);
    thumpGain.gain.linearRampToValueAtTime(material === "gold" ? 0.95 : 0.9, now + 0.004);
    thumpGain.gain.exponentialRampToValueAtTime(0.001, now + decayDuration);

    thumpOsc.connect(thumpGain);
    thumpGain.connect(masterGain);

    thumpOsc.start(now);
    thumpOsc.stop(now + decayDuration + 0.05);

    // -----------------------------------------------------------------------
    // LAYER 2: Filtered friction noise (Parchment / do paper contact slap)
    // -----------------------------------------------------------------------
    const bufferSize = Math.floor(ctx.sampleRate * 0.15);
    const noiseBuffer = ctx.createBuffer(1, bufferSize, ctx.sampleRate);
    const output = noiseBuffer.getChannelData(0);
    for (let i = 0; i < bufferSize; i++) {
      // Pink-ish white noise decay
      output[i] = (Math.random() * 2 - 1) * Math.exp(-i / (ctx.sampleRate * 0.04));
    }

    const noiseSource = ctx.createBufferSource();
    noiseSource.buffer = noiseBuffer;

    const noiseFilter = ctx.createBiquadFilter();
    noiseFilter.type = "bandpass";
    noiseFilter.frequency.setValueAtTime(
      material === "gold" ? 2200 : material === "stone" ? 1200 : 750,
      now,
    );
    noiseFilter.Q.setValueAtTime(material === "gold" ? 3.0 : 1.8, now);

    const noiseGain = ctx.createGain();
    const surfaceIntensity = Math.max(0.1, options.surfaceIntensity ?? 1.0);
    noiseGain.gain.setValueAtTime(0.4 * surfaceIntensity, now);
    noiseGain.gain.exponentialRampToValueAtTime(0.001, now + 0.08);

    noiseSource.connect(noiseFilter);
    noiseFilter.connect(noiseGain);
    noiseGain.connect(masterGain);

    noiseSource.start(now);
    noiseSource.stop(now + 0.1);

    // -----------------------------------------------------------------------
    // LAYER 3: Secondary subtle resonant bounce / mechanical tap
    // -----------------------------------------------------------------------
    const tapOsc = ctx.createOscillator();
    const tapGain = ctx.createGain();
    tapOsc.type = material === "gold" ? "sine" : "triangle";
    tapOsc.frequency.setValueAtTime(
      material === "gold" ? 587.33 : material === "stone" ? 420 : 280, // D5 chime for gold
      now + 0.012,
    );
    tapOsc.frequency.exponentialRampToValueAtTime(
      material === "gold" ? 146.83 : 60,
      now + (material === "gold" ? 0.18 : 0.09),
    );

    tapGain.gain.setValueAtTime(0.001, now);
    tapGain.gain.setValueAtTime(material === "gold" ? 0.35 : 0.25, now + 0.014);
    tapGain.gain.exponentialRampToValueAtTime(0.001, now + (material === "gold" ? 0.18 : 0.09));

    tapOsc.connect(tapGain);
    tapGain.connect(masterGain);

    tapOsc.start(now + 0.012);
    tapOsc.stop(now + (material === "gold" ? 0.2 : 0.1));

    return true;
  } catch {
    // Non-blocking fail-safe: Audio is a progressive enhancement
    return false;
  }
}

/**
 * Backward compatibility alias for playRoyalSealSound
 */
export const playStampSound = playRoyalSealSound;

/**
 * Synthesizes a celebratory royal gong chime when unlocking a milestone or major seal.
 */
export async function playRoyalGongChime(): Promise<boolean> {
  const ctx = getAudioContext();
  if (!ctx) return false;

  try {
    const now = ctx.currentTime;
    const gongOsc = ctx.createOscillator();
    const gongGain = ctx.createGain();

    gongOsc.type = "sine";
    gongOsc.frequency.setValueAtTime(329.63, now); // E4
    gongOsc.frequency.exponentialRampToValueAtTime(326.0, now + 1.2);

    gongGain.gain.setValueAtTime(0.001, now);
    gongGain.gain.linearRampToValueAtTime(0.4, now + 0.02);
    gongGain.gain.exponentialRampToValueAtTime(0.0001, now + 1.4);

    gongOsc.connect(gongGain);
    gongGain.connect(ctx.destination);

    gongOsc.start(now);
    gongOsc.stop(now + 1.5);
    return true;
  } catch {
    return false;
  }
}

/**
 * Celebratory composite audio cue for stamping unique completed zone seals (Kim Bảo / Ngự Tỷ).
 * Combines heavy metal/jade seal impact with royal ancestral court gong chime resonance.
 */
export async function playZoneCompletionSound(
  motif: "kim_bao" | "ngu_ty" = "kim_bao",
): Promise<boolean> {
  const sealPlayed = await playRoyalSealSound({
    volume: 0.95,
    material: motif === "kim_bao" ? "gold" : "jade",
    surfaceIntensity: 1.3,
  });

  // Sound celebratory gong chime shortly after impact
  setTimeout(() => {
    playRoyalGongChime().catch(() => {});
  }, 160);

  return sealPlayed;
}

export interface ThienMuBellOptions {
  volume?: number;
  duration?: number;
}

export interface NhaNhacChimeOptions {
  volume?: number;
  pitchNote?: number; // 0: D4, 1: E4, 2: G4, 3: A4, 4: B4, 5: D5
  chimeType?: "bronze_bell" | "stone_chime" | "court_gong";
}

/**
 * Synthesizes the sacred Great Bell of Thien Mu Pagoda (Đại Hồng Chung chùa Thiên Mụ, 1710).
 * Features a deep fundamental (A2 ~110Hz), harmonic partials, beating acoustic resonance,
 * and warm lingering reverberation echoing along the Perfume River (Sông Hương).
 */
export async function playThienMuBellSound(options: ThienMuBellOptions = {}): Promise<boolean> {
  const ctx = getAudioContext();
  if (!ctx) return false;

  try {
    const now = ctx.currentTime;
    const volume = Math.max(0, Math.min(1, options.volume ?? 0.8));
    const totalDuration = options.duration ?? 4.5;

    const masterGain = ctx.createGain();
    masterGain.gain.setValueAtTime(volume, now);
    masterGain.connect(ctx.destination);

    // Fundamental & beating partial pair (110 Hz and 111.4 Hz creating acoustic beating)
    const bellFrequencies = [
      { freq: 110.0, gain: 0.7, decay: totalDuration },
      { freq: 111.4, gain: 0.5, decay: totalDuration * 0.9 },
      { freq: 220.0, gain: 0.45, decay: totalDuration * 0.8 },
      { freq: 330.0, gain: 0.35, decay: totalDuration * 0.65 },
      { freq: 445.0, gain: 0.25, decay: totalDuration * 0.5 },
      { freq: 550.0, gain: 0.18, decay: totalDuration * 0.4 },
      { freq: 880.0, gain: 0.12, decay: totalDuration * 0.25 },
    ];

    bellFrequencies.forEach(({ freq, gain: partGain, decay }) => {
      const osc = ctx.createOscillator();
      const g = ctx.createGain();
      osc.type = "sine";
      osc.frequency.setValueAtTime(freq, now);

      g.gain.setValueAtTime(0.001, now);
      g.gain.linearRampToValueAtTime(partGain, now + 0.03);
      g.gain.exponentialRampToValueAtTime(0.0001, now + decay);

      osc.connect(g);
      g.connect(masterGain);

      osc.start(now);
      osc.stop(now + decay + 0.05);
    });

    // Mallet strike impulse (wood mallet on heavy bronze)
    const strikeBufferSize = Math.floor(ctx.sampleRate * 0.08);
    const strikeBuffer = ctx.createBuffer(1, strikeBufferSize, ctx.sampleRate);
    const strikeData = strikeBuffer.getChannelData(0);
    for (let i = 0; i < strikeBufferSize; i++) {
      strikeData[i] = (Math.random() * 2 - 1) * Math.exp(-i / (ctx.sampleRate * 0.015));
    }
    const strikeSource = ctx.createBufferSource();
    strikeSource.buffer = strikeBuffer;

    const strikeFilter = ctx.createBiquadFilter();
    strikeFilter.type = "lowpass";
    strikeFilter.frequency.setValueAtTime(380, now);

    const strikeGain = ctx.createGain();
    strikeGain.gain.setValueAtTime(0.35, now);
    strikeGain.gain.exponentialRampToValueAtTime(0.001, now + 0.08);

    strikeSource.connect(strikeFilter);
    strikeFilter.connect(strikeGain);
    strikeGain.connect(masterGain);

    strikeSource.start(now);
    strikeSource.stop(now + 0.09);

    return true;
  } catch {
    return false;
  }
}

/**
 * Synthesizes authentic Hue Imperial Court Music (Nhã Nhạc Cung Đình) chimes and stone lithophones.
 * Uses traditional pentatonic scale (Điệu Nam / Điệu Bắc: Hò, Xự, Xang, Xê, Cống).
 */
export async function playNhaNhacChime(options: NhaNhacChimeOptions = {}): Promise<boolean> {
  const ctx = getAudioContext();
  if (!ctx) return false;

  try {
    const now = ctx.currentTime;
    const volume = Math.max(0, Math.min(1, options.volume ?? 0.7));
    const chimeType = options.chimeType ?? "bronze_bell";

    // Traditional pentatonic scale (D4, E4, G4, A4, B4, D5)
    const pentatonicFrequencies = [293.66, 329.63, 392.0, 440.0, 493.88, 587.33];
    const baseFreq =
      options.pitchNote !== undefined
        ? pentatonicFrequencies[options.pitchNote % pentatonicFrequencies.length] || 392.0
        : pentatonicFrequencies[2]; // Default G4 (Xang)

    const masterGain = ctx.createGain();
    masterGain.gain.setValueAtTime(volume, now);
    masterGain.connect(ctx.destination);

    // Primary bell/chime tone
    const osc1 = ctx.createOscillator();
    const gain1 = ctx.createGain();
    osc1.type = chimeType === "stone_chime" ? "triangle" : "sine";
    osc1.frequency.setValueAtTime(baseFreq, now);

    gain1.gain.setValueAtTime(0.001, now);
    gain1.gain.linearRampToValueAtTime(0.6, now + 0.015);
    gain1.gain.exponentialRampToValueAtTime(0.0001, now + 2.2);

    osc1.connect(gain1);
    gain1.connect(masterGain);
    osc1.start(now);
    osc1.stop(now + 2.3);

    // Shimmering overtone partial (Biên Chung / Biên Khánh resonance)
    const osc2 = ctx.createOscillator();
    const gain2 = ctx.createGain();
    osc2.type = "sine";
    osc2.frequency.setValueAtTime(baseFreq * 2.76, now);

    gain2.gain.setValueAtTime(0.001, now);
    gain2.gain.linearRampToValueAtTime(0.25, now + 0.01);
    gain2.gain.exponentialRampToValueAtTime(0.0001, now + 1.4);

    osc2.connect(gain2);
    gain2.connect(masterGain);
    osc2.start(now);
    osc2.stop(now + 1.5);

    return true;
  } catch {
    return false;
  }
}
