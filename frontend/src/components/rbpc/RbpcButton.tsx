"use client";

import * as React from "react";
import { Slot } from "@radix-ui/react-slot";
import { Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";

export type RbpcButtonVariant =
  | "primary"
  | "secondary"
  | "subtle"
  | "highlight";

export type RbpcButtonSize = "sm" | "md" | "lg" | "icon";

export interface RbpcButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  /** Visual variant aligning with the Contemporary Huế Editorial palette */
  variant?: RbpcButtonVariant;
  /** Size tier; all tiers preserve the mandatory min 44×44px touch target */
  size?: RbpcButtonSize;
  /** Whether the button is in a busy/loading state */
  isLoading?: boolean;
  /** Accessible text for screen readers during loading */
  loadingText?: string;
  /** Optional icon displayed before the children */
  leftIcon?: React.ReactNode;
  /** Optional icon displayed after the children */
  rightIcon?: React.ReactNode;
  /** Delegate rendering to child element (e.g., Next.js Link) */
  asChild?: boolean;
}

const variantClasses: Record<RbpcButtonVariant, string> = {
  primary: "rbpc-btn-primary",
  secondary: "rbpc-btn-secondary",
  subtle: "rbpc-btn-subtle",
  highlight: "rbpc-btn-highlight",
};

const sizeClasses: Record<RbpcButtonSize, string> = {
  sm: "rbpc-btn-sm min-h-[44px] min-w-[44px]",
  md: "min-h-[44px] min-w-[44px]",
  lg: "min-h-[48px] min-w-[48px] px-6 py-3 text-base",
  icon: "h-[44px] w-[44px] min-h-[44px] min-w-[44px] p-0 flex items-center justify-center",
};

/**
 * RbpcButton — Contemporary Huế Editorial Accessible Button
 *
 * Core Guarantees:
 * - Enforces minimum 44×44px touch bounding box on all breakpoints (WCAG 2.5.5 / 2.5.8)
 * - High-contrast focus outline (minimum 2px solid #1E675A with 2px offset)
 * - Loading state with spinner, `aria-busy`, and assistive announcement
 * - Zero heavy backdrop-blur; pure paper-and-ink materiality
 */
export const RbpcButton = React.forwardRef<HTMLButtonElement, RbpcButtonProps>(
  (
    {
      className,
      variant = "primary",
      size = "md",
      isLoading = false,
      loadingText = "Đang xử lý...",
      leftIcon,
      rightIcon,
      disabled,
      children,
      asChild = false,
      type = "button",
      onClick,
      ...props
    },
    ref
  ) => {
    const isInteractiveDisabled = disabled || isLoading;

    const baseClass = cn(
      "rbpc-btn relative inline-flex items-center justify-center gap-2 select-none",
      "font-sans font-medium text-sm transition-colors",
      "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--rbpc-focus)] focus-visible:ring-offset-2",
      variantClasses[variant],
      sizeClasses[size],
      isInteractiveDisabled && "opacity-55 cursor-not-allowed pointer-events-none",
      className
    );

    const handleClick = (e: React.MouseEvent<HTMLButtonElement>) => {
      if (isInteractiveDisabled) {
        e.preventDefault();
        return;
      }
      onClick?.(e);
    };

    if (asChild) {
      return (
        <Slot
          className={baseClass}
          aria-disabled={isInteractiveDisabled ? "true" : undefined}
          aria-busy={isLoading ? "true" : undefined}
          onClick={handleClick as unknown as React.MouseEventHandler<HTMLElement>}
          {...(props as unknown as Record<string, unknown>)}
        >
          {children}
        </Slot>
      );
    }

    return (
      <button
        ref={ref}
        type={type}
        className={baseClass}
        disabled={isInteractiveDisabled}
        aria-disabled={isInteractiveDisabled ? "true" : undefined}
        aria-busy={isLoading ? "true" : undefined}
        onClick={handleClick}
        {...props}
      >
        {isLoading ? (
          <>
            <Loader2
              className="h-4 w-4 animate-spin text-current shrink-0"
              aria-hidden="true"
            />
            <span className="inline-flex items-center gap-2">
              {children}
            </span>
            <span className="rbpc-sr-only">{loadingText}</span>
          </>
        ) : (
          <>
            {leftIcon && (
              <span className="inline-flex shrink-0 items-center" aria-hidden="true">
                {leftIcon}
              </span>
            )}
            {children}
            {rightIcon && (
              <span className="inline-flex shrink-0 items-center" aria-hidden="true">
                {rightIcon}
              </span>
            )}
          </>
        )}
      </button>
    );
  }
);

RbpcButton.displayName = "RbpcButton";
