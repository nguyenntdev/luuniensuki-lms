import { describe, it, expect } from "vitest";
import {
  fetchAllAudioGuides,
  fetchSiteAudioGuide,
  hasSiteAudioGuide,
  formatAudioTime,
  findActiveCue,
} from "./audio-api";
import type { TimedTranscriptCue } from "./audio-types";

describe("Heritage Audio Guide System (STTT-SPEC-AUDIO-PASSPORT-002)", () => {
  it("fetchAllAudioGuides loads available monument tracks", async () => {
    const tracks = await fetchAllAudioGuides();
    expect(tracks).toBeDefined();
    expect(Array.isArray(tracks)).toBe(true);
    expect(tracks.length).toBeGreaterThanOrEqual(14);

    // Verify track metadata
    const ngoMon = tracks.find((t) => t.siteSlug === "ngo-mon");
    expect(ngoMon).toBeDefined();
    expect(ngoMon?.siteNameVi).toBe("Ngọ Môn");
    expect(ngoMon?.duration).toBeGreaterThan(0);
    expect(ngoMon?.transcript.length).toBeGreaterThanOrEqual(3);
  });

  it("fetchSiteAudioGuide fetches specific site audio track with timed cues", async () => {
    const track = await fetchSiteAudioGuide("dien-thai-hoa");
    expect(track).toBeDefined();
    expect(track?.siteSlug).toBe("dien-thai-hoa");
    expect(track?.titleVi).toContain("Điện Thái Hòa");
    expect(track?.transcript.length).toBeGreaterThan(0);

    // Verify cue timing order
    const cues = track!.transcript;
    for (let i = 0; i < cues.length; i++) {
      expect(cues[i].startTime).toBeLessThan(cues[i].endTime);
      if (i > 0) {
        expect(cues[i].startTime).toBeGreaterThanOrEqual(cues[i - 1].startTime);
      }
    }
  });

  it("hasSiteAudioGuide accurately checks known and unknown sites", () => {
    expect(hasSiteAudioGuide("ngo-mon")).toBe(true);
    expect(hasSiteAudioGuide("dien-thai-hoa")).toBe(true);
    expect(hasSiteAudioGuide("non-existent-site-1234")).toBe(false);
  });

  it("formatAudioTime accurately formats durations in MM:SS", () => {
    expect(formatAudioTime(0)).toBe("00:00");
    expect(formatAudioTime(5)).toBe("00:05");
    expect(formatAudioTime(65)).toBe("01:05");
    expect(formatAudioTime(128)).toBe("02:08");
    expect(formatAudioTime(-10)).toBe("00:00");
    expect(formatAudioTime(NaN)).toBe("00:00");
  });

  it("findActiveCue correctly resolves timestamp to active transcript cue", () => {
    const sampleCues: TimedTranscriptCue[] = [
      { id: "cue-1", startTime: 0, endTime: 20, textVi: "Đoạn 1" },
      { id: "cue-2", startTime: 20, endTime: 50, textVi: "Đoạn 2" },
      { id: "cue-3", startTime: 50, endTime: 90, textVi: "Đoạn 3" },
    ];

    expect(findActiveCue(sampleCues, 10)?.id).toBe("cue-1");
    expect(findActiveCue(sampleCues, 20.5)?.id).toBe("cue-2");
    expect(findActiveCue(sampleCues, 75)?.id).toBe("cue-3");
    expect(findActiveCue(sampleCues, 95)?.id).toBe("cue-3"); // At end of track
  });
});
