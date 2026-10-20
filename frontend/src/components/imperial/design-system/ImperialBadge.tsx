"use client";

import React, { forwardRef } from "react";
import { Slot } from "@radix-ui/react-slot";
import { cn } from "@/lib/utils";

export type ImperialBadgeVariant =
  | "vermilion"
  | "red"
  | "gold"
  | "blue"
  | "green"
  | "ink"
  | "parchment";

export type ImperialBadgeAppearance = "subtle" | "solid" | "outline" | "ghost";
export type ImperialBadgeSize = "xs" | "sm" | "md" | "lg";

export interface ImperialBadgeProps
  extends React.HTMLAttributes<HTMLSpanElement> {
  variant?: ImperialBadgeVariant;
  appearance?: ImperialBadgeAppearance;
  size?: ImperialBadgeSize;
  icon?: React.ReactNode;
  rightIcon?: React.ReactNode;
  dot?: boolean | "pulse";
  asChild?: boolean;
}

// Normalized color key
function normalizeVariant(
  v: ImperialBadgeVariant,
): "vermilion" | "gold" | "blue" | "green" | "ink" | "parchment" {
  if (v === "red") return "vermilion";
  return v;
}

// Map each color variant + appearance
const STYLES_SUBTLE: Record<string, string> = {
  vermilion:
    "bg-[color-mix(in_srgb,var(--ln-red)_12%,transparent)] text-ln-red border-[color-mix(in_srgb,var(--ln-red)_30%,transparent)]",
  gold:
    "bg-[color-mix(in_srgb,var(--ln-gold)_14%,transparent)] text-ln-gold border-[color-mix(in_srgb,var(--ln-gold)_35%,transparent)]",
  blue:
    "bg-[color-mix(in_srgb,var(--ln-blue)_12%,transparent)] text-ln-blue border-[color-mix(in_srgb,var(--ln-blue)_30%,transparent)]",
  green:
    "bg-[color-mix(in_srgb,var(--ln-green)_12%,transparent)] text-ln-green border-[color-mix(in_srgb,var(--ln-green)_30%,transparent)]",
  ink:
    "bg-[color-mix(in_srgb,var(--ln-ink)_8%,transparent)] text-ln-ink border-[color-mix(in_srgb,var(--ln-ink)_20%,transparent)]",
  parchment:
    "bg-ln-surface-muted text-ln-ink-muted border-ln-border",
};

const STYLES_SOLID: Record<string, string> = {
  vermilion: "bg-ln-red text-white border-transparent shadow-xs",
  gold: "bg-ln-gold text-[#2A241D] font-bold border-transparent shadow-xs",
  blue: "bg-ln-blue text-white border-transparent shadow-xs",
  green: "bg-ln-green text-white border-transparent shadow-xs",
  ink: "bg-ln-ink text-white dark:text-ln-ink dark:bg-ln-bg-soft border-transparent shadow-xs",
  parchment: "bg-ln-surface-muted text-ln-ink border-ln-border-strong",
};

const STYLES_OUTLINE: Record<string, string> = {
  vermilion: "bg-transparent text-ln-red border-ln-red/60",
  gold: "bg-transparent text-ln-gold border-ln-gold/60",
  blue: "bg-transparent text-ln-blue border-ln-blue/60",
  green: "bg-transparent text-ln-green border-ln-green/60",
  ink: "bg-transparent text-ln-ink border-ln-border-strong",
  parchment: "bg-transparent text-ln-ink-muted border-ln-border",
};

const STYLES_GHOST: Record<string, string> = {
  vermilion: "bg-transparent text-ln-red border-transparent",
  gold: "bg-transparent text-ln-gold border-transparent",
  blue: "bg-transparent text-ln-blue border-transparent",
  green: "bg-transparent text-ln-green border-transparent",
  ink: "bg-transparent text-ln-ink border-transparent",
  parchment: "bg-transparent text-ln-ink-muted border-transparent",
};

const SIZE_STYLES: Record<ImperialBadgeSize, string> = {
  xs: "text-[10px] px-2 py-0.5 gap-1 font-semibold",
  sm: "text-[11px] px-2.5 py-0.5 gap-1.5 font-medium",
  md: "text-xs px-3 py-1 gap-1.5 font-medium",
  lg: "text-sm px-3.5 py-1.5 gap-2 font-medium",
};

const DOT_COLORS: Record<string, string> = {
  vermilion: "bg-ln-red",
  gold: "bg-ln-gold",
  blue: "bg-ln-blue",
  green: "bg-ln-green",
  ink: "bg-ln-ink",
  parchment: "bg-ln-ink-muted",
};

export const ImperialBadge = forwardRef<HTMLSpanElement, ImperialBadgeProps>(
  (
    {
      variant = "gold",
      appearance = "subtle",
      size = "md",
      icon,
      rightIcon,
      dot,
      asChild = false,
      className,
      children,
      ...props
    },
    ref,
  ) => {
    const Comp = asChild ? Slot : "span";
    const normalized = normalizeVariant(variant);

    let colorStyle = STYLES_SUBTLE[normalized];
    if (appearance === "solid") colorStyle = STYLES_SOLID[normalized];
    else if (appearance === "outline") colorStyle = STYLES_OUTLINE[normalized];
    else if (appearance === "ghost") colorStyle = STYLES_GHOST[normalized];

    return (
      <Comp
        ref={ref}
        className={cn(
          "inline-flex w-fit shrink-0 items-center justify-center rounded-full border transition-colors select-none tracking-wide",
          colorStyle,
          SIZE_STYLES[size],
          className,
        )}
        {...props}
      >
        {dot && (
          <span
            aria-hidden="true"
            className={cn(
              "h-1.5 w-1.5 rounded-full shrink-0",
              DOT_COLORS[normalized] || "bg-current",
              dot === "pulse" && "animate-pulse",
            )}
          />
        )}
        {icon && (
          <span className="shrink-0 flex items-center justify-center [&>svg]:size-3.5">
            {icon}
          </span>
        )}
        <span>{children}</span>
        {rightIcon && (
          <span className="shrink-0 flex items-center justify-center [&>svg]:size-3.5">
            {rightIcon}
          </span>
        )}
      </Comp>
    );
  },
);

ImperialBadge.displayName = "ImperialBadge";
