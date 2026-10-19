"use client";

import * as React from "react";
import {
  CheckCircle2,
  AlertTriangle,
  Ban,
  HelpCircle,
  XCircle,
  Landmark,
} from "lucide-react";
import { cn } from "@/lib/utils";

export type LicenseBadgeTier =
  | "approved_cc_by"
  | "blocked_nc"
  | "blocked_noai"
  | "institutional_record"
  | "review_pending"
  | "rejected_inaccurate";

export interface LicenseBadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  tier?: LicenseBadgeTier;
  licenseText?: string;
  noai?: boolean;
  showIcon?: boolean;
  showDescription?: boolean;
  size?: "sm" | "md" | "lg";
  className?: string;
}

interface BadgeConfig {
  defaultLabel: string;
  accessibleDescription: string;
  bgClass: string;
  textClass: string;
  borderClass: string;
  icon: React.ComponentType<{ className?: string; "aria-hidden"?: boolean | "true" | "false" }>;
}

const BADGE_CONFIGS: Record<LicenseBadgeTier, BadgeConfig> = {
  approved_cc_by: {
    defaultLabel: "CC BY 4.0",
    accessibleDescription: "Được phép nhúng với quyền ghi nhận tác giả (CC BY 4.0)",
    bgClass: "bg-emerald-50 dark:bg-emerald-950/40",
    textClass: "text-emerald-700 dark:text-emerald-300",
    borderClass: "border-emerald-300 dark:border-emerald-800",
    icon: CheckCircle2,
  },
  blocked_nc: {
    defaultLabel: "CC BY-NC-SA",
    accessibleDescription: "Giới hạn phi thương mại (CC BY-NC-SA). Chỉ dùng tra cứu.",
    bgClass: "bg-amber-50 dark:bg-amber-950/40",
    textClass: "text-amber-700 dark:text-amber-300",
    borderClass: "border-amber-300 dark:border-amber-800",
    icon: AlertTriangle,
  },
  blocked_noai: {
    defaultLabel: "NoAI Protected",
    accessibleDescription: "Cấm thu thập dữ liệu huấn luyện AI (NoAI Protected)",
    bgClass: "bg-purple-50 dark:bg-purple-950/40",
    textClass: "text-purple-700 dark:text-purple-300",
    borderClass: "border-purple-300 dark:border-purple-800",
    icon: Ban,
  },
  institutional_record: {
    defaultLabel: "Institutional Record",
    accessibleDescription: "Hồ sơ lưu trữ bảo tàng / cơ quan quản lý (Institutional Record)",
    bgClass: "bg-blue-50 dark:bg-blue-950/40",
    textClass: "text-blue-700 dark:text-blue-300",
    borderClass: "border-blue-300 dark:border-blue-800",
    icon: Landmark,
  },
  review_pending: {
    defaultLabel: "Needs Rights Review",
    accessibleDescription: "Đang liên hệ tác giả xin cấp phép bản quyền",
    bgClass: "bg-slate-50 dark:bg-slate-900/40",
    textClass: "text-slate-600 dark:text-slate-400",
    borderClass: "border-slate-300 dark:border-slate-700",
    icon: HelpCircle,
  },
  rejected_inaccurate: {
    defaultLabel: "Rejected / Inaccurate",
    accessibleDescription: "Mô hình không bảo đảm tính chuẩn xác lịch sử (Bị từ chối)",
    bgClass: "bg-rose-50 dark:bg-rose-950/40",
    textClass: "text-rose-700 dark:text-rose-300",
    borderClass: "border-rose-300 dark:border-rose-800",
    icon: XCircle,
  },
};

/**
 * Resolves the license tier from explicit tier or raw license text + flags.
 */
export function resolveLicenseBadgeTier(
  tier?: LicenseBadgeTier,
  licenseText?: string,
  noai?: boolean
): LicenseBadgeTier {
  if (tier) return tier;

  if (noai && (!licenseText || licenseText.toUpperCase().includes("NOAI"))) {
    return "blocked_noai";
  }

  if (!licenseText) return "review_pending";

  const upper = licenseText.toUpperCase().trim();

  if (upper.includes("NOAI")) {
    return "blocked_noai";
  }
  if (upper.includes("NC") || upper.includes("NON-COMMERCIAL") || upper.includes("NONCOMMERCIAL")) {
    return "blocked_nc";
  }
  if (upper.includes("CC BY") || upper.includes("CC-BY")) {
    return "approved_cc_by";
  }
  if (
    upper.includes("INSTITUTION") ||
    upper.includes("BẢO TÀNG") ||
    upper.includes("LƯU TRỮ") ||
    upper.includes("RECORD") ||
    upper.includes("PUBLIC DOMAIN")
  ) {
    return "institutional_record";
  }
  if (upper.includes("REJECT") || upper.includes("INACCURATE") || upper.includes("TỪ CHỐI")) {
    return "rejected_inaccurate";
  }
  if (upper.includes("REVIEW") || upper.includes("NOT STATED") || upper.includes("CHƯA XÁC ĐỊNH")) {
    return "review_pending";
  }

  return "review_pending";
}

const SIZE_CLASSES = {
  sm: {
    badge: "px-2 py-0.5 text-[10px] gap-1",
    icon: "size-3",
  },
  md: {
    badge: "px-2.5 py-1 text-xs gap-1.5",
    icon: "size-3.5",
  },
  lg: {
    badge: "px-3 py-1.5 text-sm gap-2",
    icon: "size-4",
  },
};

export function LicenseBadge({
  tier: propTier,
  licenseText,
  noai = false,
  showIcon = true,
  showDescription = false,
  size = "md",
  className,
  ...props
}: LicenseBadgeProps) {
  const resolvedTier = resolveLicenseBadgeTier(propTier, licenseText, noai);
  const config = BADGE_CONFIGS[resolvedTier] || BADGE_CONFIGS.review_pending;
  const label = licenseText || config.defaultLabel;
  const IconComponent = config.icon;
  const sizeConfig = SIZE_CLASSES[size] || SIZE_CLASSES.md;

  return (
    <span
      role="status"
      aria-label={`${label} — ${config.accessibleDescription}`}
      title={config.accessibleDescription}
      className={cn(
        "inline-flex items-center font-medium rounded-full border tracking-wide uppercase select-none transition-colors",
        config.bgClass,
        config.textClass,
        config.borderClass,
        sizeConfig.badge,
        className
      )}
      {...props}
    >
      {showIcon && (
        <IconComponent
          className={cn("shrink-0", sizeConfig.icon)}
          aria-hidden="true"
        />
      )}
      <span className="font-semibold">{label}</span>
      {showDescription && (
        <span className="normal-case text-[11px] opacity-80 border-l border-current/20 pl-1.5 ml-0.5">
          {config.accessibleDescription}
        </span>
      )}
    </span>
  );
}

export default LicenseBadge;
