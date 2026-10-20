"use client";

import React, { useState } from "react";
import Image from "next/image";
import Link from "next/link";
import {
  Compass,
  Landmark,
  MapPin,
  ExternalLink,
  ChevronLeft,
  ChevronRight,
  Sparkles,
  CameraOff,
  Calendar,
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { FALLBACK_SITES, FALLBACK_ZONES } from "@/lib/imperial/fallback-data";
import { getPrimaryHeritageImage, HERITAGE_IMAGE_TYPES } from "@/lib/imperial/heritage-images";
import { getSiteImageCompleteness } from "@/lib/imperial/image-completeness";

interface MonumentVisualCarouselProps {
  onSelectMonument?: (slug: string) => void;
  selectedSlug?: string | null;
  className?: string;
}

export function MonumentVisualCarousel({
  onSelectMonument,
  selectedSlug,
  className = "",
}: MonumentVisualCarouselProps) {
  const [selectedZone, setSelectedZone] = useState<string>("all");

  const filteredSites = FALLBACK_SITES.filter((site) => {
    if (selectedZone !== "all" && site.zone_slug !== selectedZone) return false;
    return true;
  });

  return (
    <section
      aria-label="Khám phá nhanh hình ảnh di tích Hoàng Thành"
      className={cn("space-y-4", className)}
    >
      {/* Header and Zone Filter Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-border/70 pb-3">
        <div className="flex items-center gap-2.5">
          <div className="flex h-8 w-8 items-center justify-center rounded-xl bg-primary/15 text-primary">
            <Landmark className="h-4 w-4" />
          </div>
          <div>
            <h2 className="font-serif text-lg sm:text-xl font-bold text-foreground">
              Khám phá thị giác 16 di tích Hoàng Thành
            </h2>
            <p className="text-xs text-muted-foreground">
              Lướt xem ảnh thực tế & bấm để bay tới vị trí định vị trên bản đồ không ảnh
            </p>
          </div>
        </div>

        {/* Zone Filter Buttons */}
        <div className="flex items-center gap-1.5 overflow-x-auto pb-1 scrollbar-thin">
          <button
            type="button"
            onClick={() => setSelectedZone("all")}
            className={cn(
              "px-3 py-1 rounded-full text-xs font-semibold transition-all whitespace-nowrap border",
              selectedZone === "all"
                ? "bg-[#851C1C] text-white border-[#851C1C] shadow-sm"
                : "bg-secondary/60 text-muted-foreground border-border/60 hover:text-foreground",
            )}
          >
            Tất cả ({FALLBACK_SITES.length})
          </button>
          {FALLBACK_ZONES.map((zone) => {
            const count = FALLBACK_SITES.filter((s) => s.zone_slug === zone.slug).length;
            const isZoneActive = selectedZone === zone.slug;

            return (
              <button
                key={zone.slug}
                type="button"
                onClick={() => setSelectedZone(zone.slug)}
                className={cn(
                  "px-3 py-1 rounded-full text-xs font-semibold transition-all whitespace-nowrap border flex items-center gap-1.5",
                  isZoneActive
                    ? "bg-[#851C1C] text-white border-[#851C1C] shadow-sm"
                    : "bg-secondary/60 text-muted-foreground border-border/60 hover:text-foreground",
                )}
              >
                <span>{zone.title_vi}</span>
                <span className="opacity-70 text-[10px]">({count})</span>
              </button>
            );
          })}
        </div>
      </div>

      {/* Horizontal Carousel Track */}
      <div className="flex items-stretch gap-4 overflow-x-auto pb-3 pt-1 scrollbar-thin">
        {filteredSites.map((site) => {
          const isSelected = selectedSlug === site.slug;
          const heritageImg = getPrimaryHeritageImage(site.slug);
          const completeness = getSiteImageCompleteness(site.slug);
          const zone = FALLBACK_ZONES.find((z) => z.slug === site.zone_slug);

          return (
            <div
              key={site.slug}
              className={cn(
                "group relative flex shrink-0 w-72 sm:w-80 flex-col overflow-hidden rounded-2xl border text-left transition-all duration-300 bg-card select-none shadow-sm",
                isSelected
                  ? "border-primary ring-2 ring-primary/50 shadow-lg scale-[1.02]"
                  : "border-border/70 hover:border-primary/40 hover:shadow-md",
              )}
            >
              {/* Image Container */}
              <div
                className="relative aspect-[16/10] w-full overflow-hidden bg-neutral-950 cursor-pointer"
                onClick={() => onSelectMonument?.(site.slug)}
                role="button"
                tabIndex={0}
                onKeyDown={(e) => e.key === "Enter" && onSelectMonument?.(site.slug)}
                title={`Bấm để định vị ${site.name_vi} trên bản đồ`}
              >
                {heritageImg ? (
                  <>
                    <Image
                      src={heritageImg.src}
                      alt={heritageImg.alt || site.name_vi}
                      fill
                      className="object-cover group-hover:scale-105 transition-transform duration-500"
                      sizes="320px"
                    />
                    <div className="absolute inset-0 bg-gradient-to-t from-black/85 via-black/20 to-transparent pointer-events-none" />
                  </>
                ) : (
                  <div className="absolute inset-0 flex flex-col items-center justify-center p-4 text-center bg-gradient-to-br from-[#2C1A14] via-neutral-900 to-[#1A1612]">
                    <CameraOff className="h-7 w-7 text-amber-500/70 mb-1" />
                    <span className="text-xs font-semibold text-amber-300">
                      Chưa có ảnh thực tế
                    </span>
                    <span className="text-[10px] text-stone-400 mt-0.5 line-clamp-1">
                      {site.condition === "ruin" || site.condition === "archaeological"
                        ? "Dấu tích phế tích chiến tranh"
                        : "Đang cập nhật hồ sơ"}
                    </span>
                  </div>
                )}

                {/* Top Badges */}
                <div className="absolute top-2.5 left-2.5 flex items-center gap-1.5 z-10">
                  <span className="rounded-md bg-black/75 backdrop-blur-md px-2 py-0.5 text-[10px] font-semibold text-white shadow border border-white/10">
                    {zone?.title_vi || "Hoàng Thành"}
                  </span>
                </div>

                <div className="absolute top-2.5 right-2.5 z-10">
                  <span
                    className={cn(
                      "rounded-full px-2 py-0.5 text-[9px] font-bold shadow backdrop-blur-md",
                      completeness.status === "complete"
                        ? "bg-emerald-600/90 text-white"
                        : completeness.status === "partial"
                        ? "bg-amber-600/90 text-white"
                        : "bg-red-600/90 text-white",
                    )}
                  >
                    {completeness.status === "complete"
                      ? `${completeness.totalImages} ảnh`
                      : completeness.status === "partial"
                      ? "1 ảnh"
                      : "Thiếu ảnh"}
                  </span>
                </div>

                {/* Bottom Overlay Info on Image */}
                <div className="absolute bottom-2.5 left-3 right-3 text-white pointer-events-none z-10">
                  <h3 className="font-serif text-base font-bold text-white drop-shadow line-clamp-1">
                    {site.name_vi}
                  </h3>
                  <div className="flex items-center gap-2 text-[10px] text-amber-300 font-mono mt-0.5">
                    <Calendar className="h-3 w-3 shrink-0" />
                    <span>
                      {site.construction_year ? `Năm ${site.construction_year}` : "Triều Nguyễn"}
                      {site.reign ? ` • ${site.reign}` : ""}
                    </span>
                  </div>
                </div>
              </div>

              {/* Card Bottom Meta & Actions */}
              <div className="p-3.5 space-y-2.5 flex flex-col justify-between flex-1">
                <p className="text-xs text-muted-foreground line-clamp-2 leading-relaxed">
                  {site.historical_summary || site.description_vi}
                </p>

                <div className="flex items-center justify-between pt-2 border-t border-border/50 text-xs">
                  <button
                    type="button"
                    onClick={() => onSelectMonument?.(site.slug)}
                    className="inline-flex items-center gap-1 text-[11px] font-bold text-primary hover:underline"
                  >
                    <Compass className="h-3.5 w-3.5" />
                    <span>Định vị trên bản đồ</span>
                  </button>

                  <Link
                    href={`/dai-noi/cong-trinh/${site.slug}`}
                    className="inline-flex items-center gap-1 text-[11px] font-medium text-muted-foreground hover:text-foreground"
                  >
                    <span>Xem hồ sơ</span>
                    <ExternalLink className="h-3 w-3" />
                  </Link>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </section>
  );
}
