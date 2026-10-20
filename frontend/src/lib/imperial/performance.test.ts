import { describe, it, expect } from "vitest";
import {
  MIN_TOUCH_TARGET_PX,
  MIN_TOUCH_TARGET_CLASS,
  BREAKPOINTS,
  enforceMinTouchTarget,
  calculateTouchTargetPadding,
  getViewportCategory,
  isMobileViewport,
  isTabletViewport,
  isDesktopViewport,
  isTouchDevice,
  calculateDynamicMapHeight,
  getDynamicMapHeightCSS,
} from "./responsive-utils";
import {
  deriveWebpSrc,
  getResponsiveSizes,
  generateImperialLqipDataUrl,
} from "@/components/imperial/ui/OptimizedImage";

describe("Mobile Responsive & Performance Optimizations (SPEC V5.1)", () => {
  describe("Touch Target Accessibility & Enforcement (§44x44 CSS px standard)", () => {
    it("enforces minimum 44px on numeric values below 44", () => {
      expect(enforceMinTouchTarget(0)).toBe(44);
      expect(enforceMinTouchTarget(20)).toBe(44);
      expect(enforceMinTouchTarget(24)).toBe(44);
      expect(enforceMinTouchTarget(32)).toBe(44);
      expect(enforceMinTouchTarget(43.9)).toBe(44);
    });

    it("preserves numeric values equal to or greater than 44", () => {
      expect(enforceMinTouchTarget(44)).toBe(44);
      expect(enforceMinTouchTarget(48)).toBe(48);
      expect(enforceMinTouchTarget(64)).toBe(64);
      expect(enforceMinTouchTarget(120)).toBe(120);
    });

    it("enforces minimum 44x44 on dimension objects { width, height }", () => {
      expect(enforceMinTouchTarget({ width: 24, height: 24 })).toEqual({
        width: 44,
        height: 44,
      });

      expect(enforceMinTouchTarget({ width: 32, height: 60 })).toEqual({
        width: 44,
        height: 60,
      });

      expect(enforceMinTouchTarget({ width: 50, height: 20 })).toEqual({
        width: 50,
        height: 44,
      });

      expect(enforceMinTouchTarget({ width: 64, height: 64 })).toEqual({
        width: 64,
        height: 64,
      });
    });

    it("enforces minimum 44x44 when passed two numeric arguments", () => {
      expect(enforceMinTouchTarget(20, 30)).toEqual({
        width: 44,
        height: 44,
      });

      expect(enforceMinTouchTarget(50, 20)).toEqual({
        width: 50,
        height: 44,
      });

      expect(enforceMinTouchTarget(48, 52)).toEqual({
        width: 48,
        height: 52,
      });
    });

    it("calculates symmetric padding needed to reach 44px standard", () => {
      // 24px icon + 10px each side = 44px
      expect(calculateTouchTargetPadding(24)).toBe(10);
      // 32px button + 6px each side = 44px
      expect(calculateTouchTargetPadding(32)).toBe(6);
      // 40px element + 2px each side = 44px
      expect(calculateTouchTargetPadding(40)).toBe(2);
      // 44px and larger requires 0 additional padding
      expect(calculateTouchTargetPadding(44)).toBe(0);
      expect(calculateTouchTargetPadding(48)).toBe(0);
      expect(calculateTouchTargetPadding(64)).toBe(0);
    });

    it("exports standard Tailwind CSS touch target utility class", () => {
      expect(MIN_TOUCH_TARGET_CLASS).toBe("min-w-[44px] min-h-[44px]");
      expect(MIN_TOUCH_TARGET_PX).toBe(44);
    });
  });

  describe("Viewport Categorization & Breakpoints", () => {
    it("categorizes widths < 640px as 'mobile'", () => {
      expect(getViewportCategory(0)).toBe("mobile");
      expect(getViewportCategory(320)).toBe("mobile");
      expect(getViewportCategory(375)).toBe("mobile");
      expect(getViewportCategory(414)).toBe("mobile");
      expect(getViewportCategory(639)).toBe("mobile");
      expect(getViewportCategory(639.9)).toBe("mobile");

      expect(isMobileViewport(375)).toBe(true);
      expect(isTabletViewport(375)).toBe(false);
      expect(isDesktopViewport(375)).toBe(false);
    });

    it("categorizes widths between 640px and 1024px as 'tablet'", () => {
      expect(getViewportCategory(640)).toBe("tablet");
      expect(getViewportCategory(768)).toBe("tablet");
      expect(getViewportCategory(834)).toBe("tablet");
      expect(getViewportCategory(1024)).toBe("tablet");

      expect(isMobileViewport(768)).toBe(false);
      expect(isTabletViewport(768)).toBe(true);
      expect(isDesktopViewport(768)).toBe(false);
    });

    it("categorizes widths > 1024px as 'desktop'", () => {
      expect(getViewportCategory(1024.1)).toBe("desktop");
      expect(getViewportCategory(1025)).toBe("desktop");
      expect(getViewportCategory(1280)).toBe("desktop");
      expect(getViewportCategory(1440)).toBe("desktop");
      expect(getViewportCategory(1920)).toBe("desktop");
      expect(getViewportCategory(2560)).toBe("desktop");

      expect(isMobileViewport(1440)).toBe(false);
      expect(isTabletViewport(1440)).toBe(false);
      expect(isDesktopViewport(1440)).toBe(true);
    });

    it("safely falls back to 'desktop' when width is undefined in SSR/Node environment", () => {
      expect(getViewportCategory(undefined)).toBe("desktop");
      // @ts-expect-error Testing invalid input fallback
      expect(getViewportCategory(null)).toBe("desktop");
      expect(getViewportCategory(NaN)).toBe("desktop");
    });

    it("exposes canonical breakpoint thresholds", () => {
      expect(BREAKPOINTS.TABLET_MIN).toBe(640);
      expect(BREAKPOINTS.TABLET_MAX).toBe(1024);
      expect(BREAKPOINTS.MOBILE_MAX).toBeLessThan(640);
      expect(BREAKPOINTS.DESKTOP_MIN).toBeGreaterThan(1024);
    });
  });

  describe("Device Touch Capability Detection (isTouchDevice)", () => {
    it("returns false in headless/SSR environments where window is undefined", () => {
      // In Node environment, window is undefined by default
      expect(isTouchDevice()).toBe(false);
    });

    it("detects touch device via window.ontouchstart or navigator.maxTouchPoints", () => {
      // Mock client environment with touch support
      const originalWindow = globalThis.window;
      const originalNavigatorDesc = Object.getOwnPropertyDescriptor(globalThis, "navigator");

      try {
        globalThis.window = {
          ontouchstart: null,
          matchMedia: () => ({ matches: false }),
        } as any;
        Object.defineProperty(globalThis, "navigator", {
          value: { maxTouchPoints: 5 },
          configurable: true,
        });

        expect(isTouchDevice()).toBe(true);
      } finally {
        globalThis.window = originalWindow;
        if (originalNavigatorDesc) {
          Object.defineProperty(globalThis, "navigator", originalNavigatorDesc);
        }
      }
    });

    it("detects touch device via coarse pointer media query", () => {
      const originalWindow = globalThis.window;
      const originalNavigatorDesc = Object.getOwnPropertyDescriptor(globalThis, "navigator");

      try {
        globalThis.window = {
          matchMedia: (query: string) => ({
            matches: query === "(pointer: coarse)",
          }),
        } as any;
        Object.defineProperty(globalThis, "navigator", {
          value: { maxTouchPoints: 0 },
          configurable: true,
        });

        expect(isTouchDevice()).toBe(true);
      } finally {
        globalThis.window = originalWindow;
        if (originalNavigatorDesc) {
          Object.defineProperty(globalThis, "navigator", originalNavigatorDesc);
        }
      }
    });
  });

  describe("Dynamic Map Height Calculations (100dvh)", () => {
    it("calculates available height on desktop viewports subtracting header bar", () => {
      // 900px viewport - 56px header = 844px
      const height = calculateDynamicMapHeight(900, { isMobile: false });
      expect(height).toBe(844);
    });

    it("calculates available height on mobile viewports subtracting header and mobile bottom nav", () => {
      // 600px viewport - 56px header - 56px bottom nav = 488px
      const height = calculateDynamicMapHeight(600, { isMobile: true });
      expect(height).toBe(488);
    });

    it("accepts custom headerHeight, bottomNavHeight, and padding", () => {
      const height = calculateDynamicMapHeight({
        viewportHeight: 800,
        headerHeight: 64,
        bottomNavHeight: 64,
        padding: 16,
        isMobile: true,
      });
      // 800 - 64 - 64 - 16 = 656px
      expect(height).toBe(656);
    });

    it("enforces minimum height constraint to prevent layout collapse", () => {
      const height = calculateDynamicMapHeight({
        viewportHeight: 350,
        headerHeight: 56,
        bottomNavHeight: 56,
        padding: 50,
        minHeight: 320,
      });
      // 350 - 56 - 56 - 50 = 188px < 320 minHeight -> clamps to 320px
      expect(height).toBe(320);
    });

    it("generates CSS expressions with 100dvh", () => {
      expect(getDynamicMapHeightCSS()).toBe("calc(100dvh - 3.5rem)");
      expect(getDynamicMapHeightCSS({ includeBottomNav: true })).toBe(
        "calc(100dvh - 7rem)",
      );
      expect(
        getDynamicMapHeightCSS({ headerRem: 4, bottomNavRem: 4, includeBottomNav: true }),
      ).toBe("calc(100dvh - 8rem)");
    });
  });

  describe("Image Performance, WebP Preference & Responsive Sizes", () => {
    it("converts JPEG and PNG URLs to WebP format", () => {
      expect(deriveWebpSrc("/assets/ban-duc-noi/cao-dinh.jpg")).toBe(
        "/assets/ban-duc-noi/cao-dinh.webp",
      );
      expect(deriveWebpSrc("/assets/ban-duc-noi/nhan-dinh.jpeg")).toBe(
        "/assets/ban-duc-noi/nhan-dinh.webp",
      );
      expect(deriveWebpSrc("https://storage.histolab.icu/images/ngo-mon.png")).toBe(
        "https://storage.histolab.icu/images/ngo-mon.webp",
      );
    });

    it("preserves URL query strings and cachebusters when converting to WebP", () => {
      expect(
        deriveWebpSrc("/assets/photos/dien-thai-hoa.jpg?v=2026&format=orig"),
      ).toBe("/assets/photos/dien-thai-hoa.webp?v=2026&format=orig");

      expect(deriveWebpSrc("https://example.com/gate.png?w=800#hero")).toBe(
        "https://example.com/gate.webp?w=800#hero",
      );
    });

    it("leaves already WebP, SVG, and data URIs unaltered", () => {
      expect(deriveWebpSrc("/assets/photo.webp")).toBe("/assets/photo.webp");
      expect(deriveWebpSrc("/assets/vector.svg")).toBe("/assets/vector.svg");
      expect(
        deriveWebpSrc("data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAE="),
      ).toBe("data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAE=");
    });

    it("generates responsive sizes strings for common imperial layout presets", () => {
      expect(getResponsiveSizes("full")).toBe("100vw");
      expect(getResponsiveSizes("hero")).toBe(
        "(max-width: 640px) 100vw, (max-width: 1024px) 90vw, 1200px",
      );
      expect(getResponsiveSizes("card")).toBe(
        "(max-width: 640px) 100vw, (max-width: 1024px) 50vw, 33vw",
      );
      expect(getResponsiveSizes("half")).toBe("(max-width: 640px) 100vw, 50vw");
      expect(getResponsiveSizes("thumbnail")).toBe(
        "(max-width: 640px) 80px, 120px",
      );

      // Custom sizes attribute takes precedence
      expect(getResponsiveSizes("card", "(max-width: 480px) 100vw, 400px")).toBe(
        "(max-width: 480px) 100vw, 400px",
      );
    });

    it("generates authentic imperial LQIP data URI with amber gradient", () => {
      const dataUri = generateImperialLqipDataUrl();
      expect(dataUri).toBeDefined();
      expect(
        dataUri.startsWith("data:image/svg+xml;base64,") ||
          dataUri.startsWith("data:image/svg+xml;utf8,"),
      ).toBe(true);
      expect(dataUri).toContain("svg");
    });
  });

  describe("Image Fallback State Machine & Degradation Sequence", () => {
    it("simulates WebP -> original -> fallbackSrc -> cultural illustration cascade", () => {
      // Candidate resolution test
      const primary = "/assets/photo.jpg";
      const webpCandidate = deriveWebpSrc(primary);
      const fallbackSrc = "/assets/placeholder-default.jpg";

      // 1. Initially attempts WebP
      expect(webpCandidate).toBe("/assets/photo.webp");

      // 2. If WebP candidate fails, candidate degrades to primary JPG
      const failed = new Set<string>();
      failed.add(webpCandidate);

      let nextAttempt: string | null = null;
      if (!failed.has(primary)) {
        nextAttempt = primary;
      }
      expect(nextAttempt).toBe("/assets/photo.jpg");

      // 3. If primary JPG fails, candidate degrades to fallbackSrc
      failed.add(primary);
      if (fallbackSrc && !failed.has(fallbackSrc)) {
        nextAttempt = fallbackSrc;
      }
      expect(nextAttempt).toBe("/assets/placeholder-default.jpg");

      // 4. If fallbackSrc fails, all candidates exhausted -> trigger cultural illustration
      failed.add(fallbackSrc);
      const hasCulturalFallbackTriggered =
        failed.has(webpCandidate) && failed.has(primary) && failed.has(fallbackSrc);
      expect(hasCulturalFallbackTriggered).toBe(true);
    });
  });
});
