"use client";

import { create } from "zustand";

export interface BadgeInfo {
  id: string | number;
  name?: string;
  description?: string;
  icon?: string;
  [key: string]: unknown;
}

interface BadgeState {
  unlockedBadge: BadgeInfo | null;
  showUnlockBadge: (badge: BadgeInfo) => void;
  clearUnlockBadge: () => void;
}

const useBadgeStore = create<BadgeState>((set) => ({
  unlockedBadge: null,
  showUnlockBadge: (badge) => set({ unlockedBadge: badge }),
  clearUnlockBadge: () => set({ unlockedBadge: null }),
}));

export default useBadgeStore;
