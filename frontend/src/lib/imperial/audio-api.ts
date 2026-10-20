/**
 * STTTNNĐ Spec STTT-SPEC-AUDIO-PASSPORT-002
 * Audio API client for Heritage Audio Guides
 * Handles fetching tracks with graceful fallback to static JSON data.
 */

import { apiRequest } from "@/lib/api";
import type { AudioGuideTrack, TimedTranscriptCue } from "./audio-types";

interface RawCue {
  id: string;
  startTime: number;
  endTime: number;
  textVi: string;
  textEn?: string;
  speaker?: string;
  sectionTitle?: string;
}

interface RawTrack {
  id: string;
  site_slug: string;
  site_name_vi: string;
  site_name_han_nom?: string;
  title_vi: string;
  title_en?: string;
  narrator: string;
  duration: number;
  audio_url: string;
  historical_period?: string;
  summary?: string;
  tags?: string[];
  cover_image?: string;
  transcript: RawCue[];
}

interface AudioGuidesFile {
  content_scope: string;
  version: string;
  tracks: RawTrack[];
}

// Built-in static fallback dataset (synced with data/imperial/audio_guides.json)
import audioGuidesJson from "../../../../data/imperial/audio_guides.json";

function transformRawTrack(raw: RawTrack): AudioGuideTrack {
  return {
    id: raw.id,
    siteSlug: raw.site_slug,
    siteNameVi: raw.site_name_vi,
    siteNameHanNom: raw.site_name_han_nom,
    titleVi: raw.title_vi,
    titleEn: raw.title_en,
    narrator: raw.narrator || "Giọng đọc Thừa Thiên Huế — Lưu Niên Di Sản",
    duration: raw.duration || 120,
    audioUrl: raw.audio_url || `/assets/imperial/audio/${raw.site_slug}.mp3`,
    historicalPeriod: raw.historical_period,
    summary: raw.summary,
    tags: raw.tags || [],
    coverImage: raw.cover_image,
    transcript: (raw.transcript || []).map((cue: RawCue): TimedTranscriptCue => ({
      id: cue.id,
      startTime: cue.startTime,
      endTime: cue.endTime,
      textVi: cue.textVi,
      textEn: cue.textEn,
      speaker: cue.speaker || "Thuyết minh viên",
      sectionTitle: cue.sectionTitle,
    })),
  };
}

const STATIC_TRACKS: AudioGuideTrack[] = ((audioGuidesJson as AudioGuidesFile).tracks || []).map(
  transformRawTrack,
);

const TRACKS_BY_SLUG = new Map<string, AudioGuideTrack>(
  STATIC_TRACKS.map((t) => [t.siteSlug, t]),
);

/**
 * Fetch all available audio guide tracks.
 * Tries the canonical backend endpoint /api/v1/imperial/audio-guides,
 * and falls back to static JSON if offline or unavailable.
 */
export async function fetchAllAudioGuides(): Promise<AudioGuideTrack[]> {
  try {
    const data = await apiRequest<{ tracks?: RawTrack[]; items?: RawTrack[] }>(
      "/api/v1/imperial/audio-guides",
      { cache: "no-store" },
    );
    const rawList = data?.tracks || data?.items;
    if (Array.isArray(rawList) && rawList.length > 0) {
      return rawList.map(transformRawTrack);
    }
  } catch (err) {
    // Graceful fallback to embedded data
  }
  return STATIC_TRACKS;
}

/**
 * Fetch a specific site's audio guide track by site slug.
 */
export async function fetchSiteAudioGuide(
  siteSlug: string,
): Promise<AudioGuideTrack | null> {
  if (!siteSlug) return null;

  try {
    const data = await apiRequest<{ track?: RawTrack } | RawTrack>(
      `/api/v1/imperial/sites/${encodeURIComponent(siteSlug)}/audio`,
      { cache: "no-store" },
    );
    const raw = (data as { track?: RawTrack })?.track || (data as RawTrack);
    if (raw && (raw.site_slug || raw.id)) {
      return transformRawTrack(raw);
    }
  } catch (err) {
    // Fall through to fallback map
  }

  return TRACKS_BY_SLUG.get(siteSlug) || null;
}

/**
 * Check if a site slug has an available audio guide.
 */
export function hasSiteAudioGuide(siteSlug: string): boolean {
  return TRACKS_BY_SLUG.has(siteSlug);
}

/**
 * Helper to format seconds into MM:SS format.
 */
export function formatAudioTime(seconds: number): string {
  if (isNaN(seconds) || seconds < 0) return "00:00";
  const mins = Math.floor(seconds / 60);
  const secs = Math.floor(seconds % 60);
  const mStr = mins < 10 ? `0${mins}` : `${mins}`;
  const sStr = secs < 10 ? `0${secs}` : `${secs}`;
  return `${mStr}:${sStr}`;
}

/**
 * Find the active transcript cue based on the current playback time.
 */
export function findActiveCue(
  cues: TimedTranscriptCue[],
  currentTime: number,
): TimedTranscriptCue | null {
  if (!cues || cues.length === 0) return null;
  // Account for a small 0.1s threshold
  const matched = cues.find(
    (c) => currentTime >= c.startTime - 0.05 && currentTime < c.endTime,
  );
  if (matched) return matched;
  // If at the end
  const last = cues[cues.length - 1];
  if (currentTime >= last.endTime - 0.5) return last;
  return null;
}
