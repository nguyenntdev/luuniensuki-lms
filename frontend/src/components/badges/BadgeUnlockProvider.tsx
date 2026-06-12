"use client";

import useBadgeStore from "@/stores/badgeStore";
import BadgeUnlockToast from "./BadgeUnlockToast";
import type { ComponentProps, ReactNode } from "react";

interface BadgeUnlockProviderProps {
  children: ReactNode;
}

/**
 * Badge Unlock Provider
 * Handles display of badge unlock notifications
 * Should be placed in the app layout to show badges globally
 */
export default function BadgeUnlockProvider({ children }: BadgeUnlockProviderProps) {
  const unlockedBadge = useBadgeStore((state) => state.unlockedBadge);
  const clearUnlockBadge = useBadgeStore((state) => state.clearUnlockBadge);

  return (
    <>
      {children}
      {unlockedBadge && (
        <BadgeUnlockToast
          badge={
            unlockedBadge as ComponentProps<typeof BadgeUnlockToast>["badge"]
          }
          onClose={clearUnlockBadge}
        />
      )}
    </>
  );
}

