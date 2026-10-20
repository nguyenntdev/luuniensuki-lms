import { describe, it, expect, beforeEach, vi } from "vitest";
import {
  PASSPORT_SEALS,
  PASSPORT_ZONE_META,
  PASSPORT_ALL_BADGES,
  getUnlockedSeals,
  getUnlockedSealsMap,
  isSealUnlocked,
  getSealDefinition,
  getPassportProgress,
  unlockSeal,
  resetPassport,
  unlockAllSealsDemo,
  unlockCertificateDemo,
  playStampSound,
  isZoneSealStamped,
  stampZoneSeal,
  isGrandSealStamped,
  stampGrandSeal,
  PASSPORT_STORAGE_KEY,
} from "./passport-storage";

describe("Digital Heritage Passport & Royal Seal Storage Suite", () => {
  // In-memory mock storage for localStorage
  let mockStorage: Record<string, string> = {};

  beforeEach(() => {
    mockStorage = {};

    vi.stubGlobal("localStorage", {
      getItem: (key: string) => mockStorage[key] ?? null,
      setItem: (key: string, value: string) => {
        mockStorage[key] = value;
      },
      removeItem: (key: string) => {
        delete mockStorage[key];
      },
      clear: () => {
        mockStorage = {};
      },
    });

    vi.stubGlobal("dispatchEvent", vi.fn());
  });

  it("defines exactly 16 seals across the 4 verified spatial zones", () => {
    expect(PASSPORT_SEALS.length).toBe(16);

    const central = PASSPORT_SEALS.filter((s) => s.zoneSlug === "central-ceremonial-axis");
    const worship = PASSPORT_SEALS.filter((s) => s.zoneSlug === "ancestral-worship-space");
    const forbidden = PASSPORT_SEALS.filter((s) => s.zoneSlug === "purple-forbidden-city");
    const living = PASSPORT_SEALS.filter((s) => s.zoneSlug === "royal-living-gardens");

    expect(central.length).toBe(4);
    expect(worship.length).toBe(4);
    expect(forbidden.length).toBe(5);
    expect(living.length).toBe(3);

    // Verify all slugs are unique
    const slugs = new Set(PASSPORT_SEALS.map((s) => s.slug));
    expect(slugs.size).toBe(16);

    // Verify orders are 1..16
    const orders = PASSPORT_SEALS.map((s) => s.order);
    expect(orders).toEqual(Array.from({ length: 16 }, (_, i) => i + 1));
  });

  it("defines metadata for all 4 spatial zones and badges", () => {
    const zones = Object.keys(PASSPORT_ZONE_META);
    expect(zones).toHaveLength(4);
    expect(zones).toContain("central-ceremonial-axis");
    expect(zones).toContain("ancestral-worship-space");
    expect(zones).toContain("purple-forbidden-city");
    expect(zones).toContain("royal-living-gardens");

    expect(PASSPORT_ALL_BADGES.length).toBe(5);
  });

  it("calculates initial empty progress correctly", () => {
    const progress = getPassportProgress();
    expect(progress.totalSeals).toBe(16);
    expect(progress.unlockedCount).toBe(0);
    expect(progress.percentage).toBe(0);
    expect(progress.unlockedSlugs).toEqual([]);
    expect(progress.earnedBadges).toEqual([]);
    expect(progress.canExportCertificate).toBe(false);
    expect(progress.minCertificateSeals).toBe(4);
  });

  it("unlocks a single seal, updates progress, and stores timestamp", () => {
    expect(isSealUnlocked("ngo-mon")).toBe(false);

    const updated = unlockSeal("ngo-mon", "Khảo sát Ngọ Môn M-E-E");
    expect(updated.unlockedCount).toBe(1);
    expect(updated.percentage).toBe(6); // 1/16 ≈ 6.25% rounded to 6%
    expect(updated.unlockedSlugs).toContain("ngo-mon");
    expect(isSealUnlocked("ngo-mon")).toBe(true);

    const list = getUnlockedSeals();
    expect(list.length).toBe(1);
    expect(list[0].slug).toBe("ngo-mon");
    expect(list[0].reason).toBe("Khảo sát Ngọ Môn M-E-E");
    expect(list[0].unlockedAt).toBeDefined();

    const map = getUnlockedSealsMap();
    expect(map["ngo-mon"]).toBeDefined();
    expect(map["ngo-mon"].slug).toBe("ngo-mon");
  });

  it("prevents duplicate entries when unlocking the same seal multiple times", () => {
    unlockSeal("ngo-mon", "Lần 1");
    unlockSeal("ngo-mon", "Lần 2");

    const progress = getPassportProgress();
    expect(progress.unlockedCount).toBe(1);
    expect(progress.unlockedSlugs).toEqual(["ngo-mon"]);

    const list = getUnlockedSeals();
    expect(list.length).toBe(1);
    expect(list[0].reason).toBe("Lần 1");
  });

  it("activates certificate export when at least 4 seals are unlocked", () => {
    unlockSeal("ngo-mon");
    unlockSeal("cau-trung-dao");
    unlockSeal("san-dai-trieu-nghi");
    expect(getPassportProgress().canExportCertificate).toBe(false);

    const p4 = unlockSeal("dien-thai-hoa");
    expect(p4.unlockedCount).toBe(4);
    expect(p4.canExportCertificate).toBe(true);
  });

  it("awards zone badge when all seals in a zone are unlocked", () => {
    // Complete central axis (4 seals)
    unlockSeal("ngo-mon");
    unlockSeal("cau-trung-dao");
    unlockSeal("san-dai-trieu-nghi");
    const progress = unlockSeal("dien-thai-hoa");

    const centralZone = progress.zones.find((z) => z.zoneSlug === "central-ceremonial-axis");
    expect(centralZone).toBeDefined();
    expect(centralZone?.isComplete).toBe(true);
    expect(centralZone?.unlockedCount).toBe(4);
    expect(centralZone?.percentage).toBe(100);

    const badgeIds = progress.earnedBadges.map((b) => b.id);
    expect(badgeIds).toContain("badge-zone-central");
    expect(badgeIds).not.toContain("badge-zone-worship");
  });

  it("awards master badge when all 16 seals are unlocked", () => {
    const progress = unlockAllSealsDemo();
    expect(progress.unlockedCount).toBe(16);
    expect(progress.percentage).toBe(100);
    expect(progress.canExportCertificate).toBe(true);

    // All 4 zones complete
    expect(progress.zones.every((z) => z.isComplete)).toBe(true);

    // All 5 badges earned
    const earnedIds = progress.earnedBadges.map((b) => b.id);
    expect(earnedIds).toHaveLength(5);
    expect(earnedIds).toContain("badge-zone-central");
    expect(earnedIds).toContain("badge-zone-worship");
    expect(earnedIds).toContain("badge-zone-forbidden");
    expect(earnedIds).toContain("badge-zone-living");
    expect(earnedIds).toContain("badge-master-all");
  });

  it("unlockCertificateDemo unlocks exactly 4 seals", () => {
    const progress = unlockCertificateDemo();
    expect(progress.unlockedCount).toBe(4);
    expect(progress.canExportCertificate).toBe(true);
  });

  it("resets passport completely", () => {
    unlockAllSealsDemo();
    expect(getPassportProgress().unlockedCount).toBe(16);

    const reset = resetPassport();
    expect(reset.unlockedCount).toBe(0);
    expect(reset.percentage).toBe(0);
    expect(reset.earnedBadges).toEqual([]);
    expect(getUnlockedSeals()).toEqual([]);
  });

  it("getSealDefinition returns correct definition or undefined", () => {
    const def = getSealDefinition("dien-thai-hoa");
    expect(def).toBeDefined();
    expect(def?.name).toBe("Điện Thái Hòa");
    expect(def?.nameHanNom).toBe("太和殿");
    expect(def?.sealTitle).toBe("Thái Hòa Điện Ấn");

    const invalid = getSealDefinition("invalid-monument");
    expect(invalid).toBeUndefined();
  });

  it("playStampSound executes safely without throwing", () => {
    expect(() => playStampSound()).not.toThrow();
  });

  it("persists unique royal seals for completed zones (Kim Bảo, Ngự Tỷ) offline in localStorage", () => {
    // Initially not stamped
    expect(isZoneSealStamped("central-ceremonial-axis")).toBe(false);

    // Complete Central Axis (4 monuments)
    unlockSeal("ngo-mon");
    unlockSeal("cau-trung-dao");
    unlockSeal("san-dai-trieu-nghi");
    unlockSeal("dien-thai-hoa");

    // Inherent completion makes isZoneSealStamped true
    expect(isZoneSealStamped("central-ceremonial-axis")).toBe(true);

    // Explicitly stamp zone royal seal (Kim Bảo — Hoàng Đế Chi Bảo)
    const stampResult = stampZoneSeal("central-ceremonial-axis");
    expect(stampResult.success).toBe(true);
    expect(stampResult.seal?.sealTextQuocNgu).toBe("Hoàng Đế Chi Bảo");
    expect(stampResult.seal?.motif).toBe("kim_bao");
    expect(stampResult.seal?.material).toBe("gold");

    // Verify localStorage has the record
    const storedZoneSeals = JSON.parse(mockStorage["luuniensuki_imperial_zone_seals"] || "{}");
    expect(storedZoneSeals["central-ceremonial-axis"]).toBeDefined();
    expect(storedZoneSeals["central-ceremonial-axis"].motif).toBe("kim_bao");
  });

  it("stamps and persists Grand Imperial Seal (Đại Kim Bảo) when all 16 monuments are complete", () => {
    unlockAllSealsDemo();
    expect(isGrandSealStamped()).toBe(true);

    const grandResult = stampGrandSeal();
    expect(grandResult.success).toBe(true);
    expect(grandResult.seal?.sealTextQuocNgu).toBe("Đại Nam Hoàng Đế Chi Bảo");
    expect(grandResult.seal?.motif).toBe("kim_bao");

    const storedZoneSeals = JSON.parse(mockStorage["luuniensuki_imperial_zone_seals"] || "{}");
    expect(storedZoneSeals["grand-master-all"]).toBeDefined();
    expect(storedZoneSeals["grand-master-all"].motif).toBe("kim_bao");

    // Reset clears both monument seals and zone royal seals
    resetPassport();
    expect(isZoneSealStamped("central-ceremonial-axis")).toBe(false);
    expect(mockStorage["luuniensuki_imperial_zone_seals"]).toBeUndefined();
  });
});
