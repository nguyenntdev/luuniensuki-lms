"use client";

import React, { useState, useEffect, useId, Suspense } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import {
  CheckCircle2,
  AlertCircle,
  Calendar,
  Users,
  MessageSquare,
  ShieldCheck,
  Mail,
  Phone,
  MessageCircle,
  Clock,
  Sparkles,
  ArrowRight,
  Search,
  ChevronRight,
  RotateCcw,
  ExternalLink,
  Layers,
  Compass,
  FileCheck2,
} from "lucide-react";
import type {
  InquiryFormValues,
  InquiryStatus,
  InquiryStatusResponse,
  InquirySubmissionResult,
  ContactMethod,
  RbpcLocale,
} from "@/types/rbpc";
import { getRbpcCopy } from "@/lib/rbpc/copy";
import { cn } from "@/lib/utils";
import { setPageMeta } from "@/lib/seo";
import { RbpcCard, RbpcCardHeader } from "@/components/rbpc/RbpcCard";
import { RbpcButton } from "@/components/rbpc/RbpcButton";
import {
  CURATED_EXPERIENCES,
  CuratedExperienceOption,
  generateClientUuid,
  generatePublicReference,
  generateOpaqueToken,
  validateEmail,
  validatePhone,
  getStoredInquiries,
  saveStoredInquiry,
  submitInquiryToApi,
  fetchInquiryStatusByToken,
} from "@/lib/rbpc/inquiries";

function resolveExperience(slug: string | null): CuratedExperienceOption {
  if (!slug) return CURATED_EXPERIENCES[0];
  const found = CURATED_EXPERIENCES.find(
    (exp) => exp.slug.toLowerCase() === slug.toLowerCase()
  );
  return found || CURATED_EXPERIENCES[0];
}

function getTodayString(): string {
  const d = new Date();
  const year = d.getFullYear();
  const month = String(d.getMonth() + 1).padStart(2, "0");
  const day = String(d.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

const STATUS_BADGES: Record<
  InquiryStatus,
  { labelVi: string; labelEn: string; bg: string; text: string; border: string }
> = {
  new: {
    labelVi: "Mới tiếp nhận",
    labelEn: "Newly Received",
    bg: "bg-blue-500/10",
    text: "text-blue-800 dark:text-blue-300",
    border: "border-blue-500/30",
  },
  contacted: {
    labelVi: "Đã liên hệ",
    labelEn: "Contacted",
    bg: "bg-amber-500/10",
    text: "text-amber-900 dark:text-amber-300",
    border: "border-amber-500/30",
  },
  confirmed: {
    labelVi: "Đã xác nhận",
    labelEn: "Confirmed",
    bg: "bg-emerald-500/10",
    text: "text-emerald-800 dark:text-emerald-300",
    border: "border-emerald-500/30",
  },
  declined: {
    labelVi: "Đã từ chối",
    labelEn: "Declined",
    bg: "bg-rose-500/10",
    text: "text-rose-800 dark:text-rose-300",
    border: "border-rose-500/30",
  },
  closed: {
    labelVi: "Đã kết thúc",
    labelEn: "Closed",
    bg: "bg-slate-500/10",
    text: "text-slate-700 dark:text-slate-300",
    border: "border-slate-500/30",
  },
};

function InquiriesContent() {
  const searchParams = useSearchParams();
  const expParam = searchParams?.get("experience") || searchParams?.get("exp");
  const refParam = searchParams?.get("ref") || searchParams?.get("token");
  const tabParam = searchParams?.get("tab");

  const [locale, setLocale] = useState<RbpcLocale>("vi");
  const copy = getRbpcCopy(locale);

  // Active top tab: "submit" | "track"
  const [activeTab, setActiveTab] = useState<"submit" | "track">(
    tabParam === "track" || Boolean(refParam) ? "track" : "submit"
  );

  // Selected Experience
  const [selectedExperience, setSelectedExperience] = useState<CuratedExperienceOption>(
    resolveExperience(expParam)
  );

  // Form Field States
  const [name, setName] = useState("");
  const [contactMethod, setContactMethod] = useState<ContactMethod>("phone");
  const [contactValue, setContactValue] = useState("");
  const [preferredDate, setPreferredDate] = useState("");
  const [partySize, setPartySize] = useState(2);
  const [message, setMessage] = useState("");

  // MANDATORY: Unchecked by default per Master Spec §5.1
  const [consentAccepted, setConsentAccepted] = useState(false);
  const [privacyAccepted, setPrivacyAccepted] = useState(false);

  // Client idempotency key per form session
  const [idempotencyKey, setIdempotencyKey] = useState("");

  // Validation errors
  const [formErrors, setFormErrors] = useState<Record<string, string>>({});
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Submission result & acknowledgment screen
  const [submissionResult, setSubmissionResult] = useState<InquirySubmissionResult | null>(null);

  // Status Lookup State
  const [lookupToken, setLookupToken] = useState(refParam || "");
  const [isLookingUp, setIsLookingUp] = useState(false);
  const [lookupResult, setLookupResult] = useState<InquiryStatusResponse | null>(null);
  const [lookupError, setLookupError] = useState<string | null>(null);

  // Stored historical tokens
  const [storedInquiries, setStoredInquiries] = useState<
    Array<{ reference: string; statusToken: string; experienceTitle: string; createdAt: string }>
  >([]);

  // Initialize idempotency key and stored inquiries on mount
  useEffect(() => {
    setIdempotencyKey(generateClientUuid());
    setStoredInquiries(getStoredInquiries());

    setPageMeta({
      title:
        locale === "vi"
          ? "Đăng ký yêu cầu & Tra cứu lịch trải nghiệm — LƯU NIÊN"
          : "Experience Inquiry & Tracking — LƯU NIÊN",
      description:
        locale === "vi"
          ? "Cổng đăng ký yêu cầu trải nghiệm văn hóa cùng nghệ nhân Huế và tra cứu trạng thái hồ sơ theo thời gian thực."
          : "Submit and track verified cultural workshop availability inquiries directly with living master artisans in Hue.",
      path: "/rbpc/inquiries",
    });
  }, [locale]);

  // Sync if query param changes
  useEffect(() => {
    if (expParam) {
      setSelectedExperience(resolveExperience(expParam));
    }
    if (refParam) {
      const token = refParam.trim();
      setLookupToken(token);
      if (token) {
        setIsLookingUp(true);
        setLookupError(null);
        setLookupResult(null);
        fetchInquiryStatusByToken(token)
          .then((res) => setLookupResult(res))
          .catch((err) => {
            setLookupError(
              err instanceof Error
                ? err.message
                : locale === "vi"
                ? "Không tìm thấy hồ sơ yêu cầu tương ứng với mã cung cấp."
                : "No inquiry found matching the provided reference code."
            );
          })
          .finally(() => setIsLookingUp(false));
      }
    }
  }, [expParam, refParam, locale]);

  // Validate form inputs
  const validateForm = (): boolean => {
    const errors: Record<string, string> = {};

    if (!name.trim()) {
      errors.name = copy.inquiry.fields.name.error;
    } else if (name.trim().length < 2) {
      errors.name =
        locale === "vi"
          ? "Tên người liên hệ quá ngắn (tối thiểu 2 ký tự)."
          : "Name is too short (minimum 2 characters).";
    }

    if (!contactValue.trim()) {
      errors.contactValue =
        contactMethod === "email"
          ? copy.inquiry.fields.email.error
          : copy.inquiry.fields.phone.error;
    } else {
      if (contactMethod === "email" && !validateEmail(contactValue)) {
        errors.contactValue = copy.inquiry.fields.email.error;
      }
      if (
        (contactMethod === "phone" || contactMethod === "zalo") &&
        !validatePhone(contactValue)
      ) {
        errors.contactValue = copy.inquiry.fields.phone.error;
      }
    }

    if (preferredDate && preferredDate < getTodayString()) {
      errors.preferredDate =
        locale === "vi"
          ? "Ngày dự kiến không thể trong quá khứ."
          : "Preferred date cannot be in the past.";
    }

    if (partySize < 1 || partySize > selectedExperience.maxPartySize) {
      errors.partySize =
        locale === "vi"
          ? `Số lượng khách từ 1 đến ${selectedExperience.maxPartySize} người.`
          : `Party size must be between 1 and ${selectedExperience.maxPartySize}.`;
    }

    if (!consentAccepted || !privacyAccepted) {
      errors.consent =
        locale === "vi"
          ? "Vui lòng xác nhận đồng thuận chia sẻ thông tin và chính sách riêng tư."
          : "Please accept the contact sharing consent and privacy policy.";
    }

    setFormErrors(errors);
    return Object.keys(errors).length === 0;
  };

  // Submit Handler
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!validateForm()) return;

    setIsSubmitting(true);
    setFormErrors({});

    try {
      const payload = {
        experience_slug: selectedExperience.slug,
        contact: {
          name: name.trim(),
          method: contactMethod,
          value: contactValue.trim(),
        },
        preferred_date: preferredDate || null,
        party_size: partySize,
        message: message.trim() || null,
        consent: {
          accepted: consentAccepted,
          privacy_accepted: privacyAccepted,
          version: "2026.1_v1",
        },
        idempotency_key: idempotencyKey,
      };

      const result = await submitInquiryToApi(payload);
      setSubmissionResult(result);

      // Save to client localStorage for quick tracking
      saveStoredInquiry({
        reference: result.reference,
        statusToken: result.statusToken,
        experienceSlug: selectedExperience.slug,
        experienceTitle:
          locale === "vi" ? selectedExperience.titleVi : selectedExperience.titleEn,
        createdAt: result.createdAt,
      });
      setStoredInquiries(getStoredInquiries());
    } catch (err) {
      const msg =
        err instanceof Error
          ? err.message
          : locale === "vi"
          ? "Không thể gửi yêu cầu lúc này. Vui lòng thử lại sau."
          : "Failed to submit inquiry. Please try again later.";
      setFormErrors({ submit: msg });
    } finally {
      setIsSubmitting(false);
    }
  };

  // Status Lookup Handler
  const handlePerformLookup = async (tokenToLookup?: string) => {
    const rawToken = tokenToLookup || lookupToken;
    const token = rawToken.trim();
    if (!token) {
      setLookupError(
        locale === "vi"
          ? "Vui lòng nhập mã tham chiếu hoặc mã bí mật để tra cứu."
          : "Please enter a reference code or secret status token."
      );
      return;
    }

    setIsLookingUp(true);
    setLookupError(null);
    setLookupResult(null);

    try {
      const res = await fetchInquiryStatusByToken(token);
      setLookupResult(res);
    } catch (err) {
      setLookupError(
        err instanceof Error
          ? err.message
          : locale === "vi"
          ? "Không tìm thấy hồ sơ yêu cầu tương ứng với mã cung cấp."
          : "No inquiry found matching the provided reference code."
      );
    } finally {
      setIsLookingUp(false);
    }
  };

  const handleResetForm = () => {
    setSubmissionResult(null);
    setName("");
    setContactValue("");
    setPreferredDate("");
    setPartySize(2);
    setMessage("");
    setConsentAccepted(false);
    setPrivacyAccepted(false);
    setIdempotencyKey(generateClientUuid());
    setFormErrors({});
  };

  return (
    <div className="rbpc-theme min-h-screen bg-[var(--rbpc-bg)] text-[var(--rbpc-ink)] py-8 sm:py-12 px-4 sm:px-6 lg:px-8">
      <div className="mx-auto max-w-4xl space-y-8">
        {/* Navigation Breadcrumb & Locale Bar */}
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
              href="/experiences"
              className="hover:text-[var(--rbpc-primary)] transition-colors"
            >
              {copy.nav.experiences}
            </Link>
            <ChevronRight className="h-3 w-3" aria-hidden="true" />
            <span className="font-semibold text-[var(--rbpc-ink)]">
              {locale === "vi" ? "Yêu cầu trải nghiệm" : "Experience Inquiries"}
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
            <Link
              href="/rbpc/partner"
              className="inline-flex items-center gap-1.5 rounded-full border border-[var(--rbpc-primary-border)] bg-[var(--rbpc-primary-subtle)] px-3 py-1 text-xs font-semibold text-[var(--rbpc-primary)] hover:bg-[var(--rbpc-primary)] hover:text-white transition-all"
            >
              <span>{copy.nav.partnerInbox}</span>
              <ArrowRight className="h-3 w-3" aria-hidden="true" />
            </Link>
          </div>
        </div>

        {/* Page Header Banner */}
        <div className="space-y-3">
          <div className="inline-flex items-center gap-2 rounded-full border border-[var(--rbpc-primary-border)] bg-[var(--rbpc-primary-subtle)] px-3 py-1 text-xs font-semibold text-[var(--rbpc-primary)]">
            <Sparkles className="h-3.5 w-3.5" aria-hidden="true" />
            <span>
              {locale === "vi"
                ? "Kết nối trực tiếp nghệ nhân — Minh bạch & Không thu phí trung gian"
                : "Direct Artisan Connection — Transparent & Zero Intermediary Fees"}
            </span>
          </div>

          <h1 className="font-serif text-3xl sm:text-4xl lg:text-5xl font-bold tracking-tight text-[var(--rbpc-ink)]">
            {locale === "vi"
              ? "Cổng Yêu Cầu & Tra Cứu Lịch Trải Nghiệm"
              : "Experience Inquiry & Tracking Portal"}
          </h1>
          <p className="text-sm sm:text-base text-[var(--rbpc-ink-subtle)] max-w-2xl leading-relaxed">
            {locale === "vi"
              ? "Gửi yêu cầu lịch trải nghiệm trực tiếp đến nghệ nhân và theo dõi trạng thái hồ sơ theo thời gian thực mà không cần thanh toán trước."
              : "Submit availability inquiries directly to craft masters and track request progress in real time with zero upfront transaction pressure."}
          </p>
        </div>

        {/* Mode Switcher Tabs */}
        <div
          role="tablist"
          aria-label="Inquiry Navigation Tabs"
          className="flex border-b border-[var(--rbpc-divider)] gap-4 sm:gap-8 text-sm font-semibold"
        >
          <button
            type="button"
            role="tab"
            aria-selected={activeTab === "submit"}
            onClick={() => setActiveTab("submit")}
            className={cn(
              "pb-3 pt-1 border-b-2 transition-all min-h-[44px] flex items-center gap-2",
              activeTab === "submit"
                ? "border-[var(--rbpc-primary)] text-[var(--rbpc-primary)]"
                : "border-transparent text-[var(--rbpc-muted)] hover:text-[var(--rbpc-ink)]"
            )}
          >
            <Calendar className="h-4 w-4" aria-hidden="true" />
            <span>
              {locale === "vi" ? "1. Gửi yêu cầu mới" : "1. Submit New Inquiry"}
            </span>
          </button>

          <button
            type="button"
            role="tab"
            aria-selected={activeTab === "track"}
            onClick={() => setActiveTab("track")}
            className={cn(
              "pb-3 pt-1 border-b-2 transition-all min-h-[44px] flex items-center gap-2",
              activeTab === "track"
                ? "border-[var(--rbpc-primary)] text-[var(--rbpc-primary)]"
                : "border-transparent text-[var(--rbpc-muted)] hover:text-[var(--rbpc-ink)]"
            )}
          >
            <Search className="h-4 w-4" aria-hidden="true" />
            <span>
              {locale === "vi"
                ? "2. Tra cứu tiến độ hồ sơ"
                : "2. Track Existing Inquiry"}
            </span>
            {storedInquiries.length > 0 && (
              <span className="rounded-full bg-[var(--rbpc-primary-subtle)] text-[var(--rbpc-primary)] px-2 py-0.5 text-xs font-mono font-bold">
                {storedInquiries.length}
              </span>
            )}
          </button>
        </div>

        {/* ===================================================================
            TAB 1: SUBMISSION FORM & ACKNOWLEDGMENT VIEW
            =================================================================== */}
        {activeTab === "submit" && (
          <div className="space-y-6">
            {!submissionResult ? (
              <RbpcCard elevation="surface" padding="responsive" className="space-y-6">
                <RbpcCardHeader className="space-y-2 border-b border-[var(--rbpc-divider-subtle)] pb-4">
                  <h2 className="font-serif text-xl sm:text-2xl font-bold text-[var(--rbpc-ink)]">
                    {copy.inquiry.modalTitle}
                  </h2>
                  <p className="text-xs sm:text-sm text-[var(--rbpc-muted)]">
                    {copy.inquiry.modalSubtitle}
                  </p>
                </RbpcCardHeader>

                <form onSubmit={handleSubmit} className="space-y-6" noValidate>
                  {/* Global Submission Error Banner */}
                  {formErrors.submit && (
                    <div
                      role="alert"
                      aria-live="polite"
                      className="flex items-start gap-3 rounded-lg border border-[var(--rbpc-error-border)] bg-[var(--rbpc-error-subtle)] p-4 text-xs text-[var(--rbpc-error)]"
                    >
                      <AlertCircle className="h-4 w-4 shrink-0 mt-0.5" aria-hidden="true" />
                      <span>{formErrors.submit}</span>
                    </div>
                  )}

                  {/* Experience Selector */}
                  <div className="space-y-2">
                    <label
                      htmlFor="inquiry-experience-select"
                      className="block text-xs sm:text-sm font-semibold text-[var(--rbpc-ink)]"
                    >
                      {locale === "vi"
                        ? "Chọn trải nghiệm văn hóa (*)"
                        : "Select Cultural Experience (*)"}
                    </label>
                    <select
                      id="inquiry-experience-select"
                      value={selectedExperience.slug}
                      onChange={(e) => setSelectedExperience(resolveExperience(e.target.value))}
                      className="rbpc-select w-full"
                    >
                      {CURATED_EXPERIENCES.map((exp) => (
                        <option key={exp.slug} value={exp.slug}>
                          {locale === "vi" ? exp.titleVi : exp.titleEn} — ({exp.creatorName})
                        </option>
                      ))}
                    </select>

                    {/* Selected Experience Detail Card */}
                    <div className="rounded-lg border border-[var(--rbpc-divider-subtle)] bg-[var(--rbpc-surface-muted)] p-3.5 text-xs text-[var(--rbpc-ink)] space-y-1.5">
                      <div className="flex flex-wrap items-center justify-between gap-2">
                        <span className="font-semibold text-[var(--rbpc-primary)]">
                          {selectedExperience.providerName}
                        </span>
                        <span className="font-mono font-medium text-[var(--rbpc-highlight)]">
                          {selectedExperience.pricingDisplay}
                        </span>
                      </div>
                      <div className="flex flex-wrap items-center gap-4 text-[var(--rbpc-muted)]">
                        <span>
                          {locale === "vi" ? "Địa điểm:" : "Location:"}{" "}
                          <strong className="text-[var(--rbpc-ink)]">
                            {selectedExperience.areaPublic}
                          </strong>
                        </span>
                        <span>
                          {locale === "vi" ? "Thời lượng:" : "Duration:"}{" "}
                          <strong className="text-[var(--rbpc-ink)]">
                            {selectedExperience.durationMinutes} {locale === "vi" ? "phút" : "mins"}
                          </strong>
                        </span>
                      </div>
                      <p className="text-[11px] text-[var(--rbpc-ink-subtle)] italic pt-1">
                        {selectedExperience.notice}
                      </p>
                    </div>
                  </div>

                  {/* Visitor Name Field */}
                  <div className="space-y-1.5">
                    <label
                      htmlFor="inquiry-name"
                      className="block text-xs sm:text-sm font-semibold text-[var(--rbpc-ink)]"
                    >
                      {copy.inquiry.fields.name.label}{" "}
                      <span className="text-[var(--rbpc-error)]">*</span>
                    </label>
                    <input
                      id="inquiry-name"
                      type="text"
                      required
                      value={name}
                      onChange={(e) => {
                        setName(e.target.value);
                        if (formErrors.name) setFormErrors((prev) => ({ ...prev, name: "" }));
                      }}
                      placeholder={copy.inquiry.fields.name.placeholder}
                      aria-invalid={Boolean(formErrors.name)}
                      aria-describedby={formErrors.name ? "inquiry-name-error" : undefined}
                      className={cn(
                        "rbpc-input",
                        formErrors.name && "border-[var(--rbpc-error)] focus:ring-[var(--rbpc-error)]"
                      )}
                    />
                    {formErrors.name && (
                      <p id="inquiry-name-error" className="rbpc-field-error">
                        <AlertCircle className="h-3.5 w-3.5 shrink-0" aria-hidden="true" />
                        <span>{formErrors.name}</span>
                      </p>
                    )}
                  </div>

                  {/* Contact Method Selector & Value */}
                  <div className="space-y-2">
                    <fieldset>
                      <legend className="text-xs sm:text-sm font-semibold text-[var(--rbpc-ink)] mb-2">
                        {locale === "vi"
                          ? "Phương thức liên hệ ưu tiên (*)"
                          : "Preferred Contact Channel (*)"}
                      </legend>

                      <div className="grid grid-cols-3 gap-2">
                        {(["phone", "zalo", "email"] as ContactMethod[]).map((method) => {
                          const isSelected = contactMethod === method;
                          const iconMap = {
                            phone: Phone,
                            zalo: MessageCircle,
                            email: Mail,
                          };
                          const IconComponent = iconMap[method];
                          const labelMap = {
                            phone: locale === "vi" ? "Điện thoại" : "Phone",
                            zalo: "Zalo",
                            email: "Email",
                          };

                          return (
                            <button
                              key={method}
                              type="button"
                              onClick={() => {
                                setContactMethod(method);
                                setFormErrors((prev) => ({ ...prev, contactValue: "" }));
                              }}
                              className={cn(
                                "flex min-h-[44px] items-center justify-center gap-2 rounded-lg border px-3 py-2 text-xs font-semibold transition-all select-none",
                                isSelected
                                  ? "border-[var(--rbpc-primary)] bg-[var(--rbpc-primary)] text-white shadow-sm"
                                  : "border-[var(--rbpc-divider)] bg-[var(--rbpc-surface)] text-[var(--rbpc-ink)] hover:border-[var(--rbpc-primary-border)]"
                              )}
                            >
                              <IconComponent className="h-3.5 w-3.5 shrink-0" aria-hidden="true" />
                              <span>{labelMap[method]}</span>
                            </button>
                          );
                        })}
                      </div>
                    </fieldset>

                    <div className="space-y-1.5 pt-1">
                      <label
                        htmlFor="inquiry-contact-value"
                        className="block text-xs font-semibold text-[var(--rbpc-ink)]"
                      >
                        {contactMethod === "email"
                          ? copy.inquiry.fields.email.label
                          : contactMethod === "zalo"
                          ? "Số điện thoại đăng ký Zalo"
                          : copy.inquiry.fields.phone.label}{" "}
                        <span className="text-[var(--rbpc-error)]">*</span>
                      </label>
                      <input
                        id="inquiry-contact-value"
                        type={contactMethod === "email" ? "email" : "tel"}
                        required
                        value={contactValue}
                        onChange={(e) => {
                          setContactValue(e.target.value);
                          if (formErrors.contactValue)
                            setFormErrors((prev) => ({ ...prev, contactValue: "" }));
                        }}
                        placeholder={
                          contactMethod === "email"
                            ? copy.inquiry.fields.email.placeholder
                            : copy.inquiry.fields.phone.placeholder
                        }
                        aria-invalid={Boolean(formErrors.contactValue)}
                        aria-describedby={
                          formErrors.contactValue ? "inquiry-contact-error" : undefined
                        }
                        className={cn(
                          "rbpc-input",
                          formErrors.contactValue &&
                            "border-[var(--rbpc-error)] focus:ring-[var(--rbpc-error)]"
                        )}
                      />
                      {formErrors.contactValue && (
                        <p id="inquiry-contact-error" className="rbpc-field-error">
                          <AlertCircle className="h-3.5 w-3.5 shrink-0" aria-hidden="true" />
                          <span>{formErrors.contactValue}</span>
                        </p>
                      )}
                    </div>
                  </div>

                  {/* Preferred Date & Party Size Row */}
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                    <div className="space-y-1.5">
                      <label
                        htmlFor="inquiry-preferred-date"
                        className="block text-xs sm:text-sm font-semibold text-[var(--rbpc-ink)]"
                      >
                        {copy.inquiry.fields.preferredDate.label}
                      </label>
                      <div className="relative">
                        <input
                          id="inquiry-preferred-date"
                          type="date"
                          min={getTodayString()}
                          value={preferredDate}
                          onChange={(e) => {
                            setPreferredDate(e.target.value);
                            if (formErrors.preferredDate)
                              setFormErrors((prev) => ({ ...prev, preferredDate: "" }));
                          }}
                          aria-invalid={Boolean(formErrors.preferredDate)}
                          aria-describedby={formErrors.preferredDate ? "inquiry-date-error" : undefined}
                          className={cn(
                            "rbpc-input pr-10",
                            formErrors.preferredDate && "border-[var(--rbpc-error)]"
                          )}
                        />
                        <Calendar
                          className="absolute right-3 top-1/2 -translate-y-1/2 h-4 w-4 text-[var(--rbpc-muted)] pointer-events-none"
                          aria-hidden="true"
                        />
                      </div>
                      <p className="text-[11px] text-[var(--rbpc-muted)]">
                        {copy.inquiry.fields.preferredDate.helper}
                      </p>
                      {formErrors.preferredDate && (
                        <p id="inquiry-date-error" className="rbpc-field-error">
                          <AlertCircle className="h-3.5 w-3.5 shrink-0" aria-hidden="true" />
                          <span>{formErrors.preferredDate}</span>
                        </p>
                      )}
                    </div>

                    <div className="space-y-1.5">
                      <label
                        htmlFor="inquiry-party-size"
                        className="block text-xs sm:text-sm font-semibold text-[var(--rbpc-ink)]"
                      >
                        {copy.inquiry.fields.partySize.label}{" "}
                        <span className="text-[var(--rbpc-error)]">*</span>
                      </label>
                      <div className="flex items-center gap-3">
                        <button
                          type="button"
                          onClick={() => {
                            setPartySize((p) => Math.max(1, p - 1));
                            if (formErrors.partySize) setFormErrors((prev) => ({ ...prev, partySize: "" }));
                          }}
                          disabled={partySize <= 1}
                          className="flex h-11 w-11 items-center justify-center rounded-lg border border-[var(--rbpc-divider)] bg-[var(--rbpc-surface)] text-base font-bold text-[var(--rbpc-ink)] hover:border-[var(--rbpc-primary-border)] disabled:opacity-40 disabled:cursor-not-allowed select-none"
                          aria-label="Decrease guests"
                        >
                          -
                        </button>
                        <span
                          id="inquiry-party-size"
                          className="flex-1 text-center font-mono text-base font-bold text-[var(--rbpc-primary)]"
                        >
                          {partySize} {locale === "vi" ? "khách" : "guests"}
                        </span>
                        <button
                          type="button"
                          onClick={() => {
                            setPartySize((p) =>
                              Math.min(selectedExperience.maxPartySize, p + 1)
                            );
                            if (formErrors.partySize) setFormErrors((prev) => ({ ...prev, partySize: "" }));
                          }}
                          disabled={partySize >= selectedExperience.maxPartySize}
                          className="flex h-11 w-11 items-center justify-center rounded-lg border border-[var(--rbpc-divider)] bg-[var(--rbpc-surface)] text-base font-bold text-[var(--rbpc-ink)] hover:border-[var(--rbpc-primary-border)] disabled:opacity-40 disabled:cursor-not-allowed select-none"
                          aria-label="Increase guests"
                        >
                          +
                        </button>
                      </div>
                      <p className="text-[11px] text-[var(--rbpc-muted)]">
                        {locale === "vi"
                          ? `Tối đa ${selectedExperience.maxPartySize} khách mỗi buổi.`
                          : `Capped at max ${selectedExperience.maxPartySize} guests.`}
                      </p>
                      {formErrors.partySize && (
                        <p id="inquiry-party-error" className="rbpc-field-error">
                          <AlertCircle className="h-3.5 w-3.5 shrink-0" aria-hidden="true" />
                          <span>{formErrors.partySize}</span>
                        </p>
                      )}
                    </div>
                  </div>

                  {/* Message Field (Optional) */}
                  <div className="space-y-1.5">
                    <div className="flex items-center justify-between">
                      <label
                        htmlFor="inquiry-message"
                        className="block text-xs sm:text-sm font-semibold text-[var(--rbpc-ink)]"
                      >
                        {copy.inquiry.fields.message.label}
                      </label>
                      <span className="text-[11px] text-[var(--rbpc-muted)] font-mono">
                        {message.length}/500
                      </span>
                    </div>
                    <textarea
                      id="inquiry-message"
                      rows={3}
                      maxLength={500}
                      value={message}
                      onChange={(e) => setMessage(e.target.value)}
                      placeholder={copy.inquiry.fields.message.placeholder}
                      className="rbpc-textarea resize-none"
                    />
                    <p className="text-[11px] text-[var(--rbpc-muted)]">
                      {copy.inquiry.fields.message.helper}
                    </p>
                  </div>

                  {/* MANDATORY UNCHECKED Consent Checkboxes */}
                  <div className="space-y-3 pt-3 border-t border-[var(--rbpc-divider-subtle)]">
                    <label
                      htmlFor="inquiry-consent"
                      className="rbpc-checkbox-wrapper group min-h-[44px] flex items-start gap-3 cursor-pointer py-1 select-none"
                    >
                      <input
                        id="inquiry-consent"
                        type="checkbox"
                        required
                        checked={consentAccepted}
                        onChange={(e) => {
                          setConsentAccepted(e.target.checked);
                          if (formErrors.consent)
                            setFormErrors((prev) => ({ ...prev, consent: "" }));
                        }}
                        aria-invalid={Boolean(formErrors.consent)}
                        aria-describedby={formErrors.consent ? "inquiry-consent-error" : undefined}
                        className="rbpc-checkbox mt-0.5 min-h-[20px] min-w-[20px]"
                      />
                      <span className="rbpc-checkbox-label text-xs sm:text-sm">
                        {locale === "vi" ? (
                          <>
                            Tôi đồng ý chia sẻ thông tin liên lạc này với{" "}
                            <strong>{selectedExperience.providerName}</strong> để trao đổi xác
                            nhận lịch trải nghiệm.{" "}
                            <span className="text-[var(--rbpc-error)]">*</span>
                          </>
                        ) : (
                          <>
                            I consent to sharing this contact information with{" "}
                            <strong>{selectedExperience.providerName}</strong> solely to
                            coordinate experience availability.{" "}
                            <span className="text-[var(--rbpc-error)]">*</span>
                          </>
                        )}
                      </span>
                    </label>

                    <label
                      htmlFor="inquiry-privacy"
                      className="rbpc-checkbox-wrapper group min-h-[44px] flex items-start gap-3 cursor-pointer py-1 select-none"
                    >
                      <input
                        id="inquiry-privacy"
                        type="checkbox"
                        required
                        checked={privacyAccepted}
                        onChange={(e) => {
                          setPrivacyAccepted(e.target.checked);
                          if (formErrors.consent)
                            setFormErrors((prev) => ({ ...prev, consent: "" }));
                        }}
                        className="rbpc-checkbox mt-0.5 min-h-[20px] min-w-[20px]"
                      />
                      <span className="rbpc-checkbox-label text-xs sm:text-sm">
                        {locale === "vi" ? (
                          <>
                            Tôi hiểu rằng thông tin được lưu trữ tạm thời theo{" "}
                            <strong className="text-[var(--rbpc-primary)]">
                              Chính sách bảo mật Lưu Niên
                            </strong>
                            , không bán hay chia sẻ cho bên thứ ba, và có quyền xóa sau 24 giờ.{" "}
                            <span className="text-[var(--rbpc-error)]">*</span>
                          </>
                        ) : (
                          <>
                            I acknowledge that my data is held temporarily under the{" "}
                            <strong className="text-[var(--rbpc-primary)]">
                              Lưu Niên Privacy Policy
                            </strong>
                            , never sold to third parties, and eligible for 24h erasure upon request.{" "}
                            <span className="text-[var(--rbpc-error)]">*</span>
                          </>
                        )}
                      </span>
                    </label>

                    {formErrors.consent && (
                      <p id="inquiry-consent-error" className="rbpc-field-error">
                        <AlertCircle className="h-3.5 w-3.5 shrink-0" aria-hidden="true" />
                        <span>{formErrors.consent}</span>
                      </p>
                    )}
                  </div>

                  {/* Idempotency & Form Action Footer */}
                  <div className="pt-4 border-t border-[var(--rbpc-divider)] flex flex-col sm:flex-row items-center justify-between gap-4">
                    <span className="text-[11px] font-mono text-[var(--rbpc-muted)] flex items-center gap-1.5">
                      <ShieldCheck className="h-3.5 w-3.5 text-[var(--rbpc-primary)]" />
                      <span>
                        UUID v4 Idempotency Key: {idempotencyKey.slice(0, 8)}...
                      </span>
                    </span>

                    <RbpcButton
                      type="submit"
                      variant="primary"
                      size="lg"
                      isLoading={isSubmitting}
                      loadingText={copy.cta.submitting}
                      className="w-full sm:w-auto"
                    >
                      <span>{copy.cta.submitInquiry}</span>
                      <ArrowRight className="h-4 w-4 ml-1.5" aria-hidden="true" />
                    </RbpcButton>
                  </div>
                </form>
              </RbpcCard>
            ) : (
              /* =============================================================
                 POST-SUBMISSION ACKNOWLEDGMENT SCREEN (Master Spec §5.3)
                 ============================================================= */
              <RbpcCard elevation="elevated" padding="responsive" className="space-y-6">
                {/* Checkmark Icon & Header */}
                <div className="text-center space-y-2">
                  <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-full bg-emerald-500/10 text-emerald-700 dark:text-emerald-400 shadow-inner">
                    <CheckCircle2 className="h-10 w-10" aria-hidden="true" />
                  </div>
                  <h2 className="font-serif text-2xl sm:text-3xl font-bold text-[var(--rbpc-ink)]">
                    {copy.inquiry.confirmation.title}
                  </h2>
                  <p className="text-sm text-[var(--rbpc-muted)] max-w-lg mx-auto">
                    {copy.inquiry.confirmation.message}
                  </p>
                </div>

                {/* Reference & Status Token Card */}
                <div className="rounded-xl border border-[var(--rbpc-divider)] bg-[var(--rbpc-surface-muted)] p-5 text-center space-y-2">
                  <span className="block text-xs uppercase tracking-wider text-[var(--rbpc-muted)]">
                    {copy.inquiry.confirmation.referencePrefix}
                  </span>
                  <span className="inline-block font-mono text-2xl sm:text-3xl font-bold tracking-widest text-[var(--rbpc-primary)]">
                    {submissionResult.reference}
                  </span>

                  <div className="flex items-center justify-center gap-2 pt-1">
                    <span className="inline-flex items-center gap-1.5 rounded-full border border-blue-500/30 bg-blue-500/10 px-3 py-0.5 text-xs font-semibold text-blue-900 dark:text-blue-300">
                      <Clock className="h-3.5 w-3.5 text-blue-600" aria-hidden="true" />
                      <span>{copy.inquiry.confirmation.statusBadge}</span>
                    </span>
                  </div>

                  <p className="text-[11px] font-mono text-[var(--rbpc-muted)] pt-1">
                    Secret Status Token: {submissionResult.statusToken.slice(0, 16)}...
                  </p>
                </div>

                {/* Transparency Notice Box */}
                <div className="rounded-xl border border-[var(--rbpc-highlight-border)] bg-[var(--rbpc-highlight-subtle)] p-4 text-xs text-[var(--rbpc-ink)] space-y-1.5">
                  <div className="flex items-center gap-2 font-semibold text-[var(--rbpc-highlight)]">
                    <AlertCircle className="h-4 w-4 shrink-0" aria-hidden="true" />
                    <span>
                      {locale === "vi"
                        ? "LƯU Ý QUAN TRỌNG VỀ TÍNH KHẢ DỤNG"
                        : "IMPORTANT NOTICE ON AVAILABILITY"}
                    </span>
                  </div>
                  <p className="leading-relaxed">
                    {locale === "vi"
                      ? "Đây là bước yêu cầu lịch rảnh, CHƯA PHẢI xác nhận đặt chỗ cuối cùng. Xưởng nghề sẽ liên hệ với bạn qua thông tin đã cung cấp trong vòng 24 giờ để thống nhất thời gian và hướng dẫn cụ thể."
                      : "This is an availability inquiry, NOT an instant guaranteed reservation. The workshop coordinator will contact you via your chosen channel within 24 hours to confirm timings."}
                  </p>
                </div>

                {/* Request Summary */}
                <div className="rounded-xl border border-[var(--rbpc-divider-subtle)] bg-[var(--rbpc-surface)] p-4 text-xs space-y-2.5 text-[var(--rbpc-ink)]">
                  <h3 className="font-semibold text-[var(--rbpc-muted)] uppercase tracking-wider text-[11px]">
                    {locale === "vi" ? "Tóm tắt hồ sơ yêu cầu" : "Inquiry Summary"}
                  </h3>
                  <div className="flex justify-between py-1 border-b border-[var(--rbpc-divider-subtle)]">
                    <span className="text-[var(--rbpc-muted)]">
                      {locale === "vi" ? "Trải nghiệm:" : "Experience:"}
                    </span>
                    <span className="font-semibold text-right max-w-[280px]">
                      {locale === "vi"
                        ? selectedExperience.titleVi
                        : selectedExperience.titleEn}
                    </span>
                  </div>
                  <div className="flex justify-between py-1 border-b border-[var(--rbpc-divider-subtle)]">
                    <span className="text-[var(--rbpc-muted)]">
                      {locale === "vi" ? "Nghệ nhân chủ trì:" : "Master Artisan:"}
                    </span>
                    <span className="font-semibold">{selectedExperience.creatorName}</span>
                  </div>
                  <div className="flex justify-between py-1 border-b border-[var(--rbpc-divider-subtle)]">
                    <span className="text-[var(--rbpc-muted)]">
                      {locale === "vi" ? "Cơ sở / Xưởng nghề:" : "Workshop:"}
                    </span>
                    <span>{selectedExperience.providerName}</span>
                  </div>
                  {preferredDate && (
                    <div className="flex justify-between py-1 border-b border-[var(--rbpc-divider-subtle)]">
                      <span className="text-[var(--rbpc-muted)]">
                        {locale === "vi" ? "Ngày dự kiến:" : "Preferred Date:"}
                      </span>
                      <span className="font-mono font-medium">{preferredDate}</span>
                    </div>
                  )}
                  <div className="flex justify-between py-1 border-b border-[var(--rbpc-divider-subtle)]">
                    <span className="text-[var(--rbpc-muted)]">
                      {locale === "vi" ? "Số lượng khách:" : "Party Size:"}
                    </span>
                    <span>{partySize} {locale === "vi" ? "người" : "guest(s)"}</span>
                  </div>
                  <div className="flex justify-between py-1">
                    <span className="text-[var(--rbpc-muted)]">
                      {locale === "vi" ? "Kênh phản hồi:" : "Contact Channel:"}
                    </span>
                    <span className="font-mono font-medium">
                      {contactValue} ({contactMethod})
                    </span>
                  </div>
                </div>

                {/* Action Buttons */}
                <div className="flex flex-col sm:flex-row items-center justify-between gap-3 pt-2">
                  <RbpcButton
                    type="button"
                    variant="secondary"
                    size="md"
                    onClick={handleResetForm}
                    className="w-full sm:w-auto"
                  >
                    <RotateCcw className="h-4 w-4 mr-1.5" aria-hidden="true" />
                    <span>{locale === "vi" ? "Gửi yêu cầu khác" : "Submit Another"}</span>
                  </RbpcButton>

                  <div className="flex flex-col sm:flex-row items-center gap-2 w-full sm:w-auto">
                    <RbpcButton
                      type="button"
                      variant="primary"
                      size="md"
                      onClick={() => {
                        setActiveTab("track");
                        setLookupToken(submissionResult.reference);
                        handlePerformLookup(submissionResult.reference);
                      }}
                      className="w-full sm:w-auto"
                    >
                      <Search className="h-4 w-4 mr-1.5" aria-hidden="true" />
                      <span>{locale === "vi" ? "Tra cứu tiến độ ngay" : "Track Status Now"}</span>
                    </RbpcButton>

                    <RbpcButton
                      variant="subtle"
                      size="md"
                      asChild
                      className="w-full sm:w-auto"
                    >
                      <Link href="/explore">
                        <span>{copy.cta.exploreDeeper}</span>
                        <ChevronRight className="h-4 w-4 ml-1.5" aria-hidden="true" />
                      </Link>
                    </RbpcButton>
                  </div>
                </div>
              </RbpcCard>
            )}
          </div>
        )}

        {/* ===================================================================
            TAB 2: STATUS TRACKING & ZERO PII VERIFICATION VIEW
            =================================================================== */}
        {activeTab === "track" && (
          <div className="space-y-6">
            <RbpcCard elevation="surface" padding="responsive" className="space-y-6">
              <RbpcCardHeader className="space-y-2 border-b border-[var(--rbpc-divider-subtle)] pb-4">
                <h2 className="font-serif text-xl sm:text-2xl font-bold text-[var(--rbpc-ink)] flex items-center gap-2">
                  <FileCheck2 className="h-5 w-5 text-[var(--rbpc-primary)]" />
                  <span>
                    {locale === "vi"
                      ? "Tra cứu trạng thái hồ sơ yêu cầu"
                      : "Lookup Inquiry Status"}
                  </span>
                </h2>
                <p className="text-xs sm:text-sm text-[var(--rbpc-muted)]">
                  {locale === "vi"
                    ? "Nhập mã tham chiếu công khai (VD: INQ-7F89-A23C) hoặc mã bí mật được cấp sau khi gửi."
                    : "Enter your public reference code (e.g. INQ-7F89-A23C) or opaque secret token."}
                </p>
              </RbpcCardHeader>

              {/* Zero PII Invariant Guarantee Callout */}
              <div className="flex items-start gap-2.5 rounded-lg border border-[var(--rbpc-primary-border)] bg-[var(--rbpc-primary-subtle)] p-3.5 text-xs text-[var(--rbpc-ink)] leading-relaxed">
                <ShieldCheck className="h-4 w-4 text-[var(--rbpc-primary)] shrink-0 mt-0.5" aria-hidden="true" />
                <div>
                  <strong className="block text-[var(--rbpc-primary)]">
                    {locale === "vi"
                      ? "Cam kết bảo mật ZERO PII trên cổng tra cứu công khai:"
                      : "ZERO PII Invariant on Public Status Tracking:"}
                  </strong>
                  <span>
                    {locale === "vi"
                      ? "Cổng tra cứu không hiển thị số điện thoại, email, họ tên khách hay ghi chú nội bộ để đảm bảo quyền riêng tư tuyệt đối."
                      : "Public status responses never disclose email, phone, personal names, or partner internal notes."}
                  </span>
                </div>
              </div>

              {/* Search Input Bar */}
              <div className="flex flex-col sm:flex-row gap-3">
                <div className="relative flex-1">
                  <input
                    type="text"
                    value={lookupToken}
                    onChange={(e) => {
                      setLookupToken(e.target.value);
                      if (lookupError) setLookupError(null);
                    }}
                    placeholder={
                      locale === "vi"
                        ? "Nhập mã hồ sơ (VD: INQ-7F89-A23C)..."
                        : "Enter reference (e.g. INQ-7F89-A23C)..."
                    }
                    className="rbpc-input font-mono tracking-wider pl-10"
                    onKeyDown={(e) => {
                      if (e.key === "Enter") {
                        e.preventDefault();
                        handlePerformLookup();
                      }
                    }}
                  />
                  <Search
                    className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-[var(--rbpc-muted)]"
                    aria-hidden="true"
                  />
                </div>

                <RbpcButton
                  type="button"
                  variant="primary"
                  size="md"
                  onClick={() => handlePerformLookup()}
                  isLoading={isLookingUp}
                  loadingText={locale === "vi" ? "Đang tra cứu..." : "Searching..."}
                  className="w-full sm:w-auto"
                >
                  <Search className="h-4 w-4 mr-1.5" aria-hidden="true" />
                  <span>{locale === "vi" ? "Tra cứu" : "Lookup"}</span>
                </RbpcButton>
              </div>

              {/* Lookup Error Message */}
              {lookupError && (
                <div
                  role="alert"
                  aria-live="polite"
                  className="flex items-start gap-2.5 rounded-lg border border-[var(--rbpc-error-border)] bg-[var(--rbpc-error-subtle)] p-3.5 text-xs text-[var(--rbpc-error)]"
                >
                  <AlertCircle className="h-4 w-4 shrink-0 mt-0.5" aria-hidden="true" />
                  <span>{lookupError}</span>
                </div>
              )}

              {/* Quick Select Stored History Tokens */}
              {storedInquiries.length > 0 && (
                <div className="space-y-2 pt-2 border-t border-[var(--rbpc-divider-subtle)]">
                  <span className="text-xs font-semibold text-[var(--rbpc-muted)]">
                    {locale === "vi"
                      ? "Hồ sơ đã gửi từ trình duyệt này:"
                      : "Recently submitted from this device:"}
                  </span>
                  <div className="flex flex-wrap gap-2">
                    {storedInquiries.map((item) => (
                      <button
                        key={item.reference}
                        type="button"
                        onClick={() => {
                          setLookupToken(item.reference);
                          handlePerformLookup(item.reference);
                        }}
                        className="inline-flex items-center gap-1.5 rounded-lg border border-[var(--rbpc-divider)] bg-[var(--rbpc-surface)] px-3 py-1.5 text-xs font-mono font-medium text-[var(--rbpc-ink)] hover:border-[var(--rbpc-primary-border)] hover:bg-[var(--rbpc-primary-subtle)] transition-all"
                      >
                        <Clock className="h-3 w-3 text-[var(--rbpc-primary)]" />
                        <span>{item.reference}</span>
                      </button>
                    ))}
                  </div>
                </div>
              )}

              {/* Lookup Result Card */}
              {lookupResult && (
                <div className="rounded-xl border border-[var(--rbpc-divider)] bg-[var(--rbpc-surface-muted)] p-5 space-y-4">
                  <div className="flex flex-wrap items-center justify-between gap-3 border-b border-[var(--rbpc-divider-subtle)] pb-3">
                    <div>
                      <span className="block text-xs uppercase tracking-wider text-[var(--rbpc-muted)]">
                        {locale === "vi" ? "Mã tham chiếu hồ sơ" : "Reference Code"}
                      </span>
                      <span className="font-mono text-xl sm:text-2xl font-bold text-[var(--rbpc-primary)]">
                        {lookupResult.reference}
                      </span>
                    </div>

                    <div>
                      {(() => {
                        const badge =
                          STATUS_BADGES[lookupResult.status] || STATUS_BADGES.new;
                        return (
                          <span
                            className={cn(
                              "inline-flex items-center gap-1.5 rounded-full border px-3 py-1 text-xs font-semibold",
                              badge.bg,
                              badge.text,
                              badge.border
                            )}
                          >
                            <Clock className="h-3.5 w-3.5" aria-hidden="true" />
                            <span>
                              {locale === "vi" ? badge.labelVi : badge.labelEn}
                            </span>
                          </span>
                        );
                      })()}
                    </div>
                  </div>

                  {/* Status Explanation Message */}
                  <div className="rounded-lg bg-[var(--rbpc-surface)] p-3.5 border border-[var(--rbpc-divider-subtle)] space-y-1">
                    <span className="text-xs font-semibold text-[var(--rbpc-muted)]">
                      {locale === "vi" ? "Thông báo trạng thái:" : "Status Message:"}
                    </span>
                    <p className="text-sm font-medium text-[var(--rbpc-ink)] leading-relaxed">
                      {lookupResult.statusMessage}
                    </p>
                  </div>

                  {/* Safe Public Attributes (Zero PII) */}
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs text-[var(--rbpc-ink)]">
                    <div className="p-3 rounded-lg bg-[var(--rbpc-surface)] border border-[var(--rbpc-divider-subtle)]">
                      <span className="text-[var(--rbpc-muted)] block text-[11px]">
                        {locale === "vi" ? "Trải nghiệm yêu cầu" : "Requested Experience"}
                      </span>
                      <span className="font-semibold">{lookupResult.experienceTitle}</span>
                    </div>

                    <div className="p-3 rounded-lg bg-[var(--rbpc-surface)] border border-[var(--rbpc-divider-subtle)]">
                      <span className="text-[var(--rbpc-muted)] block text-[11px]">
                        {locale === "vi" ? "Số khách tham gia" : "Party Size"}
                      </span>
                      <span className="font-semibold">
                        {lookupResult.partySize ?? "--"}{" "}
                        {locale === "vi" ? "người" : "guest(s)"}
                      </span>
                    </div>

                    {lookupResult.preferredDate && (
                      <div className="p-3 rounded-lg bg-[var(--rbpc-surface)] border border-[var(--rbpc-divider-subtle)]">
                        <span className="text-[var(--rbpc-muted)] block text-[11px]">
                          {locale === "vi" ? "Ngày mong muốn" : "Preferred Date"}
                        </span>
                        <span className="font-mono font-semibold">
                          {lookupResult.preferredDate}
                        </span>
                      </div>
                    )}

                    <div className="p-3 rounded-lg bg-[var(--rbpc-surface)] border border-[var(--rbpc-divider-subtle)]">
                      <span className="text-[var(--rbpc-muted)] block text-[11px]">
                        {locale === "vi" ? "Cập nhật lần cuối" : "Last Updated"}
                      </span>
                      <span className="font-mono">
                        {new Date(lookupResult.lastUpdatedAt).toLocaleString(
                          locale === "vi" ? "vi-VN" : "en-US"
                        )}
                      </span>
                    </div>
                  </div>
                </div>
              )}
            </RbpcCard>
          </div>
        )}
      </div>
    </div>
  );
}

export default function InquiriesPage() {
  return (
    <Suspense
      fallback={
        <div className="rbpc-theme min-h-screen bg-[var(--rbpc-bg)] flex items-center justify-center p-8">
          <div className="h-8 w-8 animate-spin rounded-full border-2 border-[var(--rbpc-primary)] border-t-transparent" />
        </div>
      }
    >
      <InquiriesContent />
    </Suspense>
  );
}
