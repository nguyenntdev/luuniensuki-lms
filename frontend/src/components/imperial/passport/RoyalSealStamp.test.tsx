import React from "react";
import { describe, it, expect } from "vitest";
import { renderToStaticMarkup } from "react-dom/server";
import { RoyalSealStamp } from "./RoyalSealStamp";
import {
  MONUMENT_SEALS_CATALOG,
  ZONE_ROYAL_SEALS_CATALOG,
  GRAND_ROYAL_SEAL,
  getMonumentSeal,
  getZoneRoyalSeal,
  getGrandRoyalSeal,
} from "@/lib/imperial/passport-types";

describe("RoyalSealStamp Component (RoyalSealStamp.tsx)", () => {
  it("renders locked state with faint watermark style and grayscale filter", () => {
    const html = renderToStaticMarkup(
      <RoyalSealStamp monumentSlug="ngo-mon" status="locked" size="md" />,
    );

    expect(html).toContain("royal-seal-container");
    expect(html).toContain("grayscale(100%) opacity(0.32)");
    expect(html).toContain("Ngọ Môn Chi Ấn");
    expect(html).toContain("午");
    expect(html).toContain("門");
  });

  it("renders unlocked state with cinnabar vermilion ink and patina filter", () => {
    const html = renderToStaticMarkup(
      <RoyalSealStamp
        monumentSlug="dien-thai-hoa"
        status="unlocked"
        size="lg"
        showLabel={true}
        showDate={true}
      />,
    );

    expect(html).toContain("Thái Hòa Điện Khảo Ký");
    expect(html).toContain("太");
    expect(html).toContain("和");
    expect(html).toContain("Điện Thái Hòa");
    expect(html).toContain("#A62B2B");
  });

  it("renders all 16 monument seals accurately without errors", () => {
    MONUMENT_SEALS_CATALOG.forEach((seal) => {
      const html = renderToStaticMarkup(
        <RoyalSealStamp seal={seal} status="unlocked" size="sm" showLabel={true} />,
      );

      expect(html).toContain(seal.monumentNameVi);
      expect(html).toContain(seal.sealTextQuocNgu);
      seal.sealScriptCharacters.forEach((char) => {
        expect(html).toContain(char);
      });
    });
  });

  it("supports different frame geometries (square, circle, octagon, arch)", () => {
    // Circle: Cầu Trung Đạo
    const htmlCircle = renderToStaticMarkup(
      <RoyalSealStamp monumentSlug="cau-trung-dao" status="unlocked" />,
    );
    expect(htmlCircle).toContain("seal-frame-circle");

    // Octagon: Sân Đại Triều Nghi
    const htmlOctagon = renderToStaticMarkup(
      <RoyalSealStamp monumentSlug="san-dai-trieu-nghi" status="unlocked" />,
    );
    expect(htmlOctagon).toContain("seal-frame-octagon");

    // Arch: Hiển Lâm Các
    const htmlArch = renderToStaticMarkup(
      <RoyalSealStamp monumentSlug="hien-lam-cac" status="unlocked" />,
    );
    expect(htmlArch).toContain("seal-frame-arch");

    // Square: Ngọ Môn
    const htmlSquare = renderToStaticMarkup(
      <RoyalSealStamp monumentSlug="ngo-mon" status="unlocked" />,
    );
    expect(htmlSquare).toContain("seal-frame-square");
  });

  it("renders unique royal seals for completed zones (Kim Bảo and Ngự Tỷ motifs)", () => {
    // 1. Trục trung tâm: Kim Bảo "Hoàng Đế Chi Bảo"
    const htmlCentral = renderToStaticMarkup(
      <RoyalSealStamp zoneSlug="central-ceremonial-axis" status="unlocked" size="lg" showLabel={true} />,
    );
    expect(htmlCentral).toContain("Hoàng Đế Chi Bảo");
    expect(htmlCentral).toContain("emblem-kim-bao-central");
    expect(htmlCentral).toContain("皇");
    expect(htmlCentral).toContain("帝");
    expect(htmlCentral).toContain("之");
    expect(htmlCentral).toContain("寶");

    // 2. Không gian thờ tự: Ngự Tỷ "Tôn Miếu Ngự Tỷ"
    const htmlWorship = renderToStaticMarkup(
      <RoyalSealStamp zoneSlug="ancestral-worship-space" status="unlocked" size="lg" showLabel={true} />,
    );
    expect(htmlWorship).toContain("Tôn Miếu Ngự Tỷ");
    expect(htmlWorship).toContain("emblem-ngu-ty-worship");
    expect(htmlWorship).toContain("宗");
    expect(htmlWorship).toContain("廟");
    expect(htmlWorship).toContain("璽");

    // 3. Tử Cấm Thành: Kim Bảo "Ngự Tiền Chi Bảo"
    const htmlForbidden = renderToStaticMarkup(
      <RoyalSealStamp zoneSlug="purple-forbidden-city" status="unlocked" size="lg" showLabel={true} />,
    );
    expect(htmlForbidden).toContain("Ngự Tiền Chi Bảo");
    expect(htmlForbidden).toContain("emblem-kim-bao-forbidden");
    expect(htmlForbidden).toContain("御");
    expect(htmlForbidden).toContain("前");
    expect(htmlForbidden).toContain("寶");

    // 4. Không gian sinh hoạt: Ngự Tỷ "Diên Thọ Ngự Tỷ"
    const htmlLiving = renderToStaticMarkup(
      <RoyalSealStamp zoneSlug="royal-living-gardens" status="unlocked" size="lg" showLabel={true} />,
    );
    expect(htmlLiving).toContain("Diên Thọ Ngự Tỷ");
    expect(htmlLiving).toContain("emblem-ngu-ty-living");
    expect(htmlLiving).toContain("延");
    expect(htmlLiving).toContain("壽");
    expect(htmlLiving).toContain("璽");
  });

  it("renders Grand Imperial Seal (Đại Nam Hoàng Đế Chi Bảo) when isGrandSeal is true", () => {
    const htmlGrand = renderToStaticMarkup(
      <RoyalSealStamp isGrandSeal={true} status="unlocked" size="xl" showLabel={true} />,
    );
    expect(htmlGrand).toContain("Đại Nam Hoàng Đế Chi Bảo");
    expect(htmlGrand).toContain("emblem-grand-master-kim-bao");
    expect(htmlGrand).toContain("大");
    expect(htmlGrand).toContain("南");
    expect(htmlGrand).toContain("皇");
    expect(htmlGrand).toContain("帝");
    expect(htmlGrand).toContain("之");
    expect(htmlGrand).toContain("寶");
  });

  it("renders fallback message gracefully if monument slug is not found", () => {
    const html = renderToStaticMarkup(
      <RoyalSealStamp monumentSlug="non-existent-site" />,
    );
    expect(html).toContain("[Thiếu ấn triện]");
  });
});
