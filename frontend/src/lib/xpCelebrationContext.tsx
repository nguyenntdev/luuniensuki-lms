"use client";

import React, {
  createContext,
  useContext,
  useState,
  useCallback,
  type ReactNode,
} from "react";
import XpCelebrationOverlay from "@/components/XpCelebrationOverlay";

/**
 * XP Celebration Context
 * Provides a global way to trigger XP celebrations from anywhere in the app
 *
 * Usage:
 * const { showXpCelebration } = useXpCelebration();
 * showXpCelebration({ xpGained: 50, oldTotalXp: 100, newTotalXp: 150 });
 */

export interface XpCelebrationBadge {
  id?: string | number;
  name?: string;
  [key: string]: unknown;
}

export interface XpCelebrationPayload {
  xpGained: number;
  oldTotalXp: number;
  newTotalXp: number;
  badges?: XpCelebrationBadge[];
}

interface XpCelebrationContextValue {
  showXpCelebration: (payload: XpCelebrationPayload) => void;
}

const XpCelebrationContext = createContext<XpCelebrationContextValue | null>(
  null
);

export function XpCelebrationProvider({ children }: { children: ReactNode }) {
  const [celebration, setCelebration] = useState<XpCelebrationPayload | null>(
    null
  );

  const showXpCelebration = useCallback(
    ({ xpGained, oldTotalXp, newTotalXp, badges = [] }: XpCelebrationPayload) => {
      if (xpGained <= 0) return;

      setCelebration({
        xpGained,
        oldTotalXp,
        newTotalXp,
        badges,
      });
    },
    []
  );

  const handleComplete = useCallback(() => {
    setCelebration(null);
  }, []);

  return (
    <XpCelebrationContext.Provider value={{ showXpCelebration }}>
      {children}
      {celebration && (
        <XpCelebrationOverlay
          xpGained={celebration.xpGained}
          oldTotalXp={celebration.oldTotalXp}
          newTotalXp={celebration.newTotalXp}
          badges={celebration.badges}
          onComplete={handleComplete}
        />
      )}
    </XpCelebrationContext.Provider>
  );
}

export function useXpCelebration(): XpCelebrationContextValue {
  const context = useContext(XpCelebrationContext);
  if (!context) {
    throw new Error(
      "useXpCelebration must be used within XpCelebrationProvider"
    );
  }
  return context;
}
