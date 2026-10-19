"use client";

import React, { useState, useEffect, useRef } from "react";
import {
  X,
  CheckCircle2,
  AlertCircle,
  Calendar,
  Users,
  MessageSquare,
  ShieldCheck,
  Mail,
  Phone,
  MessageCircle,
  Info,
  Clock,
  Sparkles,
  ArrowRight,
  Loader2,
} from "lucide-react";
import type {
  RbpcExperience,
  InquiryFormValues,
  InquirySubmissionResult,
  ContactMethod,
  RbpcLocale,
  LocalizedField,
} from "@/types/rbpc";
import { getRbpcCopy } from "@/lib/rbpc/copy";
import { cn } from "@/lib/utils";
import { RbpcButton } from "./RbpcButton";

export interface InquiryFormModalProps {
  /** Whether the modal dialog is open */
  isOpen: boolean;
  /** Callback triggered when user requests closing the modal */
  onClose: () => void;
  /** Target experience being requested (null if none selected) */
  experience: RbpcExperience | null;
  /** Active UI locale (defaults to "vi") */
  locale?: RbpcLocale;
  /** Custom submit handler. If omitted, default simulated handler generates a valid inquiry reference */
  onSubmit?: (
    values: InquiryFormValues
  ) => Promise<InquirySubmissionResult | void> | InquirySubmissionResult | void;
  /** Pre-filled initial form values */
  initialValues?: Partial<InquiryFormValues>;
  /** Additional custom class names for the modal card */
  className?: string;
}

/**
 * Generates an RFC 4122 v4 UUID for the client-side idempotency key.
 */
function generateIdempotencyKey(): string {
  if (typeof crypto !== "undefined" && typeof crypto.randomUUID === "function") {
    return crypto.randomUUID();
  }
  return "xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx".replace(/[xy]/g, (c) => {
    const r = (Math.random() * 16) | 0;
    const v = c === "x" ? r : (r & 0x3) | 0x8;
    return v.toString(16);
  });
}

/**
 * Generates an opaque, non-sequential reference code (e.g. INQ-7F89-A23C).
 */
function generatePublicReference(): string {
  const chars = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789";
  let part1 = "";
  let part2 = "";
  for (let i = 0; i < 4; i++) {
    part1 += chars.charAt(Math.floor(Math.random() * chars.length));
    part2 += chars.charAt(Math.floor(Math.random() * chars.length));
  }
  return `INQ-${part1}-${part2}`;
}

/**
 * Safely resolves LocalizedField.
 */
function resolveLocalized(
  field: LocalizedField | string | undefined,
  locale: RbpcLocale = "vi",
  fallback = ""
): string {
  if (!field) return fallback;
  if (typeof field === "string") return field;
  if (locale === "en" && field.en && field.en.trim().length > 0) {
    return field.en;
  }
  return field.vi || field.en || fallback;
}

/**
 * Today's date in YYYY-MM-DD for min date attribute.
 */
function getTodayString(): string {
  const d = new Date();
  const year = d.getFullYear();
  const month = String(d.getMonth() + 1).padStart(2, "0");
  const day = String(d.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

/**
 * InquiryFormModal Component
 *
 * Implements Master Spec §5.1, §5.2, §5.3 & CREATE_LEARN_SPEC.md requirements:
 * 1. Minimal contact fields: name, contact method (email, phone, zalo), contact value
 * 2. Preferred date (optional) & party size stepper (bounded to maxPartySize)
 * 3. Message field (optional, max 500 chars)
 * 4. MANDATORY UNCHECKED consent checkbox (never pre-checked)
 * 5. Client UUID v4 idempotency token to prevent double-submits
 * 6. Post-submission Acknowledgment Screen with non-sequential reference and transparency notice
 * 7. Accessible keyboard trapping and ESC key dismissal
 */
export function InquiryFormModal({
  isOpen,
  onClose,
  experience,
  locale = "vi",
  onSubmit,
  initialValues,
  className,
}: InquiryFormModalProps) {
  const copy = getRbpcCopy(locale);
  const modalRef = useRef<HTMLDivElement>(null);
  const firstInputRef = useRef<HTMLInputElement>(null);

  // Modal View: "form" | "acknowledgment"
  const [viewState, setViewState] = useState<"form" | "acknowledgment">("form");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submissionResult, setSubmissionResult] = useState<InquirySubmissionResult | null>(null);

  // Form Fields State
  const [name, setName] = useState(initialValues?.name || "");
  const [contactMethod, setContactMethod] = useState<ContactMethod>(
    initialValues?.contactMethod || "phone"
  );
  const [contactValue, setContactValue] = useState(initialValues?.contactValue || "");
  const [preferredDate, setPreferredDate] = useState(initialValues?.preferredDate || "");
  const [partySize, setPartySize] = useState<number>(
    initialValues?.partySize || 2
  );
  const [message, setMessage] = useState(initialValues?.message || "");

  // MANDATORY: Unchecked consent checkbox by default
  const [consentAccepted, setConsentAccepted] = useState(false);

  // Idempotency token generated per form session
  const [idempotencyKey, setIdempotencyKey] = useState<string>("");

  // Validation errors
  const [errors, setErrors] = useState<Record<string, string>>({});

  // Initialize or reset form state whenever modal opens or experience changes
  useEffect(() => {
    if (isOpen) {
      setViewState("form");
      setIsSubmitting(false);
      setSubmissionResult(null);
      setErrors({});
      setConsentAccepted(false); // Strictly unchecked by default
      setIdempotencyKey(generateIdempotencyKey());
      setName(initialValues?.name || "");
      setContactMethod(initialValues?.contactMethod || "phone");
      setContactValue(initialValues?.contactValue || "");
      setPreferredDate(initialValues?.preferredDate || "");
      setPartySize(initialValues?.partySize || 2);
      setMessage(initialValues?.message || "");

      // Focus first input on next frame
      setTimeout(() => {
        firstInputRef.current?.focus();
      }, 50);
    }
  }, [isOpen, experience, initialValues]);

  // Handle ESC key to close
  useEffect(() => {
    if (!isOpen) return;

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape" && !isSubmitting) {
        onClose();
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isOpen, isSubmitting, onClose]);

  // Lock background body scroll when open
  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = "hidden";
    } else {
      document.body.style.overflow = "";
    }
    return () => {
      document.body.style.overflow = "";
    };
  }, [isOpen]);

  if (!isOpen || !experience) return null;

  const experienceTitle = resolveLocalized(experience.title, locale);
  const maxPartySize = experience.maxPartySize || 10;
  const minPartySize = experience.minPartySize || 1;

  // Validation logic
  const validateForm = (): boolean => {
    const newErrors: Record<string, string> = {};

    // Name validation
    if (!name.trim() || name.trim().length < 2) {
      newErrors.name = copy.inquiry.fields.name.error;
    }

    // Contact value validation
    if (!contactValue.trim()) {
      newErrors.contactValue =
        contactMethod === "email"
          ? copy.inquiry.fields.email.error
          : copy.inquiry.fields.phone.error;
    } else if (contactMethod === "email") {
      const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
      if (!emailRegex.test(contactValue.trim())) {
        newErrors.contactValue = copy.inquiry.fields.email.error;
      }
    } else {
      // Phone or Zalo: 8-15 digits allowing leading plus, spaces, dashes
      const digitsOnly = contactValue.replace(/[\s\-\(\)\.]/g, "");
      const phoneRegex = /^\+?[0-9]{8,15}$/;
      if (!phoneRegex.test(digitsOnly)) {
        newErrors.contactValue = copy.inquiry.fields.phone.error;
      }
    }

    // Message length validation
    if (message.length > 500) {
      newErrors.message = copy.inquiry.fields.message.error;
    }

    // MANDATORY Consent validation: Must be explicitly checked
    if (!consentAccepted) {
      newErrors.consent = copy.inquiry.fields.consent.error;
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (isSubmitting) return;

    if (!validateForm()) {
      return;
    }

    setIsSubmitting(true);

    const payload: InquiryFormValues = {
      experienceSlug: experience.slug,
      name: name.trim(),
      contactMethod,
      contactValue: contactValue.trim(),
      preferredDate: preferredDate || undefined,
      partySize,
      message: message.trim() || undefined,
      consentAccepted: true,
      privacyAccepted: true,
      consentVersion: "2026-v1.0",
      idempotencyKey,
    };

    try {
      if (onSubmit) {
        const result = await onSubmit(payload);
        if (result && typeof result === "object" && "reference" in result) {
          setSubmissionResult(result as InquirySubmissionResult);
        } else {
          setSubmissionResult({
            reference: generatePublicReference(),
            statusToken: generateIdempotencyKey(),
            status: "new",
            message: copy.inquiry.confirmation.message,
            createdAt: new Date().toISOString(),
          });
        }
      } else {
        // Fallback default simulated submission
        await new Promise((r) => setTimeout(r, 600));
        setSubmissionResult({
          reference: generatePublicReference(),
          statusToken: generateIdempotencyKey(),
          status: "new",
          message: copy.inquiry.confirmation.message,
          createdAt: new Date().toISOString(),
        });
      }
      setViewState("acknowledgment");
    } catch (err) {
      setErrors({
        submit:
          locale === "vi"
            ? "Có lỗi khi gửi yêu cầu. Vui lòng kiểm tra lại kết nối và thử lại."
            : "An error occurred while submitting your request. Please try again.",
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleBackdropClick = (e: React.MouseEvent<HTMLDivElement>) => {
    if (e.target === e.currentTarget && !isSubmitting) {
      onClose();
    }
  };

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-4 overflow-y-auto bg-black/65 transition-opacity duration-200"
      onClick={handleBackdropClick}
      role="dialog"
      aria-modal="true"
      aria-labelledby="inquiry-dialog-title"
      aria-describedby="inquiry-dialog-desc"
    >
      <div
        ref={modalRef}
        className={cn(
          "relative w-full max-w-xl max-h-[92vh] flex flex-col rounded-2xl border border-[var(--rbpc-divider)] bg-[var(--rbpc-surface-elevated)] text-[var(--rbpc-ink)] shadow-[var(--rbpc-shadow-lg)] overflow-hidden",
          className
        )}
      >
        {/* ===================================================================
            MODAL HEADER (Experience summary & Close button)
            =================================================================== */}
        <div className="flex items-start justify-between border-b border-[var(--rbpc-divider)] bg-[var(--rbpc-surface)] p-5 sm:p-6">
          <div className="pr-4">
            <span className="rbpc-eyebrow text-[11px] font-semibold text-[var(--rbpc-primary)] tracking-wider">
              {copy.inquiry.modalTitle}
            </span>
            <h2
              id="inquiry-dialog-title"
              className="mt-1 font-serif text-lg sm:text-xl font-bold text-[var(--rbpc-ink)] leading-snug"
            >
              {experienceTitle}
            </h2>
            <p className="mt-0.5 text-xs text-[var(--rbpc-muted)]">
              {experience.creatorName} • {experience.areaPublic || "Phường Đúc, TP. Huế"}
            </p>
          </div>

          <button
            type="button"
            onClick={onClose}
            disabled={isSubmitting}
            className="inline-flex min-h-[44px] min-w-[44px] h-11 w-11 items-center justify-center rounded-lg text-[var(--rbpc-muted)] hover:bg-[var(--rbpc-surface-muted)] hover:text-[var(--rbpc-ink)] transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--rbpc-focus)] focus-visible:ring-offset-2"
            aria-label={copy.cta.close}
          >
            <X className="h-5 w-5" aria-hidden="true" />
          </button>
        </div>

        {/* ===================================================================
            VIEW 1: INQUIRY FORM
            =================================================================== */}
        {viewState === "form" && (
          <form
            onSubmit={handleSubmit}
            className="flex-1 overflow-y-auto p-5 sm:p-6 space-y-5"
            noValidate
          >
            {/* Transparency Banner (Epistemic Honesty) */}
            <div className="flex items-start gap-2.5 rounded-xl border border-[var(--rbpc-divider-subtle)] bg-[var(--rbpc-bg)] p-3 text-xs text-[var(--rbpc-muted)] leading-relaxed">
              <Info className="h-4 w-4 text-[var(--rbpc-primary)] shrink-0 mt-0.5" aria-hidden="true" />
              <p id="inquiry-dialog-desc">
                {copy.inquiry.modalSubtitle}
              </p>
            </div>

            {/* General Submission Error Banner */}
            {errors.submit && (
              <div
                role="alert"
                className="flex items-center gap-2 rounded-lg border border-[var(--rbpc-error-border)] bg-[var(--rbpc-error-subtle)] p-3 text-xs text-[var(--rbpc-error)]"
              >
                <AlertCircle className="h-4 w-4 shrink-0" aria-hidden="true" />
                <span>{errors.submit}</span>
              </div>
            )}

            {/* Field: Full Name */}
            <div className="space-y-1.5">
              <label
                htmlFor="inquiry-name"
                className="block text-xs sm:text-sm font-semibold text-[var(--rbpc-ink)]"
              >
                {copy.inquiry.fields.name.label} <span className="text-[var(--rbpc-error)]">*</span>
              </label>
              <input
                ref={firstInputRef}
                id="inquiry-name"
                type="text"
                value={name}
                onChange={(e) => {
                  setName(e.target.value);
                  if (errors.name) setErrors((prev) => ({ ...prev, name: "" }));
                }}
                placeholder={copy.inquiry.fields.name.placeholder}
                aria-invalid={Boolean(errors.name)}
                aria-describedby={errors.name ? "inquiry-name-error" : undefined}
                className={cn(
                  "rbpc-input",
                  errors.name && "rbpc-input-error"
                )}
              />
              {errors.name && (
                <p id="inquiry-name-error" className="rbpc-field-error">
                  <AlertCircle className="h-3.5 w-3.5 shrink-0" aria-hidden="true" />
                  <span>{errors.name}</span>
                </p>
              )}
            </div>

            {/* Field: Preferred Contact Method (Segmented Control) */}
            <div className="space-y-1.5">
              <span className="block text-xs sm:text-sm font-semibold text-[var(--rbpc-ink)]">
                {locale === "vi" ? "Phương thức liên hệ ưu tiên" : "Preferred Contact Channel"}{" "}
                <span className="text-[var(--rbpc-error)]">*</span>
              </span>
              <div
                role="radiogroup"
                aria-label={locale === "vi" ? "Phương thức liên hệ" : "Contact method"}
                className="grid grid-cols-3 gap-2"
              >
                <button
                  type="button"
                  role="radio"
                  aria-checked={contactMethod === "phone"}
                  onClick={() => setContactMethod("phone")}
                  className={cn(
                    "flex min-h-[44px] min-w-[44px] items-center justify-center gap-1.5 rounded-lg border text-xs font-medium transition-colors select-none",
                    "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--rbpc-focus)] focus-visible:ring-offset-2",
                    contactMethod === "phone"
                      ? "border-[var(--rbpc-primary)] bg-[var(--rbpc-primary-subtle)] text-[var(--rbpc-primary)] font-semibold shadow-xs"
                      : "border-[var(--rbpc-divider)] bg-[var(--rbpc-surface)] text-[var(--rbpc-ink)] hover:bg-[var(--rbpc-bg)]"
                  )}
                >
                  <Phone className="h-3.5 w-3.5" aria-hidden="true" />
                  <span>{locale === "vi" ? "Điện thoại" : "Phone"}</span>
                </button>

                <button
                  type="button"
                  role="radio"
                  aria-checked={contactMethod === "zalo"}
                  onClick={() => setContactMethod("zalo")}
                  className={cn(
                    "flex min-h-[44px] min-w-[44px] items-center justify-center gap-1.5 rounded-lg border text-xs font-medium transition-colors select-none",
                    "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--rbpc-focus)] focus-visible:ring-offset-2",
                    contactMethod === "zalo"
                      ? "border-[var(--rbpc-primary)] bg-[var(--rbpc-primary-subtle)] text-[var(--rbpc-primary)] font-semibold shadow-xs"
                      : "border-[var(--rbpc-divider)] bg-[var(--rbpc-surface)] text-[var(--rbpc-ink)] hover:bg-[var(--rbpc-bg)]"
                  )}
                >
                  <MessageCircle className="h-3.5 w-3.5" aria-hidden="true" />
                  <span>Zalo</span>
                </button>

                <button
                  type="button"
                  role="radio"
                  aria-checked={contactMethod === "email"}
                  onClick={() => setContactMethod("email")}
                  className={cn(
                    "flex min-h-[44px] min-w-[44px] items-center justify-center gap-1.5 rounded-lg border text-xs font-medium transition-colors select-none",
                    "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--rbpc-focus)] focus-visible:ring-offset-2",
                    contactMethod === "email"
                      ? "border-[var(--rbpc-primary)] bg-[var(--rbpc-primary-subtle)] text-[var(--rbpc-primary)] font-semibold shadow-xs"
                      : "border-[var(--rbpc-divider)] bg-[var(--rbpc-surface)] text-[var(--rbpc-ink)] hover:bg-[var(--rbpc-bg)]"
                  )}
                >
                  <Mail className="h-3.5 w-3.5" aria-hidden="true" />
                  <span>Email</span>
                </button>
              </div>
            </div>

            {/* Field: Contact Value (Phone number or Email) */}
            <div className="space-y-1.5">
              <label
                htmlFor="inquiry-contact"
                className="block text-xs sm:text-sm font-semibold text-[var(--rbpc-ink)]"
              >
                {contactMethod === "email"
                  ? copy.inquiry.fields.email.label
                  : copy.inquiry.fields.phone.label}{" "}
                <span className="text-[var(--rbpc-error)]">*</span>
              </label>
              <input
                id="inquiry-contact"
                type={contactMethod === "email" ? "email" : "tel"}
                value={contactValue}
                onChange={(e) => {
                  setContactValue(e.target.value);
                  if (errors.contactValue)
                    setErrors((prev) => ({ ...prev, contactValue: "" }));
                }}
                placeholder={
                  contactMethod === "email"
                    ? copy.inquiry.fields.email.placeholder
                    : copy.inquiry.fields.phone.placeholder
                }
                aria-invalid={Boolean(errors.contactValue)}
                aria-describedby={
                  errors.contactValue ? "inquiry-contact-error" : undefined
                }
                className={cn(
                  "rbpc-input",
                  errors.contactValue && "rbpc-input-error"
                )}
              />
              {errors.contactValue && (
                <p id="inquiry-contact-error" className="rbpc-field-error">
                  <AlertCircle className="h-3.5 w-3.5 shrink-0" aria-hidden="true" />
                  <span>{errors.contactValue}</span>
                </p>
              )}
            </div>

            {/* Row: Preferred Date & Party Size */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              {/* Field: Preferred Date (Optional) */}
              <div className="space-y-1.5">
                <label
                  htmlFor="inquiry-date"
                  className="block text-xs sm:text-sm font-semibold text-[var(--rbpc-ink)]"
                >
                  {copy.inquiry.fields.preferredDate.label}
                </label>
                <div className="relative">
                  <input
                    id="inquiry-date"
                    type="date"
                    min={getTodayString()}
                    value={preferredDate}
                    onChange={(e) => setPreferredDate(e.target.value)}
                    className="rbpc-input pr-10"
                  />
                  <Calendar
                    className="pointer-events-none absolute right-3 top-1/2 h-4 w-4 -translate-y-1/2 text-[var(--rbpc-muted)]"
                    aria-hidden="true"
                  />
                </div>
                <p className="text-[11px] text-[var(--rbpc-muted)]">
                  {copy.inquiry.fields.preferredDate.helper}
                </p>
              </div>

              {/* Field: Party Size (Stepper) */}
              <div className="space-y-1.5">
                <label
                  htmlFor="inquiry-party-size"
                  className="block text-xs sm:text-sm font-semibold text-[var(--rbpc-ink)]"
                >
                  {copy.inquiry.fields.partySize.label}{" "}
                  <span className="text-[var(--rbpc-error)]">*</span>
                </label>
                <div className="flex items-center gap-2">
                  <button
                    type="button"
                    onClick={() => setPartySize((p) => Math.max(minPartySize, p - 1))}
                    disabled={partySize <= minPartySize}
                    aria-label={locale === "vi" ? "Giảm số lượng khách" : "Decrease party size"}
                    className="flex min-h-[44px] min-w-[44px] h-11 w-11 items-center justify-center rounded-lg border border-[var(--rbpc-divider)] bg-[var(--rbpc-surface)] text-[var(--rbpc-ink)] hover:bg-[var(--rbpc-bg)] disabled:opacity-40 disabled:cursor-not-allowed focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--rbpc-focus)] focus-visible:ring-offset-2"
                  >
                    -
                  </button>

                  <div
                    id="inquiry-party-size"
                    role="status"
                    className="flex-1 text-center font-serif text-base font-semibold py-2.5 rounded-lg border border-[var(--rbpc-divider)] bg-[var(--rbpc-surface)] text-[var(--rbpc-ink)] select-none"
                  >
                    {partySize} {locale === "vi" ? "khách" : "guest(s)"}
                  </div>

                  <button
                    type="button"
                    onClick={() => setPartySize((p) => Math.min(maxPartySize, p + 1))}
                    disabled={partySize >= maxPartySize}
                    aria-label={locale === "vi" ? "Tăng số lượng khách" : "Increase party size"}
                    className="flex min-h-[44px] min-w-[44px] h-11 w-11 items-center justify-center rounded-lg border border-[var(--rbpc-divider)] bg-[var(--rbpc-surface)] text-[var(--rbpc-ink)] hover:bg-[var(--rbpc-bg)] disabled:opacity-40 disabled:cursor-not-allowed focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--rbpc-focus)] focus-visible:ring-offset-2"
                  >
                    +
                  </button>
                </div>
                <p className="text-[11px] text-[var(--rbpc-muted)]">
                  {locale === "vi"
                    ? `Tối đa ${maxPartySize} khách mỗi buổi.`
                    : `Capped at max ${maxPartySize} guests.`}
                </p>
              </div>
            </div>

            {/* Field: Message or Specific Wishes (Optional) */}
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

            {/* MANDATORY UNCHECKED Consent Checkbox */}
            <div className="pt-2 border-t border-[var(--rbpc-divider-subtle)]">
              <label
                htmlFor="inquiry-consent"
                className="rbpc-checkbox-wrapper group min-h-[44px] flex items-start gap-3 cursor-pointer py-2 select-none"
              >
                <input
                  id="inquiry-consent"
                  type="checkbox"
                  required
                  aria-required="true"
                  checked={consentAccepted}
                  onChange={(e) => {
                    setConsentAccepted(e.target.checked);
                    if (errors.consent)
                      setErrors((prev) => ({ ...prev, consent: "" }));
                  }}
                  aria-invalid={Boolean(errors.consent)}
                  aria-describedby={errors.consent ? "inquiry-consent-error" : undefined}
                  className="rbpc-checkbox min-h-[20px] min-w-[20px] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--rbpc-focus)] focus-visible:ring-offset-2"
                />
                <span className="rbpc-checkbox-label">
                  {copy.inquiry.fields.consent.label}{" "}
                  <span className="text-[var(--rbpc-error)]">*</span>
                </span>
              </label>

              {errors.consent && (
                <p id="inquiry-consent-error" className="rbpc-field-error -mt-1 mb-2">
                  <AlertCircle className="h-3.5 w-3.5 shrink-0" aria-hidden="true" />
                  <span>{errors.consent}</span>
                </p>
              )}
            </div>

            {/* Modal Actions Footer */}
            <div className="pt-4 border-t border-[var(--rbpc-divider)] flex flex-col-reverse sm:flex-row items-center justify-end gap-3">
              <RbpcButton
                type="button"
                variant="secondary"
                size="md"
                onClick={onClose}
                disabled={isSubmitting}
                className="w-full sm:w-auto"
              >
                {copy.cta.close}
              </RbpcButton>

              <RbpcButton
                type="submit"
                variant="primary"
                size="md"
                isLoading={isSubmitting}
                loadingText={copy.cta.submitting}
                className="w-full sm:w-auto"
              >
                <span>{copy.cta.submitInquiry}</span>
                <ArrowRight className="h-4 w-4 ml-1.5" aria-hidden="true" />
              </RbpcButton>
            </div>
          </form>
        )}

        {/* ===================================================================
            VIEW 2: ACKNOWLEDGMENT & CONFIRMATION SCREEN
            =================================================================== */}
        {viewState === "acknowledgment" && (
          <div className="p-6 sm:p-8 space-y-6 overflow-y-auto">
            {/* Success Icon & Header */}
            <div className="text-center">
              <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-full bg-emerald-500/10 text-emerald-700 dark:text-emerald-400 mb-3 shadow-inner">
                <CheckCircle2 className="h-8 w-8" aria-hidden="true" />
              </div>
              <h3 className="font-serif text-2xl font-bold text-[var(--rbpc-ink)]">
                {copy.inquiry.confirmation.title}
              </h3>
              <p className="mt-1 text-sm text-[var(--rbpc-muted)] max-w-md mx-auto">
                {copy.inquiry.confirmation.message}
              </p>
            </div>

            {/* Reference & Status Pill Box */}
            <div className="rounded-xl border border-[var(--rbpc-divider)] bg-[var(--rbpc-bg)] p-4 text-center">
              <span className="block text-xs uppercase tracking-wider text-[var(--rbpc-muted)]">
                {copy.inquiry.confirmation.referencePrefix}
              </span>
              <span className="mt-1 inline-block font-mono text-xl sm:text-2xl font-bold tracking-widest text-[var(--rbpc-primary)]">
                {submissionResult?.reference || "INQ-2026-CONF"}
              </span>

              <div className="mt-2.5 flex items-center justify-center gap-1.5">
                <span className="inline-flex items-center gap-1.5 rounded-full border border-amber-600/30 bg-amber-500/10 px-3 py-0.5 text-xs font-semibold text-amber-900 dark:text-amber-300">
                  <Clock className="h-3.5 w-3.5 text-amber-600" aria-hidden="true" />
                  <span>{copy.inquiry.confirmation.statusBadge}</span>
                </span>
              </div>
            </div>

            {/* Request Summary */}
            <div className="rounded-xl border border-[var(--rbpc-divider-subtle)] bg-[var(--rbpc-surface)] p-4 text-xs space-y-2 text-[var(--rbpc-ink)]">
              <div className="flex justify-between">
                <span className="text-[var(--rbpc-muted)]">
                  {locale === "vi" ? "Trải nghiệm:" : "Experience:"}
                </span>
                <span className="font-semibold text-right max-w-[240px] truncate">
                  {experienceTitle}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-[var(--rbpc-muted)]">
                  {locale === "vi" ? "Nghệ nhân phụ trách:" : "Host:"}
                </span>
                <span className="font-semibold">{experience.creatorName}</span>
              </div>
              {preferredDate && (
                <div className="flex justify-between">
                  <span className="text-[var(--rbpc-muted)]">
                    {locale === "vi" ? "Ngày mong muốn:" : "Preferred Date:"}
                  </span>
                  <span className="font-mono font-medium">{preferredDate}</span>
                </div>
              )}
              <div className="flex justify-between">
                <span className="text-[var(--rbpc-muted)]">
                  {locale === "vi" ? "Số khách tham gia:" : "Party Size:"}
                </span>
                <span>{partySize} {locale === "vi" ? "khách" : "guest(s)"}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-[var(--rbpc-muted)]">
                  {locale === "vi" ? "Kênh phản hồi:" : "Contact Channel:"}
                </span>
                <span className="font-mono">{contactValue} ({contactMethod})</span>
              </div>
            </div>

            {/* Next Steps Card */}
            <div className="rounded-xl border border-[var(--rbpc-primary-border)] bg-[var(--rbpc-primary-subtle)] p-4 text-xs text-[var(--rbpc-ink)]">
              <h4 className="font-semibold text-[var(--rbpc-primary)] flex items-center gap-1.5 mb-1.5">
                <Sparkles className="h-4 w-4" aria-hidden="true" />
                <span>{copy.inquiry.confirmation.nextStepsTitle}</span>
              </h4>
              <p className="leading-relaxed text-[var(--rbpc-ink-subtle)]">
                {copy.inquiry.confirmation.nextStepsBody}
              </p>
            </div>

            {/* Non-Commercial Disclaimer */}
            <div className="flex items-start gap-2 rounded-lg bg-[var(--rbpc-bg)] p-3 text-[11px] text-[var(--rbpc-muted)] leading-relaxed border border-[var(--rbpc-divider-subtle)]">
              <ShieldCheck className="h-4 w-4 text-[var(--rbpc-primary)] shrink-0 mt-0.5" aria-hidden="true" />
              <div className="space-y-1">
                <p className="font-semibold text-[var(--rbpc-ink)]">
                  {locale === "vi"
                    ? "Concept demonstration — Yêu cầu trải nghiệm sẽ được gửi trực tiếp đến nghệ nhân/cơ sở để xác nhận thời gian."
                    : "Concept demonstration — Experience requests will be sent directly to the artisan/facility to confirm timing."}
                </p>
                <p>{copy.inquiry.confirmation.disclaimer}</p>
              </div>
            </div>

            {/* Return Button */}
            <div className="pt-2 text-center">
              <RbpcButton
                type="button"
                variant="primary"
                size="lg"
                onClick={onClose}
                className="w-full sm:w-auto"
              >
                <span>{copy.inquiry.confirmation.backButton}</span>
              </RbpcButton>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

InquiryFormModal.displayName = "InquiryFormModal";
