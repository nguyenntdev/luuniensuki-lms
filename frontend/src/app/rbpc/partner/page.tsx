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

  const [locale, setLocale] = useState<RbpcLocale>("vi");
  const copy = getRbpcCopy(locale);

  // Authentication store
  const authStatus = useAuthStore((s) => s.status);
  const user = useAuthStore((s) => s.user);
  const isAuthenticated = authStatus === "authed" && Boolean(user);
  const isStaffOrPartner =
    user?.role === "partner" || user?.role === "admin" || user?.role === "staff";

  // Active provider selection (for multi-tenant isolation demonstration)
  const [selectedProviderId, setSelectedProviderId] = useState<string>(
    user?.id ? user.id : providerParam
  );

  // Inquiries State
  const [inquiries, setInquiries] = useState<PartnerInboxItemWithAudit[]>(
    SEED_PARTNER_INQUIRIES
  );
  const [isLoading, setIsLoading] = useState(false);
  const [isRefreshing, setIsRefreshing] = useState(false);

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

  // Load inquiries (from API or seed fallback)
  const loadInquiries = async () => {
    setIsRefreshing(true);
    try {
      const items = await fetchPartnerInquiries();
      setInquiries(items && items.length > 0 ? items : SEED_PARTNER_INQUIRIES);
    } catch {
      setInquiries(SEED_PARTNER_INQUIRIES);
    } finally {
      setIsRefreshing(false);
    }
  };

  useEffect(() => {
    loadInquiries();
  }, [isAuthenticated, user?.id]);

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

  // Feedback alert banner state
  const [dashboardAlert, setDashboardAlert] = useState<{
    type: "success" | "error" | "info";
    message: string;
  } | null>(null);

  // Status Change Callback
  const handleStatusChange = async (
    inquiryId: string,
    newStatus: InquiryStatus,
    note?: string
  ) => {
    try {
      // 1. Call backend API endpoint
      await updatePartnerInquiryStatusApi(inquiryId, newStatus, note);

      // 2. Optimistically update local inquiry list
      const now = new Date().toISOString();
      setInquiries((prev) =>
        prev.map((item) => {
          if (item.id === inquiryId) {
            const newAudit: InquiryAuditLogEntry = {
              id: `audit-${Date.now()}`,
              inquiryId,
              timestamp: now,
              actorName:
                locale === "vi" ? currentProvider.nameVi : currentProvider.nameEn,
              previousStatus: item.status,
              newStatus,
              note,
            };
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
      setDashboardAlert({
        type: "error",
        message:
          err instanceof Error
            ? err.message
            : locale === "vi"
            ? "Không thể chuyển trạng thái hồ sơ. Vui lòng thử lại sau."
            : "Failed to transition inquiry status. Please try again later.",
      });
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

        {/* Preview / Offline Mode Alert Banner (If not logged in as partner) */}
        {!isAuthenticated && (
          <div className="flex items-start gap-3 rounded-xl border border-amber-500/30 bg-amber-500/10 p-4 text-xs text-amber-900 dark:text-amber-200">
            <HelpCircle className="h-4 w-4 shrink-0 mt-0.5 text-amber-600" aria-hidden="true" />
            <div className="space-y-1">
              <strong className="block font-semibold">
                {locale === "vi"
                  ? "Chế độ xem trước tính năng (Partner Preview Mode):"
                  : "Partner Preview Mode Active:"}
              </strong>
              <p className="leading-relaxed">
                {locale === "vi"
                  ? "Bạn đang trải nghiệm giao diện quản trị với dữ liệu mẫu mô phỏng 3 xưởng nghề truyền thống (Phường Đúc, Pháp Lam, Thanh Tiên). Bạn có thể thử nghiệm đổi trạng thái, ghi chú và mở khóa thông tin liên hệ."
                  : "You are currently viewing interactive sample data simulating 3 traditional workshops. You can test status transitions, audit logs, and contact unmasking."}
              </p>
            </div>
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
