"use client";

import { useEffect, useState } from "react";

/**
 * XP Celebration Overlay Component
 * Shows animated XP celebration when user earns XP
 * 
 * Inspired by mobile implementation: mobile/lib/shared/widgets/xp_celebration_overlay.dart
 * 
 * Celebration levels:
 * - Small (< 30 XP): Simple badge animation
 * - Medium (30-60 XP): Badge + particle effects
 * - Large (> 60 XP): Badge + confetti
 * - Level Up: Special banner + confetti
 */

const CELEBRATION_DURATION: Record<CelebrationLevel, number> = {
  small: 1500,
  medium: 2000,
  large: 2500,
};

type CelebrationLevel = "small" | "medium" | "large";

function getCelebrationLevel(xpGained: number): CelebrationLevel {
  if (xpGained < 30) return "small";
  if (xpGained < 60) return "medium";
  return "large";
}

function calculateLevelUp(oldTotalXp: number, newTotalXp: number): number | null {
  const oldLevel = Math.floor(oldTotalXp / 100);
  const newLevel = Math.floor(newTotalXp / 100);
  return newLevel > oldLevel ? newLevel : null;
}

interface XpCelebrationOverlayProps {
  xpGained: number;
  oldTotalXp: number;
  newTotalXp: number;
  badges?: unknown[];
  onComplete?: () => void;
}

export default function XpCelebrationOverlay({
  xpGained,
  oldTotalXp,
  newTotalXp,
  badges = [],
  onComplete,
}: XpCelebrationOverlayProps) {
  const [isVisible, setIsVisible] = useState(false);
  const [isAnimating, setIsAnimating] = useState(false);

  const celebrationLevel = getCelebrationLevel(xpGained);
  const newLevel = calculateLevelUp(oldTotalXp, newTotalXp);
  const didLevelUp = newLevel !== null;
  const duration = didLevelUp ? 2500 : CELEBRATION_DURATION[celebrationLevel];

  useEffect(() => {
    setIsVisible(true);
    setIsAnimating(true);

    const timer = setTimeout(() => {
      setIsAnimating(false);
      setTimeout(() => {
        setIsVisible(false);
        if (onComplete) onComplete();
      }, 300);
    }, duration);

    return () => clearTimeout(timer);
  }, [duration, onComplete]);

  if (!isVisible) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center pointer-events-none"
      role="alert"
      aria-live="polite"
    >
      {/* Confetti for large celebrations and level-ups */}
      {(celebrationLevel === "large" || didLevelUp) && isAnimating && (
        <div className="absolute inset-0 overflow-hidden">
          {[...Array(didLevelUp ? 50 : 30)].map((_, i) => (
            <div
              key={i}
              className="absolute w-2 h-2 animate-confetti"
              style={{
                left: `${50 + Math.random() * 10 - 5}%`,
                top: "20%",
                backgroundColor: [
                  "hsl(43, 74%, 49%)",
                  "hsl(var(--primary))",
                  "hsl(var(--success))",
                  "hsl(262, 83%, 58%)",
                  "hsl(142, 76%, 36%)",
                  "hsl(25, 95%, 53%)",
                ][Math.floor(Math.random() * 6)],
                animationDelay: `${Math.random() * 0.5}s`,
                animationDuration: `${2 + Math.random()}s`,
                transform: `rotate(${Math.random() * 360}deg)`,
              }}
            />
          ))}
        </div>
      )}

      {/* Particles for medium celebrations */}
      {celebrationLevel === "medium" && isAnimating && (
        <div className="absolute inset-0">
          {[...Array(15)].map((_, i) => (
            <div
              key={i}
              className="absolute w-1 h-1 rounded-full bg-primary animate-particle"
              style={{
                left: "50%",
                top: "50%",
                animationDelay: `${i * 0.1}s`,
                transform: `rotate(${i * (360 / 15)}deg)`,
              }}
            />
          ))}
        </div>
      )}

      {/* Level Up Banner */}
      {didLevelUp && (
        <div
          className={`absolute top-24 left-0 right-0 flex justify-center transition-all duration-500 ${
            isAnimating ? "translate-y-0 opacity-100" : "-translate-y-full opacity-0"
          }`}
        >
          <div className="mx-8 px-8 py-5 rounded-2xl bg-gradient-to-r from-success to-primary shadow-2xl">
            <div className="text-center text-white">
              <div className="text-sm font-medium opacity-90">🎉 LEVEL UP! 🎉</div>
              <div className="text-3xl font-bold mt-1">Cấp {newLevel}</div>
            </div>
          </div>
        </div>
      )}

      {/* XP Badge */}
      <div
        className={`transition-all duration-500 ease-out ${
          isAnimating
            ? "translate-y-0 scale-100 opacity-100"
            : "-translate-y-48 scale-75 opacity-0"
        }`}
        style={{
          animation: isAnimating
            ? `xpBadgeBounce ${duration}ms cubic-bezier(0.34, 1.56, 0.64, 1)`
            : undefined,
        }}
      >
        <div className="px-6 py-4 rounded-3xl bg-gradient-to-b from-xp-gold to-xp-gold-dark shadow-2xl">
          <div className="flex items-center gap-3">
            <span className="text-4xl">⭐</span>
            <span className="text-3xl font-bold text-white tracking-wide">
              +{xpGained} XP
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}

