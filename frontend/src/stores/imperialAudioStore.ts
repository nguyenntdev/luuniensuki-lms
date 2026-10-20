"use client";

import { create } from "zustand";
import { persist, createJSONStorage } from "zustand/middleware";
import type {
  AudioGuideTrack,
  AudioPlayerStore,
  PlaybackRate,
} from "@/lib/imperial/audio-types";
import { fetchSiteAudioGuide, findActiveCue } from "@/lib/imperial/audio-api";

// Non-persisted transient control for the HTMLAudioElement
let globalAudioElement: HTMLAudioElement | null = null;

export function getGlobalAudioElement(): HTMLAudioElement | null {
  if (typeof window === "undefined") return null;
  if (!globalAudioElement) {
    globalAudioElement = new Audio();
    globalAudioElement.preload = "metadata";
  }
  return globalAudioElement;
}

export const useAudioPlayerStore = create<AudioPlayerStore>()(
  persist(
    (set, get) => ({
      currentTrack: null,
      isPlaying: false,
      currentTime: 0,
      duration: 0,
      playbackRate: 1.0,
      volume: 1.0,
      isMuted: false,
      isLoading: false,
      isMinimized: false,
      isDrawerOpen: false,
      activeCueId: null,

      playTrack: (track: AudioGuideTrack, autoPlay = true) => {
        const audio = getGlobalAudioElement();
        const prevTrack = get().currentTrack;
        const isSame = prevTrack?.id === track.id;

        set({
          currentTrack: track,
          currentTime: isSame ? get().currentTime : 0,
          duration: track.duration || 120,
          isLoading: !isSame,
          activeCueId: track.transcript?.[0]?.id || null,
        });

        if (audio) {
          if (!isSame) {
            audio.src = track.audioUrl;
            audio.currentTime = 0;
            audio.playbackRate = get().playbackRate;
            audio.volume = get().isMuted ? 0 : get().volume;
          }

          if (autoPlay) {
            audio
              .play()
              .then(() => {
                set({ isPlaying: true, isLoading: false });
              })
              .catch((err) => {
                // Autoplay policy or missing audio file in development
                // We fallback into synthesized playback simulation if file is not found
                console.warn("[AudioGuide] Audio play notice:", err?.message || err);
                set({ isPlaying: true, isLoading: false });
              });
          }
        }
      },

      playSite: async (siteSlug: string, autoPlay = true) => {
        set({ isLoading: true });
        const track = await fetchSiteAudioGuide(siteSlug);
        if (!track) {
          set({ isLoading: false });
          return false;
        }
        get().playTrack(track, autoPlay);
        return true;
      },

      togglePlayPause: () => {
        const { isPlaying, currentTrack } = get();
        if (!currentTrack) return;

        const audio = getGlobalAudioElement();
        if (isPlaying) {
          if (audio) audio.pause();
          set({ isPlaying: false });
        } else {
          if (audio) {
            audio
              .play()
              .then(() => set({ isPlaying: true }))
              .catch(() => set({ isPlaying: true }));
          } else {
            set({ isPlaying: true });
          }
        }
      },

      pause: () => {
        const audio = getGlobalAudioElement();
        if (audio) audio.pause();
        set({ isPlaying: false });
      },

      resume: () => {
        const { currentTrack } = get();
        if (!currentTrack) return;
        const audio = getGlobalAudioElement();
        if (audio) {
          audio
            .play()
            .then(() => set({ isPlaying: true }))
            .catch(() => set({ isPlaying: true }));
        } else {
          set({ isPlaying: true });
        }
      },

      seekTo: (seconds: number) => {
        const { duration, currentTrack } = get();
        const safeTarget = Math.max(0, Math.min(seconds, duration || 9999));
        const audio = getGlobalAudioElement();
        if (audio) {
          try {
            audio.currentTime = safeTarget;
          } catch {
            // Ignore seek error if audio not ready
          }
        }

        const activeCue = currentTrack
          ? findActiveCue(currentTrack.transcript, safeTarget)
          : null;

        set({
          currentTime: safeTarget,
          activeCueId: activeCue ? activeCue.id : null,
        });
      },

      skipTime: (deltaSeconds: number) => {
        const { currentTime, duration, currentTrack } = get();
        const newTime = Math.max(0, Math.min(currentTime + deltaSeconds, duration || 9999));
        const audio = getGlobalAudioElement();
        if (audio) {
          try {
            audio.currentTime = newTime;
          } catch {
            // Safe fallback
          }
        }

        const activeCue = currentTrack
          ? findActiveCue(currentTrack.transcript, newTime)
          : null;

        set({
          currentTime: newTime,
          activeCueId: activeCue ? activeCue.id : null,
        });
      },

      setPlaybackRate: (rate: PlaybackRate) => {
        const audio = getGlobalAudioElement();
        if (audio) {
          audio.playbackRate = rate;
        }
        set({ playbackRate: rate });
      },

      cyclePlaybackRate: () => {
        const { playbackRate } = get();
        let nextRate: PlaybackRate = 1.0;
        if (playbackRate === 0.75) nextRate = 1.0;
        else if (playbackRate === 1.0) nextRate = 1.25;
        else if (playbackRate === 1.25) nextRate = 1.5;
        else if (playbackRate === 1.5) nextRate = 0.75;
        else nextRate = 1.0;

        get().setPlaybackRate(nextRate);
      },

      setVolume: (volume: number) => {
        const clamped = Math.max(0, Math.min(volume, 1));
        const audio = getGlobalAudioElement();
        if (audio) {
          audio.volume = clamped;
        }
        set({
          volume: clamped,
          isMuted: clamped === 0,
        });
      },

      toggleMute: () => {
        const { isMuted, volume } = get();
        const audio = getGlobalAudioElement();
        const newMuted = !isMuted;
        if (audio) {
          audio.muted = newMuted;
          audio.volume = newMuted ? 0 : volume;
        }
        set({ isMuted: newMuted });
      },

      setMinimized: (minimized: boolean) => set({ isMinimized: minimized }),
      toggleMinimized: () => set((s) => ({ isMinimized: !s.isMinimized })),

      setDrawerOpen: (open: boolean) => set({ isDrawerOpen: open }),
      toggleDrawer: () => set((s) => ({ isDrawerOpen: !s.isDrawerOpen })),

      closePlayer: () => {
        const audio = getGlobalAudioElement();
        if (audio) {
          audio.pause();
          audio.src = "";
        }
        set({
          currentTrack: null,
          isPlaying: false,
          currentTime: 0,
          isDrawerOpen: false,
          activeCueId: null,
        });
      },

      updateTime: (currentTime: number, duration?: number) => {
        const { currentTrack } = get();
        const finalDuration =
          duration && duration > 0 ? duration : get().duration;
        const activeCue = currentTrack
          ? findActiveCue(currentTrack.transcript, currentTime)
          : null;

        set({
          currentTime,
          duration: finalDuration,
          activeCueId: activeCue ? activeCue.id : null,
        });
      },

      setIsLoading: (loading: boolean) => set({ isLoading: loading }),
      setIsPlaying: (isPlaying: boolean) => set({ isPlaying }),
    }),
    {
      name: "sttt-imperial-audio-player",
      storage: createJSONStorage(() => localStorage),
      partialize: (state) => ({
        playbackRate: state.playbackRate,
        volume: state.volume,
        isMuted: state.isMuted,
      }),
    },
  ),
);
