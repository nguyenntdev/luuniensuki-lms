"use client";

import { create } from "zustand";
import { persist, createJSONStorage } from "zustand/middleware";

// Gems earned/spent amounts
export const GEM_AMOUNTS = {
  COMPLETE_LESSON: 10,
  PERFECT_QUIZ: 25,
  DAILY_GOAL: 20,
  STREAK_7_DAYS: 50,
  HEART_REFILL: -25,
  STREAK_FREEZE: -50,
  QUIZ_HINT: -5,
  DOUBLE_XP: -100,
} as const;

export interface GemTransaction {
  amount: number;
  reason: string;
  timestamp: string;
}

interface GemsState {
  gems: number;
  transactions: GemTransaction[];
  addGems: (amount: number, reason: string) => number;
  spendGems: (amount: number, reason: string) => number;
  canAfford: (amount: number) => boolean;
  getBalance: () => number;
  reset: () => void;
}

const useGemsStore = create<GemsState>()(
  persist(
    (set, get) => ({
      gems: 100, // Starting gems
      transactions: [],

      addGems: (amount, reason) => {
        const newGems = get().gems + amount;
        set({
          gems: newGems,
          transactions: [
            { amount, reason, timestamp: new Date().toISOString() },
            ...get().transactions.slice(0, 49), // Keep last 50
          ],
        });
        return newGems;
      },

      spendGems: (amount, reason) => {
        const currentGems = get().gems;
        if (currentGems < amount) {
          throw new Error("Insufficient gems");
        }
        const newGems = currentGems - amount;
        set({
          gems: newGems,
          transactions: [
            { amount: -amount, reason, timestamp: new Date().toISOString() },
            ...get().transactions.slice(0, 49),
          ],
        });
        return newGems;
      },

      canAfford: (amount) => get().gems >= amount,

      getBalance: () => get().gems,

      reset: () => {
        set({
          gems: 100,
          transactions: [],
        });
      },
    }),
    {
      name: "luuniensuki-gems-storage",
      version: 1,
      storage: createJSONStorage(() => localStorage),
    }
  )
);

export default useGemsStore;
