import { describe, it, expect, vi, beforeEach } from "vitest";
import {
  playGameSuccessSound,
  playGameErrorSound,
  playGameHintSound,
  playGameClickSound,
  playGameVictorySound,
} from "./game-audio";

describe("Web Audio API Synthetic Game Audio Suite (game-audio.ts)", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it("handles SSR / node environment gracefully without throwing", async () => {
    const successResult = await playGameSuccessSound();
    expect(successResult).toBe(false);

    const errorResult = await playGameErrorSound();
    expect(errorResult).toBe(false);

    const hintResult = await playGameHintSound();
    expect(hintResult).toBe(false);

    const clickResult = await playGameClickSound();
    expect(clickResult).toBe(false);

    const victoryResult = await playGameVictorySound();
    expect(victoryResult).toBe(false);
  });

  it("triggers synthesized nodes when window.AudioContext is available", async () => {
    const mockOscillator = {
      type: "sine",
      frequency: {
        setValueAtTime: vi.fn(),
        exponentialRampToValueAtTime: vi.fn(),
      },
      connect: vi.fn(),
      start: vi.fn(),
      stop: vi.fn(),
    };

    const mockGain = {
      gain: {
        setValueAtTime: vi.fn(),
        linearRampToValueAtTime: vi.fn(),
        exponentialRampToValueAtTime: vi.fn(),
      },
      connect: vi.fn(),
    };

    const mockFilter = {
      type: "lowpass",
      frequency: {
        setValueAtTime: vi.fn(),
      },
      connect: vi.fn(),
    };

    class MockAudioContext {
      currentTime = 0;
      sampleRate = 44100;
      state = "running";
      destination = {};

      createOscillator() {
        return { ...mockOscillator, frequency: { ...mockOscillator.frequency } };
      }

      createGain() {
        return { ...mockGain, gain: { ...mockGain.gain } };
      }

      createBiquadFilter() {
        return { ...mockFilter, frequency: { ...mockFilter.frequency } };
      }

      resume = vi.fn().mockResolvedValue(undefined);
    }

    // Mock window and AudioContext
    (globalThis as unknown as { window: unknown }).window = {
      AudioContext: MockAudioContext,
    };

    const playedSuccess = await playGameSuccessSound();
    expect(playedSuccess).toBe(true);

    const playedError = await playGameErrorSound();
    expect(playedError).toBe(true);

    const playedHint = await playGameHintSound();
    expect(playedHint).toBe(true);

    const playedClick = await playGameClickSound();
    expect(playedClick).toBe(true);

    const playedVictory = await playGameVictorySound();
    expect(playedVictory).toBe(true);
  });
});
