"use client";

import { create } from "zustand";
import { apiRequest } from "@/lib/api";

const useHeartsStore = create((set, get) => ({
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
      const data = await apiRequest("/api/v1/hearts");
      set({
        hearts: data.current ?? 5,
        maxHearts: data.max ?? 5,
        nextRefillAt: data.next_refill_at,
        unlimitedUntil: data.unlimited_until,
        isLoading: false,
        error: null,
        lastFetchTime: new Date().toISOString(),
      });
      return data;
    } catch (error) {
      const errorMsg = error?.message || "Failed to fetch hearts";
      console.error("Failed to fetch hearts:", error);
      set({ isLoading: false, error: errorMsg });
      throw error;
    }
  },

  useHeart: async (reason = "quiz_wrong", metadata = null) => {
    try {
      const data = await apiRequest("/api/v1/hearts/use", {
        method: "POST",
        body: { reason, metadata },
      });

      set({
        hearts: data.current ?? 0,
        nextRefillAt: data.next_refill_at,
        unlimitedUntil: data.unlimited_until,
        error: null,
      });

      return data;
    } catch (error) {
      const errorMsg = error?.message || "Failed to use heart";
      console.error("Failed to use heart:", error);
      set({ error: errorMsg });
      throw error;
    }
  },

  refillHearts: async (type = "gems") => {
    set({ isLoading: true, error: null });
    try {
      const data = await apiRequest("/api/v1/hearts/refill", {
        method: "POST",
        body: { refill_type: type },
      });

      set({
        hearts: data.current ?? 5,
        nextRefillAt: data.next_refill_at,
        unlimitedUntil: data.unlimited_until,
        isLoading: false,
        error: null,
      });

      return data;
    } catch (error) {
      const errorMsg = error?.message || "Failed to refill hearts";
      console.error("Failed to refill hearts:", error);
      set({ isLoading: false, error: errorMsg });
      throw error;
    }
  },

  useStreakFreeze: async () => {
    set({ isLoading: true, error: null });
    try {
      const data = await apiRequest("/api/v1/hearts/use-streak-freeze", {
        method: "POST",
      });

      set({
        hearts: data.current ?? 5,
        nextRefillAt: data.next_refill_at,
        unlimitedUntil: data.unlimited_until,
        isLoading: false,
        error: null,
      });

      return data;
    } catch (error) {
      const errorMsg = error?.message || "Failed to use streak freeze";
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

