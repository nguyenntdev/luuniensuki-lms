import { describe, it, expect, vi, beforeEach } from "vitest";
import {
  playRoyalSealSound,
  playRoyalGongChime,
  playThienMuBellSound,
  playNhaNhacChime,
  playZoneCompletionSound,
} from "./seal-audio";

describe("Web Audio API Synthetic Seal Engine (seal-audio.ts)", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it("handles SSR / node environment gracefully without throwing", async () => {
    // In node environment without window, should return false safely
    const played = await playRoyalSealSound();
    expect(played).toBe(false);

    const chimePlayed = await playRoyalGongChime();
    expect(chimePlayed).toBe(false);

    const bellPlayed = await playThienMuBellSound();
    expect(bellPlayed).toBe(false);

    const nhaNhacPlayed = await playNhaNhacChime();
    expect(nhaNhacPlayed).toBe(false);

    const zoneSoundPlayed = await playZoneCompletionSound("kim_bao");
    expect(zoneSoundPlayed).toBe(false);
  });

  it("successfully triggers Web Audio nodes when window.AudioContext is present", async () => {
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

    const mockBufferSource = {
      buffer: null,
      connect: vi.fn(),
      start: vi.fn(),
      stop: vi.fn(),
    };

    const mockBiquadFilter = {
      type: "bandpass",
      frequency: {
        setValueAtTime: vi.fn(),
      },
      Q: {
        setValueAtTime: vi.fn(),
      },
      connect: vi.fn(),
    };

    const mockBuffer = {
      getChannelData: vi.fn().mockReturnValue(new Float32Array(1000)),
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

      createBufferSource() {
        return { ...mockBufferSource };
      }

      createBiquadFilter() {
        return { ...mockBiquadFilter, frequency: { ...mockBiquadFilter.frequency }, Q: { ...mockBiquadFilter.Q } };
      }

      createBuffer() {
        return mockBuffer;
      }

      resume = vi.fn().mockResolvedValue(undefined);
    }

    // Mock window and AudioContext
    globalThis.window = {
      AudioContext: MockAudioContext as any,
    } as any;

    const played = await playRoyalSealSound({
      volume: 0.9,
      material: "stone",
      surfaceIntensity: 1.2,
    });
    expect(played).toBe(true);

    // Test gold material (Kim Bảo)
    const playedGold = await playRoyalSealSound({
      volume: 0.95,
      material: "gold",
      surfaceIntensity: 1.3,
    });
    expect(playedGold).toBe(true);

    // Test jade material (Ngự Tỷ)
    const playedJade = await playRoyalSealSound({
      volume: 0.85,
      material: "jade",
      surfaceIntensity: 1.1,
    });
    expect(playedJade).toBe(true);

    const chimePlayed = await playRoyalGongChime();
    expect(chimePlayed).toBe(true);

    // Test composite zone completion sound (Kim Bảo / Ngự Tỷ)
    const zoneKimBaoPlayed = await playZoneCompletionSound("kim_bao");
    expect(zoneKimBaoPlayed).toBe(true);

    const zoneNguTyPlayed = await playZoneCompletionSound("ngu_ty");
    expect(zoneNguTyPlayed).toBe(true);

    const bellPlayed = await playThienMuBellSound({ volume: 0.8, duration: 3.0 });
    expect(bellPlayed).toBe(true);

    const nhaNhacPlayed = await playNhaNhacChime({ volume: 0.7, pitchNote: 2 });
    expect(nhaNhacPlayed).toBe(true);
  });
});
