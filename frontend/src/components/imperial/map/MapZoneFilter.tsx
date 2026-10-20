"use client";

import React from "react";
import { cn } from "@/lib/utils";
import type { ImperialZone } from "@/lib/imperial/map-types";
import { announceMapNavigation } from "@/lib/imperial/a11y-utils";

export interface MapZoneFilterProps {
  zones: ImperialZone[];
  selectedZoneSlug: string | null;
  onSelectZone: (zoneSlug: string | null) => void;
  countsByZone: Record<string, number>;
  totalCount: number;
  className?: string;
}

const ZONE_THEMES: Record<
  string,
  {
    dotColor: string;
    activeBorder: string;
    activeBg: string;
    activeText: string;
  }
> = {
  "central-ceremonial-axis": {
    dotColor: "bg-red-500",
    activeBorder: "border-red-500/80",
    activeBg: "bg-red-950/40",
    activeText: "text-red-300",
  },
  "ancestral-worship-space": {
    dotColor: "bg-amber-500",
    activeBorder: "border-amber-500/80",
    activeBg: "bg-amber-950/40",
    activeText: "text-amber-300",
  },
  "purple-forbidden-city": {
    dotColor: "bg-purple-500",
    activeBorder: "border-purple-500/80",
    activeBg: "bg-purple-950/40",
    activeText: "text-purple-300",
  },
  "royal-living-gardens": {
    dotColor: "bg-emerald-500",
    activeBorder: "border-emerald-500/80",
    activeBg: "bg-emerald-950/40",
    activeText: "text-emerald-300",
  },
};

export function MapZoneFilter({
  zones,
  selectedZoneSlug,
  onSelectZone,
  countsByZone,
  totalCount,
  className,
}: MapZoneFilterProps) {
  return (
    <nav
      aria-label="Lọc phân khu Đại Nội"
      className={cn(
        "flex items-center gap-1.5 overflow-x-auto p-1.5 rounded-2xl bg-background/85 backdrop-blur-xl border border-border/80 shadow-lg no-scrollbar",
        className,
      )}
    >
      {/* "All" Chip */}
      <button
        type="button"
        onClick={() => {
          onSelectZone(null);
          announceMapNavigation("zone_filter", {
            zoneName: undefined,
            totalSites: totalCount,
          });
        }}
        aria-pressed={selectedZoneSlug === null}
        className={cn(
          "inline-flex items-center gap-2 px-3 py-1.5 rounded-xl text-xs font-medium transition-all whitespace-nowrap focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/50",
          selectedZoneSlug === null
            ? "bg-primary text-primary-foreground shadow-md font-semibold"
            : "text-muted-foreground hover:text-foreground hover:bg-secondary/60",
        )}
      >
        <span>Tất cả</span>
        <span
          className={cn(
            "inline-flex items-center justify-center px-1.5 py-0.2 rounded-full text-[10px] font-semibold",
            selectedZoneSlug === null
              ? "bg-primary-foreground/20 text-primary-foreground"
              : "bg-secondary text-muted-foreground",
          )}
        >
          {totalCount}
        </span>
      </button>

      {/* Zone Chips */}
      {zones.map((zone) => {
        const count = countsByZone[zone.slug] ?? 0;
        const isSelected = selectedZoneSlug === zone.slug;
        const theme = ZONE_THEMES[zone.slug] ?? {
          dotColor: "bg-primary",
          activeBorder: "border-primary",
          activeBg: "bg-primary/20",
          activeText: "text-primary",
        };

        return (
          <button
            key={zone.slug}
            type="button"
            onClick={() => {
              onSelectZone(zone.slug);
              announceMapNavigation("zone_filter", {
                zoneName: zone.title_vi,
                totalSites: count,
              });
            }}
            aria-pressed={isSelected}
            className={cn(
              "inline-flex items-center gap-2 px-3 py-1.5 rounded-xl text-xs font-medium transition-all whitespace-nowrap border focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/50",
              isSelected
                ? cn(
                    "shadow-sm font-semibold",
                    theme.activeBorder,
                    theme.activeBg,
                    theme.activeText,
                  )
                : "border-transparent text-muted-foreground hover:text-foreground hover:bg-secondary/60",
            )}
          >
            <span
              className={cn("w-2 h-2 rounded-full shrink-0", theme.dotColor)}
              aria-hidden="true"
            />
            <span>{zone.title_vi}</span>
            <span
              className={cn(
                "inline-flex items-center justify-center px-1.5 py-0.2 rounded-full text-[10px] font-semibold",
                isSelected
                  ? "bg-background/50 text-foreground"
                  : "bg-secondary text-muted-foreground",
              )}
            >
              {count}
            </span>
          </button>
        );
      })}
    </nav>
  );
}
