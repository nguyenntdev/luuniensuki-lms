"use client";

import { useEffect, useState, useCallback } from "react";
import { Heart } from "lucide-react";
import useHeartsStore from "@/stores/heartsStore";

function HeartIcon({ filled, index }) {
  return (
    <div
      className="relative inline-flex transition-all duration-200"
      style={{ animationDelay: `${index * 50}ms` }}
    >
      <Heart
        className={`w-6 h-6 transition-all duration-300 ${
          filled
            ? "fill-red-500 text-red-500 scale-100"
            : "fill-gray-300 text-gray-400 scale-90 opacity-60"
        }`}
        strokeWidth={2}
      />
    </div>
  );
}

function CountdownTimer({ targetTime }) {
  const [timeLeft, setTimeLeft] = useState("");

  useEffect(() => {
    if (!targetTime) {
      setTimeLeft("");
      return;
    }

    const updateTimer = () => {
      const now = new Date();
      const target = new Date(targetTime);
      const diff = target - now;

      if (diff <= 0) {
        setTimeLeft("Ready!");
        return;
      }

      const hours = Math.floor(diff / (1000 * 60 * 60));
      const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
      const seconds = Math.floor((diff % (1000 * 60)) / 1000);

      if (hours > 0) {
        setTimeLeft(`${hours}h ${minutes}m`);
      } else if (minutes > 0) {
        setTimeLeft(`${minutes}m ${seconds}s`);
      } else {
        setTimeLeft(`${seconds}s`);
      }
    };

    updateTimer();
    const interval = setInterval(updateTimer, 1000);

    return () => clearInterval(interval);
  }, [targetTime]);

  if (!timeLeft) return null;

  return (
    <div className="text-xs text-muted-foreground mt-1">
      Next heart: {timeLeft}
    </div>
  );
}

export default function HeartsDisplay({
  showLabel = true,
  showTimer = true,
  size = "md",
  onClick,
}) {
  const hearts = useHeartsStore((state) => state.hearts);
  const maxHearts = useHeartsStore((state) => state.maxHearts);
  const nextRefillAt = useHeartsStore((state) => state.nextRefillAt);
  const isUnlimited = useHeartsStore((state) => state.isUnlimited);
  const fetchHearts = useHeartsStore((state) => state.fetchHearts);
  const isLoading = useHeartsStore((state) => state.isLoading);

  useEffect(() => {
    fetchHearts().catch(() => null);
  }, [fetchHearts]);

  const handleClick = useCallback(() => {
    if (onClick) {
      onClick();
    }
  }, [onClick]);

  const isClickable = !!onClick;
  const unlimited = isUnlimited();

  return (
    <div
      className={`inline-flex flex-col items-center ${
        isClickable ? "cursor-pointer hover:opacity-80 transition-opacity" : ""
      }`}
      onClick={handleClick}
    >
      <div className="flex items-center gap-1">
        {showLabel && !unlimited && (
          <span className="text-sm font-medium text-foreground mr-1">
            {hearts}/{maxHearts}
          </span>
        )}
        {unlimited ? (
          <div className="flex items-center gap-1 text-sm font-medium text-primary">
            <Heart className="w-5 h-5 fill-primary text-primary" />
            <span>Unlimited</span>
          </div>
        ) : (
          <div className="flex gap-1">
            {Array.from({ length: maxHearts }, (_, i) => (
              <HeartIcon key={i} filled={i < hearts} index={i} />
            ))}
          </div>
        )}
      </div>
      {showTimer && !unlimited && hearts < maxHearts && (
        <CountdownTimer targetTime={nextRefillAt} />
      )}
      {isLoading && (
        <div className="text-xs text-muted-foreground mt-1">Loading...</div>
      )}
    </div>
  );
}

