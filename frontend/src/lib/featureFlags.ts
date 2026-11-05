/**
 * Feature Flags & Kill Switches Client Utility
 * Luuniensuki LMS (V5-T089)
 *
 * Provides typed access to runtime release flags and kill switches,
 * graceful service degradation detection, and user-facing maintenance banners.
 */

export interface FeatureFlagState {
  FEATURE_FLAG_AI_TUTOR_ENABLED: boolean;
  FEATURE_FLAG_LIVEKIT_MEDIA_ENABLED: boolean;
  FEATURE_FLAG_RBPC_COMMERCE_ENABLED: boolean;
}

export type KillSwitchKey = keyof FeatureFlagState;

export const DEFAULT_FEATURE_FLAGS: FeatureFlagState = {
  FEATURE_FLAG_AI_TUTOR_ENABLED: true,
  FEATURE_FLAG_LIVEKIT_MEDIA_ENABLED: true,
  FEATURE_FLAG_RBPC_COMMERCE_ENABLED: true,
};

export const FEATURE_MAINTENANCE_MESSAGES: Record<KillSwitchKey, { title: string; message: string }> = {
  FEATURE_FLAG_AI_TUTOR_ENABLED: {
    title: "Trợ lý AI đang bảo trì",
    message: "Hệ thống Trợ lý AI đang tạm ngưng bảo trì. Quý khách và học sinh vẫn có thể tra cứu thông tin di sản bình thường.",
  },
  FEATURE_FLAG_LIVEKIT_MEDIA_ENABLED: {
    title: "Phòng học trực tuyến đang gián đoạn",
    message: "Dịch vụ truyền phát âm thanh và video trực tiếp đang tạm ngưng do kết nối mạng. Vui lòng thử lại sau.",
  },
  FEATURE_FLAG_RBPC_COMMERCE_ENABLED: {
    title: "Đặt lịch trải nghiệm tạm ngưng",
    message: "Hệ thống tiếp nhận yêu cầu đặt lịch trải nghiệm đang tạm ngưng bảo trì định kỳ. Quý khách vui lòng quay lại sau.",
  },
};

/**
 * Parses raw server response or environment overrides into FeatureFlagState.
 */
export function resolveFeatureFlags(
  serverFlags?: Partial<Record<string, boolean>>,
  overrides?: Partial<Record<string, boolean>>
): FeatureFlagState {
  const flags = { ...DEFAULT_FEATURE_FLAGS };

  // Apply server flags if present
  if (serverFlags) {
    if (typeof serverFlags.FEATURE_FLAG_AI_TUTOR_ENABLED === "boolean") {
      flags.FEATURE_FLAG_AI_TUTOR_ENABLED = serverFlags.FEATURE_FLAG_AI_TUTOR_ENABLED;
    }
    if (typeof serverFlags.ai_tutor === "boolean") {
      flags.FEATURE_FLAG_AI_TUTOR_ENABLED = serverFlags.ai_tutor;
    }
    if (typeof serverFlags.FEATURE_FLAG_LIVEKIT_MEDIA_ENABLED === "boolean") {
      flags.FEATURE_FLAG_LIVEKIT_MEDIA_ENABLED = serverFlags.FEATURE_FLAG_LIVEKIT_MEDIA_ENABLED;
    }
    if (typeof serverFlags.livekit_media === "boolean") {
      flags.FEATURE_FLAG_LIVEKIT_MEDIA_ENABLED = serverFlags.livekit_media;
    }
    if (typeof serverFlags.FEATURE_FLAG_RBPC_COMMERCE_ENABLED === "boolean") {
      flags.FEATURE_FLAG_RBPC_COMMERCE_ENABLED = serverFlags.FEATURE_FLAG_RBPC_COMMERCE_ENABLED;
    }
    if (typeof serverFlags.rbpc_commerce === "boolean") {
      flags.FEATURE_FLAG_RBPC_COMMERCE_ENABLED = serverFlags.rbpc_commerce;
    }
  }

  // Apply local or test overrides
  if (overrides) {
    Object.assign(flags, overrides);
  }

  return flags;
}

/**
 * Check if a specific feature is enabled.
 */
export function isFeatureActive(
  flagKey: KillSwitchKey,
  currentFlags: FeatureFlagState = DEFAULT_FEATURE_FLAGS
): boolean {
  return Boolean(currentFlags[flagKey]);
}

/**
 * Inspect an API error to determine if it is a 503 maintenance response from a tripped kill switch.
 */
export function isKillSwitchError(
  error: unknown
): { isMaintenance: boolean; message?: string } {
  if (!error || typeof error !== "object") {
    return { isMaintenance: false };
  }

  const err = error as {
    status?: number;
    statusCode?: number;
    message?: string;
    detail?: string;
    code?: string;
  };

  const status = err.status || err.statusCode;
  if (status === 503) {
    return {
      isMaintenance: true,
      message: err.message || err.detail || "Dịch vụ đang tạm ngưng bảo trì.",
    };
  }

  return { isMaintenance: false };
}
