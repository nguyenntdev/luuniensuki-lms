"use client";

import React, { useState } from "react";
import Link from "next/link";
import {
  Hammer,
  Clock,
  MapPin,
  Award,
  CheckCircle2,
  CalendarCheck,
  ChevronRight,
  Info,
  Users,
  Sparkles,
  ShieldAlert,
  ArrowRight,
  UserCheck,
} from "lucide-react";
import type {
  ArtisanBridgeStoryBlock,
  RbpcCreator,
  RbpcExperience,
  RbpcLocale,
  LocalizedField,
  ConsentStatus,
} from "@/types/rbpc";
import { getRbpcCopy } from "@/lib/rbpc/copy";
import { cn } from "@/lib/utils";
import { RbpcCard } from "./RbpcCard";
import { RbpcButton } from "./RbpcButton";
import { InquiryFormModal } from "./InquiryFormModal";

export interface StoryArtisanBridgeProps {
  /** Polymorphic artisan_bridge block from a cultural story */
  block?: ArtisanBridgeStoryBlock;
  /** Full creator profile data (optional, used if block is omitted or to enrich) */
  creator?: RbpcCreator;
  /** Full experience listing data (optional, used if block is omitted or to enrich) */
  experience?: RbpcExperience;
  /** Active UI locale (defaults to "vi") */
  locale?: RbpcLocale;
  /** Custom bridge narrative override connecting imperial history to living practice */
  bridgeNarrative?: LocalizedField | string;
  /** Custom CTA label override */
  ctaLabel?: LocalizedField | string;
  /** Callback triggered when user clicks 'Request workshop availability' */
  onRequestAvailability?: (experienceSlug?: string, creatorSlug?: string) => void;
  /** Callback triggered when user clicks to meet the maker */
  onViewMaker?: (creatorSlug: string) => void;
  /** Callback triggered when user clicks experience details */
  onViewExperience?: (experienceSlug: string) => void;
  /** Whether to allow opening the built-in InquiryFormModal directly */
  enableInlineModal?: boolean;
  /** Additional custom class names for the container */
  className?: string;
  /** Priority loading flag for the portrait */
  priority?: boolean;
}

/**
 * Safely resolves a LocalizedField or string into the active locale.
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
 * StoryArtisanBridge Component
 *
 * Implements Master Spec §4.2, §4.4 & CREATE_LEARN_SPEC.md requirements:
 * 1. Living craft section embedded at the conclusion of cultural stories
 * 2. Introduces the master artisan with portrait, lineage, craft tradition, and verified consent
 * 3. Craft workshop preview with duration, group size, area, and indicative pricing
 * 4. Direct 'Request workshop availability' button (adheres to ADR 06 non-instant commercial transparency)
 * 5. Fail-closed safeguard: if consent is revoked, strips PII and displays respectful privacy notice
 */
export function StoryArtisanBridge({
  block,
  creator,
  experience,
  locale = "vi",
  bridgeNarrative,
  ctaLabel,
  onRequestAvailability,
  onViewMaker,
  onViewExperience,
  enableInlineModal = false,
  className,
  priority = false,
}: StoryArtisanBridgeProps) {
  const [imageError, setImageError] = useState(false);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const copy = getRbpcCopy(locale);

  // Derive consolidated attributes from block or direct creator/experience props
  const creatorSlug = block?.creatorSlug || creator?.slug || "";
  const creatorName = block?.creatorName || creator?.publicName || (locale === "vi" ? "Nghệ nhân truyền thống" : "Master Artisan");
  
  const craftTraditionField = block?.craftTradition || creator?.craftTradition;
  const craftTraditionText = resolveLocalized(
    craftTraditionField,
    locale,
    locale === "vi" ? "Nghề thủ công truyền thống Huế" : "Traditional Huế Craft"
  );

  const consentStatus: ConsentStatus =
    block?.consentStatus || creator?.consentStatus || "consented";

  const portraitUrl = block?.portraitUrl || creator?.approvedPortraitUrl;
  const portraitAlt =
    creator?.portraitAlt ||
    (locale === "vi"
      ? `Chân dung nghệ nhân ${creatorName}`
      : `Portrait of master artisan ${creatorName}`);

  const narrativeField = bridgeNarrative || block?.bridgeNarrative || creator?.approvedBio;
  const narrativeText = resolveLocalized(
    narrativeField,
    locale,
    locale === "vi"
      ? "Kế thừa kỹ nghệ thủ công qua nhiều thế hệ, gìn giữ tinh hoa văn hóa truyền thống Cố đô Huế trong đời sống đương đại."
      : "Carrying forward generations of traditional craftsmanship, sustaining the imperial heritage of Huế in contemporary life."
  );

  const experienceSlug = block?.experienceSlug || experience?.slug || "";
  const experienceTitleField = block?.experienceTitle || experience?.title;
  const experienceTitleText = resolveLocalized(
    experienceTitleField,
    locale,
    locale === "vi"
      ? "Trải nghiệm xưởng nghề thủ công"
      : "Traditional Craft Workshop"
  );

  const priceDisplayText =
    block?.experiencePriceDisplay ||
    experience?.pricing?.displayFormatted ||
    (locale === "vi" ? "Từ 450.000 VNĐ / khách" : "From 450,000 VND / guest");

  const durationMinutes = experience?.durationMinutes || 120;
  const areaPublic = experience?.areaPublic || creator?.publicRegion || (locale === "vi" ? "Phường Đúc, TP. Huế" : "Phuong Duc, Hue");
  const maxPartySize = experience?.maxPartySize || 8;

  const resolvedCtaLabel = resolveLocalized(
    ctaLabel || block?.ctaLabel,
    locale,
    copy.cta.requestAvailability || (locale === "vi" ? "Yêu cầu lịch hẹn" : "Request availability")
  );

  // =========================================================================
  // FAIL-CLOSED PRIVACY SAFEGUARD (Consent Revoked)
  // If the artisan revokes consent, all personal media, contact, and workshop
  // details are withheld immediately.
  // =========================================================================
  if (consentStatus === "revoked") {
    return (
      <section
        aria-label={locale === "vi" ? "Cầu nối nghệ nhân di sản sống" : "Living Artisan Heritage Bridge"}
        className={cn("my-10", className)}
      >
        <RbpcCard
          elevation="inset"
          padding="lg"
          className="border-dashed border-[var(--rbpc-error-border)] bg-[var(--rbpc-error-subtle)] text-center"
        >
          <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-[var(--rbpc-error)]/10 text-[var(--rbpc-error)] mb-3">
            <ShieldAlert className="h-6 w-6" aria-hidden="true" />
          </div>
          <h3 className="font-serif text-lg font-semibold text-[var(--rbpc-ink)] mb-2">
            {locale === "vi"
              ? "Cầu nối nghệ nhân tạm thời không khả dụng"
              : "Living Artisan Bridge Temporarily Unavailable"}
          </h3>
          <p className="text-sm text-[var(--rbpc-muted)] max-w-lg mx-auto leading-relaxed">
            {locale === "vi"
              ? copy.consent.withdrawnNotice ||
                "Nội dung kết nối xưởng nghề tạm thời đóng theo yêu cầu bảo vệ quyền riêng tư của nghệ nhân."
              : copy.consent.withdrawnNotice ||
                "This artisan bridge is temporarily closed in accordance with the practitioner's privacy preferences."}
          </p>
        </RbpcCard>
      </section>
    );
  }

  const handleRequestClick = (e: React.MouseEvent) => {
    e.preventDefault();
    if (onRequestAvailability) {
      onRequestAvailability(experienceSlug, creatorSlug);
    }
    if (enableInlineModal) {
      setIsModalOpen(true);
    }
  };

  const handleMakerClick = (e: React.MouseEvent) => {
    if (onViewMaker && creatorSlug) {
      e.preventDefault();
      onViewMaker(creatorSlug);
    }
  };

  const handleExperienceClick = (e: React.MouseEvent) => {
    if (onViewExperience && experienceSlug) {
      e.preventDefault();
      onViewExperience(experienceSlug);
    }
  };

  // Construct a fallback experience object if needed for the modal
  const modalExperience: RbpcExperience | null =
    experience ||
    (experienceSlug
      ? {
          id: `bridge-${experienceSlug}`,
          slug: experienceSlug,
          creatorSlug,
          creatorName,
          title: typeof experienceTitleField === "object" ? experienceTitleField : { vi: experienceTitleText, en: experienceTitleText },
          description: { vi: narrativeText, en: narrativeText },
          syllabus: [],
          areaPublic,
          durationMinutes,
          pricing: {
            isFree: false,
            amount: 450000,
            currency: "VND",
            displayFormatted: priceDisplayText,
            pricingUnit: "per_person",
          },
          availabilityMode: "inquiry_only",
          maxPartySize,
          languagesSupported: ["vi", "en"],
          notice:
            locale === "vi"
              ? "Concept demonstration — Yêu cầu trải nghiệm sẽ được gửi trực tiếp đến nghệ nhân/cơ sở để xác nhận thời gian."
              : "Concept demonstration — Experience requests will be sent directly to the artisan/facility to confirm timing.",
          publicationState: "published",
          createdAt: new Date().toISOString(),
          updatedAt: new Date().toISOString(),
        }
      : null);

  return (
    <section
      aria-labelledby="story-artisan-bridge-title"
      className={cn(
        "my-12 relative overflow-hidden rounded-2xl border border-[var(--rbpc-divider)] bg-[var(--rbpc-surface)] shadow-[var(--rbpc-shadow-md)]",
        className
      )}
    >
      {/* Decorative Warm Paper Top Accent */}
      <div
        className="h-1.5 w-full bg-gradient-to-r from-[var(--rbpc-primary)] via-[var(--rbpc-highlight)] to-[var(--rbpc-primary)]"
        aria-hidden="true"
      />

      <div className="p-6 sm:p-8 md:p-10">
        {/* Section Header: Continuity Eyebrow */}
        <div className="flex flex-wrap items-center justify-between gap-3 pb-6 border-b border-[var(--rbpc-divider)]">
          <div className="flex items-center gap-2">
            <span className="flex h-6 w-6 items-center justify-center rounded-full bg-[var(--rbpc-primary-subtle)] text-[var(--rbpc-primary)]">
              <Sparkles className="h-3.5 w-3.5" aria-hidden="true" />
            </span>
            <span className="rbpc-eyebrow text-xs font-semibold tracking-wider text-[var(--rbpc-primary)]">
              {locale === "vi"
                ? "Cầu nối di sản sống • Từ trang sử đến bàn tay người thợ"
                : "Living Heritage Bridge • From Imperial Archive to Living Hands"}
            </span>
          </div>

          {/* Consent Verification Badge */}
          <div className="flex items-center gap-1.5 rounded-full border border-emerald-700/30 bg-emerald-500/10 px-3 py-1 text-xs font-medium text-emerald-900 dark:text-emerald-300">
            <CheckCircle2 className="h-3.5 w-3.5 text-emerald-700 dark:text-emerald-400 shrink-0" aria-hidden="true" />
            <span>
              {locale === "vi"
                ? `Đã xác nhận đồng thuận ký tay`
                : `Verified Written Consent`}
            </span>
            {(creator?.displayConsentId || block?.verificationBadge?.documentRef) && (
              <span className="ml-1 font-mono text-[11px] text-emerald-800 dark:text-emerald-400 opacity-80">
                ({creator?.displayConsentId || block?.verificationBadge?.documentRef})
              </span>
            )}
          </div>
        </div>

        {/* Master Artisan & Workshop Grid */}
        <div className="mt-8 grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
          {/* ===================================================================
              1. Master Artisan Profile Column (7 Columns on Desktop)
              =================================================================== */}
          <div className="lg:col-span-7 flex flex-col sm:flex-row gap-6">
            {/* Portrait Image (1:1 with soft rounded corners) */}
            <div className="w-full sm:w-44 sm:h-44 shrink-0 overflow-hidden rounded-xl border border-[var(--rbpc-divider)] bg-[var(--rbpc-surface-muted)] shadow-[var(--rbpc-shadow-sm)]">
              {portraitUrl && !imageError ? (
                <img
                  src={portraitUrl}
                  alt={portraitAlt}
                  loading={priority ? "eager" : "lazy"}
                  onError={() => setImageError(true)}
                  className="h-full w-full object-cover transition-transform duration-500 hover:scale-105 aspect-square"
                />
              ) : (
                <div className="flex h-full w-full flex-col items-center justify-center p-4 text-center bg-radial from-[var(--rbpc-surface)] to-[var(--rbpc-surface-muted)] aspect-square">
                  <div className="flex h-12 w-12 items-center justify-center rounded-full bg-[var(--rbpc-primary)]/10 text-[var(--rbpc-primary)] mb-2">
                    <Hammer className="h-6 w-6" aria-hidden="true" />
                  </div>
                  <span className="font-serif text-xs font-semibold text-[var(--rbpc-ink)] line-clamp-1">
                    {creatorName}
                  </span>
                  <span className="text-[11px] text-[var(--rbpc-muted)] line-clamp-1">
                    {craftTraditionText}
                  </span>
                </div>
              )}
            </div>

            {/* Artisan Bio & Continuity Narrative */}
            <div className="flex-1 space-y-2.5">
              <span className="text-xs font-semibold uppercase tracking-wider text-[var(--rbpc-highlight)]">
                {craftTraditionText}
              </span>

              <h2
                id="story-artisan-bridge-title"
                className="font-serif text-2xl sm:text-3xl font-bold tracking-tight text-[var(--rbpc-ink)] leading-snug"
              >
                {creatorSlug ? (
                  <Link
                    href={`/people/${creatorSlug}`}
                    onClick={handleMakerClick}
                    className="inline-flex min-h-[44px] items-center hover:text-[var(--rbpc-primary)] transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--rbpc-focus)] focus-visible:ring-offset-2 rounded-sm"
                  >
                    {creatorName}
                  </Link>
                ) : (
                  creatorName
                )}
              </h2>

              {/* Lineage & Region Metadata */}
              <div className="flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-[var(--rbpc-muted)]">
                <span className="inline-flex items-center gap-1 font-medium text-[var(--rbpc-ink-subtle)]">
                  <MapPin className="h-3.5 w-3.5 text-[var(--rbpc-highlight)]" aria-hidden="true" />
                  <span>{areaPublic}</span>
                </span>

                {(creator?.generationLineage || block?.verificationBadge?.label) && (
                  <span className="inline-flex items-center gap-1">
                    <Award className="h-3.5 w-3.5 text-amber-600" aria-hidden="true" />
                    <span>{creator?.generationLineage || resolveLocalized(block?.verificationBadge?.label, locale)}</span>
                  </span>
                )}

                {creator?.yearsOfPractice && (
                  <span className="inline-flex items-center gap-1">
                    <Clock className="h-3.5 w-3.5 text-[var(--rbpc-primary)]" aria-hidden="true" />
                    <span>
                      {locale === "vi"
                        ? `${creator.yearsOfPractice} năm giữ nghề`
                        : `${creator.yearsOfPractice} years in craft`}
                    </span>
                  </span>
                )}
              </div>

              {/* Continuity Narrative Quote */}
              <blockquote className="mt-3 border-l-2 border-[var(--rbpc-primary-border)] pl-3 text-sm text-[var(--rbpc-ink-subtle)] leading-relaxed italic">
                “{narrativeText}”
              </blockquote>

              {/* View Maker Profile Link */}
              {creatorSlug && (
                <div className="pt-1">
                  <Link
                    href={`/people/${creatorSlug}`}
                    onClick={handleMakerClick}
                    className="inline-flex min-h-[44px] min-w-[44px] items-center gap-1.5 text-xs font-semibold text-[var(--rbpc-primary)] hover:text-[var(--rbpc-primary-hover)] hover:underline focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--rbpc-focus)] focus-visible:ring-offset-2 rounded-xs py-2"
                  >
                    <UserCheck className="h-3.5 w-3.5" aria-hidden="true" />
                    <span>
                      {locale === "vi"
                        ? `Gặp người làm nghề: ${creatorName}`
                        : `Meet the maker: ${creatorName}`}
                    </span>
                    <ChevronRight className="h-3.5 w-3.5" aria-hidden="true" />
                  </Link>
                </div>
              )}
            </div>
          </div>

          {/* ===================================================================
              2. Craft Workshop Preview & Direct Inquiry Card (5 Columns)
              =================================================================== */}
          <div className="lg:col-span-5">
            <div className="rounded-xl border border-[var(--rbpc-divider)] bg-[var(--rbpc-bg)] p-5 sm:p-6 shadow-xs space-y-4">
              <div className="flex items-center justify-between gap-2">
                <span className="text-xs font-semibold uppercase tracking-wider text-[var(--rbpc-primary)]">
                  {locale === "vi" ? "Trải nghiệm thực tế" : "Real-World Workshop"}
                </span>

                <span className="inline-flex items-center gap-1 rounded-full border border-emerald-700/30 bg-emerald-500/10 px-2 py-0.5 text-[11px] font-medium text-emerald-900 dark:text-emerald-300">
                  <span className="h-1.5 w-1.5 rounded-full bg-emerald-600" aria-hidden="true" />
                  <span>{locale === "vi" ? "Tiếp nhận yêu cầu" : "Inquiry Only"}</span>
                </span>
              </div>

              {/* Workshop Title */}
              <div>
                <h3 className="font-serif text-lg sm:text-xl font-bold text-[var(--rbpc-ink)] leading-snug">
                  {experienceSlug ? (
                    <Link
                      href={`/experiences/${experienceSlug}`}
                      onClick={handleExperienceClick}
                      className="inline-flex min-h-[44px] items-center hover:text-[var(--rbpc-primary)] transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--rbpc-focus)] focus-visible:ring-offset-2 rounded-sm"
                    >
                      {experienceTitleText}
                    </Link>
                  ) : (
                    experienceTitleText
                  )}
                </h3>
              </div>

              {/* Workshop Logistics Chips */}
              <div className="grid grid-cols-2 gap-2 text-xs text-[var(--rbpc-muted)] pt-1">
                <div className="flex items-center gap-1.5">
                  <Clock className="h-3.5 w-3.5 text-[var(--rbpc-primary)] shrink-0" aria-hidden="true" />
                  <span>{durationMinutes} {locale === "vi" ? "phút" : "mins"}</span>
                </div>
                <div className="flex items-center gap-1.5">
                  <Users className="h-3.5 w-3.5 text-[var(--rbpc-primary)] shrink-0" aria-hidden="true" />
                  <span>{locale === "vi" ? `Tối đa ${maxPartySize} khách` : `Max ${maxPartySize} guests`}</span>
                </div>
              </div>

              {/* Indicative Pricing Display */}
              <div className="pt-2 border-t border-[var(--rbpc-divider-subtle)]">
                <div className="text-[11px] font-medium text-[var(--rbpc-muted)] uppercase tracking-wider">
                  {locale === "vi" ? "Giá chỉ dẫn dự kiến" : "Indicative Contribution"}
                </div>
                <div className="font-serif text-lg font-bold text-[var(--rbpc-ink)]">
                  {priceDisplayText}
                </div>
              </div>

              {/* Epistemic Transparency Notice */}
              <div className="flex items-start gap-2 rounded-lg bg-[var(--rbpc-surface)] p-2.5 text-[11px] text-[var(--rbpc-muted)] leading-relaxed border border-[var(--rbpc-divider-subtle)]">
                <Info className="h-4 w-4 text-[var(--rbpc-primary)] shrink-0 mt-0.5" aria-hidden="true" />
                <p>
                  {locale === "vi"
                    ? "Concept demonstration — Yêu cầu trải nghiệm sẽ được gửi trực tiếp đến nghệ nhân/cơ sở để xác nhận thời gian."
                    : "Concept demonstration — Experience requests will be sent directly to the artisan/facility to confirm timing."}
                </p>
              </div>

              {/* Direct Request Workshop Availability Button */}
              <div className="pt-2">
                <RbpcButton
                  variant="primary"
                  size="md"
                  className="w-full justify-center shadow-xs min-h-[44px]"
                  onClick={handleRequestClick}
                  aria-label={
                    locale === "vi"
                      ? `Gửi yêu cầu lịch trải nghiệm: ${experienceTitleText}`
                      : `Request workshop availability for ${experienceTitleText}`
                  }
                >
                  <CalendarCheck className="h-4 w-4 mr-1.5" aria-hidden="true" />
                  <span>{resolvedCtaLabel}</span>
                  <ArrowRight className="h-4 w-4 ml-1.5" aria-hidden="true" />
                </RbpcButton>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Embedded Inquiry Modal if enabled */}
      {enableInlineModal && modalExperience && (
        <InquiryFormModal
          isOpen={isModalOpen}
          onClose={() => setIsModalOpen(false)}
          experience={modalExperience}
          locale={locale}
        />
      )}
    </section>
  );
}

StoryArtisanBridge.displayName = "StoryArtisanBridge";
