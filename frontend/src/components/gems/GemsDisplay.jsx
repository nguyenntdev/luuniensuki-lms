"use client";

import { useEffect, useState, useCallback } from "react";
import { Gem } from "lucide-react";
import useGemsStore from "@/stores/gemsStore";

export default function GemsDisplay({
  showLabel = true,
  size = "md",
  onClick,
}) {
  const gems = useGemsStore((state) => state.gems);
  const [prevGems, setPrevGems] = useState(gems);
  const [isAnimating, setIsAnimating] = useState(false);

  useEffect(() => {
    if (gems !== prevGems) {
      setIsAnimating(true);
      const timer = setTimeout(() => {
        setIsAnimating(false);
        setPrevGems(gems);
      }, 600);
      return () => clearTimeout(timer);
    }
  }, [gems, prevGems]);

  const handleClick = useCallback(() => {
    if (onClick) {
      onClick();
    }
  }, [onClick]);

  const isClickable = !!onClick;

  const sizeClasses = {
    sm: "text-xs",
    md: "text-sm",
    lg: "text-base",
  };

  const iconSizes = {
    sm: "w-4 h-4",
    md: "w-5 h-5",
    lg: "w-6 h-6",
  };

  return (
    <div
      className={`inline-flex items-center gap-1.5 ${
        isClickable ? "cursor-pointer hover:opacity-80 transition-opacity" : ""
      }`}
      onClick={handleClick}
    >
      <div
        className={`relative transition-transform duration-300 ${
          isAnimating ? "scale-125" : "scale-100"
        }`}
      >
        <Gem
          className={`${iconSizes[size]} text-blue-500 fill-blue-400 transition-all duration-300`}
        />
        {isAnimating && (
          <div className="absolute inset-0 rounded-full bg-blue-400/30 animate-ping" />
        )}
      </div>

      {showLabel && (
        <span
          className={`${sizeClasses[size]} font-semibold text-foreground transition-all duration-300 ${
            isAnimating ? "scale-110 text-blue-500" : "scale-100"
          }`}
        >
          {gems.toLocaleString()}
        </span>
      )}
    </div>
  );
}

