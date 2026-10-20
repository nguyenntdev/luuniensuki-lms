import { describe, it, expect } from "vitest";
import {
  getHonorsTitle,
  getZoneBreakdown,
  generateCertificateId,
  formatImperialDate,
  buildCertificateUrl,
} from "./certificate-utils";
import { PASSPORT_SEALS } from "./passport-storage";

describe("STTT-SPEC-AUDIO-PASSPORT-002: Certificate of Heritage Completion Suite", () => {
  it("computes accurate honors title according to unlocked seal count rules", () => {
    // 0-3 seals: Novice
    const novice0 = getHonorsTitle(0);
    expect(novice0.tier).toBe("novice");
    expect(novice0.title).toContain("Người Khởi Đầu");

    const novice3 = getHonorsTitle(3);
    expect(novice3.tier).toBe("novice");

    // 4-7 seals: "Tập Sự Khảo Cứu Di Sản"
    const apprentice4 = getHonorsTitle(4);
    expect(apprentice4.tier).toBe("apprentice");
    expect(apprentice4.title).toBe("Tập Sự Khảo Cứu Di Sản");

    const apprentice7 = getHonorsTitle(7);
    expect(apprentice7.tier).toBe("apprentice");
    expect(apprentice7.title).toBe("Tập Sự Khảo Cứu Di Sản");

    // 8-11 seals: "Thám Hiểm Cung Đình Huế"
    const explorer8 = getHonorsTitle(8);
    expect(explorer8.tier).toBe("explorer");
    expect(explorer8.title).toBe("Thám Hiểm Cung Đình Huế");

    const explorer11 = getHonorsTitle(11);
    expect(explorer11.tier).toBe("explorer");
    expect(explorer11.title).toBe("Thám Hiểm Cung Đình Huế");

    // 12-15 seals: "Học Giả Di Sản Hoàng Thành"
    const scholar12 = getHonorsTitle(12);
    expect(scholar12.tier).toBe("scholar");
    expect(scholar12.title).toBe("Học Giả Di Sản Hoàng Thành");

    const scholar15 = getHonorsTitle(15);
    expect(scholar15.tier).toBe("scholar");
    expect(scholar15.title).toBe("Học Giả Di Sản Hoàng Thành");

    // 16 seals: "Bậc Thầy Khảo Cứu Cố Đô"
    const master16 = getHonorsTitle(16);
    expect(master16.tier).toBe("master");
    expect(master16.title).toBe("Bậc Thầy Khảo Cứu Cố Đô");
  });

  it("calculates zone breakdown correctly across 4 spatial zones", () => {
    // Unlock all seals in Central Axis (4 sites)
    const centralSlugs = [
      "ngo-mon",
      "cau-trung-dao",
      "san-dai-trieu-nghi",
      "dien-thai-hoa",
    ];
    const breakdown = getZoneBreakdown(centralSlugs);

    expect(breakdown).toHaveLength(4);

    const centralZone = breakdown.find(
      (z) => z.zoneSlug === "central-ceremonial-axis",
    );
    expect(centralZone).toBeDefined();
    expect(centralZone?.totalCount).toBe(4);
    expect(centralZone?.unlockedCount).toBe(4);
    expect(centralZone?.isCompleted).toBe(true);

    const forbiddenZone = breakdown.find(
      (z) => z.zoneSlug === "purple-forbidden-city",
    );
    expect(forbiddenZone).toBeDefined();
    expect(forbiddenZone?.unlockedCount).toBe(0);
    expect(forbiddenZone?.isCompleted).toBe(false);
  });

  it("generates well-formatted certificate serial id", () => {
    const id = generateCertificateId("Nguyễn Hoàng Minh");
    expect(id).toMatch(/^LN-DN-2026-[A-Z0-9]{4}-[A-Z0-9]{4}$/);
  });

  it("formats royal decree imperial date in Vietnamese standard", () => {
    const date = new Date(2026, 9, 16); // Oct 16, 2026
    const formatted = formatImperialDate(date);
    expect(formatted).toBe("Huế, ngày 16 tháng 10 năm 2026");
  });

  it("builds valid verifiable certificate URL with query params", () => {
    const url = buildCertificateUrl(
      "https://lms.histolab.icu",
      {
        id: "LN-DN-2026-ABCD-1234",
        studentName: "Trần Bảo Nam",
        schoolName: "THPT Chuyên Quốc Học Huế",
        unlockedSiteSlugs: ["ngo-mon", "dien-thai-hoa"],
      },
      true,
    );

    expect(url).toContain("https://lms.histolab.icu/dai-noi/chung-nhan");
    expect(url).toContain("id=LN-DN-2026-ABCD-1234");
    expect(url).toContain("name=Tr%E1%BA%A7n+B%E1%BA%A3o+Nam");
    expect(url).toContain("school=THPT+Chuy%C3%AAn+Qu%E1%BB%91c+H%E1%BB%8Dc+Hu%E1%BA%BF");
    expect(url).toContain("seals=2");
    expect(url).toContain("verify=1");
  });

  it("has strictly 16 total seals defined in passport storage", () => {
    expect(PASSPORT_SEALS).toHaveLength(16);
  });
});
