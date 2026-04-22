"use client";

import useBadgeStore from "@/stores/badgeStore";
import BadgeUnlockToast from "./BadgeUnlockToast";

/**
 * Badge Unlock Provider
 * Handles display of badge unlock notifications
 * Should be placed in the app layout to show badges globally
 */
export default function BadgeUnlockProvider({ children }) {
  const unlockedBadge = useBadgeStore((state) => state.unlockedBadge);
  const clearUnlockBadge = useBadgeStore((state) => state.clearUnlockBadge);

  return (
    <>
      {children}
      {unlockedBadge && (
        <BadgeUnlockToast badge={unlockedBadge} onClose={clearUnlockBadge} />
      )}
    </>
  );
}

