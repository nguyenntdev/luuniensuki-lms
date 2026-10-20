"use client";

import React, { useCallback } from "react";
import { ArrowDown, CornerDownLeft } from "lucide-react";
import { announceToScreenReader } from "@/lib/imperial/a11y-utils";
import { cn } from "@/lib/utils";

export interface SkipTargetItem {
  id: string;
  label: string;
}

export interface SkipToContentProps {
  /** Target HTML ID to skip to. Defaults to 'imperial-main-content' */
  targetId?: string;
  /** Primary link text in Vietnamese. Defaults to 'Chuyển đến nội dung chính' */
  label?: string;
  /** Optional multiple skip targets (e.g. skip to aerial map, skip to monument list) */
  targets?: SkipTargetItem[];
  /** Optional custom CSS classes for the container */
  className?: string;
}

/**
 * Skip to Content Link component for keyboard and screen reader users.
 * Complies with WCAG 2.2 AA (Success Criterion 2.4.1: Bypass Blocks).
 *
 * Visually hidden until focused via keyboard Tab navigation, at which point it
 * displays prominently with high contrast and smooth focus restoration.
 */
export default function SkipToContent({
  targetId = "imperial-main-content",
  label = "Chuyển đến nội dung chính",
  targets,
  className,
}: SkipToContentProps) {
  const items: SkipTargetItem[] =
    targets && targets.length > 0 ? targets : [{ id: targetId, label }];

  const handleSkipTo = useCallback(
    (e: React.MouseEvent<HTMLAnchorElement>, id: string, targetLabel: string) => {
      // Don't completely prevent default so browser hash updates, but handle smooth focus transfer
      e.preventDefault();

      let targetEl = document.getElementById(id);

      // Graceful fallback if specified ID was not found in DOM
      if (!targetEl) {
        targetEl =
          document.getElementById("main-content") ||
          document.querySelector("main") ||
          document.querySelector("[role='main']");
      }

      if (targetEl) {
        // Ensure element can receive programmatic focus
        if (!targetEl.hasAttribute("tabindex")) {
          targetEl.setAttribute("tabindex", "-1");
        }

        targetEl.focus({ preventScroll: false });
        targetEl.scrollIntoView({ behavior: "smooth", block: "start" });

        // Announce navigation to screen reader
        announceToScreenReader(`Đã chuyển tiêu điểm đến ${targetLabel}`, "polite");
      }
    },
    [],
  );

  return (
    <nav
      aria-label="Liên kết bỏ qua điều hướng"
      className={cn(
        "pointer-events-none fixed top-0 left-0 z-[9999]",
        className,
      )}
    >
      <ul className="flex flex-col gap-2 p-3 sm:p-4">
        {items.map((item) => (
          <li key={item.id}>
            <a
              href={`#${item.id}`}
              onClick={(e) => handleSkipTo(e, item.id, item.label)}
              className={cn(
                // Off-screen by default, brought into prominent focus when tabbed to
                "sr-only pointer-events-auto",
                "focus:not-sr-only focus:fixed focus:top-4 focus:left-4",
                "inline-flex items-center gap-2 px-4 py-2.5 rounded-xl font-semibold text-sm",
                "bg-amber-500 text-stone-950 dark:bg-amber-400 dark:text-stone-950",
                "border-2 border-stone-950/20 dark:border-stone-900/30",
                "shadow-2xl ring-4 ring-amber-400/50 outline-none",
                "transition-all duration-150 hover:bg-amber-400 dark:hover:bg-amber-300",
                "active:scale-95",
              )}
            >
              <ArrowDown className="w-4 h-4 text-stone-950 animate-bounce" aria-hidden="true" />
              <span>{item.label}</span>
              <kbd className="hidden sm:inline-flex items-center gap-0.5 px-1.5 py-0.5 text-[10px] font-mono font-bold bg-stone-950/15 rounded border border-stone-950/20">
                <CornerDownLeft className="w-2.5 h-2.5" />
                Enter
              </kbd>
            </a>
          </li>
        ))}
      </ul>
    </nav>
  );
}
