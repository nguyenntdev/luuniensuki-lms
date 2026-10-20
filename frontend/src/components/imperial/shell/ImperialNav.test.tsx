import React from "react";
import { describe, it, expect, beforeEach, vi } from "vitest";
import { renderToStaticMarkup } from "react-dom/server";
import ImperialHeader from "./ImperialHeader";
import ImperialMobileNav from "./ImperialMobileNav";
import { isPublicPath, PUBLIC_PATH_PREFIXES } from "@/lib/publicPaths";

// Mock next/navigation
vi.mock("next/navigation", () => ({
  usePathname: () => "/dai-noi",
}));

// Mock authStore
vi.mock("@/stores/authStore", () => ({
  useAuthStore: (selector: (state: unknown) => unknown) =>
    selector({
      status: "unauthed",
      user: null,
      logout: vi.fn(),
    }),
}));

// Mock passport-storage
vi.mock("@/lib/imperial/passport-storage", () => ({
  usePassportProgress: () => ({
    unlockedCount: 4,
    totalSeals: 16,
    percentage: 25,
    isLoaded: true,
    unlockedSlugs: ["ngo-mon", "dien-thai-hoa", "the-to-mieu", "dien-kien-trung"],
  }),
}));

// Mock Radix dropdown menu Portal & Root so renderToStaticMarkup renders menu items inline
vi.mock("@radix-ui/react-dropdown-menu", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@radix-ui/react-dropdown-menu")>();
  return {
    ...actual,
    Portal: ({ children }: { children: React.ReactNode }) => <>{children}</>,
    Root: ({ children, ...props }: React.ComponentProps<typeof actual.Root>) => (
      <actual.Root defaultOpen={true} {...props}>
        {children}
      </actual.Root>
    ),
  };
});

describe("Imperial Navigation Shell Suite (STTTNNĐ Subagent 9)", () => {
  describe("publicPaths configuration", () => {
    it("ensures /dai-noi/ho-chieu, /dai-noi/chung-nhan, and /dai-noi/offline are in PUBLIC_PATH_PREFIXES", () => {
      expect(PUBLIC_PATH_PREFIXES).toContain("/dai-noi/ho-chieu");
      expect(PUBLIC_PATH_PREFIXES).toContain("/dai-noi/chung-nhan");
      expect(PUBLIC_PATH_PREFIXES).toContain("/dai-noi/offline");
    });

    it("verifies isPublicPath returns true for all newly exposed routes", () => {
      expect(isPublicPath("/dai-noi/ho-chieu")).toBe(true);
      expect(isPublicPath("/dai-noi/chung-nhan")).toBe(true);
      expect(isPublicPath("/dai-noi/offline")).toBe(true);
      expect(isPublicPath("/dai-noi/ho-chieu/chi-tiet")).toBe(true);
    });
  });

  describe("ImperialHeader component", () => {
    it("renders Hộ chiếu di sản link with stamp icon and seal progress badge", () => {
      const html = renderToStaticMarkup(<ImperialHeader />);

      // Navigation link
      expect(html).toContain("/dai-noi/ho-chieu");
      expect(html).toContain("Hộ chiếu di sản");

      // Badge showing unlocked count e.g. 4/16
      expect(html).toContain("4/16");
      expect(html).toContain("Ấn triện");
    });

    it("renders secondary utilities menu with Chứng nhận and Phiếu in & Ngoại tuyến", () => {
      const html = renderToStaticMarkup(<ImperialHeader />);

      expect(html).toContain("Tiện ích");
      expect(html).toContain("/dai-noi/chung-nhan");
      expect(html).toContain("Chứng nhận di sản");
      expect(html).toContain("/dai-noi/offline");
      expect(html).toContain("Phiếu in &amp; Ngoại tuyến");
    });
  });

  describe("ImperialMobileNav component", () => {
    it("renders exactly 5 tabs: Bản đồ, Hành trình, Trò chơi, Hộ chiếu, Cá nhân", () => {
      const html = renderToStaticMarkup(<ImperialMobileNav />);

      // Tab 1: Bản đồ
      expect(html).toContain("/dai-noi");
      expect(html).toContain("Bản đồ");

      // Tab 2: Hành trình
      expect(html).toContain("/dai-noi/tuyen-duong");
      expect(html).toContain("Hành trình");

      // Tab 3: Trò chơi
      expect(html).toContain("/dai-noi/tro-choi");
      expect(html).toContain("Trò chơi");

      // Tab 4: Hộ chiếu
      expect(html).toContain("/dai-noi/ho-chieu");
      expect(html).toContain("Hộ chiếu");

      // Tab 5: Cá nhân
      expect(html).toContain("/profile");
      expect(html).toContain("Cá nhân");
    });

    it("displays badge count on mobile Hộ chiếu tab when unlocked seals exist", () => {
      const html = renderToStaticMarkup(<ImperialMobileNav />);

      // Mobile stamp badge displays current count
      expect(html).toContain(">4<");
    });
  });
});
