"use client";

import React, { useState } from "react";
import Link from "next/link";
import {
  Landmark,
  Crown,
  Hammer,
  Music,
  Mountain,
  Sparkles,
  BookOpen,
  Utensils,
  Box,
  ShieldCheck,
  Award,
  ChevronRight,
  Clock,
  MapPin,
  CheckCircle2,
  Wrench,
  AlertCircle,
} from "lucide-react";
import type { LucideIcon } from "lucide-react";
import type { HeritagePlace, HeritageCategory } from "@/types/heritage";
import { getEpistemicBadgeCopy, type RbpcLocale } from "@/lib/rbpc/copy";
import { cn } from "@/lib/utils";

export interface HeritageCardProps {
  place: HeritagePlace;
  locale?: RbpcLocale;
  priority?: boolean;
  className?: string;
  onClick?: (place: HeritagePlace) => void;
}

interface CategoryDisplayInfo {
  labelVi: string;
  labelEn: string;
  icon: LucideIcon;
  badgeStyle: string;
}

const CATEGORY_MAP: Record<string, CategoryDisplayInfo> = {
  imperial_architecture: {
    labelVi: "Kiến trúc Cung đình",
    labelEn: "Imperial Architecture",
    icon: Landmark,
    badgeStyle:
      "border-amber-700/30 bg-amber-500/10 text-amber-900 dark:text-amber-300",
  },
  royal_tomb: {
    labelVi: "Lăng tẩm Hoàng gia",
    labelEn: "Royal Tomb",
    icon: Crown,
    badgeStyle:
      "border-purple-700/30 bg-purple-500/10 text-purple-900 dark:text-purple-300",
  },
  craft_living_culture: {
    labelVi: "Làng nghề thủ công",
    labelEn: "Living Craft",
    icon: Hammer,
    badgeStyle:
      "border-emerald-700/30 bg-emerald-500/10 text-emerald-900 dark:text-emerald-300",
  },
  music_performance: {
    labelVi: "Âm nhạc & Diễn xướng",
    labelEn: "Performing Arts",
    icon: Music,
    badgeStyle:
      "border-rose-700/30 bg-rose-500/10 text-rose-900 dark:text-rose-300",
  },
  landscape_nature: {
    labelVi: "Danh thắng & Cảnh quan",
    labelEn: "Landscape & Nature",
    icon: Mountain,
    badgeStyle:
      "border-teal-700/30 bg-teal-500/10 text-teal-900 dark:text-teal-300",
  },
  religious_spiritual: {
    labelVi: "Tín ngưỡng & Tôn giáo",
    labelEn: "Sacred & Spiritual",
    icon: Sparkles,
    badgeStyle:
      "border-indigo-700/30 bg-indigo-500/10 text-indigo-900 dark:text-indigo-300",
  },
  museum_archive: {
    labelVi: "Bảo tàng & Di sản tư liệu",
    labelEn: "Museum & Archive",
    icon: BookOpen,
    badgeStyle:
      "border-blue-700/30 bg-blue-500/10 text-blue-900 dark:text-blue-300",
  },
  culinary_heritage: {
    labelVi: "Ẩm thực Di sản",
    labelEn: "Culinary Heritage",
    icon: Utensils,
    badgeStyle:
      "border-orange-700/30 bg-orange-500/10 text-orange-900 dark:text-orange-300",
  },
};

/**
 * HeritageCard Component
 * Implements the contemporary editorial card specification:
 * - 16:10 aspect ratio image container with fallback
 * - Prominent serif title + English subtitle
 * - Category badge with icon
 * - UNESCO Reference ID badge (678-xxx)
 * - Short visitor/historical summary (line clamped)
 * - Epistemic certainty badge
 * - 3D scan indicator if available
 */
export default function HeritageCard({
  place,
  locale = "vi",
  priority = false,
  className,
  onClick,
}: HeritageCardProps) {
  const [imgError, setImgError] = useState(false);

  const categoryInfo =
    CATEGORY_MAP[place.heritage_category] || {
      labelVi: "Di tích & Di sản",
      labelEn: "Heritage Site",
      icon: Landmark,
      badgeStyle: "border-border bg-muted/60 text-muted-foreground",
    };

  const CategoryIcon = categoryInfo.icon;
  const categoryLabel =
    locale === "vi" ? categoryInfo.labelVi : categoryInfo.labelEn;

  // UNESCO Reference ID detection
  const isUnesco = Boolean(
    place.official_reference_id?.startsWith("678") ||
      place.official_designation?.toLowerCase().includes("unesco")
  );
  const unescoRef = place.official_reference_id || "678-UNESCO";

  // Epistemic certainty item lookup
  const epistemicStatusId =
    place.heritage_category === "craft_living_culture"
      ? "living_tradition"
      : place.editorial_status === "published" ||
        place.editorial_status === "source_backed" ||
        place.editorial_status === "approved"
      ? "verified_source"
      : "academic_interpretation";

  const epistemicCopy = getEpistemicBadgeCopy(epistemicStatusId, locale);

  // Summary selection
  const summary =
    (locale === "en" ? place.visitor_summary_en : place.visitor_summary_vi) ||
    place.visitor_summary_vi ||
    place.access_notes ||
    (locale === "vi"
      ? "Khảo cứu lịch sử và giá trị văn hóa kiến trúc Cố đô Huế được lưu trữ trong thư tịch cổ."
      : "Historical research and architectural cultural value preserved in Huế archives.");

  const cardHref = `/heritage/${place.slug}`;

  const handleCardClick = (e: React.MouseEvent) => {
    if (onClick) {
      e.preventDefault();
      onClick(place);
    }
  };

  return (
    <article
      className={cn(
        "group relative flex flex-col overflow-hidden rounded-2xl border border-border/80 bg-card text-card-foreground shadow-xs transition-all duration-300 hover:-translate-y-1 hover:border-primary/40 hover:shadow-md focus-within:ring-2 focus-within:ring-[var(--rbpc-focus,#1E675A)] focus-within:ring-offset-2",
        className
      )}
    >
      {/* 1. Image Section with Aspect Ratio (16:10) */}
      <div className="relative aspect-[16/10] w-full overflow-hidden bg-muted">
        {place.thumbnail_url && !imgError ? (
          <img
            src={place.thumbnail_url}
            alt={place.name_vi}
            loading={priority ? "eager" : "lazy"}
            onError={() => setImgError(true)}
            className="h-full w-full object-cover transition-transform duration-500 ease-out group-hover:scale-105"
          />
        ) : (
          /* Elegant Architectural Fallback */
          <div className="relative flex h-full w-full flex-col items-center justify-center bg-radial from-paper-elevated to-muted/80 p-6 text-center">
            {/* Subtle decorative grid/cross pattern */}
            <div
              className="absolute inset-0 opacity-10 bg-[radial-gradient(#325b52_1px,transparent_1px)] [background-size:16px_16px]"
              aria-hidden="true"
            />
            <CategoryIcon
              className="relative z-10 h-10 w-10 text-primary/60 transition-transform duration-300 group-hover:scale-110"
              aria-hidden="true"
            />
            <span className="relative z-10 mt-2 font-serif text-xs font-semibold tracking-wider text-muted-foreground uppercase">
              {categoryLabel}
            </span>
          </div>
        )}

        {/* Gradient shadow overlay for badge legibility */}
        <div
          className="pointer-events-none absolute inset-0 bg-gradient-to-t from-black/50 via-transparent to-black/20"
          aria-hidden="true"
        />

        {/* Top-Left: Category Badge (Zero heavy backdrop-blur) */}
        <div className="absolute top-3 left-3 flex flex-wrap items-center gap-1.5">
          <span
            className={cn(
              "inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-xs font-semibold shadow-xs",
              categoryInfo.badgeStyle
            )}
          >
            <CategoryIcon className="h-3.5 w-3.5" aria-hidden="true" />
            <span>{categoryLabel}</span>
          </span>
        </div>

        {/* Top-Right: UNESCO Reference ID & 3D Badges (Zero heavy backdrop-blur) */}
        <div className="absolute top-3 right-3 flex flex-col items-end gap-1.5">
          {/* UNESCO Reference Badge */}
          {isUnesco && (
            <span
              className="inline-flex items-center gap-1 rounded-full border border-emerald-600/40 bg-emerald-950/90 px-2.5 py-0.5 font-mono text-[11px] font-semibold text-emerald-200 shadow-xs"
              title={
                locale === "vi"
                  ? "Cấu phần chính thức thuộc Quần thể Di tích Cố đô Huế (UNESCO 678)"
                  : "Official component of Complex of Hué Monuments (UNESCO 678)"
              }
            >
              <Award className="h-3 w-3 text-emerald-400" aria-hidden="true" />
              <span>UNESCO {unescoRef}</span>
            </span>
          )}

          {/* 3D Model Badge */}
          {place.has_3d && (
            <span
              className="inline-flex items-center gap-1 rounded-full border border-primary/40 bg-background/95 px-2 py-0.5 text-[11px] font-semibold text-primary shadow-xs"
              title={locale === "vi" ? "Có mô hình tương tác 3D" : "Interactive 3D model available"}
            >
              <Box className="h-3 w-3" aria-hidden="true" />
              <span>3D</span>
            </span>
          )}
        </div>

        {/* Bottom Image Rail: Chronology / Period Label */}
        {place.period_label && (
          <div className="absolute bottom-2.5 left-3 flex items-center gap-1.5 rounded-md bg-black/75 px-2 py-0.5 text-[11px] font-medium text-white/95">
            <Clock className="h-3 w-3 text-amber-300" aria-hidden="true" />
            <span className="line-clamp-1">{place.period_label}</span>
          </div>
        )}
      </div>

      {/* 2. Card Content Section */}
      <div className="flex flex-1 flex-col p-5">
        {/* Title Block */}
        <div className="min-w-0 flex-1">
          <Link
            href={cardHref}
            onClick={handleCardClick}
            className="group/link block min-h-[44px] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--rbpc-focus,#1E675A)] focus-visible:ring-offset-2 rounded-sm"
            aria-label={`${place.name_vi}${place.name_en ? ` (${place.name_en})` : ""}`}
          >
            <h3 className="font-serif text-lg font-bold tracking-tight text-foreground leading-snug transition-colors group-hover:text-primary">
              {place.name_vi}
            </h3>

            {place.name_en && (
              <p className="mt-0.5 text-xs text-muted-foreground italic line-clamp-1 font-normal">
                {place.name_en}
              </p>
            )}
          </Link>

          {/* Short Visitor Summary */}
          <p className="mt-2.5 text-xs md:text-sm text-muted-foreground leading-relaxed line-clamp-2">
            {summary}
          </p>
        </div>

        {/* Epistemic Certainty & Access Status Rail */}
        <div className="mt-4 flex flex-wrap items-center justify-between gap-2 border-t border-border/60 pt-3">
          {/* Epistemic Badge */}
          <span
            className={cn(
              "inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-[11px] font-medium",
              epistemicStatusId === "verified_source"
                ? "bg-emerald-500/10 text-emerald-800 dark:text-emerald-400"
                : epistemicStatusId === "living_tradition"
                ? "bg-purple-500/10 text-purple-800 dark:text-purple-400"
                : "bg-muted text-muted-foreground"
            )}
            title={epistemicCopy.description}
          >
            <span
              className={cn(
                "h-1.5 w-1.5 rounded-full shrink-0",
                epistemicStatusId === "verified_source"
                  ? "bg-emerald-600"
                  : epistemicStatusId === "living_tradition"
                  ? "bg-purple-600"
                  : "bg-muted-foreground"
              )}
              aria-hidden="true"
            />
            <span>{epistemicCopy.label}</span>
          </span>

          {/* Access Status Pill (if known) */}
          {place.current_access_status === "open" && (
            <span className="inline-flex items-center gap-1 text-[11px] font-medium text-emerald-700 dark:text-emerald-400">
              <CheckCircle2 className="h-3 w-3" aria-hidden="true" />
              <span>{locale === "vi" ? "Mở cửa" : "Open"}</span>
            </span>
          )}
          {place.current_access_status === "undergoing_restoration" && (
            <span className="inline-flex items-center gap-1 text-[11px] font-medium text-amber-700 dark:text-amber-400">
              <Wrench className="h-3 w-3" aria-hidden="true" />
              <span>{locale === "vi" ? "Đang trùng tu" : "Restoring"}</span>
            </span>
          )}
          {place.current_access_status === "restricted" && (
            <span className="inline-flex items-center gap-1 text-[11px] font-medium text-rose-700 dark:text-rose-400">
              <AlertCircle className="h-3 w-3" aria-hidden="true" />
              <span>{locale === "vi" ? "Hạn chế" : "Restricted"}</span>
            </span>
          )}
        </div>

        {/* Bottom Action CTA Link */}
        <div className="mt-3 pt-2">
          <Link
            href={cardHref}
            onClick={handleCardClick}
            className="inline-flex min-h-[44px] w-full items-center justify-between rounded-xl border border-border/80 bg-background/80 px-3.5 py-2 text-xs font-semibold text-foreground transition-all hover:border-primary/50 hover:bg-primary/5 hover:text-primary focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--rbpc-focus,#1E675A)] focus-visible:ring-offset-2"
          >
            <span>{locale === "vi" ? "Chi tiết di sản" : "Explore Destination"}</span>
            <ChevronRight
              className="h-4 w-4 text-muted-foreground transition-transform group-hover:translate-x-1 group-hover:text-primary"
              aria-hidden="true"
            />
          </Link>
        </div>
      </div>
    </article>
  );
}
