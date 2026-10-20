"use client";

import React, { forwardRef } from "react";
import {
  Landmark,
  Hammer,
  Layers,
  Compass,
  EyeOff,
  ScrollText,
  BookOpen,
  Crown,
  HelpCircle,
} from "lucide-react";
import { cn } from "@/lib/utils";
import type { ImperialSiteCondition, LearningLevel } from "@/lib/imperial/map-types";

export type ConditionKey =
  | ImperialSiteCondition
  | "nguyen_ven"
  | "phuc_dung"
  | "phe_tich"
  | "khao_co"
  | "mat_dau";

export type LearningLevelKey =
  | LearningLevel
  | "L1"
  | "L2"
  | "L3"
  | "L1_DOCUMENTED"
  | "L2_ANALYZED"
  | "L2_LEARNING_READY"
  | "L3_SYNTHESIZED";

export type StatusPillSize = "xs" | "sm" | "md" | "lg";
export type StatusPillVariant = "subtle" | "solid" | "outline";

export interface StatusPillProps
  extends React.HTMLAttributes<HTMLSpanElement> {
  type?: "condition" | "learning" | "auto";
  condition?: ConditionKey;
  level?: LearningLevelKey;
  variant?: StatusPillVariant;
  size?: StatusPillSize;
  showIcon?: boolean;
  showDot?: boolean;
  label?: string;
}

interface ItemConfig {
  label: string;
  subtleClass: string;
  solidClass: string;
  outlineClass: string;
  dotColor: string;
  icon: React.ComponentType<{ className?: string }>;
}

const CONDITION_CONFIG: Record<string, ItemConfig> = {
  extant: {
    label: "Nguyên vẹn",
    subtleClass:
      "bg-[color-mix(in_srgb,var(--ln-green)_12%,transparent)] text-ln-green border-[color-mix(in_srgb,var(--ln-green)_30%,transparent)]",
    solidClass: "bg-ln-green text-white border-transparent",
    outlineClass: "bg-transparent text-ln-green border-ln-green/60",
    dotColor: "bg-ln-green",
    icon: Landmark,
  },
  reconstructed: {
    label: "Đã phục dựng",
    subtleClass:
      "bg-[color-mix(in_srgb,var(--ln-blue)_12%,transparent)] text-ln-blue border-[color-mix(in_srgb,var(--ln-blue)_30%,transparent)]",
    solidClass: "bg-ln-blue text-white border-transparent",
    outlineClass: "bg-transparent text-ln-blue border-ln-blue/60",
    dotColor: "bg-ln-blue",
    icon: Hammer,
  },
  ruin: {
    label: "Phế tích / Nền móng",
    subtleClass:
      "bg-[color-mix(in_srgb,var(--ln-gold)_15%,transparent)] text-ln-gold border-[color-mix(in_srgb,var(--ln-gold)_35%,transparent)]",
    solidClass: "bg-ln-gold text-[#2A241D] font-bold border-transparent",
    outlineClass: "bg-transparent text-ln-gold border-ln-gold/60",
    dotColor: "bg-ln-gold",
    icon: Layers,
  },
  archaeological: {
    label: "Khảo cổ học",
    subtleClass:
      "bg-purple-500/12 text-purple-700 dark:text-purple-300 border-purple-500/30",
    solidClass: "bg-purple-700 text-white border-transparent",
    outlineClass: "bg-transparent text-purple-700 dark:text-purple-400 border-purple-500/60",
    dotColor: "bg-purple-600",
    icon: Compass,
  },
  lost: {
    label: "Đã mất dấu",
    subtleClass:
      "bg-stone-500/12 text-stone-700 dark:text-stone-300 border-stone-500/30",
    solidClass: "bg-stone-700 text-white border-transparent",
    outlineClass: "bg-transparent text-stone-700 dark:text-stone-300 border-stone-500/60",
    dotColor: "bg-stone-500",
    icon: EyeOff,
  },
  unknown: {
    label: "Chưa khảo sát",
    subtleClass:
      "bg-ln-surface-muted text-ln-ink-muted border-ln-border",
    solidClass: "bg-ln-ink text-white border-transparent",
    outlineClass: "bg-transparent text-ln-ink-muted border-ln-border",
    dotColor: "bg-ln-ink-muted",
    icon: HelpCircle,
  },
};

// Aliases for Vietnamese input convenience
CONDITION_CONFIG.nguyen_ven = CONDITION_CONFIG.extant;
CONDITION_CONFIG.phuc_dung = CONDITION_CONFIG.reconstructed;
CONDITION_CONFIG.phe_tich = CONDITION_CONFIG.ruin;
CONDITION_CONFIG.khao_co = CONDITION_CONFIG.archaeological;
CONDITION_CONFIG.mat_dau = CONDITION_CONFIG.lost;

const LEARNING_CONFIG: Record<string, ItemConfig> = {
  L1: {
    label: "L1: Tư liệu hóa",
    subtleClass:
      "bg-stone-500/12 text-stone-700 dark:text-stone-300 border-stone-500/30",
    solidClass: "bg-stone-700 text-white border-transparent",
    outlineClass: "bg-transparent text-stone-700 dark:text-stone-300 border-stone-500/50",
    dotColor: "bg-stone-500",
    icon: ScrollText,
  },
  L2: {
    label: "L2: Phân tích tư liệu",
    subtleClass:
      "bg-[color-mix(in_srgb,var(--ln-blue)_12%,transparent)] text-ln-blue border-[color-mix(in_srgb,var(--ln-blue)_30%,transparent)]",
    solidClass: "bg-ln-blue text-white border-transparent",
    outlineClass: "bg-transparent text-ln-blue border-ln-blue/60",
    dotColor: "bg-ln-blue",
    icon: BookOpen,
  },
  L3: {
    label: "L3: Tổng hợp chuyên sâu",
    subtleClass:
      "bg-[color-mix(in_srgb,var(--ln-gold)_15%,transparent)] text-ln-gold border-[color-mix(in_srgb,var(--ln-gold)_35%,transparent)]",
    solidClass: "bg-ln-gold text-[#2A241D] font-bold border-transparent",
    outlineClass: "bg-transparent text-ln-gold border-ln-gold/60",
    dotColor: "bg-ln-gold",
    icon: Crown,
  },
};

LEARNING_CONFIG.L1_DOCUMENTED = LEARNING_CONFIG.L1;
LEARNING_CONFIG.L2_ANALYZED = LEARNING_CONFIG.L2;
LEARNING_CONFIG.L2_LEARNING_READY = LEARNING_CONFIG.L2;
LEARNING_CONFIG.L3_SYNTHESIZED = LEARNING_CONFIG.L3;

const SIZE_STYLES: Record<StatusPillSize, string> = {
  xs: "text-[10px] px-2 py-0.5 gap-1 font-semibold",
  sm: "text-[11px] px-2.5 py-0.5 gap-1.5 font-medium",
  md: "text-xs px-3 py-1 gap-1.5 font-medium",
  lg: "text-sm px-3.5 py-1.5 gap-2 font-medium",
};

export const StatusPill = forwardRef<HTMLSpanElement, StatusPillProps>(
  (
    {
      type = "auto",
      condition,
      level,
      variant = "subtle",
      size = "md",
      showIcon = true,
      showDot = false,
      label,
      className,
      ...props
    },
    ref,
  ) => {
    // Resolve mode and configuration
    let config: ItemConfig | undefined;

    if (type === "condition" || (!level && condition)) {
      const cKey = (condition || "unknown").toLowerCase();
      config = CONDITION_CONFIG[cKey] || CONDITION_CONFIG.unknown;
    } else if (type === "learning" || level) {
      const lKey = level || "L1";
      config = LEARNING_CONFIG[lKey] || LEARNING_CONFIG.L1;
    } else {
      config = CONDITION_CONFIG.unknown;
    }

    const displayText = label || config.label;
    const IconComponent = config.icon;

    let styleClass = config.subtleClass;
    if (variant === "solid") styleClass = config.solidClass;
    else if (variant === "outline") styleClass = config.outlineClass;

    return (
      <span
        ref={ref}
        className={cn(
          "inline-flex w-fit shrink-0 items-center justify-center rounded-full border select-none tracking-wide transition-colors",
          styleClass,
          SIZE_STYLES[size],
          className,
        )}
        {...props}
      >
        {showDot && (
          <span
            aria-hidden="true"
            className={cn("h-1.5 w-1.5 rounded-full shrink-0", config.dotColor)}
          />
        )}
        {showIcon && (
          <span className="shrink-0 flex items-center justify-center [&>svg]:size-3.5">
            <IconComponent />
          </span>
        )}
        <span>{displayText}</span>
      </span>
    );
  },
);

StatusPill.displayName = "StatusPill";
