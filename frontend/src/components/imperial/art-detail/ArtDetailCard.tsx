"use client";

import React, { useState } from "react";
import Link from "next/link";
import {
  BookOpen,
  CheckCircle2,
  Copy,
  ExternalLink,
  Eye,
  HelpCircle,
  History,
  Layers,
  Palette,
  Quote,
  Scroll,
  Share2,
  Sparkles,
  XCircle,
} from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  EVIDENCE_STRENGTH_METADATA,
  STORY_TYPE_METADATA,
  type ArtDetailClaimSource,
  type ArtDetailQuestion,
  type ImperialArtDetail,
} from "@/lib/imperial/v51-types";

interface ArtDetailCardProps {
  detail: ImperialArtDetail;
  showDeepLinkButton?: boolean;
  onOpenDeepLink?: () => void;
  className?: string;
}

export function ArtDetailCard({
  detail,
  showDeepLinkButton = true,
  className = "",
}: ArtDetailCardProps) {
  const [copied, setCopied] = useState(false);
  const [selectedAnswers, setSelectedAnswers] = useState<Record<string, number>>({});
  const [showExplanation, setShowExplanation] = useState<Record<string, boolean>>({});

  const storyMeta = STORY_TYPE_METADATA[detail.story_type] || STORY_TYPE_METADATA.documented_event;

  const handleShareLink = () => {
    if (typeof window !== "undefined") {
      const url = `${window.location.origin}/dai-noi/my-thuat/${detail.slug}`;
      navigator.clipboard.writeText(url);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const handleAnswerSelect = (questionId: string, optionIndex: number) => {
    setSelectedAnswers((prev) => ({ ...prev, [questionId]: optionIndex }));
    setShowExplanation((prev) => ({ ...prev, [questionId]: true }));
  };

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Header Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-border/60 pb-4">
        <div className="space-y-1">
          <div className="flex items-center gap-2 flex-wrap">
            <Badge variant="outline" className={`font-medium ${storyMeta.badgeColor}`}>
              <Sparkles className="w-3 h-3 mr-1" />
              {storyMeta.label}
            </Badge>
            {detail.site_name_vi && (
              <Badge variant="secondary" className="text-xs">
                {detail.site_name_vi}
              </Badge>
            )}
            {detail.kind && (
              <Badge variant="outline" className="text-xs capitalize">
                {detail.kind === "carving"
                  ? "Chạm khắc"
                  : detail.kind === "mosaic"
                  ? "Khảm cẩn"
                  : detail.kind === "painting"
                  ? "Bích họa"
                  : "Hoa văn"}
              </Badge>
            )}
          </div>
          <h2 className="text-xl sm:text-2xl font-serif font-bold text-foreground tracking-tight">
            {detail.title}
          </h2>
        </div>

        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={handleShareLink}
            className="text-xs gap-1.5 h-8"
          >
            {copied ? (
              <>
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                Đã sao chép link
              </>
            ) : (
              <>
                <Share2 className="w-3.5 h-3.5" />
                Chia sẻ
              </>
            )}
          </Button>

          {showDeepLinkButton && (
            <Link href={`/dai-noi/my-thuat/${detail.slug}`} target="_blank">
              <Button size="sm" variant="ghost" className="text-xs gap-1 h-8">
                <ExternalLink className="w-3.5 h-3.5" />
                Trang chuyên sâu
              </Button>
            </Link>
          )}
        </div>
      </div>

      {/* SECTION 1: MÔ TẢ QUAN SÁT TRỰC QUAN */}
      <Card className="border-border/60 shadow-sm bg-card/60">
        <CardHeader className="pb-3 pt-4 px-4 sm:px-5">
          <CardTitle className="text-sm font-semibold uppercase tracking-wider text-muted-foreground flex items-center gap-2">
            <Eye className="w-4 h-4 text-primary" />
            1. Quan sát trực quan & Chế tác
          </CardTitle>
        </CardHeader>
        <CardContent className="px-4 sm:px-5 pb-5 space-y-4">
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs bg-muted/40 p-3 rounded-lg border border-border/40">
            {detail.motif && (
              <div>
                <span className="font-semibold text-foreground/80 block">Đồ án họa tiết:</span>
                <span className="text-muted-foreground">{detail.motif}</span>
              </div>
            )}
            {detail.material && (
              <div>
                <span className="font-semibold text-foreground/80 block">Chất liệu:</span>
                <span className="text-muted-foreground">{detail.material}</span>
              </div>
            )}
            {detail.technique && (
              <div>
                <span className="font-semibold text-foreground/80 block">Kỹ thuật thể hiện:</span>
                <span className="text-muted-foreground">{detail.technique}</span>
              </div>
            )}
          </div>

          {detail.description_observation && (
            <p className="text-sm leading-relaxed text-foreground/90 font-sans">
              {detail.description_observation}
            </p>
          )}
        </CardContent>
      </Card>

      {/* SECTION 2: CÂU CHUYỆN / ĐIỂN TÍCH */}
      <Card className="border-border/60 shadow-sm bg-card/60">
        <CardHeader className="pb-3 pt-4 px-4 sm:px-5">
          <CardTitle className="text-sm font-semibold uppercase tracking-wider text-muted-foreground flex items-center gap-2">
            <Scroll className="w-4 h-4 text-amber-600 dark:text-amber-400" />
            2. Điển tích & Bối cảnh lịch sử
          </CardTitle>
        </CardHeader>
        <CardContent className="px-4 sm:px-5 pb-5 space-y-3">
          <div className="flex items-center gap-2">
            <span className="text-xs text-muted-foreground">Phân loại dữ liệu:</span>
            <Badge variant="outline" className={`text-xs ${storyMeta.badgeColor}`}>
              {storyMeta.label}
            </Badge>
          </div>
          <p className="text-xs text-muted-foreground italic border-l-2 border-primary/40 pl-3 py-0.5">
            {storyMeta.description}
          </p>

          {detail.story_body && (
            <div className="text-sm leading-relaxed text-foreground/95 space-y-3 pt-1">
              {detail.story_body.split("\n\n").map((para, idx) => (
                <p key={idx}>{para}</p>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* SECTION 3: Ý NGHĨA BIỂU TƯỢNG */}
      {detail.meaning_body && (
        <Card className="border-border/60 shadow-sm bg-card/60">
          <CardHeader className="pb-3 pt-4 px-4 sm:px-5">
            <CardTitle className="text-sm font-semibold uppercase tracking-wider text-muted-foreground flex items-center gap-2">
              <Sparkles className="w-4 h-4 text-purple-600 dark:text-purple-400" />
              3. Ý nghĩa biểu tượng & Triết lý
            </CardTitle>
          </CardHeader>
          <CardContent className="px-4 sm:px-5 pb-5">
            <p className="text-sm leading-relaxed text-foreground/90">
              {detail.meaning_body}
            </p>
          </CardContent>
        </Card>
      )}

      {/* SECTION 4: GIÁ TRỊ VĂN HÓA - LỊCH SỬ - MỸ THUẬT */}
      {(detail.historical_value_body ||
        detail.cultural_value_body ||
        detail.art_value_body) && (
        <Card className="border-border/60 shadow-sm bg-card/60">
          <CardHeader className="pb-3 pt-4 px-4 sm:px-5">
            <CardTitle className="text-sm font-semibold uppercase tracking-wider text-muted-foreground flex items-center gap-2">
              <Palette className="w-4 h-4 text-emerald-600 dark:text-emerald-400" />
              4. Giá trị Văn hóa — Lịch sử — Mỹ thuật
            </CardTitle>
          </CardHeader>
          <CardContent className="px-4 sm:px-5 pb-5 grid grid-cols-1 md:grid-cols-3 gap-4">
            {detail.historical_value_body && (
              <div className="p-3.5 rounded-lg bg-amber-500/5 border border-amber-500/20 space-y-1.5">
                <div className="flex items-center gap-1.5 font-semibold text-xs text-amber-700 dark:text-amber-400">
                  <History className="w-3.5 h-3.5" />
                  Giá trị Lịch sử
                </div>
                <p className="text-xs text-foreground/80 leading-relaxed">
                  {detail.historical_value_body}
                </p>
              </div>
            )}

            {detail.cultural_value_body && (
              <div className="p-3.5 rounded-lg bg-blue-500/5 border border-blue-500/20 space-y-1.5">
                <div className="flex items-center gap-1.5 font-semibold text-xs text-blue-700 dark:text-blue-400">
                  <BookOpen className="w-3.5 h-3.5" />
                  Giá trị Văn hóa
                </div>
                <p className="text-xs text-foreground/80 leading-relaxed">
                  {detail.cultural_value_body}
                </p>
              </div>
            )}

            {detail.art_value_body && (
              <div className="p-3.5 rounded-lg bg-purple-500/5 border border-purple-500/20 space-y-1.5">
                <div className="flex items-center gap-1.5 font-semibold text-xs text-purple-700 dark:text-purple-400">
                  <Palette className="w-3.5 h-3.5" />
                  Giá trị Mỹ thuật
                </div>
                <p className="text-xs text-foreground/80 leading-relaxed">
                  {detail.art_value_body}
                </p>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* SECTION 5: NGUỒN SỬ LIỆU ĐỐI CHIẾU */}
      {detail.claim_sources && detail.claim_sources.length > 0 && (
        <Card className="border-border/60 shadow-sm bg-card/60">
          <CardHeader className="pb-3 pt-4 px-4 sm:px-5">
            <CardTitle className="text-sm font-semibold uppercase tracking-wider text-muted-foreground flex items-center gap-2">
              <Quote className="w-4 h-4 text-primary" />
              5. Nguồn sử liệu & Luận cứ đối chiếu
            </CardTitle>
          </CardHeader>
          <CardContent className="px-4 sm:px-5 pb-5 space-y-3">
            {detail.claim_sources.map((src, sIdx) => {
              const strengthMeta =
                EVIDENCE_STRENGTH_METADATA[src.evidence_strength] ||
                EVIDENCE_STRENGTH_METADATA.verified;

              return (
                <div
                  key={src.id || sIdx}
                  className="rounded-lg border border-border/50 bg-background/50 p-3.5 space-y-2 text-xs"
                >
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <span className="font-semibold text-foreground/90 font-serif">
                      {src.source_title}
                    </span>
                    <Badge variant="outline" className={`text-[11px] ${strengthMeta.badgeColor}`}>
                      {strengthMeta.label}
                    </Badge>
                  </div>

                  {src.source_locator && (
                    <div className="text-muted-foreground text-[11px]">
                      Vị trí tra cứu: <span className="font-medium text-foreground/80">{src.source_locator}</span>
                    </div>
                  )}

                  <p className="text-foreground/90 leading-relaxed italic border-l-2 border-primary/30 pl-2.5">
                    &ldquo;{src.claim_text}&rdquo;
                  </p>

                  {src.citation_quote && (
                    <div className="pt-1 text-[11px] text-muted-foreground">
                      <span className="font-medium text-foreground/70">Nguyên văn / Dịch nghĩa:</span> {src.citation_quote}
                    </div>
                  )}
                </div>
              );
            })}
          </CardContent>
        </Card>
      )}

      {/* SECTION 6: 1–3 CÂU HỎI CỦNG CỐ */}
      {detail.questions && detail.questions.length > 0 && (
        <Card className="border-border/60 shadow-sm bg-card/60">
          <CardHeader className="pb-3 pt-4 px-4 sm:px-5">
            <CardTitle className="text-sm font-semibold uppercase tracking-wider text-muted-foreground flex items-center gap-2">
              <HelpCircle className="w-4 h-4 text-emerald-600 dark:text-emerald-400" />
              6. Câu hỏi củng cố hiểu biết ({detail.questions.length})
            </CardTitle>
          </CardHeader>
          <CardContent className="px-4 sm:px-5 pb-5 space-y-5">
            {detail.questions.map((q, qIdx) => {
              const selectedIdx = selectedAnswers[q.id];
              const isAnswered = selectedIdx !== undefined;
              const correctIdx = parseInt(q.answer_key, 10);
              const isCorrect = isAnswered && selectedIdx === correctIdx;

              return (
                <div
                  key={q.id || qIdx}
                  className="p-4 rounded-lg border border-border/60 bg-background/60 space-y-3"
                >
                  <div className="font-medium text-sm text-foreground flex items-start gap-2">
                    <span className="text-primary font-bold">Câu {qIdx + 1}:</span>
                    <span>{q.prompt}</span>
                  </div>

                  {/* Options */}
                  <div className="space-y-2 pt-1">
                    {q.options.map((opt, optIdx) => {
                      const isOptionSelected = selectedIdx === optIdx;
                      const isOptionCorrect = optIdx === correctIdx;

                      let btnStyle =
                        "justify-start text-left font-normal text-xs h-auto py-2.5 px-3 border-border/60 w-full";

                      if (isAnswered) {
                        if (isOptionCorrect) {
                          btnStyle =
                            "justify-start text-left font-medium text-xs h-auto py-2.5 px-3 border-emerald-500 bg-emerald-500/10 text-emerald-800 dark:text-emerald-300 w-full";
                        } else if (isOptionSelected) {
                          btnStyle =
                            "justify-start text-left font-medium text-xs h-auto py-2.5 px-3 border-rose-500 bg-rose-500/10 text-rose-800 dark:text-rose-300 w-full";
                        }
                      }

                      return (
                        <Button
                          key={optIdx}
                          variant="outline"
                          size="sm"
                          disabled={isAnswered}
                          onClick={() => handleAnswerSelect(q.id, optIdx)}
                          className={btnStyle}
                        >
                          <span className="inline-block w-5 font-semibold text-muted-foreground">
                            {String.fromCharCode(65 + optIdx)}.
                          </span>
                          <span className="flex-1">{opt}</span>
                          {isAnswered && isOptionCorrect && (
                            <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0 ml-2" />
                          )}
                          {isAnswered && isOptionSelected && !isOptionCorrect && (
                            <XCircle className="w-4 h-4 text-rose-600 shrink-0 ml-2" />
                          )}
                        </Button>
                      );
                    })}
                  </div>

                  {/* Immediate Explanation Feedback */}
                  {showExplanation[q.id] && (
                    <div
                      className={`p-3 rounded text-xs mt-2 space-y-1 ${
                        isCorrect
                          ? "bg-emerald-500/10 border border-emerald-500/30 text-emerald-900 dark:text-emerald-200"
                          : "bg-rose-500/10 border border-rose-500/30 text-rose-900 dark:text-rose-200"
                      }`}
                    >
                      <div className="font-semibold flex items-center gap-1.5">
                        {isCorrect ? (
                          <>
                            <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
                            Chính xác!
                          </>
                        ) : (
                          <>
                            <XCircle className="w-4 h-4 text-rose-600 shrink-0" />
                            Chưa chính xác! Đáp án đúng là {String.fromCharCode(65 + correctIdx)}.
                          </>
                        )}
                      </div>
                      {q.explanation && (
                        <p className="text-foreground/80 leading-relaxed pt-0.5">
                          {q.explanation}
                        </p>
                      )}
                    </div>
                  )}
                </div>
              );
            })}
          </CardContent>
        </Card>
      )}
    </div>
  );
}
