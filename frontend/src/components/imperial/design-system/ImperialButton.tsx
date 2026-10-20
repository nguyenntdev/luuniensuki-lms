"use client";

import React, { forwardRef } from "react";
import { Slot } from "@radix-ui/react-slot";
import { Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";

export type ImperialButtonVariant =
  | "primary"
  | "vermilion"
  | "gold"
  | "blue"
  | "green"
  | "parchment"
  | "outline"
  | "ghost";

export type ImperialButtonSize =
  | "xs"
  | "sm"
  | "md"
  | "default"
  | "lg"
  | "icon-xs"
  | "icon-sm"
  | "icon"
  | "icon-lg";

export interface ImperialButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ImperialButtonVariant;
  size?: ImperialButtonSize;
  isLoading?: boolean;
  loadingText?: string;
  leftIcon?: React.ReactNode;
  rightIcon?: React.ReactNode;
  asChild?: boolean;
}

const VARIANT_STYLES: Record<ImperialButtonVariant, string> = {
  primary:
    "bg-ln-red text-white hover:bg-[#8F2323] shadow-[0_4px_14px_-3px_rgba(166,43,43,0.45)] border-transparent active:bg-[#7D1D1D]",
  vermilion:
    "bg-ln-red text-white hover:bg-[#8F2323] shadow-[0_4px_14px_-3px_rgba(166,43,43,0.45)] border-transparent active:bg-[#7D1D1D]",
  gold:
    "bg-gradient-to-r from-ln-gold to-[#B37722] text-[#2A241D] font-bold hover:brightness-105 shadow-[0_4px_14px_-3px_rgba(198,138,44,0.4)] border-transparent active:brightness-95",
  blue:
    "bg-ln-blue text-white hover:bg-[#16496C] shadow-[0_4px_14px_-3px_rgba(29,92,134,0.4)] border-transparent active:bg-[#113A56]",
  green:
    "bg-ln-green text-white hover:bg-[#255A44] shadow-[0_4px_14px_-3px_rgba(47,111,85,0.4)] border-transparent active:bg-[#1D4736]",
  parchment:
    "bg-ln-surface text-ln-ink border-ln-border hover:bg-ln-surface-muted hover:border-ln-border-strong active:bg-ln-bg-soft shadow-xs",
  outline:
    "bg-transparent text-ln-ink border-2 border-ln-border-strong hover:bg-ln-surface-muted hover:border-ln-gold active:bg-ln-bg-soft",
  ghost:
    "bg-transparent text-ln-ink border-transparent hover:bg-ln-surface-muted active:bg-ln-bg-soft",
};

const SIZE_STYLES: Record<ImperialButtonSize, string> = {
  xs: "h-7 px-2.5 text-xs gap-1 rounded-md",
  sm: "h-8.5 px-3 text-xs gap-1.5 rounded-lg",
  md: "h-10 px-4.5 text-sm gap-2 rounded-lg",
  default: "h-10 px-4.5 text-sm gap-2 rounded-lg",
  lg: "h-12 px-6 text-base gap-2.5 rounded-xl font-medium",
  "icon-xs": "size-7 p-0 rounded-md",
  "icon-sm": "size-8.5 p-0 rounded-lg",
  icon: "size-10 p-0 rounded-lg",
  "icon-lg": "size-12 p-0 rounded-xl",
};

export const ImperialButton = forwardRef<HTMLButtonElement, ImperialButtonProps>(
  (
    {
      variant = "primary",
      size = "default",
      isLoading = false,
      loadingText,
      leftIcon,
      rightIcon,
      asChild = false,
      disabled,
      className,
      children,
      ...props
    },
    ref,
  ) => {
    const Comp = asChild ? Slot : "button";
    const isDisabled = disabled || isLoading;

    return (
      <Comp
        ref={ref}
        disabled={isDisabled}
        aria-busy={isLoading ? "true" : undefined}
        className={cn(
          "inline-flex shrink-0 items-center justify-center font-medium transition-all duration-200 select-none outline-none border",
          "focus-visible:ring-2 focus-visible:ring-ln-gold focus-visible:ring-offset-2 focus-visible:ring-offset-ln-bg",
          "disabled:pointer-events-none disabled:opacity-50 disabled:shadow-none",
          "active:scale-[0.98]",
          VARIANT_STYLES[variant],
          SIZE_STYLES[size],
          className,
        )}
        {...props}
      >
        {isLoading ? (
          <>
            <Loader2 className="h-4 w-4 animate-spin shrink-0" />
            <span>{loadingText || children}</span>
          </>
        ) : (
          <>
            {leftIcon && (
              <span className="shrink-0 flex items-center justify-center [&>svg]:size-4">
                {leftIcon}
              </span>
            )}
            {children}
            {rightIcon && (
              <span className="shrink-0 flex items-center justify-center [&>svg]:size-4">
                {rightIcon}
              </span>
            )}
          </>
        )}
      </Comp>
    );
  },
);

ImperialButton.displayName = "ImperialButton";
