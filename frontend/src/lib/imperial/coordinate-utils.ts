/**
 * Mathematical Coordinate Transformation Engine for STTTNNĐ (Lưu Niên — Đại Nội Huế).
 * Handles conversions between:
 * - Normalized UV coordinates on the canonical image plane [0.0 .. 1.0]
 * - Screen coordinates in the viewport
 * - Inverse matrix pointer mapping for pan/zoom layers
 *
 * Implements strict boundary checking, rejection of letterbox clicks,
 * invariant positioning across zoom/pan, and 7-decimal-place precision.
 *
 * Ref: LUU_NIEN_STTTNND_DAI_NOI_MASTER_SPEC_V2_1_INTEGRATED.md (§4.1, §4.2)
 */

import type {
  ScreenCoordinate,
  UVCoordinate,
  ViewportTransform,
} from "./map-types";

export const UV_PRECISION = 7;
export const MIN_ZOOM = 0.5;
export const MAX_ZOOM = 5.0;
export const DEFAULT_ZOOM = 1.0;

/**
 * 2D Affine Matrix representation matching standard DOMMatrix 2D components:
 * [ a  c  e ]
 * [ b  d  f ]
 * [ 0  0  1 ]
 */
export interface AffineMatrix2D {
  a: number;
  b: number;
  c: number;
  d: number;
  e: number;
  f: number;
}

export type MatrixLike =
  | DOMMatrix
  | AffineMatrix2D
  | { transformPoint: (point: ScreenCoordinate) => ScreenCoordinate };

/**
 * Rounds a number to a fixed decimal precision (default 7 places).
 */
export function roundToPrecision(
  value: number,
  decimals: number = UV_PRECISION,
): number {
  if (!Number.isFinite(value)) return 0;
  const factor = 10 ** decimals;
  return Math.round((value + Number.EPSILON) * factor) / factor;
}

/**
 * Rounds UV coordinates to standard precision (7 decimal places).
 */
export function roundUV(
  uv: UVCoordinate,
  decimals: number = UV_PRECISION,
): UVCoordinate {
  return {
    u: roundToPrecision(uv.u, decimals),
    v: roundToPrecision(uv.v, decimals),
  };
}

/**
 * Clamps UV coordinates strictly into the [0.0, 1.0] unit square and rounds to 7 places.
 */
export function clampUV(uv: UVCoordinate): UVCoordinate {
  const clampedU = Math.min(Math.max(uv.u, 0), 1);
  const clampedV = Math.min(Math.max(uv.v, 0), 1);
  return {
    u: roundToPrecision(clampedU),
    v: roundToPrecision(clampedV),
  };
}

/**
 * Checks whether UV coordinate lies strictly within the [0.0, 1.0] normalized area.
 */
export function isUVInBounds(uv: UVCoordinate): boolean {
  return (
    Number.isFinite(uv.u) &&
    Number.isFinite(uv.v) &&
    uv.u >= 0 &&
    uv.u <= 1 &&
    uv.v >= 0 &&
    uv.v <= 1
  );
}

/**
 * Compares two UV coordinates for equality within tolerance (default: 1e-7).
 */
export function areUVEqual(
  a: UVCoordinate,
  b: UVCoordinate,
  epsilon: number = 1e-7,
): boolean {
  return Math.abs(a.u - b.u) <= epsilon && Math.abs(a.v - b.v) <= epsilon;
}

/**
 * Clamps a zoom level within safe bounds.
 */
export function clampZoom(
  scale: number,
  minZoom: number = MIN_ZOOM,
  maxZoom: number = MAX_ZOOM,
): number {
  if (!Number.isFinite(scale)) return DEFAULT_ZOOM;
  return Math.min(Math.max(scale, minZoom), maxZoom);
}

/**
 * Transforms normalized UV coordinate on canonical image plane to screen viewport coordinates.
 *
 * Formula (§4.2):
 * x_screen = tx + s * (ox + u * wfit)
 * y_screen = ty + s * (oy + v * hfit)
 */
export function uvToScreen(
  uv: UVCoordinate,
  transform: ViewportTransform,
  intrinsicWidth: number,
  intrinsicHeight: number,
): ScreenCoordinate {
  const s = transform.scale;
  const tx = transform.translateX;
  const ty = transform.translateY;
  const ox = transform.offsetX ?? 0;
  const oy = transform.offsetY ?? 0;
  const wfit = transform.fittedWidth ?? intrinsicWidth;
  const hfit = transform.fittedHeight ?? intrinsicHeight;

  const x = tx + s * (ox + uv.u * wfit);
  const y = ty + s * (oy + uv.v * hfit);

  return { x, y };
}

/**
 * Transforms screen viewport coordinates back to normalized UV coordinate on the image.
 * Returns `null` if the click/tap falls outside the valid image boundaries (e.g. letterbox area).
 *
 * Formula (§4.2):
 * u = (((x_screen - tx) / s) - ox) / wfit
 * v = (((y_screen - ty) / s) - oy) / hfit
 */
export function screenToUV(
  screen: ScreenCoordinate,
  transform: ViewportTransform,
  intrinsicWidth: number,
  intrinsicHeight: number,
): UVCoordinate | null {
  const s = transform.scale;
  if (!Number.isFinite(s) || s <= 0) return null;

  const tx = transform.translateX;
  const ty = transform.translateY;
  const ox = transform.offsetX ?? 0;
  const oy = transform.offsetY ?? 0;
  const wfit = transform.fittedWidth ?? intrinsicWidth;
  const hfit = transform.fittedHeight ?? intrinsicHeight;

  if (wfit <= 0 || hfit <= 0) return null;

  const u = ((screen.x - tx) / s - ox) / wfit;
  const v = ((screen.y - ty) / s - oy) / hfit;

  if (
    !Number.isFinite(u) ||
    !Number.isFinite(v) ||
    u < 0 ||
    u > 1 ||
    v < 0 ||
    v > 1
  ) {
    return null;
  }

  return {
    u: roundToPrecision(u),
    v: roundToPrecision(v),
  };
}

/**
 * Transforms a pointer coordinate using an inverse transform matrix to canonical UV coordinates.
 * Returns `null` if outside image boundaries or non-finite.
 *
 * Used by Annotation Studio when clicking or dragging on an arbitrarily transformed canvas.
 * Ref: §4.2 pseudocode viewportPointerToUV
 */
export function viewportPointerToUV(
  pointer: ScreenCoordinate,
  inverseMatrix: MatrixLike,
  intrinsicWidth: number,
  intrinsicHeight: number,
): UVCoordinate | null {
  if (intrinsicWidth <= 0 || intrinsicHeight <= 0) return null;

  let qx: number;
  let qy: number;

  const anyMatrix = inverseMatrix as unknown as Record<string, unknown>;

  if (typeof anyMatrix.transformPoint === "function") {
    const pt = (
      anyMatrix.transformPoint as (p: ScreenCoordinate) => ScreenCoordinate
    )(pointer);
    qx = pt.x;
    qy = pt.y;
  } else if (
    typeof DOMPoint !== "undefined" &&
    typeof (pointer as unknown as { matrixTransform?: unknown })
      .matrixTransform === "function"
  ) {
    const pt = (
      pointer as unknown as {
        matrixTransform: (m: DOMMatrix) => { x: number; y: number };
      }
    ).matrixTransform(inverseMatrix as DOMMatrix);
    qx = pt.x;
    qy = pt.y;
  } else if (
    typeof DOMPoint !== "undefined" &&
    typeof DOMMatrix !== "undefined" &&
    inverseMatrix instanceof DOMMatrix
  ) {
    const pt = new DOMPoint(pointer.x, pointer.y).matrixTransform(
      inverseMatrix,
    );
    qx = pt.x;
    qy = pt.y;
  } else if (
    typeof anyMatrix.a === "number" &&
    typeof anyMatrix.b === "number" &&
    typeof anyMatrix.c === "number" &&
    typeof anyMatrix.d === "number" &&
    typeof anyMatrix.e === "number" &&
    typeof anyMatrix.f === "number"
  ) {
    const m = anyMatrix as unknown as AffineMatrix2D;
    qx = m.a * pointer.x + m.c * pointer.y + m.e;
    qy = m.b * pointer.x + m.d * pointer.y + m.f;
  } else {
    return null;
  }

  const u = qx / intrinsicWidth;
  const v = qy / intrinsicHeight;

  if (
    !Number.isFinite(u) ||
    !Number.isFinite(v) ||
    u < 0 ||
    u > 1 ||
    v < 0 ||
    v > 1
  ) {
    return null;
  }

  return {
    u: roundToPrecision(u),
    v: roundToPrecision(v),
  };
}

/**
 * Calculates default fit parameters when rendering the image inside a container (letterbox fit).
 */
export function calculateFitTransform(
  containerWidth: number,
  containerHeight: number,
  intrinsicWidth: number,
  intrinsicHeight: number,
): ViewportTransform {
  if (
    containerWidth <= 0 ||
    containerHeight <= 0 ||
    intrinsicWidth <= 0 ||
    intrinsicHeight <= 0
  ) {
    return {
      scale: 1,
      translateX: 0,
      translateY: 0,
      offsetX: 0,
      offsetY: 0,
      fittedWidth: intrinsicWidth,
      fittedHeight: intrinsicHeight,
    };
  }

  const scale = Math.min(
    containerWidth / intrinsicWidth,
    containerHeight / intrinsicHeight,
  );
  const fittedWidth = intrinsicWidth * scale;
  const fittedHeight = intrinsicHeight * scale;
  const offsetX = (containerWidth - fittedWidth) / 2;
  const offsetY = (containerHeight - fittedHeight) / 2;

  return {
    scale: 1,
    translateX: 0,
    translateY: 0,
    offsetX,
    offsetY,
    fittedWidth,
    fittedHeight,
  };
}

/**
 * Returns the screen bounding box of the transformed image.
 */
export function getViewportBounds(
  transform: ViewportTransform,
  intrinsicWidth: number,
  intrinsicHeight: number,
): {
  left: number;
  top: number;
  right: number;
  bottom: number;
  width: number;
  height: number;
} {
  const s = transform.scale;
  const tx = transform.translateX;
  const ty = transform.translateY;
  const ox = transform.offsetX ?? 0;
  const oy = transform.offsetY ?? 0;
  const wfit = transform.fittedWidth ?? intrinsicWidth;
  const hfit = transform.fittedHeight ?? intrinsicHeight;

  const left = tx + s * ox;
  const top = ty + s * oy;
  const width = s * wfit;
  const height = s * hfit;

  return {
    left,
    top,
    right: left + width,
    bottom: top + height,
    width,
    height,
  };
}

/**
 * Checks whether a screen pointer is inside the image bounds.
 */
export function isPointerInBounds(
  screen: ScreenCoordinate,
  transform: ViewportTransform,
  intrinsicWidth: number,
  intrinsicHeight: number,
): boolean {
  const bounds = getViewportBounds(transform, intrinsicWidth, intrinsicHeight);
  return (
    screen.x >= bounds.left &&
    screen.x <= bounds.right &&
    screen.y >= bounds.top &&
    screen.y <= bounds.bottom
  );
}

/**
 * Constrains pan translation so at least a fraction of the image remains visible.
 */
export function clampPan(
  translateX: number,
  translateY: number,
  transform: ViewportTransform,
  containerWidth: number,
  containerHeight: number,
  visibleMarginRatio: number = 0.2,
): { translateX: number; translateY: number } {
  const s = transform.scale;
  const wfit = transform.fittedWidth ?? containerWidth;
  const hfit = transform.fittedHeight ?? containerHeight;
  const imgW = s * wfit;
  const imgH = s * hfit;

  const minVisibleX = imgW * visibleMarginRatio;
  const minVisibleY = imgH * visibleMarginRatio;

  const minTx = -imgW + minVisibleX;
  const maxTx = containerWidth - minVisibleX;
  const minTy = -imgH + minVisibleY;
  const maxTy = containerHeight - minVisibleY;

  return {
    translateX: Math.min(Math.max(translateX, minTx), maxTx),
    translateY: Math.min(Math.max(translateY, minTy), maxTy),
  };
}
