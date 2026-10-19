"use client";

import * as React from "react";
import { Check, Clock, FileCheck, Award, Sparkles } from "lucide-react";
import { cn } from "@/lib/utils";
import type { RbpcLocale } from "@/lib/rbpc/copy";

export type EvidenceStageCode = "S0" | "S1" | "S2" | "S3" | "S4";
export type EvidenceStageInput = EvidenceStageCode | 0 | 1 | 2 | 3 | 4 | string;

export interface EvidenceStageMeta {
  code: EvidenceStageCode;
  step: number;
  labelVi: string;
  labelEn: string;
  subtitleVi: string;
  subtitleEn: string;
  descriptionVi: string;
  descriptionEn: string;
  eligibilityVi: string;
  eligibilityEn: string;
  badgeClass: string;
  textClass: string;
  bgClass: string;
  borderClass: string;
}

export const EVIDENCE_STAGES: Record<EvidenceStageCode, EvidenceStageMeta> = {
  S0: {
    code: "S0",
    step: 0,
    labelVi: "Chưa kiểm chứng",
    labelEn: "Discovered Title Only",
    subtitleVi: "Tiêu đề ghi nhận ban đầu",
    subtitleEn: "Unreviewed Candidate",
    descriptionVi:
      "Bản ghi mới được ghi nhận từ danh mục; chưa qua đối chiếu thư tịch hoặc kiểm tra thực địa.",
    descriptionEn:
      "Initial title captured from catalogue; pending archival corroboration and field check.",
    eligibilityVi: "Chưa xuất bản (Unpublished)",
    eligibilityEn: "Unpublished",
    badgeClass: "bg-[var(--rbpc-badge-gap-bg)] text-[var(--rbpc-badge-gap-text)] border-[var(--rbpc-badge-gap-border)]",
    textClass: "text-[var(--rbpc-badge-gap-text)]",
    bgClass: "bg-[var(--rbpc-badge-gap-bg)]",
    borderClass: "border-[var(--rbpc-badge-gap-border)]",
  },
  S1: {
    code: "S1",
    step: 1,
    labelVi: "Đã định danh nguồn",
    labelEn: "Source-Backed Draft",
    subtitleVi: "Thông tin cơ bản + Mã định danh chính thức",
    subtitleEn: "Source-backed basic facts + Authoritative ID",
    descriptionVi:
      "Đã xác định mã di tích UNESCO hoặc hồ sơ lưu trữ chính thức; đang biên tập nội dung.",
    descriptionEn:
      "Authoritative ID (e.g. UNESCO Ref 678) confirmed; basic factual claims drafted.",
    eligibilityVi: "Bản thảo nghiên cứu (Draft)",
    eligibilityEn: "Candidate Draft",
    badgeClass: "bg-[var(--rbpc-warning-subtle)] text-[#8F5938] border-[var(--rbpc-warning-border)]",
    textClass: "text-[#8F5938]",
    bgClass: "bg-[var(--rbpc-warning-subtle)]",
    borderClass: "border-[var(--rbpc-warning-border)]",
  },
  S2: {
    code: "S2",
    step: 2,
    labelVi: "Ban biên tập duyệt",
    labelEn: "Editor-Reviewed",
    subtitleVi: "Tối thiểu 2 nguồn thư tịch đối chiếu",
    subtitleEn: "Min 2 source citations + Rights checked",
    descriptionVi:
      "Đã đối chiếu ít nhất 2 nguồn tư liệu tin cậy; kiểm tra bản quyền hình ảnh; đủ điều kiện công bố.",
    descriptionEn:
      "Corroborated by ≥2 authoritative citations, rights verified; cleared for public browse.",
    eligibilityVi: "Đủ điều kiện xuất bản (Publishable)",
    eligibilityEn: "Publishable",
    badgeClass: "bg-[var(--rbpc-primary-subtle)] text-[var(--rbpc-primary)] border-[var(--rbpc-primary-border)]",
    textClass: "text-[var(--rbpc-primary)]",
    bgClass: "bg-[var(--rbpc-primary-subtle)]",
    borderClass: "border-[var(--rbpc-primary-border)]",
  },
  S3: {
    code: "S3",
    step: 3,
    labelVi: "Khảo cứu chuyên sâu",
    labelEn: "Featured Research",
    subtitleVi: "Đa góc nhìn + Dòng thời gian liên kết",
    subtitleEn: "Deeper multiview history + Relations",
    descriptionVi:
      "Nghiên cứu đa chiều hoàn chỉnh, phục dựng bối cảnh, liên kết mạng lưới di sản và đã ký duyệt chuyên môn.",
    descriptionEn:
      "Comprehensive multi-perspective history, architectural context, and relational links.",
    eligibilityVi: "Bản ghi nổi bật (Featured)",
    eligibilityEn: "Featured",
    badgeClass: "bg-[var(--rbpc-success-subtle)] text-[var(--rbpc-success)] border-[var(--rbpc-success-border)]",
    textClass: "text-[var(--rbpc-success)]",
    bgClass: "bg-[var(--rbpc-success-subtle)]",
    borderClass: "border-[var(--rbpc-success-border)]",
  },
  S4: {
    code: "S4",
    step: 4,
    labelVi: "Đối tác xác thực",
    labelEn: "Living Heritage Partner",
    subtitleVi: "Nghệ nhân sống + Điều khoản trải nghiệm minh bạch",
    subtitleEn: "Living creator + Commerce permission",
    descriptionVi:
      "Kết nối trực tiếp nghệ nhân di sản sống; có văn bản đồng thuận; minh bạch điều khoản trải nghiệm.",
    descriptionEn:
      "Direct bridge to verified living artisan, written consent signed, transparent inquiry terms.",
    eligibilityVi: "Mở yêu cầu trải nghiệm (Eligible for CTA)",
    eligibilityEn: "Eligible for CTA",
    badgeClass: "bg-[var(--rbpc-highlight-subtle)] text-[var(--rbpc-highlight)] border-[var(--rbpc-highlight-border)]",
    textClass: "text-[var(--rbpc-highlight)]",
    bgClass: "bg-[var(--rbpc-highlight-subtle)]",
    borderClass: "border-[var(--rbpc-highlight-border)]",
  },
};

export function parseEvidenceStage(input: EvidenceStageInput): EvidenceStageMeta {
  if (typeof input === "number") {
    const clamped = Math.max(0, Math.min(4, Math.floor(input))) as 0 | 1 | 2 | 3 | 4;
    const code = `S${clamped}` as EvidenceStageCode;
    return EVIDENCE_STAGES[code];
  }

  const str = String(input).toUpperCase().trim();
  if (str in EVIDENCE_STAGES) {
    return EVIDENCE_STAGES[str as EvidenceStageCode];
  }

  // Handle stage names or numbers in string format ("s2", "2", "stage2")
  const match = str.match(/([0-4])/);
  if (match) {
    const code = `S${match[1]}` as EvidenceStageCode;
    return EVIDENCE_STAGES[code];
  }

  return EVIDENCE_STAGES.S0;
}

export type EvidenceStatusVariant = "compact" | "pill" | "stepper" | "detailed";

export interface EvidenceStatusProps extends React.HTMLAttributes<HTMLDivElement> {
  /** Review stage input: "S0", "S1", "S2", "S3", "S4" or numeric 0..4 */
  stage: EvidenceStageInput;
  /** Display variant aligning with editorial density */
  variant?: EvidenceStatusVariant;
  /** Interface language locale */
  locale?: RbpcLocale;
  /** Whether to show descriptive subtitle in compact / pill variants */
  showSubtitle?: boolean;
  /** Interactive touch-target container */
  interactive?: boolean;
}

/**
 * EvidenceStatus — Compact Indicator for Content Review Stage (S0 to S4)
 *
 * Implements Master Spec §1300 Record Completeness Rubric:
 * - S0: Discovered Title Only -> Unpublished
 * - S1: Source-Backed Basic Facts + Authoritative ID -> Candidate Draft
 * - S2: Editor-Reviewed Narrative + Min 2 Source Citations -> Publishable
 * - S3: Deeper Multiview History + Verified Timeline & Relations -> Featured
 * - S4: Living Creator and Commerce Permission + Profile + Booking Terms -> Eligible for CTA
 */
export const EvidenceStatus = React.forwardRef<HTMLDivElement, EvidenceStatusProps>(
  (
    {
      stage,
      variant = "compact",
      locale = "vi",
      showSubtitle = false,
      interactive = false,
      className,
      onClick,
      ...props
    },
    ref
  ) => {
    const currentMeta = parseEvidenceStage(stage);
    const isEn = locale === "en";

    const label = isEn ? currentMeta.labelEn : currentMeta.labelVi;
    const subtitle = isEn ? currentMeta.subtitleEn : currentMeta.subtitleVi;
    const description = isEn ? currentMeta.descriptionEn : currentMeta.descriptionVi;
    const eligibility = isEn ? currentMeta.eligibilityEn : currentMeta.eligibilityVi;

    const isInteractive = interactive || Boolean(onClick);

    // Variant 1: Compact inline badge (S0..S4 code + label)
    if (variant === "compact") {
      return (
        <div
          ref={ref}
          role="status"
          aria-label={`${currentMeta.code}: ${label} — ${subtitle}`}
          title={`${currentMeta.code} · ${label}: ${description}`}
          onClick={onClick}
          className={cn(
            "inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full border text-xs font-medium font-sans select-none transition-colors",
            currentMeta.badgeClass,
            isInteractive && [
              "rbpc-touch-target min-h-[44px] cursor-pointer hover:opacity-90",
              "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--rbpc-focus)] focus-visible:ring-offset-1",
            ],
            className
          )}
          {...props}
        >
          <span className="font-mono font-bold tracking-tight">{currentMeta.code}</span>
          <span className="h-1 w-1 rounded-full bg-current opacity-60" aria-hidden="true" />
          <span className="truncate">{label}</span>
          {showSubtitle && (
            <span className="hidden sm:inline text-[11px] opacity-75 font-normal">
              ({subtitle})
            </span>
          )}
        </div>
      );
    }

    // Variant 2: Pill badge with visual dot
    if (variant === "pill") {
      return (
        <div
          ref={ref}
          role="status"
          aria-label={`${currentMeta.code} - ${label}`}
          title={`${label}: ${description}`}
          onClick={onClick}
          className={cn(
            "inline-flex items-center gap-2 px-3 py-1.5 rounded-full border text-xs font-medium select-none",
            currentMeta.badgeClass,
            isInteractive && "cursor-pointer hover:opacity-90 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--rbpc-focus)]",
            className
          )}
          {...props}
        >
          <span className="h-2 w-2 rounded-full bg-current shrink-0" aria-hidden="true" />
          <span className="font-mono font-bold">{currentMeta.code}</span>
          <span className="font-medium">{label}</span>
        </div>
      );
    }

    // Variant 3: Sequential 5-step milestone stepper (S0 to S4)
    if (variant === "stepper") {
      const allCodes: EvidenceStageCode[] = ["S0", "S1", "S2", "S3", "S4"];

      return (
        <div
          ref={ref}
          role="status"
          aria-label={`${isEn ? "Verification Progress" : "Tiến độ kiểm chứng"}: ${currentMeta.code} - ${label}`}
          className={cn("w-full space-y-2 select-none", className)}
          {...props}
        >
          {/* Progress bar line */}
          <div className="grid grid-cols-5 gap-1.5" aria-hidden="true">
            {allCodes.map((code, idx) => {
              const isPassed = idx <= currentMeta.step;
              const isCurrent = idx === currentMeta.step;

              return (
                <div key={code} className="flex flex-col gap-1">
                  <div
                    className={cn(
                      "h-1.5 rounded-full transition-all",
                      isPassed
                        ? idx === 4
                          ? "bg-[var(--rbpc-highlight)]"
                          : idx >= 2
                          ? "bg-[var(--rbpc-primary)]"
                          : "bg-[var(--rbpc-warning)]"
                        : "bg-[var(--rbpc-divider)]"
                    )}
                  />
                  <div className="flex items-center justify-between text-[11px] font-mono px-0.5">
                    <span
                      className={cn(
                        "font-semibold",
                        isCurrent
                          ? "text-[var(--rbpc-ink)]"
                          : isPassed
                          ? "text-[var(--rbpc-primary)]"
                          : "text-[var(--rbpc-muted)]"
                      )}
                    >
                      {code}
                    </span>
                    {isCurrent && (
                      <span className="h-1 w-1 rounded-full bg-[var(--rbpc-primary)]" />
                    )}
                  </div>
                </div>
              );
            })}
          </div>

          {/* Current Milestone label */}
          <div className="flex items-center justify-between text-xs text-[var(--rbpc-muted)] pt-0.5">
            <span className="font-medium text-[var(--rbpc-ink)]">
              {currentMeta.code}: {label}
            </span>
            <span className="text-[11px] text-[var(--rbpc-primary)] font-medium">
              {eligibility}
            </span>
          </div>
        </div>
      );
    }

    // Variant 4: Detailed editorial callout card
    return (
      <div
        ref={ref}
        role="status"
        aria-label={`${currentMeta.code} · ${label}`}
        className={cn(
          "rounded-[var(--rbpc-radius-md)] border p-4 bg-[var(--rbpc-surface)] shadow-[var(--rbpc-shadow-sm)] space-y-3",
          currentMeta.borderClass,
          className
        )}
        {...props}
      >
        <div className="flex items-center justify-between gap-3">
          <div className="flex items-center gap-2.5">
            <span
              className={cn(
                "inline-flex items-center justify-center font-mono font-bold text-xs h-7 px-2.5 rounded-full border",
                currentMeta.badgeClass
              )}
            >
              {currentMeta.code}
            </span>
            <div>
              <h4 className="font-serif font-semibold text-sm text-[var(--rbpc-ink)]">
                {label}
              </h4>
              <p className="text-xs text-[var(--rbpc-muted)]">{subtitle}</p>
            </div>
          </div>

          <span className="text-xs font-medium px-2 py-0.5 rounded bg-[var(--rbpc-bg)] text-[var(--rbpc-ink-subtle)] border border-[var(--rbpc-divider-subtle)]">
            {eligibility}
          </span>
        </div>

        <p className="text-xs text-[var(--rbpc-ink-subtle)] leading-relaxed">
          {description}
        </p>

        {/* Milestone checklist preview */}
        <div className="pt-2 border-t border-[var(--rbpc-divider-subtle)] grid grid-cols-2 gap-2 text-[11px] text-[var(--rbpc-muted)]">
          <div className="flex items-center gap-1.5">
            {currentMeta.step >= 1 ? (
              <Check className="h-3.5 w-3.5 text-[var(--rbpc-success)]" />
            ) : (
              <Clock className="h-3.5 w-3.5 text-[var(--rbpc-muted)]" />
            )}
            <span>{isEn ? "Archival ID confirmed" : "Định danh hồ sơ lưu trữ"}</span>
          </div>
          <div className="flex items-center gap-1.5">
            {currentMeta.step >= 2 ? (
              <Check className="h-3.5 w-3.5 text-[var(--rbpc-success)]" />
            ) : (
              <FileCheck className="h-3.5 w-3.5 text-[var(--rbpc-muted)]" />
            )}
            <span>{isEn ? "≥2 sources corroborated" : "≥2 nguồn đối chiếu"}</span>
          </div>
          <div className="flex items-center gap-1.5">
            {currentMeta.step >= 3 ? (
              <Check className="h-3.5 w-3.5 text-[var(--rbpc-success)]" />
            ) : (
              <Award className="h-3.5 w-3.5 text-[var(--rbpc-muted)]" />
            )}
            <span>{isEn ? "Editorial sign-off" : "Hội đồng học thuật duyệt"}</span>
          </div>
          <div className="flex items-center gap-1.5">
            {currentMeta.step >= 4 ? (
              <Check className="h-3.5 w-3.5 text-[var(--rbpc-highlight)]" />
            ) : (
              <Sparkles className="h-3.5 w-3.5 text-[var(--rbpc-muted)]" />
            )}
            <span>{isEn ? "Living artisan consent" : "Đồng thuận nghệ nhân"}</span>
          </div>
        </div>
      </div>
    );
  }
);

EvidenceStatus.displayName = "EvidenceStatus";
