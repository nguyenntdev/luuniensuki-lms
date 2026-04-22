"use client";

import { create } from "zustand";

const useBadgeStore = create((set, get) => ({
  unlockedBadge: null,
  showUnlockBadge: (badge) => set({ unlockedBadge: badge }),
  clearUnlockBadge: () => set({ unlockedBadge: null }),
}));

export default useBadgeStore;

