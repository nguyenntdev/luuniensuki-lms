"use client";

import React, { useState, useMemo } from "react";
import {
  Inbox,
  Filter,
  Search,
  Calendar,
  Clock,
  User,
  Phone,
  Mail,
  MessageCircle,
  Eye,
  EyeOff,
  CheckCircle2,
  XCircle,
  AlertCircle,
  ChevronRight,
  ShieldCheck,
  ShieldAlert,
  ArrowRight,
  History,
  FileText,
  Save,
  RotateCcw,
  Sparkles,
  ExternalLink,
  Info,
} from "lucide-react";
import type {
  PartnerInboxItem,
  InquiryStatus,
  ContactMethod,
  RbpcLocale,
  IsoDateString,
  IsoDateTimeString,
} from "@/types/rbpc";
import { getRbpcCopy } from "@/lib/rbpc/copy";
import { cn } from "@/lib/utils";
import { RbpcCard } from "./RbpcCard";
import { RbpcButton } from "./RbpcButton";

export interface InquiryAuditLogEntry {
  id: string;
  inquiryId: string;
  timestamp: IsoDateTimeString;
  actorId?: string;
  actorName?: string;
  previousStatus: InquiryStatus;
  newStatus: InquiryStatus;
  note?: string;
}

export interface PartnerInboxItemWithAudit extends PartnerInboxItem {
  providerId?: string;
  auditLog?: InquiryAuditLogEntry[];
}

export interface PartnerInboxViewProps {
  /** Initial or controlled inquiries */
  initialInquiries?: PartnerInboxItemWithAudit[];
  /** Controlled inquiries list (if passed, takes precedence over internal state) */
  inquiries?: PartnerInboxItemWithAudit[];
  /** Current provider ID for strict multi-tenant data isolation */
  providerId?: string;
  /** Current provider display name */
  providerName?: string;
  /** Active UI locale (default "vi") */
  locale?: RbpcLocale;
  /** Callback triggered when inquiry status is updated */
  onStatusChange?: (
    inquiryId: string,
    newStatus: InquiryStatus,
    note?: string
  ) => Promise<void> | void;
  /** Callback triggered when internal notes are saved */
  onSaveNotes?: (inquiryId: string, notes: string) => Promise<void> | void;
  /** Callback triggered when contact info is unmasked */
  onUnmaskContact?: (inquiryId: string) => void;
  /** Additional container CSS class names */
  className?: string;
}

/**
 * Valid state transitions allowed per Master Spec §5.4:
 * new -> contacted, declined
 * contacted -> confirmed, declined
 * confirmed -> closed
 * declined -> closed
 * closed -> (terminal)
 */
export const VALID_TRANSITIONS: Record<InquiryStatus, InquiryStatus[]> = {
  new: ["contacted", "declined"],
  contacted: ["confirmed", "declined"],
  confirmed: ["closed"],
  declined: ["closed"],
  closed: [],
};

/**
 * Masks visitor contact details to prevent unauthorized harvesting or exposure
 * until an authenticated partner explicitly unlocks/acknowledges handling.
 */
export function maskContactValue(value: string, method: ContactMethod): string {
  if (!value) return "";
  const trimmed = value.trim();
  if (!trimmed) return "";

  if (method === "email") {
    const atIndex = trimmed.indexOf("@");
    if (atIndex < 0) return "***";
    if (atIndex <= 1) return "***" + trimmed.slice(atIndex);
    const user = trimmed.slice(0, atIndex);
    const domain = trimmed.slice(atIndex);
    if (user.length <= 2) {
      return user[0] + "***" + domain;
    }
    return user[0] + "***" + user[user.length - 1] + domain;
  }

  // Phone or Zalo: Show first 4 and last 3 digits, mask middle
  const digits = trimmed.replace(/\D/g, "");
  if (digits.length < 7) {
    return trimmed.slice(0, 2) + " ••• " + trimmed.slice(-2);
  }
  const prefix = digits.slice(0, 4);
  const suffix = digits.slice(-3);
  return `${prefix} ••• ${suffix}`;
}

/**
 * Maps inquiry status to human-readable label and styling classes.
 */
export function getStatusBadgeInfo(
  status: InquiryStatus,
  locale: RbpcLocale = "vi"
): { label: string; bgClass: string; textClass: string; borderClass: string } {
  switch (status) {
    case "new":
      return {
        label: locale === "vi" ? "Mới tiếp nhận" : "New Request",
        bgClass: "bg-blue-500/10",
        textClass: "text-blue-700 dark:text-blue-300",
        borderClass: "border-blue-600/30",
      };
    case "contacted":
      return {
        label: locale === "vi" ? "Đã liên hệ" : "Contacted",
        bgClass: "bg-amber-500/10",
        textClass: "text-amber-800 dark:text-amber-300",
        borderClass: "border-amber-600/30",
      };
    case "confirmed":
      return {
        label: locale === "vi" ? "Đã xác nhận" : "Confirmed",
        bgClass: "bg-emerald-500/10",
        textClass: "text-emerald-800 dark:text-emerald-300",
        borderClass: "border-emerald-600/30",
      };
    case "declined":
      return {
        label: locale === "vi" ? "Đã từ chối" : "Declined",
        bgClass: "bg-rose-500/10",
        textClass: "text-rose-800 dark:text-rose-300",
        borderClass: "border-rose-600/30",
      };
    case "closed":
      return {
        label: locale === "vi" ? "Đã lưu trữ" : "Closed",
        bgClass: "bg-stone-500/10",
        textClass: "text-stone-700 dark:text-stone-300",
        borderClass: "border-stone-500/30",
      };
    default:
      return {
        label: status,
        bgClass: "bg-stone-500/10",
        textClass: "text-stone-700 dark:text-stone-300",
        borderClass: "border-stone-500/30",
      };
  }
}

/**
 * PartnerInboxView Component
 *
 * Implements Master Spec §5.4, §6.1, §6.2 requirements:
 * 1. Filter inquiries by status (`new`, `contacted`, `confirmed`, `declined`), date range, and experience
 * 2. Status transition dropdown with state change feedback and audit log entry
 * 3. Strict provider data isolation and privacy protection (masks visitor contact info until authenticated handling)
 */
export function PartnerInboxView({
  initialInquiries = [],
  inquiries: controlledInquiries,
  providerId,
  providerName = "Xưởng nghề đối tác Huế",
  locale = "vi",
  onStatusChange,
  onSaveNotes,
  onUnmaskContact,
  className,
}: PartnerInboxViewProps) {
  const copy = getRbpcCopy(locale);

  // Internal state of inquiries if not controlled
  const [inquiryList, setInquiryList] = useState<PartnerInboxItemWithAudit[]>(
    controlledInquiries || initialInquiries
  );

  // Active filter states
  const [statusFilter, setStatusFilter] = useState<InquiryStatus | "all">("all");
  const [experienceFilter, setExperienceFilter] = useState<string>("all");
  const [dateFrom, setDateFrom] = useState<string>("");
  const [dateTo, setDateTo] = useState<string>("");
  const [searchQuery, setSearchQuery] = useState<string>("");

  // Selected inquiry for detail drawer
  const [selectedInquiryId, setSelectedInquiryId] = useState<string | null>(
    null
  );

  // Set of unmasked inquiry IDs for session privacy
  const [unmaskedIds, setUnmaskedIds] = useState<Set<string>>(new Set());

  // Status transition form state
  const [pendingStatus, setPendingStatus] = useState<InquiryStatus | "">("");
  const [transitionNote, setTransitionNote] = useState<string>("");
  const [isUpdatingStatus, setIsUpdatingStatus] = useState(false);

  // Notes editing state
  const [editingNotes, setEditingNotes] = useState<string>("");
  const [isSavingNotes, setIsSavingNotes] = useState(false);

  // User feedback notification
  const [feedbackMessage, setFeedbackMessage] = useState<{
    type: "success" | "error" | "info";
    text: string;
  } | null>(null);

  // Sync when controlled inquiries change
  React.useEffect(() => {
    if (controlledInquiries) {
      setInquiryList(controlledInquiries);
    }
  }, [controlledInquiries]);

  // =========================================================================
  // STRICT PROVIDER DATA ISOLATION
  // Filter out any inquiry that belongs to another provider when providerId is set
  // =========================================================================
  const isolatedInquiries = useMemo(() => {
    if (!providerId) return inquiryList;
    return inquiryList.filter(
      (item) => !item.providerId || item.providerId === providerId
    );
  }, [inquiryList, providerId]);

  // Unique experiences available in current dataset
  const uniqueExperiences = useMemo(() => {
    const map = new Map<string, string>();
    for (const item of isolatedInquiries) {
      if (item.experienceSlug && !map.has(item.experienceSlug)) {
        map.set(item.experienceSlug, item.experienceTitle);
      }
    }
    return Array.from(map.entries()).map(([slug, title]) => ({ slug, title }));
  }, [isolatedInquiries]);

  // Filtered inquiries based on active user controls
  const filteredInquiries = useMemo(() => {
    return isolatedInquiries.filter((item) => {
      // 1. Status Filter
      if (statusFilter !== "all" && item.status !== statusFilter) {
        return false;
      }

      // 2. Experience Filter
      if (
        experienceFilter !== "all" &&
        item.experienceSlug !== experienceFilter
      ) {
        return false;
      }

      // 3. Date Range Filter (against preferredDate or createdAt)
      const targetDate = item.preferredDate || item.createdAt.split("T")[0];
      if (dateFrom && targetDate < dateFrom) {
        return false;
      }
      if (dateTo && targetDate > dateTo) {
        return false;
      }

      // 4. Search Query Filter
      if (searchQuery.trim()) {
        const query = searchQuery.trim().toLowerCase();
        const matchesRef = item.reference.toLowerCase().includes(query);
        const matchesName = item.contactName.toLowerCase().includes(query);
        const matchesExp = item.experienceTitle.toLowerCase().includes(query);
        const matchesMsg = item.message?.toLowerCase().includes(query) ?? false;
        const matchesContact = unmaskedIds.has(item.id)
          ? item.contactValue.toLowerCase().includes(query)
          : false;

        if (
          !matchesRef &&
          !matchesName &&
          !matchesExp &&
          !matchesMsg &&
          !matchesContact
        ) {
          return false;
        }
      }

      return true;
    });
  }, [
    isolatedInquiries,
    statusFilter,
    experienceFilter,
    dateFrom,
    dateTo,
    searchQuery,
    unmaskedIds,
  ]);

  // Counts by status
  const counts = useMemo(() => {
    const c = { all: isolatedInquiries.length, new: 0, contacted: 0, confirmed: 0, declined: 0, closed: 0 };
    for (const item of isolatedInquiries) {
      if (item.status in c) {
        c[item.status as keyof typeof c]++;
      }
    }
    return c;
  }, [isolatedInquiries]);

  // Active selected inquiry
  const selectedInquiry = useMemo(() => {
    if (!selectedInquiryId) return null;
    return isolatedInquiries.find((item) => item.id === selectedInquiryId) || null;
  }, [isolatedInquiries, selectedInquiryId]);

  // Initialize editing notes when selected inquiry changes
  React.useEffect(() => {
    if (selectedInquiry) {
      setEditingNotes(selectedInquiry.partnerNotes || "");
      setPendingStatus("");
      setTransitionNote("");
    }
  }, [selectedInquiry]);

  // Clear feedback after 4 seconds
  React.useEffect(() => {
    if (feedbackMessage) {
      const timer = setTimeout(() => {
        setFeedbackMessage(null);
      }, 4000);
      return () => clearTimeout(timer);
    }
  }, [feedbackMessage]);

  // Handle unmasking contact information
  const handleToggleUnmask = (inquiryId: string) => {
    setUnmaskedIds((prev) => {
      const next = new Set(prev);
      if (next.has(inquiryId)) {
        next.delete(inquiryId);
      } else {
        next.add(inquiryId);
        if (onUnmaskContact) {
          onUnmaskContact(inquiryId);
        }
      }
      return next;
    });
  };

  // Handle status transition execution
  const handleExecuteTransition = async () => {
    if (!selectedInquiry || !pendingStatus) return;

    const prevStatus = selectedInquiry.status;
    const nextStatus = pendingStatus as InquiryStatus;

    // Verify transition validity per state machine
    const allowed = VALID_TRANSITIONS[prevStatus] || [];
    if (!allowed.includes(nextStatus)) {
      setFeedbackMessage({
        type: "error",
        text:
          locale === "vi"
            ? `Chuyển trạng thái từ ${prevStatus} sang ${nextStatus} không hợp lệ theo quy trình.`
            : `Transition from ${prevStatus} to ${nextStatus} is not permitted by state machine rules.`,
      });
      return;
    }

    setIsUpdatingStatus(true);

    const now = new Date().toISOString();
    const newAuditEntry: InquiryAuditLogEntry = {
      id: `audit-${Date.now()}`,
      inquiryId: selectedInquiry.id,
      timestamp: now,
      actorName: providerName,
      previousStatus: prevStatus,
      newStatus: nextStatus,
      note: transitionNote.trim() || undefined,
    };

    try {
      if (onStatusChange) {
        await onStatusChange(selectedInquiry.id, nextStatus, transitionNote.trim() || undefined);
      }

      // Update local state
      setInquiryList((prev) =>
        prev.map((item) => {
          if (item.id === selectedInquiry.id) {
            const existingAudit = item.auditLog || [];
            return {
              ...item,
              status: nextStatus,
              updatedAt: now,
              lastContactedAt: nextStatus === "contacted" ? now : item.lastContactedAt,
              auditLog: [newAuditEntry, ...existingAudit],
            };
          }
          return item;
        })
      );

      const statusBadge = getStatusBadgeInfo(nextStatus, locale);
      setFeedbackMessage({
        type: "success",
        text:
          locale === "vi"
            ? `Cập nhật thành công: Hồ sơ ${selectedInquiry.reference} đã chuyển sang "${statusBadge.label}".`
            : `Updated successfully: Inquiry ${selectedInquiry.reference} transitioned to "${statusBadge.label}".`,
      });

      setPendingStatus("");
      setTransitionNote("");
    } catch (err) {
      setFeedbackMessage({
        type: "error",
        text:
          locale === "vi"
            ? "Đã xảy ra sự cố khi cập nhật trạng thái. Vui lòng thử lại."
            : "Failed to update status. Please try again.",
      });
    } finally {
      setIsUpdatingStatus(false);
    }
  };

  // Handle saving internal partner notes
  const handleSaveNotes = async () => {
    if (!selectedInquiry) return;

    setIsSavingNotes(true);
    const now = new Date().toISOString();

    try {
      if (onSaveNotes) {
        await onSaveNotes(selectedInquiry.id, editingNotes.trim());
      }

      setInquiryList((prev) =>
        prev.map((item) => {
          if (item.id === selectedInquiry.id) {
            return {
              ...item,
              partnerNotes: editingNotes.trim(),
              updatedAt: now,
            };
          }
          return item;
        })
      );

      setFeedbackMessage({
        type: "success",
        text:
          locale === "vi"
            ? "Đã lưu ghi chú nội bộ thành công."
            : "Internal notes saved successfully.",
      });
    } catch (err) {
      setFeedbackMessage({
        type: "error",
        text:
          locale === "vi"
            ? "Lỗi khi lưu ghi chú nội bộ."
            : "Failed to save internal notes.",
      });
    } finally {
      setIsSavingNotes(false);
    }
  };

  const handleResetFilters = () => {
    setStatusFilter("all");
    setExperienceFilter("all");
    setDateFrom("");
    setDateTo("");
    setSearchQuery("");
  };

  return (
    <div
      className={cn(
        "flex flex-col space-y-6 rounded-2xl border border-[var(--rbpc-divider)] bg-[var(--rbpc-surface)] p-6 sm:p-8 shadow-[var(--rbpc-shadow-sm)]",
        className
      )}
    >
      {/* =====================================================================
          1. HEADER & STRICT PROVIDER ISOLATION BANNER
          ===================================================================== */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-6 border-b border-[var(--rbpc-divider)]">
        <div>
          <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-[var(--rbpc-primary)] mb-1">
            <Inbox className="h-4 w-4" aria-hidden="true" />
            <span>{locale === "vi" ? "Bảng điều khiển xưởng nghề" : "Partner Workshop Console"}</span>
          </div>
          <h1 className="font-serif text-2xl sm:text-3xl font-bold text-[var(--rbpc-ink)]">
            {copy.nav.partnerInbox || (locale === "vi" ? "Hộp thư đối tác" : "Partner Inbox")}
          </h1>
          <p className="text-xs sm:text-sm text-[var(--rbpc-muted)] mt-1">
            <span>{locale === "vi" ? "Xưởng phụ trách: " : "Host Studio: "}</span>
            <strong className="text-[var(--rbpc-ink)]">{providerName}</strong>
          </p>
        </div>

        {/* Strict Isolation & Zero-PII Compliance Badge */}
        <div className="flex items-center gap-2 rounded-xl border border-emerald-700/30 bg-emerald-500/10 px-3.5 py-2 text-xs font-medium text-emerald-900 dark:text-emerald-300">
          <ShieldCheck className="h-4 w-4 text-emerald-700 dark:text-emerald-400 shrink-0" aria-hidden="true" />
          <div className="text-[11px] leading-tight">
            <span className="font-semibold block">
              {locale === "vi" ? "Cách ly dữ liệu xưởng nghề" : "Provider Data Isolation Active"}
            </span>
            <span className="text-emerald-800/80 dark:text-emerald-400/80">
              {locale === "vi"
                ? "Ẩn thông tin khách cho đến khi xác nhận xử lý"
                : "Visitor PII masked until authenticated handling"}
            </span>
          </div>
        </div>
      </div>

      {/* =====================================================================
          1.1 CANONICAL TRUST STATEMENT BANNER
          ===================================================================== */}
      <div className="flex items-start gap-2.5 rounded-xl border border-[var(--rbpc-divider-subtle)] bg-[var(--rbpc-bg)] p-3 text-xs text-[var(--rbpc-muted)] leading-relaxed">
        <Info className="h-4 w-4 text-[var(--rbpc-primary)] shrink-0 mt-0.5" aria-hidden="true" />
        <p>
          {locale === "vi"
            ? "Concept demonstration — Yêu cầu trải nghiệm sẽ được gửi trực tiếp đến nghệ nhân/cơ sở để xác nhận thời gian."
            : "Concept demonstration — Experience requests will be sent directly to the artisan/facility to confirm timing."}
        </p>
      </div>

      {/* =====================================================================
          2. FEEDBACK STATE ANNOUNCEMENT BANNER
          ===================================================================== */}
      {feedbackMessage && (
        <div
          role="status"
          aria-live="polite"
          className={cn(
            "flex items-center justify-between rounded-xl p-3.5 text-xs font-medium border transition-all duration-200",
            feedbackMessage.type === "success" &&
              "border-emerald-600/30 bg-emerald-500/10 text-emerald-900 dark:text-emerald-300",
            feedbackMessage.type === "error" &&
              "border-rose-600/30 bg-rose-500/10 text-rose-900 dark:text-rose-300",
            feedbackMessage.type === "info" &&
              "border-blue-600/30 bg-blue-500/10 text-blue-900 dark:text-blue-300"
          )}
        >
          <div className="flex items-center gap-2">
            {feedbackMessage.type === "success" && (
              <CheckCircle2 className="h-4 w-4 shrink-0" aria-hidden="true" />
            )}
            {feedbackMessage.type === "error" && (
              <AlertCircle className="h-4 w-4 shrink-0" aria-hidden="true" />
            )}
            <span>{feedbackMessage.text}</span>
          </div>
          <button
            type="button"
            onClick={() => setFeedbackMessage(null)}
            className="inline-flex min-h-[44px] min-w-[44px] items-center justify-center rounded-md text-xs hover:opacity-75 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--rbpc-focus)] focus-visible:ring-offset-2"
            aria-label={copy.cta.close}
          >
            ×
          </button>
        </div>
      )}

      {/* =====================================================================
          3. FILTER CONTROLS & STATUS TABS
          ===================================================================== */}
      <div className="space-y-4">
        {/* Status Pill Tabs */}
        <div
          role="tablist"
          aria-label={locale === "vi" ? "Lọc theo trạng thái yêu cầu" : "Filter by status"}
          className="flex flex-wrap gap-2"
        >
          {(
            [
              { key: "all", label: locale === "vi" ? "Tất cả" : "All", count: counts.all },
              { key: "new", label: locale === "vi" ? "Mới tiếp nhận" : "New", count: counts.new },
              { key: "contacted", label: locale === "vi" ? "Đã liên hệ" : "Contacted", count: counts.contacted },
              { key: "confirmed", label: locale === "vi" ? "Đã xác nhận" : "Confirmed", count: counts.confirmed },
              { key: "declined", label: locale === "vi" ? "Đã từ chối" : "Declined", count: counts.declined },
            ] as const
          ).map((tab) => {
            const isActive = statusFilter === tab.key;
            return (
              <button
                key={tab.key}
                role="tab"
                aria-selected={isActive}
                onClick={() => setStatusFilter(tab.key)}
                className={cn(
                  "flex min-h-[44px] min-w-[44px] items-center gap-2 rounded-xl px-4 py-2 text-xs font-medium transition-colors select-none",
                  "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--rbpc-focus)] focus-visible:ring-offset-2",
                  isActive
                    ? "bg-[var(--rbpc-primary)] text-white shadow-xs"
                    : "border border-[var(--rbpc-divider)] bg-[var(--rbpc-surface)] text-[var(--rbpc-ink)] hover:bg-[var(--rbpc-bg)]"
                )}
              >
                <span>{tab.label}</span>
                <span
                  className={cn(
                    "flex h-5 min-w-[20px] items-center justify-center rounded-full px-1.5 text-[11px] font-semibold",
                    isActive
                      ? "bg-white/20 text-white"
                      : "bg-[var(--rbpc-surface-muted)] text-[var(--rbpc-muted)]"
                  )}
                >
                  {tab.count}
                </span>
              </button>
            );
          })}
        </div>

        {/* Filter Bar: Experience Select, Date Range, Search Query */}
        <div className="grid grid-cols-1 md:grid-cols-12 gap-3 pt-2">
          {/* Search Box */}
          <div className="md:col-span-4 relative">
            <label htmlFor="partner-search-input" className="rbpc-sr-only">
              {locale === "vi" ? "Tìm kiếm yêu cầu" : "Search inquiries"}
            </label>
            <input
              id="partner-search-input"
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder={
                locale === "vi"
                  ? "Tìm mã hồ sơ, tên khách, nội dung..."
                  : "Search ref, guest name, text..."
              }
              className="rbpc-input pl-9 text-xs sm:text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--rbpc-focus)] focus-visible:ring-offset-2"
            />
            <Search
              className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-[var(--rbpc-muted)]"
              aria-hidden="true"
            />
          </div>

          {/* Experience Filter Dropdown */}
          <div className="md:col-span-3">
            <label htmlFor="partner-experience-select" className="rbpc-sr-only">
              {locale === "vi" ? "Lọc theo trải nghiệm" : "Filter by experience"}
            </label>
            <select
              id="partner-experience-select"
              value={experienceFilter}
              onChange={(e) => setExperienceFilter(e.target.value)}
              className="rbpc-select text-xs sm:text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--rbpc-focus)] focus-visible:ring-offset-2"
            >
              <option value="all">
                {locale === "vi" ? "Tất cả trải nghiệm" : "All Experiences"}
              </option>
              {uniqueExperiences.map((exp) => (
                <option key={exp.slug} value={exp.slug}>
                  {exp.title}
                </option>
              ))}
            </select>
          </div>

          {/* Date Range: From */}
          <div className="md:col-span-2">
            <label htmlFor="partner-date-from" className="rbpc-sr-only">
              {locale === "vi" ? "Từ ngày" : "From Date"}
            </label>
            <input
              id="partner-date-from"
              type="date"
              value={dateFrom}
              onChange={(e) => setDateFrom(e.target.value)}
              title={locale === "vi" ? "Từ ngày" : "From Date"}
              className="rbpc-input text-xs focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--rbpc-focus)] focus-visible:ring-offset-2"
            />
          </div>

          {/* Date Range: To */}
          <div className="md:col-span-2">
            <label htmlFor="partner-date-to" className="rbpc-sr-only">
              {locale === "vi" ? "Đến ngày" : "To Date"}
            </label>
            <input
              id="partner-date-to"
              type="date"
              value={dateTo}
              onChange={(e) => setDateTo(e.target.value)}
              title={locale === "vi" ? "Đến ngày" : "To Date"}
              className="rbpc-input text-xs focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--rbpc-focus)] focus-visible:ring-offset-2"
            />
          </div>

          {/* Reset Filters */}
          <div className="md:col-span-1 flex items-center">
            <button
              type="button"
              onClick={handleResetFilters}
              title={locale === "vi" ? "Xóa bộ lọc" : "Reset Filters"}
              aria-label={locale === "vi" ? "Xóa bộ lọc" : "Reset Filters"}
              className="flex min-h-[44px] min-w-[44px] w-full items-center justify-center rounded-xl border border-[var(--rbpc-divider)] bg-[var(--rbpc-surface)] text-[var(--rbpc-muted)] hover:bg-[var(--rbpc-bg)] hover:text-[var(--rbpc-ink)] transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--rbpc-focus)] focus-visible:ring-offset-2"
            >
              <RotateCcw className="h-4 w-4" aria-hidden="true" />
            </button>
          </div>
        </div>
      </div>

      {/* =====================================================================
          4. MAIN WORKSPACE: INQUIRY TABLE + DETAIL PANEL
          ===================================================================== */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        {/* ===================================================================
            LEFT: INQUIRY TABLE (7 Columns on large screens)
            =================================================================== */}
        <div className="lg:col-span-7 space-y-3">
          <div className="flex items-center justify-between text-xs text-[var(--rbpc-muted)] px-1">
            <span>
              {locale === "vi"
                ? `Hiển thị ${filteredInquiries.length} / ${isolatedInquiries.length} yêu cầu`
                : `Showing ${filteredInquiries.length} of ${isolatedInquiries.length} inquiries`}
            </span>

            {statusFilter !== "all" && (
              <span className="font-medium text-[var(--rbpc-primary)]">
                {locale === "vi" ? "Đang lọc theo trạng thái" : "Filtered view active"}
              </span>
            )}
          </div>

          {filteredInquiries.length === 0 ? (
            <div className="rounded-2xl border border-dashed border-[var(--rbpc-divider)] bg-[var(--rbpc-bg)] p-10 text-center space-y-3">
              <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-[var(--rbpc-surface-muted)] text-[var(--rbpc-muted)]">
                <Inbox className="h-6 w-6" aria-hidden="true" />
              </div>
              <h3 className="font-serif text-base font-semibold text-[var(--rbpc-ink)]">
                {locale === "vi" ? "Không có yêu cầu phù hợp" : "No Matching Inquiries Found"}
              </h3>
              <p className="text-xs text-[var(--rbpc-muted)] max-w-sm mx-auto">
                {locale === "vi"
                  ? "Thử điều chỉnh trạng thái, khoảng ngày hoặc từ khóa tìm kiếm để xem các hồ sơ khác."
                  : "Try adjusting the status tabs, date range, or search query to find inquiries."}
              </p>
              <RbpcButton variant="secondary" size="sm" onClick={handleResetFilters}>
                {locale === "vi" ? "Xóa toàn bộ bộ lọc" : "Clear all filters"}
              </RbpcButton>
            </div>
          ) : (
            <div className="space-y-2.5">
              {filteredInquiries.map((item) => {
                const isSelected = selectedInquiryId === item.id;
                const isUnmasked = unmaskedIds.has(item.id);
                const badge = getStatusBadgeInfo(item.status, locale);
                const displayContact = isUnmasked
                  ? item.contactValue
                  : maskContactValue(item.contactValue, item.contactMethod);

                return (
                  <article
                    key={item.id}
                    tabIndex={0}
                    role="button"
                    aria-pressed={isSelected}
                    onClick={() => setSelectedInquiryId(item.id)}
                    onKeyDown={(e) => {
                      if (e.key === "Enter" || e.key === " ") {
                        e.preventDefault();
                        setSelectedInquiryId(item.id);
                      }
                    }}
                    className={cn(
                      "group relative flex flex-col sm:flex-row sm:items-center justify-between gap-3 p-4 sm:p-5 rounded-xl border transition-all duration-200 cursor-pointer select-none",
                      "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--rbpc-focus)] focus-visible:ring-offset-2",
                      isSelected
                        ? "border-[var(--rbpc-primary)] bg-[var(--rbpc-primary-subtle)] shadow-xs"
                        : "border-[var(--rbpc-divider)] bg-[var(--rbpc-surface)] hover:border-[var(--rbpc-primary-border)] hover:bg-[var(--rbpc-bg)]"
                    )}
                  >
                    <div className="space-y-1.5 flex-1 min-w-0">
                      {/* Top Row: Reference, Status Badge & Preferred Date */}
                      <div className="flex flex-wrap items-center gap-2">
                        <span className="font-mono text-xs font-bold tracking-wider text-[var(--rbpc-primary)]">
                          {item.reference}
                        </span>

                        <span
                          className={cn(
                            "inline-flex items-center gap-1 rounded-full border px-2 py-0.5 text-[11px] font-semibold",
                            badge.bgClass,
                            badge.textClass,
                            badge.borderClass
                          )}
                        >
                          <span className="h-1.5 w-1.5 rounded-full bg-current" aria-hidden="true" />
                          <span>{badge.label}</span>
                        </span>

                        {item.preferredDate && (
                          <span className="inline-flex items-center gap-1 text-[11px] text-[var(--rbpc-muted)]">
                            <Calendar className="h-3 w-3" aria-hidden="true" />
                            <span>{item.preferredDate}</span>
                          </span>
                        )}
                      </div>

                      {/* Guest Name & Experience Title */}
                      <div>
                        <h4 className="font-serif text-sm sm:text-base font-bold text-[var(--rbpc-ink)] truncate">
                          {item.contactName}
                        </h4>
                        <p className="text-xs text-[var(--rbpc-muted)] truncate">
                          {item.experienceTitle} • {item.partySize} {locale === "vi" ? "khách" : "guest(s)"}
                        </p>
                      </div>

                      {/* Masked Contact Info */}
                      <div className="flex items-center gap-2 text-xs text-[var(--rbpc-muted)] pt-0.5">
                        <span className="inline-flex items-center gap-1 font-mono text-[11px]">
                          {item.contactMethod === "email" && <Mail className="h-3 w-3" aria-hidden="true" />}
                          {item.contactMethod === "phone" && <Phone className="h-3 w-3" aria-hidden="true" />}
                          {item.contactMethod === "zalo" && <MessageCircle className="h-3 w-3" aria-hidden="true" />}
                          <span>{displayContact}</span>
                        </span>

                        <button
                          type="button"
                          onClick={(e) => {
                            e.stopPropagation();
                            handleToggleUnmask(item.id);
                          }}
                          className="inline-flex min-h-[44px] min-w-[44px] items-center justify-center gap-1.5 rounded-lg border border-[var(--rbpc-divider-subtle)] bg-[var(--rbpc-surface)] px-2.5 py-1 text-[11px] font-medium text-[var(--rbpc-primary)] hover:bg-[var(--rbpc-surface-muted)] transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--rbpc-focus)] focus-visible:ring-offset-2"
                          title={isUnmasked ? (locale === "vi" ? "Ẩn bảo mật PII" : "Mask PII") : (locale === "vi" ? "Mở thông tin liên hệ" : "Reveal PII")}
                          aria-label={
                            isUnmasked
                              ? (locale === "vi" ? `Ẩn thông tin liên hệ của ${item.contactName}` : `Mask contact details for ${item.contactName}`)
                              : (locale === "vi" ? `Mở thông tin liên hệ của ${item.contactName}` : `Reveal contact details for ${item.contactName}`)
                          }
                        >
                          {isUnmasked ? (
                            <>
                              <EyeOff className="h-3.5 w-3.5" aria-hidden="true" />
                              <span>{locale === "vi" ? "Ẩn PII" : "Mask"}</span>
                            </>
                          ) : (
                            <>
                              <Eye className="h-3.5 w-3.5" aria-hidden="true" />
                              <span>{locale === "vi" ? "Hiện PII" : "Reveal"}</span>
                            </>
                          )}
                        </button>
                      </div>
                    </div>

                    {/* Right Chevron & Arrow */}
                    <div className="shrink-0 flex sm:flex-col items-center justify-between sm:justify-center gap-2">
                      <span className="text-[10px] text-[var(--rbpc-muted)] font-mono">
                        {item.createdAt.split("T")[0]}
                      </span>
                      <ChevronRight
                        className={cn(
                          "h-5 w-5 transition-transform text-[var(--rbpc-muted)]",
                          isSelected ? "text-[var(--rbpc-primary)] translate-x-1" : "group-hover:translate-x-0.5"
                        )}
                        aria-hidden="true"
                      />
                    </div>
                  </article>
                );
              })}
            </div>
          )}
        </div>

        {/* ===================================================================
            RIGHT: DETAIL & STATUS TRANSITION WORKSPACE (5 Columns)
            =================================================================== */}
        <div className="lg:col-span-5">
          {selectedInquiry ? (
            <div className="space-y-5 rounded-2xl border border-[var(--rbpc-divider)] bg-[var(--rbpc-bg)] p-5 sm:p-6 shadow-xs">
              {/* Detail Header */}
              <div className="flex items-start justify-between gap-3 pb-4 border-b border-[var(--rbpc-divider)]">
                <div>
                  <span className="font-mono text-xs font-bold tracking-widest text-[var(--rbpc-primary)]">
                    {selectedInquiry.reference}
                  </span>
                  <h3 className="font-serif text-lg font-bold text-[var(--rbpc-ink)] leading-snug mt-0.5">
                    {selectedInquiry.contactName}
                  </h3>
                  <span className="text-xs text-[var(--rbpc-muted)]">
                    {selectedInquiry.experienceTitle}
                  </span>
                </div>

                {/* Status Badge */}
                {(() => {
                  const b = getStatusBadgeInfo(selectedInquiry.status, locale);
                  return (
                    <span
                      className={cn(
                        "inline-flex items-center gap-1 rounded-full border px-2.5 py-1 text-xs font-semibold shrink-0",
                        b.bgClass,
                        b.textClass,
                        b.borderClass
                      )}
                    >
                      <span className="h-1.5 w-1.5 rounded-full bg-current" aria-hidden="true" />
                      <span>{b.label}</span>
                    </span>
                  );
                })()}
              </div>

              {/* Visitor Contact Card with Privacy Reveal Toggle */}
              <div className="rounded-xl border border-[var(--rbpc-divider-subtle)] bg-[var(--rbpc-surface)] p-4 space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-semibold uppercase tracking-wider text-[var(--rbpc-primary)] flex items-center gap-1.5">
                    <User className="h-3.5 w-3.5" aria-hidden="true" />
                    <span>{locale === "vi" ? "Thông tin liên hệ" : "Contact Details"}</span>
                  </span>

                  <button
                    type="button"
                    onClick={() => handleToggleUnmask(selectedInquiry.id)}
                    className="inline-flex min-h-[44px] min-w-[44px] items-center gap-2 rounded-lg border border-[var(--rbpc-divider)] bg-[var(--rbpc-bg)] px-3 py-2 text-xs font-medium text-[var(--rbpc-ink)] hover:bg-[var(--rbpc-surface-muted)] transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--rbpc-focus)] focus-visible:ring-offset-2"
                    aria-label={
                      unmaskedIds.has(selectedInquiry.id)
                        ? (locale === "vi" ? "Ẩn thông tin liên hệ (Bảo mật PII)" : "Mask visitor contact details")
                        : (locale === "vi" ? "Mở thông tin liên hệ (Xác nhận xử lý)" : "Reveal visitor contact details")
                    }
                  >
                    {unmaskedIds.has(selectedInquiry.id) ? (
                      <>
                        <EyeOff className="h-4 w-4" aria-hidden="true" />
                        <span>{locale === "vi" ? "Ẩn bảo mật (PII)" : "Mask PII"}</span>
                      </>
                    ) : (
                      <>
                        <Eye className="h-4 w-4 text-[var(--rbpc-primary)]" aria-hidden="true" />
                        <span>{locale === "vi" ? "Mở thông tin liên hệ" : "Reveal Contact"}</span>
                      </>
                    )}
                  </button>
                </div>

                <div className="text-xs space-y-2 pt-1 text-[var(--rbpc-ink)]">
                  <div className="flex justify-between items-center">
                    <span className="text-[var(--rbpc-muted)]">
                      {locale === "vi" ? "Kênh liên hệ:" : "Channel:"}
                    </span>
                    <span className="font-semibold uppercase font-mono text-[11px]">
                      {selectedInquiry.contactMethod}
                    </span>
                  </div>

                  <div className="flex justify-between items-center">
                    <span className="text-[var(--rbpc-muted)]">
                      {locale === "vi" ? "Chi tiết liên lạc:" : "Contact Value:"}
                    </span>
                    <span className="font-mono font-medium">
                      {unmaskedIds.has(selectedInquiry.id)
                        ? selectedInquiry.contactValue
                        : maskContactValue(selectedInquiry.contactValue, selectedInquiry.contactMethod)}
                    </span>
                  </div>

                  {selectedInquiry.preferredDate && (
                    <div className="flex justify-between items-center">
                      <span className="text-[var(--rbpc-muted)]">
                        {locale === "vi" ? "Ngày hẹn dự kiến:" : "Preferred Date:"}
                      </span>
                      <span className="font-mono font-semibold text-[var(--rbpc-primary)]">
                        {selectedInquiry.preferredDate}
                      </span>
                    </div>
                  )}

                  <div className="flex justify-between items-center">
                    <span className="text-[var(--rbpc-muted)]">
                      {locale === "vi" ? "Số khách tham gia:" : "Party Size:"}
                    </span>
                    <span className="font-medium">
                      {selectedInquiry.partySize} {locale === "vi" ? "người" : "guest(s)"}
                    </span>
                  </div>
                </div>

                {/* Direct Contact Launcher when unmasked */}
                {unmaskedIds.has(selectedInquiry.id) && (
                  <div className="pt-2 border-t border-[var(--rbpc-divider-subtle)] flex items-center gap-2">
                    {selectedInquiry.contactMethod === "email" ? (
                      <a
                        href={`mailto:${selectedInquiry.contactValue}?subject=Lưu Niên - Phản hồi yêu cầu trải nghiệm ${selectedInquiry.reference}`}
                        className="rbpc-btn rbpc-btn-secondary rbpc-btn-sm min-h-[44px] min-w-[44px] w-full text-xs flex items-center justify-center focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--rbpc-focus)] focus-visible:ring-offset-2"
                      >
                        <Mail className="h-3.5 w-3.5 mr-1" aria-hidden="true" />
                        <span>{locale === "vi" ? "Gửi Email cho khách" : "Email Guest"}</span>
                      </a>
                    ) : (
                      <a
                        href={`tel:${selectedInquiry.contactValue}`}
                        className="rbpc-btn rbpc-btn-secondary rbpc-btn-sm min-h-[44px] min-w-[44px] w-full text-xs flex items-center justify-center focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--rbpc-focus)] focus-visible:ring-offset-2"
                      >
                        <Phone className="h-3.5 w-3.5 mr-1" aria-hidden="true" />
                        <span>{locale === "vi" ? "Gọi điện thoại" : "Call Guest"}</span>
                      </a>
                    )}
                  </div>
                )}
              </div>

              {/* Visitor Note / Message */}
              {selectedInquiry.message && (
                <div className="space-y-1.5">
                  <span className="text-xs font-semibold text-[var(--rbpc-ink)] flex items-center gap-1.5">
                    <MessageCircle className="h-3.5 w-3.5 text-[var(--rbpc-highlight)]" aria-hidden="true" />
                    <span>{locale === "vi" ? "Lời nhắn từ khách gửi:" : "Visitor Message:"}</span>
                  </span>
                  <div className="rounded-xl border border-[var(--rbpc-divider-subtle)] bg-[var(--rbpc-surface)] p-3.5 text-xs text-[var(--rbpc-ink-subtle)] leading-relaxed italic">
                    “{selectedInquiry.message}”
                  </div>
                </div>
              )}

              {/* ===============================================================
                  STATE MACHINE TRANSITION DROPDOWN & FEEDBACK
                  =============================================================== */}
              <div className="space-y-3 pt-3 border-t border-[var(--rbpc-divider)]">
                <span className="text-xs font-semibold text-[var(--rbpc-ink)] uppercase tracking-wider block">
                  {locale === "vi" ? "Chuyển trạng thái xử lý" : "State Transition"}
                </span>

                {VALID_TRANSITIONS[selectedInquiry.status]?.length > 0 ? (
                  <div className="space-y-3">
                    <div className="space-y-1">
                      <label htmlFor="partner-status-select" className="rbpc-sr-only">
                        {locale === "vi" ? "Chọn trạng thái mới" : "Select target status"}
                      </label>
                      <select
                        id="partner-status-select"
                        value={pendingStatus}
                        onChange={(e) => setPendingStatus(e.target.value as InquiryStatus)}
                        className="rbpc-select text-xs font-medium focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--rbpc-focus)] focus-visible:ring-offset-2"
                      >
                        <option value="">
                          {locale === "vi" ? "-- Chọn trạng thái tiếp theo --" : "-- Choose target status --"}
                        </option>
                        {VALID_TRANSITIONS[selectedInquiry.status].map((target) => {
                          const info = getStatusBadgeInfo(target, locale);
                          return (
                            <option key={target} value={target}>
                              {info.label} ({target})
                            </option>
                          );
                        })}
                      </select>
                    </div>

                    {/* Transition Note Input */}
                    {pendingStatus && (
                      <div className="space-y-2">
                        <label
                          htmlFor="partner-transition-note"
                          className="block text-[11px] font-medium text-[var(--rbpc-muted)]"
                        >
                          {locale === "vi"
                            ? "Ghi chú lý do chuyển trạng thái (bắt buộc khi từ chối):"
                            : "Transition note (required if declining):"}
                        </label>
                        <input
                          id="partner-transition-note"
                          type="text"
                          value={transitionNote}
                          onChange={(e) => setTransitionNote(e.target.value)}
                          placeholder={
                            pendingStatus === "declined"
                              ? locale === "vi"
                                ? "Lý do xưởng không tiếp nhận (trùng lịch, hết phôi đúc...)"
                                : "Reason (studio busy, materials out...)"
                              : locale === "vi"
                              ? "Ghi chú: Đã gọi khách, hẹn thứ 7 tuần sau..."
                              : "Note: Called guest, confirmed next Saturday..."
                          }
                          className="rbpc-input text-xs focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--rbpc-focus)] focus-visible:ring-offset-2"
                        />

                        <RbpcButton
                          variant="primary"
                          size="sm"
                          className="w-full justify-center min-h-[44px]"
                          isLoading={isUpdatingStatus}
                          onClick={handleExecuteTransition}
                        >
                          <ArrowRight className="h-3.5 w-3.5 mr-1.5" aria-hidden="true" />
                          <span>
                            {locale === "vi"
                              ? `Xác nhận chuyển sang: ${getStatusBadgeInfo(pendingStatus as InquiryStatus, locale).label}`
                              : `Confirm Transition to ${getStatusBadgeInfo(pendingStatus as InquiryStatus, locale).label}`}
                          </span>
                        </RbpcButton>
                      </div>
                    )}
                  </div>
                ) : (
                  <div className="rounded-lg bg-[var(--rbpc-surface-muted)] p-3 text-xs text-[var(--rbpc-muted)] text-center">
                    {locale === "vi"
                      ? "Hồ sơ đã ở trạng thái lưu trữ cuối cùng (closed)."
                      : "Inquiry has reached its terminal retention state (closed)."}
                  </div>
                )}
              </div>

              {/* ===============================================================
                  INTERNAL PARTNER NOTES (Private CRM Note)
                  =============================================================== */}
              <div className="space-y-2 pt-3 border-t border-[var(--rbpc-divider)]">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-semibold text-[var(--rbpc-ink)] flex items-center gap-1.5">
                    <FileText className="h-3.5 w-3.5 text-[var(--rbpc-primary)]" aria-hidden="true" />
                    <span>{locale === "vi" ? "Ghi chú nội bộ xưởng nghề" : "Internal Studio Notes"}</span>
                  </span>
                  <span className="text-[10px] text-[var(--rbpc-muted)]">
                    {locale === "vi" ? "Chỉ lưu nội bộ" : "Private to studio"}
                  </span>
                </div>

                <textarea
                  rows={2}
                  value={editingNotes}
                  onChange={(e) => setEditingNotes(e.target.value)}
                  placeholder={
                    locale === "vi"
                      ? "Nhập ghi chú cho riêng xưởng (ví dụ: khách muốn mua thêm chuông gió, người già đi kèm...)"
                      : "Private studio notes (e.g. guest wants extra wind chime, elderly guest attending...)"
                  }
                  className="rbpc-textarea text-xs resize-none focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--rbpc-focus)] focus-visible:ring-offset-2"
                />

                <div className="flex justify-end">
                  <RbpcButton
                    variant="secondary"
                    size="sm"
                    className="min-h-[44px]"
                    isLoading={isSavingNotes}
                    onClick={handleSaveNotes}
                  >
                    <Save className="h-3.5 w-3.5 mr-1.5" aria-hidden="true" />
                    <span>{locale === "vi" ? "Lưu ghi chú" : "Save Note"}</span>
                  </RbpcButton>
                </div>
              </div>

              {/* ===============================================================
                  AUDIT LOG TIMELINE
                  =============================================================== */}
              <div className="space-y-2 pt-3 border-t border-[var(--rbpc-divider)]">
                <span className="text-xs font-semibold text-[var(--rbpc-ink)] flex items-center gap-1.5">
                  <History className="h-3.5 w-3.5 text-[var(--rbpc-muted)]" aria-hidden="true" />
                  <span>{locale === "vi" ? "Nhật ký xử lý (Audit Log)" : "Audit Log Timeline"}</span>
                </span>

                <div className="space-y-2 max-h-48 overflow-y-auto pr-1">
                  {selectedInquiry.auditLog && selectedInquiry.auditLog.length > 0 ? (
                    selectedInquiry.auditLog.map((log) => (
                      <div
                        key={log.id}
                        className="rounded-lg border border-[var(--rbpc-divider-subtle)] bg-[var(--rbpc-surface)] p-2.5 text-[11px] space-y-1"
                      >
                        <div className="flex items-center justify-between text-[var(--rbpc-muted)]">
                          <span className="font-semibold text-[var(--rbpc-ink)]">
                            {getStatusBadgeInfo(log.previousStatus, locale).label} →{" "}
                            {getStatusBadgeInfo(log.newStatus, locale).label}
                          </span>
                          <span className="font-mono text-[10px]">
                            {log.timestamp.replace("T", " ").slice(0, 16)}
                          </span>
                        </div>
                        {log.note && (
                          <p className="text-[var(--rbpc-ink-subtle)] italic">
                            “{log.note}”
                          </p>
                        )}
                        {log.actorName && (
                          <span className="text-[10px] text-[var(--rbpc-muted)] block">
                            {locale === "vi" ? "Thực hiện bởi: " : "By: "}
                            {log.actorName}
                          </span>
                        )}
                      </div>
                    ))
                  ) : (
                    <div className="rounded-lg bg-[var(--rbpc-surface)] p-2.5 text-[11px] text-[var(--rbpc-muted)] text-center">
                      {locale === "vi"
                        ? "Chưa có thay đổi trạng thái nào kể từ khi tiếp nhận."
                        : "No status changes recorded yet since submission."}
                    </div>
                  )}
                </div>
              </div>
            </div>
          ) : (
            <div className="rounded-2xl border border-dashed border-[var(--rbpc-divider)] bg-[var(--rbpc-bg)] p-8 text-center text-xs text-[var(--rbpc-muted)] space-y-2">
              <FileText className="h-8 w-8 mx-auto text-[var(--rbpc-muted)] opacity-60" aria-hidden="true" />
              <p className="font-medium text-[var(--rbpc-ink)]">
                {locale === "vi" ? "Chưa chọn yêu cầu nào" : "No Inquiry Selected"}
              </p>
              <p>
                {locale === "vi"
                  ? "Chọn một hồ sơ ở danh sách bên trái để xem đầy đủ chi tiết, mở thông tin liên hệ và chuyển trạng thái."
                  : "Select an inquiry from the left to view details, unmask contact info, and execute state transitions."}
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

PartnerInboxView.displayName = "PartnerInboxView";
