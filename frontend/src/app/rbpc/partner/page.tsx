"use client";

import React, { useState, useEffect, useMemo, Suspense } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import {
  Inbox,
  ShieldCheck,
  ShieldAlert,
  Building2,
  Calendar,
  Clock,
  Sparkles,
  ArrowRight,
  LogIn,
  LogOut,
  RefreshCw,
  ExternalLink,
  ChevronRight,
  Compass,
  CheckCircle2,
  AlertCircle,
  HelpCircle,
  Filter,
  UserCheck,
  FileCheck,
  Upload,
  PlusCircle,
  Mic,
} from "lucide-react";
import type { InquiryStatus, RbpcLocale } from "@/types/rbpc";
import { getRbpcCopy } from "@/lib/rbpc/copy";
import { cn } from "@/lib/utils";
import { setPageMeta } from "@/lib/seo";
import { useAuthStore } from "@/stores/authStore";
import {
  PartnerInboxView,
  PartnerInboxItemWithAudit,
  InquiryAuditLogEntry,
} from "@/components/rbpc/PartnerInboxView";
import { CreatorConsentStudio } from "./CreatorConsentStudio";
import { RbpcButton } from "@/components/rbpc/RbpcButton";
import { RbpcCard } from "@/components/rbpc/RbpcCard";
import {
  SEED_PARTNER_INQUIRIES,
  fetchPartnerInquiries,
  updatePartnerInquiryStatusApi,
} from "@/lib/rbpc/inquiries";

const PROVIDER_OPTIONS = [
  {
    id: "all",
    nameVi: "Tất cả cơ sở đối tác (Toàn quyền)",
    nameEn: "All Partner Workshops (Global View)",
  },
  {
    id: "prov-phuong-duc-01",
    nameVi: "Xưởng Đúc Đồng Gia Tộc Nguyễn Văn (Phường Đúc)",
    nameEn: "Nguyen Van Bronze Foundry (Phuong Duc Guild)",
  },
  {
    id: "prov-phap-lam-01",
    nameVi: "Trung tâm Nghiên cứu & Ứng dụng Pháp lam Huế",
    nameEn: "Hue Vitreous Enamel Art Center",
  },
  {
    id: "prov-thanh-tien-02",
    nameVi: "Cơ sở Hoa giấy Thanh Tiên - Nghệ nhân Thân Văn Huy",
    nameEn: "Thanh Tien Paper Lotus Workshop - Artisan Than Van Huy",
  },
];

function PartnerDashboardContent() {
  const searchParams = useSearchParams();
  const providerParam = searchParams?.get("provider") || "prov-phuong-duc-01";
  const isDemoParam = searchParams?.get("demo") === "true" || searchParams?.get("demo") === "1";

  const [locale, setLocale] = useState<RbpcLocale>("vi");
  const copy = getRbpcCopy(locale);

  // Authentication store
  const authStatus = useAuthStore((s) => s.status);
  const user = useAuthStore((s) => s.user);
  const isAuthenticated = authStatus === "authed" && Boolean(user);
  const isStaffOrPartner =
    user?.role === "partner" || user?.role === "admin" || user?.role === "staff";

  // In demo mode only if unauthenticated OR explicitly requested via ?demo=true
  const isDemoMode = !isAuthenticated || isDemoParam;

  // Active provider selection (for multi-tenant isolation demonstration)
  const [selectedProviderId, setSelectedProviderId] = useState<string>(
    user?.id ? user.id : providerParam
  );

  // Navigation tabs: "inbox" | "onboarding" | "experience" | "oral_history"
  const [activeTab, setActiveTab] = useState<"inbox" | "onboarding" | "experience" | "oral_history">("inbox");

  // Onboarding & Profile Form State
  const [profileData, setProfileData] = useState<{
    slug: string;
    public_name: string;
    craft_tradition_vi: string;
    craft_tradition_en: string;
    approved_bio_vi: string;
    approved_bio_en: string;
    approved_portrait_url: string;
    public_region: string;
    years_of_practice: number | "";
    generation_lineage: string;
    display_consent_ref: string;
    identity_document_ref: string;
    rights_clearance_notes: string;
    is_verified?: boolean;
    consent_status?: string;
  }>({
    slug: "",
    public_name: "",
    craft_tradition_vi: "",
    craft_tradition_en: "",
    approved_bio_vi: "",
    approved_bio_en: "",
    approved_portrait_url: "",
    public_region: "Huế",
    years_of_practice: "",
    generation_lineage: "",
    display_consent_ref: "",
    identity_document_ref: "",
    rights_clearance_notes: "",
  });
  const [hasExistingProfile, setHasExistingProfile] = useState<boolean>(false);
  const [isSubmittingProfile, setIsSubmittingProfile] = useState(false);

  // Experience Listing Form State
  const [expFormData, setExpFormData] = useState<{
    slug: string;
    title_vi: string;
    title_en: string;
    description_vi: string;
    description_en: string;
    area_public: string;
    duration_minutes: number | "";
    pricing_display: string;
    indicative_price_amount: number | "";
    max_party_size: number | "";
  }>({
    slug: "",
    title_vi: "",
    title_en: "",
    description_vi: "",
    description_en: "",
    area_public: "Huế",
    duration_minutes: 90,
    pricing_display: "Từ 250.000 VNĐ / khách",
    indicative_price_amount: 250000,
    max_party_size: 10,
  });
  const [isSubmittingExp, setIsSubmittingExp] = useState(false);

  // Inquiries State - Initialized as empty array [] (no seed data in production)
  const [inquiries, setInquiries] = useState<PartnerInboxItemWithAudit[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isRefreshing, setIsRefreshing] = useState(false);

  // Feedback alert banner state
  const [dashboardAlert, setDashboardAlert] = useState<{
    type: "success" | "error" | "info";
    message: string;
  } | null>(null);

  // Sync selected provider if authenticated user becomes available
  useEffect(() => {
    if (isAuthenticated && user?.id) {
      setSelectedProviderId(user.id);
    }
  }, [isAuthenticated, user?.id]);

  // Set Page SEO & Title
  useEffect(() => {
    setPageMeta({
      title:
        locale === "vi"
          ? "Bảng điều khiển hộp thư đối tác — LƯU NIÊN RBPC 2026"
          : "Partner Inquiry Inbox Dashboard — LƯU NIÊN RBPC 2026",
      description:
        locale === "vi"
          ? "Hệ thống quản lý yêu cầu trải nghiệm văn hóa dành cho nghệ nhân và xưởng nghề Huế, tuân thủ phân quyền đa người thuê và bảo mật thông tin."
          : "Multi-tenant partner inquiry management inbox for Hue artisans and workshop operators with strict privacy isolation.",
      path: "/rbpc/partner",
    });
  }, [locale]);

  // Load inquiries (from API or seed fallback only in demo mode)
  const loadInquiries = async () => {
    if (isDemoMode) {
      setInquiries(SEED_PARTNER_INQUIRIES);
      return;
    }

    setIsRefreshing(true);
    try {
      const items = await fetchPartnerInquiries();
      setInquiries(items);
    } catch (err) {
      setInquiries([]);
      setDashboardAlert({
        type: "error",
        message:
          err instanceof Error
            ? err.message
            : locale === "vi"
            ? "Không thể tải danh sách yêu cầu từ máy chủ. Vui lòng thử lại sau."
            : "Failed to load inquiries from server. Please try again later.",
      });
    } finally {
      setIsRefreshing(false);
    }
  };

  useEffect(() => {
    if (authStatus === "checking") return;
    loadInquiries();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [authStatus, isAuthenticated, isDemoMode, user?.id]);

  // Active provider name
  const currentProvider = useMemo(() => {
    if (isAuthenticated && user?.display_name) {
      return {
        id: user.id,
        nameVi: user.display_name,
        nameEn: user.display_name,
      };
    }
    const found = PROVIDER_OPTIONS.find((p) => p.id === selectedProviderId);
    return found || PROVIDER_OPTIONS[1];
  }, [isAuthenticated, user, selectedProviderId]);

  // Inquiries scoped to selected provider for stats
  const providerScopedInquiries = useMemo(() => {
    if (selectedProviderId === "all") return inquiries;
    return inquiries.filter(
      (item) => !item.providerId || item.providerId === selectedProviderId
    );
  }, [inquiries, selectedProviderId]);

  // Aggregate Metrics for Top Ribbon
  const metrics = useMemo(() => {
    const total = providerScopedInquiries.length;
    const newCount = providerScopedInquiries.filter((i) => i.status === "new").length;
    const contactedCount = providerScopedInquiries.filter(
      (i) => i.status === "contacted"
    ).length;
    const confirmedCount = providerScopedInquiries.filter(
      (i) => i.status === "confirmed"
    ).length;
    const closedCount = providerScopedInquiries.filter(
      (i) => i.status === "closed" || i.status === "declined"
    ).length;

    return { total, newCount, contactedCount, confirmedCount, closedCount };
  }, [providerScopedInquiries]);

  // Status Change Callback
  const handleStatusChange = async (
    inquiryId: string,
    newStatus: InquiryStatus,
    note?: string
  ) => {
    // Snapshot previous state for rollback
    const previousInquiries = inquiries;
    const targetItem = inquiries.find((i) => i.id === inquiryId);
    const previousStatus = targetItem?.status;

    // Optimistically update local inquiry list
    const now = new Date().toISOString();
    const newAudit: InquiryAuditLogEntry = {
      id: `audit-${Date.now()}`,
      inquiryId,
      timestamp: now,
      actorName:
        locale === "vi" ? currentProvider.nameVi : currentProvider.nameEn,
      previousStatus: previousStatus || "new",
      newStatus,
      note,
    };

    setInquiries((prev) =>
      prev.map((item) => {
        if (item.id === inquiryId) {
          return {
            ...item,
            status: newStatus,
            updatedAt: now,
            lastContactedAt: newStatus === "contacted" ? now : item.lastContactedAt,
            auditLog: [newAudit, ...(item.auditLog || [])],
          };
        }
        return item;
      })
    );

    try {
      // 1. Call backend API endpoint
      await updatePartnerInquiryStatusApi(inquiryId, newStatus, note);

      const targetLabel =
        newStatus === "contacted"
          ? locale === "vi" ? "Đã liên hệ" : "Contacted"
          : newStatus === "confirmed"
          ? locale === "vi" ? "Đã xác nhận" : "Confirmed"
          : newStatus === "declined"
          ? locale === "vi" ? "Đã từ chối" : "Declined"
          : newStatus === "closed"
          ? locale === "vi" ? "Đã đóng" : "Closed"
          : newStatus;

      setDashboardAlert({
        type: "success",
        message:
          locale === "vi"
            ? `Thao tác thành công: Hồ sơ đã được chuyển sang trạng thái "${targetLabel}".`
            : `Operation successful: Inquiry updated to "${targetLabel}".`,
      });
    } catch (err) {
      // Rollback: revert the local item status back to its previous status
      setInquiries(previousInquiries);

      setDashboardAlert({
        type: "error",
        message:
          err instanceof Error
            ? err.message
            : locale === "vi"
            ? "Không thể chuyển trạng thái hồ sơ. Vui lòng thử lại sau."
            : "Failed to transition inquiry status. Please try again later.",
      });
      throw err;
    }
  };

  // Internal Notes Save Callback
  const handleSaveNotes = (inquiryId: string, notes: string) => {
    const now = new Date().toISOString();
    setInquiries((prev) =>
      prev.map((item) => {
        if (item.id === inquiryId) {
          return {
            ...item,
            partnerNotes: notes,
            updatedAt: now,
          };
        }
        return item;
      })
    );

    setDashboardAlert({
      type: "success",
      message:
        locale === "vi"
          ? "Đã lưu ghi chú nội bộ thành công."
          : "Internal studio notes saved successfully.",
    });
  };

  return (
    <div className="rbpc-theme min-h-screen bg-[var(--rbpc-bg)] text-[var(--rbpc-ink)] py-8 px-4 sm:px-6 lg:px-8">
      <div className="mx-auto max-w-7xl space-y-8">
        {/* Navigation Breadcrumb & Console Header Bar */}
        <div className="flex flex-wrap items-center justify-between gap-4 border-b border-[var(--rbpc-divider-subtle)] pb-4">
          <nav aria-label="Breadcrumb" className="flex items-center gap-2 text-xs text-[var(--rbpc-muted)]">
            <Link
              href="/explore"
              className="hover:text-[var(--rbpc-primary)] flex items-center gap-1 transition-colors"
            >
              <Compass className="h-3.5 w-3.5" aria-hidden="true" />
              <span>{copy.nav.discover}</span>
            </Link>
            <ChevronRight className="h-3 w-3" aria-hidden="true" />
            <Link
              href="/rbpc/inquiries"
              className="hover:text-[var(--rbpc-primary)] transition-colors"
            >
              {locale === "vi" ? "Yêu cầu trải nghiệm" : "Inquiries"}
            </Link>
            <ChevronRight className="h-3 w-3" aria-hidden="true" />
            <span className="font-semibold text-[var(--rbpc-ink)]">
              {locale === "vi" ? "Hộp thư đối tác" : "Partner Console"}
            </span>
          </nav>

          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={() => setLocale(locale === "vi" ? "en" : "vi")}
              className="inline-flex items-center gap-1.5 rounded-full border border-[var(--rbpc-divider)] bg-[var(--rbpc-surface)] px-3 py-1 text-xs font-semibold text-[var(--rbpc-ink)] hover:border-[var(--rbpc-primary-border)] transition-colors"
              aria-label="Toggle language"
            >
              <span>{locale === "vi" ? "English" : "Tiếng Việt"}</span>
            </button>

            <button
              type="button"
              onClick={loadInquiries}
              disabled={isRefreshing}
              className="inline-flex items-center gap-1.5 rounded-full border border-[var(--rbpc-divider)] bg-[var(--rbpc-surface)] px-3 py-1 text-xs font-semibold text-[var(--rbpc-ink)] hover:border-[var(--rbpc-primary-border)] disabled:opacity-50 transition-colors"
              title={locale === "vi" ? "Làm mới dữ liệu" : "Refresh data"}
            >
              <RefreshCw
                className={cn("h-3.5 w-3.5", isRefreshing && "animate-spin text-[var(--rbpc-primary)]")}
              />
              <span>{locale === "vi" ? "Làm mới" : "Refresh"}</span>
            </button>

            <Link
              href="/rbpc/impact"
              className="inline-flex items-center gap-1.5 rounded-full border border-[var(--rbpc-divider)] bg-[var(--rbpc-surface)] px-3 py-1 text-xs font-semibold text-[var(--rbpc-ink)] hover:border-[var(--rbpc-primary-border)] transition-colors"
            >
              <span>{locale === "vi" ? "Bảng tác động" : "Impact"}</span>
            </Link>

            {isAuthenticated ? (
              <span className="inline-flex items-center gap-1.5 rounded-full border border-emerald-500/30 bg-emerald-500/10 px-3 py-1 text-xs font-semibold text-emerald-800 dark:text-emerald-300">
                <ShieldCheck className="h-3.5 w-3.5" />
                <span>{user?.username || "Đã đăng nhập"}</span>
              </span>
            ) : (
              <Link
                href="/login"
                className="inline-flex items-center gap-1.5 rounded-full border border-[var(--rbpc-primary-border)] bg-[var(--rbpc-primary-subtle)] px-3 py-1 text-xs font-semibold text-[var(--rbpc-primary)] hover:bg-[var(--rbpc-primary)] hover:text-white transition-all"
              >
                <LogIn className="h-3.5 w-3.5" />
                <span>{locale === "vi" ? "Đăng nhập đối tác" : "Partner Login"}</span>
              </Link>
            )}
          </div>
        </div>

        {/* Dashboard Title & Multi-Tenant Switcher */}
        <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
          <div className="space-y-2">
            <div className="inline-flex items-center gap-2 rounded-full border border-[var(--rbpc-primary-border)] bg-[var(--rbpc-primary-subtle)] px-3 py-1 text-xs font-semibold text-[var(--rbpc-primary)]">
              <Building2 className="h-3.5 w-3.5" aria-hidden="true" />
              <span>
                {locale === "vi"
                  ? "Cổng điều phối lịch trải nghiệm đối tác làng nghề Huế"
                  : "Huế Artisan Workshop Booking & Availability Operations"}
              </span>
            </div>

            <h1 className="font-serif text-2xl sm:text-3xl lg:text-4xl font-bold tracking-tight text-[var(--rbpc-ink)]">
              {locale === "vi" ? "Hộp Thư Tiếp Nhận Đối Tác" : "Partner Inquiries Inbox"}
            </h1>
            <p className="text-xs sm:text-sm text-[var(--rbpc-ink-subtle)] max-w-2xl leading-relaxed">
              {locale === "vi"
                ? "Theo dõi các yêu cầu đăng ký lịch trải nghiệm văn hóa, bảo vệ thông tin liên hệ của khách tham quan và thực hiện chuyển trạng thái hồ sơ minh bạch."
                : "Manage inbound experience requests, preserve visitor PII via progressive unmasking, and advance inquiries through the verified lifecycle state machine."}
            </p>
          </div>

          {/* Provider Scoping Selector (Multi-Tenant Isolation Demo) */}
          <div className="space-y-1.5 min-w-[280px]">
            <label
              htmlFor="partner-provider-select"
              className="block text-xs font-semibold text-[var(--rbpc-muted)]"
            >
              {locale === "vi"
                ? "Tài khoản cơ sở đối tác (Multi-tenant):"
                : "Active Workshop Account (Multi-tenant):"}
            </label>
            <select
              id="partner-provider-select"
              value={selectedProviderId}
              onChange={(e) => setSelectedProviderId(e.target.value)}
              disabled={isAuthenticated && !isStaffOrPartner}
              className="rbpc-select w-full text-xs font-medium"
            >
              {PROVIDER_OPTIONS.map((opt) => (
                <option key={opt.id} value={opt.id}>
                  {locale === "vi" ? opt.nameVi : opt.nameEn}
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Responsive Dashboard Alert Banner */}
        {dashboardAlert && (
          <div
            role="status"
            aria-live="polite"
            className={cn(
              "flex items-center justify-between rounded-xl p-3.5 text-xs font-medium border transition-all duration-200",
              dashboardAlert.type === "success" &&
                "border-emerald-600/30 bg-emerald-500/10 text-emerald-900 dark:text-emerald-300",
              dashboardAlert.type === "error" &&
                "border-rose-600/30 bg-rose-500/10 text-rose-900 dark:text-rose-300",
              dashboardAlert.type === "info" &&
                "border-blue-600/30 bg-blue-500/10 text-blue-900 dark:text-blue-300"
            )}
          >
            <div className="flex items-center gap-2">
              {dashboardAlert.type === "success" && (
                <CheckCircle2 className="h-4 w-4 shrink-0 text-emerald-600" aria-hidden="true" />
              )}
              {dashboardAlert.type === "error" && (
                <AlertCircle className="h-4 w-4 shrink-0 text-rose-600" aria-hidden="true" />
              )}
              {dashboardAlert.type === "info" && (
                <HelpCircle className="h-4 w-4 shrink-0 text-blue-600" aria-hidden="true" />
              )}
              <span>{dashboardAlert.message}</span>
            </div>
            <button
              type="button"
              onClick={() => setDashboardAlert(null)}
              className="inline-flex min-h-[36px] min-w-[36px] items-center justify-center rounded-md text-xs hover:opacity-75 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--rbpc-focus)]"
              aria-label={locale === "vi" ? "Đóng thông báo" : "Dismiss notification"}
            >
              ✕
            </button>
          </div>
        )}

        {/* Preview / Offline Mode Alert Banner (If not logged in as partner or in demo mode) */}
        {isDemoMode ? (
          <div className="flex items-start gap-3 rounded-xl border border-amber-500/30 bg-amber-500/10 p-4 text-xs text-amber-900 dark:text-amber-200">
            <HelpCircle className="h-4 w-4 shrink-0 mt-0.5 text-amber-600" aria-hidden="true" />
            <div className="space-y-1">
              <div className="flex items-center gap-2">
                <span className="rounded bg-amber-600 px-1.5 py-0.5 text-[10px] font-black tracking-wider text-white uppercase">
                  DEMO DATA
                </span>
                <strong className="font-semibold">
                  {locale === "vi"
                    ? "Chế độ xem trước tính năng (Partner Preview Mode):"
                    : "Partner Preview Mode Active:"}
                </strong>
              </div>
              <p className="leading-relaxed">
                {locale === "vi"
                  ? "Bạn đang trải nghiệm giao diện quản trị với dữ liệu mẫu mô phỏng 3 xưởng nghề truyền thống (Phường Đúc, Pháp Lam, Thanh Tiên). Dữ liệu này được cô lập hoàn toàn và không ảnh hưởng đến cơ sở dữ liệu thật."
                  : "You are currently viewing interactive sample data simulating 3 traditional workshops. This data is strictly isolated and does not affect live production databases."}
              </p>
            </div>
          </div>
        ) : (
          <div className="flex items-center justify-between rounded-xl border border-slate-500/20 bg-slate-500/5 px-4 py-2.5 text-xs text-[var(--rbpc-ink-subtle)]">
            <div className="flex items-center gap-2">
              <ShieldCheck className="h-4 w-4 text-emerald-600" />
              <span>
                {locale === "vi"
                  ? "Chế độ sản xuất: Không gian người thuê được bảo vệ nghiêm ngặt (Strict Tenant Isolation Enforced)."
                  : "Production Mode: Strict Tenant Isolation Enforced."}
              </span>
            </div>
            <span className="rounded border border-emerald-500/30 bg-emerald-500/10 px-2 py-0.5 text-[10px] font-bold text-emerald-800 dark:text-emerald-300 uppercase">
              LIVE TENANT
            </span>
          </div>
        )}

        {/* Top Operational Metrics Ribbon */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 sm:gap-4">
          <RbpcCard elevation="surface" padding="sm" className="space-y-1">
            <span className="block text-[11px] font-semibold text-[var(--rbpc-muted)] uppercase tracking-wider">
              {locale === "vi" ? "Tổng yêu cầu" : "Total Inquiries"}
            </span>
            <div className="flex items-baseline justify-between">
              <span className="font-mono text-2xl font-bold text-[var(--rbpc-ink)]">
                {metrics.total}
              </span>
              <span className="text-xs text-[var(--rbpc-muted)]">
                {locale === "vi" ? "hồ sơ" : "records"}
              </span>
            </div>
          </RbpcCard>

          <RbpcCard elevation="surface" padding="sm" className="space-y-1 border-l-4 border-l-blue-600">
            <span className="block text-[11px] font-semibold text-blue-700 dark:text-blue-400 uppercase tracking-wider">
              {locale === "vi" ? "Mới tiếp nhận" : "Newly Received"}
            </span>
            <div className="flex items-baseline justify-between">
              <span className="font-mono text-2xl font-bold text-blue-800 dark:text-blue-300">
                {metrics.newCount}
              </span>
              <span className="rounded-full bg-blue-500/10 px-2 py-0.5 text-[10px] font-bold text-blue-800">
                {locale === "vi" ? "Cần xử lý" : "Action Req."}
              </span>
            </div>
          </RbpcCard>

          <RbpcCard elevation="surface" padding="sm" className="space-y-1 border-l-4 border-l-amber-600">
            <span className="block text-[11px] font-semibold text-amber-700 dark:text-amber-400 uppercase tracking-wider">
              {locale === "vi" ? "Đang liên hệ" : "Contacted"}
            </span>
            <div className="flex items-baseline justify-between">
              <span className="font-mono text-2xl font-bold text-amber-800 dark:text-amber-300">
                {metrics.contactedCount}
              </span>
              <span className="text-xs text-[var(--rbpc-muted)]">
                {locale === "vi" ? "đang trao đổi" : "in progress"}
              </span>
            </div>
          </RbpcCard>

          <RbpcCard elevation="surface" padding="sm" className="space-y-1 border-l-4 border-l-emerald-600">
            <span className="block text-[11px] font-semibold text-emerald-700 dark:text-emerald-400 uppercase tracking-wider">
              {locale === "vi" ? "Đã xác nhận" : "Confirmed"}
            </span>
            <div className="flex items-baseline justify-between">
              <span className="font-mono text-2xl font-bold text-emerald-800 dark:text-emerald-300">
                {metrics.confirmedCount}
              </span>
              <span className="text-xs text-emerald-700 font-semibold">
                {locale === "vi" ? "thành công" : "scheduled"}
              </span>
            </div>
          </RbpcCard>
        </div>

        {/* Navigation Tabs */}
        <div className="flex border-b border-[var(--rbpc-divider)] gap-2">
          <button
            type="button"
            onClick={() => setActiveTab("inbox")}
            className={cn(
              "flex items-center gap-2 px-4 py-2.5 text-xs sm:text-sm font-semibold border-b-2 transition-all",
              activeTab === "inbox"
                ? "border-[var(--rbpc-primary)] text-[var(--rbpc-primary)]"
                : "border-transparent text-[var(--rbpc-ink-subtle)] hover:text-[var(--rbpc-ink)]"
            )}
          >
            <Inbox className="h-4 w-4" />
            <span>{locale === "vi" ? "Hộp thư tiếp nhận" : "Inquiries Inbox"}</span>
          </button>
          <button
            type="button"
            onClick={() => setActiveTab("onboarding")}
            className={cn(
              "flex items-center gap-2 px-4 py-2.5 text-xs sm:text-sm font-semibold border-b-2 transition-all",
              activeTab === "onboarding"
                ? "border-[var(--rbpc-primary)] text-[var(--rbpc-primary)]"
                : "border-transparent text-[var(--rbpc-ink-subtle)] hover:text-[var(--rbpc-ink)]"
            )}
          >
            <UserCheck className="h-4 w-4" />
            <span>{locale === "vi" ? "Hồ sơ nghệ nhân & Xác thực" : "Artisan Profile & Verification"}</span>
          </button>
          <button
            type="button"
            onClick={() => setActiveTab("experience")}
            className={cn(
              "flex items-center gap-2 px-4 py-2.5 text-xs sm:text-sm font-semibold border-b-2 transition-all",
              activeTab === "experience"
                ? "border-[var(--rbpc-primary)] text-[var(--rbpc-primary)]"
                : "border-transparent text-[var(--rbpc-ink-subtle)] hover:text-[var(--rbpc-ink)]"
            )}
          >
            <FileCheck className="h-4 w-4" />
            <span>{locale === "vi" ? "Đăng ký trải nghiệm" : "Register Experience"}</span>
          </button>
          <button
            type="button"
            onClick={() => setActiveTab("oral_history")}
            className={cn(
              "flex items-center gap-2 px-4 py-2.5 text-xs sm:text-sm font-semibold border-b-2 transition-all",
              activeTab === "oral_history"
                ? "border-[var(--rbpc-primary)] text-[var(--rbpc-primary)]"
                : "border-transparent text-[var(--rbpc-ink-subtle)] hover:text-[var(--rbpc-ink)]"
            )}
          >
            <Mic className="h-4 w-4" />
            <span>{locale === "vi" ? "Lịch sử truyền khẩu & Đồng thuận" : "Oral History Studio"}</span>
          </button>
        </div>

        {activeTab === "inbox" ? (
          <>
            {/* Embedded Core PartnerInboxView Component */}
            <div className="space-y-4">
              <PartnerInboxView
                inquiries={inquiries}
                providerId={selectedProviderId === "all" ? undefined : selectedProviderId}
                providerName={locale === "vi" ? currentProvider.nameVi : currentProvider.nameEn}
                locale={locale}
                onStatusChange={handleStatusChange}
                onSaveNotes={handleSaveNotes}
              />
            </div>
          </>
        ) : activeTab === "onboarding" ? (
          <div className="space-y-6">
            <RbpcCard elevation="surface" padding="responsive" className="space-y-4">
              <div className="flex items-center justify-between border-b border-[var(--rbpc-divider)] pb-3">
                <div className="space-y-1">
                  <h3 className="font-serif text-lg font-bold text-[var(--rbpc-ink)]">
                    {locale === "vi"
                      ? "Đăng ký & Cập nhật Hồ sơ Nghệ nhân (Artisan Self-Onboarding)"
                      : "Artisan Profile Self-Onboarding & Identity Review"}
                  </h3>
                  <p className="text-xs text-[var(--rbpc-ink-subtle)]">
                    {locale === "vi"
                      ? "Chân dung và thông tin xuất bản sẽ được nhân sự kiểm tra giấy phép và văn bản đồng thuận trước khi hiển thị công khai."
                      : "Portraits and bios require staff identity, rights, and consent verification before public publication."}
                  </p>
                </div>
                {profileData.is_verified ? (
                  <span className="inline-flex items-center gap-1.5 rounded-full border border-emerald-500/30 bg-emerald-500/10 px-3 py-1 text-xs font-semibold text-emerald-800">
                    <ShieldCheck className="h-3.5 w-3.5" />
                    <span>{locale === "vi" ? "Đã xác thực" : "Verified"}</span>
                  </span>
                ) : (
                  <span className="inline-flex items-center gap-1.5 rounded-full border border-amber-500/30 bg-amber-500/10 px-3 py-1 text-xs font-semibold text-amber-800">
                    <AlertCircle className="h-3.5 w-3.5" />
                    <span>{locale === "vi" ? "Chờ nhân viên duyệt" : "Pending Staff Verification"}</span>
                  </span>
                )}
              </div>

              <form
                onSubmit={async (e) => {
                  e.preventDefault();
                  setIsSubmittingProfile(true);
                  try {
                    const endpoint = hasExistingProfile
                      ? "/api/v1/rbpc/partner/profile"
                      : "/api/v1/rbpc/partner/onboarding";
                    const method = hasExistingProfile ? "PUT" : "POST";
                    const res = await fetch(endpoint, {
                      method,
                      headers: { "Content-Type": "application/json" },
                      body: JSON.stringify({
                        slug: profileData.slug,
                        public_name: profileData.public_name,
                        craft_tradition_vi: profileData.craft_tradition_vi,
                        approved_bio_vi: profileData.approved_bio_vi,
                        approved_portrait_url: profileData.approved_portrait_url || undefined,
                        years_of_practice: Number(profileData.years_of_practice) || undefined,
                        generation_lineage: profileData.generation_lineage || undefined,
                        display_consent_ref: profileData.display_consent_ref || undefined,
                        identity_document_ref: profileData.identity_document_ref || undefined,
                        rights_clearance_notes: profileData.rights_clearance_notes || undefined,
                      }),
                    });
                    if (!res.ok) {
                      const err = await res.json().catch(() => ({}));
                      throw new Error(err?.error?.message || "Lỗi lưu hồ sơ đối tác");
                    }
                    const saved = await res.json();
                    setProfileData((prev) => ({
                      ...prev,
                      ...saved,
                      is_verified: saved.is_verified,
                      consent_status: saved.consent_status,
                    }));
                    setHasExistingProfile(true);
                    setDashboardAlert({
                      type: "success",
                      message: locale === "vi" ? "Đã gửi hồ sơ nghệ nhân thành công!" : "Profile submitted successfully!",
                    });
                  } catch (err) {
                    setDashboardAlert({
                      type: "error",
                      message: err instanceof Error ? err.message : "Thao tác thất bại",
                    });
                  } finally {
                    setIsSubmittingProfile(false);
                  }
                }}
                className="space-y-4"
              >
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="space-y-1">
                    <label className="text-xs font-semibold text-[var(--rbpc-ink)]">
                      {locale === "vi" ? "Mã định danh (Slug)" : "Unique Slug"} *
                    </label>
                    <input
                      type="text"
                      required
                      disabled={hasExistingProfile}
                      value={profileData.slug}
                      onChange={(e) => setProfileData({ ...profileData, slug: e.target.value })}
                      placeholder="vd: nghe-nhan-nguyen-van-a"
                      className="w-full rounded-md border border-[var(--rbpc-divider)] bg-[var(--rbpc-surface)] px-3 py-2 text-xs text-[var(--rbpc-ink)] disabled:opacity-50"
                    />
                  </div>
                  <div className="space-y-1">
                    <label className="text-xs font-semibold text-[var(--rbpc-ink)]">
                      {locale === "vi" ? "Họ tên Nghệ nhân / Xưởng" : "Artisan / Workshop Name"} *
                    </label>
                    <input
                      type="text"
                      required
                      value={profileData.public_name}
                      onChange={(e) => setProfileData({ ...profileData, public_name: e.target.value })}
                      placeholder="vd: Nghệ nhân Nguyễn Văn A"
                      className="w-full rounded-md border border-[var(--rbpc-divider)] bg-[var(--rbpc-surface)] px-3 py-2 text-xs text-[var(--rbpc-ink)]"
                    />
                  </div>
                  <div className="space-y-1">
                    <label className="text-xs font-semibold text-[var(--rbpc-ink)]">
                      {locale === "vi" ? "Nghề truyền thống" : "Traditional Craft"} *
                    </label>
                    <input
                      type="text"
                      required
                      value={profileData.craft_tradition_vi}
                      onChange={(e) => setProfileData({ ...profileData, craft_tradition_vi: e.target.value })}
                      placeholder="vd: Đúc đồng Phường Đúc"
                      className="w-full rounded-md border border-[var(--rbpc-divider)] bg-[var(--rbpc-surface)] px-3 py-2 text-xs text-[var(--rbpc-ink)]"
                    />
                  </div>
                  <div className="space-y-1">
                    <label className="text-xs font-semibold text-[var(--rbpc-ink)]">
                      {locale === "vi" ? "Đường dẫn ảnh chân dung (URL)" : "Portrait Image URL"}
                    </label>
                    <input
                      type="url"
                      value={profileData.approved_portrait_url}
                      onChange={(e) => setProfileData({ ...profileData, approved_portrait_url: e.target.value })}
                      placeholder="https://... (ảnh cần nhân sự kiểm duyệt bản quyền)"
                      className="w-full rounded-md border border-[var(--rbpc-divider)] bg-[var(--rbpc-surface)] px-3 py-2 text-xs text-[var(--rbpc-ink)]"
                    />
                  </div>
                </div>

                <div className="space-y-1">
                  <label className="text-xs font-semibold text-[var(--rbpc-ink)]">
                    {locale === "vi" ? "Tiểu sử & Quá trình làm nghề" : "Artisan Bio & Lineage"} *
                  </label>
                  <textarea
                    required
                    rows={3}
                    value={profileData.approved_bio_vi}
                    onChange={(e) => setProfileData({ ...profileData, approved_bio_vi: e.target.value })}
                    placeholder="Mô tả truyền thống gia tộc, số năm gắn bó với nghề..."
                    className="w-full rounded-md border border-[var(--rbpc-divider)] bg-[var(--rbpc-surface)] px-3 py-2 text-xs text-[var(--rbpc-ink)]"
                  />
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="space-y-1">
                    <label className="text-xs font-semibold text-[var(--rbpc-ink)]">
                      {locale === "vi" ? "Mã văn bản đồng thuận (Consent Ref)" : "Consent Agreement Ref"}
                    </label>
                    <input
                      type="text"
                      value={profileData.display_consent_ref}
                      onChange={(e) => setProfileData({ ...profileData, display_consent_ref: e.target.value })}
                      placeholder="HĐ-ĐONGTHUAN-2026-001"
                      className="w-full rounded-md border border-[var(--rbpc-divider)] bg-[var(--rbpc-surface)] px-3 py-2 text-xs text-[var(--rbpc-ink)]"
                    />
                  </div>
                  <div className="space-y-1">
                    <label className="text-xs font-semibold text-[var(--rbpc-ink)]">
                      {locale === "vi" ? "Mã số định danh/CMND xác thực" : "Identity Verification Document Ref"}
                    </label>
                    <input
                      type="text"
                      value={profileData.identity_document_ref}
                      onChange={(e) => setProfileData({ ...profileData, identity_document_ref: e.target.value })}
                      placeholder="ID-REF-XXXX"
                      className="w-full rounded-md border border-[var(--rbpc-divider)] bg-[var(--rbpc-surface)] px-3 py-2 text-xs text-[var(--rbpc-ink)]"
                    />
                  </div>
                </div>

                <div className="flex justify-end pt-2">
                  <RbpcButton type="submit" disabled={isSubmittingProfile} variant="primary" size="sm">
                    {isSubmittingProfile
                      ? locale === "vi" ? "Đang gửi..." : "Saving..."
                      : hasExistingProfile
                      ? locale === "vi" ? "Cập nhật hồ sơ" : "Update Profile"
                      : locale === "vi" ? "Đăng ký xác thực" : "Submit for Verification"}
                  </RbpcButton>
                </div>
              </form>
            </RbpcCard>
          </div>
        ) : activeTab === "experience" ? (
          <div className="space-y-6">
            <RbpcCard elevation="surface" padding="responsive" className="space-y-4">
              <div className="border-b border-[var(--rbpc-divider)] pb-3">
                <h3 className="font-serif text-lg font-bold text-[var(--rbpc-ink)]">
                  {locale === "vi"
                    ? "Đăng ký Trải nghiệm Văn hóa Làng nghề (Experience Submission)"
                    : "Cultural Experience Submission & Moderation"}
                </h3>
                <p className="text-xs text-[var(--rbpc-ink-subtle)]">
                  {locale === "vi"
                    ? "Trải nghiệm mới sẽ ở trạng thái 'Bản nháp' cho đến khi nhân viên kiểm tra bản quyền và xác thực nghệ nhân."
                    : "New listings remain in Draft until verified and moderated by staff."}
                </p>
              </div>

              <form
                onSubmit={async (e) => {
                  e.preventDefault();
                  setIsSubmittingExp(true);
                  try {
                    const res = await fetch("/api/v1/rbpc/partner/experiences", {
                      method: "POST",
                      headers: { "Content-Type": "application/json" },
                      body: JSON.stringify({
                        slug: expFormData.slug,
                        title_vi: expFormData.title_vi,
                        title_en: expFormData.title_en || undefined,
                        description_vi: expFormData.description_vi,
                        description_en: expFormData.description_en || undefined,
                        area_public: expFormData.area_public,
                        duration_minutes: Number(expFormData.duration_minutes) || undefined,
                        pricing_display: expFormData.pricing_display || undefined,
                        indicative_price_amount: Number(expFormData.indicative_price_amount) || undefined,
                        max_party_size: Number(expFormData.max_party_size) || 10,
                      }),
                    });
                    if (!res.ok) {
                      const err = await res.json().catch(() => ({}));
                      throw new Error(err?.error?.message || "Không thể tạo trải nghiệm");
                    }
                    setDashboardAlert({
                      type: "success",
                      message: locale === "vi"
                        ? "Đã tạo bản nháp trải nghiệm thành công! Đang chờ kiểm duyệt."
                        : "Experience draft created! Awaiting staff moderation.",
                    });
                  } catch (err) {
                    setDashboardAlert({
                      type: "error",
                      message: err instanceof Error ? err.message : "Thao tác thất bại",
                    });
                  } finally {
                    setIsSubmittingExp(false);
                  }
                }}
                className="space-y-4"
              >
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="space-y-1">
                    <label className="text-xs font-semibold text-[var(--rbpc-ink)]">
                      {locale === "vi" ? "Mã trải nghiệm (Slug)" : "Experience Slug"} *
                    </label>
                    <input
                      type="text"
                      required
                      value={expFormData.slug}
                      onChange={(e) => setExpFormData({ ...expFormData, slug: e.target.value })}
                      placeholder="trai-nghiem-duc-dong-hue"
                      className="w-full rounded-md border border-[var(--rbpc-divider)] bg-[var(--rbpc-surface)] px-3 py-2 text-xs text-[var(--rbpc-ink)]"
                    />
                  </div>
                  <div className="space-y-1">
                    <label className="text-xs font-semibold text-[var(--rbpc-ink)]">
                      {locale === "vi" ? "Tiêu đề trải nghiệm" : "Experience Title"} *
                    </label>
                    <input
                      type="text"
                      required
                      value={expFormData.title_vi}
                      onChange={(e) => setExpFormData({ ...expFormData, title_vi: e.target.value })}
                      placeholder="Học đúc chuông đồng cùng nghệ nhân..."
                      className="w-full rounded-md border border-[var(--rbpc-divider)] bg-[var(--rbpc-surface)] px-3 py-2 text-xs text-[var(--rbpc-ink)]"
                    />
                  </div>
                </div>

                <div className="space-y-1">
                  <label className="text-xs font-semibold text-[var(--rbpc-ink)]">
                    {locale === "vi" ? "Mô tả chi tiết lịch trình" : "Detailed Description"} *
                  </label>
                  <textarea
                    required
                    rows={4}
                    value={expFormData.description_vi}
                    onChange={(e) => setExpFormData({ ...expFormData, description_vi: e.target.value })}
                    placeholder="Giới thiệu quy trình trải nghiệm, vật liệu cung cấp..."
                    className="w-full rounded-md border border-[var(--rbpc-divider)] bg-[var(--rbpc-surface)] px-3 py-2 text-xs text-[var(--rbpc-ink)]"
                  />
                </div>

                <div className="flex justify-end pt-2">
                  <RbpcButton type="submit" disabled={isSubmittingExp} variant="primary" size="sm">
                    {isSubmittingExp
                      ? locale === "vi" ? "Đang lưu..." : "Saving..."
                      : locale === "vi" ? "Gửi duyệt trải nghiệm" : "Submit Listing"}
                  </RbpcButton>
                </div>
              </form>
            </RbpcCard>
          </div>
        ) : (
          <CreatorConsentStudio
            creatorId={selectedProviderId === "all" ? undefined : selectedProviderId}
            locale={locale}
            isStaffOrPartner={isStaffOrPartner}
            onAlert={setDashboardAlert}
          />
        )}

        {/* Security & Architectural Invariant Footer Card */}
        <RbpcCard elevation="inset" padding="responsive" className="text-xs text-[var(--rbpc-ink)] space-y-3">
          <div className="flex items-center gap-2 font-semibold text-[var(--rbpc-primary)]">
            <ShieldCheck className="h-4 w-4" aria-hidden="true" />
            <span>
              {locale === "vi"
                ? "Cam kết tuân thủ kiến trúc phân quyền RBPC 2026:"
                : "RBPC 2026 Architectural Compliance & Privacy Invariants:"}
            </span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-[11px] text-[var(--rbpc-ink-subtle)] leading-relaxed">
            <div className="space-y-1">
              <strong className="block text-[var(--rbpc-ink)] font-semibold">
                {locale === "vi"
                  ? "1. Cô lập dữ liệu đa người thuê (Multi-Tenant):"
                  : "1. Multi-Tenant Server Scoping:"}
              </strong>
              <p>
                {locale === "vi"
                  ? "Nhà cung cấp chỉ có quyền truy cập các hồ sơ thuộc về trải nghiệm do chính mình quản lý (provider_id = current_user.id). Tuyệt đối không rò rỉ hồ sơ giữa các xưởng nghề."
                  : "Each provider only receives inquiries bound to their own offerings via server-side database scoping. Cross-provider data leakage is strictly prohibited."}
              </p>
            </div>

            <div className="space-y-1">
              <strong className="block text-[var(--rbpc-ink)] font-semibold">
                {locale === "vi"
                  ? "2. Bảo vệ thông tin liên lạc (PII Masking):"
                  : "2. Progressive PII Unmasking:"}
              </strong>
              <p>
                {locale === "vi"
                  ? "Số điện thoại và email được che dấu mặc định cho đến khi nhân sự có thẩm quyền mở khóa trong phiên làm việc, chống cào quét dữ liệu tự động."
                  : "Phone numbers and email addresses are masked by default until explicitly unmasked by authorized workshop personnel."}
              </p>
            </div>

            <div className="space-y-1">
              <strong className="block text-[var(--rbpc-ink)] font-semibold">
                {locale === "vi"
                  ? "3. Vết kiểm toán bất biến (Audit Trail):"
                  : "3. Immutable Cryptographic Audit Log:"}
              </strong>
              <p>
                {locale === "vi"
                  ? "Mọi thao tác chuyển trạng thái (new -> contacted -> confirmed/declined -> closed) đều ghi nhận dấu thời gian UTC, định danh tài khoản và lý do vào nhật ký kiểm toán."
                  : "Every state transition strictly validates allowed lifecycle pathways and logs an append-only audit trail entry."}
              </p>
            </div>
          </div>
        </RbpcCard>
      </div>
    </div>
  );
}

export default function PartnerInboxPage() {
  return (
    <Suspense
      fallback={
        <div className="rbpc-theme min-h-screen bg-[var(--rbpc-bg)] flex items-center justify-center p-8">
          <div className="h-8 w-8 animate-spin rounded-full border-2 border-[var(--rbpc-primary)] border-t-transparent" />
        </div>
      }
    >
      <PartnerDashboardContent />
    </Suspense>
  );
}
