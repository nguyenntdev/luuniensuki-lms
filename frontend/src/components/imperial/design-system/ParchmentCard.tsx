"use client";

import React, { forwardRef } from "react";
import { cn } from "@/lib/utils";

export type ParchmentVariant = "default" | "soft" | "muted" | "pure";
export type ParchmentElevation = "none" | "sm" | "md" | "lg";
export type ParchmentBorderStyle = "single" | "delicate" | "double" | "accented";
export type ParchmentTexture = "none" | "grain" | "cloud" | "water";

export interface ParchmentCardProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: ParchmentVariant;
  elevation?: ParchmentElevation;
  borderStyle?: ParchmentBorderStyle;
  texture?: ParchmentTexture;
  interactive?: boolean;
  cornerAccents?: boolean;
  as?: React.ElementType;
}

const VARIANT_STYLES: Record<ParchmentVariant, string> = {
  default: "bg-ln-surface text-ln-ink border-ln-border",
  soft: "bg-ln-bg-soft text-ln-ink border-ln-border",
  muted: "bg-ln-surface-muted text-ln-ink border-ln-border-strong/60",
  pure: "bg-ln-bg text-ln-ink border-ln-border",
};

const ELEVATION_STYLES: Record<ParchmentElevation, string> = {
  none: "shadow-none",
  sm: "shadow-[0_2px_8px_-2px_rgba(42,36,29,0.06)] dark:shadow-[0_2px_8px_-2px_rgba(0,0,0,0.4)]",
  md: "shadow-[0_6px_20px_-4px_rgba(42,36,29,0.08)] dark:shadow-[0_6px_20px_-4px_rgba(0,0,0,0.5)]",
  lg: "shadow-[0_12px_32px_-6px_rgba(42,36,29,0.12)] dark:shadow-[0_12px_32px_-6px_rgba(0,0,0,0.6)]",
};

const BORDER_STYLES: Record<ParchmentBorderStyle, string> = {
  single: "border",
  delicate: "border ring-1 ring-inset ring-ln-border-strong/30",
  double: "border-2 border-double border-ln-border-strong",
  accented: "border border-ln-gold/40 shadow-[inset_0_1px_0_rgba(198,138,44,0.15)]",
};

const TEXTURE_STYLES: Record<ParchmentTexture, string> = {
  none: "",
  grain: "parchment-grain",
  cloud: "pattern-van-may bg-blend-soft-light",
  water: "pattern-thuy-ba bg-blend-soft-light",
};

/**
 * Imperial corner brackets (triện góc / hồi văn)
 * Subtle decorative brackets evoking Nguyen Dynasty royal edicts and lacquered panels.
 */
function ImperialCornerOrnaments() {
  return (
    <>
      <span
        aria-hidden="true"
        className="pointer-events-none absolute top-1.5 left-1.5 h-2.5 w-2.5 border-t border-l border-ln-border-strong/70"
      />
      <span
        aria-hidden="true"
        className="pointer-events-none absolute top-1.5 right-1.5 h-2.5 w-2.5 border-t border-r border-ln-border-strong/70"
      />
      <span
        aria-hidden="true"
        className="pointer-events-none absolute bottom-1.5 left-1.5 h-2.5 w-2.5 border-b border-l border-ln-border-strong/70"
      />
      <span
        aria-hidden="true"
        className="pointer-events-none absolute bottom-1.5 right-1.5 h-2.5 w-2.5 border-b border-r border-ln-border-strong/70"
      />
    </>
  );
}

export const ParchmentCard = forwardRef<HTMLDivElement, ParchmentCardProps>(
  (
    {
      variant = "default",
      elevation = "md",
      borderStyle = "delicate",
      texture = "none",
      interactive = false,
      cornerAccents = false,
      as: Component = "div",
      className,
      children,
      ...props
    },
    ref,
  ) => {
    const Comp = Component as any;
    return (
      <Comp
        ref={ref}
        className={cn(
          "relative overflow-hidden rounded-xl transition-all duration-300",
          VARIANT_STYLES[variant],
          ELEVATION_STYLES[elevation],
          BORDER_STYLES[borderStyle],
          TEXTURE_STYLES[texture],
          interactive &&
            "cursor-pointer hover:-translate-y-0.5 hover:shadow-lg hover:border-ln-gold/50 active:translate-y-0 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ln-gold focus-visible:ring-offset-2",
          className,
        )}
        {...props}
      >
        {cornerAccents && <ImperialCornerOrnaments />}
        {children}
      </Comp>
    );
  },
);

ParchmentCard.displayName = "ParchmentCard";

export function ParchmentCardHeader({
  className,
  ...props
}: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn("flex flex-col space-y-1.5 p-5 sm:p-6", className)}
      {...props}
    />
  );
}

export interface ParchmentCardTitleProps
  extends React.HTMLAttributes<HTMLHeadingElement> {
  as?: "h1" | "h2" | "h3" | "h4" | "h5" | "h6" | "span" | "div";
}

export function ParchmentCardTitle({
  as: Component = "h3",
  className,
  ...props
}: ParchmentCardTitleProps) {
  return (
    <Component
      className={cn(
        "font-serif text-lg sm:text-xl font-bold tracking-tight text-ln-ink",
        className,
      )}
      {...props}
    />
  );
}

export function ParchmentCardDescription({
  className,
  ...props
}: React.HTMLAttributes<HTMLParagraphElement>) {
  return (
    <p
      className={cn(
        "text-xs sm:text-sm text-ln-ink-muted leading-relaxed",
        className,
      )}
      {...props}
    />
  );
}

export function ParchmentCardContent({
  className,
  ...props
}: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn("p-5 sm:p-6 pt-0 text-ln-ink", className)}
      {...props}
    />
  );
}

export function ParchmentCardFooter({
  className,
  ...props
}: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn(
        "flex items-center p-5 sm:p-6 pt-0 border-t border-ln-border/60 mt-4",
        className,
      )}
      {...props}
    />
  );
}

export function ParchmentCardSeparator({
  className,
  ...props
}: React.HTMLAttributes<HTMLHRElement>) {
  return (
    <hr
      className={cn(
        "border-0 h-px w-full bg-ln-border my-4 opacity-70",
        className,
      )}
      {...props}
    />
  );
}
