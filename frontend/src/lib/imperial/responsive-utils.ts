/**
 * Mobile Responsive & Performance Optimization Utilities for STTTNNĐ (Lưu Niên — Đại Nội Huế).
 * Follow-On SPEC V5.1 (Mobile Responsive & Performance per 11_WEBSITE_UI_UX_DESIGN_SPEC.md).
 *
 * Implements:
 * 1. Touch device detection (SSR-safe, hybrid pointer & coarse media queries).
 * 2. Viewport categorization ('mobile' < 640px, 'tablet' 640-1024px, 'desktop' > 1024px).
 * 3. Touch target enforcement (WCAG 2.1 AA/AAA 44x44 CSS px standard).
 * 4. Dynamic viewport height calculations accounting for mobile browser chrome (100dvh).
 * 5. React hooks for responsive state synchronization.
 */

import { useState, useEffect } from "react";

export const MIN_TOUCH_TARGET_PX = 44;
export const MIN_TOUCH_TARGET_CLASS = "min-w-[44px] min-h-[44px]";

export const BREAKPOINTS = {
  MOBILE_MAX: 639.98,
  TABLET_MIN: 640,
  TABLET_MAX: 1024,
  DESKTOP_MIN: 1024.01,
} as const;

export type ViewportCategory = "mobile" | "tablet" | "desktop";

export interface TouchTargetDimensions {
  width: number;
  height: number;
}

export interface DynamicMapHeightOptions {
  /** Base viewport height in px. If omitted, uses visualViewport.height or innerHeight (or default 800 in SSR). */
  viewportHeight?: number;
  /** Top header bar height in px. Defaults to 56 (3.5rem / h-14). */
  headerHeight?: number;
  /** Bottom navigation bar height in px. Defaults to 56 on mobile, 0 on tablet/desktop. */
  bottomNavHeight?: number;
  /** Additional container padding or margins to subtract in px. Defaults to 0. */
  padding?: number;
  /** Is mobile viewport flag override. If omitted, inferred from viewport width or window.innerWidth. */
  isMobile?: boolean;
  /** Minimum returned height in px. Defaults to 320. */
  minHeight?: number;
}

/**
 * Detects whether the current environment / device supports touch interactions.
 * SSR-safe, checks touch events, navigator touch points, and coarse pointer media query.
 */
export function isTouchDevice(): boolean {
  if (typeof window === "undefined") {
    return false;
  }

  const nav = typeof navigator !== "undefined" ? navigator : null;
  const hasTouchStart = "ontouchstart" in window;
  const hasMaxTouchPoints = Boolean(nav && nav.maxTouchPoints > 0);
  const hasMsMaxTouchPoints = Boolean(
    nav &&
      ((nav as unknown as { msMaxTouchPoints?: number }).msMaxTouchPoints ?? 0) > 0,
  );
  const hasCoarsePointer = Boolean(
    typeof window.matchMedia === "function" &&
      window.matchMedia("(pointer: coarse)").matches,
  );

  return hasTouchStart || hasMaxTouchPoints || hasMsMaxTouchPoints || hasCoarsePointer;
}

/**
 * Categorizes a viewport width into 'mobile' (< 640px), 'tablet' (640-1024px), or 'desktop' (> 1024px).
 *
 * @param width Optional width in CSS px. Defaults to window.innerWidth if available, or 1200 (desktop) in SSR.
 */
export function getViewportCategory(width?: number): ViewportCategory {
  let w: number;
  if (typeof width === "number" && !Number.isNaN(width)) {
    w = width;
  } else if (typeof window !== "undefined") {
    w = window.innerWidth;
  } else {
    return "desktop";
  }

  if (w < 640) {
    return "mobile";
  }
  if (w <= 1024) {
    return "tablet";
  }
  return "desktop";
}

/**
 * Helper to check if a width corresponds to the mobile breakpoint (< 640px).
 */
export function isMobileViewport(width?: number): boolean {
  return getViewportCategory(width) === "mobile";
}

/**
 * Helper to check if a width corresponds to the tablet breakpoint (640px .. 1024px).
 */
export function isTabletViewport(width?: number): boolean {
  return getViewportCategory(width) === "tablet";
}

/**
 * Helper to check if a width corresponds to the desktop breakpoint (> 1024px).
 */
export function isDesktopViewport(width?: number): boolean {
  return getViewportCategory(width) === "desktop";
}

/**
 * Ensures touch targets meet the minimum 44x44 CSS px accessibility standard (WCAG / Apple HIG).
 * Supports single number dimension, dimension objects { width, height }, or two numbers.
 *
 * @example
 * enforceMinTouchTarget(32) // => 44
 * enforceMinTouchTarget(50) // => 50
 * enforceMinTouchTarget({ width: 24, height: 48 }) // => { width: 44, height: 48 }
 * enforceMinTouchTarget(24, 32) // => { width: 44, height: 44 }
 */
export function enforceMinTouchTarget(size: number): number;
export function enforceMinTouchTarget(dimensions: TouchTargetDimensions): TouchTargetDimensions;
export function enforceMinTouchTarget(width: number, height: number): TouchTargetDimensions;
export function enforceMinTouchTarget(
  sizeOrDimensions: number | TouchTargetDimensions,
  heightArg?: number,
): number | TouchTargetDimensions {
  if (typeof sizeOrDimensions === "number") {
    if (typeof heightArg === "number") {
      return {
        width: Math.max(MIN_TOUCH_TARGET_PX, sizeOrDimensions),
        height: Math.max(MIN_TOUCH_TARGET_PX, heightArg),
      };
    }
    return Math.max(MIN_TOUCH_TARGET_PX, sizeOrDimensions);
  }

  return {
    width: Math.max(MIN_TOUCH_TARGET_PX, sizeOrDimensions.width),
    height: Math.max(MIN_TOUCH_TARGET_PX, sizeOrDimensions.height),
  };
}

/**
 * Calculates the required padding on each side (in px) to expand an element of `contentSize`
 * up to the minimum 44px touch target standard.
 *
 * @example
 * calculateTouchTargetPadding(24) // => 10 px on each side ((44 - 24) / 2)
 */
export function calculateTouchTargetPadding(
  contentSize: number,
  minTarget: number = MIN_TOUCH_TARGET_PX,
): number {
  if (!Number.isFinite(contentSize) || contentSize >= minTarget) {
    return 0;
  }
  return Math.ceil((minTarget - contentSize) / 2);
}

/**
 * Accurately calculates available canvas / map height considering mobile browser chrome (`100dvh`).
 * Accounts for visual viewport changes, address bar collapse/expansion, header bar, and mobile bottom nav.
 *
 * @param viewportHeightOrOptions Optional viewport height or options object.
 * @param maybeOptions Optional configuration options if viewportHeight is passed as first arg.
 * @returns Available height in integer CSS pixels (clamped to at least minHeight).
 */
export function calculateDynamicMapHeight(
  viewportHeightOrOptions?: number | DynamicMapHeightOptions,
  maybeOptions?: DynamicMapHeightOptions,
): number {
  let opts: DynamicMapHeightOptions = {};

  if (typeof viewportHeightOrOptions === "number") {
    opts = { ...maybeOptions, viewportHeight: viewportHeightOrOptions };
  } else if (viewportHeightOrOptions && typeof viewportHeightOrOptions === "object") {
    opts = viewportHeightOrOptions;
  }

  const minHeight = opts.minHeight ?? 320;
  const headerHeight = opts.headerHeight ?? 56; // 3.5rem default header
  const padding = opts.padding ?? 0;

  // Determine viewport height
  let vpHeight: number;
  if (typeof opts.viewportHeight === "number") {
    vpHeight = opts.viewportHeight;
  } else if (typeof window !== "undefined") {
    // visualViewport height accounts for on-screen chrome and software keyboard on mobile
    vpHeight = window.visualViewport?.height ?? window.innerHeight;
  } else {
    vpHeight = 800; // SSR fallback
  }

  // Determine if mobile viewport to apply bottom nav subtraction
  let isMobile: boolean;
  if (typeof opts.isMobile === "boolean") {
    isMobile = opts.isMobile;
  } else if (typeof window !== "undefined") {
    isMobile = window.innerWidth < BREAKPOINTS.TABLET_MIN;
  } else {
    isMobile = false;
  }

  const bottomNavHeight = opts.bottomNavHeight ?? (isMobile ? 56 : 0);

  const availableHeight = vpHeight - headerHeight - bottomNavHeight - padding;
  return Math.max(minHeight, Math.round(availableHeight));
}

/**
 * Generates dynamic CSS height expression using `100dvh` for styling responsive containers.
 *
 * @example
 * getDynamicMapHeightCSS() // => "calc(100dvh - 3.5rem)"
 * getDynamicMapHeightCSS({ includeBottomNav: true }) // => "calc(100dvh - 7rem)"
 */
export function getDynamicMapHeightCSS(options?: {
  headerRem?: number;
  bottomNavRem?: number;
  includeBottomNav?: boolean;
}): string {
  const header = options?.headerRem ?? 3.5;
  if (options?.includeBottomNav) {
    const bottom = options?.bottomNavRem ?? 3.5;
    return `calc(100dvh - ${header + bottom}rem)`;
  }
  return `calc(100dvh - ${header}rem)`;
}

/**
 * React hook that returns the current ViewportCategory ('mobile' | 'tablet' | 'desktop')
 * and reactively updates on window resize events.
 */
export function useViewportCategory(): ViewportCategory {
  const [category, setCategory] = useState<ViewportCategory>(() =>
    typeof window !== "undefined" ? getViewportCategory(window.innerWidth) : "desktop",
  );

  useEffect(() => {
    if (typeof window === "undefined") return;

    const handleResize = () => {
      setCategory(getViewportCategory(window.innerWidth));
    };

    handleResize();
    window.addEventListener("resize", handleResize, { passive: true });
    return () => window.removeEventListener("resize", handleResize);
  }, []);

  return category;
}

/**
 * React hook that safely returns touch device capability on the client,
 * avoiding SSR hydration mismatches by initializing to false during SSR.
 */
export function useIsTouchDevice(): boolean {
  const [touchDevice, setTouchDevice] = useState<boolean>(false);

  useEffect(() => {
    setTouchDevice(isTouchDevice());
  }, []);

  return touchDevice;
}
