"use client";

import { cn } from "@/lib/utils";
import type { EpistemicInfo } from "@/lib/history";

const TONE_CLASSES: Record<EpistemicInfo["tone"], string> = {
  documented:
    "border-success/30 bg-success/10 text-success",
  interpretation:
    "border-primary/30 bg-primary/10 text-primary",
  traditional:
    "border-warning/30 bg-warning/10 text-warning",
  uncertain:
    "border-border/70 bg-secondary/60 text-muted-foreground",
  disputed:
    "border-destructive/30 bg-destructive/10 text-destructive",
  unreviewed:
    "border-border/70 bg-secondary/60 text-muted-foreground",
};

export default function EpistemicLabel({
  info,
  className,
}: {
  info: EpistemicInfo;
  className?: string;
}) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-[11px] font-semibold tracking-wide uppercase",
        TONE_CLASSES[info.tone] || TONE_CLASSES.unreviewed,
        className,
      )}
    >
      <span
        aria-hidden="true"
        className={cn(
          "h-1.5 w-1.5 rounded-full",
          info.tone === "documented"
            ? "bg-success"
            : info.tone === "interpretation"
              ? "bg-primary"
              : info.tone === "traditional"
                ? "bg-warning"
                : info.tone === "disputed"
                  ? "bg-destructive"
                  : "bg-muted-foreground",
        )}
      />
      {info.label}
    </span>
  );
}