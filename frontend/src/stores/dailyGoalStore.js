"use client";

import { create } from "zustand";
import { persist, createJSONStorage } from "zustand/middleware";

export const GOAL_LEVELS = {
  CASUAL: { xp: 10, name: "Thoải mái", description: "10 XP/ngày", emoji: "🌱" },
  REGULAR: { xp: 20, name: "Thường xuyên", description: "20 XP/ngày", emoji: "🔥" },
  SERIOUS: { xp: 30, name: "Nghiêm túc", description: "30 XP/ngày", emoji: "💪" },
  INTENSE: { xp: 50, name: "Cao thủ", description: "50 XP/ngày", emoji: "⚡" },
  INSANE: { xp: 100, name: "Điên cuồng", description: "100 XP/ngày", emoji: "🚀" },
};

const useDailyGoalStore = create(
  persist(
    (set, get) => ({
      goalLevel: "REGULAR",
      currentXp: 0,
      lastUpdated: new Date().toISOString(),
      isCompleted: false,
      lastResetDate: new Date().toDateString(),

      getGoalConfig: () => {
        const level = get().goalLevel;
        return GOAL_LEVELS[level] || GOAL_LEVELS.REGULAR;
      },

      getProgressPercentage: () => {
        const { currentXp } = get();
        const goalXp = get().getGoalConfig().xp;
        return Math.min(100, Math.round((currentXp / goalXp) * 100));
      },

      getRemainingXp: () => {
        const { currentXp } = get();
        const goalXp = get().getGoalConfig().xp;
        const remaining = goalXp - currentXp;
        return remaining > 0 ? remaining : 0;
      },

      shouldReset: () => {
        const { lastResetDate } = get();
        const today = new Date().toDateString();
        return lastResetDate !== today;
      },

      resetIfNeeded: () => {
        if (get().shouldReset()) {
          const level = get().goalLevel;
          set({
            currentXp: 0,
            isCompleted: false,
            lastResetDate: new Date().toDateString(),
            lastUpdated: new Date().toISOString(),
            goalLevel: level,
          });
          return true;
        }
        return false;
      },

      setGoalLevel: (level) => {
        if (!GOAL_LEVELS[level]) {
          console.warn(`Invalid goal level: ${level}`);
          return;
        }

        const { currentXp } = get();
        const newGoalXp = GOAL_LEVELS[level].xp;
        const isCompleted = currentXp >= newGoalXp;

        set({
          goalLevel: level,
          isCompleted,
          lastUpdated: new Date().toISOString(),
        });
      },

      addXp: (xpGained) => {
        if (xpGained <= 0) return false;

        get().resetIfNeeded();

        const { currentXp, isCompleted: wasCompleted } = get();
        const newXp = currentXp + xpGained;
        const goalXp = get().getGoalConfig().xp;
        const isNowCompleted = newXp >= goalXp;

        set({
          currentXp: newXp,
          isCompleted: isNowCompleted,
          lastUpdated: new Date().toISOString(),
        });

        return !wasCompleted && isNowCompleted;
      },

      syncWithUserXp: (totalXp, previousXp = null) => {
        get().resetIfNeeded();

        if (previousXp !== null && previousXp < totalXp) {
          const xpGained = totalXp - previousXp;
          return get().addXp(xpGained);
        }

        return false;
      },

      getTimeUntilMidnight: () => {
        const now = new Date();
        const tomorrow = new Date(
          now.getFullYear(),
          now.getMonth(),
          now.getDate() + 1
        );
        const diff = tomorrow - now;
        const hours = Math.floor(diff / (1000 * 60 * 60));
        const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
        return { hours, minutes, totalMs: diff };
      },

      reset: () => {
        const level = get().goalLevel;
        set({
          goalLevel: level,
          currentXp: 0,
          lastUpdated: new Date().toISOString(),
          isCompleted: false,
          lastResetDate: new Date().toDateString(),
        });
      },

      resetAll: () => {
        set({
          goalLevel: "REGULAR",
          currentXp: 0,
          lastUpdated: new Date().toISOString(),
          isCompleted: false,
          lastResetDate: new Date().toDateString(),
        });
      },
    }),
    {
      name: "luuniensuki-daily-goal-storage",
      version: 1,
      storage: createJSONStorage(() => localStorage),
    }
  )
);

export default useDailyGoalStore;

