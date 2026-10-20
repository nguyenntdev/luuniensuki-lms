import { describe, it, expect } from "vitest";
import {
  degToRad,
  radToDeg,
  normalizeAngle,
  clampPitch,
  sphericalToCartesian,
  cartesianToSpherical,
  uvToSpherical,
  sphericalToUV,
  cartesianToScreen,
  DEFAULT_SPHERE_RADIUS,
} from "./panorama-math";

describe("panorama-math unit tests", () => {
  describe("degToRad and radToDeg", () => {
    it("converts 0, 90, 180, 360 degrees to radians accurately", () => {
      expect(degToRad(0)).toBe(0);
      expect(degToRad(180)).toBeCloseTo(Math.PI, 6);
      expect(degToRad(90)).toBeCloseTo(Math.PI / 2, 6);
      expect(degToRad(360)).toBeCloseTo(2 * Math.PI, 6);
    });

    it("converts radians back to degrees accurately", () => {
      expect(radToDeg(0)).toBe(0);
      expect(radToDeg(Math.PI)).toBeCloseTo(180, 6);
      expect(radToDeg(Math.PI / 2)).toBeCloseTo(90, 6);
      expect(radToDeg(2 * Math.PI)).toBeCloseTo(360, 6);
    });
  });

  describe("normalizeAngle", () => {
    it("preserves angles already within [-180, 180]", () => {
      expect(normalizeAngle(0)).toBe(0);
      expect(normalizeAngle(45)).toBe(45);
      expect(normalizeAngle(-45)).toBe(-45);
      expect(normalizeAngle(90)).toBe(90);
      expect(normalizeAngle(-90)).toBe(-90);
      expect(normalizeAngle(180)).toBe(180);
      expect(normalizeAngle(-180)).toBe(-180);
    });

    it("wraps angles outside [-180, 180] symmetrically", () => {
      expect(normalizeAngle(190)).toBe(-170);
      expect(normalizeAngle(-190)).toBe(170);
      expect(normalizeAngle(360)).toBe(0);
      expect(normalizeAngle(450)).toBe(90);
      expect(normalizeAngle(-450)).toBe(-90);
      expect(normalizeAngle(540)).toBe(180);
      expect(normalizeAngle(-540)).toBe(-180);
      expect(normalizeAngle(720)).toBe(0);
    });

    it("handles non-finite inputs safely", () => {
      expect(normalizeAngle(NaN)).toBe(0);
      expect(normalizeAngle(Infinity)).toBe(0);
    });

    it("supports custom min and max bounds", () => {
      expect(normalizeAngle(270, 0, 360)).toBe(270);
      expect(normalizeAngle(-90, 0, 360)).toBe(270);
      expect(normalizeAngle(400, 0, 360)).toBe(40);
    });
  });

  describe("clampPitch", () => {
    it("preserves pitches within safe bounds", () => {
      expect(clampPitch(0)).toBe(0);
      expect(clampPitch(45)).toBe(45);
      expect(clampPitch(-45)).toBe(-45);
      expect(clampPitch(85)).toBe(85);
      expect(clampPitch(-85)).toBe(-85);
    });

    it("clamps extreme pitches to avoid polar gimbal lock", () => {
      expect(clampPitch(89)).toBe(85);
      expect(clampPitch(90)).toBe(85);
      expect(clampPitch(120)).toBe(85);
      expect(clampPitch(-90)).toBe(-85);
      expect(clampPitch(-100)).toBe(-85);
    });

    it("handles custom limits", () => {
      expect(clampPitch(89, -90, 90)).toBe(89);
      expect(clampPitch(95, -90, 90)).toBe(90);
      expect(clampPitch(-95, -90, 90)).toBe(-90);
    });

    it("handles non-finite values safely", () => {
      expect(clampPitch(NaN)).toBe(0);
      expect(clampPitch(Infinity)).toBe(0);
    });
  });

  describe("sphericalToCartesian", () => {
    const R = DEFAULT_SPHERE_RADIUS;

    it("projects yaw=0, pitch=0 to forward direction (0, 0, -R)", () => {
      const pos = sphericalToCartesian(0, 0, R);
      expect(pos.x).toBeCloseTo(0, 4);
      expect(pos.y).toBeCloseTo(0, 4);
      expect(pos.z).toBeCloseTo(-R, 4);
    });

    it("projects yaw=90, pitch=0 to right direction (R, 0, 0)", () => {
      const pos = sphericalToCartesian(90, 0, R);
      expect(pos.x).toBeCloseTo(R, 4);
      expect(pos.y).toBeCloseTo(0, 4);
      expect(pos.z).toBeCloseTo(0, 4);
    });

    it("projects yaw=-90, pitch=0 to left direction (-R, 0, 0)", () => {
      const pos = sphericalToCartesian(-90, 0, R);
      expect(pos.x).toBeCloseTo(-R, 4);
      expect(pos.y).toBeCloseTo(0, 4);
      expect(pos.z).toBeCloseTo(0, 4);
    });

    it("projects yaw=180, pitch=0 to back direction (0, 0, R)", () => {
      const pos = sphericalToCartesian(180, 0, R);
      expect(pos.x).toBeCloseTo(0, 4);
      expect(pos.y).toBeCloseTo(0, 4);
      expect(pos.z).toBeCloseTo(R, 4);
    });

    it("projects pitch=90 to Zenith (0, R, 0)", () => {
      const pos = sphericalToCartesian(0, 90, R);
      expect(pos.x).toBeCloseTo(0, 4);
      expect(pos.y).toBeCloseTo(R, 4);
      expect(pos.z).toBeCloseTo(0, 4);
    });

    it("projects pitch=-90 to Nadir (0, -R, 0)", () => {
      const pos = sphericalToCartesian(0, -90, R);
      expect(pos.x).toBeCloseTo(0, 4);
      expect(pos.y).toBeCloseTo(-R, 4);
      expect(pos.z).toBeCloseTo(0, 4);
    });

    it("maintains constant spherical radius for arbitrary angles", () => {
      const testAngles = [
        { yaw: 37, pitch: 42 },
        { yaw: -125, pitch: -33 },
        { yaw: 88, pitch: -60 },
        { yaw: -45, pitch: 45 },
      ];

      for (const { yaw, pitch } of testAngles) {
        const p = sphericalToCartesian(yaw, pitch, R);
        const distance = Math.sqrt(p.x * p.x + p.y * p.y + p.z * p.z);
        expect(distance).toBeCloseTo(R, 4);
      }
    });
  });

  describe("Inversion property: cartesianToSpherical(sphericalToCartesian(yaw, pitch))", () => {
    it("recovers yaw and pitch with near-zero error", () => {
      const testCases = [
        { yaw: 0, pitch: 0 },
        { yaw: 90, pitch: 0 },
        { yaw: -90, pitch: 0 },
        { yaw: 180, pitch: 0 },
        { yaw: 45, pitch: 30 },
        { yaw: -120, pitch: -45 },
        { yaw: 75, pitch: -60 },
        { yaw: -160, pitch: 50 },
      ];

      for (const { yaw, pitch } of testCases) {
        const cartesian = sphericalToCartesian(yaw, pitch, 500);
        const spherical = cartesianToSpherical(cartesian.x, cartesian.y, cartesian.z);

        expect(spherical.yaw).toBeCloseTo(yaw, 4);
        expect(spherical.pitch).toBeCloseTo(pitch, 4);
        expect(spherical.radius).toBeCloseTo(500, 4);
      }
    });

    it("handles zero vector safely", () => {
      const zero = cartesianToSpherical(0, 0, 0);
      expect(zero.yaw).toBe(0);
      expect(zero.pitch).toBe(0);
      expect(zero.radius).toBe(0);
    });
  });

  describe("Equirectangular UV conversions", () => {
    it("converts UV to spherical coordinates correctly", () => {
      // Center (0.5, 0.5) is yaw 0, pitch 0
      expect(uvToSpherical(0.5, 0.5)).toEqual({ yaw: 0, pitch: 0 });

      // Top-left (0, 0) is yaw -180, pitch +90
      expect(uvToSpherical(0, 0)).toEqual({ yaw: -180, pitch: 90 });

      // Bottom-right (1, 1) is yaw 180, pitch -90
      expect(uvToSpherical(1, 1)).toEqual({ yaw: 180, pitch: -90 });
    });

    it("converts spherical coordinates to UV correctly", () => {
      expect(sphericalToUV(0, 0)).toEqual({ u: 0.5, v: 0.5 });
      expect(sphericalToUV(-180, 90)).toEqual({ u: 0, v: 0 });
      expect(sphericalToUV(180, -90)).toEqual({ u: 1, v: 1 });
      expect(sphericalToUV(90, 0)).toEqual({ u: 0.75, v: 0.5 });
      expect(sphericalToUV(-90, 0)).toEqual({ u: 0.25, v: 0.5 });
    });

    it("maintains round-trip UV -> Spherical -> UV property", () => {
      const uvs = [
        { u: 0.5, v: 0.5 },
        { u: 0.25, v: 0.5 },
        { u: 0.75, v: 0.5 },
        { u: 0.1, v: 0.3 },
        { u: 0.85, v: 0.7 },
      ];

      for (const uv of uvs) {
        const spherical = uvToSpherical(uv.u, uv.v);
        const roundTrip = sphericalToUV(spherical.yaw, spherical.pitch);
        expect(roundTrip.u).toBeCloseTo(uv.u, 5);
        expect(roundTrip.v).toBeCloseTo(uv.v, 5);
      }
    });
  });

  describe("cartesianToScreen", () => {
    const width = 1000;
    const height = 800;

    it("projects center-forward point to screen center when camera looks forward", () => {
      const mockCamera = {
        project: (v: { x: number; y: number; z: number }) => ({ x: 0, y: 0, z: 0.5 }),
      };

      const screen = cartesianToScreen({ x: 0, y: 0, z: -500 }, mockCamera, width, height);
      expect(screen.isVisible).toBe(true);
      expect(screen.x).toBe(500); // center of width
      expect(screen.y).toBe(400); // center of height
    });

    it("marks points behind the camera as invisible (ndc.z > 1)", () => {
      const mockCamera = {
        project: (v: { x: number; y: number; z: number }) => ({ x: 0, y: 0, z: 1.5 }),
      };

      const screen = cartesianToScreen({ x: 0, y: 0, z: 500 }, mockCamera, width, height);
      expect(screen.isVisible).toBe(false);
    });

    it("projects top-right quadrant correctly", () => {
      const mockCamera = {
        project: (v: { x: number; y: number; z: number }) => ({ x: 0.5, y: 0.5, z: 0.2 }),
      };

      const screen = cartesianToScreen({ x: 100, y: 100, z: -400 }, mockCamera, width, height);
      expect(screen.isVisible).toBe(true);
      expect(screen.x).toBe(750); // 0.75 * 1000
      expect(screen.y).toBe(200); // (1 - 0.75) * 800 = 0.25 * 800
    });

    it("handles zero viewport dimensions gracefully", () => {
      const mockCamera = {
        project: (v: { x: number; y: number; z: number }) => ({ x: 0, y: 0, z: 0 }),
      };

      const screen = cartesianToScreen({ x: 0, y: 0, z: -100 }, mockCamera, 0, 0);
      expect(screen.isVisible).toBe(false);
      expect(screen.x).toBe(0);
      expect(screen.y).toBe(0);
    });
  });
});
