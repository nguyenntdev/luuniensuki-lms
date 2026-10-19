"use client";

import * as React from "react";
import { X, ExternalLink, Copy, Check, BookOpen, ShieldCheck } from "lucide-react";
import { cn } from "@/lib/utils";
import { getRbpcCopy, type RbpcLocale } from "@/lib/rbpc/copy";
import { RbpcButton } from "./RbpcButton";
import { EpistemicBadge } from "./EpistemicBadge";

export interface CitationSourceItem {
  id: string;
  title?: string;
  source_title?: string;
  author?: string | null;
  source_author?: string | null;
  publisher?: string | null;
  year?: number | string | null;
  publication_year?: number | string | null;
  locator?: string | null;
  cited_page?: string | null;
  cited_section?: string | null;
  url?: string | null;
  source_url?: string | null;
  statement?: string | null;
  interpretation_note?: string | null;
  archiveRef?: string | null;
  official_reference_id?: string | null;
  evidence_status?: string | null;
  reuse_rights?: string | null;
}

export interface CitationDrawerProps {
  /** Controls open/close state of the drawer */
  isOpen: boolean;
  /** Callback fired when user closes the drawer via Escape, overlay, or close button */
  onClose: () => void;
  /** List of primary bibliographic source records */
  sources: CitationSourceItem[];
  /** Optional title of the cited historical entity, story, or motif */
  entityName?: string;
  /** Custom drawer title overriding the default */
  title?: string;
  /** Interface language locale ("vi" | "en", defaults to "vi") */
  locale?: RbpcLocale;
  /** Optional custom class name applied to drawer panel */
  className?: string;
}

/**
 * Format a bibliographic item into a human-readable citation string.
 */
function formatBibliographicCitation(item: CitationSourceItem): string {
  const author = item.source_author || item.author;
  const title = item.source_title || item.title || "Tư liệu không tiêu đề";
  const year = item.publication_year || item.year;
  const publisher = item.publisher;
  const locator = item.cited_page || item.locator || item.cited_section;

  const parts: string[] = [];
  if (author) parts.push(`${author}.`);
  parts.push(year ? `${title} (${year}).` : `${title}.`);
  if (publisher) parts.push(`${publisher}.`);
  if (locator) parts.push(locator.startsWith("Tr.") || locator.startsWith("p.") ? locator : `Tr. ${locator}.`);
  if (item.source_url || item.url) parts.push(`<${item.source_url || item.url}>`);

  return parts.join(" ");
}

/**
 * CitationDrawer — Accessible Drawer for Archival Sources & Bibliographic Evidence
 *
 * Implements Master Spec §4.3 & §4.5:
 * - Slides over reading viewport (max 480px width)
 * - Zero heavy backdrop-blur (solid 45% dark-tint overlay)
 * - Accessible keyboard focus trap, Escape dismissal, and focus restoration
 * - Copy-to-clipboard action with canonical bilingual microcopy feedback
 * - Displays primary author, publication date, archive locators, and claim notes
 */
export const CitationDrawer: React.FC<CitationDrawerProps> = ({
  isOpen,
  onClose,
  sources = [],
  entityName,
  title,
  locale = "vi",
  className,
}) => {
  const dict = getRbpcCopy(locale);
  const [copiedId, setCopiedId] = React.useState<string | null>(null);
  const drawerRef = React.useRef<HTMLDivElement>(null);
  const closeButtonRef = React.useRef<HTMLButtonElement>(null);
  const previouslyFocusedElementRef = React.useRef<HTMLElement | null>(null);

  // Store previously focused element and manage focus trapping
  React.useEffect(() => {
    if (isOpen) {
      previouslyFocusedElementRef.current = document.activeElement as HTMLElement;

      // Lock body scroll
      const originalOverflow = document.body.style.overflow;
      document.body.style.overflow = "hidden";

      // Focus close button on open
      const timer = setTimeout(() => {
        closeButtonRef.current?.focus();
      }, 50);

      return () => {
        clearTimeout(timer);
        document.body.style.overflow = originalOverflow;
        previouslyFocusedElementRef.current?.focus();
      };
    }
  }, [isOpen]);

  // Handle Escape key and Tab focus trap
  React.useEffect(() => {
    if (!isOpen) return;

    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        event.preventDefault();
        onClose();
        return;
      }

      if (event.key === "Tab" && drawerRef.current) {
        const focusableElements = drawerRef.current.querySelectorAll<HTMLElement>(
          'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
        );
        if (focusableElements.length === 0) return;

        const firstElement = focusableElements[0];
        const lastElement = focusableElements[focusableElements.length - 1];

        if (event.shiftKey && document.activeElement === firstElement) {
          event.preventDefault();
          lastElement.focus();
        } else if (!event.shiftKey && document.activeElement === lastElement) {
          event.preventDefault();
          firstElement.focus();
        }
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isOpen, onClose]);

  const handleCopy = async (item: CitationSourceItem) => {
    const formatted = formatBibliographicCitation(item);
    try {
      if (typeof navigator !== "undefined" && navigator.clipboard) {
        await navigator.clipboard.writeText(formatted);
        setCopiedId(item.id);
        setTimeout(() => setCopiedId(null), 2500);
      }
    } catch {
      // Fallback if clipboard API restricted
      setCopiedId(item.id);
      setTimeout(() => setCopiedId(null), 2500);
    }
  };

  if (!isOpen) return null;

  const headerTitle =
    title ||
    (locale === "vi"
      ? "Nguồn tư liệu & Đối chiếu"
      : "Sources & Bibliographic Evidence");

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="rbpc-citation-drawer-title"
      aria-describedby="rbpc-citation-drawer-desc"
      className="relative z-[900]"
    >
      {/* Dim Overlay — NO heavy blur, uses solid tinted alpha */}
      <div
        className="rbpc-drawer-overlay is-open fixed inset-0 bg-[#242C2B]/45 transition-opacity"
        onClick={onClose}
        aria-hidden="true"
      />

      {/* Drawer Panel Container */}
      <div
        ref={drawerRef}
        className={cn(
          "rbpc-drawer-panel is-open fixed top-0 right-0 bottom-0 w-full max-w-[var(--rbpc-drawer-max)]",
          "bg-[var(--rbpc-surface)] border-l border-[var(--rbpc-divider)] shadow-[var(--rbpc-shadow-lg)]",
          "flex flex-col z-[910] text-[var(--rbpc-ink)]",
          className
        )}
      >
        {/* Header */}
        <div className="rbpc-drawer-header flex items-center justify-between p-5 border-b border-[var(--rbpc-divider)] bg-[var(--rbpc-surface)]">
          <div className="flex items-center gap-2.5">
            <BookOpen className="h-5 w-5 text-[var(--rbpc-primary)] shrink-0" aria-hidden="true" />
            <div>
              <h2
                id="rbpc-citation-drawer-title"
                className="font-serif text-lg font-semibold text-[var(--rbpc-ink)] leading-snug"
              >
                {headerTitle}
              </h2>
              {entityName && (
                <p className="text-xs text-[var(--rbpc-muted)] line-clamp-1">
                  {entityName}
                </p>
              )}
            </div>
          </div>

          <button
            ref={closeButtonRef}
            type="button"
            onClick={onClose}
            aria-label={dict.cta.close}
            className={cn(
              "rbpc-touch-target min-h-[44px] min-w-[44px] inline-flex items-center justify-center",
              "rounded-[var(--rbpc-radius-md)] text-[var(--rbpc-muted)] hover:text-[var(--rbpc-ink)]",
              "hover:bg-[var(--rbpc-primary-subtle)] transition-colors",
              "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--rbpc-focus)] focus-visible:ring-offset-2"
            )}
          >
            <X className="h-5 w-5" aria-hidden="true" />
          </button>
        </div>

        {/* Drawer Body */}
        <div
          id="rbpc-citation-drawer-desc"
          className="rbpc-drawer-body flex-1 p-5 sm:p-6 overflow-y-auto space-y-4"
        >
          {/* Institutional Citation Policy Banner */}
          <div className="p-3.5 rounded-[var(--rbpc-radius-md)] bg-[var(--rbpc-bg)] border border-[var(--rbpc-divider)] text-xs text-[var(--rbpc-ink-subtle)] leading-relaxed flex items-start gap-2.5">
            <ShieldCheck className="h-4 w-4 text-[var(--rbpc-primary)] shrink-0 mt-0.5" aria-hidden="true" />
            <div>
              <p className="font-medium text-[var(--rbpc-ink)] mb-1">
                {locale === "vi" ? "Chính sách đối chiếu tư liệu" : "Archival Verification Policy"}
              </p>
              <p>{dict.brand.citationPolicy}</p>
            </div>
          </div>

          {/* Sources List */}
          {sources.length === 0 ? (
            <div className="py-12 text-center text-[var(--rbpc-muted)] text-sm space-y-2">
              <BookOpen className="h-8 w-8 mx-auto opacity-40" aria-hidden="true" />
              <p>{dict.ai.noSourcesFound}</p>
            </div>
          ) : (
            <div className="space-y-3">
              <p className="text-xs font-medium uppercase tracking-wider text-[var(--rbpc-muted)]">
                {locale === "vi"
                  ? `Danh mục nguồn tham khảo (${sources.length})`
                  : `Referenced Citations (${sources.length})`}
              </p>

              {sources.map((item, index) => {
                const titleText = item.source_title || item.title || "Tư liệu không tiêu đề";
                const authorText = item.source_author || item.author;
                const yearText = item.publication_year || item.year;
                const locatorText = item.cited_page || item.locator || item.cited_section;
                const externalUrl = item.source_url || item.url;
                const isCopied = copiedId === item.id;

                return (
                  <article
                    key={item.id || index}
                    className="rbpc-citation-item p-4 rounded-[var(--rbpc-radius-md)] bg-[var(--rbpc-bg)] border border-[var(--rbpc-divider)] transition-shadow hover:shadow-[var(--rbpc-shadow-sm)]"
                  >
                    <div className="flex items-start justify-between gap-2 mb-1.5">
                      <h3 className="font-serif font-semibold text-sm text-[var(--rbpc-ink)] leading-snug">
                        {titleText}
                      </h3>
                      {item.evidence_status && (
                        <EpistemicBadge
                          status={item.evidence_status}
                          locale={locale}
                          size="sm"
                          showDot={false}
                        />
                      )}
                    </div>

                    {/* Metadata line */}
                    <div className="text-xs text-[var(--rbpc-muted)] leading-relaxed space-y-0.5">
                      {authorText && (
                        <p>
                          <span className="font-medium text-[var(--rbpc-ink-subtle)]">
                            {locale === "vi" ? "Tác giả / Khảo cứu:" : "Author / Scholar:"}
                          </span>{" "}
                          {authorText}
                        </p>
                      )}
                      {(item.publisher || yearText) && (
                        <p>
                          {item.publisher && <span>{item.publisher}</span>}
                          {item.publisher && yearText && <span> · </span>}
                          {yearText && <span>{yearText}</span>}
                        </p>
                      )}
                      {item.archiveRef && (
                        <p className="font-mono text-[11px] text-[var(--rbpc-muted)]">
                          {locale === "vi" ? "Mã lưu trữ:" : "Archive Ref:"} {item.archiveRef}
                        </p>
                      )}
                    </div>

                    {/* Cited statement or interpretation note */}
                    {item.statement && (
                      <blockquote className="mt-2.5 pl-3 border-l-2 border-[var(--rbpc-primary-border)] text-xs text-[var(--rbpc-ink)] italic leading-relaxed">
                        “{item.statement}”
                      </blockquote>
                    )}
                    {item.interpretation_note && (
                      <p className="mt-2 text-[11px] text-[var(--rbpc-muted)]">
                        <span className="font-medium text-[var(--rbpc-ink-subtle)]">
                          {locale === "vi" ? "Ghi chú khảo cứu:" : "Research note:"}
                        </span>{" "}
                        {item.interpretation_note}
                      </p>
                    )}

                    {/* Locator and Actions */}
                    <div className="mt-3 pt-2.5 border-t border-[var(--rbpc-divider-subtle)] flex flex-wrap items-center justify-between gap-2">
                      {locatorText ? (
                        <span className="rbpc-citation-locator font-mono text-[11px] text-[var(--rbpc-primary)] bg-[var(--rbpc-primary-subtle)] px-2 py-0.5 rounded">
                          {locatorText}
                        </span>
                      ) : <span />}

                      <div className="flex items-center gap-1.5 ml-auto">
                        {externalUrl && (
                          <a
                            href={externalUrl}
                            target="_blank"
                            rel="noopener noreferrer"
                            aria-label={`${locale === "vi" ? "Mở liên kết nguồn" : "Open external source"}: ${titleText}`}
                            className={cn(
                              "rbpc-touch-target min-h-[44px] min-w-[44px] inline-flex items-center justify-center",
                              "text-xs text-[var(--rbpc-primary)] hover:text-[var(--rbpc-primary-hover)]",
                              "rounded-[var(--rbpc-radius-sm)] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--rbpc-focus)]"
                            )}
                          >
                            <ExternalLink className="h-4 w-4" aria-hidden="true" />
                          </a>
                        )}

                        <button
                          type="button"
                          onClick={() => handleCopy(item)}
                          aria-label={isCopied ? dict.cta.copied : dict.cta.copyCitation}
                          className={cn(
                            "min-h-[44px] px-2.5 inline-flex items-center gap-1.5 text-xs font-medium",
                            "rounded-[var(--rbpc-radius-sm)] border border-[var(--rbpc-divider)] bg-[var(--rbpc-surface)] text-[var(--rbpc-ink)]",
                            "hover:border-[var(--rbpc-primary)] hover:text-[var(--rbpc-primary)] transition-colors",
                            "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--rbpc-focus)]"
                          )}
                        >
                          {isCopied ? (
                            <>
                              <Check className="h-3.5 w-3.5 text-[var(--rbpc-success)]" aria-hidden="true" />
                              <span className="text-[var(--rbpc-success)]">{dict.cta.copied}</span>
                            </>
                          ) : (
                            <>
                              <Copy className="h-3.5 w-3.5" aria-hidden="true" />
                              <span>{dict.cta.copyCitation}</span>
                            </>
                          )}
                        </button>
                      </div>
                    </div>
                  </article>
                );
              })}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="rbpc-drawer-footer p-4 border-t border-[var(--rbpc-divider)] bg-[var(--rbpc-bg)] flex items-center justify-between">
          <p className="text-xs text-[var(--rbpc-muted)]">
            {locale === "vi" ? "UNESCO Ref 678 · LƯU NIÊN" : "UNESCO Ref 678 · LƯU NIÊN"}
          </p>
          <RbpcButton
            variant="secondary"
            size="sm"
            onClick={onClose}
          >
            {dict.cta.close}
          </RbpcButton>
        </div>
      </div>
    </div>
  );
};

CitationDrawer.displayName = "CitationDrawer";
