"use client";

import { create } from "zustand";
import { apiRequest } from "@/lib/api";

export interface HeartsData {
  current?: number;
  max?: number;
  next_refill_at?: string | null;
  unlimited_until?: string | null;
  [key: string]: unknown;
}

interface HeartsState {
  hearts: number;
  maxHearts: number;
  nextRefillAt: string | null;
  unlimitedUntil: string | null;
  isLoading: boolean;
  error: string | null;
  lastFetchTime: string | null;
  isUnlimited: () => boolean;
  fetchHearts: () => Promise<HeartsData>;
  useHeart: (
    reason?: string,
    metadata?: Record<string, unknown> | null
  ) => Promise<HeartsData>;
  refillHearts: (type?: string) => Promise<HeartsData>;
  useStreakFreeze: () => Promise<HeartsData>;
  decrementHearts: () => void;
  incrementHearts: () => void;
  reset: () => void;
}

const useHeartsStore = create<HeartsState>((set, get) => ({
  hearts: 5,
  maxHearts: 5,
  nextRefillAt: null,
  unlimitedUntil: null,
  isLoading: false,
  error: null,
  lastFetchTime: null,

  isUnlimited: () => {
    const { unlimitedUntil } = get();
    if (!unlimitedUntil) return false;
    return new Date(unlimitedUntil) > new Date();
  },

  fetchHearts: async () => {
    set({ isLoading: true, error: null });
    try {
      const data = (await apiRequest("/api/v1/hearts")) as HeartsData;
      set({
        hearts: data.current ?? 5,
        maxHearts: data.max ?? 5,
        nextRefillAt: data.next_refill_at ?? null,
        unlimitedUntil: data.unlimited_until ?? null,
        isLoading: false,
        error: null,
        lastFetchTime: new Date().toISOString(),
      });
      return data;
    } catch (error) {
      const errorMsg =
        (error instanceof Error && error.message) || "Failed to fetch hearts";
      console.error("Failed to fetch hearts:", error);
      set({ isLoading: false, error: errorMsg });
      throw error;
    }
  },

  useHeart: async (reason = "quiz_wrong", metadata = null) => {
    try {
      const data = (await apiRequest("/api/v1/hearts/use", {
        method: "POST",
        body: { reason, metadata },
      })) as HeartsData;

      set({
        hearts: data.current ?? 0,
        nextRefillAt: data.next_refill_at ?? null,
        unlimitedUntil: data.unlimited_until ?? null,
        error: null,
      });

      return data;
    } catch (error) {
      const errorMsg =
        (error instanceof Error && error.message) || "Failed to use heart";
      console.error("Failed to use heart:", error);
      set({ error: errorMsg });
      throw error;
    }
  },

  refillHearts: async (type = "gems") => {
    set({ isLoading: true, error: null });
    try {
      const data = (await apiRequest("/api/v1/hearts/refill", {
        method: "POST",
        body: { refill_type: type },
      })) as HeartsData;

      set({
        hearts: data.current ?? 5,
        nextRefillAt: data.next_refill_at ?? null,
        unlimitedUntil: data.unlimited_until ?? null,
        isLoading: false,
        error: null,
      });

      return data;
    } catch (error) {
      const errorMsg =
        (error instanceof Error && error.message) || "Failed to refill hearts";
      console.error("Failed to refill hearts:", error);
      set({ isLoading: false, error: errorMsg });
      throw error;
    }
  },

  useStreakFreeze: async () => {
    set({ isLoading: true, error: null });
    try {
      const data = (await apiRequest("/api/v1/hearts/use-streak-freeze", {
        method: "POST",
      })) as HeartsData;

      set({
        hearts: data.current ?? 5,
        nextRefillAt: data.next_refill_at ?? null,
        unlimitedUntil: data.unlimited_until ?? null,
        isLoading: false,
        error: null,
      });

      return data;
    } catch (error) {
      const errorMsg =
        (error instanceof Error && error.message) ||
        "Failed to use streak freeze";
      console.error("Failed to use streak freeze:", error);
      set({ isLoading: false, error: errorMsg });
      throw error;
    }
  },

  decrementHearts: () => {
    set((state) => ({
      hearts: Math.max(0, state.hearts - 1),
    }));
  },

  incrementHearts: () => {
    set((state) => ({
      hearts: Math.min(state.maxHearts, state.hearts + 1),
    }));
  },

  reset: () => {
    set({
      hearts: 5,
      maxHearts: 5,
      nextRefillAt: null,
      unlimitedUntil: null,
      isLoading: false,
      error: null,
      lastFetchTime: null,
    });
  },
}));

export default useHeartsStore;
