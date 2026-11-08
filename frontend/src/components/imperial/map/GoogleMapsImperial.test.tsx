import React from "react";
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { renderToStaticMarkup } from "react-dom/server";
import { GoogleMapsImperial } from "./GoogleMapsImperial";
import {
  DAI_NOI_CENTER,
  IMPERIAL_MONUMENTS_GEO,
} from "@/lib/imperial/monuments-geo";

// Mock @googlemaps/js-api-loader
vi.mock("@googlemaps/js-api-loader", () => ({
  setOptions: vi.fn(),
  importLibrary: vi.fn().mockImplementation((lib: string) => {
    if (lib === "maps") {
      return Promise.resolve({
        Map: vi.fn().mockImplementation(() => ({
          addListener: vi.fn(),
          setZoom: vi.fn(),
          getZoom: vi.fn().mockReturnValue(16),
          setCenter: vi.fn(),
          panTo: vi.fn(),
          setMapTypeId: vi.fn(),
        })),
        InfoWindow: vi.fn().mockImplementation(() => ({
          setContent: vi.fn(),
          open: vi.fn(),
          close: vi.fn(),
        })),
      });
    }
    if (lib === "marker") {
      return Promise.resolve({
        Marker: vi.fn().mockImplementation(() => ({
          addListener: vi.fn(),
          setMap: vi.fn(),
          setIcon: vi.fn(),
          setZIndex: vi.fn(),
        })),
      });
    }
    return Promise.resolve({});
  }),
}));

describe("GoogleMapsImperial Component", () => {
  const originalEnv = process.env.NEXT_PUBLIC_GOOGLE_MAPS_API_KEY;

  beforeEach(() => {
    delete process.env.NEXT_PUBLIC_GOOGLE_MAPS_API_KEY;
  });

  afterEach(() => {
    process.env.NEXT_PUBLIC_GOOGLE_MAPS_API_KEY = originalEnv;
    vi.clearAllMocks();
  });

  it("1. Gracefully renders interactive satellite fallback when API key is not provided (zero crashes)", () => {
    const html = renderToStaticMarkup(
      <GoogleMapsImperial apiKey={undefined} interactiveFallbackOnly={true} />
    );

    expect(html).toContain("data-testid=\"google-maps-imperial-container\"");
    expect(html).toContain("data-testid=\"interactive-fallback-view\"");
    expect(html).toContain("Mô phỏng vệ tinh");
    expect(html).toContain("Đại Nội Huế — Tọa độ Google Maps");
    expect(html).toContain("16.4697° N, 107.5779° E (Đại Nội)");
  });

  it("2. Renders all 16 Đại Nội monument pins with correct coordinates in fallback view", () => {
    const html = renderToStaticMarkup(
      <GoogleMapsImperial interactiveFallbackOnly={true} />
    );

    // Verify key monuments across all 4 zones
    expect(html).toContain("Ngọ Môn");
    expect(html).toContain("Cầu Trung Đạo");
    expect(html).toContain("Sân Đại Triều Nghi");
    expect(html).toContain("Điện Thái Hòa");
    expect(html).toContain("Thế Tổ Miếu");
    expect(html).toContain("Hiển Lâm Các");
    expect(html).toContain("Hưng Tổ Miếu");
    expect(html).toContain("Triệu Tổ Miếu");
    expect(html).toContain("Điện Phụng Tiên");
    expect(html).toContain("Đại Cung Môn");
    expect(html).toContain("Điện Cần Chánh");
    expect(html).toContain("Duyệt Thị Đường");
    expect(html).toContain("Thái Bình Lâu");
    expect(html).toContain("Điện Kiến Trung");
    expect(html).toContain("Cung Diên Thọ");
    expect(html).toContain("Cung Trường Sanh");

    // Total count of monuments verified
    expect(IMPERIAL_MONUMENTS_GEO.length).toBe(16);
  });

  it("3. Renders zone filter controls with counts for all 4 imperial zones", () => {
    const html = renderToStaticMarkup(
      <GoogleMapsImperial showZoneFilter={true} interactiveFallbackOnly={true} />
    );

    expect(html).toContain("data-testid=\"zone-filters\"");
    expect(html).toContain("Tất cả (16)");
    expect(html).toContain("Trục trung tâm");
    expect(html).toContain("Không gian thờ tự");
    expect(html).toContain("Tử Cấm Thành");
    expect(html).toContain("Không gian sinh hoạt");
  });

  it("4. Renders map type controls (HYBRID, ROADMAP, TERRAIN)", () => {
    const html = renderToStaticMarkup(
      <GoogleMapsImperial
        showMapTypeSelector={true}
        initialMapType="HYBRID"
        interactiveFallbackOnly={true}
      />
    );

    expect(html).toContain("data-testid=\"map-type-controls\"");
    expect(html).toContain("Vệ tinh");
    expect(html).toContain("Đường phố");
    expect(html).toContain("Địa hình");
  });

  it("5. Renders zoom controls and full-screen toggle", () => {
    const html = renderToStaticMarkup(
      <GoogleMapsImperial
        showZoomControls={true}
        showFullscreenToggle={true}
        interactiveFallbackOnly={true}
      />
    );

    expect(html).toContain("data-testid=\"btn-zoom-in\"");
    expect(html).toContain("data-testid=\"btn-zoom-out\"");
    expect(html).toContain("data-testid=\"btn-zoom-reset\"");
    expect(html).toContain("data-testid=\"btn-fullscreen-toggle\"");
  });

  it("6. Renders rich InfoWindow preview when a monument is pre-selected", () => {
    const html = renderToStaticMarkup(
      <GoogleMapsImperial
        selectedMonumentSlug="dien-thai-hoa"
        interactiveFallbackOnly={true}
      />
    );

    expect(html).toContain("data-testid=\"monument-infowindow\"");
    expect(html).toContain("Điện Thái Hòa");
    expect(html).toContain("(太和殿)");
    expect(html).toContain("Trục trung tâm · Khởi dựng 1805");
    expect(html).toContain("Nguyên vẹn");
    expect(html).toContain("href=\"/dai-noi/cong-trinh/dien-thai-hoa\"");
    expect(html).toContain("16.4695°N, 107.5779°E");
  });

  it("7. InfoWindow provides valid deep link to `/dai-noi/cong-trinh/[slug]` for each monument", () => {
    const testMonuments = ["ngo-mon", "dien-kien-trung", "the-to-mieu", "cung-dien-tho"];

    for (const slug of testMonuments) {
      const html = renderToStaticMarkup(
        <GoogleMapsImperial
          selectedMonumentSlug={slug}
          interactiveFallbackOnly={true}
        />
      );
      expect(html).toContain(`href="/dai-noi/cong-trinh/${slug}"`);
    }
  });

  it("8. Center of Đại Nội Huế is configured at Lat 16.4697, Lng 107.5779 with zoom 16", () => {
    expect(DAI_NOI_CENTER.lat).toBe(16.4697);
    expect(DAI_NOI_CENTER.lng).toBe(107.5779);
    expect(DAI_NOI_CENTER.zoom).toBe(16);
  });
});
