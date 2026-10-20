import { describe, it, expect } from "vitest";
import {
  UV_PRECISION,
  MIN_ZOOM,
  MAX_ZOOM,
  roundToPrecision,
  roundUV,
  clampUV,
  isUVInBounds,
  areUVEqual,
  clampZoom,
  uvToScreen,
  screenToUV,
  viewportPointerToUV,
  calculateFitTransform,
  getViewportBounds,
  isPointerInBounds,
  clampPan,
  type AffineMatrix2D,
} from "./coordinate-utils";
import type { ViewportTransform, UVCoordinate } from "./map-types";

describe("coordinate-utils", () => {
  const intrinsicWidth = 4096;
  const intrinsicHeight = 3072;

  describe("Precision rounding & clamping", () => {
    it("rounds numbers and UV coordinates to 7 decimal places by default", () => {
      expect(roundToPrecision(0.123456789)).toBe(0.1234568);
      expect(roundToPrecision(0.123456711)).toBe(0.1234567);
      expect(roundToPrecision(0.5)).toBe(0.5);

      const rounded = roundUV({
        u: 0.321456789,
        v: 0.987654321,
      });
      expect(rounded).toEqual({
        u: 0.3214568,
        v: 0.9876543,
      });
    });

    it("clamps UV coordinates strictly into [0.0, 1.0]", () => {
      expect(clampUV({ u: -0.15, v: 0.5 })).toEqual({ u: 0, v: 0.5 });
      expect(clampUV({ u: 1.25, v: -0.05 })).toEqual({ u: 1, v: 0 });
      expect(clampUV({ u: 0.333333333, v: 0.666666666 })).toEqual({
        u: 0.3333333,
        v: 0.6666667,
      });
    });

    it("checks UV bounds correctly", () => {
      expect(isUVInBounds({ u: 0, v: 0 })).toBe(true);
      expect(isUVInBounds({ u: 1, v: 1 })).toBe(true);
      expect(isUVInBounds({ u: 0.5, v: 0.5 })).toBe(true);
      expect(isUVInBounds({ u: -0.0001, v: 0.5 })).toBe(false);
      expect(isUVInBounds({ u: 0.5, v: 1.0001 })).toBe(false);
      expect(isUVInBounds({ u: NaN, v: 0.5 })).toBe(false);
      expect(isUVInBounds({ u: 0.5, v: Infinity })).toBe(false);
    });

    it("evaluates UV equality within tolerance", () => {
      const a: UVCoordinate = { u: 0.3214567, v: 0.4567891 };
      const b: UVCoordinate = { u: 0.32145670001, v: 0.45678910001 };
      const c: UVCoordinate = { u: 0.32146, v: 0.45678 };

      expect(areUVEqual(a, b)).toBe(true);
      expect(areUVEqual(a, c)).toBe(false);
    });
  });

  describe("Mathematical Inversion Property (screenToUV(uvToScreen(uv)) === uv)", () => {
    const testCases: UVCoordinate[] = [
      { u: 0, v: 0 },
      { u: 1, v: 1 },
      { u: 0.5, v: 0.5 },
      { u: 0.3214567, v: 0.6543219 }, // Ngọ Môn sample
      { u: 0.1234567, v: 0.8765432 },
      { u: 0.9999999, v: 0.0000001 },
    ];

    const transforms: ViewportTransform[] = [
      // Standard 1:1 view
      { scale: 1, translateX: 0, translateY: 0 },
      // Zoomed in with translation
      { scale: 2.5, translateX: 150, translateY: -80 },
      // Zoomed out with translation
      { scale: 0.75, translateX: -40, translateY: 60 },
      // With letterbox fit offsets
      {
        scale: 1.8,
        translateX: 120,
        translateY: -50,
        offsetX: 45,
        offsetY: 25,
        fittedWidth: 1920,
        fittedHeight: 1080,
      },
    ];

    testCases.forEach((uv) => {
      transforms.forEach((transform, idx) => {
        it(`preserves exact UV coordinates (${uv.u}, ${uv.v}) under transform #${idx + 1}`, () => {
          const screen = uvToScreen(uv, transform, intrinsicWidth, intrinsicHeight);
          const inverted = screenToUV(screen, transform, intrinsicWidth, intrinsicHeight);

          expect(inverted).not.toBeNull();
          expect(inverted!.u).toBe(uv.u);
          expect(inverted!.v).toBe(uv.v);
        });
      });
    });
  });

  describe("Invariant positioning across zoom scales and pan offsets", () => {
    it("maintains the same UV anchor regardless of scale changes", () => {
      const monumentUV: UVCoordinate = { u: 0.4258901, v: 0.5123456 };

      const t1: ViewportTransform = { scale: 1.0, translateX: 0, translateY: 0 };
      const t2: ViewportTransform = { scale: 3.2, translateX: -600, translateY: -400 };

      const screen1 = uvToScreen(monumentUV, t1, intrinsicWidth, intrinsicHeight);
      const screen2 = uvToScreen(monumentUV, t2, intrinsicWidth, intrinsicHeight);

      // Screen positions are physically different in pixels:
      expect(screen1.x).not.toBe(screen2.x);
      expect(screen1.y).not.toBe(screen2.y);

      // But both invert back to the identical canonical UV anchor:
      const inv1 = screenToUV(screen1, t1, intrinsicWidth, intrinsicHeight);
      const inv2 = screenToUV(screen2, t2, intrinsicWidth, intrinsicHeight);

      expect(inv1).toEqual(monumentUV);
      expect(inv2).toEqual(monumentUV);
    });

    it("correctly tracks image pixel coordinates through scale and translation", () => {
      const uv: UVCoordinate = { u: 0.25, v: 0.75 };
      const transform: ViewportTransform = {
        scale: 2.0,
        translateX: 100,
        translateY: 50,
        offsetX: 0,
        offsetY: 0,
        fittedWidth: intrinsicWidth,
        fittedHeight: intrinsicHeight,
      };

      const screen = uvToScreen(uv, transform, intrinsicWidth, intrinsicHeight);

      // Expected x = 100 + 2.0 * (0 + 0.25 * 4096) = 100 + 2048 = 2148
      // Expected y = 50 + 2.0 * (0 + 0.75 * 3072) = 50 + 4608 = 4658
      expect(screen.x).toBe(2148);
      expect(screen.y).toBe(4658);

      const recovered = screenToUV(screen, transform, intrinsicWidth, intrinsicHeight);
      expect(recovered).toEqual(uv);
    });
  });

  describe("Rejection of out-of-bounds letterbox clicks", () => {
    const transform: ViewportTransform = {
      scale: 1.0,
      translateX: 100,
      translateY: 80,
      offsetX: 50,
      offsetY: 40,
      fittedWidth: 1000,
      fittedHeight: 800,
    };

    // Valid screen bounds:
    // x: [100 + 1*(50) = 150, 150 + 1000 = 1150]
    // y: [80 + 1*(40) = 120, 120 + 800 = 920]

    it("rejects clicks strictly outside the left boundary (letterbox)", () => {
      const outLeft = { x: 149.9, y: 500 };
      expect(screenToUV(outLeft, transform, intrinsicWidth, intrinsicHeight)).toBeNull();
    });

    it("rejects clicks strictly outside the right boundary (letterbox)", () => {
      const outRight = { x: 1150.1, y: 500 };
      expect(screenToUV(outRight, transform, intrinsicWidth, intrinsicHeight)).toBeNull();
    });

    it("rejects clicks strictly above the top boundary (letterbox)", () => {
      const outTop = { x: 500, y: 119.9 };
      expect(screenToUV(outTop, transform, intrinsicWidth, intrinsicHeight)).toBeNull();
    });

    it("rejects clicks strictly below the bottom boundary (letterbox)", () => {
      const outBottom = { x: 500, y: 920.1 };
      expect(screenToUV(outBottom, transform, intrinsicWidth, intrinsicHeight)).toBeNull();
    });

    it("accepts edge clicks on the exact boundary [0.0 and 1.0]", () => {
      const topLeft = { x: 150, y: 120 };
      const bottomRight = { x: 1150, y: 920 };

      expect(screenToUV(topLeft, transform, intrinsicWidth, intrinsicHeight)).toEqual({
        u: 0,
        v: 0,
      });
      expect(screenToUV(bottomRight, transform, intrinsicWidth, intrinsicHeight)).toEqual({
        u: 1,
        v: 1,
      });
    });

    it("rejects invalid scale or dimensions", () => {
      expect(
        screenToUV({ x: 100, y: 100 }, { scale: 0, translateX: 0, translateY: 0 }, 100, 100),
      ).toBeNull();
      expect(
        screenToUV({ x: 100, y: 100 }, { scale: -1, translateX: 0, translateY: 0 }, 100, 100),
      ).toBeNull();
      expect(
        screenToUV({ x: 100, y: 100 }, { scale: 1, translateX: 0, translateY: 0 }, 0, 100),
      ).toBeNull();
    });
  });

  describe("viewportPointerToUV with Matrix transformation", () => {
    it("inverts pointer coordinates using a 2D affine matrix", () => {
      const scale = 2.0;
      const tx = 100;
      const ty = 50;

      // Forward transform: x_screen = scale * x_img + tx
      // Inverse transform: x_img = (x_screen - tx) / scale
      // Affine components: a = 1/scale, c = 0, e = -tx/scale
      const invMatrix: AffineMatrix2D = {
        a: 1 / scale,
        b: 0,
        c: 0,
        d: 1 / scale,
        e: -tx / scale,
        f: -ty / scale,
      };

      const originalUV: UVCoordinate = { u: 0.35, v: 0.65 };
      const screenX = scale * (originalUV.u * intrinsicWidth) + tx;
      const screenY = scale * (originalUV.v * intrinsicHeight) + ty;

      const recovered = viewportPointerToUV(
        { x: screenX, y: screenY },
        invMatrix,
        intrinsicWidth,
        intrinsicHeight,
      );

      expect(recovered).not.toBeNull();
      expect(recovered!.u).toBe(originalUV.u);
      expect(recovered!.v).toBe(originalUV.v);
    });

    it("rejects out-of-bounds pointer clicks with matrix", () => {
      const invMatrix: AffineMatrix2D = {
        a: 1,
        b: 0,
        c: 0,
        d: 1,
        e: 0,
        f: 0,
      };

      // Pointer x is -10 (outside left)
      expect(
        viewportPointerToUV({ x: -10, y: 100 }, invMatrix, intrinsicWidth, intrinsicHeight),
      ).toBeNull();

      // Pointer x exceeds width
      expect(
        viewportPointerToUV(
          { x: intrinsicWidth + 10, y: 100 },
          invMatrix,
          intrinsicWidth,
          intrinsicHeight,
        ),
      ).toBeNull();
    });

    it("supports transformPoint method if present", () => {
      const mockTransformable = {
        transformPoint: (p: { x: number; y: number }) => ({
          x: p.x / 2,
          y: p.y / 2,
        }),
      };

      const recovered = viewportPointerToUV(
        { x: intrinsicWidth, y: intrinsicHeight },
        mockTransformable,
        intrinsicWidth,
        intrinsicHeight,
      );

      expect(recovered).toEqual({ u: 0.5, v: 0.5 });
    });
  });

  describe("Zoom limits & Viewport calculations", () => {
    it("enforces zoom scaling limits", () => {
      expect(clampZoom(0.1)).toBe(MIN_ZOOM);
      expect(clampZoom(10.0)).toBe(MAX_ZOOM);
      expect(clampZoom(2.5)).toBe(2.5);
      expect(clampZoom(NaN)).toBe(1.0);
    });

    it("calculates fit transform for letterbox containment", () => {
      const containerW = 1920;
      const containerH = 1080;
      const imgW = 4096;
      const imgH = 2048; // aspect ratio 2:1

      const fit = calculateFitTransform(containerW, containerH, imgW, imgH);
      expect(fit.scale).toBe(1);
      // scale = min(1920/4096 = 0.46875, 1080/2048 = 0.52734375) => 0.46875
      expect(fit.fittedWidth).toBe(1920);
      expect(fit.fittedHeight).toBe(2048 * 0.46875); // 960
      expect(fit.offsetX).toBe(0);
      expect(fit.offsetY).toBe((1080 - 960) / 2); // 60
    });

    it("calculates viewport bounding box and pointer hit testing", () => {
      const transform: ViewportTransform = {
        scale: 2.0,
        translateX: 50,
        translateY: 30,
        offsetX: 10,
        offsetY: 20,
        fittedWidth: 800,
        fittedHeight: 600,
      };

      const bounds = getViewportBounds(transform, intrinsicWidth, intrinsicHeight);
      expect(bounds.left).toBe(50 + 2 * 10); // 70
      expect(bounds.top).toBe(30 + 2 * 20); // 70
      expect(bounds.width).toBe(2 * 800); // 1600
      expect(bounds.height).toBe(2 * 600); // 1200
      expect(bounds.right).toBe(70 + 1600); // 1670
      expect(bounds.bottom).toBe(70 + 1200); // 1270

      expect(isPointerInBounds({ x: 100, y: 100 }, transform, intrinsicWidth, intrinsicHeight)).toBe(
        true,
      );
      expect(isPointerInBounds({ x: 50, y: 50 }, transform, intrinsicWidth, intrinsicHeight)).toBe(
        false,
      );
    });

    it("clamps pan translation to prevent losing map off-screen", () => {
      const transform: ViewportTransform = {
        scale: 1.0,
        translateX: 0,
        translateY: 0,
        fittedWidth: 1000,
        fittedHeight: 800,
      };

      // Massive pan to the right
      const clamped = clampPan(5000, -5000, transform, 1000, 800, 0.2);
      expect(clamped.translateX).toBeLessThan(5000);
      expect(clamped.translateY).toBeGreaterThan(-5000);
    });
  });
});
