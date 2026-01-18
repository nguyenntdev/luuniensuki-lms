"use client";

import React, { createContext, useContext, useState, useCallback } from "react";
import XpCelebrationOverlay from "@/components/XpCelebrationOverlay";

/**
 * XP Celebration Context
 * Provides a global way to trigger XP celebrations from anywhere in the app
 * 
 * Usage:
 * const { showXpCelebration } = useXpCelebration();
 * showXpCelebration({ xpGained: 50, oldTotalXp: 100, newTotalXp: 150 });
 */

const XpCelebrationContext = createContext(null);

export function XpCelebrationProvider({ children }) {
  const [celebration, setCelebration] = useState(null);

  const showXpCelebration = useCallback(({ xpGained, oldTotalXp, newTotalXp, badges = [] }) => {
    if (xpGained <= 0) return;
    
    setCelebration({
      xpGained,
      oldTotalXp,
      newTotalXp,
      badges,
    });
  }, []);

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

export function useXpCelebration() {
  const context = useContext(XpCelebrationContext);
  if (!context) {
    throw new Error("useXpCelebration must be used within XpCelebrationProvider");
  }
  return context;
}

