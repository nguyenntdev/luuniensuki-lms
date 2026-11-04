/**
 * AR Capabilities & Mobile Performance Budget Engine (V5-T045).
 *
 * Implements:
 * 1. WebXR capability detection ('immersive-ar' session support).
 * 2. Camera permission checking and graceful user consent prompt.
 * 3. Mobile performance budget evaluation (RAM, CPU concurrency, connection, GPU).
 * 4. Device tier classification ('low_end_mobile', 'mid_range_mobile', 'high_end_mobile', 'desktop').
 * 5. Deterministic fallback mode resolution:
 *    - Camera denied/unsupported -> 2D Turntable / Rubbing fallback.
 *    - Insecure context (HTTP) -> Fallback mode.
 *    - Low-end mobile / Save-Data enabled -> Lightweight 2D fallback.
 * 6. NEGATIVE ABUSE SAFEGUARD:
 *    Learner who denies camera permission or uses 2D fallback is NEVER penalized;
 *    they complete the exact same equivalent learning/inspection task and receive
 *    the identical XP, progress status, and feedback.
 */

export type DeviceTier =
  | "low_end_mobile"
  | "mid_range_mobile"
  | "high_end_mobile"
  | "desktop";

export type CameraPermissionState =
  | "prompt"
  | "granted"
  | "denied"
  | "unsupported"
  | "insecure_context";

export type WebXRAvailability =
  | "supported"
  | "unsupported"
  | "session_unsupported"
  | "unknown";

export type ARInspectionMode =
  | "webxr_ar"
  | "quicklook_ar"
  | "turntable_3d"
  | "turntable_2d"
  | "image_fallback";

export type FallbackReason =
  | "camera_denied"
  | "webxr_unsupported"
  | "budget_exceeded"
  | "insecure_context"
  | "hardware_unsupported"
  | null;

export interface MobilePerformanceBudget {
  /** Available device memory in GB (via navigator.deviceMemory, or null in unsupported browsers) */
  deviceMemoryGB: number | null;
  /** Logical CPU processors (via navigator.hardwareConcurrency) */
  hardwareConcurrency: number;
  /** Effective connection type (slow-2g, 2g, 3g, 4g) */
  connectionType: "slow-2g" | "2g" | "3g" | "4g" | "unknown";
  /** Whether the user has requested data-saving mode */
  saveData: boolean;
  /** Maximum supported WebGL texture size (e.g. 4096, 8192, 16384) */
  maxTextureSize: number;
  /** Estimated GPU performance tier */
  estimatedGpuTier: "low" | "medium" | "high";
  /** Whether the device meets the mobile performance budget for WebXR 3D rendering */
  meetsArBudget: boolean;
  /** Reasons why the device does not meet budget (empty if meetsArBudget=true) */
  budgetViolations: string[];
}

export interface DeviceCapabilityReport {
  hasWebXR: boolean;
  hasCamera: boolean;
  hasQuickLook: boolean;
  cameraPermission: CameraPermissionState;
  webxrAvailability: WebXRAvailability;
  deviceTier: DeviceTier;
  performanceBudget: MobilePerformanceBudget;
  recommendedMode: ARInspectionMode;
  supportsAR: boolean;
  fallbackReason: FallbackReason;
}

export interface RelicInspectionSession {
  targetSlug: string;
  inspectionMode: ARInspectionMode;
  cameraPermissionGranted: boolean;
  deviceTier: DeviceTier;
  startTime: number;
  anglesInspected: Set<string>;
  hotspotsExamined: Set<string>;
  equivalentLearningCompleted: boolean;
}

// --------------------------------------------------------------------------- //
// Capability Checking Helpers
// --------------------------------------------------------------------------- //

/**
 * Checks if the browser and environment support WebXR immersive AR.
 */
export async function checkWebXRSupport(): Promise<WebXRAvailability> {
  if (typeof window === "undefined" || typeof navigator === "undefined") {
    return "unsupported";
  }

  // WebXR requires secure context (HTTPS or localhost)
  if (!window.isSecureContext) {
    return "unsupported";
  }

  const xr = (navigator as unknown as { xr?: { isSessionSupported?: (mode: string) => Promise<boolean> } }).xr;
  if (!xr || typeof xr.isSessionSupported !== "function") {
    return "unsupported";
  }

  try {
    const isSupported = await xr.isSessionSupported("immersive-ar");
    return isSupported ? "supported" : "session_unsupported";
  } catch {
    return "unsupported";
  }
}

/**
 * Checks current Camera permission status without triggering an intrusive prompt.
 */
export async function checkCameraPermission(): Promise<CameraPermissionState> {
  if (typeof window === "undefined" || typeof navigator === "undefined") {
    return "unsupported";
  }

  if (!window.isSecureContext) {
    return "insecure_context";
  }

  if (!navigator.mediaDevices || typeof navigator.mediaDevices.getUserMedia !== "function") {
    return "unsupported";
  }

  // Check via Permissions API if available
  if (navigator.permissions && typeof navigator.permissions.query === "function") {
    try {
      const status = await navigator.permissions.query({ name: "camera" as PermissionName });
      return status.state as CameraPermissionState;
    } catch {
      // Some browsers (Firefox/Safari) don't support camera query in permissions.query
      return "prompt";
    }
  }

  return "prompt";
}

/**
 * Gracefully requests camera access from the user.
 * Catches user refusal, hardware errors, or security policy violations gracefully.
 */
export async function requestCameraAccess(): Promise<CameraPermissionState> {
  if (typeof window === "undefined" || typeof navigator === "undefined") {
    return "unsupported";
  }

  if (!window.isSecureContext) {
    return "insecure_context";
  }

  if (!navigator.mediaDevices || typeof navigator.mediaDevices.getUserMedia !== "function") {
    return "unsupported";
  }

  try {
    const stream = await navigator.mediaDevices.getUserMedia({
      video: { facingMode: { ideal: "environment" } },
      audio: false,
    });
    // Immediately stop the stream after verification to release hardware resources
    stream.getTracks().forEach((track) => track.stop());
    return "granted";
  } catch (error: unknown) {
    const err = error as { name?: string };
    if (err.name === "NotAllowedError" || err.name === "PermissionDeniedError") {
      return "denied";
    }
    return "unsupported";
  }
}

/**
 * Detects whether the device supports iOS QuickLook USDZ AR.
 */
export function checkQuickLookSupport(): boolean {
  if (typeof window === "undefined" || typeof document === "undefined") {
    return false;
  }
  const a = document.createElement("a");
  return Boolean(a.relList && a.relList.supports && a.relList.supports("ar"));
}

/**
 * Evaluates the client's mobile performance budget.
 * Guards low-end devices and slow mobile connections from heavy WebXR or high-poly models.
 */
export function evaluateMobilePerformanceBudget(): MobilePerformanceBudget {
  if (typeof window === "undefined" || typeof navigator === "undefined") {
    return {
      deviceMemoryGB: 4,
      hardwareConcurrency: 4,
      connectionType: "4g",
      saveData: false,
      maxTextureSize: 4096,
      estimatedGpuTier: "medium",
      meetsArBudget: true,
      budgetViolations: [],
    };
  }

  const nav = navigator as unknown as {
    deviceMemory?: number;
    hardwareConcurrency?: number;
    connection?: {
      effectiveType?: "slow-2g" | "2g" | "3g" | "4g";
      saveData?: boolean;
    };
  };

  const deviceMemoryGB = typeof nav.deviceMemory === "number" ? nav.deviceMemory : null;
  const hardwareConcurrency = typeof nav.hardwareConcurrency === "number" ? nav.hardwareConcurrency : 4;
  const connectionType = nav.connection?.effectiveType || "unknown";
  const saveData = Boolean(nav.connection?.saveData);

  // Check WebGL max texture size and context capability
  let maxTextureSize = 4096;
  let estimatedGpuTier: "low" | "medium" | "high" = "medium";
  try {
    const canvas = document.createElement("canvas");
    const gl = canvas.getContext("webgl") || (canvas.getContext("experimental-webgl") as WebGLRenderingContext | null);
    if (gl) {
      maxTextureSize = gl.getParameter(gl.MAX_TEXTURE_SIZE) || 4096;
      const debugInfo = gl.getExtension("WEBGL_debug_renderer_info");
      if (debugInfo) {
        const renderer = gl.getParameter(debugInfo.UNMASKED_RENDERER_WEBGL) || "";
        const lowerRenderer = String(renderer).toLowerCase();
        if (
          lowerRenderer.includes("swiftshader") ||
          lowerRenderer.includes("llvmpipe") ||
          lowerRenderer.includes("software")
        ) {
          estimatedGpuTier = "low";
        } else if (
          lowerRenderer.includes("apple") ||
          lowerRenderer.includes("geforce") ||
          lowerRenderer.includes("radeon") ||
          lowerRenderer.includes("adreno 6") ||
          lowerRenderer.includes("adreno 7") ||
          lowerRenderer.includes("mali-g7")
        ) {
          estimatedGpuTier = "high";
        }
      }
    }
  } catch {
    estimatedGpuTier = "low";
  }

  const budgetViolations: string[] = [];

  // Budget rule 1: Minimum 3GB RAM recommended for stable WebXR
  if (deviceMemoryGB !== null && deviceMemoryGB < 3) {
    budgetViolations.push(`Bộ nhớ RAM hạn chế (${deviceMemoryGB}GB < 3GB)`);
  }

  // Budget rule 2: User explicitly requested data saver
  if (saveData) {
    budgetViolations.push("Người dùng bật chế độ Tiết kiệm Dữ liệu (Data Saver)");
  }

  // Budget rule 3: Network too slow for 3D/AR assets
  if (connectionType === "slow-2g" || connectionType === "2g" || connectionType === "3g") {
    budgetViolations.push(`Kết nối mạng chậm (${connectionType})`);
  }

  // Budget rule 4: Low CPU cores
  if (hardwareConcurrency <= 2) {
    budgetViolations.push(`Vi xử lý hạn chế (${hardwareConcurrency} nhân)`);
  }

  // Budget rule 5: Software GPU / very low texture limit
  if (estimatedGpuTier === "low" || maxTextureSize < 2048) {
    budgetViolations.push("Khả năng đồ họa (GPU/WebGL) không đủ đáp ứng dựng hình AR");
  }

  const meetsArBudget = budgetViolations.length === 0;

  return {
    deviceMemoryGB,
    hardwareConcurrency,
    connectionType,
    saveData,
    maxTextureSize,
    estimatedGpuTier,
    meetsArBudget,
    budgetViolations,
  };
}

/**
 * Classifies device into a standard tier.
 */
export function classifyDeviceTier(budget: MobilePerformanceBudget): DeviceTier {
  if (typeof window === "undefined") {
    return "desktop";
  }

  const isMobile = window.innerWidth < 768 || "ontouchstart" in window;

  if (!isMobile) {
    return "desktop";
  }

  if (
    (budget.deviceMemoryGB !== null && budget.deviceMemoryGB <= 2) ||
    budget.saveData ||
    budget.connectionType === "2g" ||
    budget.connectionType === "slow-2g" ||
    budget.estimatedGpuTier === "low"
  ) {
    return "low_end_mobile";
  }

  if (
    (budget.deviceMemoryGB !== null && budget.deviceMemoryGB >= 6) &&
    budget.hardwareConcurrency >= 6 &&
    budget.estimatedGpuTier === "high"
  ) {
    return "high_end_mobile";
  }

  return "mid_range_mobile";
}

/**
 * Generates an end-to-end device capability report.
 */
export async function getDeviceCapabilityReport(): Promise<DeviceCapabilityReport> {
  const budget = evaluateMobilePerformanceBudget();
  const deviceTier = classifyDeviceTier(budget);
  const webxrAvail = await checkWebXRSupport();
  const cameraPerm = await checkCameraPermission();
  const hasQuickLook = checkQuickLookSupport();

  const hasWebXR = webxrAvail === "supported";
  const hasCamera = cameraPerm !== "unsupported" && cameraPerm !== "insecure_context";

  let recommendedMode: ARInspectionMode = "turntable_2d";
  let fallbackReason: FallbackReason = null;
  let supportsAR = false;

  if (cameraPerm === "insecure_context") {
    recommendedMode = "turntable_2d";
    fallbackReason = "insecure_context";
  } else if (cameraPerm === "denied") {
    recommendedMode = "turntable_2d";
    fallbackReason = "camera_denied";
  } else if (!budget.meetsArBudget) {
    recommendedMode = "turntable_2d";
    fallbackReason = "budget_exceeded";
  } else if (hasWebXR && cameraPerm === "granted") {
    recommendedMode = "webxr_ar";
    supportsAR = true;
  } else if (hasQuickLook) {
    recommendedMode = "quicklook_ar";
    supportsAR = true;
  } else if (hasWebXR && cameraPerm === "prompt") {
    // Eligible for AR upon user consent
    recommendedMode = "webxr_ar";
    supportsAR = true;
  } else {
    recommendedMode = "turntable_2d";
    fallbackReason = "webxr_unsupported";
  }

  return {
    hasWebXR,
    hasCamera,
    hasQuickLook,
    cameraPermission: cameraPerm,
    webxrAvailability: webxrAvail,
    deviceTier,
    performanceBudget: budget,
    recommendedMode,
    supportsAR,
    fallbackReason,
  };
}

/**
 * Resolves the inspection mode to use, respecting user preferences or fallback overrides.
 */
export function resolveInspectionMode(
  report: DeviceCapabilityReport,
  forceFallback: boolean = false,
): ARInspectionMode {
  if (forceFallback) {
    return "turntable_2d";
  }

  if (report.cameraPermission === "denied" || report.fallbackReason === "camera_denied") {
    return "turntable_2d";
  }

  if (report.fallbackReason === "budget_exceeded") {
    return "turntable_2d";
  }

  return report.recommendedMode;
}

// --------------------------------------------------------------------------- //
// Pedagogical Invariant: Equivalent Learning Task Engine
// --------------------------------------------------------------------------- //

/**
 * Initializes a tracked inspection session.
 */
export function createEquivalentInspectionSession(
  targetSlug: string,
  mode: ARInspectionMode,
  cameraGranted: boolean,
  deviceTier: DeviceTier = "desktop",
): RelicInspectionSession {
  return {
    targetSlug,
    inspectionMode: mode,
    cameraPermissionGranted: cameraGranted,
    deviceTier,
    startTime: Date.now(),
    anglesInspected: new Set<string>(),
    hotspotsExamined: new Set<string>(),
    equivalentLearningCompleted: false,
  };
}

/**
 * Records that the learner inspected a specific angle or view of the relic.
 */
export function recordInspectedAngle(
  session: RelicInspectionSession,
  angle: "front" | "right" | "back" | "left" | "top" | string,
): void {
  session.anglesInspected.add(angle);
}

/**
 * Records that the learner inspected a specific hotspot or detail.
 */
export function recordExaminedHotspot(
  session: RelicInspectionSession,
  hotspotId: string,
): void {
  session.hotspotsExamined.add(hotspotId);
}

/**
 * Evaluates whether the learner has satisfied the inspection criteria.
 *
 * Core rule:
 * Inspection completion requires active observation (duration >= 3s AND at least
 * 1 angle or hotspot examined). Camera permission is NEVER required.
 */
export function validateInspectionCompletion(
  session: RelicInspectionSession,
  currentTimeMs: number = Date.now(),
): { valid: boolean; reason?: string } {
  const elapsedSeconds = Math.floor((currentTimeMs - session.startTime) / 1000);

  if (elapsedSeconds < 3) {
    return {
      valid: false,
      reason: `Thời gian quan sát hiện vật chưa đủ (${elapsedSeconds}s < 3s). Vui lòng quan sát thêm.`,
    };
  }

  if (session.anglesInspected.size === 0 && session.hotspotsExamined.size === 0) {
    return {
      valid: false,
      reason: "Cần xoay hiện vật hoặc kiểm tra ít nhất một góc nhìn hoặc điểm chi tiết.",
    };
  }

  session.equivalentLearningCompleted = true;
  return { valid: true };
}
