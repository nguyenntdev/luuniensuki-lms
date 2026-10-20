"use client";

import React, { useState, useMemo } from "react";
import {
  Calendar,
  CheckCircle2,
  ChevronDown,
  ChevronRight,
  ChevronUp,
  HelpCircle,
  History,
  Lightbulb,
  RotateCcw,
  Sparkles,
  Trophy,
  Volume2,
  VolumeX,
  XCircle,
  ArrowRight,
  BookOpen,
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import {
  TIMELINE_CHALLENGES,
  verifyTimelineOrdering,
  type TimelineChallenge,
  type TimelineEventItem,
} from "@/lib/imperial/games-data";
import {
  playGameSuccessSound,
  playGameErrorSound,
  playGameHintSound,
  playGameClickSound,
  playGameVictorySound,
} from "@/lib/imperial/game-audio";
import { cn } from "@/lib/utils";

export interface TimelineSequenceGameProps {
  onComplete?: (score: number) => void;
  className?: string;
}

export function TimelineSequenceGame({
  onComplete,
  className,
}: TimelineSequenceGameProps) {
  const [activeChallengeIndex, setActiveChallengeIndex] = useState<number>(0);
  const activeChallenge = TIMELINE_CHALLENGES[activeChallengeIndex] || TIMELINE_CHALLENGES[0];

  // Deterministically shuffle initial items so student must reorder
  const initialShuffledEvents = useMemo(() => {
    const list = [...activeChallenge.events];
    if (list.length >= 4) {
      // Swap positions [0] with [2] and [1] with [3] for a good pedagogical puzzle
      const temp0 = list[0];
      list[0] = list[2];
      list[2] = temp0;
      const temp1 = list[1];
      list[1] = list[3];
      list[3] = temp1;
    }
    return list;
  }, [activeChallenge]);

  const [currentOrder, setCurrentOrder] = useState<TimelineEventItem[]>(initialShuffledEvents);
  const [revealedHintIndex, setRevealedHintIndex] = useState<number>(0);
  const [validationResult, setValidationResult] = useState<{
    validated: boolean;
    isCorrect: boolean;
    correctCount: number;
    scoreAwarded: number;
    feedback: string;
  } | null>(null);

  const [soundEnabled, setSoundEnabled] = useState<boolean>(true);

  // When switching challenge, reset states
  const handleSelectChallenge = (index: number) => {
    setActiveChallengeIndex(index);
    const targetChallenge = TIMELINE_CHALLENGES[index] || TIMELINE_CHALLENGES[0];
    const list = [...targetChallenge.events];
    if (list.length >= 4) {
      const temp0 = list[0];
      list[0] = list[2];
      list[2] = temp0;
      const temp1 = list[1];
      list[1] = list[3];
      list[3] = temp1;
    }
    setCurrentOrder(list);
    setRevealedHintIndex(0);
    setValidationResult(null);
    if (soundEnabled) playGameClickSound();
  };

  const handleMoveUp = (index: number) => {
    if (index <= 0) return;
    if (soundEnabled) playGameClickSound();
    setCurrentOrder((prev) => {
      const next = [...prev];
      const temp = next[index - 1];
      next[index - 1] = next[index];
      next[index] = temp;
      return next;
    });
    setValidationResult(null);
  };

  const handleMoveDown = (index: number) => {
    if (index >= currentOrder.length - 1) return;
    if (soundEnabled) playGameClickSound();
    setCurrentOrder((prev) => {
      const next = [...prev];
      const temp = next[index + 1];
      next[index + 1] = next[index];
      next[index] = temp;
      return next;
    });
    setValidationResult(null);
  };

  const handleRevealHint = () => {
    if (revealedHintIndex < activeChallenge.hints.length) {
      setRevealedHintIndex((prev) => prev + 1);
      if (soundEnabled) playGameHintSound();
    }
  };

  const handleResetOrder = () => {
    setCurrentOrder(initialShuffledEvents);
    setValidationResult(null);
    if (soundEnabled) playGameClickSound();
  };

  const handleValidateOrder = () => {
    const submittedIds = currentOrder.map((e) => e.id);
    const result = verifyTimelineOrdering(activeChallenge, submittedIds);

    setValidationResult({
      validated: true,
      isCorrect: result.isCorrect,
      correctCount: result.correctCount,
      scoreAwarded: result.scoreAwarded,
      feedback: result.feedback,
    });

    if (result.isCorrect) {
      if (soundEnabled) playGameSuccessSound();
      if (onComplete) {
        onComplete(result.scoreAwarded);
      }
    } else {
      if (soundEnabled) playGameErrorSound();
    }
  };

  return (
    <div className={cn("space-y-6", className)}>
      {/* Header & Challenge Switcher */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-border/60 pb-4">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <Badge className="bg-amber-500/15 text-amber-700 dark:text-amber-300 border-amber-500/30 text-xs font-semibold gap-1.5 py-0.5 px-2.5">
              <History className="size-3.5" />
              <span>Năng Lực S2 — Sắp Xếp Niên Biểu Di Sản</span>
            </Badge>
            <Badge variant="outline" className="text-xs">
              +{activeChallenge.points} XP
            </Badge>
          </div>
          <h3 className="font-serif font-bold text-lg sm:text-xl text-foreground">
            {activeChallenge.title}
          </h3>
          <p className="text-xs sm:text-sm text-muted-foreground">
            {activeChallenge.description}
          </p>
        </div>

        {/* Audio Toggle & Quick Switch */}
        <div className="flex items-center gap-2 shrink-0">
          <Button
            variant="ghost"
            size="icon"
            onClick={() => setSoundEnabled((prev) => !prev)}
            className="size-8 text-muted-foreground hover:text-foreground"
            title={soundEnabled ? "Tắt âm thanh hiệu ứng" : "Bật âm thanh hiệu ứng"}
          >
            {soundEnabled ? <Volume2 className="size-4" /> : <VolumeX className="size-4" />}
          </Button>

          <span className="text-xs text-muted-foreground font-medium">
            Thử thách {activeChallengeIndex + 1}/{TIMELINE_CHALLENGES.length}
          </span>
        </div>
      </div>

      {/* Challenge Navigation Tabs */}
      <div className="flex flex-wrap gap-2">
        {TIMELINE_CHALLENGES.map((ch, idx) => (
          <Button
            key={ch.id}
            variant={idx === activeChallengeIndex ? "default" : "outline"}
            size="sm"
            onClick={() => handleSelectChallenge(idx)}
            className="text-xs h-8 gap-1.5"
          >
            <span>Bài {idx + 1}: {ch.title.split("(")[0].trim()}</span>
          </Button>
        ))}
      </div>

      {/* Main Timeline Card */}
      <Card className="border border-border/80 shadow-md bg-card/95 overflow-hidden">
        <CardHeader className="bg-muted/30 p-4 sm:p-5 border-b border-border/60">
          <div className="flex items-center justify-between gap-2">
            <CardTitle className="text-sm sm:text-base font-serif flex items-center gap-2">
              <Calendar className="size-4 text-primary" />
              <span>Dùng các nút ▲ ▼ để sắp xếp các sự kiện theo đúng thứ tự thời gian:</span>
            </CardTitle>
            <span className="text-xs text-muted-foreground hidden sm:inline">
              (Từ sớm nhất ở trên đến muộn nhất ở dưới)
            </span>
          </div>
        </CardHeader>

        <CardContent className="p-4 sm:p-6 space-y-4">
          {/* Timeline Cards Container */}
          <div className="space-y-3">
            {currentOrder.map((evt, idx) => {
              const isFirst = idx === 0;
              const isLast = idx === currentOrder.length - 1;

              return (
                <div
                  key={evt.id}
                  className={cn(
                    "flex items-center gap-3 p-3.5 sm:p-4 rounded-2xl border transition-all duration-200",
                    validationResult?.isCorrect
                      ? "border-emerald-500/60 bg-emerald-500/5 shadow-sm"
                      : "border-border/70 bg-background hover:border-primary/40 shadow-xs",
                  )}
                >
                  {/* Step Order Badge */}
                  <div className="flex size-8 sm:size-9 shrink-0 items-center justify-center rounded-xl bg-primary/10 border border-primary/20 text-xs sm:text-sm font-bold text-primary font-mono">
                    {idx + 1}
                  </div>

                  {/* Event Details */}
                  <div className="flex-1 min-w-0 space-y-1">
                    <div className="flex flex-wrap items-center gap-2">
                      <span className="font-serif font-bold text-xs sm:text-sm text-foreground">
                        {evt.title}
                      </span>
                      {validationResult?.isCorrect && (
                        <Badge className="bg-emerald-600 text-white text-[10px] font-mono px-1.5 py-0">
                          {evt.year_label}
                        </Badge>
                      )}
                    </div>
                    <p className="text-xs text-muted-foreground leading-relaxed line-clamp-2">
                      {evt.description}
                    </p>
                  </div>

                  {/* Reordering Controls (Touch-Friendly min 44px) */}
                  {!validationResult?.isCorrect && (
                    <div className="flex flex-col gap-1 shrink-0">
                      <button
                        type="button"
                        disabled={isFirst}
                        onClick={() => handleMoveUp(idx)}
                        className={cn(
                          "size-9 sm:size-10 rounded-lg flex items-center justify-center border transition-all touch-manipulation",
                          isFirst
                            ? "opacity-30 cursor-not-allowed border-border/40 text-muted-foreground"
                            : "border-border/80 bg-muted/40 hover:bg-primary/10 hover:border-primary text-foreground active:scale-95",
                        )}
                        title="Di chuyển lên trước"
                        aria-label={`Di chuyển sự kiện "${evt.title}" lên trước`}
                      >
                        <ChevronUp className="size-4" />
                      </button>

                      <button
                        type="button"
                        disabled={isLast}
                        onClick={() => handleMoveDown(idx)}
                        className={cn(
                          "size-9 sm:size-10 rounded-lg flex items-center justify-center border transition-all touch-manipulation",
                          isLast
                            ? "opacity-30 cursor-not-allowed border-border/40 text-muted-foreground"
                            : "border-border/80 bg-muted/40 hover:bg-primary/10 hover:border-primary text-foreground active:scale-95",
                        )}
                        title="Di chuyển xuống sau"
                        aria-label={`Di chuyển sự kiện "${evt.title}" xuống sau`}
                      >
                        <ChevronDown className="size-4" />
                      </button>
                    </div>
                  )}

                  {validationResult?.isCorrect && (
                    <CheckCircle2 className="size-5 text-emerald-500 shrink-0" />
                  )}
                </div>
              );
            })}
          </div>

          {/* Progressive Hints Section */}
          {revealedHintIndex > 0 && (
            <div className="rounded-xl border border-amber-500/30 bg-amber-500/5 p-3.5 space-y-2 animate-in fade-in">
              <span className="text-[11px] font-bold text-amber-700 dark:text-amber-300 uppercase tracking-wider block">
                Manh mối niên đại ({revealedHintIndex}/{activeChallenge.hints.length}):
              </span>
              <div className="space-y-1.5">
                {activeChallenge.hints.slice(0, revealedHintIndex).map((hint, hIdx) => (
                  <div key={hIdx} className="text-xs text-amber-950 dark:text-amber-200 flex items-start gap-2">
                    <Lightbulb className="size-3.5 text-amber-500 shrink-0 mt-0.5" />
                    <span>{hint}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Action Buttons Bar */}
          <div className="flex flex-wrap items-center justify-between gap-3 pt-2 border-t border-border/60">
            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={handleRevealHint}
                disabled={revealedHintIndex >= activeChallenge.hints.length || validationResult?.isCorrect}
                className="text-xs h-9 gap-1.5 border-dashed"
              >
                <HelpCircle className="size-3.5 text-amber-500" />
                <span>
                  {revealedHintIndex >= activeChallenge.hints.length
                    ? "Đã mở hết manh mối"
                    : `Mở manh mối (${revealedHintIndex}/${activeChallenge.hints.length})`}
                </span>
              </Button>

              {!validationResult?.isCorrect && (
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={handleResetOrder}
                  className="text-xs h-9 text-muted-foreground gap-1"
                >
                  <RotateCcw className="size-3" />
                  <span>Xếp lại</span>
                </Button>
              )}
            </div>

            {!validationResult?.isCorrect ? (
              <Button
                onClick={handleValidateOrder}
                className="gap-2 bg-primary text-primary-foreground font-semibold text-xs h-9 px-5 shadow-sm"
              >
                <span>Kiểm tra thứ tự</span>
                <ChevronRight className="size-4" />
              </Button>
            ) : (
              <Button
                onClick={() => {
                  if (activeChallengeIndex < TIMELINE_CHALLENGES.length - 1) {
                    handleSelectChallenge(activeChallengeIndex + 1);
                  } else {
                    if (soundEnabled) playGameVictorySound();
                  }
                }}
                className="gap-2 bg-emerald-600 hover:bg-emerald-700 text-white font-semibold text-xs h-9 px-5 shadow-sm"
              >
                <span>
                  {activeChallengeIndex < TIMELINE_CHALLENGES.length - 1
                    ? "Thử thách tiếp theo"
                    : "Hoàn thành toàn bộ niên biểu"}
                </span>
                <ArrowRight className="size-4" />
              </Button>
            )}
          </div>

          {/* Result Feedback Banner */}
          {validationResult && (
            <div
              className={cn(
                "rounded-2xl border p-4 sm:p-5 space-y-3 animate-in fade-in slide-in-from-top-2",
                validationResult.isCorrect
                  ? "border-emerald-500/40 bg-emerald-500/10 text-emerald-950 dark:text-emerald-200"
                  : "border-amber-500/40 bg-amber-500/10 text-amber-950 dark:text-amber-200",
              )}
            >
              <div className="flex items-center justify-between gap-2">
                <div className="flex items-center gap-2">
                  {validationResult.isCorrect ? (
                    <Sparkles className="size-5 text-emerald-600 dark:text-emerald-400 shrink-0" />
                  ) : (
                    <XCircle className="size-5 text-amber-600 shrink-0" />
                  )}
                  <span className="font-serif font-bold text-sm sm:text-base">
                    {validationResult.isCorrect
                      ? "Khảo cứu niên biểu chuẩn xác tuyệt đối!"
                      : "Thứ tự niên biểu chưa hoàn toàn khớp"}
                  </span>
                </div>

                {validationResult.isCorrect && (
                  <Badge className="bg-emerald-600 text-white font-bold text-xs">
                    +{validationResult.scoreAwarded} XP
                  </Badge>
                )}
              </div>

              <p className="text-xs sm:text-sm leading-relaxed">
                {validationResult.feedback}
              </p>

              {validationResult.isCorrect && (
                <div className="space-y-2 pt-2 border-t border-emerald-500/30">
                  <div className="text-xs font-serif leading-relaxed opacity-95">
                    <strong>Tổng kết diễn tiến lịch sử:</strong> {activeChallenge.explanation}
                  </div>

                  <div className="rounded-lg border border-border/60 bg-background/80 p-2 text-[11px] text-muted-foreground flex items-center gap-2">
                    <BookOpen className="size-3 text-primary shrink-0" />
                    <span>
                      <strong>Nguồn sử liệu đối chiếu:</strong> {activeChallenge.source_citation}
                    </span>
                  </div>
                </div>
              )}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
