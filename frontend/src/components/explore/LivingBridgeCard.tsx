"use client";

import * as React from "react";
import Link from "next/link";
import {
  Landmark,
  Hammer,
  Sparkles,
  ArrowRight,
  ShieldCheck,
  ShieldAlert,
  Clock,
  MapPin,
  Calendar,
  ExternalLink,
  Award,
  ChevronRight,
  Info,
} from "lucide-react";
import { cn } from "@/lib/utils";
import type {
  RbpcCreator,
  RbpcExperience,
  ConsentStatus,
  VerificationBadge,
  LocalizedField,
  InquiryFormValues,
  InquirySubmissionResult,
} from "@/types/rbpc";
import type { RbpcLocale } from "@/lib/rbpc/copy";
import { getRbpcCopy } from "@/lib/rbpc/copy";
import { InquiryFormModal } from "@/components/rbpc/InquiryFormModal";

export interface LivingBridgeArtisanInput {
  id?: string;
  slug: string;
  publicName: string;
  craftTradition: LocalizedField | string;
  approvedBio?: LocalizedField | string;
  approvedPortraitUrl?: string;
  portraitAlt?: string;
  publicRegion?: string;
  consentStatus: ConsentStatus;
  verificationBadge?: VerificationBadge;
  yearsOfPractice?: number;
  generationLineage?: string;
}

export interface LivingBridgeExperienceInput {
  slug: string;
  title: LocalizedField | string;
  description?: LocalizedField | string;
  durationMinutes?: number;
  pricingDisplay?: string;
  areaPublic?: string;
  notice?: string;
}

export interface LivingBridgeCardProps extends React.HTMLAttributes<HTMLDivElement> {
  /** Historical monument or site name */
  monumentName: string;
  /** English translated monument name */
  monumentNameEn?: string;
  /** Historical dynasty/period label (e.g. "Triều Minh Mạng, 1835-1837") */
  monumentPeriod?: string;
  /** Monument category or role (e.g. "Thế Miếu & Cửu Đỉnh") */
  monumentCategory?: string;
  /** Optional monument slug */
  monumentSlug?: string;
  /** Optional monument thumbnail URL */
  monumentThumbnailUrl?: string;

  /** Living artisan / master counterpart */
  artisan: RbpcCreator | LivingBridgeArtisanInput;

  /** Historical bridge narrative explaining unbroken continuity */
  bridgeNarrative: LocalizedField | string;

  /** Optional linked workshop or hands-on experience */
  experience?: RbpcExperience | LivingBridgeExperienceInput;

  /** Active UI locale ("vi" | "en", defaults to "vi") */
  locale?: RbpcLocale;

  /** Additional container classes */
  className?: string;

  /** Callback fired when user clicks to explore the artisan profile */
  onExploreArtisan?: (artisanSlug: string) => void;

  /** Callback fired when user clicks to inquire about the workshop experience */
  onRequestExperience?: (experienceSlug: string) => void;

  /** Callback fired when the workshop inquiry modal is opened */
  onOpenInquiryModal?: () => void;

  /** Callback fired when the workshop inquiry form is submitted */
  onInquirySubmit?: (
    values: InquiryFormValues
  ) => Promise<InquirySubmissionResult | void> | InquirySubmissionResult | void;

  /** Whether to allow opening the built-in InquiryFormModal directly (defaults to true) */
  enableInquiryModal?: boolean;

  /** Whether the inquiry modal should be open initially (useful for tests or deep-linking) */
  initialInquiryModalOpen?: boolean;
}

/**
 * Helper to safely extract string from LocalizedField or string
 */
export function resolveLocalizedText(
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
 * LivingBridgeCard Component
 *
 * Implements the core Living Heritage Bridge concept:
 * Connects an imperial historical monument (e.g. Thế Miếu / Cửu Đỉnh) directly to
 * its contemporary living craft practitioner (e.g. Nghệ nhân Phường Đúc Huế).
 *
 * Grounding & Guardrails:
 * - Epistemic honesty: Clearly marks verified consent status.
 * - Fail-closed privacy: If consentStatus === "revoked", suppresses PII and renders a dignified notice.
 * - Commercial transparency: Marks workshop inquiries as non-instant contact requests.
 */
export function LivingBridgeCard({
  monumentName,
  monumentNameEn,
  monumentPeriod,
  monumentCategory,
  monumentSlug,
  monumentThumbnailUrl,
  artisan,
  bridgeNarrative,
  experience,
  locale = "vi",
  className,
  onExploreArtisan,
  onRequestExperience,
  onOpenInquiryModal,
  onInquirySubmit,
  enableInquiryModal = true,
  initialInquiryModalOpen = false,
  ...restProps
}: LivingBridgeCardProps) {
  const isEn = locale === "en";
  const dict = getRbpcCopy(locale);
  const [imageError, setImageError] = React.useState(false);
  const [isInquiryOpen, setIsInquiryOpen] = React.useState(initialInquiryModalOpen);

  // Synchronize modal state if initialInquiryModalOpen prop changes
  React.useEffect(() => {
    if (initialInquiryModalOpen !== undefined) {
      setIsInquiryOpen(initialInquiryModalOpen);
    }
  }, [initialInquiryModalOpen]);

  const displayMonumentName = isEn && monumentNameEn ? monumentNameEn : monumentName;
  const resolvedNarrative = resolveLocalizedText(bridgeNarrative, locale);
  const resolvedCraftTradition = resolveLocalizedText(artisan.craftTradition, locale);
  const resolvedBio = resolveLocalizedText(artisan.approvedBio, locale);

  // Format experience details if provided
  const expTitle = experience
    ? resolveLocalizedText(experience.title, locale)
    : "";
  const expDuration =
    experience && "durationMinutes" in experience && experience.durationMinutes
      ? `${experience.durationMinutes} ${isEn ? "mins" : "phút"}`
      : undefined;
  const expPrice =
    experience && "pricing" in experience && experience.pricing
      ? experience.pricing.displayFormatted
      : experience && "pricingDisplay" in experience
      ? experience.pricingDisplay
      : undefined;

  // Synthesize or normalize full RbpcExperience for the inquiry modal
  const modalExperience: RbpcExperience | null = React.useMemo(() => {
    if (!experience && !artisan) return null;
    if (experience && "syllabus" in experience && experience.syllabus) {
      return experience as RbpcExperience;
    }

    const expSlug = experience?.slug || `workshop-${artisan.slug}`;
    const expTitle =
      experience?.title || {
        vi: `Trải nghiệm xưởng nghề ${artisan.publicName}`,
        en: `Craft Workshop with ${artisan.publicName}`,
      };
    const expDesc =
      (experience && "description" in experience && experience.description) ||
      bridgeNarrative ||
      (locale === "vi"
        ? `Trải nghiệm thực hành trực tiếp tại xưởng nghề cùng ${artisan.publicName}.`
        : `Hands-on traditional craft workshop directly with ${artisan.publicName}.`);

    return {
      id: `bridge-${expSlug}`,
      slug: expSlug,
      creatorSlug: artisan.slug,
      creatorName: artisan.publicName,
      title:
        typeof expTitle === "object"
          ? expTitle
          : { vi: String(expTitle), en: String(expTitle) },
      description:
        typeof expDesc === "object"
          ? expDesc
          : { vi: String(expDesc), en: String(expDesc) },
      syllabus: [],
      areaPublic:
        (experience && "areaPublic" in experience && experience.areaPublic) ||
        artisan.publicRegion ||
        (locale === "vi" ? "Phường Đúc, TP. Huế" : "Phuong Duc, Hue"),
      durationMinutes:
        (experience && "durationMinutes" in experience && experience.durationMinutes) || 120,
      pricing: {
        isFree: false,
        amount: 450000,
        currency: "VND",
        displayFormatted:
          expPrice ||
          (locale === "vi" ? "Từ 450.000 VNĐ / khách" : "From 450,000 VND / guest"),
        pricingUnit: "per_person",
      },
      availabilityMode: "inquiry_only",
      maxPartySize: 8,
      languagesSupported: ["vi", "en"],
      notice:
        (experience && "notice" in experience && experience.notice) ||
        (locale === "vi"
          ? "Yêu cầu trải nghiệm chỉ là bước liên hệ xác nhận, không phải giao dịch thanh toán tức thì."
          : "This is an availability request, not an instant financial checkout."),
      publicationState: "published",
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    };
  }, [experience, artisan, bridgeNarrative, locale, expPrice]);

  // FAIL-CLOSED SAFEGUARD: Revoked consent
  if (artisan.consentStatus === "revoked") {
    return (
      <div
        role="region"
        aria-label={isEn ? "Living Artisan Bridge" : "Cầu nối nghệ nhân di sản sống"}
        className={cn(
          "rounded-2xl border border-dashed border-[var(--rbpc-error-border)] bg-[var(--rbpc-error-subtle)] p-6 text-center",
          className
        )}
        {...restProps}
      >
        <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-[var(--rbpc-error)]/10 text-[var(--rbpc-error)] mb-3">
          <ShieldAlert className="h-6 w-6" aria-hidden="true" />
        </div>
        <h4 className="font-serif text-lg font-bold text-[var(--rbpc-ink)] mb-1">
          {isEn
            ? "Living Artisan Bridge Temporarily Unavailable"
            : "Cầu nối nghệ nhân tạm thời không khả dụng"}
        </h4>
        <p className="text-xs sm:text-sm text-[var(--rbpc-muted)] max-w-lg mx-auto leading-relaxed">
          {isEn
            ? "In accordance with our artisan consent protocol, this practitioner's profile and workshop details have been withdrawn."
            : "Tuân thủ quy chế chấp thuận và quyền riêng tư của nghệ nhân, nội dung kết nối xưởng nghề tạm thời đóng theo yêu cầu."}
        </p>
      </div>
    );
  }

  const handleInquireClick = (e: React.MouseEvent) => {
    e.preventDefault();
    const targetSlug = experience?.slug || modalExperience?.slug || `workshop-${artisan.slug}`;
    if (onRequestExperience) {
      onRequestExperience(targetSlug);
    }
    if (enableInquiryModal) {
      setIsInquiryOpen(true);
    }
    onOpenInquiryModal?.();
  };

  return (
    <article
      data-testid="living-bridge-card"
      aria-label={isEn ? "Living Heritage Bridge" : "Cầu nối di sản sống"}
      className={cn(
        "relative overflow-hidden rounded-2xl border border-[var(--rbpc-highlight-border)] bg-[var(--rbpc-surface)] p-5 sm:p-7 shadow-xs transition-all hover:border-[var(--rbpc-highlight)] hover:shadow-md",
        className
      )}
      {...restProps}
    >
      {/* Decorative top accent line */}
      <div className="absolute top-0 inset-x-0 h-1 bg-gradient-to-r from-[var(--rbpc-primary)] via-[var(--rbpc-highlight)] to-[var(--rbpc-primary)]" />

      {/* Header Eyebrow & Continuity Indicator */}
      <div className="flex flex-wrap items-center justify-between gap-2 border-b border-[var(--rbpc-divider-subtle)] pb-4">
        <div className="inline-flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-[var(--rbpc-highlight)]">
          <Sparkles className="h-4 w-4" aria-hidden="true" />
          <span>{isEn ? "Living Heritage Bridge" : "Cầu nối Di sản Sống"}</span>
        </div>

        {/* Written Consent Verification Badge */}
        <div className="inline-flex items-center gap-1.5 rounded-full bg-emerald-50 px-3 py-1 text-xs font-semibold text-emerald-800 border border-emerald-200 dark:bg-emerald-950/40 dark:text-emerald-300">
          <ShieldCheck className="h-3.5 w-3.5" aria-hidden="true" />
          <span>
            {artisan.consentStatus === "verified_written_consent"
              ? isEn
                ? "Verified Written Consent"
                : "Đã xác thực chấp thuận"
              : isEn
              ? "Artisan Consented"
              : "Nghệ nhân đồng thuận"}
          </span>
        </div>
      </div>

      {/* Dual Anchor Bridge Banner */}
      <div className="mt-5 grid grid-cols-1 md:grid-cols-11 gap-4 items-center rounded-xl bg-[var(--rbpc-surface-muted)]/70 p-4 border border-[var(--rbpc-divider)]">
        {/* Left Anchor: Historical Monument */}
        <div className="md:col-span-5 flex items-center gap-3">
          <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-[var(--rbpc-surface-elevated)] border border-[var(--rbpc-divider)] text-[var(--rbpc-primary)] shadow-2xs">
            <Landmark className="h-5 w-5" aria-hidden="true" />
          </div>
          <div className="min-w-0">
            <span className="text-[10px] font-bold uppercase tracking-wider text-[var(--rbpc-muted)]">
              {isEn ? "Imperial Historical Site" : "Di tích Cung đình"}
            </span>
            <h4 className="font-serif text-sm sm:text-base font-bold text-[var(--rbpc-ink)] truncate">
              {displayMonumentName}
            </h4>
            {monumentPeriod && (
              <p className="text-xs text-[var(--rbpc-muted)] truncate">
                {monumentPeriod}
              </p>
            )}
          </div>
        </div>

        {/* Center: Continuity Connector */}
        <div className="md:col-span-1 flex items-center justify-center py-1 md:py-0">
          <div className="flex h-8 w-8 items-center justify-center rounded-full bg-[var(--rbpc-highlight-subtle)] text-[var(--rbpc-highlight)] border border-[var(--rbpc-highlight-border)] shadow-2xs">
            <ArrowRight className="h-4 w-4 transform md:rotate-0 rotate-90" aria-hidden="true" />
          </div>
        </div>

        {/* Right Anchor: Living Master Artisan */}
        <div className="md:col-span-5 flex items-center gap-3">
          {/* Artisan Portrait or Icon Fallback */}
          <div className="relative h-11 w-11 shrink-0 overflow-hidden rounded-xl border border-[var(--rbpc-divider)] bg-[var(--rbpc-surface-elevated)] shadow-2xs">
            {artisan.approvedPortraitUrl && !imageError ? (
              <img
                src={artisan.approvedPortraitUrl}
                alt={artisan.portraitAlt || artisan.publicName}
                loading="lazy"
                onError={() => setImageError(true)}
                className="h-full w-full object-cover"
              />
            ) : (
              <div className="flex h-full w-full items-center justify-center text-[var(--rbpc-highlight)]">
                <Hammer className="h-5 w-5" aria-hidden="true" />
              </div>
            )}
          </div>
          <div className="min-w-0">
            <span className="text-[10px] font-bold uppercase tracking-wider text-[var(--rbpc-highlight)]">
              {isEn ? "Living Master Practitioner" : "Nghệ nhân Di sản Sống"}
            </span>
            <h4 className="font-serif text-sm sm:text-base font-bold text-[var(--rbpc-ink)] truncate">
              {artisan.publicName}
            </h4>
            <p className="text-xs text-[var(--rbpc-muted)] truncate">
              {resolvedCraftTradition}
            </p>
          </div>
        </div>
      </div>

      {/* Continuity Bridge Narrative Passage */}
      <div className="mt-5">
        <h5 className="text-xs font-semibold uppercase tracking-wider text-[var(--rbpc-ink-subtle)]">
          {isEn ? "Living Lineage Continuity" : "Mạch nguồn Kỹ nghệ Tiếp nối"}
        </h5>
        <div className="mt-2 rounded-xl border-l-3 border-[var(--rbpc-highlight)] bg-[var(--rbpc-surface-muted)]/40 p-4">
          <p className="font-serif text-sm sm:text-base italic leading-relaxed text-[var(--rbpc-ink)]">
            “{resolvedNarrative}”
          </p>
        </div>
      </div>

      {/* Artisan Credentials / Bio snippet */}
      <div className="mt-4 flex flex-wrap items-center gap-2 text-xs">
        {artisan.generationLineage && (
          <span className="inline-flex items-center gap-1 rounded-md bg-[var(--rbpc-surface-muted)] px-2.5 py-1 font-semibold text-[var(--rbpc-ink)] border border-[var(--rbpc-divider)]">
            <Award className="h-3.5 w-3.5 text-[var(--rbpc-highlight)]" aria-hidden="true" />
            <span>{artisan.generationLineage}</span>
          </span>
        )}

        {artisan.yearsOfPractice && (
          <span className="inline-flex items-center gap-1 rounded-md bg-[var(--rbpc-surface-muted)] px-2.5 py-1 font-semibold text-[var(--rbpc-ink)] border border-[var(--rbpc-divider)]">
            <Clock className="h-3.5 w-3.5 text-[var(--rbpc-primary)]" aria-hidden="true" />
            <span>
              {artisan.yearsOfPractice} {isEn ? "years of mastery" : "năm tuổi nghề"}
            </span>
          </span>
        )}

        {artisan.publicRegion && (
          <span className="inline-flex items-center gap-1 rounded-md bg-[var(--rbpc-surface-muted)] px-2.5 py-1 text-[var(--rbpc-muted)] border border-[var(--rbpc-divider)]">
            <MapPin className="h-3.5 w-3.5" aria-hidden="true" />
            <span>{artisan.publicRegion}</span>
          </span>
        )}
      </div>

      {resolvedBio && (
        <p className="mt-3 text-xs sm:text-sm text-[var(--rbpc-muted)] leading-relaxed line-clamp-2">
          {resolvedBio}
        </p>
      )}

      {/* Linked Workshop Experience Sub-Panel (if present) */}
      {experience && (
        <div className="mt-5 rounded-xl border border-[var(--rbpc-divider)] bg-[var(--rbpc-surface-elevated)] p-4 shadow-2xs">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
            <div>
              <span className="text-[10px] font-bold uppercase tracking-wider text-[var(--rbpc-primary)]">
                {isEn ? "Hands-on Heritage Experience" : "Trải nghiệm Xưởng nghề Thực tế"}
              </span>
              <h5 className="font-serif text-sm sm:text-base font-bold text-[var(--rbpc-ink)]">
                {expTitle}
              </h5>
              <div className="mt-1 flex flex-wrap items-center gap-3 text-xs text-[var(--rbpc-muted)]">
                {expDuration && <span>⏱ {expDuration}</span>}
                {expPrice && <span className="font-semibold text-[var(--rbpc-ink)]">{expPrice}</span>}
                {experience.areaPublic && <span>📍 {experience.areaPublic}</span>}
              </div>
            </div>

            {/* Inquire Action Button */}
            <div className="shrink-0">
              {enableInquiryModal || onRequestExperience ? (
                <button
                  type="button"
                  onClick={handleInquireClick}
                  className="inline-flex items-center gap-1.5 rounded-lg bg-[var(--rbpc-highlight)] px-4 py-2 text-xs font-semibold text-white hover:bg-[var(--rbpc-highlight-hover)] transition-colors min-h-[44px] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--rbpc-focus,#1E675A)] focus-visible:ring-offset-2"
                  aria-label={isEn ? "Inquire Experience" : "Yêu cầu trải nghiệm"}
                  data-testid="living-bridge-inquire-btn"
                >
                  <span>{isEn ? "Inquire Experience" : "Yêu cầu trải nghiệm"}</span>
                  <ChevronRight className="h-4 w-4" aria-hidden="true" />
                </button>
              ) : (
                <Link
                  href={`/rbpc/inquiries?experience=${encodeURIComponent(experience.slug)}`}
                  className="inline-flex items-center gap-1.5 rounded-lg bg-[var(--rbpc-highlight)] px-4 py-2 text-xs font-semibold text-white hover:bg-[var(--rbpc-highlight-hover)] transition-colors min-h-[44px] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--rbpc-focus,#1E675A)] focus-visible:ring-offset-2"
                  aria-label={isEn ? "Inquire Experience" : "Đăng ký tham gia workshop (Yêu cầu trải nghiệm)"}
                  data-testid="living-bridge-inquire-link"
                >
                  <span>{isEn ? "Inquire Experience" : "Đăng ký tham gia workshop"}</span>
                  <ChevronRight className="h-4 w-4" aria-hidden="true" />
                </Link>
              )}
            </div>
          </div>

          {/* Transparency Notice */}
          <p className="mt-2 text-[10px] text-[var(--rbpc-muted)] italic">
            * {experience.notice ||
              (isEn
                ? "Inquiries are non-commercial requests sent directly to the artisan community; not an instant payment."
                : "Yêu cầu trải nghiệm chỉ là bước liên hệ xác nhận, không phải giao dịch thanh toán tức thì.")}
          </p>
        </div>
      )}

      {/* Primary Action Footer */}
      <div className="mt-5 flex flex-wrap items-center justify-between gap-3 border-t border-[var(--rbpc-divider-subtle)] pt-4">
        <div className="flex flex-wrap items-center gap-3">
          {onExploreArtisan ? (
            <button
              type="button"
              onClick={() => onExploreArtisan(artisan.slug)}
              className="inline-flex items-center gap-1.5 text-xs font-semibold text-[var(--rbpc-primary)] hover:underline min-h-[44px] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--rbpc-focus,#1E675A)] focus-visible:ring-offset-2 rounded-sm"
            >
              <span>{isEn ? `Meet ${artisan.publicName}` : `Tìm hiểu Nghệ nhân ${artisan.publicName}`}</span>
              <ArrowRight className="h-3.5 w-3.5" aria-hidden="true" />
            </button>
          ) : (
            <Link
              href={`/people/${artisan.slug}`}
              className="inline-flex items-center gap-1.5 text-xs font-semibold text-[var(--rbpc-primary)] hover:underline min-h-[44px] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--rbpc-focus,#1E675A)] focus-visible:ring-offset-2 rounded-sm"
            >
              <span>{isEn ? `Meet ${artisan.publicName}` : `Tìm hiểu Nghệ nhân ${artisan.publicName}`}</span>
              <ArrowRight className="h-3.5 w-3.5" aria-hidden="true" />
            </Link>
          )}

          {/* Action Trigger: Direct Workshop Inquiry Modal */}
          {enableInquiryModal && (
            <button
              type="button"
              onClick={handleInquireClick}
              className="inline-flex items-center gap-1.5 rounded-lg border border-[var(--rbpc-highlight-border)] bg-[var(--rbpc-surface-elevated)] px-3.5 py-2 text-xs font-semibold text-[var(--rbpc-highlight)] hover:bg-[var(--rbpc-highlight-subtle)] transition-colors min-h-[44px] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--rbpc-focus,#1E675A)] focus-visible:ring-offset-2"
              aria-label={isEn ? "Open workshop inquiry modal" : "Mở phiếu yêu cầu trải nghiệm xưởng nghề"}
              data-testid="living-bridge-inquire-modal-trigger"
            >
              <Calendar className="h-3.5 w-3.5" aria-hidden="true" />
              <span>{isEn ? "Workshop Inquiry" : "Yêu cầu lịch hẹn xưởng nghề"}</span>
            </button>
          )}
        </div>

        <span className="text-[11px] text-[var(--rbpc-muted)]">
          {isEn ? "Preserving Hue's Living Craft Lineage" : "Gìn giữ ngọn lửa nghề Cố đô"}
        </span>
      </div>

      {/* Workshop Inquiry Modal with Pre-Selected Experience Slug */}
      {enableInquiryModal && modalExperience && (
        <InquiryFormModal
          isOpen={isInquiryOpen}
          onClose={() => setIsInquiryOpen(false)}
          experience={modalExperience}
          locale={locale}
          onSubmit={onInquirySubmit}
        />
      )}
    </article>
  );
}

LivingBridgeCard.displayName = "LivingBridgeCard";

export default LivingBridgeCard;
