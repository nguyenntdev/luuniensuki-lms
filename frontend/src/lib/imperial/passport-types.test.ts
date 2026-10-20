import { describe, it, expect } from "vitest";
import {
  MONUMENT_SEALS_CATALOG,
  getMonumentSeal,
  getHeritageRankTitle,
  calculatePassportProgress,
  createDefaultPassportData,
  type PassportStampRecord,
} from "./passport-types";

describe("Passport & Royal Seals Engine (passport-types.ts)", () => {
  describe("MONUMENT_SEALS_CATALOG", () => {
    it("contains all 16 monuments in Đại Nội Huế", () => {
      expect(MONUMENT_SEALS_CATALOG).toHaveLength(16);
    });

    it("verifies all 16 monuments have unique slugs and IDs", () => {
      const slugs = MONUMENT_SEALS_CATALOG.map((s) => s.monumentSlug);
      const ids = MONUMENT_SEALS_CATALOG.map((s) => s.id);

      const uniqueSlugs = new Set(slugs);
      const uniqueIds = new Set(ids);

      expect(uniqueSlugs.size).toBe(16);
      expect(uniqueIds.size).toBe(16);
    });

    it("verifies all expected core monuments exist", () => {
      const expectedSlugs = [
        "ngo-mon",
        "cau-trung-dao",
        "san-dai-trieu-nghi",
        "dien-thai-hoa",
        "the-to-mieu",
        "hien-lam-cac",
        "hung-to-mieu",
        "trieu-to-mieu",
        "dien-phung-tien",
        "dai-cung-mon",
        "dien-can-chanh",
        "dien-kien-trung",
        "duyet-thi-duong",
        "thai-binh-lau",
        "cung-dien-tho",
        "cung-truong-sanh",
      ];

      expectedSlugs.forEach((slug) => {
        const found = MONUMENT_SEALS_CATALOG.find((s) => s.monumentSlug === slug);
        expect(found, `Missing seal definition for: ${slug}`).toBeDefined();
        expect(found?.sealTextQuocNgu.length).toBeGreaterThan(0);
        expect(found?.sealTextHanNom.length).toBeGreaterThan(0);
        expect(found?.sealScriptCharacters.length).toBeGreaterThanOrEqual(4);
        expect(found?.inkColor).toBe("#A62B2B");
      });
    });

    it("checks distribution across all 4 imperial zones", () => {
      const zones = new Set(MONUMENT_SEALS_CATALOG.map((s) => s.zoneSlug));
      expect(zones).toContain("central-ceremonial-axis");
      expect(zones).toContain("ancestral-worship-space");
      expect(zones).toContain("purple-forbidden-city");
      expect(zones).toContain("royal-living-gardens");
      expect(zones.size).toBe(4);
    });
  });

  describe("getMonumentSeal helper", () => {
    it("retrieves a seal by monument slug or ID case-insensitively", () => {
      const bySlug = getMonumentSeal("ngo-mon");
      const byUpperSlug = getMonumentSeal("NGO-MON");
      const byId = getMonumentSeal("seal-ngo-mon");

      expect(bySlug).toBeDefined();
      expect(bySlug?.monumentNameVi).toBe("Ngọ Môn");
      expect(byUpperSlug?.id).toBe("seal-ngo-mon");
      expect(byId?.monumentSlug).toBe("ngo-mon");
    });

    it("returns undefined for unknown monument slugs", () => {
      expect(getMonumentSeal("unknown-monument")).toBeUndefined();
      expect(getMonumentSeal("")).toBeUndefined();
    });
  });

  describe("getHeritageRankTitle", () => {
    it("assigns appropriate imperial scholarly ranks based on progress", () => {
      expect(getHeritageRankTitle(0)).toBe("Học Tử Nhập Môn");
      expect(getHeritageRankTitle(1)).toBe("Tập Sự Khám Phá Di Sản");
      expect(getHeritageRankTitle(3)).toBe("Tập Sự Khám Phá Di Sản");
      expect(getHeritageRankTitle(4)).toBe("Khảo Cứu Sinh Hoàng Triều");
      expect(getHeritageRankTitle(7)).toBe("Khảo Cứu Sinh Hoàng Triều");
      expect(getHeritageRankTitle(8)).toBe("Bác Học Viện Sĩ Cố Đô");
      expect(getHeritageRankTitle(11)).toBe("Bác Học Viện Sĩ Cố Đô");
      expect(getHeritageRankTitle(12)).toBe("Hàn Lâm Viện Thị Giảng Học Sĩ");
      expect(getHeritageRankTitle(15)).toBe("Hàn Lâm Viện Thị Giảng Học Sĩ");
      expect(getHeritageRankTitle(16)).toBe("Đại Học Sĩ Thái Hòa Điển Tịch");
    });
  });

  describe("calculatePassportProgress", () => {
    it("handles undefined or empty stamp records", () => {
      const res = calculatePassportProgress(undefined);
      expect(res.total).toBe(16);
      expect(res.unlocked).toBe(0);
      expect(res.percentage).toBe(0);
      expect(res.rankTitle).toBe("Học Tử Nhập Môn");
      expect(res.remainingForNextMilestone).toBe(1);
    });

    it("calculates partial progress accurately", () => {
      const stamps: Record<string, PassportStampRecord> = {
        "ngo-mon": { isUnlocked: true },
        "dien-thai-hoa": { isUnlocked: true },
        "the-to-mieu": { isUnlocked: true },
        "cau-trung-dao": { isUnlocked: true }, // 4 unlocked -> 25%
        "thai-binh-lau": { isUnlocked: false },
      };

      const res = calculatePassportProgress(stamps);
      expect(res.total).toBe(16);
      expect(res.unlocked).toBe(4);
      expect(res.percentage).toBe(25);
      expect(res.rankTitle).toBe("Khảo Cứu Sinh Hoàng Triều");
      expect(res.remainingForNextMilestone).toBe(4); // needs 8 for Bac Hoc Vien Si Co Do
    });

    it("calculates 100% completion when all 16 are unlocked", () => {
      const stamps: Record<string, PassportStampRecord> = {};
      MONUMENT_SEALS_CATALOG.forEach((s) => {
        stamps[s.monumentSlug] = { isUnlocked: true };
      });

      const res = calculatePassportProgress(stamps);
      expect(res.unlocked).toBe(16);
      expect(res.percentage).toBe(100);
      expect(res.rankTitle).toBe("Đại Học Sĩ Thái Hòa Điển Tịch");
      expect(res.remainingForNextMilestone).toBe(0);
    });
  });

  describe("createDefaultPassportData", () => {
    it("initializes a valid default passport for a student", () => {
      const passport = createDefaultPassportData("Nguyễn Văn A", "11 Chuyên Sử");

      expect(passport.studentName).toBe("Nguyễn Văn A");
      expect(passport.studentClass).toBe("11 Chuyên Sử");
      expect(passport.totalMonuments).toBe(16);
      expect(passport.totalStamped).toBe(0);
      expect(passport.completionPercentage).toBe(0);
      expect(Object.keys(passport.stamps)).toHaveLength(16);

      // Verify every monument is initially locked
      Object.values(passport.stamps).forEach((stamp) => {
        expect(stamp.isUnlocked).toBe(false);
      });
    });
  });
});
