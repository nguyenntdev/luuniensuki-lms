"use client";

import * as React from "react";
import Link from "next/link";
import {
  BookOpen,
  ChevronLeft,
  ChevronRight,
  Clock,
  Sparkles,
  Quote,
  ShieldCheck,
  AlertCircle,
  Info,
  CheckCircle2,
  Share2,
  Bookmark,
  Volume2,
  VolumeX,
  Play,
  Pause,
  ExternalLink,
  Copy,
  Check,
  X,
  Layers,
  ArrowRight,
  HelpCircle,
  FileText,
} from "lucide-react";
import { cn } from "@/lib/utils";
import type {
  RbpcStory,
  StoryChapter,
  StoryBlock,
  RbpcClaimEvidence,
  RbpcCreator,
  RbpcExperience,
  LocalizedField,
  EpistemicCertainty,
} from "@/types/rbpc";
import type { RbpcLocale } from "@/lib/rbpc/copy";
import { getRbpcCopy } from "@/lib/rbpc/copy";
import { SketchfabExhibit } from "@/components/media/SketchfabExhibit";
import { LivingBridgeCard } from "./LivingBridgeCard";
import { resolveLocalizedText } from "./LivingBridgeCard";
import { StoryArtisanBridge } from "@/components/rbpc/StoryArtisanBridge";

export interface StoryViewerStoryData {
  id: string;
  slug: string;
  title: LocalizedField | string;
  intro?: LocalizedField | string;
  approvedSummary?: LocalizedField | string;
  heroImageUrl?: string;
  heroImageAlt?: string;
  readingTimeMinutes?: number;
  chapters?: StoryChapter[];
  blocks?: StoryBlock[]; // Fallback flat blocks
  evidenceClaims?: RbpcClaimEvidence[];
  creator?: RbpcCreator;
  experience?: RbpcExperience;
  heritagePlaceSlug?: string;
  reviewedBy?: string;
  reviewedAt?: string;
}

export interface StoryChapterViewerProps extends React.HTMLAttributes<HTMLDivElement> {
  /** Complete story record with chapters and polymorphic content blocks */
  story: RbpcStory | StoryViewerStoryData;
  /** Initial active chapter index (0-based) */
  initialChapterIndex?: number;
  /** Active UI locale ("vi" | "en", defaults to "vi") */
  locale?: RbpcLocale;
  /** Additional custom class names */
  className?: string;
  /** Callback fired when user navigates between chapters */
  onChapterChange?: (chapterIndex: number, chapter: StoryChapter) => void;
  /** Callback fired when an inline citation reference is activated */
  onCitationClick?: (citation: RbpcClaimEvidence | string) => void;
  /** Callback fired when an artisan counterpart is clicked */
  onArtisanClick?: (creatorSlug: string) => void;
  /** Callback fired when an experience inquiry is requested */
  onExperienceClick?: (experienceSlug: string) => void;
  /** Callback fired when user requests workshop availability */
  onRequestAvailability?: (experienceSlug?: string, creatorSlug?: string) => void;
  /** Living artisan counterpart override */
  creator?: RbpcCreator;
  /** Living workshop experience counterpart override */
  experience?: RbpcExperience;
  /** Whether to allow opening the built-in InquiryFormModal directly (defaults to true) */
  enableInquiryModal?: boolean;
  /** Explicit control over displaying StoryArtisanBridge at the end of chapters */
  showArtisanBridge?: boolean;
}

/**
 * Epistemic certainty badge configuration
 */
const CERTAINTY_CONFIG: Record<
  EpistemicCertainty,
  { labelVi: string; labelEn: string; badgeClass: string }
> = {
  high: {
    labelVi: "Độ tin cậy cao (Đa nguồn chính sử)",
    labelEn: "High Certainty (Multiple Sources)",
    badgeClass: "bg-emerald-50 text-emerald-800 border-emerald-300 dark:bg-emerald-950/40 dark:text-emerald-300",
  },
  medium: {
    labelVi: "Độ tin cậy vừa (Nguồn độc bản)",
    labelEn: "Medium Certainty",
    badgeClass: "bg-teal-50 text-teal-800 border-teal-300 dark:bg-teal-950/40 dark:text-teal-300",
  },
  contested: {
    labelVi: "Còn ý kiến tranh biện học thuật",
    labelEn: "Scholarly Contested",
    badgeClass: "bg-purple-50 text-purple-800 border-purple-300 dark:bg-purple-950/40 dark:text-purple-300",
  },
  insufficient_sources: {
    labelVi: "Nguồn thư tịch chưa đầy đủ",
    labelEn: "Insufficient Sources",
    badgeClass: "bg-amber-50 text-amber-800 border-amber-300 dark:bg-amber-950/40 dark:text-amber-300",
  },
};

/**
 * StoryChapterViewer Component
 *
 * Implements the comprehensive multi-chapter reading interface:
 * 1. Smooth reading progress bar tracking overall completion
 * 2. Chapter navigation bar with Table of Contents jump menu
 * 3. Polymorphic block renderer:
 *    - Text with interactive inline citation triggers
 *    - Stylized quote callouts with speaker lineage & citation
 *    - Thematic callouts (cultural_note, epistemic, warning, info)
 *    - Source excerpts with ancient text and modern translation
 *    - LivingBridgeCard embedded for living artisan continuity
 *    - SketchfabExhibit 3D models embedded
 *    - Audio oral history excerpts with transcripts
 * 4. Interactive citation detail drawer / modal
 */
export function StoryChapterViewer({
  story,
  initialChapterIndex = 0,
  locale = "vi",
  className,
  onChapterChange,
  onCitationClick,
  onArtisanClick,
  onExperienceClick,
  onRequestAvailability,
  creator,
  experience,
  enableInquiryModal = true,
  showArtisanBridge,
  ...restProps
}: StoryChapterViewerProps) {
  const isEn = locale === "en";
  const dict = getRbpcCopy(locale);

  const activeCreator = creator || story.creator;
  const activeExperience = experience || story.experience;
  const hasArtisanData = Boolean(
    activeCreator ||
    activeExperience ||
    ("creatorSlug" in story && story.creatorSlug) ||
    ("experienceSlug" in story && story.experienceSlug)
  );

  // Normalize chapters list from story
  const chapters: StoryChapter[] = React.useMemo(() => {
    if (story.chapters && story.chapters.length > 0) {
      return story.chapters;
    }
    // Fallback: If story has flat blocks without chapters, wrap in a single chapter
    if (story.blocks && story.blocks.length > 0) {
      return [
        {
          id: "chapter-default",
          chapterNumber: 1,
          slug: "toan-van",
          title: typeof story.title === "string" ? { vi: story.title } : story.title,
          summary: typeof story.intro === "string" ? { vi: story.intro } : story.intro,
          readingTimeMinutes: story.readingTimeMinutes || 5,
          blocks: story.blocks,
        },
      ];
    }
    return [];
  }, [story]);

  const [activeChapterIndex, setActiveChapterIndex] = React.useState<number>(
    Math.min(Math.max(0, initialChapterIndex), Math.max(0, chapters.length - 1))
  );

  const [activeCitationModal, setActiveCitationModal] = React.useState<
    RbpcClaimEvidence | string | null
  >(null);
  const [copiedCitation, setCopiedCitation] = React.useState(false);
  const [tocOpen, setTocOpen] = React.useState(false);

  // Synchronize initial chapter index if props change
  React.useEffect(() => {
    if (initialChapterIndex >= 0 && initialChapterIndex < chapters.length) {
      setActiveChapterIndex((prev) =>
        prev !== initialChapterIndex ? initialChapterIndex : prev
      );
    }
  }, [initialChapterIndex, chapters.length]);

  const currentChapter = chapters[activeChapterIndex] || chapters[0];

  const chapterHasInlineArtisanBridge = currentChapter?.blocks?.some(
    (b) => b.type === "artisan_bridge"
  );

  const shouldRenderArtisanBridge =
    showArtisanBridge !== undefined
      ? showArtisanBridge
      : hasArtisanData && !chapterHasInlineArtisanBridge;

  const handleSelectChapter = (idx: number) => {
    if (idx >= 0 && idx < chapters.length) {
      setActiveChapterIndex(idx);
      setTocOpen(false);
      onChapterChange?.(idx, chapters[idx]);
      // Scroll smoothly to top of chapter content
      if (typeof window !== "undefined") {
        window.scrollTo({ top: 0, behavior: "smooth" });
      }
    }
  };

  // Calculate progress percentage
  const progressPercent = chapters.length > 0
    ? Math.round(((activeChapterIndex + 1) / chapters.length) * 100)
    : 100;

  const storyTitle = resolveLocalizedText(story.title, locale);
  const currentChapterTitle = currentChapter
    ? resolveLocalizedText(currentChapter.title, locale)
    : "";

  // Inline citation click handler
  const handleTriggerCitation = (citationToken: string) => {
    // Try to find matching evidence claim from story
    const matchedClaim = story.evidenceClaims?.find(
      (c) =>
        c.citationLabel === citationToken ||
        c.id === citationToken ||
        `[${c.citationLabel}]` === citationToken ||
        c.locator?.includes(citationToken)
    );

    const citationToOpen = matchedClaim || citationToken;
    setActiveCitationModal(citationToOpen);
    onCitationClick?.(citationToOpen);
  };

  return (
    <article
      aria-label={storyTitle}
      className={cn(
        "relative mx-auto max-w-4xl rounded-2xl border border-[var(--rbpc-divider)] bg-[var(--rbpc-surface)] shadow-xs",
        className
      )}
      {...restProps}
    >
      {/* 1. STICKY READING PROGRESS BAR */}
      <div
        role="progressbar"
        aria-valuenow={progressPercent}
        aria-valuemin={0}
        aria-valuemax={100}
        aria-label={isEn ? "Story Reading Progress" : "Tiến độ đọc câu chuyện"}
        className="sticky top-0 z-30 h-1.5 w-full bg-[var(--rbpc-divider-subtle)]"
      >
        <div
          className="h-full bg-gradient-to-r from-[var(--rbpc-primary)] via-[var(--rbpc-highlight)] to-[var(--rbpc-primary)] transition-all duration-300"
          style={{ width: `${progressPercent}%` }}
        />
      </div>

      {/* 2. STORY & CHAPTER TOP NAVIGATION BAR */}
      <header className="border-b border-[var(--rbpc-divider-subtle)] px-5 py-4 sm:px-8">
        <div className="flex flex-wrap items-center justify-between gap-3 text-xs text-[var(--rbpc-muted)]">
          {/* Breadcrumb / Story reference */}
          <div className="flex items-center gap-1.5 font-medium text-[var(--rbpc-ink-subtle)]">
            <BookOpen className="h-4 w-4 text-[var(--rbpc-primary)]" aria-hidden="true" />
            <span className="truncate max-w-[200px] sm:max-w-xs">{storyTitle}</span>
          </div>

          {/* Reading Time & Progress Indicator */}
          <div className="flex items-center gap-3">
            {currentChapter?.readingTimeMinutes && (
              <span className="inline-flex items-center gap-1">
                <Clock className="h-3.5 w-3.5 text-[var(--rbpc-primary)]" aria-hidden="true" />
                <span>
                  {currentChapter.readingTimeMinutes} {isEn ? "min read" : "phút đọc"}
                </span>
              </span>
            )}

            <span className="rounded-full bg-[var(--rbpc-primary-subtle)] px-2.5 py-0.5 font-semibold text-[var(--rbpc-primary)]">
              {isEn ? "Chapter" : "Chương"} {activeChapterIndex + 1}/{chapters.length} ({progressPercent}%)
            </span>
          </div>
        </div>

        {/* Chapter Header Title */}
        <div className="mt-4 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
          <div>
            <span className="text-[11px] font-bold uppercase tracking-wider text-[var(--rbpc-highlight)]">
              {isEn ? `Chapter 0${activeChapterIndex + 1}` : `Chương 0${activeChapterIndex + 1}`}
            </span>
            <h1 className="font-serif text-2xl sm:text-3xl font-bold text-[var(--rbpc-ink)] mt-1">
              {currentChapterTitle}
            </h1>
            {currentChapter?.summary && (
              <p className="mt-2 text-xs sm:text-sm text-[var(--rbpc-muted)] leading-relaxed max-w-2xl">
                {resolveLocalizedText(currentChapter.summary, locale)}
              </p>
            )}
          </div>

          {/* Table of Contents Dropdown Button */}
          {chapters.length > 1 && (
            <div className="relative shrink-0">
              <button
                type="button"
                onClick={() => setTocOpen(!tocOpen)}
                aria-expanded={tocOpen}
                aria-haspopup="listbox"
                className="inline-flex items-center gap-1.5 rounded-lg border border-[var(--rbpc-divider)] bg-[var(--rbpc-surface-elevated)] px-3.5 py-2 text-xs font-semibold text-[var(--rbpc-ink)] shadow-2xs hover:bg-[var(--rbpc-surface-muted)] transition-colors min-h-[44px] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--rbpc-focus,#1E675A)] focus-visible:ring-offset-2"
              >
                <Layers className="h-4 w-4 text-[var(--rbpc-primary)]" aria-hidden="true" />
                <span>{isEn ? "Chapters Index" : "Mục lục chương"}</span>
              </button>

              {/* TOC Dropdown Menu */}
              {tocOpen && (
                <div
                  role="listbox"
                  aria-label={isEn ? "Chapters index" : "Danh sách chương"}
                  className="absolute right-0 mt-2 w-72 sm:w-80 rounded-xl border border-[var(--rbpc-divider)] bg-[var(--rbpc-surface-elevated)] p-2 shadow-xl z-20"
                >
                  <div className="px-3 py-2 border-b border-[var(--rbpc-divider-subtle)] text-[11px] font-bold uppercase text-[var(--rbpc-muted)]">
                    {isEn ? "Story Chapters" : "Các chương câu chuyện"}
                  </div>
                  <div className="mt-1 max-h-64 overflow-y-auto space-y-1">
                    {chapters.map((ch, idx) => (
                      <button
                        key={ch.id || idx}
                        type="button"
                        onClick={() => handleSelectChapter(idx)}
                        className={cn(
                          "flex w-full items-start gap-2.5 rounded-lg px-3 py-2 text-left text-xs transition-colors min-h-[44px] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--rbpc-focus,#1E675A)] focus-visible:ring-offset-2",
                          activeChapterIndex === idx
                            ? "bg-[var(--rbpc-primary-subtle)] font-bold text-[var(--rbpc-primary)]"
                            : "hover:bg-[var(--rbpc-surface-muted)] text-[var(--rbpc-ink)]"
                        )}
                      >
                        <span className="shrink-0 font-mono text-[11px] text-[var(--rbpc-highlight)]">
                          {String(idx + 1).padStart(2, "0")}
                        </span>
                        <div className="min-w-0 flex-1">
                          <p className="truncate font-serif">
                            {resolveLocalizedText(ch.title, locale)}
                          </p>
                          {ch.readingTimeMinutes && (
                            <span className="text-[10px] text-[var(--rbpc-muted)]">
                              {ch.readingTimeMinutes} {isEn ? "mins" : "phút"}
                            </span>
                          )}
                        </div>
                      </button>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </header>

      {/* 3. CHAPTER CONTENT BLOCKS (Constrained to max-w-[720px] for optimal editorial prose reading) */}
      <section className="px-5 py-6 sm:px-8 sm:py-8 space-y-7 max-w-[720px] mx-auto">
        {currentChapter?.blocks && currentChapter.blocks.length > 0 ? (
          currentChapter.blocks.map((block, idx) => (
            <StoryBlockRenderer
              key={block.id || idx}
              block={block}
              locale={locale}
              onTriggerCitation={handleTriggerCitation}
              onArtisanClick={onArtisanClick}
              onExperienceClick={onExperienceClick}
            />
          ))
        ) : (
          <div className="py-12 text-center text-xs text-[var(--rbpc-muted)]">
            {isEn
              ? "Chapter content is currently undergoing editorial review."
              : "Nội dung chương này đang trong tiến trình đối chiếu và biên tập."}
          </div>
        )}

        {/* Living Artisan Bridge at the end of story chapters */}
        {shouldRenderArtisanBridge && (
          <div className="pt-6 border-t border-[var(--rbpc-divider-subtle)]" data-testid="story-chapter-artisan-bridge">
            <StoryArtisanBridge
              creator={activeCreator}
              experience={activeExperience}
              locale={locale}
              onViewMaker={onArtisanClick}
              onViewExperience={onExperienceClick}
              onRequestAvailability={(expSlug, crSlug) => {
                onRequestAvailability?.(expSlug, crSlug);
                if (expSlug) onExperienceClick?.(expSlug);
              }}
              enableInlineModal={enableInquiryModal}
            />
          </div>
        )}
      </section>

      {/* 4. CHAPTER NAVIGATION FOOTER */}
      <footer className="border-t border-[var(--rbpc-divider-subtle)] px-5 py-5 sm:px-8 bg-[var(--rbpc-surface-muted)]/40 rounded-b-2xl">
        <div className="flex flex-col sm:flex-row items-center justify-between gap-3">
          {/* Previous Chapter button */}
          {activeChapterIndex > 0 ? (
            <button
              type="button"
              onClick={() => handleSelectChapter(activeChapterIndex - 1)}
              className="inline-flex items-center gap-2 rounded-xl border border-[var(--rbpc-divider)] bg-[var(--rbpc-surface)] px-4 py-2.5 text-xs font-semibold text-[var(--rbpc-ink)] shadow-2xs hover:bg-[var(--rbpc-surface-muted)] transition-colors min-h-[44px] w-full sm:w-auto justify-center focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--rbpc-focus,#1E675A)] focus-visible:ring-offset-2"
            >
              <ChevronLeft className="h-4 w-4" aria-hidden="true" />
              <span>
                {isEn ? "Previous:" : "Chương trước:"}{" "}
                <span className="font-serif">
                  {resolveLocalizedText(chapters[activeChapterIndex - 1]?.title, locale)}
                </span>
              </span>
            </button>
          ) : (
            <div className="hidden sm:block" />
          )}

          {/* Next Chapter or Story Completion button */}
          {activeChapterIndex < chapters.length - 1 ? (
            <button
              type="button"
              onClick={() => handleSelectChapter(activeChapterIndex + 1)}
              className="inline-flex items-center gap-2 rounded-xl bg-[var(--rbpc-primary)] px-5 py-2.5 text-xs font-semibold text-white shadow-xs hover:bg-[var(--rbpc-primary-hover)] transition-colors min-h-[44px] w-full sm:w-auto justify-center focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--rbpc-focus,#1E675A)] focus-visible:ring-offset-2"
            >
              <span>
                {isEn ? "Next:" : "Chương tiếp theo:"}{" "}
                <span className="font-serif">
                  {resolveLocalizedText(chapters[activeChapterIndex + 1]?.title, locale)}
                </span>
              </span>
              <ChevronRight className="h-4 w-4" aria-hidden="true" />
            </button>
          ) : (
            /* Story Completion celebration block */
            <div className="flex items-center gap-2 rounded-xl bg-emerald-50 px-4 py-2 text-xs font-semibold text-emerald-800 border border-emerald-200 dark:bg-emerald-950/40 dark:text-emerald-300">
              <CheckCircle2 className="h-4 w-4" aria-hidden="true" />
              <span>{isEn ? "You've read the full story!" : "Bạn đã hoàn thành câu chuyện!"}</span>
            </div>
          )}
        </div>
      </footer>

      {/* 5. INTERACTIVE INLINE CITATION MODAL / DRAWER (Zero heavy backdrop-blur) */}
      {activeCitationModal && (
        <div
          role="dialog"
          aria-modal="true"
          aria-label={isEn ? "Bibliographic Citation" : "Trích dẫn thư tịch"}
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4"
        >
          <div className="relative max-w-lg w-full rounded-2xl border border-[var(--rbpc-divider)] bg-[var(--rbpc-surface-elevated)] p-5 shadow-2xl">
            {/* Modal Header */}
            <div className="flex items-center justify-between border-b border-[var(--rbpc-divider-subtle)] pb-3">
              <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-[var(--rbpc-primary)]">
                <BookOpen className="h-4 w-4" aria-hidden="true" />
                <span>{isEn ? "Authoritative Citation" : "Khảo cứu thư tịch đối chiếu"}</span>
              </div>
              <button
                type="button"
                onClick={() => {
                  setActiveCitationModal(null);
                  setCopiedCitation(false);
                }}
                aria-label={isEn ? "Close citation" : "Đóng trích dẫn"}
                className="rounded-lg p-1.5 text-[var(--rbpc-muted)] hover:bg-[var(--rbpc-surface-muted)] hover:text-[var(--rbpc-ink)] min-h-[44px] min-w-[44px] flex items-center justify-center focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--rbpc-focus,#1E675A)] focus-visible:ring-offset-2"
              >
                <X className="h-4 w-4" aria-hidden="true" />
              </button>
            </div>

            {/* Modal Body */}
            <div className="mt-4 space-y-3">
              {typeof activeCitationModal === "string" ? (
                <div className="rounded-xl bg-[var(--rbpc-surface-muted)] p-3.5 text-xs text-[var(--rbpc-ink)]">
                  <span className="font-semibold">{isEn ? "Citation marker: " : "Ký hiệu trích dẫn: "}</span>
                  {activeCitationModal}
                </div>
              ) : (
                <>
                  <div className="flex items-center justify-between gap-2">
                    <span className="font-serif text-sm font-bold text-[var(--rbpc-ink)]">
                      {activeCitationModal.sourceTitle}
                    </span>
                    {activeCitationModal.locator && (
                      <span className="rounded bg-[var(--rbpc-surface-muted)] px-2 py-0.5 font-mono text-[11px] font-semibold text-[var(--rbpc-ink)] border border-[var(--rbpc-divider)]">
                        {activeCitationModal.locator}
                      </span>
                    )}
                  </div>

                  <div className="rounded-xl bg-[var(--rbpc-surface-muted)] p-3 text-xs italic text-[var(--rbpc-ink)] border-l-2 border-[var(--rbpc-primary)]">
                    “{activeCitationModal.statement}”
                  </div>

                  <div className="flex flex-wrap items-center justify-between gap-2 text-[11px] text-[var(--rbpc-muted)] pt-2">
                    <span>
                      {isEn ? "Category: " : "Nhóm đối chiếu: "}
                      <strong className="text-[var(--rbpc-ink)]">{activeCitationModal.claimCategory}</strong>
                    </span>
                    <span className="rounded bg-emerald-50 text-emerald-800 px-2 py-0.5 font-semibold">
                      {activeCitationModal.reviewStatus}
                    </span>
                  </div>
                </>
              )}
            </div>

            {/* Modal Footer Actions */}
            <div className="mt-5 flex items-center justify-between border-t border-[var(--rbpc-divider-subtle)] pt-3 text-xs">
              <button
                type="button"
                onClick={() => {
                  const citationString =
                    typeof activeCitationModal === "string"
                      ? activeCitationModal
                      : `${activeCitationModal.sourceTitle}. ${activeCitationModal.locator || ""}. Statement: ${activeCitationModal.statement}`;
                  if (typeof navigator !== "undefined" && navigator.clipboard) {
                    navigator.clipboard.writeText(citationString).catch(() => {});
                  }
                  setCopiedCitation(true);
                  setTimeout(() => setCopiedCitation(false), 2000);
                }}
                className={cn(
                  "inline-flex items-center gap-1.5 rounded-lg px-3.5 py-2 font-semibold transition-colors min-h-[44px] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--rbpc-focus,#1E675A)] focus-visible:ring-offset-2",
                  copiedCitation
                    ? "bg-emerald-100 text-emerald-800"
                    : "bg-[var(--rbpc-surface-muted)] text-[var(--rbpc-ink)] hover:bg-[var(--rbpc-divider)]"
                )}
              >
                {copiedCitation ? (
                  <>
                    <Check className="h-3.5 w-3.5" aria-hidden="true" />
                    <span>{isEn ? "Copied" : "Đã sao chép"}</span>
                  </>
                ) : (
                  <>
                    <Copy className="h-3.5 w-3.5" aria-hidden="true" />
                    <span>{isEn ? "Copy Citation" : "Sao chép trích dẫn"}</span>
                  </>
                )}
              </button>

              {typeof activeCitationModal !== "string" && activeCitationModal.sourceUrl && (
                <a
                  href={activeCitationModal.sourceUrl}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-1 font-semibold text-[var(--rbpc-primary)] hover:underline min-h-[44px] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--rbpc-focus,#1E675A)] focus-visible:ring-offset-2 rounded-sm"
                >
                  <span>{isEn ? "Visit Source" : "Mở nguồn tư liệu"}</span>
                  <ExternalLink className="h-3.5 w-3.5" aria-hidden="true" />
                </a>
              )}
            </div>
          </div>
        </div>
      )}
    </article>
  );
}

/**
 * StoryBlockRenderer Component
 * Handles the rendering of polymorphic story blocks
 */
export function StoryBlockRenderer({
  block,
  locale = "vi",
  onTriggerCitation,
  onArtisanClick,
  onExperienceClick,
}: {
  block: StoryBlock;
  locale?: RbpcLocale;
  onTriggerCitation?: (citationToken: string) => void;
  onArtisanClick?: (creatorSlug: string) => void;
  onExperienceClick?: (experienceSlug: string) => void;
}) {
  const isEn = locale === "en";

  switch (block.type) {
    // ------------------------------------------------------------------------
    // 1. TEXT BLOCK WITH INLINE CITATIONS
    // ------------------------------------------------------------------------
    case "text": {
      // Split text by inline citation tags like [1], [2], [Tr. 45], [^1]
      const citationRegex = /(\[(?:\d+|Tr\.[^\]]+|\^[0-9]+)\])/g;
      const parts = block.body.split(citationRegex);

      return (
        <div className="space-y-3">
          {block.title && (
            <h3 className="font-serif text-xl sm:text-2xl font-bold text-[var(--rbpc-ink)]">
              {block.title}
            </h3>
          )}
          <p className="font-serif text-base sm:text-lg leading-[1.8] text-[var(--rbpc-ink)]">
            {parts.map((part, pIdx) => {
              if (citationRegex.test(part)) {
                return (
                  <button
                    key={pIdx}
                    type="button"
                    onClick={() => onTriggerCitation?.(part)}
                    aria-label={`Trích dẫn ${part}`}
                    className="inline-flex items-center mx-1 align-super font-mono text-[11px] font-bold text-[var(--rbpc-primary)] bg-[var(--rbpc-primary-subtle)] px-2 py-0.5 rounded-md hover:bg-[var(--rbpc-primary)] hover:text-white transition-colors cursor-pointer focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--rbpc-focus,#1E675A)] focus-visible:ring-offset-1"
                  >
                    {part}
                  </button>
                );
              }
              return <React.Fragment key={pIdx}>{part}</React.Fragment>;
            })}
          </p>
        </div>
      );
    }

    // ------------------------------------------------------------------------
    // 2. QUOTE CALLOUT BLOCK
    // ------------------------------------------------------------------------
    case "quote": {
      return (
        <figure className="relative my-6 rounded-2xl border-l-4 border-[var(--rbpc-highlight)] bg-[var(--rbpc-surface-muted)]/60 p-5 sm:p-6 shadow-2xs">
          <Quote className="h-8 w-8 text-[var(--rbpc-highlight)]/40 mb-2" aria-hidden="true" />
          <blockquote className="font-serif text-base sm:text-xl italic leading-relaxed text-[var(--rbpc-ink)]">
            “{block.quote}”
          </blockquote>
          <figcaption className="mt-3 flex flex-wrap items-center justify-between gap-2 border-t border-[var(--rbpc-divider-subtle)] pt-2.5 text-xs text-[var(--rbpc-muted)]">
            <div className="flex items-center gap-1.5">
              <span className="font-bold text-[var(--rbpc-ink)]">— {block.speaker}</span>
              {block.roleOrLineage && <span>({block.roleOrLineage})</span>}
            </div>
            {block.sourceCitation && (
              <span className="rounded bg-[var(--rbpc-surface)] px-2 py-0.5 font-mono text-[10px] text-[var(--rbpc-primary)] border border-[var(--rbpc-divider)]">
                {block.sourceCitation}
              </span>
            )}
          </figcaption>
        </figure>
      );
    }

    // ------------------------------------------------------------------------
    // 3. EDITORIAL CALLOUT BLOCK
    // ------------------------------------------------------------------------
    case "callout": {
      const toneStyles = {
        cultural_note: "border-[var(--rbpc-highlight)] bg-[var(--rbpc-highlight-subtle)] text-[var(--rbpc-ink)]",
        epistemic: "border-[var(--rbpc-primary)] bg-[var(--rbpc-primary-subtle)] text-[var(--rbpc-ink)]",
        warning: "border-amber-500 bg-amber-50/70 dark:bg-amber-950/30 text-amber-950 dark:text-amber-200",
        info: "border-sky-500 bg-sky-50/70 dark:bg-sky-950/30 text-sky-950 dark:text-sky-200",
      };

      const toneIcons = {
        cultural_note: Sparkles,
        epistemic: ShieldCheck,
        warning: AlertCircle,
        info: Info,
      };

      const ToneIcon = toneIcons[block.tone] || Info;

      return (
        <aside
          role="note"
          className={cn(
            "my-5 rounded-xl border-l-4 p-4 text-xs sm:text-sm leading-relaxed",
            toneStyles[block.tone] || toneStyles.info
          )}
        >
          <div className="flex items-start gap-3">
            <ToneIcon className="h-5 w-5 shrink-0 mt-0.5" aria-hidden="true" />
            <div className="space-y-1">
              {block.title && (
                <h4 className="font-serif font-bold text-sm sm:text-base">
                  {block.title}
                </h4>
              )}
              <p>{block.body}</p>
            </div>
          </div>
        </aside>
      );
    }

    // ------------------------------------------------------------------------
    // 4. SOURCE EXCERPT BLOCK (ANCIENT TEXT + MODERN TRANSLATION)
    // ------------------------------------------------------------------------
    case "source_excerpt": {
      const certainty = CERTAINTY_CONFIG[block.certainty] || CERTAINTY_CONFIG.medium;

      return (
        <section
          aria-label="Đoạn trích thư tịch lịch sử"
          className="my-6 rounded-2xl border border-[var(--rbpc-divider)] bg-[var(--rbpc-surface-elevated)] p-5 shadow-xs"
        >
          <div className="flex flex-wrap items-center justify-between gap-2 border-b border-[var(--rbpc-divider-subtle)] pb-3">
            <div className="flex items-center gap-2">
              <FileText className="h-4 w-4 text-[var(--rbpc-primary)]" aria-hidden="true" />
              <h4 className="font-serif text-sm font-bold text-[var(--rbpc-ink)]">
                {block.sourceTitle}
              </h4>
            </div>

            <span
              className={cn(
                "rounded-md border px-2 py-0.5 text-[10px] font-semibold",
                certainty.badgeClass
              )}
            >
              {isEn ? certainty.labelEn : certainty.labelVi}
            </span>
          </div>

          {/* Original Text (Hán Nôm or Classical Vietnamese) */}
          <div className="mt-3 rounded-lg bg-[var(--rbpc-surface-muted)]/80 p-3.5 font-serif text-sm leading-relaxed text-[var(--rbpc-ink)] border-l-2 border-[var(--rbpc-highlight)]">
            <span className="text-[10px] font-bold uppercase tracking-wider text-[var(--rbpc-muted)] block mb-1">
              {isEn ? "Original Excerpt" : "Nguyên văn Thư tịch"}
            </span>
            “{block.originalText}”
          </div>

          {/* Modern Translation */}
          {block.modernTranslation && (
            <div className="mt-3 p-2 text-xs sm:text-sm text-[var(--rbpc-muted)] leading-relaxed">
              <span className="text-[10px] font-bold uppercase tracking-wider text-[var(--rbpc-ink)] block mb-1">
                {isEn ? "Modern Translation / Exegesis" : "Bản dịch & Khảo giải"}
              </span>
              {block.modernTranslation}
            </div>
          )}

          {block.locator && (
            <div className="mt-3 border-t border-[var(--rbpc-divider-subtle)] pt-2 text-right text-[11px] font-mono text-[var(--rbpc-muted)]">
              {block.locator}
            </div>
          )}
        </section>
      );
    }

    // ------------------------------------------------------------------------
    // 5. LIVING ARTISAN BRIDGE BLOCK
    // ------------------------------------------------------------------------
    case "artisan_bridge": {
      return (
        <div className="my-8">
          <StoryArtisanBridge
            block={block}
            locale={locale}
            onViewMaker={onArtisanClick}
            onViewExperience={onExperienceClick}
            onRequestAvailability={(expSlug, crSlug) => {
              if (expSlug) onExperienceClick?.(expSlug);
            }}
            enableInlineModal={true}
          />
        </div>
      );
    }

    // ------------------------------------------------------------------------
    // 6. 3D MODEL EXHIBIT BLOCK
    // ------------------------------------------------------------------------
    case "model_3d": {
      return (
        <div className="my-6">
          <SketchfabExhibit
            modelId={block.modelId}
            modelTitle={block.title}
            creatorName={block.creatorCredit}
            licenseText={block.license}
            thumbnailUrl={block.stillPhotoFallbackUrl}
            modelUrl={block.embedUrl}
            className="w-full"
          />
        </div>
      );
    }

    // ------------------------------------------------------------------------
    // 7. IMAGE BLOCK
    // ------------------------------------------------------------------------
    case "image": {
      return (
        <figure className="my-6 overflow-hidden rounded-2xl border border-[var(--rbpc-divider)] bg-[var(--rbpc-surface)] shadow-xs">
          <img
            src={block.url}
            alt={block.altText}
            loading="lazy"
            className="w-full max-h-[500px] object-cover"
          />
          {(block.caption || block.credit || block.rightsRef) && (
            <figcaption className="flex flex-wrap items-center justify-between gap-2 p-3 text-xs text-[var(--rbpc-muted)] bg-[var(--rbpc-surface-muted)]/50">
              {block.caption && <span>{block.caption}</span>}
              <div className="flex items-center gap-2 text-[11px]">
                {block.credit && <span>Ảnh: {block.credit}</span>}
                {block.rightsRef && (
                  <span className="rounded bg-black/10 dark:bg-white/10 px-1.5 py-0.5 font-semibold">
                    {block.rightsRef}
                  </span>
                )}
              </div>
            </figcaption>
          )}
        </figure>
      );
    }

    // ------------------------------------------------------------------------
    // 8. AUDIO RECORDING (ORAL HISTORY) BLOCK
    // ------------------------------------------------------------------------
    case "audio_recording": {
      return (
        <div className="my-6 rounded-2xl border border-[var(--rbpc-divider)] bg-[var(--rbpc-surface-elevated)] p-4 shadow-xs">
          <div className="flex items-center justify-between gap-3">
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-[var(--rbpc-primary-subtle)] text-[var(--rbpc-primary)]">
                <Volume2 className="h-5 w-5" aria-hidden="true" />
              </div>
              <div>
                <h4 className="font-serif text-sm font-bold text-[var(--rbpc-ink)]">
                  {block.title}
                </h4>
                <p className="text-xs text-[var(--rbpc-muted)]">
                  {block.speakerName} • {Math.round(block.durationSeconds / 60)} {isEn ? "mins" : "phút"}
                </p>
              </div>
            </div>

            <audio controls src={block.audioUrl} className="max-w-[240px] h-9" />
          </div>

          {block.transcript && (
            <div className="mt-3 rounded-lg bg-[var(--rbpc-surface-muted)] p-3 text-xs text-[var(--rbpc-ink)] border-l-2 border-[var(--rbpc-primary)]">
              <span className="font-semibold block mb-1">
                {isEn ? "Transcript Excerpt: " : "Trích lược lời kể: "}
              </span>
              “{block.transcript}”
            </div>
          )}
        </div>
      );
    }

    // ------------------------------------------------------------------------
    // 9. REFLECTION PROMPT BLOCK
    // ------------------------------------------------------------------------
    case "reflection_prompt": {
      return (
        <div className="my-6 rounded-2xl border border-[var(--rbpc-primary-border)] bg-[var(--rbpc-primary-subtle)] p-5">
          <div className="flex items-start gap-3">
            <HelpCircle className="h-5 w-5 text-[var(--rbpc-primary)] shrink-0 mt-0.5" aria-hidden="true" />
            <div className="space-y-2">
              <h4 className="font-serif text-base font-bold text-[var(--rbpc-primary)]">
                {isEn ? "Reflective Inquiry" : "Gợi mở Suy ngẫm"}
              </h4>
              <p className="font-serif text-sm sm:text-base italic text-[var(--rbpc-ink)]">
                {block.question}
              </p>
              {block.helperText && (
                <p className="text-xs text-[var(--rbpc-muted)]">{block.helperText}</p>
              )}
            </div>
          </div>
        </div>
      );
    }

    // ------------------------------------------------------------------------
    // 10. COMPARISON BLOCK
    // ------------------------------------------------------------------------
    case "comparison": {
      return (
        <div className="my-6 rounded-2xl border border-[var(--rbpc-divider)] bg-[var(--rbpc-surface)] p-5">
          <h4 className="font-serif text-base font-bold text-[var(--rbpc-ink)] mb-3">
            {isEn ? "Historical vs Contemporary Continuity" : "Đối sánh Lịch sử & Hiện tại"}
          </h4>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="rounded-xl bg-[var(--rbpc-surface-muted)] p-4 border border-[var(--rbpc-divider)]">
              <span className="text-[10px] font-bold uppercase text-[var(--rbpc-muted)]">
                {isEn ? "Imperial Past" : "Thời Nguyễn Lịch sử"}
              </span>
              <h5 className="font-serif text-sm font-bold text-[var(--rbpc-ink)] mt-1">
                {block.historical.title}
              </h5>
              <p className="mt-1 text-xs text-[var(--rbpc-muted)] leading-relaxed">
                {block.historical.description}
              </p>
            </div>
            <div className="rounded-xl bg-[var(--rbpc-surface-muted)] p-4 border border-[var(--rbpc-highlight-border)]">
              <span className="text-[10px] font-bold uppercase text-[var(--rbpc-highlight)]">
                {isEn ? "Contemporary Living Practice" : "Thực hành Đương đại"}
              </span>
              <h5 className="font-serif text-sm font-bold text-[var(--rbpc-ink)] mt-1">
                {block.contemporary.title}
              </h5>
              <p className="mt-1 text-xs text-[var(--rbpc-muted)] leading-relaxed">
                {block.contemporary.description}
              </p>
            </div>
          </div>
          {block.synthesisNote && (
            <p className="mt-3 text-xs text-[var(--rbpc-ink-subtle)] italic text-center">
              * {block.synthesisNote}
            </p>
          )}
        </div>
      );
    }

    // ------------------------------------------------------------------------
    // 11. CULTURAL CONTEXT BLOCK
    // ------------------------------------------------------------------------
    case "cultural_context": {
      return (
        <div className="my-5 rounded-xl border border-[var(--rbpc-divider)] bg-[var(--rbpc-surface-muted)]/50 p-4">
          <div className="flex items-center gap-2">
            <Sparkles className="h-4 w-4 text-[var(--rbpc-highlight)]" aria-hidden="true" />
            <h4 className="font-serif text-sm font-bold text-[var(--rbpc-ink)]">
              {block.title}
            </h4>
            {block.era && (
              <span className="rounded bg-[var(--rbpc-surface)] px-2 py-0.5 text-[10px] font-semibold text-[var(--rbpc-muted)] border border-[var(--rbpc-divider)]">
                {block.era}
              </span>
            )}
          </div>
          <p className="mt-1.5 text-xs text-[var(--rbpc-muted)] leading-relaxed">
            {block.significance}
          </p>
        </div>
      );
    }

    default:
      return null;
  }
}

StoryChapterViewer.displayName = "StoryChapterViewer";

export default StoryChapterViewer;
