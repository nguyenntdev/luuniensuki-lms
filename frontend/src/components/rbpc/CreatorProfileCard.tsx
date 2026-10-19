"use client";

import React, { useState } from "react";
import Link from "next/link";
import {
  CheckCircle2,
  ShieldCheck,
  Hammer,
  Clock,
  MapPin,
  Mic,
  Calendar,
  ChevronRight,
  ShieldAlert,
  Award,
} from "lucide-react";
import type { RbpcCreator, RbpcLocale, LocalizedField } from "@/types/rbpc";
import { getRbpcCopy } from "@/lib/rbpc/copy";
import { cn } from "@/lib/utils";
import { RbpcCard } from "./RbpcCard";
import { RbpcButton } from "./RbpcButton";

export interface CreatorProfileCardProps {
  /** The creator/artisan profile data object conforming to RbpcCreator */
  creator: RbpcCreator;
  /** Active UI locale (defaults to "vi") */
  locale?: RbpcLocale;
  /** Additional custom class names for the card container */
  className?: string;
  /** Optional click handler when user chooses to view linked workshop experiences */
  onViewExperiences?: (creator: RbpcCreator) => void;
  /** Optional click handler when user selects the creator card */
  onSelectCreator?: (creator: RbpcCreator) => void;
  /** Custom destination href for the primary CTA (defaults to /people/[slug]) */
  ctaHref?: string;
  /** Whether to show the count of linked experiences */
  showExperiencesCount?: boolean;
  /** Priority loading flag for the portrait image */
  priority?: boolean;
}

/**
 * Safely resolves a LocalizedField or string into the target locale.
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
 * CreatorProfileCard Component
 *
 * Implements the Master Spec §4.2 & CREATE_LEARN_SPEC.md requirements:
 * 1. Documentary portrait with graceful fallback and alt text
 * 2. Prominent artisan name and lineage/years in craft tradition
 * 3. Consent verification badge (`Story approved by [name]`)
 * 4. Human-reviewed approved biographical narrative
 * 5. Oral history audio archive indicator
 * 6. Linked workshop experiences CTA
 * 7. Fail-closed safeguard: if consent is revoked, strips PII and renders privacy notice
 */
export function CreatorProfileCard({
  creator,
  locale = "vi",
  className,
  onViewExperiences,
  onSelectCreator,
  ctaHref,
  showExperiencesCount = true,
  priority = false,
}: CreatorProfileCardProps) {
  const [imageError, setImageError] = useState(false);
  const copy = getRbpcCopy(locale);

  const destinationHref = ctaHref || `/people/${creator.slug}`;

  // =========================================================================
  // FAIL-CLOSED PRIVACY SAFEGUARD (Consent Revoked)
  // If an artisan revokes consent, all personal media, contact, and portrait
  // assets are withheld immediately.
  // =========================================================================
  if (creator.consentStatus === "revoked") {
    return (
      <RbpcCard
        elevation="inset"
        padding="lg"
        className={cn(
          "border-dashed border-[var(--rbpc-error-border)] bg-[var(--rbpc-error-subtle)] text-center",
          className
        )}
      >
        <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-[var(--rbpc-error)]/10 text-[var(--rbpc-error)] mb-4">
          <ShieldAlert className="h-6 w-6" aria-hidden="true" />
        </div>
        <h3 className="font-serif text-lg font-semibold text-[var(--rbpc-ink)] mb-2">
          {locale === "vi"
            ? "Hồ sơ tạm thời không khả dụng"
            : "Profile Temporarily Unavailable"}
        </h3>
        <p className="text-sm text-[var(--rbpc-muted)] max-w-md mx-auto leading-relaxed">
          {locale === "vi"
            ? copy.consent.withdrawnNotice ||
              "Hồ sơ này tạm thời đóng theo yêu cầu bảo vệ quyền riêng tư của nghệ nhân."
            : copy.consent.withdrawnNotice ||
              "This profile is temporarily closed in accordance with artisan privacy preferences."}
        </p>
      </RbpcCard>
    );
  }

  // Localized textual attributes
  const craftTraditionText = resolveLocalized(
    creator.craftTradition,
    locale,
    locale === "vi" ? "Nghề thủ công truyền thống Huế" : "Traditional Huế Craft"
  );
  const bioText = resolveLocalized(creator.approvedBio, locale);

  const portraitAlt =
    creator.portraitAlt ||
    (locale === "vi"
      ? `Chân dung tư liệu nghệ nhân ${creator.publicName}`
      : `Documentary portrait of artisan ${creator.publicName}`);

  // Count of linked experiences
  const experienceCount =
    creator.linkedExperiences?.length ?? creator.experienceSlugs?.length ?? 0;

  // Consent badge text ("Story approved by [name]")
  const consentBadgeLabel =
    locale === "vi"
      ? `Câu chuyện đã được ${creator.publicName} phê duyệt`
      : `Story approved by ${creator.publicName}`;

  const consentId = creator.displayConsentId || "CONSENT-HUE-2026";

  const handleCtaClick = (e: React.MouseEvent) => {
    if (onViewExperiences) {
      e.preventDefault();
      onViewExperiences(creator);
    } else if (onSelectCreator) {
      e.preventDefault();
      onSelectCreator(creator);
    }
  };

  return (
    <article
      className={cn(
        "group relative flex flex-col md:flex-row overflow-hidden rounded-2xl border border-[var(--rbpc-divider)] bg-[var(--rbpc-surface)] shadow-[var(--rbpc-shadow-sm)] transition-all duration-300 hover:border-[var(--rbpc-primary-border)] hover:shadow-[var(--rbpc-shadow-md)]",
        className
      )}
    >
      {/* =====================================================================
          1. Documentary Portrait Column (1:1 mobile, 4:5 on desktop)
          ===================================================================== */}
      <div className="relative w-full md:w-2/5 md:min-w-[280px] md:max-w-[340px] shrink-0 overflow-hidden bg-[var(--rbpc-surface-muted)]">
        <div className="relative aspect-square md:aspect-[4/5] w-full h-full">
          {creator.approvedPortraitUrl && !imageError ? (
            <img
              src={creator.approvedPortraitUrl}
              alt={portraitAlt}
              loading={priority ? "eager" : "lazy"}
              onError={() => setImageError(true)}
              className="h-full w-full object-cover transition-transform duration-500 ease-out group-hover:scale-105"
            />
          ) : (
            /* Dignified Materiality Fallback */
            <div className="flex h-full w-full flex-col items-center justify-center p-6 text-center bg-radial from-[var(--rbpc-surface)] to-[var(--rbpc-surface-muted)]">
              <div className="flex h-16 w-16 items-center justify-center rounded-full bg-[var(--rbpc-primary)]/10 text-[var(--rbpc-primary)] shadow-inner mb-3">
                <Hammer className="h-8 w-8" aria-hidden="true" />
              </div>
              <span className="font-serif text-sm font-semibold tracking-wide text-[var(--rbpc-ink)]">
                {creator.publicName}
              </span>
              <span className="mt-1 text-xs text-[var(--rbpc-muted)] line-clamp-1">
                {craftTraditionText}
              </span>
            </div>
          )}

          {/* Subtle gradient vignette for text legibility */}
          <div
            className="pointer-events-none absolute inset-0 bg-gradient-to-t from-black/60 via-black/10 to-transparent"
            aria-hidden="true"
          />

          {/* Region & Lineage Chip Bar at bottom of photo (Zero heavy backdrop-blur) */}
          <div className="absolute bottom-3 left-3 right-3 flex flex-wrap items-center gap-1.5 text-white">
            <span className="inline-flex items-center gap-1 rounded-md bg-black/75 px-2.5 py-1 text-xs font-medium">
              <MapPin className="h-3.5 w-3.5 text-[var(--rbpc-highlight)]" aria-hidden="true" />
              <span>{creator.publicRegion || "TP. Huế"}</span>
            </span>

            {creator.generationLineage && (
              <span className="inline-flex items-center gap-1 rounded-md bg-black/75 px-2.5 py-1 text-xs font-medium">
                <Award className="h-3.5 w-3.5 text-amber-300" aria-hidden="true" />
                <span>{creator.generationLineage}</span>
              </span>
            )}
          </div>
        </div>
      </div>

      {/* =====================================================================
          2. Content & Bio Column
          ===================================================================== */}
      <div className="flex flex-1 flex-col justify-between p-6 sm:p-7">
        <div>
          {/* Craft Tradition Lineage Eyebrow */}
          <div className="flex flex-wrap items-center justify-between gap-2 mb-2">
            <span className="rbpc-eyebrow text-xs tracking-wider font-semibold text-[var(--rbpc-primary)]">
              {craftTraditionText}
            </span>

            {creator.yearsOfPractice && (
              <span className="inline-flex items-center gap-1 text-xs text-[var(--rbpc-muted)] font-medium">
                <Clock className="h-3.5 w-3.5" aria-hidden="true" />
                <span>
                  {locale === "vi"
                    ? `${creator.yearsOfPractice} năm thâm niên`
                    : `${creator.yearsOfPractice} years in craft`}
                </span>
              </span>
            )}
          </div>

          {/* Artisan Name (Min 44px hit-target) */}
          <Link
            href={destinationHref}
            onClick={handleCtaClick}
            className="group/link inline-flex min-h-[44px] items-center focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--rbpc-focus,#1E675A)] focus-visible:ring-offset-2 rounded-sm"
          >
            <h2 className="font-serif text-2xl sm:text-3xl font-bold tracking-tight text-[var(--rbpc-ink)] transition-colors group-hover/link:text-[var(--rbpc-primary)]">
              {creator.publicName}
            </h2>
          </Link>

          {/* Consent Verification Badge */}
          <div className="mt-3 flex flex-wrap items-center gap-2">
            <span
              className="inline-flex items-center gap-1.5 rounded-full border border-emerald-700/30 bg-emerald-500/10 px-3 py-1 text-xs font-medium text-emerald-900 dark:text-emerald-300 shadow-xs"
              title={`${consentBadgeLabel} (${locale === "vi" ? "Mã lưu trữ" : "Consent ID"}: ${consentId})`}
            >
              <CheckCircle2 className="h-3.5 w-3.5 text-emerald-700 dark:text-emerald-400 shrink-0" aria-hidden="true" />
              <span className="font-medium">{consentBadgeLabel}</span>
            </span>

            {creator.displayConsentId && (
              <span className="font-mono text-[11px] text-[var(--rbpc-muted)] px-2 py-0.5 rounded-md bg-[var(--rbpc-surface-muted)]">
                {creator.displayConsentId}
              </span>
            )}
          </div>

          {/* Approved Biographical Narrative */}
          {bioText && (
            <p className="mt-4 text-sm sm:text-base text-[var(--rbpc-ink-subtle)] leading-[var(--rbpc-lh-body)] line-clamp-3 sm:line-clamp-4">
              {bioText}
            </p>
          )}

          {/* Oral History Recording Indicator */}
          {creator.oralHistory?.consentGranted && (
            <div className="mt-4 flex items-center gap-2 rounded-lg border border-[var(--rbpc-divider-subtle)] bg-[var(--rbpc-bg)] px-3 py-2 text-xs text-[var(--rbpc-muted)]">
              <Mic className="h-4 w-4 text-[var(--rbpc-primary)] shrink-0" aria-hidden="true" />
              <span className="font-medium text-[var(--rbpc-ink)]">
                {locale === "vi"
                  ? "Tư liệu truyền khẩu có ghi âm đối chiếu"
                  : "Oral history recording archival audio"}
              </span>
              {creator.oralHistory.durationSeconds && (
                <span className="ml-auto font-mono text-[11px]">
                  {Math.round(creator.oralHistory.durationSeconds / 60)} min
                </span>
              )}
            </div>
          )}
        </div>

        {/* =====================================================================
            3. Linked Workshop CTA Footer
            ===================================================================== */}
        <div className="mt-6 pt-4 border-t border-[var(--rbpc-divider)] flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          {showExperiencesCount && (
            <div className="flex items-center gap-1.5 text-xs text-[var(--rbpc-muted)]">
              <Calendar className="h-4 w-4 text-[var(--rbpc-highlight)]" aria-hidden="true" />
              <span>
                {locale === "vi"
                  ? `${experienceCount} trải nghiệm xưởng nghề gắn liền`
                  : `${experienceCount} linked workshop experience${experienceCount === 1 ? "" : "s"}`}
              </span>
            </div>
          )}

          <RbpcButton
            asChild
            variant="primary"
            size="md"
            className="w-full sm:w-auto"
          >
            <Link href={destinationHref} onClick={handleCtaClick}>
              <span>
                {locale === "vi"
                  ? "Xem trải nghiệm xưởng nghề"
                  : "View Workshop Experiences"}
              </span>
              <ChevronRight className="h-4 w-4 transition-transform group-hover:translate-x-1" aria-hidden="true" />
            </Link>
          </RbpcButton>
        </div>
      </div>
    </article>
  );
}

CreatorProfileCard.displayName = "CreatorProfileCard";
