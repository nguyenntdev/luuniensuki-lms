import { describe, expect, it } from "vitest";
import {
  VERIFIED_VIRTUAL_MUSEUM_MONUMENTS,
  getVerifiedMonument,
  getVerifiedMonumentOrFallback,
  isBrokenPanoramaUri,
  generateAccessible2DDescription,
  resolvePanorama2DFallback,
} from "./panorama-sources";

describe("360 Virtual Museum Source Links & Provenance Registry", () => {
  it("verifies canonical monuments are registered with primary sources and rights owner", () => {
    const requiredKeys = ["cuu-dinh", "the-mieu", "ngo-mon", "dien-thai-hoa", "kinh-thanh", "hien-lam-cac"];
    for (const key of requiredKeys) {
      const mon = VERIFIED_VIRTUAL_MUSEUM_MONUMENTS[key];
      expect(mon).toBeDefined();
      expect(mon.name).toBeTruthy();
      expect(mon.historicalPeriod).toBeTruthy();
      expect(mon.provenance).toBeTruthy();
      expect(mon.rightsOwner).toBe("Trung tâm Bảo tồn Di tích Cố đô Huế (HMCC)");
      expect(mon.license).toContain("CC BY 4.0");
      expect(mon.fallbackImageUrl).toBeTruthy();
      expect(mon.sourceCitations.length).toBeGreaterThan(0);

      // Verify each citation contains title, author, and evidence strength
      for (const cite of mon.sourceCitations) {
        expect(cite.title).toBeTruthy();
        expect(cite.evidenceStrength).toBe("verified");
      }
    }
  });

  it("resolves monuments by exact or prefix slug", () => {
    const cuuDinh = getVerifiedMonument("cuu-dinh");
    expect(cuuDinh?.slug).toBe("cuu-dinh");
    expect(cuuDinh?.name).toContain("Cửu Đỉnh");

    const withPrefix = getVerifiedMonument("monument-the-mieu");
    expect(withPrefix?.slug).toBe("the-mieu");
  });

  it("generates deterministic fallback monument for unregistered slugs", () => {
    const fallback = getVerifiedMonumentOrFallback("dien-kien-trung", "Điện Kiến Trung");
    expect(fallback.id).toBe("monument-dien-kien-trung");
    expect(fallback.name).toBe("Điện Kiến Trung");
    expect(fallback.rightsOwner).toContain("HMCC");
    expect(fallback.sourceCitations.length).toBeGreaterThan(0);
    expect(fallback.fallbackImageUrl).toBeTruthy();
  });

  it("accurately detects broken or inaccessible panorama URIs", () => {
    expect(isBrokenPanoramaUri("")).toBe(true);
    expect(isBrokenPanoramaUri(null)).toBe(true);
    expect(isBrokenPanoramaUri(undefined)).toBe(true);
    expect(isBrokenPanoramaUri("   ")).toBe(true);
    expect(isBrokenPanoramaUri("broken://inaccessible-texture.jpg")).toBe(true);
    expect(isBrokenPanoramaUri("/panoramas/invalid-404.jpg")).toBe(true);
    expect(isBrokenPanoramaUri("/panoramas/missing-texture.jpg")).toBe(true);

    expect(isBrokenPanoramaUri("/panoramas/cuu-dinh.jpg")).toBe(false);
    expect(isBrokenPanoramaUri("https://cdn.example.com/panoramas/the-mieu.jpg")).toBe(false);
  });

  it("generates structured accessible 2D descriptions with historical evidence", () => {
    const cuuDinh = VERIFIED_VIRTUAL_MUSEUM_MONUMENTS["cuu-dinh"];
    const description = generateAccessible2DDescription(cuuDinh, [
      { title: "Cao Đỉnh", description: "Đỉnh đồng biểu trưng cho vua Gia Long" },
      { title: "Nhân Đỉnh", description: "Đỉnh đồng biểu trưng cho vua Minh Mạng" },
    ]);

    expect(description).toContain("Cửu Đỉnh");
    expect(description).toContain("Minh Mạng");
    expect(description).toContain("Đại Nam Thực Lục Chính Biên");
    expect(description).toContain("Cao Đỉnh");
    expect(description).toContain("Nhân Đỉnh");
    expect(description).toContain("Trung tâm Bảo tồn Di tích Cố đô Huế (HMCC)");
  });

  it("resolves 2D still fallbacks with safe defaults for broken URIs", () => {
    const resolution = resolvePanorama2DFallback(
      "broken://bad-uri.jpg",
      undefined,
      "cuu-dinh"
    );

    expect(resolution.isBroken).toBe(true);
    expect(resolution.fallbackImageUrl).toBe("/ban-duc-noi/CAO DINH/CAO ĐỈNH.jpg");
    expect(resolution.monument.slug).toBe("cuu-dinh");
    expect(resolution.accessibleDescription).toContain("Cửu Đỉnh");
  });
});
