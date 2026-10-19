"use client";

import React, { useState, useId } from "react";
import { MessageSquare, Sparkles, AlertCircle, ArrowRight, ExternalLink, RefreshCw } from "lucide-react";
import { EpistemicBadge } from "./EpistemicBadge";
import { RbpcButton } from "./RbpcButton";
import { RbpcCard, RbpcCardHeader, RbpcCardTitle, RbpcCardContent, RbpcCardFooter } from "./RbpcCard";
import { getRbpcCopy } from "@/lib/rbpc/copy";
import type { EpistemicCertainty } from "@/types/rbpc";

export interface CulturalBridgeCitation {
  citation_number: number;
  source_id: string;
  source_title: string;
  locator?: string;
  cited_statement?: string;
}

export interface CulturalBridgeAnswerPayload {
  status: "supported" | "insufficient_evidence" | "error";
  locale: string;
  answer_markdown: string;
  citations: CulturalBridgeCitation[];
  epistemic_certainty: EpistemicCertainty;
  context_boundary?: string;
  uncertainty_note?: string;
  linked_creator_slug?: string;
  linked_creator_name?: string;
  linked_experience_slug?: string;
  linked_experience_title?: string;
}

export interface CulturalBridgePanelProps {
  entitySlug?: string;
  storySlug?: string;
  entityName?: string;
  locale?: "vi" | "en";
  className?: string;
  onCitationClick?: (citation: CulturalBridgeCitation) => void;
  onExploreExperienceClick?: (experienceSlug: string) => void;
  customEndpoint?: string;
}

const DEFAULT_PROMPTS_VI = [
  "Tại sao địa điểm/câu chuyện này có ý nghĩa lịch sử đặc biệt?",
  "Quy trình chế tác thủ công truyền thống này diễn ra như thế nào?",
  "Có điểm gì khác biệt giữa hiện vật cung đình và sản phẩm làng nghề?",
  "Ý nghĩa biểu tượng văn hóa sâu xa của họa tiết/công trình này là gì?",
];

const DEFAULT_PROMPTS_EN = [
  "Why does this heritage site/story hold special cultural significance?",
  "How is this traditional craftsmanship technique practiced?",
  "What is the difference between royal antiquities and living craft traditions?",
  "What is the deeper cultural symbolism behind this monument/motif?",
];

export function CulturalBridgePanel({
  entitySlug,
  storySlug,
  entityName,
  locale = "vi",
  className = "",
  onCitationClick,
  onExploreExperienceClick,
  customEndpoint = "/api/v1/rbpc/cultural-bridge",
}: CulturalBridgePanelProps) {
  const copy = getRbpcCopy(locale);
  const inputId = useId();
  const [question, setQuestion] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [responsePayload, setResponsePayload] = useState<CulturalBridgeAnswerPayload | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const prompts = locale === "en" ? DEFAULT_PROMPTS_EN : DEFAULT_PROMPTS_VI;

  const handleAsk = async (textToAsk: string) => {
    const q = textToAsk.trim();
    if (!q || isLoading) return;

    setIsLoading(true);
    setErrorMsg(null);

    try {
      const res = await fetch(customEndpoint, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          question: q,
          story_slug: storySlug,
          entity_slug: entitySlug,
          locale,
        }),
      });

      if (!res.ok) {
        throw new Error(`Server returned HTTP ${res.status}`);
      }

      const data = await res.json();
      setResponsePayload({
        status: data.status || "supported",
        locale: data.locale || locale,
        answer_markdown: data.answer_markdown || data.answer || "",
        citations: (data.citations || []).map((c: any, idx: number) => ({
          citation_number: idx + 1,
          source_id: c.source_id,
          source_title: c.source_title || "Nguồn khảo cứu lịch sử",
          locator: c.locator,
          cited_statement: c.cited_statement,
        })),
        epistemic_certainty: data.epistemic_certainty || "verified_source",
        context_boundary: data.context_boundary,
        uncertainty_note: data.uncertainty_note,
        linked_creator_slug: data.linked_creator_slug,
        linked_creator_name: data.linked_creator_name,
        linked_experience_slug: data.linked_experience_slug,
        linked_experience_title: data.linked_experience_title,
      });
    } catch (err: any) {
      // Fail-closed graceful degradation
      setResponsePayload({
        status: "insufficient_evidence",
        locale,
        answer_markdown:
          locale === "en"
            ? "The Cultural Bridge assistant is currently in fail-closed safety mode. You can still read the approved story and consult primary sources."
            : "Trợ lý Cầu nối Văn hóa tạm thời chuyển sang chế độ đối chiếu an toàn. Bạn vẫn có thể tiếp tục tham khảo tóm tắt lịch sử và nguồn tư liệu đã thẩm định.",
        citations: [],
        epistemic_certainty: "insufficient_sources",
        context_boundary:
          locale === "en"
            ? "AI strictly refrains from ungrounded speculation beyond verified database sources."
            : "Hệ thống kiên quyết không phỏng đoán vượt quá nguồn tư liệu đã kiểm chứng.",
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handlePromptClick = (p: string) => {
    setQuestion(p);
    handleAsk(p);
  };

  return (
    <RbpcCard className={`rbpc-cultural-bridge-panel border-line bg-surface ${className}`}>
      <RbpcCardHeader className="border-b border-line/60 pb-4">
        <div className="flex items-center justify-between gap-3">
          <div className="flex items-center gap-2">
            <span className="flex h-8 w-8 items-center justify-center rounded-full bg-primary/10 text-primary">
              <Sparkles className="h-4 w-4" />
            </span>
            <div>
              <RbpcCardTitle className="text-base font-serif font-bold text-ink sm:text-lg">
                {locale === "en" ? "Cultural Bridge AI Guide" : "Trợ lý Cầu nối Văn hóa"}
              </RbpcCardTitle>
              <p className="text-xs text-muted">
                {entityName
                  ? `${locale === "en" ? "Grounded insights for" : "Đối thoại có trích dẫn về"} ${entityName}`
                  : locale === "en"
                  ? "Source-grounded historical & living heritage insights"
                  : "Khảo chứng từ thư tịch triều Nguyễn & truyền thống làng nghề"}
              </p>
            </div>
          </div>
          <span className="rounded border border-primary/20 bg-primary/5 px-2 py-0.5 text-[10px] font-semibold text-primary uppercase tracking-wider">
            Fail-Closed RAG
          </span>
        </div>
      </RbpcCardHeader>

      <RbpcCardContent className="space-y-4 pt-4">
        {/* Quick guided prompt chips (Min 44px Touch Targets) */}
        <div className="space-y-2">
          <span className="text-xs font-semibold text-muted uppercase tracking-wider">
            {locale === "en" ? "Suggested questions:" : "Câu hỏi gợi ý:"}
          </span>
          <div className="flex flex-wrap gap-2">
            {prompts.map((p, idx) => (
              <button
                key={idx}
                type="button"
                onClick={() => handlePromptClick(p)}
                disabled={isLoading}
                className="inline-flex min-h-[44px] items-center rounded-full border border-line bg-rice/40 px-3.5 py-2 text-left text-xs text-ink transition-colors hover:border-primary hover:bg-primary/5 hover:text-primary disabled:opacity-50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--rbpc-focus,#1E675A)] focus-visible:ring-offset-2"
              >
                {p}
              </button>
            ))}
          </div>
        </div>

        {/* Input form */}
        <form
          onSubmit={(e) => {
            e.preventDefault();
            handleAsk(question);
          }}
          className="flex flex-col gap-2 sm:flex-row"
        >
          <div className="relative flex-1">
            <label htmlFor={inputId} className="sr-only">
              {locale === "en" ? "Ask a question about this heritage" : "Hỏi về bối cảnh văn hóa"}
            </label>
            <input
              id={inputId}
              type="text"
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              placeholder={
                locale === "en"
                  ? "Ask about historical context, craft techniques, or symbolism..."
                  : "Hỏi về bối cảnh lịch sử, kỹ thuật làng nghề hoặc ý nghĩa biểu tượng..."
              }
              maxLength={300}
              disabled={isLoading}
              className="w-full min-h-[44px] rounded-md border border-line bg-white px-3 py-2 text-sm text-ink placeholder:text-muted/60 focus:border-primary focus:outline-none focus-visible:ring-2 focus-visible:ring-[var(--rbpc-focus,#1E675A)] focus-visible:ring-offset-2 disabled:opacity-50"
            />
          </div>
          <RbpcButton
            type="submit"
            variant="primary"
            disabled={isLoading || !question.trim()}
            className="shrink-0"
          >
            {isLoading ? (
              <span className="flex items-center gap-1.5">
                <RefreshCw className="h-3.5 w-3.5 animate-spin" />
                {locale === "en" ? "Grounding..." : "Khảo chứng..."}
              </span>
            ) : (
              <span className="flex items-center gap-1.5">
                <MessageSquare className="h-3.5 w-3.5" />
                {locale === "en" ? "Ask AI" : "Đặt câu hỏi"}
              </span>
            )}
          </RbpcButton>
        </form>

        {/* Response Card */}
        {responsePayload && (
          <div className="mt-4 rounded-lg border border-line/80 bg-white p-4 shadow-sm transition-all">
            <div className="mb-2 flex items-center justify-between gap-2">
              <EpistemicBadge
                status={responsePayload.epistemic_certainty}
                locale={locale}
                size="sm"
              />
              {responsePayload.status === "insufficient_evidence" && (
                <span className="flex items-center gap-1 text-[11px] font-semibold text-highlight">
                  <AlertCircle className="h-3 w-3" />
                  {locale === "en" ? "Evidence Gap Refusal" : "Khoảng trống bằng chứng"}
                </span>
              )}
            </div>

            {/* Answer Prose */}
            <div className="prose prose-sm max-w-none text-ink/90 leading-relaxed font-sans">
              <p className="whitespace-pre-line text-sm">{responsePayload.answer_markdown}</p>
            </div>

            {/* Citations List */}
            {responsePayload.citations && responsePayload.citations.length > 0 && (
              <div className="mt-4 border-t border-line/60 pt-3">
                <span className="text-[11px] font-bold text-muted uppercase tracking-wider">
                  {locale === "en" ? "Primary Citations:" : "Nguồn thư tịch kiểm chứng:"}
                </span>
                <ul className="mt-1.5 space-y-1">
                  {responsePayload.citations.map((c, i) => (
                    <li
                      key={i}
                      className="flex items-start gap-1.5 text-xs text-ink/80 hover:text-primary"
                    >
                      <span className="font-semibold text-primary">[{c.citation_number}]</span>
                      <button
                        type="button"
                        onClick={() => onCitationClick && onCitationClick(c)}
                        className="text-left underline decoration-primary/40 underline-offset-2 hover:decoration-primary focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--rbpc-focus,#1E675A)] focus-visible:ring-offset-1 rounded-xs"
                      >
                        <span className="font-medium">{c.source_title}</span>
                        {c.locator && <span className="text-muted"> ({c.locator})</span>}
                      </button>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* Context Boundary Safety Notice */}
            {responsePayload.context_boundary && (
              <p className="mt-3 text-[11px] italic text-muted/80 border-t border-line/40 pt-2">
                * {responsePayload.context_boundary}
              </p>
            )}

            {/* Living Artisan / Workshop Bridge Recommendation */}
            {(responsePayload.linked_experience_slug || responsePayload.linked_creator_slug) && (
              <div className="mt-4 rounded-md border border-primary/20 bg-primary/5 p-3 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                <div>
                  <span className="text-[10px] font-bold uppercase tracking-wider text-primary">
                    {locale === "en" ? "Living Heritage Connection" : "Kết nối Nghệ nhân Đương đại"}
                  </span>
                  <p className="text-xs font-semibold text-ink">
                    {responsePayload.linked_experience_title ||
                      responsePayload.linked_creator_name ||
                      "Trải nghiệm thực tế cùng nghệ nhân"}
                  </p>
                </div>
                <RbpcButton
                  variant="highlight"
                  size="sm"
                  onClick={() =>
                    onExploreExperienceClick &&
                    onExploreExperienceClick(
                      responsePayload.linked_experience_slug || responsePayload.linked_creator_slug || ""
                    )
                  }
                  className="shrink-0 text-xs"
                >
                  <span className="flex items-center gap-1">
                    {locale === "en" ? "Meet the Maker" : "Gặp người làm nghề"}
                    <ArrowRight className="h-3 w-3" />
                  </span>
                </RbpcButton>
              </div>
            )}
          </div>
        )}
      </RbpcCardContent>
    </RbpcCard>
  );
}
