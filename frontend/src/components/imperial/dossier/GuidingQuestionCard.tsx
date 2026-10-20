"use client";

import { HelpCircle, Sparkles, CheckCircle, BookOpen } from "lucide-react";
import { Badge } from "@/components/ui/badge";

interface GuidingQuestionCardProps {
  question: string;
  historicalSummary?: string | null;
  learningLevel?: string;
  monumentName: string;
}

export default function GuidingQuestionCard({
  question,
  historicalSummary,
  learningLevel = "L2_LEARNING_READY",
  monumentName,
}: GuidingQuestionCardProps) {
  const isL2 =
    learningLevel === "L2_LEARNING_READY" || learningLevel === "L2_ANALYZED";

  return (
    <section
      aria-labelledby="guiding-question-title"
      className="relative rounded-2xl border-2 border-primary/30 bg-gradient-to-br from-primary/5 via-background to-secondary/30 p-6 md:p-8 shadow-sm"
    >
      <div className="flex flex-col gap-4">
        {/* Header label */}
        <div className="flex flex-wrap items-center justify-between gap-2 border-b border-border/60 pb-3">
          <div className="flex items-center gap-2 text-primary font-semibold text-xs tracking-wider uppercase">
            <Sparkles className="h-4 w-4 shrink-0" />
            <span id="guiding-question-title">Câu hỏi dẫn dắt nghiên cứu sư phạm</span>
          </div>

          <div className="flex items-center gap-2">
            {isL2 ? (
              <Badge
                variant="default"
                className="bg-emerald-600 hover:bg-emerald-700 text-white gap-1 text-[11px] font-semibold"
              >
                <CheckCircle className="h-3 w-3" />
                L2_LEARNING_READY
              </Badge>
            ) : (
              <Badge variant="outline" className="text-[11px]">
                L1_DOCUMENTED
              </Badge>
            )}
          </div>
        </div>

        {/* The driving inquiry question */}
        <div className="my-2 rounded-xl border border-primary/25 bg-background/80 p-5 shadow-inner">
          <div className="flex items-start gap-3">
            <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-primary/15 text-primary">
              <HelpCircle className="h-5 w-5" />
            </span>
            <div className="space-y-1">
              <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wide">
                Vấn đề cốt lõi (Vì sao / Như thế nào):
              </p>
              <h2 className="font-display text-lg font-bold leading-relaxed text-foreground md:text-xl">
                &ldquo;{question}&rdquo;
              </h2>
            </div>
          </div>
        </div>

        {/* Vetted historical summary */}
        {historicalSummary && (
          <div className="rounded-xl bg-card/60 p-4 border border-border/40">
            <div className="flex items-center gap-2 mb-2 text-xs font-semibold text-muted-foreground uppercase tracking-wide">
              <BookOpen className="h-3.5 w-3.5 text-primary" />
              <span>Tóm tắt bối cảnh lịch sử đã thẩm định:</span>
            </div>
            <p className="text-sm leading-relaxed text-foreground/90 text-justify">
              {historicalSummary}
            </p>
          </div>
        )}
      </div>
    </section>
  );
}
