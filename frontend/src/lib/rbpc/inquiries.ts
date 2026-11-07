/**
 * LƯU NIÊN — RBPC 2026: Inquiry Services, Seeds & Tracking Helpers
 * Scope: Client-side contracts, API bridges, and local persistence for visitor inquiries and partner inbox.
 * Base Specification: Master Execution Goal V2 (§5.1, §5.2, §5.3, §5.4, §6.1, §6.2) & CREATE_LEARN_SPEC.md
 */

import { apiRequest, ApiError, type ApiErrorOptions } from "@/lib/api";
import { trackInquirySubmit } from "@/lib/analytics";
import type {
  InquiryFormValues,
  InquiryStatus,
  InquiryStatusResponse,
  InquirySubmissionResult,
  PartnerInboxItem,
  PartnerInquiryUpdatePayload,
  RbpcExperience,
  ContactMethod,
  RbpcImpactMetricsOut,
  CuratorStoryRecommendationsResponse,
} from "@/types/rbpc";
import type { PartnerInboxItemWithAudit, InquiryAuditLogEntry } from "@/components/rbpc/PartnerInboxView";

// ============================================================================
// 1. Curated Experiences for Standalone Inquiries
// ============================================================================

export interface CuratedExperienceOption {
  slug: string;
  providerId: string;
  providerName: string;
  creatorSlug: string;
  creatorName: string;
  titleVi: string;
  titleEn: string;
  areaPublic: string;
  durationMinutes: number;
  pricingDisplay: string;
  maxPartySize: number;
  notice: string;
}

export const CURATED_EXPERIENCES: CuratedExperienceOption[] = [
  {
    slug: "workshop-duc-dong-phuong-duc",
    providerId: "prov-phuong-duc-01",
    providerName: "Xưởng Đúc Đồng Gia Tộc Nguyễn Văn (Phường Đúc)",
    creatorSlug: "nghe-nhan-nguyen-van-sinh",
    creatorName: "Nghệ nhân Nhân dân Nguyễn Văn Sinh",
    titleVi: "Trải nghiệm nghệ thuật nặn khuôn sáp & đúc đồng truyền thống Phường Đúc",
    titleEn: "Traditional Lost-Wax Molding & Bronze Smelting Masterclass",
    areaPublic: "Phường Đúc, Thành phố Huế",
    durationMinutes: 180,
    pricingDisplay: "Từ 650.000 VNĐ / khách",
    maxPartySize: 8,
    notice: "Yêu cầu trải nghiệm chỉ là bước đăng ký giữ chỗ và xác nhận thời gian với nghệ nhân; không thu phí trực tuyến tức thì.",
  },
  {
    slug: "workshop-phap-lam-hue",
    providerId: "prov-phap-lam-01",
    providerName: "Trung tâm Nghiên cứu & Ứng dụng Pháp lam Huế",
    creatorSlug: "nghe-nhan-do-huu-triet",
    creatorName: "Thạc sĩ - Nghệ nhân Đỗ Hữu Triết",
    titleVi: "Lớp học nghệ thuật họa Pháp lam hoàng cung trên cốt đồng",
    titleEn: "Royal Huế Vitreous Enamel Painting Masterclass",
    areaPublic: "Phường Phú Cát, Thành phố Huế",
    durationMinutes: 150,
    pricingDisplay: "Từ 550.000 VNĐ / khách",
    maxPartySize: 6,
    notice: "Yêu cầu trải nghiệm chỉ là bước liên hệ xác nhận lịch hẹn, không phải giao dịch thanh toán trực tuyến tức thì.",
  },
  {
    slug: "workshop-hoa-giay-thanh-tien",
    providerId: "prov-thanh-tien-02",
    providerName: "Cơ sở Hoa giấy Thanh Tiên - Nghệ nhân Thân Văn Huy",
    creatorSlug: "nghe-nhan-than-van-huy",
    creatorName: "Nghệ nhân Ưu tú Thân Văn Huy",
    titleVi: "Nghệ thuật hoa giấy thờ tự làng Thanh Tiên",
    titleEn: "Thanh Tiên Traditional Paper Flower Crafting",
    areaPublic: "Làng Thanh Tiên, Xã Phú Mậu, Thành phố Huế",
    durationMinutes: 120,
    pricingDisplay: "Từ 250.000 VNĐ / khách",
    maxPartySize: 10,
    notice: "Yêu cầu trải nghiệm chỉ là bước liên hệ xác nhận lịch hẹn, không phải giao dịch thanh toán trực tuyến tức thì.",
  },
];

// ============================================================================
// 2. Realistic Seed Data for Partner Inbox Management & Offline Demonstration
// ============================================================================

export const SEED_PARTNER_INQUIRIES: PartnerInboxItemWithAudit[] = [
  {
    id: "inq-001",
    reference: "INQ-7F89-A23C",
    experienceSlug: "workshop-duc-dong-phuong-duc",
    experienceTitle: "Trải nghiệm nghệ thuật nặn khuôn sáp & đúc đồng truyền thống Phường Đúc",
    providerId: "prov-phuong-duc-01",
    creatorSlug: "nghe-nhan-nguyen-van-sinh",
    creatorName: "Nghệ nhân Nhân dân Nguyễn Văn Sinh",
    contactName: "Nguyễn An Nhiên",
    contactMethod: "phone",
    contactValue: "0912345678",
    preferredDate: "2026-11-05",
    partySize: 2,
    message: "Chúng tôi là 2 bạn trẻ muốn tìm hiểu kỹ nghệ đúc chuông để nghiên cứu văn hóa Huế.",
    status: "new",
    partnerNotes: "Chưa liên hệ. Khách quan tâm kỹ thuật sáp ong.",
    createdAt: "2026-10-18T10:00:00Z",
    updatedAt: "2026-10-18T10:00:00Z",
    auditLog: [],
    isDemo: true,
    watermark: "DEMO DATA",
  },
  {
    id: "inq-002",
    reference: "INQ-6E21-B44D",
    experienceSlug: "workshop-duc-dong-phuong-duc",
    experienceTitle: "Trải nghiệm nghệ thuật nặn khuôn sáp & đúc đồng truyền thống Phường Đúc",
    providerId: "prov-phuong-duc-01",
    creatorSlug: "nghe-nhan-nguyen-van-sinh",
    creatorName: "Nghệ nhân Nhân dân Nguyễn Văn Sinh",
    contactName: "David Miller",
    contactMethod: "email",
    contactValue: "d.miller@example.com",
    preferredDate: "2026-11-08",
    partySize: 4,
    message: "Cultural heritage researchers from Australia interested in the bronze alloy acoustic tuning.",
    status: "contacted",
    partnerNotes: "Đã gửi email báo khung giờ lò nấu đồng lúc 14:00 ngày 08/11. Đang đợi xác nhận thời gian đến.",
    lastContactedAt: "2026-10-18T11:30:00Z",
    createdAt: "2026-10-18T09:30:00Z",
    updatedAt: "2026-10-18T11:30:00Z",
    auditLog: [
      {
        id: "audit-01",
        inquiryId: "inq-002",
        timestamp: "2026-10-18T11:30:00Z",
        actorName: "Xưởng Đúc Đồng Gia Tộc Nguyễn Văn",
        previousStatus: "new",
        newStatus: "contacted",
        note: "Gửi email hẹn giờ và hướng dẫn trang phục xưởng đúc",
      },
    ],
    isDemo: true,
    watermark: "DEMO DATA",
  },
  {
    id: "inq-003",
    reference: "INQ-5B10-C89E",
    experienceSlug: "workshop-phap-lam-hue",
    experienceTitle: "Lớp học nghệ thuật họa Pháp lam hoàng cung trên cốt đồng",
    providerId: "prov-phap-lam-01",
    creatorSlug: "nghe-nhan-do-huu-triet",
    creatorName: "Thạc sĩ - Nghệ nhân Đỗ Hữu Triết",
    contactName: "Trần Bảo Ngọc",
    contactMethod: "zalo",
    contactValue: "0988112233",
    preferredDate: "2026-10-28",
    partySize: 1,
    message: "Muốn học tự vẽ pháp lam họa tiết hoa sen hoàng gia làm quà kỷ niệm.",
    status: "confirmed",
    partnerNotes: "Đã chốt lịch ngày 28/10 lúc 09:00. Đã chuẩn bị sẵn phôi đồng và men màu xanh lam coban.",
    lastContactedAt: "2026-10-17T14:00:00Z",
    createdAt: "2026-10-17T08:00:00Z",
    updatedAt: "2026-10-17T14:00:00Z",
    auditLog: [
      {
        id: "audit-02",
        inquiryId: "inq-003",
        timestamp: "2026-10-17T09:15:00Z",
        actorName: "Trung tâm Pháp lam Huế",
        previousStatus: "new",
        newStatus: "contacted",
        note: "Trao đổi qua Zalo xác nhận chọn mẫu hoa sen",
      },
      {
        id: "audit-03",
        inquiryId: "inq-003",
        timestamp: "2026-10-17T14:00:00Z",
        actorName: "Trung tâm Pháp lam Huế",
        previousStatus: "contacted",
        newStatus: "confirmed",
        note: "Xác nhận lịch sáng 28/10",
      },
    ],
    isDemo: true,
    watermark: "DEMO DATA",
  },
  {
    id: "inq-004",
    reference: "INQ-4A02-D11F",
    experienceSlug: "workshop-duc-dong-phuong-duc",
    experienceTitle: "Trải nghiệm nghệ thuật nặn khuôn sáp & đúc đồng truyền thống Phường Đúc",
    providerId: "prov-phuong-duc-01",
    creatorSlug: "nghe-nhan-nguyen-van-sinh",
    creatorName: "Nghệ nhân Nhân dân Nguyễn Văn Sinh",
    contactName: "Jean Dupont",
    contactMethod: "email",
    contactValue: "j.dupont@laposte.fr",
    preferredDate: "2026-10-24",
    partySize: 6,
    message: "Group of cultural architecture students from Paris looking for a private masterclass.",
    status: "declined",
    partnerNotes: "Xưởng trùng lịch nấu mẻ đại hồng chung 2 tấn của chùa, không thể đảm bảo an toàn cho đoàn 6 người.",
    lastContactedAt: "2026-10-16T17:00:00Z",
    createdAt: "2026-10-16T15:00:00Z",
    updatedAt: "2026-10-16T17:00:00Z",
    auditLog: [
      {
        id: "audit-04",
        inquiryId: "inq-004",
        timestamp: "2026-10-16T17:00:00Z",
        actorName: "Xưởng Đúc Đồng Gia Tộc Nguyễn Văn",
        previousStatus: "new",
        newStatus: "declined",
        note: "Trùng lịch nấu đại hồng chung chùa Thiên Mụ, hẹn khách dịp sau",
      },
    ],
    isDemo: true,
    watermark: "DEMO DATA",
  },
  {
    id: "inq-005",
    reference: "INQ-3C98-E52A",
    experienceSlug: "workshop-hoa-giay-thanh-tien",
    experienceTitle: "Nghệ thuật hoa giấy thờ tự làng Thanh Tiên",
    providerId: "prov-thanh-tien-02",
    creatorSlug: "nghe-nhan-than-van-huy",
    creatorName: "Nghệ nhân Ưu tú Thân Văn Huy",
    contactName: "Phạm Hải Đăng",
    contactMethod: "phone",
    contactValue: "0903456789",
    preferredDate: "2026-11-15",
    partySize: 3,
    message: "Muốn học kỹ thuật nhuộm màu giấy thủ công từ cây cỏ tự nhiên theo lối truyền thống.",
    status: "new",
    partnerNotes: "Mới tiếp nhận hồ sơ qua cổng RBPC.",
    createdAt: "2026-10-18T14:20:00Z",
    updatedAt: "2026-10-18T14:20:00Z",
    auditLog: [],
    isDemo: true,
    watermark: "DEMO DATA",
  },
];

// ============================================================================
// 3. Client Generation Utilities (RFC 4122 v4 UUID, Opaque Non-Sequential Tokens)
// ============================================================================

export function generateClientUuid(): string {
  if (typeof crypto !== "undefined" && typeof crypto.randomUUID === "function") {
    return crypto.randomUUID();
  }
  return "xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx".replace(/[xy]/g, (c) => {
    const r = (Math.random() * 16) | 0;
    const v = c === "x" ? r : (r & 0x3) | 0x8;
    return v.toString(16);
  });
}

export function generatePublicReference(): string {
  const chars = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789";
  let part1 = "";
  let part2 = "";
  for (let i = 0; i < 4; i++) {
    part1 += chars.charAt(Math.floor(Math.random() * chars.length));
    part2 += chars.charAt(Math.floor(Math.random() * chars.length));
  }
  return `INQ-${part1}-${part2}`;
}

export function generateOpaqueToken(): string {
  const chars = "abcdef0123456789";
  let hash = "";
  for (let i = 0; i < 32; i++) {
    hash += chars.charAt(Math.floor(Math.random() * chars.length));
  }
  return `tok_sec_${hash}`;
}

export function validateEmail(email: string): boolean {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email.trim());
}

export function validatePhone(phone: string): boolean {
  const digits = phone.replace(/\D/g, "");
  return digits.length >= 8 && digits.length <= 15;
}

// ============================================================================
// 4. Local Persistence for Visitor Inquiries
// ============================================================================

export interface StoredInquiryItem {
  reference: string;
  statusToken: string;
  experienceSlug: string;
  experienceTitle: string;
  createdAt: string;
}

const STORAGE_KEY = "luunien_rbpc_inquiry_tokens";

export function getStoredInquiries(): StoredInquiryItem[] {
  if (typeof window === "undefined" || !window.localStorage) return [];
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return [];
    const parsed = JSON.parse(raw);
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
}

export function saveStoredInquiry(item: StoredInquiryItem): void {
  if (typeof window === "undefined" || !window.localStorage) return;
  try {
    const existing = getStoredInquiries();
    const deduped = [item, ...existing.filter((i) => i.reference !== item.reference)].slice(0, 10);
    localStorage.setItem(STORAGE_KEY, JSON.stringify(deduped));
  } catch {
    // Ignore quota issues
  }
}

// ============================================================================
// 5. API Call Wrappers
// ============================================================================

export interface CreateInquiryApiPayload {
  experience_slug: string;
  experience_id?: string;
  contact: {
    name: string;
    method: ContactMethod;
    value: string;
  };
  preferred_date?: string | null;
  party_size: number;
  message?: string | null;
  consent: {
    accepted: boolean;
    privacy_accepted: boolean;
    version: string;
  };
  idempotency_key: string;
}

interface BackendInquiryResponse {
  reference: string;
  status_token?: string;
  statusToken?: string;
  status: InquiryStatus;
  message: string;
  created_at?: string;
  createdAt?: string;
}

export async function submitInquiryToApi(
  payload: CreateInquiryApiPayload
): Promise<InquirySubmissionResult> {
  try {
    const res = await apiRequest<BackendInquiryResponse>("/api/v1/rbpc/inquiries", {
      method: "POST",
      body: payload,
    });

    if (!res || !res.reference) {
      throw new ApiError("Phản hồi từ máy chủ không hợp lệ.");
    }

    // Fire-and-forget consent-aware business conversion telemetry (zero PII)
    trackInquirySubmit({
      inquiryId: res.reference,
      experienceId: payload.experience_id,
      idempotencyKey: payload.idempotency_key,
    }).catch(() => null);

    return {
      reference: res.reference,
      statusToken: res.statusToken || res.status_token || "",
      status: res.status,
      message: res.message,
      createdAt: res.createdAt || res.created_at || new Date().toISOString(),
    };
  } catch (error) {
    if (error instanceof ApiError) {
      throw error;
    }
    if (error instanceof Error) {
      throw new ApiError(error.message, { data: error });
    }
    throw new ApiError("Gửi yêu cầu không thành công do lỗi mạng hoặc máy chủ.");
  }
}

export class InquiryNotFoundError extends ApiError {
  constructor(
    message: string = "Không tìm thấy hồ sơ với mã tra cứu này.",
    options: ApiErrorOptions = { status: 404 }
  ) {
    super(message, options);
    this.name = "InquiryNotFoundError";
  }
}

export async function fetchInquiryStatusByToken(
  opaqueToken: string
): Promise<InquiryStatusResponse> {
  const token = opaqueToken.trim();
  if (!token) {
    throw new InquiryNotFoundError("Mã tra cứu không được để trống.", { status: 400 });
  }

  try {
    interface BackendInquiryStatusResponse {
      reference: string;
      experience_title?: string;
      experienceTitle?: string;
      status: InquiryStatus;
      status_message?: string;
      statusMessage?: string;
      preferred_date?: string | null;
      preferredDate?: string | null;
      party_size?: number | null;
      partySize?: number | null;
      last_updated_at?: string;
      lastUpdatedAt?: string;
      created_at?: string;
      createdAt?: string;
      email_opt_in?: boolean;
      sms_opt_in?: boolean;
      is_overdue?: boolean;
      sla_due_at?: string | null;
      can_escalate?: boolean;
      escalated_at?: string | null;
      escalation_reason?: string | null;
      escalation_count?: number;
    }

    const res = await apiRequest<BackendInquiryStatusResponse>(
      `/api/v1/rbpc/inquiries/status/${encodeURIComponent(token)}`
    );

    if (!res || !res.reference) {
      throw new InquiryNotFoundError("Không tìm thấy hồ sơ với mã tra cứu này.", { status: 404 });
    }

    return {
      reference: res.reference,
      experienceTitle: res.experienceTitle || res.experience_title || "Trải nghiệm văn hóa",
      status: res.status,
      statusMessage: res.statusMessage || res.status_message || "",
      preferredDate: res.preferredDate ?? res.preferred_date ?? null,
      partySize: res.partySize ?? res.party_size ?? null,
      lastUpdatedAt: res.lastUpdatedAt || res.last_updated_at || new Date().toISOString(),
      createdAt: res.createdAt || res.created_at,
      emailOptIn: res.email_opt_in ?? true,
      smsOptIn: res.sms_opt_in ?? false,
      isOverdue: res.is_overdue ?? false,
      slaDueAt: res.sla_due_at ?? null,
      canEscalate: res.can_escalate ?? false,
      escalatedAt: res.escalated_at ?? null,
      escalationReason: res.escalation_reason ?? null,
      escalationCount: res.escalation_count ?? 0,
    };
  } catch (error) {
    if (error instanceof InquiryNotFoundError) {
      throw error;
    }

    if (error instanceof ApiError) {
      if (error.status === 404) {
        throw new InquiryNotFoundError("Không tìm thấy hồ sơ với mã tra cứu này.", {
          status: 404,
          data: error.data,
        });
      }
      throw error;
    }

    const isNetworkError =
      error instanceof TypeError ||
      (error instanceof Error &&
        (error.message.includes("Failed to fetch") ||
          error.message.includes("NetworkError") ||
          error.message.includes("fetch failed") ||
          error.message.includes("Invalid URL")));

    if (isNetworkError) {
      throw new InquiryNotFoundError("Không tìm thấy hồ sơ với mã tra cứu này.", {
        status: 404,
        data: error,
      });
    }

    if (error instanceof Error) {
      throw new InquiryNotFoundError(
        error.message.includes("404")
          ? "Không tìm thấy hồ sơ với mã tra cứu này."
          : error.message,
        { data: error }
      );
    }

    throw new InquiryNotFoundError("Không tìm thấy hồ sơ với mã tra cứu này.");
  }
}

export async function updateInquiryNotificationPreferences(
  opaqueToken: string,
  payload: {
    emailOptIn?: boolean;
    smsOptIn?: boolean;
    frequency?: string;
  }
): Promise<{
  reference: string;
  emailOptIn: boolean;
  smsOptIn: boolean;
  unsubscribed: boolean;
  message: string;
  updatedAt: string;
}> {
  const token = opaqueToken.trim();
  if (!token) {
    throw new InquiryNotFoundError("Mã tra cứu không được để trống.", { status: 400 });
  }

  interface BackendPrefOut {
    reference: string;
    email_opt_in: boolean;
    sms_opt_in: boolean;
    unsubscribed: boolean;
    message: string;
    updated_at: string;
  }

  const res = await apiRequest<BackendPrefOut>(
    `/api/v1/rbpc/inquiries/status/${encodeURIComponent(token)}/preferences`,
    {
      method: "POST",
      body: JSON.stringify({
        email_opt_in: payload.emailOptIn,
        sms_opt_in: payload.smsOptIn,
        frequency: payload.frequency,
      }),
    }
  );

  return {
    reference: res.reference,
    emailOptIn: res.email_opt_in,
    smsOptIn: res.sms_opt_in,
    unsubscribed: res.unsubscribed,
    message: res.message,
    updatedAt: res.updated_at,
  };
}

export async function unsubscribeInquiryNotifications(
  opaqueToken: string
): Promise<{
  reference: string;
  emailOptIn: boolean;
  smsOptIn: boolean;
  unsubscribed: boolean;
  message: string;
  updatedAt: string;
}> {
  const token = opaqueToken.trim();
  if (!token) {
    throw new InquiryNotFoundError("Mã tra cứu không được để trống.", { status: 400 });
  }

  interface BackendPrefOut {
    reference: string;
    email_opt_in: boolean;
    sms_opt_in: boolean;
    unsubscribed: boolean;
    message: string;
    updated_at: string;
  }

  const res = await apiRequest<BackendPrefOut>(
    `/api/v1/rbpc/inquiries/status/${encodeURIComponent(token)}/unsubscribe`,
    {
      method: "POST",
    }
  );

  return {
    reference: res.reference,
    emailOptIn: res.email_opt_in,
    smsOptIn: res.sms_opt_in,
    unsubscribed: res.unsubscribed,
    message: res.message,
    updatedAt: res.updated_at,
  };
}

export async function escalateInquiryLateResponse(
  opaqueToken: string,
  reason?: string
): Promise<{
  reference: string;
  status: InquiryStatus;
  escalatedAt: string;
  escalationCount: number;
  slaOverdueSeconds: number;
  message: string;
  notificationDispatched: boolean;
}> {
  const token = opaqueToken.trim();
  if (!token) {
    throw new InquiryNotFoundError("Mã tra cứu không được để trống.", { status: 400 });
  }

  interface BackendEscOut {
    reference: string;
    status: InquiryStatus;
    escalated_at: string;
    escalation_count: number;
    sla_overdue_seconds: number;
    message: string;
    notification_dispatched: boolean;
  }

  const res = await apiRequest<BackendEscOut>(
    `/api/v1/rbpc/inquiries/status/${encodeURIComponent(token)}/escalate`,
    {
      method: "POST",
      body: JSON.stringify({ reason: reason || null }),
    }
  );

  return {
    reference: res.reference,
    status: res.status,
    escalatedAt: res.escalated_at,
    escalationCount: res.escalation_count,
    slaOverdueSeconds: res.sla_overdue_seconds,
    message: res.message,
    notificationDispatched: res.notification_dispatched,
  };
}

export interface FetchPartnerInquiriesOptions {
  allowDemoFallback?: boolean;
}

export async function fetchPartnerInquiries(
  options?: FetchPartnerInquiriesOptions
): Promise<PartnerInboxItemWithAudit[]> {
  try {
    interface BackendPartnerList {
      items: Array<{
        id: string;
        reference: string;
        experience_slug: string;
        experience_title: string;
        contact_name: string;
        contact_method: ContactMethod;
        contact_value: string;
        preferred_date?: string | null;
        party_size: number;
        message?: string | null;
        status: InquiryStatus;
        created_at: string;
        updated_at: string;
      }>;
      total: number;
    }

    const res = await apiRequest<BackendPartnerList>("/api/v1/rbpc/partner/inquiries");
    if (res && Array.isArray(res.items)) {
      return res.items.map((item) => ({
        id: item.id,
        reference: item.reference,
        experienceSlug: item.experience_slug,
        experienceTitle: item.experience_title,
        contactName: item.contact_name,
        contactMethod: item.contact_method,
        contactValue: item.contact_value,
        preferredDate: item.preferred_date,
        partySize: item.party_size,
        message: item.message,
        status: item.status,
        createdAt: item.created_at,
        updatedAt: item.updated_at,
      }));
    }
    return [];
  } catch (error) {
    if (options?.allowDemoFallback) {
      return SEED_PARTNER_INQUIRIES;
    }
    throw error;
  }
}

export async function updatePartnerInquiryStatusApi(
  id: string,
  newStatus: InquiryStatus,
  note?: string
): Promise<void> {
  await apiRequest(`/api/v1/rbpc/partner/inquiries/${encodeURIComponent(id)}`, {
    method: "PATCH",
    body: {
      status: newStatus,
      note: note || undefined,
    },
  });
}

// ============================================================================
// Verified Reviews & Disputes API Client (V5-T107)
// ============================================================================

export interface SubmitReviewPayload {
  inquiry_token: string;
  rating: number;
  title: string;
  comment: string;
  author_display_name?: string;
}

export interface ReviewResponse {
  id: string;
  experience_id: string;
  experience_slug?: string;
  author_display_name: string;
  rating: number;
  title: string;
  comment: string;
  verified_completed: boolean;
  status: string;
  created_at: string;
  updated_at: string;
}

export interface ReviewListResponse {
  items: ReviewResponse[];
  total: number;
  average_rating: number;
}

export async function submitCustomerReviewApi(
  payload: SubmitReviewPayload
): Promise<ReviewResponse> {
  return await apiRequest<ReviewResponse>("/api/v1/rbpc/reviews", {
    method: "POST",
    body: payload,
  });
}

export async function fetchExperienceReviewsApi(
  slug: string
): Promise<ReviewListResponse> {
  return await apiRequest<ReviewListResponse>(
    `/api/v1/rbpc/experiences/${encodeURIComponent(slug)}/reviews`
  );
}

export async function fileReviewDisputeApi(
  reviewId: string,
  reason: string,
  evidencePayload?: Record<string, unknown>
): Promise<{ id: string; status: string; reason: string }> {
  return await apiRequest<{ id: string; status: string; reason: string }>(
    `/api/v1/rbpc/reviews/${encodeURIComponent(reviewId)}/dispute`,
    {
      method: "POST",
      body: {
        reason,
        evidence_payload: evidencePayload || {},
      },
    }
  );
}

// ============================================================================
// Public Impact Metrics API Client (V5-T110)
// ============================================================================

export async function fetchImpactMetricsApi(): Promise<RbpcImpactMetricsOut> {
  return await apiRequest<RbpcImpactMetricsOut>("/api/v1/rbpc/impact");
}

// ============================================================================
// Curator-Controlled Story Recommendations Client (V5-T105)
// ============================================================================

export async function fetchCuratorStoryRecommendationsApi(
  storySlug: string,
  locale: string = "vi",
  limit: number = 5
): Promise<CuratorStoryRecommendationsResponse> {
  return await apiRequest<CuratorStoryRecommendationsResponse>(
    `/api/v1/rbpc/stories/${encodeURIComponent(storySlug)}/recommendations?locale=${encodeURIComponent(locale)}&limit=${limit}`
  );
}


