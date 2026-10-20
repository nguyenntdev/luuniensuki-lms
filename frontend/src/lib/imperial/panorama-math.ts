/**
 * Mathematical Utilities for 360° Equirectangular Panorama Projection & Hotspots
 * Ref: Luu Nien STTTNND Follow-On SPEC V5.1 (02_MEDIA_EXPLORATION.md)
 *
 * Implements:
 * - Spherical coordinates (yaw/pitch) <-> Cartesian coordinates (X/Y/Z)
 * - 3D Cartesian coordinates <-> 2D Screen Viewport coordinates projection
 * - Angle normalization, clamping, and UV conversions
 */

export interface Vector3Like {
  x: number;
  y: number;
  z: number;
}

export interface ScreenPosition {
  x: number;
  y: number;
  isVisible: boolean;
  depth: number;
}

export interface CameraLike {
  matrixWorldInverse?: {
    elements: ArrayLike<number>;
  };
  projectionMatrix?: {
    elements: ArrayLike<number>;
  };
  project?: (vec: { x: number; y: number; z: number }) => { x: number; y: number; z: number };
  matrixWorld?: {
    elements: ArrayLike<number>;
  };
  getWorldDirection?: (target: { x: number; y: number; z: number }) => { x: number; y: number; z: number };
}

export const DEFAULT_SPHERE_RADIUS = 500;
export const MIN_PITCH = -85;
export const MAX_PITCH = 85;

/**
 * Convert degrees to radians.
 */
export function degToRad(degrees: number): number {
  return (degrees * Math.PI) / 180;
}

/**
 * Convert radians to degrees.
 */
export function radToDeg(radians: number): number {
  return (radians * 180) / Math.PI;
}

/**
 * Normalizes an angle into the specified range [min, max], default [-180, 180].
 * If degrees is not finite, returns 0.
 */
export function normalizeAngle(
  degrees: number,
  min: number = -180,
  max: number = 180
): number {
  if (!Number.isFinite(degrees)) return 0;
  const range = max - min;
  if (range <= 0) return degrees;

  if (min === -180 && max === 180) {
    let a = degrees % 360;
    if (a > 180) a -= 360;
    if (a < -180) a += 360;
    return a;
  }

  let normalized = (degrees - min) % range;
  if (normalized < 0) normalized += range;
  return normalized + min;
}

/**
 * Clamps pitch angle between min and max (default [-85, 85] to avoid gimbal singularities).
 */
export function clampPitch(
  pitch: number,
  min: number = MIN_PITCH,
  max: number = MAX_PITCH
): number {
  if (!Number.isFinite(pitch)) return 0;
  return Math.max(min, Math.min(max, pitch));
}

/**
 * Convert spherical coordinates (yaw, pitch in degrees) to 3D Cartesian coordinates.
 * Convention (matching Three.js camera looking towards -Z when yaw=0, pitch=0):
 * - yaw = 0, pitch = 0 -> (0, 0, -radius)
 * - yaw = 90, pitch = 0 -> (radius, 0, 0) [looking right / East]
 * - yaw = -90, pitch = 0 -> (-radius, 0, 0) [looking left / West]
 * - yaw = 180, pitch = 0 -> (0, 0, radius) [looking behind / South]
 * - pitch = 90 -> (0, radius, 0) [Zenith / looking up]
 * - pitch = -90 -> (0, -radius, 0) [Nadir / looking down]
 */
export function sphericalToCartesian(
  yawDegrees: number,
  pitchDegrees: number,
  radius: number = DEFAULT_SPHERE_RADIUS
): Vector3Like {
  const yawRad = degToRad(yawDegrees);
  const pitchRad = degToRad(pitchDegrees);

  const cosPitch = Math.cos(pitchRad);
  const sinPitch = Math.sin(pitchRad);
  const sinYaw = Math.sin(yawRad);
  const cosYaw = Math.cos(yawRad);

  return {
    x: radius * cosPitch * sinYaw,
    y: radius * sinPitch,
    z: -radius * cosPitch * cosYaw,
  };
}

/**
 * Convert 3D Cartesian coordinates back to spherical coordinates (yaw, pitch in degrees).
 */
export function cartesianToSpherical(
  x: number,
  y: number,
  z: number
): { yaw: number; pitch: number; radius: number } {
  const radius = Math.sqrt(x * x + y * y + z * z);
  if (radius === 0) {
    return { yaw: 0, pitch: 0, radius: 0 };
  }

  // pitch is angle from XZ plane towards Y axis
  const pitchRad = Math.asin(Math.max(-1, Math.min(1, y / radius)));
  const pitch = radToDeg(pitchRad);

  // yaw: looking at -Z when yaw=0, X is right
  // x = cosPitch * sinYaw, -z = cosPitch * cosYaw
  // atan2(x, -z) gives yaw in radians
  const yawRad = Math.atan2(x, -z);
  const yaw = radToDeg(yawRad);

  return {
    yaw: normalizeAngle(yaw),
    pitch: clampPitch(pitch, -90, 90),
    radius,
  };
}

/**
 * Converts equirectangular 2D UV (u, v in 0..1) to spherical yaw (-180..180) and pitch (-90..90).
 * - u = 0.5, v = 0.5 -> yaw = 0, pitch = 0 (center)
 * - u = 0.0 -> yaw = -180
 * - u = 1.0 -> yaw = 180
 * - v = 0.0 -> pitch = 90 (top / sky)
 * - v = 1.0 -> pitch = -90 (bottom / ground)
 */
export function uvToSpherical(
  u: number,
  v: number
): { yaw: number; pitch: number } {
  const clampedU = Math.max(0, Math.min(1, u));
  const clampedV = Math.max(0, Math.min(1, v));

  const yaw = (clampedU - 0.5) * 360; // -180 .. 180
  const pitch = (0.5 - clampedV) * 180; // 90 .. -90

  return {
    yaw: normalizeAngle(yaw),
    pitch: clampPitch(pitch, -90, 90),
  };
}

/**
 * Converts spherical yaw (-180..180) and pitch (-90..90) to equirectangular UV (0..1, 0..1).
 */
export function sphericalToUV(
  yawDegrees: number,
  pitchDegrees: number
): { u: number; v: number } {
  const normYaw = normalizeAngle(yawDegrees);
  const clampedPitch = clampPitch(pitchDegrees, -90, 90);

  const u = (normYaw + 180) / 360;
  const v = (90 - clampedPitch) / 180;

  return {
    u: Math.max(0, Math.min(1, u)),
    v: Math.max(0, Math.min(1, v)),
  };
}

/**
 * Transform a 3D vector by a 4x4 matrix (column-major array of 16 numbers).
 */
function applyMatrix4(
  v: Vector3Like,
  m: ArrayLike<number>
): { x: number; y: number; z: number; w: number } {
  const x = v.x;
  const y = v.y;
  const z = v.z;

  const w = m[3] * x + m[7] * y + m[11] * z + m[15];
  const outX = m[0] * x + m[4] * y + m[8] * z + m[12];
  const outY = m[1] * x + m[5] * y + m[9] * z + m[13];
  const outZ = m[2] * x + m[6] * y + m[10] * z + m[14];

  return { x: outX, y: outY, z: outZ, w };
}

/**
 * Projects a 3D Cartesian position to 2D screen coordinates within the given viewport.
 * Works with either a Three.js Camera (via `.project()` or matrices) or manual matrix math.
 *
 * Screen coordinates:
 * - (0, 0) is top-left
 * - (viewportWidth, viewportHeight) is bottom-right
 *
 * Returns:
 * - x: pixel x coordinate
 * - y: pixel y coordinate
 * - isVisible: true if the point is in front of the camera and within clip space
 * - depth: normalized clip depth (ndc.z)
 */
export function cartesianToScreen(
  vector3: Vector3Like,
  camera: CameraLike,
  viewportWidth: number,
  viewportHeight: number
): ScreenPosition {
  if (viewportWidth <= 0 || viewportHeight <= 0) {
    return { x: 0, y: 0, isVisible: false, depth: 1 };
  }

  let ndcX = 0;
  let ndcY = 0;
  let ndcZ = 0;
  let isFront = true;

  if (typeof camera.project === "function") {
    // Clone coordinate to avoid mutating caller object
    const projected = camera.project({ x: vector3.x, y: vector3.y, z: vector3.z });
    ndcX = projected.x;
    ndcY = projected.y;
    ndcZ = projected.z;

    // In Three.js, points behind the camera project to ndcZ > 1 (or sometimes < -1 depending on near/far)
    isFront = ndcZ <= 1 && ndcZ >= -1;
  } else if (
    camera.matrixWorldInverse?.elements &&
    camera.projectionMatrix?.elements
  ) {
    // View transform: world -> view space
    const viewPt = applyMatrix4(vector3, camera.matrixWorldInverse.elements);
    // In OpenGL/Three.js view space, forward is -Z. If viewPt.z >= 0, point is behind camera
    isFront = viewPt.z < 0;

    // Projection transform: view -> clip space
    const clipPt = applyMatrix4(
      { x: viewPt.x, y: viewPt.y, z: viewPt.z },
      camera.projectionMatrix.elements
    );

    const w = clipPt.w !== 0 ? clipPt.w : 1;
    ndcX = clipPt.x / w;
    ndcY = clipPt.y / w;
    ndcZ = clipPt.z / w;
  } else {
    // Fallback: assume identity camera looking along -Z
    ndcX = vector3.x / Math.max(1, Math.abs(vector3.z));
    ndcY = vector3.y / Math.max(1, Math.abs(vector3.z));
    ndcZ = vector3.z;
    isFront = vector3.z < 0;
  }

  // Convert Normalized Device Coordinates [-1, 1] to screen pixel space
  const screenX = ((ndcX + 1) / 2) * viewportWidth;
  const screenY = ((-ndcY + 1) / 2) * viewportHeight;

  // Point is visible if it is in front of camera and roughly within the viewport boundary
  const inViewport =
    screenX >= -50 &&
    screenX <= viewportWidth + 50 &&
    screenY >= -50 &&
    screenY <= viewportHeight + 50;

  const isVisible = isFront && inViewport;

  return {
    x: Math.round(screenX * 10) / 10,
    y: Math.round(screenY * 10) / 10,
    isVisible,
    depth: ndcZ,
  };
}
