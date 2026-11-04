"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useMemo, useState } from "react";
import {
  AlertCircle,
  ArrowRight,
  BookOpen,
  Box,
  Clock,
  Feather,
  FlaskConical,
  Landmark,
  Lightbulb,
  Map,
  MessageCircleQuestion,
  ScrollText,
  Star,
} from "lucide-react";

import { getHistoryStory } from "@/lib/api";
import { urnSlugFromReliefSlug } from "@/lib/history";
import Skeleton from "@/components/Skeleton";
import VerificationNote from "@/components/history/VerificationNote";
import EpistemicLabel from "@/components/history/EpistemicLabel";
import { Badge } from "@/components/ui/badge";
import {
  StoryPassageEpistemicBadge,
  EmptyEvidenceWarning,
  ClaimFootnoteTag,
  StoryEvidenceFootnotes,
  StoryBilingualPassage,
} from "@/components/history/StoryCitationRenderer";
import { CitationDrawer } from "@/components/rbpc/CitationDrawer";
import { parseStoryFootnotes } from "@/lib/history";

function BlockLink({
  href,
  children,
  className,
}) {
  if (!href) {
    return <span className={className}>{children}</span>;
  }
  return (
    <Link
      href={href}
      className={`inline-flex items-center gap-1.5 font-medium text-primary hover:underline ${className || ""}`}
    >
      {children}
      <ArrowRight className="h-3.5 w-3.5" aria-hidden="true" />
    </Link>
  );
}

function TextBlock({ block, citationMap, onOpenDrawer }) {
  const blockCitations = Array.isArray(block.citations) ? block.citations : [];
  const cids = Array.isArray(block.source_claim_ids) ? block.source_claim_ids : [];
  const hasSource = block.has_source !== false && (
    Boolean(block.source_id) ||
    blockCitations.some((c) => Boolean(c.source_id || c.source_title)) ||
    cids.length > 0
  );
  const showEmptyWarning =
    block.has_source === false ||
    block.warning === "UNVERIFIED_EMPTY_EVIDENCE" ||
    (block.epistemic_certainty === "su_lieu_xac_thuc" && !hasSource);

  // Parse markdown-style footnotes like [^1] or [^dntl-01]
  const parsedVi = parseStoryFootnotes(block.body || block.body_vi, blockCitations);
  const parsedEn = parseStoryFootnotes(block.body_en, blockCitations);

  const renderParsed = (parsed) => {
    if (!parsed || parsed.segments.length === 0) return null;
    return parsed.segments.map((seg, sIdx) => {
      if (seg.footnote) {
        const fn = seg.footnote;
        const matched = fn.citation;
        const idx = citationMap?.get(matched?.id) || citationMap?.get(matched?.source_id) || fn.index;
        return (
          <ClaimFootnoteTag
            key={sIdx}
            index={idx}
            citationId={matched?.id || fn.citationId}
            sourceTitle={matched?.source_title}
            hasSource={matched?.has_source !== false && Boolean(matched?.source_id || matched?.source_title || fn.citationId)}
            onOpenDrawer={onOpenDrawer}
          />
        );
      }
      return <span key={sIdx}>{seg.text}</span>;
    });
  };

  return (
    <div className="max-w-3xl space-y-3">
      <div className="flex flex-wrap items-center gap-2">
        {block.epistemic_certainty ? (
          <StoryPassageEpistemicBadge
            certainty={block.epistemic_certainty}
            hasSource={hasSource}
            verificationStatus={block.verification_status}
            isDisputed={block.verification_status === "disputed"}
          />
        ) : null}
        {showEmptyWarning ? (
          <span className="text-[11px] font-semibold text-amber-700 dark:text-amber-400">
            (Chưa xác thực nguồn)
          </span>
        ) : null}
      </div>

      {block.title || block.title_vi ? (
        <h2 className="font-display text-2xl font-bold tracking-tight text-foreground">
          {block.title || block.title_vi}
        </h2>
      ) : null}
      {block.title_en ? (
        <p className="font-serif text-lg italic text-muted-foreground">
          {block.title_en}
        </p>
      ) : null}

      {(block.body || block.body_vi) ? (
        <p className="mt-3 text-base leading-8 text-foreground/85">
          {parsedVi.segments.length > 0 ? renderParsed(parsedVi) : (block.body || block.body_vi)}
          {/* Append any extra unreferenced citations */}
          {blockCitations
            .filter((c) => !parsedVi.referencedCitations.some((rc) => rc.id === c.id))
            .map((c, i) => {
              const idx = citationMap?.get(c.id) || citationMap?.get(c.source_id) || i + 1;
              return (
                <ClaimFootnoteTag
                  key={c.id || i}
                  index={idx}
                  citationId={c.id}
                  sourceTitle={c.source_title}
                  hasSource={c.has_source !== false}
                  onOpenDrawer={onOpenDrawer}
                />
              );
            })}
          {cids.map((cid, i) => {
            const idx = citationMap?.get(cid) || blockCitations.length + i + 1;
            return (
              <ClaimFootnoteTag
                key={cid}
                index={idx}
                sourceTitle="Khẳng định lịch sử"
                hasSource={hasSource}
                onOpenDrawer={onOpenDrawer}
              />
            );
          })}
        </p>
      ) : null}

      {block.body_en ? (
        <p className="mt-2 text-sm italic leading-7 text-muted-foreground border-t border-border/40 pt-2">
          {parsedEn.segments.length > 0 ? renderParsed(parsedEn) : block.body_en}
        </p>
      ) : null}

      {showEmptyWarning ? (
        <EmptyEvidenceWarning message="Đoạn trích này chưa gắn kèm nguồn thư tịch sử liệu đối chiếu — không thể coi là sử liệu xác thực." />
      ) : null}
    </div>
  );
}

function ImageBlock({ block }) {
  if (!block.image_url) return null;
  return (
    <figure className="max-w-3xl">
      <img
        src={block.image_url}
        alt={block.caption || block.title || ""}
        className="w-full rounded-lg border border-border/70 bg-card/45 object-cover"
      />
      {block.caption ? (
        <figcaption className="mt-2 text-sm text-muted-foreground">
          {block.caption}
        </figcaption>
      ) : null}
    </figure>
  );
}

function QuoteBlock({ block, citationMap, onOpenDrawer }) {
  const blockCitations = Array.isArray(block.citations) ? block.citations : [];
  const hasSource = block.has_source !== false && (
    Boolean(block.source_id) ||
    blockCitations.some((c) => Boolean(c.source_id || c.source_title))
  );
  const showEmptyWarning =
    block.has_source === false ||
    block.warning === "UNVERIFIED_EMPTY_EVIDENCE" ||
    (block.epistemic_certainty === "su_lieu_xac_thuc" && !hasSource);

  const parsedVi = parseStoryFootnotes(block.quote || block.quote_vi, blockCitations);
  const parsedEn = parseStoryFootnotes(block.quote_en, blockCitations);

  const renderParsed = (parsed) => {
    if (!parsed || parsed.segments.length === 0) return null;
    return parsed.segments.map((seg, sIdx) => {
      if (seg.footnote) {
        const fn = seg.footnote;
        const matched = fn.citation;
        const idx = citationMap?.get(matched?.id) || citationMap?.get(matched?.source_id) || fn.index;
        return (
          <ClaimFootnoteTag
            key={sIdx}
            index={idx}
            citationId={matched?.id || fn.citationId}
            sourceTitle={matched?.source_title}
            hasSource={matched?.has_source !== false && Boolean(matched?.source_id || matched?.source_title || fn.citationId)}
            onOpenDrawer={onOpenDrawer}
          />
        );
      }
      return <span key={sIdx}>{seg.text}</span>;
    });
  };

  return (
    <div className="max-w-3xl space-y-2">
      <div className="flex flex-wrap items-center gap-2">
        {block.epistemic_certainty ? (
          <StoryPassageEpistemicBadge
            certainty={block.epistemic_certainty}
            hasSource={hasSource}
            verificationStatus={block.verification_status}
            isDisputed={block.verification_status === "disputed"}
          />
        ) : null}
        {showEmptyWarning ? (
          <span className="text-[11px] font-semibold text-amber-700 dark:text-amber-400">
            (Chưa xác thực nguồn)
          </span>
        ) : null}
      </div>

      <blockquote className="border-l-2 border-primary/40 pl-5">
        {(block.quote || block.quote_vi) ? (
          <p className="font-display text-xl italic leading-8 text-foreground/90">
            “{parsedVi.segments.length > 0 ? renderParsed(parsedVi) : (block.quote || block.quote_vi)}”
            {blockCitations
              .filter((c) => !parsedVi.referencedCitations.some((rc) => rc.id === c.id))
              .map((c, i) => {
                const idx = citationMap?.get(c.id) || citationMap?.get(c.source_id) || i + 1;
                return (
                  <ClaimFootnoteTag
                    key={c.id || i}
                    index={idx}
                    citationId={c.id}
                    sourceTitle={c.source_title}
                    hasSource={c.has_source !== false}
                    onOpenDrawer={onOpenDrawer}
                  />
                );
              })}
          </p>
        ) : null}
        {block.quote_en ? (
          <p className="mt-2 font-serif text-sm italic leading-7 text-muted-foreground border-t border-border/30 pt-2">
            “{parsedEn.segments.length > 0 ? renderParsed(parsedEn) : block.quote_en}”
          </p>
        ) : null}
        {block.attribution ? (
          <footer className="mt-2 text-sm text-muted-foreground">
            — {block.attribution}
          </footer>
        ) : null}
      </blockquote>

      {showEmptyWarning ? (
        <EmptyEvidenceWarning message="Trích dẫn này chưa có nguồn thư tịch gốc bảo chứng." />
      ) : null}
    </div>
  );
}

function ReliefFocusBlock({ block }) {
  const reliefSlug = block.entity_slug || (block.entity_id ? String(block.entity_id) : "");
  const urnSlug = urnSlugFromReliefSlug(reliefSlug);
  const href =
    reliefSlug && urnSlug
      ? `/atlas/${urnSlug}/${reliefSlug}`
      : "/atlas";
  return (
    <div className="rounded-lg border border-primary/20 bg-primary/5 p-6">
      <div className="flex items-start gap-3">
        <Box className="mt-0.5 h-5 w-5 shrink-0 text-primary" aria-hidden="true" />
        <div>
          <h3 className="font-display text-lg font-semibold text-foreground">
            {block.title || "Điểm nhấn phù điêu"}
          </h3>
          {block.body ? (
            <p className="mt-2 text-sm leading-7 text-muted-foreground">{block.body}</p>
          ) : null}
          <div className="mt-3">
            <BlockLink href={href}>
              Xem phù điêu trong Atlas
            </BlockLink>
          </div>
        </div>
      </div>
    </div>
  );
}

function Urn3dFocusBlock({ block }) {
  const urnSlug =
    block.urn_slug || urnSlugFromReliefSlug(block.entity_slug || "");
  const href = urnSlug
    ? `/urns/${urnSlug}${block.relief ? `?relief=${encodeURIComponent(block.relief)}` : ""}`
    : "/cuu-dinh";
  return (
    <div className="rounded-lg border border-primary/20 bg-primary/5 p-6">
      <div className="flex items-start gap-3">
        <Landmark className="mt-0.5 h-5 w-5 shrink-0 text-primary" aria-hidden="true" />
        <div>
          <h3 className="font-display text-lg font-semibold text-foreground">
            {block.title || "Khám phá trong 3D"}
          </h3>
          {block.body ? (
            <p className="mt-2 text-sm leading-7 text-muted-foreground">{block.body}</p>
          ) : null}
          <div className="mt-3">
            <BlockLink href={href}>
              Mở trình xem 3D
            </BlockLink>
          </div>
        </div>
      </div>
    </div>
  );
}

function MapFocusBlock({ block }) {
  return (
    <div className="rounded-lg border border-border/70 bg-secondary/40 p-6">
      <div className="flex items-start gap-3">
        <Map className="mt-0.5 h-5 w-5 shrink-0 text-primary" aria-hidden="true" />
        <div>
          <h3 className="font-display text-lg font-semibold text-foreground">
            {block.title || "Trên bản đồ"}
          </h3>
          {block.body ? (
            <p className="mt-2 text-sm leading-7 text-muted-foreground">{block.body}</p>
          ) : null}
          <div className="mt-3">
            <BlockLink href="/map">Mở bản đồ di sản</BlockLink>
          </div>
        </div>
      </div>
    </div>
  );
}

function TimelineFocusBlock({ block }) {
  return (
    <div className="rounded-lg border border-border/70 bg-secondary/40 p-6">
      <div className="flex items-start gap-3">
        <Clock className="mt-0.5 h-5 w-5 shrink-0 text-primary" aria-hidden="true" />
        <div>
          <h3 className="font-display text-lg font-semibold text-foreground">
            {block.title || "Dòng thời gian"}
          </h3>
          {block.body ? (
            <p className="mt-2 text-sm leading-7 text-muted-foreground">{block.body}</p>
          ) : null}
          <div className="mt-3">
            <BlockLink href="/timeline">Xem trên dòng thời gian</BlockLink>
          </div>
        </div>
      </div>
    </div>
  );
}

function SourceExcerptBlock({ block, citationMap, onOpenDrawer }) {
  const href = block.source_id ? `/sources/${block.source_id}` : "/sources";
  const citeIdx = block.source_id ? citationMap?.get(block.source_id) : null;
  return (
    <div className="rounded-lg border border-border/70 bg-card/60 p-6 max-w-3xl">
      <div className="flex items-start gap-3">
        <ScrollText className="mt-0.5 h-5 w-5 shrink-0 text-primary" aria-hidden="true" />
        <div className="w-full">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <div className="flex items-center gap-2">
              {block.title ? (
                <h3 className="font-display text-lg font-semibold text-foreground">
                  {block.title}
                </h3>
              ) : null}
              {citeIdx ? (
                <ClaimFootnoteTag
                  index={citeIdx}
                  citationId={block.source_id}
                  sourceTitle={block.title}
                  hasSource={Boolean(block.source_id)}
                  onOpenDrawer={onOpenDrawer}
                />
              ) : null}
            </div>
            <StoryPassageEpistemicBadge
              certainty={block.source_id ? "su_lieu_xac_thuc" : "dang_khao_cuu"}
              hasSource={Boolean(block.source_id)}
              verificationStatus={block.source_id ? "expert_verified" : "unreviewed"}
            />
          </div>
          {block.quote ? (
            <p className="mt-2 border-l-2 border-primary/30 pl-3 text-sm italic leading-7 text-foreground/85">
              “{block.quote}”
            </p>
          ) : block.body ? (
            <p className="mt-2 text-sm leading-7 text-muted-foreground">{block.body}</p>
          ) : null}
          {!block.source_id && (
            <div className="mt-3">
              <EmptyEvidenceWarning message="Trích đoạn này chưa gắn mã định danh nguồn thư tịch." />
            </div>
          )}
          <div className="mt-3 flex items-center gap-3">
            <BlockLink href={href}>
              Xem nguồn sử liệu
            </BlockLink>
            {onOpenDrawer && (
              <button
                type="button"
                onClick={onOpenDrawer}
                className="text-xs font-semibold text-primary hover:underline cursor-pointer"
              >
                Mở ngăn kéo thư tịch
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

function CompareBlock({ block }) {
  return (
    <div className="rounded-lg border border-border/70 bg-secondary/40 p-6">
      <div className="flex items-start gap-3">
        <FlaskConical className="mt-0.5 h-5 w-5 shrink-0 text-primary" aria-hidden="true" />
        <div>
          <h3 className="font-display text-lg font-semibold text-foreground">
            {block.title || "So sánh"}
          </h3>
          {block.body ? (
            <p className="mt-2 text-sm leading-7 text-muted-foreground">{block.body}</p>
          ) : null}
          <div className="mt-3">
            <BlockLink href="/explore/connections">
              Khám phá các kết nối
            </BlockLink>
          </div>
        </div>
      </div>
    </div>
  );
}

function ReflectionQuestionBlock({ block }) {
  return (
    <div className="rounded-lg border border-warning/30 bg-warning/10 p-6">
      <div className="flex items-start gap-3">
        <MessageCircleQuestion
          className="mt-0.5 h-5 w-5 shrink-0 text-warning"
          aria-hidden="true"
        />
        <div>
          <h3 className="font-display text-lg font-semibold text-foreground">
            {block.title || "Câu hỏi suy ngẫm"}
          </h3>
          {block.question ? (
            <p className="mt-2 text-base leading-7 text-foreground/85">{block.question}</p>
          ) : null}
        </div>
      </div>
    </div>
  );
}

function QuizBlock({ block }) {
  return (
    <div className="rounded-lg border border-success/30 bg-success/10 p-6">
      <div className="flex items-start gap-3">
        <Lightbulb className="mt-0.5 h-5 w-5 shrink-0 text-success" aria-hidden="true" />
        <div>
          <h3 className="font-display text-lg font-semibold text-foreground">
            {block.title || "Thử thách nhỏ"}
          </h3>
          {block.body ? (
            <p className="mt-2 text-sm leading-7 text-muted-foreground">{block.body}</p>
          ) : null}
          <div className="mt-3">
            <BlockLink href="/practice">Luyện tập cùng câu hỏi</BlockLink>
          </div>
        </div>
      </div>
    </div>
  );
}

function CalloutBlock({ block, citationMap, onOpenDrawer }) {
  const blockCitations = Array.isArray(block.citations) ? block.citations : [];
  const hasSource = block.has_source !== false && (
    Boolean(block.source_id) ||
    blockCitations.some((c) => Boolean(c.source_id || c.source_title))
  );
  const showEmptyWarning =
    block.has_source === false ||
    block.warning === "UNVERIFIED_EMPTY_EVIDENCE" ||
    (block.epistemic_certainty === "su_lieu_xac_thuc" && !hasSource);

  const parsedVi = parseStoryFootnotes(block.body || block.body_vi, blockCitations);
  const parsedEn = parseStoryFootnotes(block.body_en, blockCitations);

  const renderParsed = (parsed) => {
    if (!parsed || parsed.segments.length === 0) return null;
    return parsed.segments.map((seg, sIdx) => {
      if (seg.footnote) {
        const fn = seg.footnote;
        const matched = fn.citation;
        const idx = citationMap?.get(matched?.id) || citationMap?.get(matched?.source_id) || fn.index;
        return (
          <ClaimFootnoteTag
            key={sIdx}
            index={idx}
            citationId={matched?.id || fn.citationId}
            sourceTitle={matched?.source_title}
            hasSource={matched?.has_source !== false && Boolean(matched?.source_id || matched?.source_title || fn.citationId)}
            onOpenDrawer={onOpenDrawer}
          />
        );
      }
      return <span key={sIdx}>{seg.text}</span>;
    });
  };

  return (
    <aside className="max-w-3xl space-y-2">
      <div className="flex items-start gap-3 rounded-lg border border-border/70 bg-secondary/50 px-4 py-4">
        <AlertCircle className="mt-0.5 h-4 w-4 shrink-0 text-primary" aria-hidden="true" />
        <div className="w-full">
          <div className="flex flex-wrap items-center justify-between gap-2">
            {block.title || block.title_vi ? (
              <h3 className="font-display text-sm font-semibold text-foreground">
                {block.title || block.title_vi}
              </h3>
            ) : <span />}
            {block.epistemic_certainty ? (
              <StoryPassageEpistemicBadge
                certainty={block.epistemic_certainty}
                hasSource={hasSource}
                verificationStatus={block.verification_status}
                isDisputed={block.verification_status === "disputed"}
              />
            ) : null}
          </div>
          {(block.body || block.body_vi) ? (
            <p className="text-sm leading-7 text-muted-foreground mt-1">
              {parsedVi.segments.length > 0 ? renderParsed(parsedVi) : (block.body || block.body_vi)}
              {blockCitations
                .filter((c) => !parsedVi.referencedCitations.some((rc) => rc.id === c.id))
                .map((c, i) => {
                  const idx = citationMap?.get(c.id) || citationMap?.get(c.source_id) || i + 1;
                  return (
                    <ClaimFootnoteTag
                      key={c.id || i}
                      index={idx}
                      citationId={c.id}
                      sourceTitle={c.source_title}
                      hasSource={c.has_source !== false}
                      onOpenDrawer={onOpenDrawer}
                    />
                  );
                })}
            </p>
          ) : null}
          {block.body_en ? (
            <p className="text-xs italic leading-6 text-muted-foreground/80 mt-1 border-t border-border/40 pt-1">
              {parsedEn.segments.length > 0 ? renderParsed(parsedEn) : block.body_en}
            </p>
          ) : null}
        </div>
      </div>
      {showEmptyWarning ? (
        <EmptyEvidenceWarning message="Lưu ý này chưa có bằng chứng sử liệu đối chiếu." />
      ) : null}
    </aside>
  );
}

function StoryBlockRenderer({ block, citationMap, onOpenDrawer }) {
  if (!block || typeof block !== "object") return null;
  switch (block.type) {
    case "text":
      return <TextBlock block={block} citationMap={citationMap} onOpenDrawer={onOpenDrawer} />;
    case "image":
      return <ImageBlock block={block} />;
    case "quote":
      return <QuoteBlock block={block} citationMap={citationMap} onOpenDrawer={onOpenDrawer} />;
    case "relief_focus":
      return <ReliefFocusBlock block={block} />;
    case "urn_3d_focus":
      return <Urn3dFocusBlock block={block} />;
    case "map_focus":
      return <MapFocusBlock block={block} />;
    case "timeline_focus":
      return <TimelineFocusBlock block={block} />;
    case "source_excerpt":
      return <SourceExcerptBlock block={block} citationMap={citationMap} onOpenDrawer={onOpenDrawer} />;
    case "compare":
      return <CompareBlock block={block} />;
    case "reflection_question":
      return <ReflectionQuestionBlock block={block} />;
    case "quiz":
      return <QuizBlock block={block} />;
    case "callout":
      return <CalloutBlock block={block} citationMap={citationMap} onOpenDrawer={onOpenDrawer} />;
    default:
      return null;
  }
}

export default function StoryDetailPage() {
  const params = useParams();
  const slug = useMemo(
    () => (typeof params?.slug === "string" ? params.slug : ""),
    [params],
  );

  const [story, setStory] = useState(null);
  const [notFound, setNotFound] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [isDrawerOpen, setIsDrawerOpen] = useState(false);

  useEffect(() => {
    if (!slug) return;
    document.title = `${story?.title_vi || "Truyện sử"} — Lưu Niên Sử Kí`;
  }, [slug, story]);

  useEffect(() => {
    if (!slug) return;
    let cancelled = false;
    async function load() {
      setLoading(true);
      setError(null);
      setNotFound(false);
      try {
        let res;
        try {
          res = await getHistoryStory(slug);
        } catch (err) {
          if (cancelled) return;
          if (
            err?.status === 404 ||
            (err instanceof Error && /404|not found/i.test(err.message))
          ) {
            setNotFound(true);
            return;
          }
          throw err;
        }
        if (cancelled || !res) return;
        setStory(res);
      } catch (err) {
        if (!cancelled)
          setError(err instanceof Error ? err.message : String(err));
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    load();
    return () => {
      cancelled = true;
    };
  }, [slug]);

  if (!slug) return null;

  if (loading) {
    return (
      <main className="site-shell" aria-busy="true">
        <div className="heritage-hero p-6 md:p-9">
          <Skeleton className="h-8 w-1/2" />
          <Skeleton className="mt-3 h-4 w-1/3" />
        </div>
        <div className="mt-6 space-y-4">
          {[...Array(5)].map((_, i) => (
            <Skeleton key={i} className="h-12 w-full" />
          ))}
        </div>
      </main>
    );
  }

  if (notFound || !story) {
    return (
      <main className="site-shell">
        <section className="heritage-surface mx-auto max-w-xl p-8 text-center">
          <h1 className="font-display text-2xl font-bold text-foreground">
            Không tìm thấy truyện này
          </h1>
          <p className="mt-3 text-sm leading-6 text-muted-foreground">
            Không có truyện nào khớp với “{slug}” trên máy chủ lịch sử.
          </p>
          <Link
            href="/stories"
            className="mt-6 inline-flex items-center gap-2 rounded-lg bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground"
          >
            Về danh sách truyện
            <ArrowRight className="h-4 w-4" aria-hidden="true" />
          </Link>
        </section>
      </main>
    );
  }

  const blocks = Array.isArray(story.blocks) ? story.blocks : [];
  const citations = Array.isArray(story.citations) ? story.citations : [];

  // Build lookup index: ID, source_id, claim_id -> 1-based citation index
  const citationMap = useMemo(() => {
    const map = new Map();
    citations.forEach((c, idx) => {
      const num = idx + 1;
      if (c.id) {
        map.set(String(c.id), num);
        map.set(`cite-${c.id}`, num);
      }
      if (c.source_id) map.set(String(c.source_id), num);
      if (c.claim_id) map.set(String(c.claim_id), num);
      if (c.footnote_key) map.set(String(c.footnote_key), num);
    });
    return map;
  }, [citations]);

  // Convert story citations to CitationDrawer source format
  const drawerSources = useMemo(() => {
    return citations.map((c, idx) => ({
      id: c.id || `cite-${idx + 1}`,
      title: c.source_title,
      source_title: c.source_title,
      author: c.author,
      source_author: c.author,
      year: c.publication_year,
      publication_year: c.publication_year,
      locator: c.locator,
      cited_page: c.locator,
      url: c.url,
      source_url: c.url,
      statement: c.claim_statement || c.quote,
      evidence_status: c.verification_status || (c.has_source ? "verified" : "needs_review"),
      reuse_rights: c.rights_status || "fair_use_educational",
    }));
  }, [citations]);

  return (
    <main className="site-shell">
      <section className="heritage-hero p-6 md:p-9">
        <div className="relative max-w-4xl">
          <div className="flex flex-wrap items-center gap-2">
            <span className="heritage-chip">
              <Feather className="h-4 w-4" aria-hidden="true" />
              Truyện sử
            </span>
            {story.featured ? (
              <Badge variant="secondary">
                <Star className="mr-1 h-3.5 w-3.5 fill-warning text-warning" aria-hidden="true" />
                Nổi bật
              </Badge>
            ) : null}
            <EpistemicLabel
              info={{
                label:
                  story.publication_status === "unreviewed"
                    ? "Chưa kiểm chứng"
                    : "Đã kiểm chứng",
                tone:
                  story.publication_status === "unreviewed"
                    ? "unreviewed"
                    : "documented",
              }}
            />
          </div>
          <h1 className="mt-5 font-display text-3xl font-bold tracking-tight text-foreground md:text-5xl">
            {story.title_vi}
          </h1>
          {story.title_en ? (
            <p className="mt-2 text-lg italic text-muted-foreground">
              {story.title_en}
            </p>
          ) : null}
          {story.summary_vi ? (
            <p className="mt-4 max-w-2xl text-base leading-7 text-muted-foreground md:text-lg">
              {story.summary_vi}
            </p>
          ) : null}
          {story.hero_image_url ? (
            <img
              src={story.hero_image_url}
              alt=""
              className="mt-6 max-h-80 w-full rounded-lg border border-border/70 bg-card/45 object-cover"
            />
          ) : null}
        </div>
      </section>

      <div className="mt-5">
        <VerificationNote />
      </div>

      {error ? (
        <div
          role="alert"
          className="mt-5 rounded-lg border border-destructive/30 bg-destructive/10 p-4 text-sm text-destructive"
        >
          Có lỗi khi tải dữ liệu: {error}
        </div>
      ) : null}

      <article className="mt-10 space-y-10">
        {blocks.length > 0 ? (
          blocks.map((block, i) => (
            <StoryBlockRenderer
              key={i}
              block={block}
              citationMap={citationMap}
              onOpenDrawer={() => setIsDrawerOpen(true)}
            />
          ))
        ) : (
          <div className="flex max-w-3xl items-center gap-3 rounded-lg border border-dashed border-border/70 bg-card/45 px-6 py-10 text-sm text-muted-foreground">
            <BookOpen className="h-5 w-5 shrink-0" aria-hidden="true" />
            Bài viết đang được biên tập — các khối nội dung sẽ xuất hiện tại đây.
          </div>
        )}
      </article>

      {/* Bibliographic Footnotes Section */}
      {citations.length > 0 && (
        <div className="max-w-3xl">
          <StoryEvidenceFootnotes
            citations={citations}
            onOpenDrawer={() => setIsDrawerOpen(true)}
          />
        </div>
      )}

      {/* Slide-out Source Drawer */}
      <CitationDrawer
        isOpen={isDrawerOpen}
        onClose={() => setIsDrawerOpen(false)}
        sources={drawerSources}
        entityName={story.title_vi}
        title="Thư mục Thư tịch & Dẫn chứng Lịch sử"
        locale="vi"
      />
    </main>
  );
}
