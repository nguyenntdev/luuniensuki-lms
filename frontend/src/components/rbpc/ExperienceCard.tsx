"use client";

import React from "react";
import Link from "next/link";
import {
  Clock,
  MapPin,
  Users,
  Globe,
  Info,
  CalendarCheck,
  ChevronRight,
  Sparkles,
  ShieldAlert,
} from "lucide-react";
import type { RbpcExperience, RbpcLocale, LocalizedField } from "@/types/rbpc";
import { getRbpcCopy } from "@/lib/rbpc/copy";
import { cn } from "@/lib/utils";
import { RbpcCard } from "./RbpcCard";
import { RbpcButton } from "./RbpcButton";

export interface ExperienceCardProps {
  /** The workshop experience object conforming to RbpcExperience */
  experience: RbpcExperience;
  /** Active UI locale (defaults to "vi") */
  locale?: RbpcLocale;
  /** Additional custom CSS class names */
  className?: string;
  /** Callback triggered when user clicks 'Request availability' CTA */
  onRequestAvailability?: (experience: RbpcExperience) => void;
  /** Callback triggered when user clicks the card or title for details */
  onViewDetails?: (experience: RbpcExperience) => void;
  /** Custom destination href (defaults to /experiences/[slug]) */
  href?: string;
  /** Priority loading flag */
  priority?: boolean;
}

/**
 * Safely resolves a LocalizedField or string into target locale.
 */
function resolveLocalized(
  field: LocalizedField | string | undefined,
  locale: RbpcLocale = "vi",
  fallback = ""
): string {
  if (!field) return fallback;
  if (typeof field === "string") return field;
  if (locale === "en" && field.en && field.en.trim().length > 0) {
    return field.en;
  }
  return field.vi || field.en || fallback;
}

/**
 * Formats duration in minutes into a clean human-readable bilingual string.
 * Example: 150 -> "150 phút (2.5 giờ)" / "150 mins (2.5 hrs)"
 */
function formatDuration(minutes: number, locale: RbpcLocale): string {
  if (minutes < 60) {
    return locale === "vi" ? `${minutes} phút` : `${minutes} mins`;
  }
  const hours = (minutes / 60).toFixed(minutes % 60 === 0 ? 0 : 1);
  if (locale === "vi") {
    return `${minutes} phút (${hours} giờ)`;
  }
  return `${minutes} mins (${hours} hrs)`;
}

/**
 * Maps language codes to friendly localized labels.
 */
function formatLanguage(code: string, locale: RbpcLocale): string {
  const normalized = code.toLowerCase().trim();
  if (normalized === "vi") return locale === "vi" ? "Tiếng Việt" : "Vietnamese";
  if (normalized === "en") return locale === "vi" ? "Tiếng Anh" : "English";
  if (normalized === "fr") return locale === "vi" ? "Tiếng Pháp" : "French";
  return code.toUpperCase();
}

/**
 * ExperienceCard Component
 *
 * Implements Master Spec §4.4 & CREATE_LEARN_SPEC.md requirements:
 * 1. Title, Host artisan credit, and craft overview
 * 2. Duration and public area (e.g. Phường Đúc, TP. Huế)
 * 3. Indicative pricing with transparent non-commercial disclaimers
 * 4. Explicit availability notice (`inquiry_only` state, never fake instant booking)
 * 5. Primary CTA: `Gửi yêu cầu lịch hẹn (Request availability)` per ADR 06
 */
export function ExperienceCard({
  experience,
  locale = "vi",
  className,
  onRequestAvailability,
  onViewDetails,
  href,
  priority = false,
}: ExperienceCardProps) {
  const copy = getRbpcCopy(locale);
  const destinationHref = href || `/experiences/${experience.slug}`;

  const titleText = resolveLocalized(experience.title, locale);
  const descriptionText = resolveLocalized(experience.description, locale);

  const isAvailable = experience.availabilityMode === "inquiry_only";
  const durationLabel = formatDuration(experience.durationMinutes, locale);

  // Transparency Notice text
  const transparencyNotice =
    experience.notice ||
    (locale === "vi"
      ? "Yêu cầu trải nghiệm chỉ là bước liên hệ xác nhận, không phải giao dịch thanh toán tức thì."
      : "This is an availability request, not an instant financial checkout.");

  // Indicative Price Display
  const pricingFormatted =
    experience.pricing?.displayFormatted ||
    (experience.pricing?.isFree
      ? locale === "vi"
        ? "Miễn phí"
        : "Complimentary"
      : `${(experience.pricing?.amount || 0).toLocaleString("vi-VN")} ${experience.pricing?.currency || "VNĐ"}`);

  const handleRequestClick = (e: React.MouseEvent) => {
    if (onRequestAvailability) {
      e.preventDefault();
      onRequestAvailability(experience);
    }
  };

  const handleCardClick = (e: React.MouseEvent) => {
    if (onViewDetails) {
      e.preventDefault();
      onViewDetails(experience);
    }
  };

  return (
    <article
      className={cn(
        "group relative flex flex-col justify-between overflow-hidden rounded-2xl border border-[var(--rbpc-divider)] bg-[var(--rbpc-surface)] shadow-[var(--rbpc-shadow-sm)] transition-all duration-300 hover:border-[var(--rbpc-primary-border)] hover:shadow-[var(--rbpc-shadow-md)]",
        className
      )}
    >
      {/* =====================================================================
          1. Header & Metadata Section
          ===================================================================== */}
      <div className="p-6">
        {/* Eyebrow & Mode Badges */}
        <div className="flex flex-wrap items-center justify-between gap-2 mb-3">
          <div className="flex items-center gap-1.5 text-xs text-[var(--rbpc-primary)] font-semibold tracking-wide uppercase">
            <Sparkles className="h-3.5 w-3.5 text-[var(--rbpc-highlight)]" aria-hidden="true" />
            <span>
              {locale === "vi" ? "Trải nghiệm xưởng nghề" : "Craft Experience"}
            </span>
          </div>

          {/* Availability Status Badge */}
          {isAvailable ? (
            <span
              className="inline-flex items-center gap-1 rounded-full border border-emerald-700/30 bg-emerald-500/10 px-2.5 py-0.5 text-[11px] font-medium text-emerald-900 dark:text-emerald-300"
              title={transparencyNotice}
            >
              <span className="h-1.5 w-1.5 rounded-full bg-emerald-600" aria-hidden="true" />
              <span>{locale === "vi" ? "Tiếp nhận yêu cầu" : "Accepting Requests"}</span>
            </span>
          ) : (
            <span className="inline-flex items-center gap-1 rounded-full border border-stone-300 bg-stone-100 px-2.5 py-0.5 text-[11px] font-medium text-stone-600">
              <ShieldAlert className="h-3 w-3" aria-hidden="true" />
              <span>{locale === "vi" ? "Chưa mở tiếp nhận" : "Currently Closed"}</span>
            </span>
          )}
        </div>

        {/* Experience Title */}
        <Link
          href={destinationHref}
          onClick={handleCardClick}
          className="group/title block focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--rbpc-focus)] rounded-sm"
        >
          <h3 className="font-serif text-xl sm:text-2xl font-bold tracking-tight text-[var(--rbpc-ink)] leading-snug transition-colors group-hover/title:text-[var(--rbpc-primary)]">
            {titleText}
          </h3>
        </Link>

        {/* Creator / Host Attribution */}
        <div className="mt-2 text-xs sm:text-sm text-[var(--rbpc-muted)]">
          <span>{locale === "vi" ? "Nghệ nhân chủ trì: " : "Host: "}</span>
          {experience.creatorSlug ? (
            <Link
              href={`/people/${experience.creatorSlug}`}
              className="font-medium text-[var(--rbpc-ink)] hover:text-[var(--rbpc-primary)] hover:underline focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-[var(--rbpc-focus)] rounded-xs"
            >
              {experience.creatorName}
            </Link>
          ) : (
            <span className="font-medium text-[var(--rbpc-ink)]">
              {experience.creatorName}
            </span>
          )}
        </div>

        {/* Operational Metadata Bar (Duration, Area, Party Size, Languages) */}
        <div className="mt-4 grid grid-cols-2 gap-2 rounded-xl bg-[var(--rbpc-bg)] p-3 text-xs text-[var(--rbpc-muted)]">
          {/* Duration */}
          <div className="flex items-center gap-2">
            <Clock className="h-4 w-4 text-[var(--rbpc-primary)] shrink-0" aria-hidden="true" />
            <span className="line-clamp-1">{durationLabel}</span>
          </div>

          {/* Location Area */}
          <div className="flex items-center gap-2">
            <MapPin className="h-4 w-4 text-[var(--rbpc-highlight)] shrink-0" aria-hidden="true" />
            <span className="line-clamp-1" title={experience.fullAddressPublic || experience.areaPublic}>
              {experience.areaPublic || "Phường Đúc, Huế"}
            </span>
          </div>

          {/* Max Party Size */}
          <div className="flex items-center gap-2">
            <Users className="h-4 w-4 text-[var(--rbpc-primary)] shrink-0" aria-hidden="true" />
            <span className="line-clamp-1">
              {locale === "vi"
                ? `Tối đa ${experience.maxPartySize} khách`
                : `Max ${experience.maxPartySize} guests`}
            </span>
          </div>

          {/* Languages Supported */}
          <div className="flex items-center gap-2">
            <Globe className="h-4 w-4 text-[var(--rbpc-primary)] shrink-0" aria-hidden="true" />
            <span className="line-clamp-1">
              {experience.languagesSupported?.map((lang) => formatLanguage(lang, locale)).join(", ") ||
                (locale === "vi" ? "Tiếng Việt" : "Vietnamese")}
            </span>
          </div>
        </div>

        {/* Short Summary Description */}
        {descriptionText && (
          <p className="mt-4 text-sm text-[var(--rbpc-ink-subtle)] leading-[var(--rbpc-lh-body)] line-clamp-3">
            {descriptionText}
          </p>
        )}

        {/* Syllabus Activities Count Indicator */}
        {experience.syllabus && experience.syllabus.length > 0 && (
          <div className="mt-3 flex items-center gap-1.5 text-xs text-[var(--rbpc-muted)]">
            <span className="font-semibold text-[var(--rbpc-ink)]">
              {experience.syllabus.length}
            </span>
            <span>
              {locale === "vi"
                ? "bước thực hành trong giáo trình xưởng"
                : "hands-on syllabus steps"}
            </span>
          </div>
        )}
      </div>

      {/* =====================================================================
          2. Commercial Transparency & Action Footer
          ===================================================================== */}
      <div className="border-t border-[var(--rbpc-divider)] bg-[var(--rbpc-surface)] p-6 pt-4">
        {/* Indicative Pricing Display */}
        <div className="flex items-baseline justify-between mb-3">
          <div>
            <span className="block text-[11px] font-medium uppercase tracking-wider text-[var(--rbpc-muted)]">
              {locale === "vi" ? "Giá chỉ dẫn dự kiến" : "Indicative Contribution"}
            </span>
            <span className="font-serif text-lg sm:text-xl font-bold text-[var(--rbpc-ink)]">
              {pricingFormatted}
            </span>
          </div>

          {experience.pricing?.notes && (
            <span className="text-[11px] text-[var(--rbpc-muted)] italic max-w-[160px] text-right line-clamp-1">
              {resolveLocalized(experience.pricing.notes, locale)}
            </span>
          )}
        </div>

        {/* Epistemic Transparency Notice */}
        <div className="mb-4 flex items-start gap-2 rounded-lg bg-[var(--rbpc-bg)] p-2.5 text-[11px] text-[var(--rbpc-muted)] leading-relaxed border border-[var(--rbpc-divider-subtle)]">
          <Info className="h-4 w-4 text-[var(--rbpc-primary)] shrink-0 mt-0.5" aria-hidden="true" />
          <p className="line-clamp-2">{transparencyNotice}</p>
        </div>

        {/* Primary Action Button: "Request availability" (ADR 06 Mandate) */}
        <div className="flex items-center gap-2">
          <RbpcButton
            variant="primary"
            size="md"
            className="flex-1"
            disabled={!isAvailable}
            onClick={handleRequestClick}
          >
            <CalendarCheck className="h-4 w-4 mr-1.5" aria-hidden="true" />
            <span>{copy.cta.requestAvailability}</span>
          </RbpcButton>

          {/* Details Link */}
          <RbpcButton
            asChild
            variant="secondary"
            size="md"
            className="px-3"
          >
            <Link
              href={destinationHref}
              onClick={handleCardClick}
              title={locale === "vi" ? "Xem chi tiết giáo trình" : "View Details"}
              aria-label={locale === "vi" ? `Xem chi tiết ${titleText}` : `View details for ${titleText}`}
            >
              <ChevronRight className="h-4 w-4" aria-hidden="true" />
            </Link>
          </RbpcButton>
        </div>
      </div>
    </article>
  );
}

ExperienceCard.displayName = "ExperienceCard";
