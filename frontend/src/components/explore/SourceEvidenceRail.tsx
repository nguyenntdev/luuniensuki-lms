"use client";

import * as React from "react";
import {
  BookOpen,
  ShieldCheck,
  Clock,
  AlertCircle,
  XCircle,
  Copy,
  Check,
  ExternalLink,
  Filter,
  FileText,
  ChevronDown,
  Layers,
  Sparkles,
} from "lucide-react";
import { cn } from "@/lib/utils";
import type { HeritageSourceEvidence, EvidenceStatus, HeritageReuseRights } from "@/types/heritage";
import type { RbpcLocale } from "@/lib/rbpc/copy";
import { getRbpcCopy } from "@/lib/rbpc/copy";

export type SourceRailLayout = "sidebar" | "bottom" | "auto";
export type EvidenceFilterStatus = "all" | EvidenceStatus;

export interface SourceEvidenceRailProps extends React.HTMLAttributes<HTMLDivElement> {
  /** Primary bibliographic source items */
  sources: HeritageSourceEvidence[];
  /** Primary name of the heritage monument/place in Vietnamese */
  placeName?: string;
  /** English translated name */
  placeNameEn?: string;
  /** Display layout: "sidebar" (sticky vertical), "bottom" (horizontal / multi-col), or "auto" */
  layout?: SourceRailLayout;
  /** Active UI locale ("vi" | "en", defaults to "vi") */
  locale?: RbpcLocale;
  /** Additional CSS classes */
  className?: string;
  /** Callback fired when user selects a source */
  onSourceSelect?: (source: HeritageSourceEvidence) => void;
  /** Callback fired to open full citation drawer */
  onOpenCitationDrawer?: () => void;
}

/**
 * Status visual mapping for evidence verification
 */
export const EVIDENCE_STATUS_CONFIG: Record<
  EvidenceStatus,
  {
    labelVi: string;
    labelEn: string;
    icon: React.ComponentType<{ className?: string }>;
    badgeClass: string;
    bgSubtle: string;
  }
> = {
  verified: {
    labelVi: "Đã đối chiếu thư tịch",
    labelEn: "Verified by Source",
    icon: ShieldCheck,
    badgeClass:
      "bg-emerald-50 text-emerald-800 border-emerald-300 dark:bg-emerald-950/40 dark:text-emerald-300",
    bgSubtle: "bg-emerald-50/50 dark:bg-emerald-950/20",
  },
  needs_review: {
    labelVi: "Chờ kiểm chứng",
    labelEn: "Needs Review",
    icon: Clock,
    badgeClass:
      "bg-amber-50 text-amber-800 border-amber-300 dark:bg-amber-950/40 dark:text-amber-300",
    bgSubtle: "bg-amber-50/50 dark:bg-amber-950/20",
  },
  disputed: {
    labelVi: "Còn tranh luận học thuật",
    labelEn: "Scholarly Disputed",
    icon: AlertCircle,
    badgeClass:
      "bg-purple-50 text-purple-800 border-purple-300 dark:bg-purple-950/40 dark:text-purple-300",
    bgSubtle: "bg-purple-50/50 dark:bg-purple-950/20",
  },
  rejected: {
    labelVi: "Bác bỏ do sai lệch",
    labelEn: "Rejected Claim",
    icon: XCircle,
    badgeClass:
      "bg-rose-50 text-rose-800 border-rose-300 dark:bg-rose-950/40 dark:text-rose-300",
    bgSubtle: "bg-rose-50/50 dark:bg-rose-950/20",
  },
};

/**
 * Reuse rights readable badge mapping
 */
export const REUSE_RIGHTS_LABELS: Record<
  HeritageReuseRights,
  { vi: string; en: string }
> = {
  public_domain: {
    vi: "Miền công cộng (Tư liệu lịch sử)",
    en: "Public Domain",
  },
  cc_by: {
    vi: "CC BY (Ghi nhận tác giả)",
    en: "CC BY Attribution",
  },
  cc_by_sa: {
    vi: "CC BY-SA",
    en: "CC BY-SA",
  },
  cc_by_nc_sa: {
    vi: "CC BY-NC-SA (Phi thương mại)",
    en: "CC BY-NC-SA",
  },
  educational_fair_use: {
    vi: "Trích dẫn nghiên cứu giáo dục",
    en: "Educational Fair Use",
  },
  restricted: {
    vi: "Bản quyền lưu trữ giới hạn",
    en: "Restricted Archive",
  },
  unknown: {
    vi: "Đang rà soát bản quyền",
    en: "Rights Under Review",
  },
};

/**
 * Format a bibliographic record into an APA/Chicago-style citation string
 */
export function formatBibliographicCitation(source: HeritageSourceEvidence): string {
  const parts: string[] = [];

  if (source.source_author) {
    parts.push(`${source.source_author}.`);
  }

  const titleWithYear = source.publication_year
    ? `${source.source_title} (${source.publication_year}).`
    : `${source.source_title}.`;
  parts.push(titleWithYear);

  if (source.publisher) {
    parts.push(`${source.publisher}.`);
  }

  if (source.cited_section) {
    parts.push(source.cited_section);
  }

  if (source.cited_page) {
    const pageText =
      source.cited_page.startsWith("Tr.") ||
      source.cited_page.startsWith("p.") ||
      source.cited_page.startsWith("Quyển")
        ? source.cited_page
        : `Tr. ${source.cited_page}`;
    parts.push(`${pageText}.`);
  }

  if (source.source_url) {
    parts.push(`<${source.source_url}>`);
  }

  return parts.join(" ");
}

/**
 * SourceEvidenceRail Component
 *
 * Displays primary bibliographic sources, cited pages/locators, and epistemic
 * verification badges for a heritage place. Can be positioned as a sticky sidebar
 * or full-width bottom rail.
 */
export function SourceEvidenceRail({
  sources = [],
  placeName = "Địa danh di sản",
  placeNameEn,
  layout = "auto",
  locale = "vi",
  className,
  onSourceSelect,
  onOpenCitationDrawer,
  ...restProps
}: SourceEvidenceRailProps) {
  const isEn = locale === "en";
  const displayName = isEn && placeNameEn ? placeNameEn : placeName;

  const [activeFilter, setActiveFilter] = React.useState<EvidenceFilterStatus>("all");
  const [copiedId, setCopiedId] = React.useState<string | null>(null);

  // Filter sources
  const filteredSources = React.useMemo(() => {
    if (activeFilter === "all") return sources;
    return sources.filter((s) => s.evidence_status === activeFilter);
  }, [sources, activeFilter]);

  // Counts by status
  const verifiedCount = React.useMemo(
    () => sources.filter((s) => s.evidence_status === "verified").length,
    [sources]
  );

  const needsReviewCount = React.useMemo(
    () => sources.filter((s) => s.evidence_status === "needs_review").length,
    [sources]
  );

  const disputedCount = React.useMemo(
    () => sources.filter((s) => s.evidence_status === "disputed").length,
    [sources]
  );

  // Copy citation to clipboard
  const handleCopyCitation = (source: HeritageSourceEvidence) => {
    const citation = formatBibliographicCitation(source);
    if (typeof navigator !== "undefined" && navigator.clipboard) {
      navigator.clipboard.writeText(citation).catch(() => {});
    }
    setCopiedId(source.id);
    setTimeout(() => {
      setCopiedId(null);
    }, 2000);
  };

  const isSidebar = layout === "sidebar";
  const isBottom = layout === "bottom";

  return (
    <aside
      aria-label={isEn ? "Primary Bibliographic Sources" : "Thư tịch & Nguồn đối chiếu"}
      className={cn(
        "rounded-2xl border border-[var(--rbpc-divider)] bg-[var(--rbpc-surface)] p-4 sm:p-5 shadow-xs transition-all",
        isSidebar ? "sticky top-24" : "",
        className
      )}
      {...restProps}
    >
      {/* Header section */}
      <div className="border-b border-[var(--rbpc-divider-subtle)] pb-4">
        <div className="flex items-center justify-between gap-2">
          <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-[var(--rbpc-primary)]">
            <BookOpen className="h-4 w-4" aria-hidden="true" />
            <span>{isEn ? "Bibliographic Evidence" : "Khảo cứu thư tịch"}</span>
          </div>

          {/* Ratio badge */}
          <span className="inline-flex items-center gap-1 rounded-full bg-[var(--rbpc-primary-subtle)] px-2.5 py-0.5 text-xs font-semibold text-[var(--rbpc-primary)]">
            <ShieldCheck className="h-3.5 w-3.5" aria-hidden="true" />
            <span>
              {verifiedCount}/{sources.length} {isEn ? "verified" : "đã đối chiếu"}
            </span>
          </span>
        </div>

        <h3 className="mt-1 font-serif text-lg font-bold text-[var(--rbpc-ink)]">
          {isEn ? `Primary Sources — ${displayName}` : `Nguồn tư liệu — ${displayName}`}
        </h3>

        <p className="mt-1 text-xs text-[var(--rbpc-muted)] leading-relaxed">
          {isEn
            ? "Authoritative imperial chronicles, UNESCO registration dossiers, and field documentation anchoring claims."
            : "Chính sử triều Nguyễn, hồ sơ di sản UNESCO và tài liệu khảo sát thực địa chứng thực cho địa điểm."}
        </p>

        {/* Filter Chips */}
        <div className="mt-3 flex flex-wrap gap-1.5" role="toolbar" aria-label="Lọc nguồn tư liệu">
          <button
            type="button"
            onClick={() => setActiveFilter("all")}
            className={cn(
              "rounded-lg px-3 py-1.5 text-xs font-medium border transition-colors min-h-[44px] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--rbpc-focus,#1E675A)] focus-visible:ring-offset-2",
              activeFilter === "all"
                ? "bg-[var(--rbpc-primary)] text-white border-[var(--rbpc-primary)] font-semibold"
                : "bg-[var(--rbpc-surface)] text-[var(--rbpc-muted)] border-[var(--rbpc-divider)] hover:text-[var(--rbpc-ink)]"
            )}
          >
            {isEn ? "All" : "Tất cả"} ({sources.length})
          </button>

          <button
            type="button"
            onClick={() => setActiveFilter("verified")}
            className={cn(
              "rounded-lg px-3 py-1.5 text-xs font-medium border transition-colors min-h-[44px] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--rbpc-focus,#1E675A)] focus-visible:ring-offset-2",
              activeFilter === "verified"
                ? "bg-emerald-700 text-white border-emerald-700 font-semibold"
                : "bg-emerald-50/60 text-emerald-800 border-emerald-200 dark:bg-emerald-950/30 dark:text-emerald-300"
            )}
          >
            {isEn ? "Verified" : "Đã đối chiếu"} ({verifiedCount})
          </button>

          {needsReviewCount > 0 && (
            <button
              type="button"
              onClick={() => setActiveFilter("needs_review")}
              className={cn(
                "rounded-lg px-3 py-1.5 text-xs font-medium border transition-colors min-h-[44px] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--rbpc-focus,#1E675A)] focus-visible:ring-offset-2",
                activeFilter === "needs_review"
                  ? "bg-amber-700 text-white border-amber-700 font-semibold"
                  : "bg-amber-50/60 text-amber-800 border-amber-200 dark:bg-amber-950/30 dark:text-amber-300"
              )}
            >
              {isEn ? "Needs Review" : "Chờ kiểm chứng"} ({needsReviewCount})
            </button>
          )}

          {disputedCount > 0 && (
            <button
              type="button"
              onClick={() => setActiveFilter("disputed")}
              className={cn(
                "rounded-lg px-3 py-1.5 text-xs font-medium border transition-colors min-h-[44px] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--rbpc-focus,#1E675A)] focus-visible:ring-offset-2",
                activeFilter === "disputed"
                  ? "bg-purple-700 text-white border-purple-700 font-semibold"
                  : "bg-purple-50/60 text-purple-800 border-purple-200 dark:bg-purple-950/30 dark:text-purple-300"
              )}
            >
              {isEn ? "Disputed" : "Tranh luận"} ({disputedCount})
            </button>
          )}
        </div>
      </div>

      {/* Sources List */}
      <div
        className={cn(
          "mt-4 space-y-3",
          isBottom ? "grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3 space-y-0" : ""
        )}
      >
        {filteredSources.length > 0 ? (
          filteredSources.map((source) => {
            const statusConfig =
              EVIDENCE_STATUS_CONFIG[source.evidence_status] || EVIDENCE_STATUS_CONFIG.needs_review;
            const StatusIcon = statusConfig.icon;
            const isCopied = copiedId === source.id;

            return (
              <div
                key={source.id}
                onClick={() => onSourceSelect?.(source)}
                className="group relative flex flex-col justify-between rounded-xl border border-[var(--rbpc-divider)] bg-[var(--rbpc-surface-elevated)] p-3.5 shadow-2xs hover:border-[var(--rbpc-primary)] transition-all"
              >
                <div>
                  {/* Status & Cited Locator Bar */}
                  <div className="flex flex-wrap items-center justify-between gap-1.5 pb-2">
                    <span
                      className={cn(
                        "inline-flex items-center gap-1 rounded-md border px-2 py-0.5 text-[10px] font-semibold",
                        statusConfig.badgeClass
                      )}
                    >
                      <StatusIcon className="h-3 w-3" />
                      <span>{isEn ? statusConfig.labelEn : statusConfig.labelVi}</span>
                    </span>

                    {/* Locator Badge (Page / Section) */}
                    {(source.cited_page || source.cited_section) && (
                      <span className="inline-flex items-center rounded-md bg-[var(--rbpc-surface-muted)] px-2 py-0.5 text-[11px] font-mono font-medium text-[var(--rbpc-ink)] border border-[var(--rbpc-divider)]">
                        {source.cited_page
                          ? source.cited_page.startsWith("Tr.") || source.cited_page.startsWith("p.")
                            ? source.cited_page
                            : `Tr. ${source.cited_page}`
                          : source.cited_section}
                      </span>
                    )}
                  </div>

                  {/* Bibliographic Title & Author */}
                  <h4 className="font-serif text-sm font-bold text-[var(--rbpc-ink)] leading-snug">
                    {source.source_title}
                  </h4>

                  <div className="mt-1 text-xs text-[var(--rbpc-muted)]">
                    {source.source_author ? (
                      <span className="font-medium text-[var(--rbpc-ink-subtle)]">
                        {source.source_author}
                      </span>
                    ) : (
                      <span>Hồ sơ lưu trữ chính thức</span>
                    )}
                    {source.publication_year && <span> ({source.publication_year})</span>}
                    {source.publisher && <span> • {source.publisher}</span>}
                  </div>

                  {/* Historical Statement / Claim anchored */}
                  {source.statement && (
                    <div className="mt-2.5 rounded-lg bg-[var(--rbpc-surface-muted)] p-2.5 text-xs text-[var(--rbpc-ink)] border-l-2 border-[var(--rbpc-primary)]">
                      <p className="line-clamp-3 italic leading-relaxed">
                        “{source.statement}”
                      </p>
                    </div>
                  )}

                  {/* Scholarly Interpretation Note */}
                  {source.interpretation_note && (
                    <p className="mt-2 text-[11px] text-[var(--rbpc-muted)] line-clamp-2">
                      <span className="font-semibold text-[var(--rbpc-ink)]">
                        {isEn ? "Note: " : "Ghi chú: "}
                      </span>
                      {source.interpretation_note}
                    </p>
                  )}
                </div>

                {/* Footer Actions & Rights */}
                <div className="mt-3 flex items-center justify-between border-t border-[var(--rbpc-divider-subtle)] pt-2.5 text-[11px]">
                  {/* Rights indicator */}
                  <span className="text-[var(--rbpc-muted)] truncate max-w-[140px]">
                    {REUSE_RIGHTS_LABELS[source.reuse_rights]?.[locale] ||
                      REUSE_RIGHTS_LABELS[source.reuse_rights]?.vi ||
                      "Bản quyền bảo lưu"}
                  </span>

                  {/* Actions */}
                  <div className="flex items-center gap-1">
                    {/* Copy Citation button */}
                    <button
                      type="button"
                      onClick={(e) => {
                        e.stopPropagation();
                        handleCopyCitation(source);
                      }}
                      aria-label={isEn ? "Copy bibliographic citation" : "Sao chép trích dẫn thư tịch"}
                      className={cn(
                        "inline-flex items-center gap-1 rounded-md px-2.5 py-1.5 font-medium transition-colors min-h-[44px] min-w-[44px] justify-center focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--rbpc-focus,#1E675A)] focus-visible:ring-offset-2",
                        isCopied
                          ? "bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300"
                          : "text-[var(--rbpc-muted)] hover:bg-[var(--rbpc-surface-muted)] hover:text-[var(--rbpc-ink)]"
                      )}
                    >
                      {isCopied ? (
                        <>
                          <Check className="h-3.5 w-3.5" aria-hidden="true" />
                          <span>{isEn ? "Copied" : "Đã chép"}</span>
                        </>
                      ) : (
                        <>
                          <Copy className="h-3.5 w-3.5" aria-hidden="true" />
                          <span>{isEn ? "Copy" : "Trích dẫn"}</span>
                        </>
                      )}
                    </button>

                    {/* Source URL link */}
                    {source.source_url && (
                      <a
                        href={source.source_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        onClick={(e) => e.stopPropagation()}
                        aria-label={isEn ? "Visit source repository" : "Đến trang tư liệu gốc"}
                        className="rounded-md p-2 text-[var(--rbpc-muted)] hover:bg-[var(--rbpc-surface-muted)] hover:text-[var(--rbpc-primary)] min-h-[44px] min-w-[44px] flex items-center justify-center focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--rbpc-focus,#1E675A)] focus-visible:ring-offset-2"
                      >
                        <ExternalLink className="h-4 w-4" aria-hidden="true" />
                      </a>
                    )}
                  </div>
                </div>
              </div>
            );
          })
        ) : (
          /* Empty state */
          <div className="flex flex-col items-center justify-center rounded-xl border border-dashed border-[var(--rbpc-divider)] bg-[var(--rbpc-surface-muted)]/40 p-8 text-center col-span-full">
            <BookOpen className="h-8 w-8 text-[var(--rbpc-muted)]/50 mb-2" aria-hidden="true" />
            <p className="text-xs font-semibold text-[var(--rbpc-ink)]">
              {isEn ? "No sources match the filter" : "Không có thư tịch phù hợp bộ lọc"}
            </p>
            <p className="mt-1 text-[11px] text-[var(--rbpc-muted)]">
              {isEn
                ? "Switch back to 'All' to browse the complete bibliographic dossier."
                : "Chuyển về 'Tất cả' để xem toàn bộ thư mục tư liệu."}
            </p>
            <button
              type="button"
              onClick={() => setActiveFilter("all")}
              className="mt-3 inline-flex min-h-[44px] items-center text-xs font-semibold text-[var(--rbpc-primary)] hover:underline focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--rbpc-focus,#1E675A)] focus-visible:ring-offset-2 rounded-sm"
            >
              {isEn ? "Show all sources" : "Hiện tất cả nguồn"}
            </button>
          </div>
        )}
      </div>

      {/* Full citation drawer trigger if callback passed */}
      {onOpenCitationDrawer && (
        <div className="mt-4 pt-3 border-t border-[var(--rbpc-divider-subtle)] text-center">
          <button
            type="button"
            onClick={onOpenCitationDrawer}
            className="inline-flex items-center gap-1.5 rounded-lg border border-[var(--rbpc-divider)] bg-[var(--rbpc-surface)] px-4 py-2 text-xs font-semibold text-[var(--rbpc-ink)] hover:bg-[var(--rbpc-surface-muted)] transition-colors min-h-[44px] w-full justify-center focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--rbpc-focus,#1E675A)] focus-visible:ring-offset-2"
          >
            <Layers className="h-3.5 w-3.5 text-[var(--rbpc-primary)]" aria-hidden="true" />
            <span>{isEn ? "Open Complete Citation Drawer" : "Mở toàn bộ mục lục trích dẫn"}</span>
          </button>
        </div>
      )}
    </aside>
  );
}

SourceEvidenceRail.displayName = "SourceEvidenceRail";

export default SourceEvidenceRail;
