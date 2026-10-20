"use client";

import React, { memo, useRef } from "react";
import {
  Compass,
  Crown,
  Flame,
  Hammer,
  HelpCircle,
  Home,
  Landmark,
  Route as BridgeIcon,
} from "lucide-react";
import { cn } from "@/lib/utils";
import type { ImperialMapAnnotation } from "@/lib/imperial/map-types";

export interface StudioMarkerProps {
  annotation: ImperialMapAnnotation;
  isSelected: boolean;
  scale: number;
  interactiveMode: "SELECT" | "ADD_POINT" | "PAN" | "DELETE";
  onSelect: (annotation: ImperialMapAnnotation) => void;
  onDragStart: (
    annotation: ImperialMapAnnotation,
    e: React.PointerEvent<HTMLDivElement>,
  ) => void;
  onDelete: (annotation: ImperialMapAnnotation) => void;
}

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

export const StudioMarker = memo(function StudioMarker({
  annotation,
  isSelected,
  scale,
  interactiveMode,
  onSelect,
  onDragStart,
  onDelete,
}: StudioMarkerProps) {
  const IconComponent = getMarkerIcon(annotation.marker_style);
  const nameVi = annotation.label || annotation.site?.name_vi || "Điểm ghim";

  // Optical counter-scale
  const counterScale = Math.min(Math.max(1 / (scale ** 0.65 || 1), 0.65), 1.35);

  const isDraft = annotation.review_status === "draft";

  const handlePointerDown = (e: React.PointerEvent<HTMLDivElement>) => {
    e.stopPropagation();

    if (interactiveMode === "DELETE") {
      onDelete(annotation);
      return;
    }

    if (interactiveMode === "SELECT") {
      onSelect(annotation);
      onDragStart(annotation, e);
    }
  };

  return (
    <div
      role="button"
      tabIndex={0}
      aria-label={nameVi}
      onPointerDown={handlePointerDown}
      className={cn(
        "absolute z-20 pointer-events-auto select-none transition-transform duration-75",
        isSelected && "z-30",
        interactiveMode === "SELECT" && "cursor-grab active:cursor-grabbing",
        interactiveMode === "DELETE" && "cursor-pointer hover:scale-110",
      )}
      style={{
        left: `${annotation.u * 100}%`,
        top: `${annotation.v * 100}%`,
        transform: `translate(-50%, -100%) scale(${counterScale})`,
        transformOrigin: "bottom center",
      }}
    >
      {/* Selection Glow Indicator */}
      {isSelected && (
        <span className="absolute -inset-2.5 rounded-full animate-ping bg-primary/40 opacity-75 pointer-events-none" />
      )}

      {/* Pin Body */}
      <div
        className={cn(
          "relative flex items-center justify-center w-8 h-8 rounded-full border-2 text-white shadow-xl transition-all",
          isDraft
            ? "bg-amber-600 border-amber-300 ring-amber-400"
            : "bg-emerald-600 border-emerald-300 ring-emerald-400",
          isSelected
            ? "ring-4 ring-offset-2 ring-offset-background ring-primary scale-110 shadow-[0_0_20px_rgba(245,158,11,0.8)]"
            : "hover:scale-105",
        )}
      >
        <IconComponent className="w-4 h-4 stroke-[2.2]" />

        {/* Draft Tag */}
        {isDraft && (
          <span
            className="absolute -top-1 -right-1 w-2.5 h-2.5 bg-amber-400 border border-stone-900 rounded-full"
            title="Bản nháp"
          />
        )}
      </div>

      {/* Pin Tip */}
      <div
        className={cn(
          "w-0 h-0 border-l-[5px] border-l-transparent border-r-[5px] border-r-transparent border-t-[7px] -mt-0.5 mx-auto",
          isDraft ? "border-t-amber-600" : "border-t-emerald-600",
        )}
      />

      {/* Anchor point */}
      <div className="w-1.5 h-1.5 rounded-full bg-amber-400 ring-2 ring-black mx-auto mt-0.5" />

      {/* Studio Label with Row Version */}
      <div
        className={cn(
          "mt-1 px-1.5 py-0.5 rounded text-[10px] font-medium tracking-tight whitespace-nowrap shadow-md pointer-events-none border text-center",
          isSelected
            ? "bg-primary text-primary-foreground border-primary-foreground/30 font-bold"
            : "bg-card/90 text-foreground border-border/80",
        )}
      >
        <span>{nameVi}</span>
        {annotation.row_version > 1 && (
          <span className="ml-1 opacity-70 font-mono text-[9px]">
            v{annotation.row_version}
          </span>
        )}
      </div>
    </div>
  );
});
