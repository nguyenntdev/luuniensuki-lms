import { describe, it, expect, beforeEach, afterEach, vi } from "vitest";
import {
  checkWebXRSupport,
  checkCameraPermission,
  requestCameraAccess,
  evaluateMobilePerformanceBudget,
  classifyDeviceTier,
  resolveInspectionMode,
  createEquivalentInspectionSession,
  recordInspectedAngle,
  recordExaminedHotspot,
  validateInspectionCompletion,
  type MobilePerformanceBudget,
  type DeviceCapabilityReport,
} from "./ar-capabilities";

describe("AR Capabilities & Mobile Performance Budget (V5-T045)", () => {
  let mockWindow: any;
  let mockNavigator: any;

  beforeEach(() => {
    mockWindow = {
      isSecureContext: true,
      innerWidth: 1200,
      document: {
        createElement: (tag: string) => {
          if (tag === "canvas") {
            return {
              getContext: () => ({
                getParameter: (param: any) => 4096,
                getExtension: () => null,
                MAX_TEXTURE_SIZE: 4096,
              }),
            };
          }
          if (tag === "a") {
            return {
              relList: {
                supports: (rel: string) => rel === "ar",
              },
            };
          }
          return {};
        },
      },
    };

    mockNavigator = {
      deviceMemory: 8,
      hardwareConcurrency: 8,
      connection: {
        saveData: false,
        effectiveType: "4g",
      },
      mediaDevices: {
        getUserMedia: vi.fn(),
      },
      permissions: {
        query: vi.fn(),
      },
      xr: {
        isSessionSupported: vi.fn(),
      },
    };

    // Attach to globalThis safely
    (globalThis as any).window = mockWindow;
    (globalThis as any).document = mockWindow.document;
    Object.defineProperty(globalThis, "navigator", {
      value: mockNavigator,
      configurable: true,
      writable: true,
    });
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe("WebXR Capability Detection", () => {
    it("returns 'unsupported' when WebXR is not present on navigator", async () => {
      delete mockNavigator.xr;
      const result = await checkWebXRSupport();
      expect(result).toBe("unsupported");
    });

    it("returns 'supported' when navigator.xr.isSessionSupported('immersive-ar') resolves true", async () => {
      mockNavigator.xr.isSessionSupported = vi.fn().mockResolvedValue(true);
      const status = await checkWebXRSupport();
      expect(status).toBe("supported");
      expect(mockNavigator.xr.isSessionSupported).toHaveBeenCalledWith("immersive-ar");
    });

    it("returns 'session_unsupported' when navigator.xr.isSessionSupported resolves false", async () => {
      mockNavigator.xr.isSessionSupported = vi.fn().mockResolvedValue(false);
      const status = await checkWebXRSupport();
      expect(status).toBe("session_unsupported");
    });
  });

  describe("Camera Permission & Graceful Consent Handling", () => {
    it("returns 'insecure_context' when window.isSecureContext is false", async () => {
      mockWindow.isSecureContext = false;
      const perm = await checkCameraPermission();
      expect(perm).toBe("insecure_context");
    });

    it("returns 'denied' when user denies camera access during requestCameraAccess()", async () => {
      const deniedError = new Error("Permission denied");
      deniedError.name = "NotAllowedError";
      mockNavigator.mediaDevices.getUserMedia = vi.fn().mockRejectedValue(deniedError);

      const result = await requestCameraAccess();
      expect(result).toBe("denied");
    });

    it("returns 'granted' and immediately stops tracks when camera access is allowed", async () => {
      const stopTrackMock = vi.fn();
      const mockStream = {
        getTracks: () => [{ stop: stopTrackMock }],
      };
      mockNavigator.mediaDevices.getUserMedia = vi.fn().mockResolvedValue(mockStream);

      const result = await requestCameraAccess();
      expect(result).toBe("granted");
      expect(stopTrackMock).toHaveBeenCalled();
    });
  });

  describe("Mobile Performance Budget Evaluation", () => {
    it("identifies budget violations when device has low RAM (< 3GB)", () => {
      mockNavigator.deviceMemory = 2; // 2GB RAM
      const budget = evaluateMobilePerformanceBudget();
      expect(budget.meetsArBudget).toBe(false);
      expect(budget.budgetViolations.some((v) => v.includes("Bộ nhớ RAM hạn chế"))).toBe(true);
    });

    it("identifies budget violations when user enables SaveData", () => {
      mockNavigator.connection.saveData = true;
      const budget = evaluateMobilePerformanceBudget();
      expect(budget.meetsArBudget).toBe(false);
      expect(budget.budgetViolations.some((v) => v.includes("Tiết kiệm Dữ liệu"))).toBe(true);
    });

    it("identifies budget violations when network connection is 2g or 3g", () => {
      mockNavigator.connection.effectiveType = "3g";
      const budget = evaluateMobilePerformanceBudget();
      expect(budget.meetsArBudget).toBe(false);
      expect(budget.budgetViolations.some((v) => v.includes("Kết nối mạng chậm"))).toBe(true);
    });

    it("classifies device as 'low_end_mobile' when memory is <= 2GB or connection is slow", () => {
      mockWindow.innerWidth = 375;
      const budget: MobilePerformanceBudget = {
        deviceMemoryGB: 2,
        hardwareConcurrency: 2,
        connectionType: "3g",
        saveData: false,
        maxTextureSize: 4096,
        estimatedGpuTier: "low",
        meetsArBudget: false,
        budgetViolations: ["low ram"],
      };

      const tier = classifyDeviceTier(budget);
      expect(tier).toBe("low_end_mobile");
    });
  });

  describe("Deterministic Inspection Mode Resolution", () => {
    it("falls back to 'turntable_2d' when camera permission is denied", () => {
      const mockReport: DeviceCapabilityReport = {
        hasWebXR: true,
        hasCamera: true,
        hasQuickLook: false,
        cameraPermission: "denied",
        webxrAvailability: "supported",
        deviceTier: "mid_range_mobile",
        performanceBudget: {
          deviceMemoryGB: 4,
          hardwareConcurrency: 4,
          connectionType: "4g",
          saveData: false,
          maxTextureSize: 4096,
          estimatedGpuTier: "medium",
          meetsArBudget: true,
          budgetViolations: [],
        },
        recommendedMode: "turntable_2d",
        supportsAR: false,
        fallbackReason: "camera_denied",
      };

      const mode = resolveInspectionMode(mockReport, false);
      expect(mode).toBe("turntable_2d");
    });

    it("falls back to 'turntable_2d' when performance budget is exceeded", () => {
      const mockReport: DeviceCapabilityReport = {
        hasWebXR: true,
        hasCamera: true,
        hasQuickLook: false,
        cameraPermission: "granted",
        webxrAvailability: "supported",
        deviceTier: "low_end_mobile",
        performanceBudget: {
          deviceMemoryGB: 2,
          hardwareConcurrency: 2,
          connectionType: "3g",
          saveData: true,
          maxTextureSize: 2048,
          estimatedGpuTier: "low",
          meetsArBudget: false,
          budgetViolations: ["save data"],
        },
        recommendedMode: "turntable_2d",
        supportsAR: false,
        fallbackReason: "budget_exceeded",
      };

      const mode = resolveInspectionMode(mockReport, false);
      expect(mode).toBe("turntable_2d");
    });

    it("falls back to 'turntable_2d' when forceFallback is true", () => {
      const mockReport: DeviceCapabilityReport = {
        hasWebXR: true,
        hasCamera: true,
        hasQuickLook: false,
        cameraPermission: "granted",
        webxrAvailability: "supported",
        deviceTier: "desktop",
        performanceBudget: {
          deviceMemoryGB: 8,
          hardwareConcurrency: 8,
          connectionType: "4g",
          saveData: false,
          maxTextureSize: 8192,
          estimatedGpuTier: "high",
          meetsArBudget: true,
          budgetViolations: [],
        },
        recommendedMode: "webxr_ar",
        supportsAR: true,
        fallbackReason: null,
      };

      const mode = resolveInspectionMode(mockReport, true);
      expect(mode).toBe("turntable_2d");
    });
  });

  describe("Equivalent Learning Invariant (NEGATIVE ABUSE SAFEGUARD)", () => {
    it("fails validation if inspection duration is under 3 seconds", () => {
      const startTime = Date.now();
      const session = createEquivalentInspectionSession("ngai-vang-hoang-de", "turntable_2d", false);
      session.startTime = startTime;
      recordInspectedAngle(session, "front");

      // Only 1 second elapsed
      const validation = validateInspectionCompletion(session, startTime + 1000);
      expect(validation.valid).toBe(false);
      expect(validation.reason).toContain("chưa đủ");
    });

    it("fails validation if 0 angles and 0 hotspots were examined", () => {
      const startTime = Date.now();
      const session = createEquivalentInspectionSession("ngai-vang-hoang-de", "turntable_2d", false);
      session.startTime = startTime;

      // 5 seconds elapsed but nothing viewed
      const validation = validateInspectionCompletion(session, startTime + 5000);
      expect(validation.valid).toBe(false);
      expect(validation.reason).toContain("Cần xoay hiện vật");
    });

    it("SUCCESS: Denied camera permission (cameraGranted=false) completes 100% equivalent learning task", () => {
      const startTime = Date.now();
      // Learner denied camera permission -> uses turntable_2d mode
      const session = createEquivalentInspectionSession(
        "ngai-vang-hoang-de",
        "turntable_2d",
        false, // cameraPermissionGranted = FALSE
        "low_end_mobile",
      );
      session.startTime = startTime;

      // Learner rotates relic and examines details
      recordInspectedAngle(session, "front");
      recordInspectedAngle(session, "back");
      recordExaminedHotspot(session, "h1");

      const validation = validateInspectionCompletion(session, startTime + 4000);
      expect(validation.valid).toBe(true);
      expect(session.equivalentLearningCompleted).toBe(true);
      expect(session.cameraPermissionGranted).toBe(false);
      expect(session.inspectionMode).toBe("turntable_2d");
    });

    it("SUCCESS: Granted camera permission (cameraGranted=true) completes equivalent task identically", () => {
      const startTime = Date.now();
      // AR learner
      const session = createEquivalentInspectionSession(
        "ngai-vang-hoang-de",
        "webxr_ar",
        true, // cameraPermissionGranted = TRUE
        "high_end_mobile",
      );
      session.startTime = startTime;

      recordInspectedAngle(session, "front");
      recordExaminedHotspot(session, "h1");

      const validation = validateInspectionCompletion(session, startTime + 4000);
      expect(validation.valid).toBe(true);
      expect(session.equivalentLearningCompleted).toBe(true);
      expect(session.cameraPermissionGranted).toBe(true);
      expect(session.inspectionMode).toBe("webxr_ar");
    });
  });
});
