import { describe, it, expect } from "vitest";
import { RBPC_NAV_ITEMS } from "./shell/RbpcHeader";
import { FILTER_CATEGORY_TABS } from "./explore/HeritageFilters";
import { getRbpcCopy, getEpistemicBadgeCopy } from "@/lib/rbpc/copy";
import type { HeritagePlace } from "@/types/heritage";

describe("RbpcHeader Navigation Contract", () => {
  it("defines exactly 5 primary navigation destinations", () => {
    expect(RBPC_NAV_ITEMS).toHaveLength(5);
  });

  it("contains the canonical 5-link destinations with exact routes", () => {
    const expectedRoutes = [
      "/explore",
      "/people",
      "/experiences",
      "/learn",
      "/about",
    ];
    const actualRoutes = RBPC_NAV_ITEMS.map((item) => item.href);
    expect(actualRoutes).toEqual(expectedRoutes);
  });

  it("provides bilingual labels and descriptions for all 5 nav links", () => {
    for (const item of RBPC_NAV_ITEMS) {
      expect(item.labelVi.trim().length).toBeGreaterThan(0);
      expect(item.labelEn.trim().length).toBeGreaterThan(0);
      expect(item.descriptionVi.trim().length).toBeGreaterThan(0);
      expect(item.descriptionEn.trim().length).toBeGreaterThan(0);
      expect(item.labelVi).not.toEqual(item.labelEn);
    }
  });

  it("maps to correct default localized labels", () => {
    const viLabels = RBPC_NAV_ITEMS.map((i) => i.labelVi);
    expect(viLabels).toContain("Khám phá");
    expect(viLabels).toContain("Nghệ nhân");
    expect(viLabels).toContain("Trải nghiệm");
    expect(viLabels).toContain("Học tập");
    expect(viLabels).toContain("Về dự án");
  });
});

describe("HeritageFilters Category Tabs Contract", () => {
  it("defines all required category tabs including all", () => {
    const categoryIds = FILTER_CATEGORY_TABS.map((t) => t.id);
    expect(categoryIds).toContain("all");
    expect(categoryIds).toContain("imperial_architecture");
    expect(categoryIds).toContain("royal_tomb");
    expect(categoryIds).toContain("craft_living_culture");
    expect(categoryIds).toContain("music_performance");
  });

  it("provides distinct bilingual labels for each tab", () => {
    for (const tab of FILTER_CATEGORY_TABS) {
      expect(tab.labelVi.trim().length).toBeGreaterThan(0);
      expect(tab.labelEn.trim().length).toBeGreaterThan(0);
      expect(tab.icon).toBeDefined();
    }
  });
});

describe("HeritageCard Epistemic & UNESCO Contract Integration", () => {
  const mockPlace: HeritagePlace = {
    id: "hue-ngo-mon",
    slug: "ngo-mon",
    name_vi: "Ngọ Môn — Đại Nội Huế",
    name_en: "Meridian Gate, Hue Imperial City",
    entity_type: "monument",
    heritage_category: "imperial_architecture",
    official_reference_id: "678-001",
    official_designation: "UNESCO World Heritage Component",
    period_label: "Triều Minh Mạng (1833)",
    visitor_summary_vi: "Cổng chính phía Nam của Hoàng thành Huế.",
    visitor_summary_en: "Main southern gate of the Hue Imperial City.",
    current_access_status: "open",
    editorial_status: "published",
    content_scope: "RBPC_HUE",
    has_3d: true,
    created_at: "2026-10-18T00:00:00Z",
    updated_at: "2026-10-18T00:00:00Z",
  };

  it("evaluates verified_source for published editorial status", () => {
    const badgeVi = getEpistemicBadgeCopy("verified_source", "vi");
    const badgeEn = getEpistemicBadgeCopy("verified_source", "en");

    expect(badgeVi.label).toBe("Đã đối chiếu tư liệu");
    expect(badgeEn.label).toBe("Verified by source");
  });

  it("evaluates living_tradition for craft heritage category", () => {
    const badgeVi = getEpistemicBadgeCopy("living_tradition", "vi");
    const badgeEn = getEpistemicBadgeCopy("living_tradition", "en");

    expect(badgeVi.label).toBe("Di sản sống & Làng nghề");
    expect(badgeEn.label).toBe("Living Tradition");
  });

  it("verifies official UNESCO 678 reference format on mock place", () => {
    expect(mockPlace.official_reference_id).toMatch(/^678-\d{3}$/);
  });
});

describe("RbpcFooter Provenance & Brand Copy Verification", () => {
  it("contains UNESCO 678 disclaimer in both languages", () => {
    const copyVi = getRbpcCopy("vi");
    const copyEn = getRbpcCopy("en");

    expect(copyVi.brand.unescoDisclaimer).toContain("UNESCO");
    expect(copyVi.brand.unescoDisclaimer).toContain("678");
    expect(copyEn.brand.unescoDisclaimer).toContain("UNESCO");
    expect(copyEn.brand.unescoDisclaimer).toContain("678");
  });

  it("contains strict archival citation policy in both languages", () => {
    const copyVi = getRbpcCopy("vi");
    const copyEn = getRbpcCopy("en");

    expect(copyVi.brand.citationPolicy.length).toBeGreaterThan(20);
    expect(copyEn.brand.citationPolicy.length).toBeGreaterThan(20);
  });

  it("contains valid brand strapline and identity", () => {
    const copyVi = getRbpcCopy("vi");
    const copyEn = getRbpcCopy("en");

    expect(copyVi.brand.name).toBe("LƯU NIÊN");
    expect(copyVi.brand.strapline).toContain("Khám phá câu chuyện");
    expect(copyEn.brand.strapline).toContain("Discover the story");
  });
});
