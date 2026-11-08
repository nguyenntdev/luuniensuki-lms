import { describe, it, expect } from "vitest";
import {
  HUE_IMPERIAL_CITY_CENTER,
  HUE_IMPERIAL_CITY_BOUNDS,
  MONUMENT_GPS_REGISTRY,
  getMonumentGps,
  getGoogleMapsUrl,
  getGoogleMapsDirectionsUrl,
  getGoogleMapsEmbedUrl,
} from "./gps-coordinates";

describe("Đại Nội Huế GPS Coordinates Registry & Geodetics", () => {
  it("defines centroid inside Huế Imperial City", () => {
    expect(HUE_IMPERIAL_CITY_CENTER.lat).toBeCloseTo(16.4697, 3);
    expect(HUE_IMPERIAL_CITY_CENTER.lng).toBeCloseTo(107.5786, 3);
  });

  it("registers all 16 primary monuments with accurate WGS84 coordinates", () => {
    const keys = Object.keys(MONUMENT_GPS_REGISTRY);
    expect(keys.length).toBe(16);

    const requiredSlugs = [
      "ngo-mon",
      "cau-trung-dao",
      "san-dai-trieu-nghi",
      "dien-thai-hoa",
      "the-to-mieu",
      "hien-lam-cac",
      "hung-to-mieu",
      "trieu-to-mieu",
      "dai-cung-mon",
      "dien-can-chanh",
      "dien-kien-trung",
      "duyet-thi-duong",
      "thai-binh-lau",
      "cung-dien-tho",
      "cung-truong-sanh",
      "dien-phung-tien",
    ];

    requiredSlugs.forEach((slug) => {
      expect(MONUMENT_GPS_REGISTRY[slug]).toBeDefined();
      const mon = MONUMENT_GPS_REGISTRY[slug];
      expect(mon.name_vi).toBeTruthy();
      expect(mon.name_en).toBeTruthy();
      expect(mon.name_han_nom).toBeTruthy();

      // Verify coordinate is strictly within Huế Citadel bounding box
      expect(mon.lat).toBeGreaterThan(HUE_IMPERIAL_CITY_BOUNDS.south);
      expect(mon.lat).toBeLessThan(HUE_IMPERIAL_CITY_BOUNDS.north);
      expect(mon.lng).toBeGreaterThan(HUE_IMPERIAL_CITY_BOUNDS.west);
      expect(mon.lng).toBeLessThan(HUE_IMPERIAL_CITY_BOUNDS.east);
    });
  });

  it("getMonumentGps returns specific monument or defaults to Huế Citadel center", () => {
    const ngoMon = getMonumentGps("ngo-mon");
    expect(ngoMon.slug).toBe("ngo-mon");
    expect(ngoMon.name_vi).toBe("Ngọ Môn");
    expect(ngoMon.lat).toBe(16.4678);

    const fallback = getMonumentGps("unknown-random-slug");
    expect(fallback.slug).toBe("dai-noi-hue");
    expect(fallback.lat).toBe(HUE_IMPERIAL_CITY_CENTER.lat);
  });

  it("generates valid Google Maps navigation and embed URLs", () => {
    const dirUrl = getGoogleMapsDirectionsUrl(16.4678, 107.5786, "Ngọ Môn");
    expect(dirUrl).toContain("destination=Ng%E1%BB%8D%20M%C3%B4n");
    expect(dirUrl).toContain("16.4678,107.5786");

    const searchUrl = getGoogleMapsUrl(16.4678, 107.5786, "Ngọ Môn");
    expect(searchUrl).toContain("query=Ng%E1%BB%8D%20M%C3%B4n");

    const embedUrl = getGoogleMapsEmbedUrl(16.4678, 107.5786, 18);
    expect(embedUrl).toContain("maps.google.com/maps");
    expect(embedUrl).toContain("t=k");
    expect(embedUrl).toContain("z=18");
  });
});
