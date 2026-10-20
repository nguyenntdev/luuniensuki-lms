"use client";

import React from "react";
import Image from "next/image";
import {
  CheckCircle2,
  CameraOff,
  ChevronRight,
  ArrowRight,
  MapPin,
  Sparkles,
} from "lucide-react";
import { cn } from "@/lib/utils";
import type { ImperialTrailStop } from "@/lib/imperial/map-types";
import { getPrimaryHeritageImage } from "@/lib/imperial/heritage-images";
import { getSiteImageCompleteness } from "@/lib/imperial/image-completeness";

interface RouteJourneyStripProps {
  stops: ImperialTrailStop[];
  currentIndex: number;
  completedStops: number[];
  savedSubmissionsSlugs: string[];
  onSelectStop: (index: number) => void;
  className?: string;
}

export function RouteJourneyStrip({
  stops,
  currentIndex,
  completedStops,
  savedSubmissionsSlugs,
  onSelectStop,
  className = "",
}: RouteJourneyStripProps) {
  return (
    <div className={cn("space-y-3", className)}>
      <div className="flex items-center justify-between text-xs px-1">
        <div className="flex items-center gap-2">
          <span className="font-serif font-bold text-foreground flex items-center gap-1.5">
            <span className="h-2 w-2 rounded-full bg-primary animate-pulse" />
            Lộ trình khảo sát dọc trục Thần đạo (Nam ➔ Bắc):
          </span>
          <span className="text-muted-foreground hidden sm:inline">
            (Bấm trạm dừng để chuyển nhanh)
          </span>
        </div>
        <span className="font-mono text-[11px] text-muted-foreground">
          Trạm {currentIndex + 1} / {stops.length}
        </span>
      </div>

      {/* Horizontal Scrollable Track */}
      <div className="flex items-stretch gap-3 overflow-x-auto pb-2 scrollbar-thin">
        {stops.map((stop, idx) => {
          const isActive = idx === currentIndex;
          const isDone =
            completedStops.includes(idx) ||
            savedSubmissionsSlugs.includes(stop.monument_slug);

          // Get primary verified photo for this stop
          const primaryImg = getPrimaryHeritageImage(stop.monument_slug);
          const completeness = getSiteImageCompleteness(stop.monument_slug);

          return (
            <button
              key={stop.monument_slug}
              type="button"
              onClick={() => onSelectStop(idx)}
              className={cn(
                "group relative flex shrink-0 w-64 flex-col overflow-hidden rounded-2xl border text-left transition-all duration-200 select-none",
                isActive
                  ? "border-primary bg-card ring-2 ring-primary/40 shadow-md scale-[1.02]"
                  : isDone
                  ? "border-emerald-500/40 bg-card hover:border-emerald-500/60 shadow-xs"
                  : "border-border/70 bg-card/60 hover:bg-card hover:border-border shadow-2xs",
              )}
            >
              {/* Image Preview Container */}
              <div className="relative aspect-[16/9] w-full overflow-hidden bg-neutral-950">
                {primaryImg ? (
                  <>
                    <Image
                      src={primaryImg.src}
                      alt={primaryImg.alt || stop.monument_name_vi}
                      fill
                      className="object-cover group-hover:scale-105 transition-transform duration-300"
                      sizes="260px"
                    />
                    <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-black/20 to-transparent pointer-events-none" />
                  </>
                ) : (
                  /* Graceful Missing Image Placeholder with Historic Texture */
                  <div className="absolute inset-0 flex flex-col items-center justify-center p-3 text-center bg-gradient-to-br from-stone-900 via-neutral-900 to-stone-900">
                    <CameraOff className="h-6 w-6 text-amber-500/60 mb-1" />
                    <span className="text-[10px] font-semibold text-amber-300">
                      Chưa có ảnh thực tế
                    </span>
                    <span className="text-[9px] text-stone-400 line-clamp-1 mt-0.5">
                      {stop.monument_slug === "dien-can-chanh"
                        ? "Phế tích bom đạn 1947"
                        : "Đang cập nhật tư liệu"}
                    </span>
                  </div>
                )}

                {/* Top Badge: Stop Number & Status */}
                <div className="absolute top-2 left-2 flex items-center gap-1.5">
                  <span
                    className={cn(
                      "flex h-5 w-5 items-center justify-center rounded-full text-[11px] font-bold shadow",
                      isActive
                        ? "bg-primary text-primary-foreground"
                        : isDone
                        ? "bg-emerald-600 text-white"
                        : "bg-black/75 text-white/90 backdrop-blur-md",
                    )}
                  >
                    {isDone ? <CheckCircle2 className="h-3 w-3" /> : idx + 1}
                  </span>
                  <span className="rounded bg-black/70 backdrop-blur-md px-1.5 py-0.5 text-[9px] font-mono text-white/90">
                    Trạm {idx + 1}
                  </span>
                </div>

                {/* Top Right: Completeness Pill */}
                <div className="absolute top-2 right-2">
                  <span
                    className={cn(
                      "rounded-full px-2 py-0.5 text-[9px] font-semibold backdrop-blur-md shadow",
                      completeness.status === "complete"
                        ? "bg-emerald-500/80 text-white"
                        : completeness.status === "partial"
                        ? "bg-amber-500/80 text-white"
                        : "bg-red-500/80 text-white",
                    )}
                  >
                    {completeness.status === "complete"
                      ? `${completeness.totalImages} ảnh`
                      : completeness.status === "partial"
                      ? "1 ảnh"
                      : "Thiếu ảnh"}
                  </span>
                </div>

                {/* Bottom Overlay on Image: Name */}
                <div className="absolute bottom-2 left-2.5 right-2.5 text-white pointer-events-none">
                  <h3 className="font-serif text-sm font-bold text-white line-clamp-1 drop-shadow">
                    {stop.monument_name_vi}
                  </h3>
                </div>
              </div>

              {/* Stop Meta & Task hint below image */}
              <div className="p-3 space-y-1.5 flex flex-col justify-between flex-1">
                <p className="text-[11px] font-medium text-foreground line-clamp-1">
                  {stop.title.replace(/^Trạm \d+: /, "")}
                </p>

                <div className="flex items-center justify-between text-[10px] text-muted-foreground pt-1 border-t border-border/40">
                  <span className="truncate max-w-[140px]">
                    {stop.inquiry_question.slice(0, 32)}...
                  </span>
                  <span
                    className={cn(
                      "font-semibold shrink-0",
                      isDone
                        ? "text-emerald-600 dark:text-emerald-400"
                        : isActive
                        ? "text-primary"
                        : "text-muted-foreground",
                    )}
                  >
                    {isDone ? "Đã nộp M-E-E" : isActive ? "Đang khảo sát" : "Chưa làm"}
                  </span>
                </div>
              </div>
            </button>
          );
        })}
      </div>
    </div>
  );
}
