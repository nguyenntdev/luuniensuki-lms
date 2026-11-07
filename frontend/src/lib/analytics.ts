/**
 * LƯU NIÊN — RBPC 2026: Analytics Event Taxonomy & Consent-Aware Telemetry Client
 * Scope: Frontend event ingestion, consent verification, idempotency tracking,
 * zero student PII scrubbing, and business conversion funnel telemetry.
 * Base Specification: Wave W11, Slot A01 (Ticket V5-T111).
 */

import { logAnalyticsEvents, type AnalyticsEvent } from "@/lib/api";

export const EVENT_CATEGORIES = {
  ACTIVATION: "activation",
  LESSON: "lesson",
  QUIZ: "quiz",
  STREAK: "streak",
  DISCOVERY: "discovery",
  ENGAGEMENT: "engagement",
  PERFORMANCE: "performance",
  BUSINESS_CONVERSION: "business_conversion",
} as const;

export const ANALYTICS_EVENT_TYPES = {
  // Activation
  APP_OPENED: "app_opened",
  ONBOARDING_STARTED: "onboarding_started",
  ONBOARDING_COMPLETED: "onboarding_completed",

  // Business Conversion (V5-T111)
  VIEW: "view",
  EXPLORE: "explore",
  INQUIRY_START: "inquiry_start",
  INQUIRY_SUBMIT: "inquiry_submit",
  INQUIRY_CONFIRM: "inquiry_confirm",

  // Performance
  RENDER_PERFORMANCE: "render_performance",
} as const;

export type AnalyticsEventType =
  (typeof ANALYTICS_EVENT_TYPES)[keyof typeof ANALYTICS_EVENT_TYPES];

const CONSENT_STORAGE_KEY = "luuniensuki_telemetry_consent";

// Sensitive student PII field keys to scrub client-side
const SENSITIVE_PII_KEYS = new Set([
  "student_name",
  "student_email",
  "student_id",
  "guardian_name",
  "guardian_phone",
  "guardian_email",
  "school_address",
  "full_name",
  "phone",
  "email",
  "phone_number",
  "contact_phone",
  "national_id",
  "citizen_id",
  "cccd",
  "cmnd",
  "password",
  "token",
  "jwt",
]);

const EMAIL_REGEX = /\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b/g;
const PHONE_REGEX = /(?:(?:\+84|84|0)(?:\s*[\.\-]?\s*\d){8,10}\b|\b\(?0\d{1,3}\)?[\s\.\-]?\d{3,4}[\s\.\-]?\d{3,4}\b)/g;

export const REDACTED_PII = "[REDACTED_STUDENT_PII]";
export const REDACTED_EMAIL = "[REDACTED_EMAIL]";
export const REDACTED_PHONE = "[REDACTED_PHONE]";

/**
 * Check if data contains student PII client-side.
 */
export function containsClientPii(data: unknown): boolean {
  if (!data) return false;
  if (typeof data === "string") {
    return EMAIL_REGEX.test(data) || PHONE_REGEX.test(data);
  }
  if (typeof data === "object") {
    if (Array.isArray(data)) {
      return data.some((item) => containsClientPii(item));
    }
    const record = data as Record<string, unknown>;
    for (const [key, value] of Object.entries(record)) {
      if (SENSITIVE_PII_KEYS.has(key.toLowerCase().trim())) {
        if (value && value !== REDACTED_PII && value !== REDACTED_EMAIL && value !== REDACTED_PHONE) {
          return true;
        }
      }
      if (containsClientPii(value)) return true;
    }
  }
  return false;
}

/**
 * Scrub sensitive student PII recursively from client payloads before transmission.
 */
export function sanitizeClientPayload<T = unknown>(data: T): T {
  if (!data) return data;
  if (typeof data === "string") {
    let sanitized = data.replace(EMAIL_REGEX, REDACTED_EMAIL);
    sanitized = sanitized.replace(PHONE_REGEX, REDACTED_PHONE);
    return sanitized as unknown as T;
  }
  if (typeof data === "object") {
    if (Array.isArray(data)) {
      return data.map((item) => sanitizeClientPayload(item)) as unknown as T;
    }
    const record = data as Record<string, unknown>;
    const sanitizedRecord: Record<string, unknown> = {};
    for (const [key, value] of Object.entries(record)) {
      if (SENSITIVE_PII_KEYS.has(key.toLowerCase().trim())) {
        sanitizedRecord[key] = REDACTED_PII;
      } else {
        sanitizedRecord[key] = sanitizeClientPayload(value);
      }
    }
    return sanitizedRecord as unknown as T;
  }
  return data;
}

/**
 * Manage Telemetry Consent (opt-in / opt-out).
 */
export function getTelemetryConsent(): boolean {
  if (typeof window === "undefined") return true;
  const stored = window.localStorage.getItem(CONSENT_STORAGE_KEY);
  if (stored === null) return true; // Default opt-in
  return stored === "true" || stored === "consented";
}

export function setTelemetryConsent(consented: boolean): void {
  if (typeof window === "undefined") return;
  window.localStorage.setItem(
    CONSENT_STORAGE_KEY,
    consented ? "consented" : "denied"
  );
}

/**
 * Generate unique client-side idempotency key for telemetry events.
 */
export function generateIdempotencyKey(): string {
  if (typeof crypto !== "undefined" && typeof crypto.randomUUID === "function") {
    return crypto.randomUUID();
  }
  return `idem_${Date.now()}_${Math.random().toString(36).substring(2, 12)}`;
}

export interface TrackConversionOptions {
  experienceId?: string;
  creatorId?: string;
  inquiryId?: string;
  slug?: string;
  step?: string;
  path?: string;
  isDemo?: boolean;
  isSynthetic?: boolean;
  idempotencyKey?: string;
  metadata?: Record<string, unknown>;
}

/**
 * Core event tracking dispatch with consent and PII safeguards.
 */
export async function trackEvent(
  name: string,
  payload: Record<string, unknown> = {},
  options: {
    path?: string;
    idempotencyKey?: string;
    isDemo?: boolean;
    isSynthetic?: boolean;
    consentStatus?: string;
  } = {}
): Promise<{ success: boolean; count: number; deduplicated?: boolean; opted_out?: boolean }> {
  // 1. Consent guard
  const consent = getTelemetryConsent();
  if (!consent || options.consentStatus === "denied" || options.consentStatus === "withdrawn") {
    return { success: true, count: 0, opted_out: true };
  }

  // 2. Scrub student PII
  const cleanPayload = sanitizeClientPayload(payload);

  // 3. Attach idempotency key
  const idempotencyKey = options.idempotencyKey || generateIdempotencyKey();

  const event: AnalyticsEvent = {
    name,
    payload: {
      ...cleanPayload,
      idempotency_key: idempotencyKey,
      is_demo: options.isDemo || false,
      is_synthetic: options.isSynthetic || false,
    },
    path: options.path || (typeof window !== "undefined" ? window.location.pathname : null),
    idempotency_key: idempotencyKey,
    consent_status: options.consentStatus || "consented",
    is_demo: options.isDemo || false,
    is_synthetic: options.isSynthetic || false,
  };

  try {
    const res = await logAnalyticsEvents({ events: [event] });
    return (res as { success: boolean; count: number }) || { success: true, count: 1 };
  } catch (err) {
    return { success: false, count: 0 };
  }
}

// ============================================================================
// Business Conversion Funnel Telemetry Helpers (V5-T111)
// ============================================================================

export async function trackConversionView(
  options: TrackConversionOptions
): Promise<unknown> {
  return trackEvent(
    ANALYTICS_EVENT_TYPES.VIEW,
    {
      experience_id: options.experienceId,
      creator_id: options.creatorId,
      item_slug: options.slug,
      ...(options.metadata || {}),
    },
    {
      path: options.path,
      idempotencyKey: options.idempotencyKey,
      isDemo: options.isDemo,
      isSynthetic: options.isSynthetic,
    }
  );
}

export async function trackConversionExplore(
  options: TrackConversionOptions
): Promise<unknown> {
  return trackEvent(
    ANALYTICS_EVENT_TYPES.EXPLORE,
    {
      experience_id: options.experienceId,
      creator_id: options.creatorId,
      item_slug: options.slug,
      step: options.step || "details",
      ...(options.metadata || {}),
    },
    {
      path: options.path,
      idempotencyKey: options.idempotencyKey,
      isDemo: options.isDemo,
      isSynthetic: options.isSynthetic,
    }
  );
}

export async function trackInquiryStart(
  options: TrackConversionOptions
): Promise<unknown> {
  return trackEvent(
    ANALYTICS_EVENT_TYPES.INQUIRY_START,
    {
      experience_id: options.experienceId,
      creator_id: options.creatorId,
      item_slug: options.slug,
      ...(options.metadata || {}),
    },
    {
      path: options.path,
      idempotencyKey: options.idempotencyKey,
      isDemo: options.isDemo,
      isSynthetic: options.isSynthetic,
    }
  );
}

export async function trackInquirySubmit(
  options: TrackConversionOptions
): Promise<unknown> {
  return trackEvent(
    ANALYTICS_EVENT_TYPES.INQUIRY_SUBMIT,
    {
      inquiry_id: options.inquiryId,
      experience_id: options.experienceId,
      creator_id: options.creatorId,
      ...(options.metadata || {}),
    },
    {
      path: options.path,
      idempotencyKey: options.idempotencyKey,
      isDemo: options.isDemo,
      isSynthetic: options.isSynthetic,
    }
  );
}

export async function trackInquiryConfirm(
  options: TrackConversionOptions
): Promise<unknown> {
  return trackEvent(
    ANALYTICS_EVENT_TYPES.INQUIRY_CONFIRM,
    {
      inquiry_id: options.inquiryId,
      experience_id: options.experienceId,
      ...(options.metadata || {}),
    },
    {
      path: options.path,
      idempotencyKey: options.idempotencyKey,
      isDemo: options.isDemo,
      isSynthetic: options.isSynthetic,
    }
  );
}
