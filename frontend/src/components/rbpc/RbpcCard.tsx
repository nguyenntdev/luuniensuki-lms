"use client";

import * as React from "react";
import { Slot } from "@radix-ui/react-slot";
import { cn } from "@/lib/utils";

export type RbpcCardElevation = "surface" | "elevated" | "inset";
export type RbpcCardPadding = "none" | "sm" | "md" | "lg" | "responsive";

export interface RbpcCardProps extends React.HTMLAttributes<HTMLDivElement> {
  /** Surface elevation tier */
  elevation?: RbpcCardElevation;
  /** Inner padding scale */
  padding?: RbpcCardPadding;
  /** Whether the card features hover elevation and active focus rings */
  interactive?: boolean;
  /** Delegate rendering to child element (e.g. Next.js Link) */
  asChild?: boolean;
}

const elevationClasses: Record<RbpcCardElevation, string> = {
  surface: "bg-[var(--rbpc-surface)] border-[var(--rbpc-divider)] shadow-[var(--rbpc-shadow-sm)]",
  elevated: "bg-[var(--rbpc-surface-elevated)] border-[var(--rbpc-divider)] shadow-[var(--rbpc-shadow-md)]",
  inset: "rbpc-card-inset bg-[var(--rbpc-bg)] border-dashed border-[var(--rbpc-divider)] shadow-none",
};

const paddingClasses: Record<RbpcCardPadding, string> = {
  none: "p-0",
  sm: "p-4",
  md: "p-6",
  lg: "p-8",
  responsive: "p-4 sm:p-6 lg:p-8",
};

/**
 * RbpcCard — Contemporary Huế Editorial Paper Surface Container
 *
 * Design Guarantees:
 * - Warm paper surface (`#FFFCF7`) with 1px subtle divider border (`#D8D7CE`)
 * - Strictly ZERO heavy backdrop blur (avoids mobile GPU compositing latency)
 * - Soft ambient paper drop shadow with reduced-motion safe hover elevation
 * - Full WCAG keyboard accessibility when interactive
 */
export const RbpcCard = React.forwardRef<HTMLDivElement, RbpcCardProps>(
  (
    {
      className,
      elevation = "surface",
      padding = "md",
      interactive = false,
      asChild = false,
      children,
      onKeyDown,
      onClick,
      tabIndex,
      role,
      ...props
    },
    ref
  ) => {
    const isInteractive = interactive || Boolean(onClick);

    const baseClass = cn(
      "rbpc-card relative rounded-[var(--rbpc-radius-md)] border transition-all text-[var(--rbpc-ink)] overflow-hidden",
      elevationClasses[elevation],
      paddingClasses[padding],
      isInteractive && [
        "rbpc-card-interactive cursor-pointer select-none",
        "hover:-translate-y-0.5 hover:border-[var(--rbpc-primary-border)] hover:shadow-[var(--rbpc-shadow-md)]",
        "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--rbpc-focus)] focus-visible:ring-offset-2",
        "active:translate-y-0 active:shadow-[var(--rbpc-shadow-sm)]",
      ],
      className
    );

    const handleKeyDown = (e: React.KeyboardEvent<HTMLDivElement>) => {
      onKeyDown?.(e);
      if (isInteractive && onClick && (e.key === "Enter" || e.key === " ")) {
        e.preventDefault();
        (onClick as unknown as (event: React.KeyboardEvent<HTMLDivElement>) => void)(e);
      }
    };

    if (asChild) {
      return (
        <Slot
          className={baseClass}
          onClick={onClick}
          onKeyDown={handleKeyDown}
          tabIndex={tabIndex ?? (isInteractive ? 0 : undefined)}
          role={role ?? (isInteractive ? "button" : undefined)}
          {...(props as unknown as Record<string, unknown>)}
        >
          {children}
        </Slot>
      );
    }

    return (
      <div
        ref={ref}
        className={baseClass}
        onClick={onClick}
        onKeyDown={handleKeyDown}
        tabIndex={tabIndex ?? (isInteractive ? 0 : undefined)}
        role={role ?? (isInteractive && onClick ? "button" : undefined)}
        {...props}
      >
        {children}
      </div>
    );
  }
);
RbpcCard.displayName = "RbpcCard";

/**
 * RbpcCardHeader — Header section for card titles and actions
 */
export const RbpcCardHeader = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement>
>(({ className, ...props }, ref) => (
  <div
    ref={ref}
    className={cn(
      "flex flex-col gap-1.5 pb-4 mb-4 border-b border-[var(--rbpc-divider-subtle)]",
      className
    )}
    {...props}
  />
));
RbpcCardHeader.displayName = "RbpcCardHeader";

/**
 * RbpcCardTitle — Editorial serif heading
 */
export const RbpcCardTitle = React.forwardRef<
  HTMLHeadingElement,
  React.HTMLAttributes<HTMLHeadingElement> & { as?: "h1" | "h2" | "h3" | "h4" | "h5" }
>(({ className, as: Comp = "h3", children, ...props }, ref) => (
  <Comp
    ref={ref}
    className={cn(
      "font-serif font-semibold text-[var(--rbpc-ink)] tracking-tight leading-[var(--rbpc-lh-heading)] text-lg sm:text-xl",
      className
    )}
    {...props}
  >
    {children}
  </Comp>
));
RbpcCardTitle.displayName = "RbpcCardTitle";

/**
 * RbpcCardDescription — Secondary muted contextual label
 */
export const RbpcCardDescription = React.forwardRef<
  HTMLParagraphElement,
  React.HTMLAttributes<HTMLParagraphElement>
>(({ className, ...props }, ref) => (
  <p
    ref={ref}
    className={cn(
      "text-xs sm:text-sm text-[var(--rbpc-muted)] leading-[var(--rbpc-lh-lead)]",
      className
    )}
    {...props}
  />
));
RbpcCardDescription.displayName = "RbpcCardDescription";

/**
 * RbpcCardContent — Main editorial body content
 */
export const RbpcCardContent = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement>
>(({ className, ...props }, ref) => (
  <div ref={ref} className={cn("text-[var(--rbpc-ink)] leading-[var(--rbpc-lh-body)]", className)} {...props} />
));
RbpcCardContent.displayName = "RbpcCardContent";

/**
 * RbpcCardFooter — Bottom metadata, actions, or citation drawer triggers
 */
export const RbpcCardFooter = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement>
>(({ className, ...props }, ref) => (
  <div
    ref={ref}
    className={cn(
      "flex items-center justify-between gap-3 pt-4 mt-4 border-t border-[var(--rbpc-divider-subtle)] text-xs text-[var(--rbpc-muted)]",
      className
    )}
    {...props}
  />
));
RbpcCardFooter.displayName = "RbpcCardFooter";
