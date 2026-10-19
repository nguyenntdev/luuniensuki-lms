"use client";

import * as React from "react";
import {
  CheckCircle2,
  BookOpen,
  Sparkles,
  AlertCircle,
  Landmark,
  UserCheck,
  Flame,
  Library,
} from "lucide-react";
import { cn } from "@/lib/utils";
import {
  getEpistemicBadgeCopy,
  type RbpcLocale,
  type EpistemicStatusItem,
} from "@/lib/rbpc/copy";

export type EpistemicStatusKey =
  | "verified_source"
  | "verified"
  | "Verified by source"
  | "traditional_account"
  | "tradition"
  | "Traditional account"
  | "academic_interpretation"
  | "interpretation"
  | "Academic interpretation"
  | "evidence_gap"
  | "gap"
  | "Evidence gap"
  | "unesco_inscribed"
  | "unesco"
  | "unesco_678"
  | "UNESCO 678 Component"
  | "living_tradition"
  | "human_reviewed"
  | "pre_existing_research";

export type EpistemicBadgeSize = "sm" | "md" | "lg";

export interface EpistemicBadgeProps
  extends React.HTMLAttributes<HTMLSpanElement> {
  /** Epistemic status key or canonical identifier */
  status: EpistemicStatusKey | string;
  /** Language locale for microcopy (defaults to "vi") */
  locale?: RbpcLocale;
  /** Size variant */
  size?: EpistemicBadgeSize;
  /** Whether to render the visual dot indicator */
  showDot?: boolean;
  /** Whether to render the status icon */
  showIcon?: boolean;
  /** Optional custom label overriding the canonical dictionary */
  labelOverride?: string;
  /** Optional custom tooltip/description */
  descriptionOverride?: string;
  /** Makes badge keyboard focusable and interactive */
  interactive?: boolean;
}

/**
 * Normalizes user-facing or technical status strings into canonical dictionary IDs.
 */
function normalizeStatusId(rawStatus: string): string {
  const normalized = rawStatus.trim().toLowerCase().replace(/[\s-]+/g, "_");

  switch (normalized) {
    case "verified_by_source":
    case "verified":
    case "verified_source":
      return "verified_source";

    case "traditional_account":
    case "tradition":
    case "traditional":
      return "traditional_account";

    case "academic_interpretation":
    case "interpretation":
      return "academic_interpretation";

    case "evidence_gap":
    case "gap":
      return "evidence_gap";

    case "unesco_678_component":
    case "unesco_678":
    case "unesco":
    case "unesco_inscribed":
      return "unesco_inscribed";

    case "living_tradition":
      return "living_tradition";

    case "human_reviewed":
      return "human_reviewed";

    case "pre_existing_research":
      return "pre_existing_research";

    default:
      return normalized;
  }
}

/**
 * Maps canonical status IDs to an appropriate Lucide icon.
 */
function getStatusIcon(statusId: string) {
  switch (statusId) {
    case "unesco_inscribed":
      return Landmark;
    case "verified_source":
      return CheckCircle2;
    case "traditional_account":
      return Sparkles;
    case "academic_interpretation":
      return BookOpen;
    case "evidence_gap":
      return AlertCircle;
    case "living_tradition":
      return Flame;
    case "human_reviewed":
      return UserCheck;
    case "pre_existing_research":
      return Library;
    default:
      return AlertCircle;
  }
}

const sizeClasses: Record<EpistemicBadgeSize, { badge: string; icon: string; dot: string }> = {
  sm: {
    badge: "text-[11px] px-2 py-0.5 gap-1 min-h-[22px]",
    icon: "h-3 w-3",
    dot: "h-1.5 w-1.5",
  },
  md: {
    badge: "text-xs px-2.5 py-1 gap-1.5 min-h-[26px]",
    icon: "h-3.5 w-3.5",
    dot: "h-1.5 w-1.5",
  },
  lg: {
    badge: "text-sm px-3.5 py-1.5 gap-2 min-h-[32px]",
    icon: "h-4 w-4",
    dot: "h-2 w-2",
  },
};

/**
 * EpistemicBadge — Historical Certainty & Provenance Indicator
 *
 * Implements the core epistemic honesty principle of LƯU NIÊN:
 * Visible, honest provenance markers differentiating verified archival facts,
 * living folk traditions, academic interpretations, and explicit evidence gaps.
 */
export const EpistemicBadge = React.forwardRef<HTMLSpanElement, EpistemicBadgeProps>(
  (
    {
      status,
      locale = "vi",
      size = "md",
      showDot = true,
      showIcon = true,
      labelOverride,
      descriptionOverride,
      interactive = false,
      className,
      onClick,
      ...props
    },
    ref
  ) => {
    const canonicalId = normalizeStatusId(status);
    const badgeCopy: EpistemicStatusItem = getEpistemicBadgeCopy(canonicalId, locale);

    const displayLabel = labelOverride || badgeCopy.label;
    const tooltipText = descriptionOverride || badgeCopy.description;
    const IconComponent = getStatusIcon(canonicalId);
    const currentSize = sizeClasses[size];

    const isClickable = interactive || Boolean(onClick);

    return (
      <span
        ref={ref}
        role="status"
        title={tooltipText || displayLabel}
        aria-label={`${displayLabel}${tooltipText ? `: ${tooltipText}` : ""}`}
        tabIndex={isClickable ? 0 : undefined}
        onClick={onClick}
        className={cn(
          "rbpc-badge inline-flex items-center font-sans font-medium rounded-full border transition-colors select-none",
          badgeCopy.badgeClass,
          currentSize.badge,
          isClickable && [
            "cursor-pointer hover:opacity-90 active:scale-[0.98]",
            "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--rbpc-focus)] focus-visible:ring-offset-1",
          ],
          className
        )}
        {...props}
      >
        {showDot && (
          <span
            className={cn("rbpc-badge-dot rounded-full shrink-0", currentSize.dot)}
            aria-hidden="true"
          />
        )}
        {showIcon && (
          <IconComponent
            className={cn("shrink-0", currentSize.icon)}
            aria-hidden="true"
          />
        )}
        <span className="truncate leading-none">{displayLabel}</span>
      </span>
    );
  }
);

EpistemicBadge.displayName = "EpistemicBadge";
