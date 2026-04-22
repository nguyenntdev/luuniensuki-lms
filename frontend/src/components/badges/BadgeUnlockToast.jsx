"use client";

import { useEffect, useState } from "react";
import { X, Award } from "lucide-react";

export default function BadgeUnlockToast({ badge, onClose }) {
  const [isVisible, setIsVisible] = useState(false);

  useEffect(() => {
    if (badge) {
      // Trigger entrance animation
      setIsVisible(true);

      // Auto-dismiss after 5 seconds
      const timer = setTimeout(() => {
        setIsVisible(false);
        setTimeout(() => {
          onClose();
        }, 300); // Wait for exit animation
      }, 5000);

      return () => clearTimeout(timer);
    }
  }, [badge, onClose]);

  if (!badge) return null;

  return (
    <div
      className={`fixed bottom-4 right-4 z-50 transition-all duration-500 ${
        isVisible
          ? "translate-y-0 opacity-100"
          : "translate-y-full opacity-0"
      }`}
    >
      <div className="bg-gradient-to-r from-yellow-500 to-amber-600 rounded-lg p-4 shadow-2xl flex items-center gap-4 max-w-sm">
        <div className="w-16 h-16 bg-white/20 rounded-full flex items-center justify-center flex-shrink-0">
          {badge.icon_url ? (
            <img
              src={badge.icon_url}
              alt={badge.name}
              className="w-12 h-12 object-contain"
            />
          ) : (
            <Award className="w-8 h-8 text-white" />
          )}
        </div>
        <div className="flex-1 min-w-0">
          <p className="text-xs text-yellow-100 uppercase tracking-wide font-medium">
            Huy hiệu mới!
          </p>
          <p className="text-lg font-bold text-white truncate">
            {badge.name}
          </p>
          <p className="text-sm text-yellow-100 line-clamp-2">
            {badge.description}
          </p>
        </div>
        <button
          onClick={() => {
            setIsVisible(false);
            setTimeout(onClose, 300);
          }}
          className="text-white/70 hover:text-white transition-colors flex-shrink-0"
          aria-label="Đóng thông báo"
        >
          <X className="w-5 h-5" />
        </button>
      </div>
    </div>
  );
}

