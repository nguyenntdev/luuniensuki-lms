"use client";

import { create } from "zustand";
import { getDailyMissions } from "@/lib/api";

export interface DailyMission {
  id: string | number;
  title?: string;
  description?: string;
  xp_reward?: number;
  progress?: number;
  target?: number;
  completed?: boolean;
  [key: string]: unknown;
}

interface TimeUntilMidnight {
  hours: number;
  minutes: number;
  totalMs: number;
}

interface DailyMissionsState {
  missions: DailyMission[];
  loading: boolean;
  error: string | null;
  lastFetchedAt: string | null;
  totalXpToday: number;
  completedCount: number;
  totalCount: number;
  fetchMissions: () => Promise<void>;
  getTimeUntilMidnight: () => TimeUntilMidnight;
  getMissionById: (missionId: string | number) => DailyMission | null;
  reset: () => void;
}

export const useDailyMissionsStore = create<DailyMissionsState>((set, get) => ({
  missions: [],
  loading: false,
  error: null,
  lastFetchedAt: null,
  totalXpToday: 0,
  completedCount: 0,
  totalCount: 0,

  fetchMissions: async () => {
    set({ loading: true, error: null });
    try {
      const response = (await getDailyMissions()) as {
        missions?: DailyMission[];
        total_xp_today?: number;
        completed_count?: number;
        total_count?: number;
      };
      set({
        missions: response.missions || [],
        totalXpToday: response.total_xp_today || 0,
        completedCount: response.completed_count || 0,
        totalCount: response.total_count || 0,
        lastFetchedAt: new Date().toISOString(),
        loading: false,
        error: null,
      });
    } catch (error) {
      set({
        loading: false,
        error: error instanceof Error ? error.message : String(error),
      });
      console.error("Failed to fetch daily missions:", error);
    }
  },

  getTimeUntilMidnight: () => {
    const now = new Date();
    const tomorrow = new Date(
      now.getFullYear(),
      now.getMonth(),
      now.getDate() + 1
    );
    const diff = tomorrow.getTime() - now.getTime();
    const hours = Math.floor(diff / (1000 * 60 * 60));
    const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
    return { hours, minutes, totalMs: diff };
  },

  getMissionById: (missionId) => {
    const missions = get().missions;
    return missions.find((m) => m.id === missionId) || null;
  },

  reset: () => {
    set({
      missions: [],
      loading: false,
      error: null,
      lastFetchedAt: null,
      totalXpToday: 0,
      completedCount: 0,
      totalCount: 0,
    });
  },
}));

export default useDailyMissionsStore;
