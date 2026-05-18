"use client";

import { useEffect, useState } from "react";
import { Zap } from "lucide-react";
import useXpBoostStore from "@/stores/xpBoostStore";

export default function XpBoostIndicator({ size = "md", showLabel = true }) {
  const { isActive, getRemainingTimeFormatted, checkExpiry } = useXpBoostStore();
  const [timeRemaining, setTimeRemaining] = useState("00:00");

  useEffect(() => {
    if (!isActive) return;

    checkExpiry();

    const updateTimer = () => {
      if (checkExpiry()) {
        return;
      }
      setTimeRemaining(getRemainingTimeFormatted());
    };

    updateTimer();
    const interval = setInterval(updateTimer, 1000);

    return () => clearInterval(interval);
  }, [isActive, checkExpiry, getRemainingTimeFormatted]);

  if (!isActive) return null;

  const sizeClasses = {
    sm: "text-xs",
    md: "text-sm",
    lg: "text-base",
  };

  const badgeSizes = {
    sm: "text-sm px-2 py-1",
    md: "text-base px-3 py-1.5",
    lg: "text-lg px-4 py-2",
  };

  const iconSizes = {
    sm: "w-3 h-3",
    md: "w-4 h-4",
    lg: "w-5 h-5",
  };

  return (
    <div
      className={`inline-flex items-center gap-2 rounded-full bg-gradient-to-r from-yellow-500 to-orange-500 ${badgeSizes[size]} shadow-lg animate-pulse`}
    >
      <div className="flex items-center gap-1.5">
        <Zap className={`${iconSizes[size]} fill-white text-white`} />
        <span className="font-bold text-white">2X XP</span>
      </div>
      {showLabel && (
        <span className={`${sizeClasses[size]} font-mono font-semibold text-yellow-100`}>
          {timeRemaining}
        </span>
      )}
    </div>
  );
}

