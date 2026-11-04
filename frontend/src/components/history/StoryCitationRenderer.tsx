"use client";

import React, { useState } from "react";
import Link from "next/link";
import {
  ShieldCheck,
  ScrollText,
  HelpCircle,
  AlertTriangle,
  ExternalLink,
  BookOpen,
  Copy,
  Check,
  FileText,
  Layers,
} from "lucide-react";

import { cn } from "@/lib/utils";
import type {
  StoryCitation,
  EpistemicCertaintyBadgeInfo,
  StoryFootnoteRef,
} from "@/lib/history";
import { getStoryPassageEpistemic, parseStoryFootnotes } from "@/lib/history";
import { CitationDrawer, type CitationSourceItem } from "@/components/rbpc/CitationDrawer";

export interface StoryPassageEpistemicBadgeProps {
  certainty?: string | null;
  hasSource?: boolean;
  verificationStatus?: string | null;
  isDisputed?: boolean;
  className?: string;
}

export function StoryPassageEpistemicBadge({
  certainty,
  hasSource,
  verificationStatus,
  isDisputed,
  className,
}: StoryPassageEpistemicBadgeProps) {
  const info: EpistemicCertaintyBadgeInfo = getStoryPassageEpistemic(certainty, {
    hasSource,
    verificationStatus,
    isDisputed,
  });

  const toneClass =
    info.tone === "documented"
      ? "border-emerald-500/30 bg-emerald-500/10 text-emerald-800 dark:text-emerald-300"
      : info.tone === "traditional"
      ? "border-amber-500/30 bg-amber-500/10 text-amber-800 dark:text-amber-300"
      : "border-sky-500/30 bg-sky-500/10 text-sky-800 dark:text-sky-300";

  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-[11px] font-semibold tracking-wide uppercase transition-colors",
        toneClass,
        className
      )}
      title={info.description}
    >
      {info.tone === "documented" ? (
        <ShieldCheck className="h-3 w-3 shrink-0" aria-hidden="true" />
      ) : info.tone === "traditional" ? (
        <ScrollText className="h-3 w-3 shrink-0" aria-hidden="true" />
      ) : (
        <HelpCircle className="h-3 w-3 shrink-0" aria-hidden="true" />
      )}
      <span>{info.label}</span>
    </span>
  );
}

export interface EmptyEvidenceWarningProps {
  message?: string;
  className?: string;
}

export function EmptyEvidenceWarning({
  message = "Khẳng định chưa gắn nguồn thư tịch — chưa có bằng chứng xác thực đối chiếu.",
  className,
}: EmptyEvidenceWarningProps) {
  return (
    <div
      role="alert"
      className={cn(
        "flex items-start gap-2.5 rounded-lg border border-amber-500/40 bg-amber-50/70 p-3 text-xs text-amber-900 dark:bg-amber-950/30 dark:text-amber-200",
        className
      )}
    >
      <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-amber-600 dark:text-amber-400" aria-hidden="true" />
      <div>
        <span className="font-semibold uppercase tracking-wider text-[10px] text-amber-800 dark:text-amber-300">
          Chưa xác thực nguồn
        </span>
        <p className="mt-0.5 leading-relaxed">{message}</p>
      </div>
    </div>
  );
}

export interface ClaimFootnoteTagProps {
  index: number;
  citationId?: string;
  sourceTitle?: string;
  hasSource?: boolean;
  onOpenDrawer?: () => void;
  className?: string;
}

export function ClaimFootnoteTag({
  index,
  citationId,
  sourceTitle,
  hasSource = true,
  onOpenDrawer,
  className,
}: ClaimFootnoteTagProps) {
  const targetId = citationId ? `citation-${citationId}` : `footnote-${index}`;
  return (
    <a
      href={`#${targetId}`}
      onClick={(e) => {
        if (onOpenDrawer) {
          e.preventDefault();
          onOpenDrawer();
        }
      }}
      className={cn(
        "inline-flex items-center justify-center font-mono text-[11px] font-bold px-1.5 py-0.2 rounded transition-colors ml-1 align-super leading-none cursor-pointer",
        hasSource
          ? "bg-primary/10 text-primary hover:bg-primary/20"
          : "bg-amber-500/20 text-amber-800 dark:text-amber-300 hover:bg-amber-500/30",
        className
      )}
      title={
        hasSource
          ? `Nguồn [${index}]: ${sourceTitle || "Xem thư tịch đối chiếu"}`
          : `[${index}] Chưa gắn nguồn kiểm chứng`
      }
    >
      [{index}]
    </a>
  );
}

export interface StoryEvidenceFootnotesProps {
  citations: StoryCitation[];
  onOpenDrawer?: () => void;
  className?: string;
}

export function StoryEvidenceFootnotes({
  citations,
  onOpenDrawer,
  className,
}: StoryEvidenceFootnotesProps) {
  const [copiedId, setCopiedId] = useState<string | null>(null);

  if (!citations || citations.length === 0) {
    return (
      <section className={cn("mt-12 rounded-xl border border-dashed border-border/80 bg-card/40 p-6", className)}>
        <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
          <BookOpen className="h-4 w-4" />
          <span>Thư tịch & Khảo chứng</span>
        </div>
        <p className="mt-2 text-sm text-muted-foreground">
          Chưa có dẫn chứng thư tịch nào được gắn cho bài viết này.
        </p>
      </section>
    );
  }

  const handleCopy = (id: string, text: string) => {
    if (typeof navigator !== "undefined" && navigator.clipboard) {
      navigator.clipboard.writeText(text).catch(() => {});
      setCopiedId(id);
      setTimeout(() => setCopiedId(null), 2000);
    }
  };

  return (
    <section
      aria-label="Khảo chứng sử liệu và nguồn dẫn chứng"
      className={cn(
        "mt-12 rounded-2xl border border-border/80 bg-card p-6 shadow-xs sm:p-8",
        className
      )}
    >
      <div className="flex flex-wrap items-center justify-between border-b border-border/60 pb-4 gap-4">
        <div>
          <div className="flex items-center gap-2 text-xs font-semibold tracking-wider text-primary uppercase">
            <BookOpen className="h-4 w-4" />
            <span>Khảo chứng Sử liệu & Nguồn dẫn chứng</span>
          </div>
          <h3 className="mt-1 font-display text-xl font-bold text-foreground">
            Thư mục Dẫn chứng & Bằng chứng Lịch sử
          </h3>
          <p className="mt-1 text-xs text-muted-foreground leading-relaxed">
            Mỗi khẳng định lịch sử trong bài viết được bảo chứng bởi thư tịch triều Nguyễn, châu bản hoặc các nghiên cứu thực địa đối chiếu.
          </p>
        </div>
        {onOpenDrawer && (
          <button
            type="button"
            onClick={onOpenDrawer}
            className="inline-flex items-center gap-2 rounded-xl border border-border/80 bg-background px-3.5 py-2 text-xs font-semibold text-foreground transition-colors hover:bg-secondary/60 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary"
          >
            <Layers className="h-4 w-4 text-primary" />
            <span>Xem chi tiết thư tịch (Drawer)</span>
          </button>
        )}
      </div>

      <ol className="mt-6 space-y-4">
        {citations.map((cite, idx) => {
          const indexNum = idx + 1;
          const targetId = cite.id ? `citation-${cite.id}` : `footnote-${indexNum}`;
          const hasSource = cite.has_source !== false && Boolean(cite.source_id || cite.source_title);
          const isDisputed = cite.verification_status === "disputed" || cite.warning === "CLAIM_DISPUTED_NOT_VERIFIED";

          const citationString = [
            cite.author ? `${cite.author}.` : null,
            cite.source_title ? `“${cite.source_title}”` : null,
            cite.publication_year ? `(${cite.publication_year}).` : null,
            cite.locator ? `${cite.locator}.` : null,
          ]
            .filter(Boolean)
            .join(" ");

          return (
            <li
              key={cite.id || idx}
              id={targetId}
              className={cn(
                "rounded-xl border p-4 transition-colors",
                hasSource
                  ? "border-border/70 bg-card/60 hover:bg-card"
                  : "border-amber-500/30 bg-amber-50/40 dark:bg-amber-950/20"
              )}
            >
              <div className="flex flex-wrap items-start justify-between gap-2">
                <div className="flex items-center gap-2">
                  <span className="font-mono text-xs font-bold text-primary">
                    [{indexNum}]
                  </span>
                  <span className="font-semibold text-sm text-foreground">
                    {cite.source_title || "Nguồn thư tịch"}
                  </span>
                  <StoryPassageEpistemicBadge
                    certainty={cite.epistemic_certainty}
                    hasSource={hasSource}
                    verificationStatus={cite.verification_status}
                    isDisputed={isDisputed}
                  />
                </div>

                <div className="flex items-center gap-2">
                  {cite.source_id && (
                    <Link
                      href={`/sources/${cite.source_id}`}
                      className="inline-flex items-center gap-1 text-xs text-primary hover:underline font-medium"
                    >
                      <FileText className="h-3.5 w-3.5" />
                      <span>Xem nguồn</span>
                    </Link>
                  )}
                  {cite.url && (
                    <a
                      href={cite.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center gap-1 text-xs text-muted-foreground hover:text-foreground"
                    >
                      <ExternalLink className="h-3 w-3" />
                      <span>Tài liệu</span>
                    </a>
                  )}
                  <button
                    type="button"
                    onClick={() => handleCopy(cite.id, citationString || cite.source_title)}
                    className="inline-flex items-center gap-1 text-xs text-muted-foreground hover:text-foreground border border-border/60 rounded px-2 py-0.5"
                    title="Sao chép trích dẫn"
                  >
                    {copiedId === cite.id ? (
                      <>
                        <Check className="h-3 w-3 text-emerald-600" />
                        <span className="text-emerald-600">Đã chép</span>
                      </>
                    ) : (
                      <>
                        <Copy className="h-3 w-3" />
                        <span>Trích dẫn</span>
                      </>
                    )}
                  </button>
                </div>
              </div>

              {/* Citation details line */}
              <div className="mt-2 text-xs text-muted-foreground leading-relaxed">
                {cite.author && <span className="font-medium text-foreground">{cite.author} </span>}
                {cite.publication_year && <span>({cite.publication_year}). </span>}
                {cite.locator && <span className="font-mono text-primary/90">{cite.locator}. </span>}
                {cite.citation_text && <span>{cite.citation_text}</span>}
              </div>

              {/* Backing claim statement if available */}
              {cite.claim_statement && (
                <div className="mt-2 rounded-lg bg-secondary/40 p-2.5 text-xs text-foreground/90 border-l-2 border-primary/40">
                  <span className="font-semibold text-muted-foreground">Khẳng định lịch sử: </span>
                  <span>{cite.claim_statement}</span>
                </div>
              )}

              {/* Empty evidence warning */}
              {!hasSource && (
                <div className="mt-2">
                  <EmptyEvidenceWarning message="Khẳng định này chưa có liên kết thư tịch trực tiếp — đang trong diện khảo cứu hoặc chờ bổ sung nguồn." />
                </div>
              )}
            </li>
          );
        })}
      </ol>
    </section>
  );
}

export interface StoryBilingualPassageProps {
  textVi?: string | null;
  textEn?: string | null;
  citations?: StoryCitation[] | null;
  onOpenDrawer?: () => void;
  className?: string;
}

/**
 * StoryBilingualPassage renders Vietnamese and English prose with parsed [^k] footnotes
 * aligned to canonical primary bibliographic source records and open drawer triggers.
 */
export function StoryBilingualPassage({
  textVi,
  textEn,
  citations,
  onOpenDrawer,
  className,
}: StoryBilingualPassageProps) {
  const parsedVi = parseStoryFootnotes(textVi, citations);
  const parsedEn = parseStoryFootnotes(textEn, citations);

  const renderSegments = (segments: Array<{ text: string; footnote?: StoryFootnoteRef }>) => {
    return segments.map((seg, sIdx) => {
      if (seg.footnote) {
        const fn = seg.footnote;
        return (
          <ClaimFootnoteTag
            key={sIdx}
            index={fn.index}
            citationId={fn.citationId}
            sourceTitle={fn.citation?.source_title}
            hasSource={fn.citation?.has_source !== false && Boolean(fn.citation?.source_id || fn.citation?.source_title)}
            onOpenDrawer={onOpenDrawer}
          />
        );
      }
      return <React.Fragment key={sIdx}>{seg.text}</React.Fragment>;
    });
  };

  return (
    <div className={cn("space-y-3", className)}>
      {textVi && (
        <p className="font-serif text-base leading-relaxed text-foreground sm:text-lg">
          {renderSegments(parsedVi.segments)}
        </p>
      )}
      {textEn && (
        <p className="font-serif text-sm italic leading-relaxed text-muted-foreground sm:text-base border-t border-border/40 pt-2.5">
          {renderSegments(parsedEn.segments)}
        </p>
      )}
    </div>
  );
}
