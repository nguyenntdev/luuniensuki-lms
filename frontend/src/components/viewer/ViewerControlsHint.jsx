"use client";

/**
 * ViewerControlsHint — a one-time, dismissible hint that teaches first-time
 * visitors how to interact with the 3D urn (drag / zoom / tap hotspots). It
 * shows once per browser (localStorage), auto-hides after a few seconds, and
 * hides immediately on the first pointer interaction.
 */

import { useEffect, useState } from "react";
import { Hand, ZoomIn, MousePointerClick, X } from "lucide-react";

const SEEN_KEY = "lns_viewer_controls_hint_seen_v1";

export default function ViewerControlsHint() {
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    let seen = false;
    try {
      seen = localStorage.getItem(SEEN_KEY) === "1";
    } catch {
      /* private mode */
    }
    if (seen) return;
    setVisible(true);

    const dismiss = () => setVisible(false);
    const autoHide = setTimeout(dismiss, 9000);
    // Hide as soon as the user starts interacting with the canvas.
    window.addEventListener("pointerdown", dismiss, { once: true, capture: true });
    window.addEventListener("wheel", dismiss, { once: true, passive: true });
    return () => {
      clearTimeout(autoHide);
      window.removeEventListener("pointerdown", dismiss, { capture: true });
      window.removeEventListener("wheel", dismiss);
    };
  }, []);

  useEffect(() => {
    if (visible) return;
    try {
      localStorage.setItem(SEEN_KEY, "1");
    } catch {
      /* ignore */
    }
  }, [visible]);

  if (!visible) return null;

  return (
    <div className="pointer-events-none absolute inset-x-0 bottom-24 z-20 flex justify-center px-4 md:bottom-8">
      <div className="pointer-events-auto flex items-center gap-3 rounded-full border border-white/15 bg-black/65 px-4 py-2.5 text-xs text-white shadow-[0_12px_34px_rgba(0,0,0,0.5)] backdrop-blur-md animate-fade-in">
        <span className="inline-flex items-center gap-1.5">
          <Hand className="h-4 w-4 text-sky-300" /> Kéo để xoay
        </span>
        <span className="h-3 w-px bg-white/20" />
        <span className="inline-flex items-center gap-1.5">
          <ZoomIn className="h-4 w-4 text-emerald-300" /> Cuộn/chụm để phóng
        </span>
        <span className="h-3 w-px bg-white/20" />
        <span className="inline-flex items-center gap-1.5">
          <MousePointerClick className="h-4 w-4 text-amber-300" /> Chạm điểm sáng để mở họa tiết
        </span>
        <button
          type="button"
          onClick={() => setVisible(false)}
          aria-label="Đóng gợi ý"
          className="ml-1 grid h-6 w-6 place-items-center rounded-full text-white/60 hover:bg-white/10 hover:text-white"
        >
          <X className="h-3.5 w-3.5" />
        </button>
      </div>
    </div>
  );
}
