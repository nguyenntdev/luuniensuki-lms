"use client";

import { cn } from "@/lib/utils";

/**
 * Editorial section header: small uppercase kicker + heading + optional lead.
 * Matches the museum-editorial voice used across the history-first pages.
 */
export default function SectionHeading({
  kicker,
  title,
  lead,
  as: Tag = "h2",
  className,
}: {
  kicker?: string;
  title: string;
  lead?: string;
  as?: "h2" | "h3";
  className?: string;
}) {
  return (
    <div className={cn("max-w-3xl", className)}>
      {kicker ? (
        <p className="text-xs font-semibold uppercase tracking-[0.22em] text-primary">
          {kicker}
        </p>
      ) : null}
      <Tag className="mt-3 font-display text-2xl font-bold tracking-tight text-foreground md:text-3xl">
        {title}
      </Tag>
      {lead ? (
        <p className="mt-3 text-sm leading-7 text-muted-foreground md:text-base">
          {lead}
        </p>
      ) : null}
    </div>
  );
}