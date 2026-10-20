/**
 * Unit test suite for STTTNNĐ Royal Seals & Digital Heritage Passport Logic.
 * Spec ID: STTT-SPEC-AUDIO-PASSPORT-002
 * Scope: STTT_IMPERIAL_CITY (Đại Nội Huế — 16 Historical Monuments across 4 Spatial Zones)
 *
 * Validates:
 * 1. Seal unlocking progression across 16 monuments.
 * 2. Cluster / zone completion calculations.
 * 3. Title tier evaluation based on count (4, 8, 12, 16).
 * 4. Idempotency of seal unlocks.
 * 5. Certificate eligibility and validation.
 */

import { describe, it, expect, beforeEach, vi } from "vitest";
import {
  PASSPORT_SEALS,
  PASSPORT_ZONE_META,
  PASSPORT_ALL_BADGES,
  TOTAL_MONUMENTS_COUNT,
  MIN_CERTIFICATE_SEALS_REQUIRED,
  TITLE_TIER_THRESHOLDS,
  getPassportProgress,
  getUnlockedSeals,
  getUnlockedSealsMap,
  isSealUnlocked,
  getSealDefinition,
  unlockSeal,
  resetPassport,
  unlockAllSealsDemo,
  unlockCertificateDemo,
  evaluateTitleTier,
  getHonorsTitle,
  calculateClusterCompletion,
  getZoneBreakdown,
  isClusterCompleted,
  getClusterUnlockedCount,
  generateCertificateId,
  formatImperialDate,
  PASSPORT_STORAGE_KEY,
  ZONE_ROYAL_SEALS_CATALOG,
  GRAND_ROYAL_SEAL,
  getZoneRoyalSeal,
  getGrandRoyalSeal,
  isZoneSealStamped,
  stampZoneSeal,
  isGrandSealStamped,
  stampGrandSeal,
} from "./passport-logic";

describe("STTTNNĐ Royal Heritage Passport Logic Suite", () => {
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

  // =========================================================================
  // 1. SEAL UNLOCKING PROGRESSION ACROSS 16 MONUMENTS
  // =========================================================================
  describe("1. Seal Unlocking Progression Across 16 Monuments", () => {
    it("contains exactly 16 verified historical monuments in catalog", () => {
      expect(PASSPORT_SEALS).toHaveLength(TOTAL_MONUMENTS_COUNT);
      expect(TOTAL_MONUMENTS_COUNT).toBe(16);

      const slugs = PASSPORT_SEALS.map((s) => s.slug);
      const uniqueSlugs = new Set(slugs);
      expect(uniqueSlugs.size).toBe(16);
    });

    it("verifies initial state has 0 unlocked seals and 0% progress", () => {
      const progress = getPassportProgress();
      expect(progress.totalSeals).toBe(16);
      expect(progress.unlockedCount).toBe(0);
      expect(progress.percentage).toBe(0);
      expect(progress.unlockedSlugs).toHaveLength(0);
      expect(progress.canExportCertificate).toBe(false);
    });

    it("tracks incremental progression accurately from 1 to 16 seals", () => {
      for (let i = 0; i < PASSPORT_SEALS.length; i++) {
        const seal = PASSPORT_SEALS[i];
        const progress = unlockSeal(seal.slug, `Hoàn thành nhiệm vụ di tích ${seal.name}`);

        const expectedCount = i + 1;
        const expectedPercentage = Math.round((expectedCount / 16) * 100);

        expect(progress.unlockedCount).toBe(expectedCount);
        expect(progress.percentage).toBe(expectedPercentage);
        expect(progress.unlockedSlugs).toContain(seal.slug);
        expect(isSealUnlocked(seal.slug)).toBe(true);

        const storedList = getUnlockedSeals();
        expect(storedList).toHaveLength(expectedCount);
        expect(storedList[i].slug).toBe(seal.slug);
        expect(storedList[i].siteName).toBe(seal.name);
      }

      // At step 16: exactly 100% completion
      const finalProgress = getPassportProgress();
      expect(finalProgress.unlockedCount).toBe(16);
      expect(finalProgress.percentage).toBe(100);
      expect(finalProgress.canExportCertificate).toBe(true);
    });

    it("supports unlocking all seals via demo helper", () => {
      const progress = unlockAllSealsDemo();
      expect(progress.unlockedCount).toBe(16);
      expect(progress.percentage).toBe(100);
      expect(progress.unlockedSlugs).toHaveLength(16);

      for (const seal of PASSPORT_SEALS) {
        expect(isSealUnlocked(seal.slug)).toBe(true);
      }
    });

    it("clears all unlocked seals and resets progression to zero", () => {
      unlockAllSealsDemo();
      expect(getPassportProgress().unlockedCount).toBe(16);

      const resetResult = resetPassport();
      expect(resetResult.unlockedCount).toBe(0);
      expect(resetResult.percentage).toBe(0);
      expect(resetResult.unlockedSlugs).toEqual([]);
      expect(resetResult.earnedBadges).toEqual([]);
      expect(getUnlockedSeals()).toEqual([]);

      for (const seal of PASSPORT_SEALS) {
        expect(isSealUnlocked(seal.slug)).toBe(false);
      }
    });

    it("retrieves individual seal definition with valid epigraphy and metadata", () => {
      const ngoMon = getSealDefinition("ngo-mon");
      expect(ngoMon).toBeDefined();
      expect(ngoMon?.name).toBe("Ngọ Môn");
      expect(ngoMon?.nameHanNom).toBe("午門");
      expect(ngoMon?.sealTitle).toBe("Ngọ Môn Chi Ấn");
      expect(ngoMon?.sealTitleHanNom).toBe("午門之印");
      expect(ngoMon?.zoneSlug).toBe("central-ceremonial-axis");
      expect(ngoMon?.constructionYear).toBe(1833);
      expect(ngoMon?.reign).toBe("Minh Mạng");

      const thaiHoa = getSealDefinition("dien-thai-hoa");
      expect(thaiHoa).toBeDefined();
      expect(thaiHoa?.name).toBe("Điện Thái Hòa");
      expect(thaiHoa?.nameHanNom).toBe("太和殿");
      expect(thaiHoa?.sealTitle).toBe("Thái Hòa Điện Ấn");

      const unknown = getSealDefinition("unknown-monument");
      expect(unknown).toBeUndefined();
    });
  });

  // =========================================================================
  // 2. CLUSTER COMPLETION CALCULATIONS
  // =========================================================================
  describe("2. Cluster / Zone Completion Calculations", () => {
    it("distributes all 16 monuments across exactly 4 spatial clusters", () => {
      const central = PASSPORT_SEALS.filter((s) => s.zoneSlug === "central-ceremonial-axis");
      const worship = PASSPORT_SEALS.filter((s) => s.zoneSlug === "ancestral-worship-space");
      const forbidden = PASSPORT_SEALS.filter((s) => s.zoneSlug === "purple-forbidden-city");
      const living = PASSPORT_SEALS.filter((s) => s.zoneSlug === "royal-living-gardens");

      expect(central).toHaveLength(4);
      expect(worship).toHaveLength(4);
      expect(forbidden).toHaveLength(5);
      expect(living).toHaveLength(3);
      expect(central.length + worship.length + forbidden.length + living.length).toBe(16);
    });

    it("evaluates empty cluster breakdown when 0 seals are unlocked", () => {
      const breakdown = calculateClusterCompletion([]);
      expect(breakdown).toHaveLength(4);

      for (const cluster of breakdown) {
        expect(cluster.unlockedCount).toBe(0);
        expect(cluster.isCompleted).toBe(false);
      }

      expect(isClusterCompleted("central-ceremonial-axis", [])).toBe(false);
      expect(getClusterUnlockedCount("central-ceremonial-axis", [])).toBe(0);
    });

    it("calculates partial cluster completion accurately", () => {
      // Unlock 2 out of 4 in Central axis
      const unlockedSlugs = ["ngo-mon", "cau-trung-dao"];
      const breakdown = calculateClusterCompletion(unlockedSlugs);

      const central = breakdown.find((z) => z.zoneSlug === "central-ceremonial-axis");
      expect(central).toBeDefined();
      expect(central?.totalCount).toBe(4);
      expect(central?.unlockedCount).toBe(2);
      expect(central?.isCompleted).toBe(false);

      expect(isClusterCompleted("central-ceremonial-axis", unlockedSlugs)).toBe(false);
      expect(getClusterUnlockedCount("central-ceremonial-axis", unlockedSlugs)).toBe(2);

      // Other clusters must remain 0
      const worship = breakdown.find((z) => z.zoneSlug === "ancestral-worship-space");
      expect(worship?.unlockedCount).toBe(0);
      expect(worship?.isCompleted).toBe(false);
    });

    it("marks cluster as complete when all its monuments are unlocked", () => {
      const centralSlugs = ["ngo-mon", "cau-trung-dao", "san-dai-trieu-nghi", "dien-thai-hoa"];
      for (const slug of centralSlugs) {
        unlockSeal(slug);
      }

      const progress = getPassportProgress();
      const centralZone = progress.zones.find((z) => z.zoneSlug === "central-ceremonial-axis");
      expect(centralZone?.isComplete).toBe(true);
      expect(centralZone?.unlockedCount).toBe(4);
      expect(centralZone?.percentage).toBe(100);

      // Verify helper function returns true
      expect(isClusterCompleted("central-ceremonial-axis", centralSlugs)).toBe(true);

      // Central zone badge awarded
      const badgeIds = progress.earnedBadges.map((b) => b.id);
      expect(badgeIds).toContain("badge-zone-central");
      expect(badgeIds).not.toContain("badge-zone-worship");
      expect(badgeIds).not.toContain("badge-zone-forbidden");
      expect(badgeIds).not.toContain("badge-zone-living");
      expect(badgeIds).not.toContain("badge-master-all");
    });

    it("awards master badge only when all 4 clusters are completed", () => {
      // 1. Complete Central Axis (4)
      ["ngo-mon", "cau-trung-dao", "san-dai-trieu-nghi", "dien-thai-hoa"].forEach((s) => unlockSeal(s));
      // 2. Complete Worship Space (4)
      ["the-to-mieu", "hien-lam-cac", "hung-to-mieu", "trieu-to-mieu"].forEach((s) => unlockSeal(s));
      // 3. Complete Forbidden City (5)
      ["dai-cung-mon", "dien-can-chanh", "dien-kien-trung", "duyet-thi-duong", "thai-binh-lau"].forEach((s) => unlockSeal(s));

      let progress = getPassportProgress();
      expect(progress.unlockedCount).toBe(13);
      expect(progress.earnedBadges.map((b) => b.id)).not.toContain("badge-master-all");

      // 4. Complete Living Gardens (3)
      ["cung-dien-tho", "cung-truong-sanh", "dien-phung-tien"].forEach((s) => unlockSeal(s));

      progress = getPassportProgress();
      expect(progress.unlockedCount).toBe(16);
      expect(progress.percentage).toBe(100);

      const allEarnedIds = progress.earnedBadges.map((b) => b.id);
      expect(allEarnedIds).toHaveLength(5);
      expect(allEarnedIds).toContain("badge-zone-central");
      expect(allEarnedIds).toContain("badge-zone-worship");
      expect(allEarnedIds).toContain("badge-zone-forbidden");
      expect(allEarnedIds).toContain("badge-zone-living");
      expect(allEarnedIds).toContain("badge-master-all");
    });
  });

  // =========================================================================
  // 3. TITLE TIER EVALUATION BASED ON COUNT (4, 8, 12, 16)
  // =========================================================================
  describe("3. Title Tier Evaluation Based on Count (4, 8, 12, 16)", () => {
    it("evaluates 'novice' tier for 0 to 3 seals", () => {
      for (let count = 0; count <= 3; count++) {
        const title = evaluateTitleTier(count);
        expect(title.tier).toBe("novice");
        expect(title.title).toBe("Người Khởi Đầu Khám Phá");
        expect(title.titleEn).toBe("Heritage Explorer Novice");
        expect(title.minSeals).toBe(TITLE_TIER_THRESHOLDS.NOVICE);
        expect(title.maxSeals).toBe(3);
      }
    });

    it("evaluates 'apprentice' tier starting at threshold of 4 seals", () => {
      for (let count = 4; count <= 7; count++) {
        const title = evaluateTitleTier(count);
        expect(title.tier).toBe("apprentice");
        expect(title.title).toBe("Tập Sự Khảo Cứu Di Sản");
        expect(title.titleEn).toBe("Heritage Research Apprentice");
        expect(title.minSeals).toBe(TITLE_TIER_THRESHOLDS.APPRENTICE);
        expect(title.maxSeals).toBe(7);
        expect(title.accentColor).toBe("#A62B2B"); // Chu sa red
      }
    });

    it("evaluates 'explorer' tier starting at threshold of 8 seals", () => {
      for (let count = 8; count <= 11; count++) {
        const title = evaluateTitleTier(count);
        expect(title.tier).toBe("explorer");
        expect(title.title).toBe("Thám Hiểm Cung Đình Huế");
        expect(title.titleEn).toBe("Imperial Citadel Explorer");
        expect(title.minSeals).toBe(TITLE_TIER_THRESHOLDS.EXPLORER);
        expect(title.maxSeals).toBe(11);
      }
    });

    it("evaluates 'scholar' tier starting at threshold of 12 seals", () => {
      for (let count = 12; count <= 15; count++) {
        const title = evaluateTitleTier(count);
        expect(title.tier).toBe("scholar");
        expect(title.title).toBe("Học Giả Di Sản Hoàng Thành");
        expect(title.titleEn).toBe("Imperial Heritage Scholar");
        expect(title.minSeals).toBe(TITLE_TIER_THRESHOLDS.SCHOLAR);
        expect(title.maxSeals).toBe(15);
      }
    });

    it("evaluates 'master' tier at full 16 seals", () => {
      const title = evaluateTitleTier(16);
      expect(title.tier).toBe("master");
      expect(title.title).toBe("Bậc Thầy Khảo Cứu Cố Đô");
      expect(title.titleEn).toBe("Master Heritage Researcher of the Ancient Capital");
      expect(title.minSeals).toBe(TITLE_TIER_THRESHOLDS.MASTER);
      expect(title.maxSeals).toBe(16);
      expect(title.accentColor).toBe("#C68A2C"); // Imperial Gold
    });

    it("handles boundary edge values safely", () => {
      // Negative count clamps to 0 (novice)
      const underflow = evaluateTitleTier(-5);
      expect(underflow.tier).toBe("novice");
      expect(underflow.minSeals).toBe(0);

      // Over 16 clamps to 16 (master)
      const overflow = evaluateTitleTier(100);
      expect(overflow.tier).toBe("master");
      expect(overflow.minSeals).toBe(16);
    });

    it("triggers rank tier transition exactly at milestone boundaries", () => {
      // 3 -> 4
      expect(evaluateTitleTier(3).tier).toBe("novice");
      expect(evaluateTitleTier(4).tier).toBe("apprentice");

      // 7 -> 8
      expect(evaluateTitleTier(7).tier).toBe("apprentice");
      expect(evaluateTitleTier(8).tier).toBe("explorer");

      // 11 -> 12
      expect(evaluateTitleTier(11).tier).toBe("explorer");
      expect(evaluateTitleTier(12).tier).toBe("scholar");

      // 15 -> 16
      expect(evaluateTitleTier(15).tier).toBe("scholar");
      expect(evaluateTitleTier(16).tier).toBe("master");
    });
  });

  // =========================================================================
  // 4. IDEMPOTENCY OF SEAL UNLOCKS
  // =========================================================================
  describe("4. Idempotency of Seal Unlocks", () => {
    it("ensures duplicate unlock calls for the same seal do not inflate count", () => {
      expect(getPassportProgress().unlockedCount).toBe(0);

      const p1 = unlockSeal("ngo-mon", "Khảo sát lần đầu");
      expect(p1.unlockedCount).toBe(1);

      const p2 = unlockSeal("ngo-mon", "Khảo sát lặp lại 1");
      expect(p2.unlockedCount).toBe(1);

      const p3 = unlockSeal("ngo-mon", "Khảo sát lặp lại 2");
      expect(p3.unlockedCount).toBe(1);

      const list = getUnlockedSeals();
      expect(list).toHaveLength(1);
      expect(list[0].slug).toBe("ngo-mon");
      expect(list[0].reason).toBe("Khảo sát lần đầu"); // Preserves initial unlock reason
    });

    it("maintains storage idempotency across multiple distinct seals and repeats", () => {
      unlockSeal("ngo-mon", "Lần 1");
      unlockSeal("cau-trung-dao", "Lần 1");
      unlockSeal("ngo-mon", "Lần 2"); // Duplicate
      unlockSeal("san-dai-trieu-nghi", "Lần 1");
      unlockSeal("cau-trung-dao", "Lần 2"); // Duplicate
      unlockSeal("dien-thai-hoa", "Lần 1");

      const progress = getPassportProgress();
      expect(progress.unlockedCount).toBe(4);
      expect(progress.unlockedSlugs).toEqual([
        "ngo-mon",
        "cau-trung-dao",
        "san-dai-trieu-nghi",
        "dien-thai-hoa",
      ]);

      const stored = getUnlockedSeals();
      expect(stored).toHaveLength(4);
      const slugsInStorage = stored.map((s) => s.slug);
      expect(new Set(slugsInStorage).size).toBe(4);
    });

    it("returns consistent lookup map entries regardless of call count", () => {
      for (let i = 0; i < 5; i++) {
        unlockSeal("the-to-mieu", `Lần ${i}`);
      }

      const map = getUnlockedSealsMap();
      expect(Object.keys(map)).toHaveLength(1);
      expect(map["the-to-mieu"]).toBeDefined();
      expect(map["the-to-mieu"].slug).toBe("the-to-mieu");
    });
  });

  // =========================================================================
  // 5. CERTIFICATE ELIGIBILITY & VALIDATION
  // =========================================================================
  describe("5. Certificate Eligibility & Validation", () => {
    it("locks certificate export until at least 4 seals are unlocked", () => {
      expect(getPassportProgress().canExportCertificate).toBe(false);

      unlockSeal("ngo-mon");
      expect(getPassportProgress().canExportCertificate).toBe(false);

      unlockSeal("cau-trung-dao");
      expect(getPassportProgress().canExportCertificate).toBe(false);

      unlockSeal("san-dai-trieu-nghi");
      expect(getPassportProgress().canExportCertificate).toBe(false);

      unlockSeal("dien-thai-hoa");
      expect(getPassportProgress().canExportCertificate).toBe(true);
      expect(getPassportProgress().minCertificateSeals).toBe(MIN_CERTIFICATE_SEALS_REQUIRED);
    });

    it("unlockCertificateDemo unlocks exactly 4 seals and enables certificate", () => {
      const progress = unlockCertificateDemo();
      expect(progress.unlockedCount).toBe(4);
      expect(progress.canExportCertificate).toBe(true);
    });

    it("generates deterministic serial format for completion certificates", () => {
      const id1 = generateCertificateId();
      const id2 = generateCertificateId();

      expect(id1).toMatch(/^LN-DN-2026-[A-Z0-9]{4}-[A-Z0-9]{4}$/);
      expect(id2).toMatch(/^LN-DN-2026-[A-Z0-9]{4}-[A-Z0-9]{4}$/);
      expect(id1).not.toBe(id2);
    });

    it("formats traditional imperial date string properly", () => {
      const testDate = new Date(2026, 9, 16); // October 16, 2026
      const formatted = formatImperialDate(testDate);
      expect(formatted).toBe("Huế, ngày 16 tháng 10 năm 2026");
    });
  });

  // =========================================================================
  // 6. UNIQUE ZONE ROYAL SEALS (KIM BẢO & NGỰ TỶ MOTIFS)
  // =========================================================================
  describe("6. Unique Zone Royal Seals (Kim Bảo & Ngự Tỷ Motifs)", () => {
    it("defines 4 authentic zone royal seals matching Nguyen Dynasty imperial seal history", () => {
      const central = getZoneRoyalSeal("central-ceremonial-axis");
      expect(central).toBeDefined();
      expect(central?.sealTextQuocNgu).toBe("Hoàng Đế Chi Bảo");
      expect(central?.sealTextHanNom).toBe("皇帝之寶");
      expect(central?.motif).toBe("kim_bao");
      expect(central?.material).toBe("gold");

      const worship = getZoneRoyalSeal("ancestral-worship-space");
      expect(worship).toBeDefined();
      expect(worship?.sealTextQuocNgu).toBe("Tôn Miếu Ngự Tỷ");
      expect(worship?.sealTextHanNom).toBe("宗廟之璽");
      expect(worship?.motif).toBe("ngu_ty");
      expect(worship?.material).toBe("jade");

      const forbidden = getZoneRoyalSeal("purple-forbidden-city");
      expect(forbidden).toBeDefined();
      expect(forbidden?.sealTextQuocNgu).toBe("Ngự Tiền Chi Bảo");
      expect(forbidden?.sealTextHanNom).toBe("御前之寶");
      expect(forbidden?.motif).toBe("kim_bao");
      expect(forbidden?.material).toBe("gold");

      const living = getZoneRoyalSeal("royal-living-gardens");
      expect(living).toBeDefined();
      expect(living?.sealTextQuocNgu).toBe("Diên Thọ Ngự Tỷ");
      expect(living?.sealTextHanNom).toBe("延壽之璽");
      expect(living?.motif).toBe("ngu_ty");
      expect(living?.material).toBe("jade");
    });

    it("defines the Grand Imperial Seal (Đại Nam Hoàng Đế Chi Bảo) for 16/16 mastery", () => {
      const grand = getGrandRoyalSeal();
      expect(grand).toBeDefined();
      expect(grand.sealTextQuocNgu).toBe("Đại Nam Hoàng Đế Chi Bảo");
      expect(grand.sealTextHanNom).toBe("大南皇帝之寶");
      expect(grand.motif).toBe("kim_bao");
      expect(grand.material).toBe("gold");
      expect(grand.sealScriptCharacters).toEqual(["大", "南", "皇", "帝", "之", "寶"]);
    });

    it("stamps and records zone royal seals when completing clusters", () => {
      // Complete Central Axis
      unlockSeal("ngo-mon");
      unlockSeal("cau-trung-dao");
      unlockSeal("san-dai-trieu-nghi");
      unlockSeal("dien-thai-hoa");

      expect(isZoneSealStamped("central-ceremonial-axis")).toBe(true);
      const res = stampZoneSeal("central-ceremonial-axis");
      expect(res.success).toBe(true);
      expect(res.seal?.motif).toBe("kim_bao");

      const p = getPassportProgress();
      const z = p.zones.find((item) => item.zoneSlug === "central-ceremonial-axis");
      expect(z?.isZoneSealStamped).toBe(true);
      expect(z?.royalSeal?.status).toBe("unlocked");
    });
  });
});
