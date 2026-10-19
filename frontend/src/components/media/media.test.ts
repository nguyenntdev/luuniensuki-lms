import { describe, it, expect } from "vitest";
import React from "react";
import { renderToStaticMarkup } from "react-dom/server";
import {
  LicenseBadge,
  resolveLicenseBadgeTier,
  type LicenseBadgeTier,
} from "./LicenseBadge";
import {
  ThreeDFallback,
  type FallbackReason,
} from "./ThreeDFallback";
import {
  SketchfabExhibit,
  APPROVED_SKETCHFAB_MODELS,
  BLOCKED_SKETCHFAB_MODELS,
  REJECTED_SKETCHFAB_MODEL,
  REJECTED_SKETCHFAB_UID,
  CURATED_MODELS,
  isValidSketchfabUid,
} from "./SketchfabExhibit";

describe("LicenseBadge Component & Logic", () => {
  it("resolves tier correctly from license text and flags", () => {
    expect(resolveLicenseBadgeTier(undefined, "CC BY 4.0")).toBe("approved_cc_by");
    expect(resolveLicenseBadgeTier(undefined, "CC-BY")).toBe("approved_cc_by");
    expect(resolveLicenseBadgeTier(undefined, "CC BY-NC-SA 4.0")).toBe("blocked_nc");
    expect(resolveLicenseBadgeTier(undefined, "CC BY-NC")).toBe("blocked_nc");
    expect(resolveLicenseBadgeTier(undefined, "NonCommercial")).toBe("blocked_nc");
    expect(resolveLicenseBadgeTier(undefined, "NoAI Protected")).toBe("blocked_noai");
    expect(resolveLicenseBadgeTier(undefined, undefined, true)).toBe("blocked_noai");
    expect(resolveLicenseBadgeTier(undefined, "Institutional Record")).toBe("institutional_record");
    expect(resolveLicenseBadgeTier(undefined, "Hồ sơ lưu trữ bảo tàng")).toBe("institutional_record");
    expect(resolveLicenseBadgeTier(undefined, "Rejected Inaccurate")).toBe("rejected_inaccurate");
    expect(resolveLicenseBadgeTier(undefined, "NOT STATED")).toBe("review_pending");
    expect(resolveLicenseBadgeTier(undefined, undefined)).toBe("review_pending");
  });

  it("prioritizes explicit tier when passed", () => {
    expect(resolveLicenseBadgeTier("blocked_noai", "CC BY 4.0")).toBe("blocked_noai");
    expect(resolveLicenseBadgeTier("rejected_inaccurate", "CC BY 4.0")).toBe("rejected_inaccurate");
  });

  it("renders accessible CC BY badge with emerald styling", () => {
    const html = renderToStaticMarkup(
      React.createElement(LicenseBadge, { tier: "approved_cc_by", licenseText: "CC BY 4.0" })
    );
    expect(html).toContain('role="status"');
    expect(html).toContain("CC BY 4.0");
    expect(html).toContain("bg-emerald-50");
    expect(html).toContain("text-emerald-700");
  });

  it("renders accessible NoAI badge with purple styling", () => {
    const html = renderToStaticMarkup(
      React.createElement(LicenseBadge, { tier: "blocked_noai", licenseText: "NoAI Protected" })
    );
    expect(html).toContain("NoAI Protected");
    expect(html).toContain("bg-purple-50");
    expect(html).toContain("text-purple-700");
  });

  it("renders accessible CC BY-NC-SA badge with amber styling", () => {
    const html = renderToStaticMarkup(
      React.createElement(LicenseBadge, { tier: "blocked_nc", licenseText: "CC BY-NC-SA" })
    );
    expect(html).toContain("CC BY-NC-SA");
    expect(html).toContain("bg-amber-50");
    expect(html).toContain("text-amber-700");
  });

  it("renders accessible Institutional Record badge with blue styling", () => {
    const html = renderToStaticMarkup(
      React.createElement(LicenseBadge, { tier: "institutional_record" })
    );
    expect(html).toContain("Institutional Record");
    expect(html).toContain("bg-blue-50");
    expect(html).toContain("text-blue-700");
  });

  it("renders description when showDescription is enabled", () => {
    const html = renderToStaticMarkup(
      React.createElement(LicenseBadge, {
        tier: "approved_cc_by",
        showDescription: true,
      })
    );
    expect(html).toContain("Được phép nhúng với quyền ghi nhận tác giả");
  });
});

describe("ThreeDFallback Component", () => {
  it("renders 16:9 container and archival image attributes", () => {
    const html = renderToStaticMarkup(
      React.createElement(ThreeDFallback, {
        modelId: "SF-009",
        modelTitle: "Tomb of Tu Duc",
        siteName: "Lăng Tự Đức",
        reason: "webgl_unsupported",
      })
    );
    expect(html).toContain("aspect-video");
    expect(html).toContain("img");
    expect(html).toContain("Lăng Tự Đức");
    expect(html).toContain("Tomb of Tu Duc");
    expect(html).toContain("Open Heritage 3D");
  });

  it("enforces negative guardrail for SF-020: warns inaccurate and omits external 3D link", () => {
    const html = renderToStaticMarkup(
      React.createElement(ThreeDFallback, {
        modelId: "SF-020",
        sketchfabUrl: "https://sketchfab.com/3d-models/ai-noi-hue-van-hoa-viet-nam-84a8ab573293497ab0d4f97b4650bb55",
      })
    );
    expect(html).toContain("SF-020");
    expect(html).toContain("không bảo đảm tính xác thực lịch sử");
    expect(html).toContain("loại trừ vĩnh viễn");
    // Must NOT show link to explore as valid 3D model
    expect(html).not.toContain("Xem trên Sketchfab");
  });

  it("renders CC BY-NC-SA restriction notice for SF-010 with research link", () => {
    const html = renderToStaticMarkup(
      React.createElement(ThreeDFallback, {
        modelId: "SF-010",
        sketchfabUrl: "https://sketchfab.com/3d-models/tomb-of-tu-duc-978f8e7afd9a4aebb738339c9f0087a0",
      })
    );
    expect(html).toContain("SF-010");
    expect(html).toContain("phi thương mại (CC BY-NC-SA)");
    expect(html).toContain("Xem trên Sketchfab");
    expect(html).toContain('target="_blank"');
    expect(html).toContain('rel="noopener noreferrer"');
  });

  it("renders NoAI restriction notice for SF-017", () => {
    const html = renderToStaticMarkup(
      React.createElement(ThreeDFallback, {
        modelId: "SF-017",
        sketchfabUrl: "https://sketchfab.com/3d-models/an-dinh-palace-photogrammetry-lidar-dca05e147d79420eb3696eefcf8e1f19",
      })
    );
    expect(html).toContain("SF-017");
    expect(html).toContain("NoAI");
    expect(html).toContain("Nghiêm cấm thu thập làm dữ liệu huấn luyện AI");
  });

  it("renders outbound citation link with DOI when available", () => {
    const html = renderToStaticMarkup(
      React.createElement(ThreeDFallback, {
        modelId: "SF-016",
      })
    );
    expect(html).toContain("https://doi.org/10.26301/4z5b-vz23");
    expect(html).toContain("DOI: 10.26301/4z5b-vz23");
  });
});

describe("SketchfabExhibit Component & Guardrails", () => {
  it("maintains approved model list matching specification", () => {
    expect(APPROVED_SKETCHFAB_MODELS).toEqual(["SF-009", "SF-011", "SF-016"]);
    expect(BLOCKED_SKETCHFAB_MODELS).toEqual(["SF-010", "SF-017"]);
    expect(REJECTED_SKETCHFAB_MODEL).toBe("SF-020");
    expect(REJECTED_SKETCHFAB_UID).toBe("84a8ab573293497ab0d4f97b4650bb55");
  });

  it("validates 32-character hexadecimal UIDs strictly", () => {
    expect(isValidSketchfabUid("77728a86ad1d4964824b63844d50bfe7")).toBe(true);
    expect(isValidSketchfabUid("B5D78ECD5E62483192D7CCD193BC063B")).toBe(true);
    expect(isValidSketchfabUid("b6143a3e8ff1446aa0c6d5694d08f9e7")).toBe(true);
    expect(isValidSketchfabUid("84a8ab573293497ab0d4f97b4650bb55")).toBe(true);

    // Invalid UIDs
    expect(isValidSketchfabUid("")).toBe(false);
    expect(isValidSketchfabUid(null)).toBe(false);
    expect(isValidSketchfabUid(undefined)).toBe(false);
    expect(isValidSketchfabUid("short-uid")).toBe(false);
    expect(isValidSketchfabUid("77728a86ad1d4964824b63844d50bfe7-extra")).toBe(false);
    expect(isValidSketchfabUid("zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz")).toBe(false);
  });

  it("contains complete metadata for approved models in curated registry", () => {
    for (const modelId of APPROVED_SKETCHFAB_MODELS) {
      const model = CURATED_MODELS[modelId];
      expect(model).toBeDefined();
      expect(isValidSketchfabUid(model.modelUid)).toBe(true);
      expect(model.license).toBe("CC BY 4.0");
      expect(model.doi).toBeDefined();
      expect(model.creatorName).toBeDefined();
      expect(model.thumbnailUrl).toBeDefined();
    }
  });

  it("enforces negative guardrail: rejects SF-020 permanently and falls back to 2D", () => {
    const htmlById = renderToStaticMarkup(
      React.createElement(SketchfabExhibit, { modelId: "SF-020" })
    );
    expect(htmlById).not.toContain("<iframe");
    expect(htmlById).toContain("SF-020");
    expect(htmlById).toContain("loại trừ vĩnh viễn");

    const htmlByUid = renderToStaticMarkup(
      React.createElement(SketchfabExhibit, { modelUid: REJECTED_SKETCHFAB_UID })
    );
    expect(htmlByUid).not.toContain("<iframe");
    expect(htmlByUid).toContain("SF-020");
    expect(htmlByUid).toContain("loại trừ vĩnh viễn");
  });

  it("blocks SF-010 from embedding and falls back to 2D", () => {
    const html = renderToStaticMarkup(
      React.createElement(SketchfabExhibit, { modelId: "SF-010" })
    );
    expect(html).not.toContain("<iframe");
    expect(html).toContain("SF-010");
    expect(html).toContain("phi thương mại (CC BY-NC-SA)");
  });

  it("blocks SF-017 from embedding and falls back to 2D", () => {
    const html = renderToStaticMarkup(
      React.createElement(SketchfabExhibit, { modelId: "SF-017" })
    );
    expect(html).not.toContain("<iframe");
    expect(html).toContain("SF-017");
    expect(html).toContain("NoAI");
  });

  it("degrades gracefully to 2D fallback when UID is invalid", () => {
    const html = renderToStaticMarkup(
      React.createElement(SketchfabExhibit, {
        modelUid: "invalid-uid-not-32-chars",
        modelTitle: "Test Model",
      })
    );
    expect(html).not.toContain("<iframe");
    expect(html).toContain("không hợp lệ");
  });

  it("renders idle preview card with CTA button for approved model SF-009 without mounting iframe", () => {
    const html = renderToStaticMarkup(
      React.createElement(SketchfabExhibit, { modelId: "SF-009" })
    );

    // Initial idle state must NOT render iframe (lazy user-initiated)
    expect(html).not.toContain("<iframe");

    // Must render preview card elements
    expect(html).toContain("Xem mô hình 3D tương tác");
    expect(html).toContain("Tomb of Tu Duc");
    expect(html).toContain("matousekfoto");
    expect(html).toContain("Lăng Tự Đức");
    expect(html).toContain("CC BY 4.0");
    expect(html).toContain("10.26301/n06n-qa49");
    expect(html).toContain("SF-009");
  });

  it("renders idle preview card for approved model SF-011", () => {
    const html = renderToStaticMarkup(
      React.createElement(SketchfabExhibit, { modelId: "SF-011" })
    );
    expect(html).not.toContain("<iframe");
    expect(html).toContain("Xem mô hình 3D tương tác");
    expect(html).toContain("Stele Building (CyArk Dataset)");
    expect(html).toContain("Vasilis Haroupas");
    expect(html).toContain("Bi Đình — Lăng Tự Đức");
  });

  it("renders idle preview card for approved model SF-016", () => {
    const html = renderToStaticMarkup(
      React.createElement(SketchfabExhibit, { modelId: "SF-016" })
    );
    expect(html).not.toContain("<iframe");
    expect(html).toContain("Xem mô hình 3D tương tác");
    expect(html).toContain("An Dinh Palace - Open Heritage 3D");
    expect(html).toContain("Alexei MKLT");
    expect(html).toContain("Cung An Định");
    expect(html).toContain("10.26301/4z5b-vz23");
  });

  it("verifies SF-010 and SF-017 curated entries in CURATED_MODELS map to ThreeDFallback", () => {
    const sf010 = CURATED_MODELS["SF-010"];
    expect(sf010).toBeDefined();
    expect(sf010.license).toContain("NC");

    const sf017 = CURATED_MODELS["SF-017"];
    expect(sf017).toBeDefined();
    expect(sf017.noai).toBe(true);

    const sf020 = CURATED_MODELS["SF-020"];
    expect(sf020).toBeDefined();
    expect(sf020.modelUid).toBe(REJECTED_SKETCHFAB_UID);
  });
});
