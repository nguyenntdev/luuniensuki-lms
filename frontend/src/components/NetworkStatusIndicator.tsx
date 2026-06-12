"use client";

import { useEffect, useState } from "react";
import type { ReactNode } from "react";

/**
 * Network Status Indicator Component
 * Shows a banner when the user goes offline
 * Auto-hides when connection is restored
 * 
 * Inspired by mobile implementation: mobile/lib/shared/widgets/network_status_indicator.dart
 */
interface NetworkStatusIndicatorProps {
  children: ReactNode;
}

export default function NetworkStatusIndicator({ children }: NetworkStatusIndicatorProps) {
  const [isOnline, setIsOnline] = useState(true);
  const [showBanner, setShowBanner] = useState(false);
  const [wasOffline, setWasOffline] = useState(false);

  useEffect(() => {
    const handleOnline = () => {
      setIsOnline(true);
      if (wasOffline) {
        setTimeout(() => {
          setShowBanner(false);
          setWasOffline(false);
        }, 300);
      }
    };

    const handleOffline = () => {
      setIsOnline(false);
      setWasOffline(true);
      setShowBanner(true);
    };

    setIsOnline(navigator.onLine);
    if (!navigator.onLine) {
      setShowBanner(true);
      setWasOffline(true);
    }

    window.addEventListener("online", handleOnline);
    window.addEventListener("offline", handleOffline);

    return () => {
      window.removeEventListener("online", handleOnline);
      window.removeEventListener("offline", handleOffline);
    };
  }, [wasOffline]);

  return (
    <>
      {showBanner && (
        <div
          className={[
            "fixed top-0 left-0 right-0 z-50 transition-transform duration-300",
            showBanner && !isOnline ? "translate-y-0" : "-translate-y-full",
          ].join(" ")}
        >
          <div className="bg-destructive text-destructive-foreground px-4 py-3 shadow-lg">
            <div className="flex items-center justify-center gap-2">
              <svg
                xmlns="http://www.w3.org/2000/svg"
                width="20"
                height="20"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
              >
                <path d="M5 13a10 10 0 0 1 14 0" />
                <path d="M8.5 16.5a5 5 0 0 1 7 0" />
                <path d="M12 20h.01" />
                <line x1="2" y1="2" x2="22" y2="22" />
              </svg>
              <span className="text-sm font-medium">
                Không có kết nối mạng
              </span>
            </div>
          </div>
        </div>
      )}
      <div className={showBanner && !isOnline ? "pt-12" : ""}>
        {children}
      </div>
    </>
  );
}

