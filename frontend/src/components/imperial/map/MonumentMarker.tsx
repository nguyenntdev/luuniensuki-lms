"use client";

import React, { memo } from "react";
import {
  Landmark,
  Crown,
  Flame,
  Compass,
  Hammer,
  Route as BridgeIcon,
  Home,
  AlertCircle,
  HelpCircle,
} from "lucide-react";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import type { ImperialMapAnnotation, ImperialSiteCondition, LearningLevel } from "@/lib/imperial/map-types";

export interface MonumentMarkerProps {
  annotation: ImperialMapAnnotation;
  isSelected?: boolean;
  isDimmed?: boolean;
  showLabel?: boolean;
  scale?: number;
  onClick?: (annotation: ImperialMapAnnotation) => void;
}

/**
 * Returns icon component matching marker style.
 */
function getMarkerIcon(style: string) {
  const s = style.toLowerCase();
  if (s.includes("gate")) return Landmark;
  if (s.includes("palace") || s.includes("court") || s.includes("primary")) return Crown;
  if (s.includes("temple") || s.includes("altar")) return Flame;
  if (s.includes("pavilion") || s.includes("library") || s.includes("theater")) return Compass;
  if (s.includes("ruin") || s.includes("foundation")) return Hammer;
  if (s.includes("bridge")) return BridgeIcon;
  if (s.includes("residence") || s.includes("garden")) return Home;
  return Landmark;
}

/**
 * Returns color classes matching spatial zone.
 */
function getZoneColor(zoneSlug?: string) {
  switch (zoneSlug) {
    case "central-ceremonial-axis":
      return {
        bg: "bg-gradient-to-tr from-red-600 via-rose-600 to-amber-500",
        border: "border-red-300",
        ring: "ring-red-400/50",
        glow: "shadow-[0_0_18px_rgba(220,38,38,0.7)]",
        badge: "bg-red-500/15 text-red-300 border-red-500/30",
        labelBg: "bg-red-950/90 text-red-100 border-red-700/60",
      };
    case "ancestral-worship-space":
      return {
        bg: "bg-gradient-to-tr from-amber-600 via-yellow-600 to-orange-400",
        border: "border-amber-300",
        ring: "ring-amber-400/50",
        glow: "shadow-[0_0_18px_rgba(217,119,6,0.7)]",
        badge: "bg-amber-500/15 text-amber-300 border-amber-500/30",
        labelBg: "bg-amber-950/90 text-amber-100 border-amber-700/60",
      };
    case "purple-forbidden-city":
      return {
        bg: "bg-gradient-to-tr from-purple-700 via-violet-600 to-fuchsia-500",
        border: "border-purple-300",
        ring: "ring-purple-400/50",
        glow: "shadow-[0_0_18px_rgba(124,58,237,0.7)]",
        badge: "bg-purple-500/15 text-purple-300 border-purple-500/30",
        labelBg: "bg-purple-950/90 text-purple-100 border-purple-700/60",
      };
    case "royal-living-gardens":
      return {
        bg: "bg-gradient-to-tr from-emerald-600 via-teal-600 to-cyan-500",
        border: "border-emerald-300",
        ring: "ring-emerald-400/50",
        glow: "shadow-[0_0_18px_rgba(5,150,105,0.7)]",
        badge: "bg-emerald-500/15 text-emerald-300 border-emerald-500/30",
        labelBg: "bg-emerald-950/90 text-emerald-100 border-emerald-700/60",
      };
    default:
      return {
        bg: "bg-gradient-to-tr from-stone-600 via-zinc-600 to-stone-400",
        border: "border-stone-300",
        ring: "ring-stone-400/50",
        glow: "shadow-[0_0_14px_rgba(120,113,108,0.5)]",
        badge: "bg-stone-500/15 text-stone-300 border-stone-500/30",
        labelBg: "bg-stone-900/90 text-stone-100 border-stone-700/60",
      };
  }
}

function getConditionLabel(condition?: ImperialSiteCondition) {
  switch (condition) {
    case "extant":
      return "Nguyên vẹn";
    case "ruin":
      return "Phế tích / Nền móng";
    case "reconstructed":
      return "Đã phục dựng";
    case "archaeological":
      return "Khảo cổ học";
    case "lost":
      return "Đã mất dấu";
    default:
      return "Di tích";
  }
}

function getLevelLabel(level?: LearningLevel) {
  switch (level) {
    case "L1_DOCUMENTED":
      return "Cấp 1: Tư liệu hóa";
    case "L2_ANALYZED":
      return "Cấp 2: Phân tích tư liệu";
    case "L3_SYNTHESIZED":
      return "Cấp 3: Tổng hợp chuyên sâu";
    default:
      return "Đã xác thực";
  }
}

export const MonumentMarker = memo(function MonumentMarker({
  annotation,
  isSelected = false,
  isDimmed = false,
  showLabel = true,
  scale = 1.0,
  onClick,
}: MonumentMarkerProps) {
  const IconComponent = getMarkerIcon(annotation.marker_style);
  const zoneColors = getZoneColor(annotation.site?.zone_slug);
  const nameVi = annotation.site?.name_vi || annotation.label || "Công trình";
  const hanNom = annotation.site?.name_han_nom || annotation.site?.chinese_name;

  // Counter-scale factor so pin optical size stays comfortably readable across zooms
  // Clamped between 0.65 and 1.35
  const counterScale = Math.min(Math.max(1 / (scale ** 0.65 || 1), 0.65), 1.35);

  const handleClick = (e: React.MouseEvent) => {
    e.stopPropagation();
    onClick?.(annotation);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" || e.key === " ") {
      e.preventDefault();
      e.stopPropagation();
      onClick?.(annotation);
    }
  };

  return (
    <div
      className={cn(
        "absolute z-20 pointer-events-auto transition-opacity duration-200 select-none",
        isDimmed && "opacity-25 hover:opacity-90",
        isSelected && "z-30",
      )}
      style={{
        left: `${annotation.u * 100}%`,
        top: `${annotation.v * 100}%`,
      }}
    >
      <TooltipProvider delayDuration={150}>
        <Tooltip>
          <TooltipTrigger asChild>
            <button
              type="button"
              role="button"
              tabIndex={0}
              aria-label={`${nameVi}${hanNom ? ` (${hanNom})` : ""}`}
              onClick={handleClick}
              onKeyDown={handleKeyDown}
              style={{
                transform: `translate(-50%, -100%) scale(${counterScale})`,
                transformOrigin: "bottom center",
              }}
              className="relative flex flex-col items-center group cursor-pointer focus-visible:outline-none"
            >
              {/* Selected Pulse Wave */}
              {isSelected && (
                <span className="absolute -inset-2.5 rounded-full animate-ping bg-amber-400/40 opacity-75 pointer-events-none" />
              )}

              {/* Pin Head */}
              <div
                className={cn(
                  "relative flex items-center justify-center w-8 h-8 rounded-full border-2 text-white shadow-xl transition-transform duration-200 group-hover:scale-110",
                  zoneColors.bg,
                  zoneColors.border,
                  isSelected && "ring-4 ring-offset-2 ring-offset-background ring-amber-400 scale-110 " + zoneColors.glow,
                )}
              >
                <IconComponent className="w-4 h-4 stroke-[2.2] drop-shadow-sm" />

                {/* Status Dot */}
                {annotation.position_confidence === "verified" ? (
                  <span className="absolute -top-0.5 -right-0.5 w-2.5 h-2.5 bg-emerald-400 border border-emerald-950 rounded-full shadow-sm" />
                ) : (
                  <span className="absolute -top-0.5 -right-0.5 w-2.5 h-2.5 bg-amber-400 border border-amber-950 rounded-full shadow-sm" />
                )}
              </div>

              {/* Pin Point Tip */}
              <div
                className={cn(
                  "w-0 h-0 border-l-[5px] border-l-transparent border-r-[5px] border-r-transparent border-t-[7px] -mt-0.5 transition-transform duration-200 group-hover:translate-y-0.5",
                  annotation.site?.zone_slug === "central-ceremonial-axis"
                    ? "border-t-rose-600"
                    : annotation.site?.zone_slug === "ancestral-worship-space"
                      ? "border-t-amber-600"
                      : annotation.site?.zone_slug === "purple-forbidden-city"
                        ? "border-t-purple-600"
                        : annotation.site?.zone_slug === "royal-living-gardens"
                          ? "border-t-emerald-600"
                          : "border-t-stone-600",
                )}
              />

              {/* Static Anchor Dot on Image Plane */}
              <div className="w-1.5 h-1.5 rounded-full bg-amber-400/90 ring-2 ring-black/80 mt-0.5 shadow-sm" />

              {/* Floating Name Label */}
              {showLabel && (
                <div
                  className={cn(
                    "mt-1 px-2 py-0.5 rounded-md text-[11px] font-medium tracking-tight whitespace-nowrap backdrop-blur-md border shadow-lg transition-all duration-150 group-hover:scale-105 pointer-events-none",
                    zoneColors.labelBg,
                    isSelected ? "ring-2 ring-amber-400 font-semibold" : "opacity-90",
                  )}
                >
                  <span>{nameVi}</span>
                  {hanNom && (
                    <span className="ml-1 opacity-70 font-serif text-[10px]">
                      ({hanNom})
                    </span>
                  )}
                </div>
              )}
            </button>
          </TooltipTrigger>

          {/* Hover Tooltip Card */}
          <TooltipContent
            side="top"
            sideOffset={8}
            className="z-50 max-w-xs p-3.5 bg-card/95 text-card-foreground border border-border/80 rounded-xl shadow-2xl backdrop-blur-xl animate-in fade-in-0 zoom-in-95"
          >
            <div className="space-y-2">
              <div className="flex items-start justify-between gap-2">
                <div>
                  <h4 className="text-sm font-bold tracking-tight text-foreground flex items-center gap-1.5">
                    {nameVi}
                    {hanNom && (
                      <span className="text-amber-500 font-serif font-normal">
                        {hanNom}
                      </span>
                    )}
                  </h4>
                  <p className="text-[11px] text-muted-foreground mt-0.5">
                    {getConditionLabel(annotation.site?.condition)}
                  </p>
                </div>
                <Badge
                  variant="outline"
                  className={cn("text-[10px] px-1.5 py-0 font-medium shrink-0", zoneColors.badge)}
                >
                  {annotation.position_confidence === "verified" ? "Đã thẩm định" : "Ước lượng"}
                </Badge>
              </div>

              {annotation.site?.summary_vi && (
                <p className="text-xs text-foreground/85 line-clamp-2 leading-relaxed">
                  {annotation.site.summary_vi}
                </p>
              )}

              <div className="flex items-center justify-between pt-1 border-t border-border/50 text-[10px] text-muted-foreground">
                <span className="text-primary font-medium">
                  {getLevelLabel(annotation.site?.learning_level)}
                </span>
                <span className="font-semibold text-primary/90 flex items-center gap-0.5">
                  Chi tiết &rarr;
                </span>
              </div>
            </div>
          </TooltipContent>
        </Tooltip>
      </TooltipProvider>
    </div>
  );
});
