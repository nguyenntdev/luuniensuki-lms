"use client";

import React, { useState } from "react";
import Link from "next/link";
import {
  Compass,
  HelpCircle,
  Lightbulb,
  Search,
  Sparkles,
  CheckCircle2,
  AlertCircle,
  ArrowRight,
  Eye,
  SkipForward,
  ChevronRight,
  Award,
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import type { ImperialClue } from "@/lib/imperial/v51-types";
import { submitClueAttempt } from "@/lib/imperial/v51-api";
import {
  unlockSeal,
  showSealCelebrationToast,
  getSealDefinition,
} from "@/lib/imperial/passport-storage";
import { playRoyalSealSound } from "@/lib/imperial/seal-audio";
import {
  playGameSuccessSound,
  playGameErrorSound,
  playGameHintSound,
  playGameClickSound,
} from "@/lib/imperial/game-audio";
import { cn } from "@/lib/utils";

interface HeritageDetectiveWidgetProps {
  clue: ImperialClue;
  currentSiteSlug?: string;
  currentSiteId?: string;
  onClueSolved?: (clueId: string, pointsAwarded: number) => void;
  onOpenFullModal?: () => void;
  className?: string;
}

const CANDIDATE_TARGETS = [
  { slug: "ngo-mon", name: "Ngọ Môn" },
  { slug: "dien-thai-hoa", name: "Điện Thái Hòa" },
  { slug: "dien-kien-trung", name: "Điện Kiến Trung" },
  { slug: "hien-lam-cac", name: "Hiển Lâm Các" },
  { slug: "the-to-mieu", name: "Thế Tổ Miếu" },
  { slug: "thai-binh-lau", name: "Thái Bình Lâu" },
];

export function HeritageDetectiveWidget({
  clue,
  currentSiteSlug,
  currentSiteId,
  onClueSolved,
  onOpenFullModal,
  className,
}: HeritageDetectiveWidgetProps) {
  const [revealedHintIndex, setRevealedHintIndex] = useState<number>(0);
  const [isSkipped, setIsSkipped] = useState<boolean>(false);
  const [attemptState, setAttemptState] = useState<{
    status: "idle" | "verifying" | "success" | "wrong";
    message?: string;
    points?: number;
  }>({ status: "idle" });

  const hints = clue.hint_steps || [];
  const maxHints = hints.length;

  const handleRevealNextHint = () => {
    if (revealedHintIndex < maxHints) {
      setRevealedHintIndex((prev) => prev + 1);
      playGameHintSound();
    }
  };

  const handleCheckTarget = async (targetSlugOrId: string) => {
    if (!targetSlugOrId) return;

    setAttemptState({ status: "verifying" });
    try {
      const res = await submitClueAttempt(clue.id, targetSlugOrId);
      if (res.success) {
        playGameSuccessSound();
        playRoyalSealSound({ material: "stone" });
        setAttemptState({
          status: "success",
          message: res.message || "Xuất sắc! Bạn đã giải mã chính xác manh mối di sản!",
          points: res.points_awarded || 30,
        });
        if (onClueSolved) {
          onClueSolved(clue.id, res.points_awarded || 30);
        }

        // Automatically unlock royal seal and notify student
        const targetSlug =
          clue.target_slug ||
          (targetSlugOrId.startsWith("site-")
            ? targetSlugOrId.replace("site-", "")
            : targetSlugOrId) ||
          currentSiteSlug;

        if (targetSlug) {
          const sealDef = getSealDefinition(targetSlug);
          const monumentName =
            sealDef?.name ||
            CANDIDATE_TARGETS.find((c) => c.slug === targetSlug)?.name ||
            targetSlug;

          try {
            unlockSeal(targetSlug, `Giải mã manh mối: ${clue.title}`);
            showSealCelebrationToast(targetSlug, monumentName);
          } catch (err) {
            console.warn("Could not unlock passport seal for clue:", err);
          }
        }
      } else {
        playGameErrorSound();
        // Automatically reveal hint on wrong attempt
        if (revealedHintIndex < maxHints) {
          setRevealedHintIndex((prev) => Math.min(prev + 1, maxHints));
        }
        setAttemptState({
          status: "wrong",
          message: res.message || "Chưa chính xác! Hãy quan sát kỹ kiến trúc xung quanh hoặc mở thêm gợi ý.",
        });
      }
    } catch {
      playGameErrorSound();
      setAttemptState({
        status: "wrong",
        message: "Không thể kiểm tra lúc này. Bạn có thể bỏ qua để tiếp tục học tập.",
      });
    }
  };

  const handleCheckCurrentLocation = async () => {
    const targetIdOrSlug = currentSiteId || currentSiteSlug;
    if (!targetIdOrSlug) return;
    await handleCheckTarget(targetIdOrSlug);
  };

  const handleSkip = () => {
    setIsSkipped(true);
  };

  if (isSkipped) {
    return (
      <div
        className={cn(
          "rounded-xl border border-border/60 bg-muted/30 px-3.5 py-2 text-xs flex items-center justify-between gap-3 text-muted-foreground",
          className,
        )}
      >
        <div className="flex items-center gap-2">
          <Search className="size-3.5 text-primary" />
          <span>Thám tử di sản đang tạm ẩn cho bài học này.</span>
        </div>
        <Button
          variant="ghost"
          size="sm"
          className="h-7 text-xs text-primary font-medium hover:bg-primary/10"
          onClick={() => setIsSkipped(false)}
        >
          Hiện lại manh mối
        </Button>
      </div>
    );
  }

  return (
    <Card
      className={cn(
        "relative overflow-hidden border-2 transition-all duration-300",
        attemptState.status === "success"
          ? "border-emerald-500/50 bg-emerald-500/5 shadow-emerald-500/10"
          : attemptState.status === "wrong"
          ? "border-amber-500/50 bg-amber-500/5"
          : "border-primary/30 bg-gradient-to-r from-card via-card to-primary/5 shadow-md",
        className,
      )}
    >
      <div className="absolute top-0 right-0 h-24 w-24 bg-primary/5 rounded-bl-full pointer-events-none" />

      <CardContent className="p-4 sm:p-5 space-y-3.5">
        {/* Header Bar */}
        <div className="flex flex-wrap items-center justify-between gap-2">
          <div className="flex items-center gap-2">
            <Badge className="bg-primary/15 text-primary border-primary/20 hover:bg-primary/20 text-xs font-semibold gap-1 py-0.5 px-2.5">
              <Compass className="size-3.5 animate-spin-slow" />
              <span>Thám tử di sản Đại Nội</span>
            </Badge>

            <span className="text-[11px] font-medium text-muted-foreground">
              Độ khó:{" "}
              <strong className="text-foreground capitalize">
                {clue.difficulty === "easy"
                  ? "Cơ bản"
                  : clue.difficulty === "hard"
                  ? "Nâng cao"
                  : "Trung bình"}
              </strong>
            </span>
          </div>

          <div className="flex items-center gap-2">
            {onOpenFullModal && (
              <Button
                variant="ghost"
                size="sm"
                onClick={onOpenFullModal}
                className="h-7 text-xs text-muted-foreground hover:text-foreground gap-1 px-2"
              >
                <Eye className="size-3" />
                <span>Xem tất cả câu đố</span>
              </Button>
            )}

            <Button
              variant="ghost"
              size="sm"
              onClick={handleSkip}
              className="h-7 text-xs text-muted-foreground hover:text-foreground gap-1 px-2"
              title="Không khóa tiến trình học tập"
            >
              <SkipForward className="size-3" />
              <span>Bỏ qua để học</span>
            </Button>
          </div>
        </div>

        {/* Riddle / Clue Description */}
        <div className="space-y-1">
          <h4 className="font-serif font-bold text-base text-foreground flex items-center gap-1.5">
            <Sparkles className="size-4 text-amber-500 shrink-0" />
            <span>{clue.title}</span>
          </h4>
          <p className="text-xs sm:text-sm text-foreground/90 font-serif italic leading-relaxed border-l-2 border-primary/40 pl-3 py-0.5 bg-background/50 rounded-r-md">
            &ldquo;{clue.clue_text}&rdquo;
          </p>
        </div>

        {/* Progressive Hints Section */}
        {revealedHintIndex > 0 && (
          <div className="space-y-1.5 pt-1">
            <span className="text-[11px] font-semibold text-muted-foreground uppercase tracking-wider block">
              Gợi ý manh mối ({revealedHintIndex}/{maxHints}):
            </span>
            <div className="space-y-1.5">
              {hints.slice(0, revealedHintIndex).map((hint, idx) => (
                <div
                  key={idx}
                  className="rounded-lg border border-amber-500/20 bg-amber-500/5 px-3 py-1.5 text-xs text-amber-950 dark:text-amber-200 flex items-start gap-2 animate-in fade-in slide-in-from-top-1"
                >
                  <Lightbulb className="size-3.5 text-amber-500 shrink-0 mt-0.5" />
                  <span>
                    <strong>Gợi ý {idx + 1}:</strong> {hint}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Feedback State */}
        {attemptState.status === "success" && (
          <div className="space-y-2 animate-in zoom-in-95">
            <div className="rounded-xl border border-emerald-500/40 bg-emerald-500/10 p-3 text-xs sm:text-sm text-emerald-900 dark:text-emerald-200 flex items-center justify-between gap-3">
              <div className="flex items-center gap-2.5">
                <CheckCircle2 className="size-5 text-emerald-600 dark:text-emerald-400 shrink-0" />
                <div>
                  <strong className="block font-semibold">Chính xác xuất sắc!</strong>
                  <span className="opacity-90">{attemptState.message}</span>
                </div>
              </div>
              <Badge className="bg-emerald-600 text-white font-bold text-xs shrink-0 gap-1 py-1 px-2.5">
                <Award className="size-3.5" />
                <span>+{attemptState.points || 30} XP</span>
              </Badge>
            </div>

            <div className="flex items-center justify-between rounded-lg border border-red-700/30 bg-red-700/5 px-3 py-2 text-xs">
              <span className="flex items-center gap-1.5 text-red-700 dark:text-red-400 font-semibold">
                <span className="font-serif font-black">印</span>
                <span>Đã đóng Dấu Triện Hoàng Gia vào Hộ Chiếu</span>
              </span>
              <Link
                href="/dai-noi/ho-chieu"
                className="font-bold text-primary hover:underline flex items-center gap-1 text-[11px]"
              >
                <span>Mở Hộ Chiếu</span>
                <ChevronRight className="size-3" />
              </Link>
            </div>
          </div>
        )}

        {attemptState.status === "wrong" && (
          <div className="rounded-xl border border-amber-500/40 bg-amber-500/10 p-3 text-xs sm:text-sm text-amber-900 dark:text-amber-200 flex items-center gap-2.5 animate-in shake">
            <AlertCircle className="size-4 text-amber-600 dark:text-amber-400 shrink-0" />
            <span>{attemptState.message}</span>
          </div>
        )}

        {/* Interactive Action Footer */}
        {attemptState.status !== "success" && (
          <div className="flex flex-wrap items-center justify-between gap-2.5 pt-2 border-t border-border/50">
            <Button
              variant="outline"
              size="sm"
              onClick={handleRevealNextHint}
              disabled={revealedHintIndex >= maxHints}
              className="text-xs h-8 gap-1.5 border-dashed"
            >
              <HelpCircle className="size-3.5 text-amber-500" />
              <span>
                {revealedHintIndex >= maxHints
                  ? "Đã mở hết gợi ý"
                  : `Gợi ý manh mối (${revealedHintIndex}/${maxHints})`}
              </span>
            </Button>

            {currentSiteSlug ? (
              <Button
                size="sm"
                onClick={handleCheckCurrentLocation}
                disabled={attemptState.status === "verifying"}
                className="text-xs h-8 gap-1.5 bg-primary text-primary-foreground font-semibold shadow-sm"
              >
                <span>Xác nhận vị trí hiện tại</span>
                <ChevronRight className="size-3.5" />
              </Button>
            ) : null}
          </div>
        )}

        {/* Candidate Target Quick Options (when no current site is pre-set) */}
        {attemptState.status !== "success" && !currentSiteSlug && (
          <div className="space-y-2 pt-2 border-t border-border/40">
            <span className="text-[11px] font-semibold text-muted-foreground uppercase tracking-wider block">
              Gửi dự đoán công trình:
            </span>
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
              {CANDIDATE_TARGETS.map((tgt) => (
                <Button
                  key={tgt.slug}
                  variant="outline"
                  size="sm"
                  onClick={() => handleCheckTarget(tgt.slug)}
                  disabled={attemptState.status === "verifying"}
                  className="text-xs min-h-[42px] py-2 px-2.5 justify-start truncate border-border/70 hover:bg-primary/10 hover:text-primary active:scale-[0.98] transition-all"
                >
                  <Search className="size-3.5 mr-1.5 shrink-0 text-primary" />
                  <span className="truncate">{tgt.name}</span>
                </Button>
              ))}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
