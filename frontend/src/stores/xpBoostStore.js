"use client";

import { create } from "zustand";
import { persist, createJSONStorage } from "zustand/middleware";

export const XP_BOOST_COST = 100;

const useXpBoostStore = create(
  persist(
    (set, get) => ({
      isActive: false,
      multiplier: 2,
      expiresAt: null,
      availableBoosts: 0,

      activateBoost: (durationMinutes = 15) => {
        const { availableBoosts, isActive } = get();
        
        if (availableBoosts <= 0) {
          throw new Error("No boosts available");
        }

        if (isActive) {
          throw new Error("Boost already active");
        }

        const expiresAt = Date.now() + durationMinutes * 60 * 1000;
        set({
          isActive: true,
          expiresAt,
          availableBoosts: availableBoosts - 1,
        });

        setTimeout(() => {
          get().checkExpiry();
        }, durationMinutes * 60 * 1000);
      },

      checkExpiry: () => {
        const { expiresAt, isActive } = get();
        if (isActive && expiresAt && Date.now() > expiresAt) {
          set({ isActive: false, expiresAt: null });
          return true;
        }
        return false;
      },

      addBoost: (count = 1) => {
        set({ availableBoosts: get().availableBoosts + count });
      },

      getRemainingTime: () => {
        const { expiresAt, isActive } = get();
        if (!isActive || !expiresAt) return 0;
        return Math.max(0, expiresAt - Date.now());
      },

      getRemainingTimeFormatted: () => {
        const ms = get().getRemainingTime();
        if (ms === 0) return "00:00";
        
        const totalSeconds = Math.floor(ms / 1000);
        const minutes = Math.floor(totalSeconds / 60);
        const seconds = totalSeconds % 60;
        
        return `${minutes.toString().padStart(2, "0")}:${seconds.toString().padStart(2, "0")}`;
      },

      canActivate: () => {
        const { availableBoosts, isActive } = get();
        return availableBoosts > 0 && !isActive;
      },

      reset: () => {
        set({
          isActive: false,
          expiresAt: null,
          availableBoosts: 0,
        });
      },
    }),
    {
      name: "luuniensuki-xp-boost-storage",
      version: 1,
      storage: createJSONStorage(() => localStorage),
    }
  )
);

export default useXpBoostStore;

