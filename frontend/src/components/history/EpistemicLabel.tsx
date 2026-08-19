"use client";

import {
  ShieldCheck,
  BookOpen,
  ScrollText,
  HelpCircle,
  AlertTriangle,
  Clock,
} from "lucide-react";
import { cn } from "@/lib/utils";
import type { EpistemicInfo } from "@/lib/history";

const TONE_CLASSES: Record<EpistemicInfo["tone"], string> = {
  documented: "border-success/30 bg-success/10 text-success",
  interpretation: "border-primary/30 bg-primary/10 text-primary",
  traditional: "border-warning/30 bg-warning/10 text-warning",
  uncertain: "border-border/70 bg-secondary/60 text-muted-foreground",
  disputed: "border-destructive/30 bg-destructive/10 text-destructive",
  unreviewed: "border-border/70 bg-secondary/60 text-muted-foreground",
};

function EpistemicIcon({ tone }: { tone: EpistemicInfo["tone"] }) {
  switch (tone) {
    case "documented":
      return <ShieldCheck className="h-3 w-3 shrink-0" aria-hidden="true" />;
    case "interpretation":
      return <BookOpen className="h-3 w-3 shrink-0" aria-hidden="true" />;
    case "traditional":
      return <ScrollText className="h-3 w-3 shrink-0" aria-hidden="true" />;
    case "uncertain":
      return <HelpCircle className="h-3 w-3 shrink-0" aria-hidden="true" />;
    case "disputed":
      return <AlertTriangle className="h-3 w-3 shrink-0" aria-hidden="true" />;
    default:
      return <Clock className="h-3 w-3 shrink-0" aria-hidden="true" />;
  }
}

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
      <EpistemicIcon tone={info.tone} />
      <span>{info.label}</span>
    </span>
  );
}
