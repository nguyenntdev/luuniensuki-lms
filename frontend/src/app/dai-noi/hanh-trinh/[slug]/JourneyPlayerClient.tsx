"use client";

import React, { useState, useEffect, useMemo } from "react";
import Image from "next/image";
import Link from "next/link";
import {
  ArrowLeft,
  ArrowRight,
  Award,
  BookOpen,
  CheckCircle2,
  ChevronLeft,
  ChevronRight,
  Clock,
  Compass,
  Crosshair,
  Eye,
  FileCheck2,
  FileText,
  Footprints,
  GraduationCap,
  HelpCircle,
  Layers,
  Lightbulb,
  MapPin,
  Maximize2,
  RotateCcw,
  Route,
  Save,
  Send,
  Sparkles,
  Trophy,
} from "lucide-react";
import ImperialHeader from "@/components/imperial/shell/ImperialHeader";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import type { ImperialTrail, StudentSubmission } from "@/lib/imperial/map-types";
import type { ImperialArtDetail, ImperialClue } from "@/lib/imperial/v51-types";
import { FALLBACK_ART_DETAILS, FALLBACK_CLUES } from "@/lib/imperial/v51-api";
import { HeritageDetectiveWidget } from "@/components/imperial/detective/HeritageDetectiveWidget";
import { HeritageGames } from "@/components/imperial/games/HeritageGames";
import StudentSubmissionModal from "@/components/imperial/dossier/StudentSubmissionModal";
import { cn } from "@/lib/utils";

interface JourneyPlayerClientProps {
  trail: ImperialTrail;
}

type JourneyStage = 1 | 2 | 3 | 4 | 5;

const STAGE_CONFIG: Record<
  JourneyStage,
  {
    order: JourneyStage;
    timeRange: string;
    title: string;
    description: string;
    badge: string;
  }
> = {
  1: {
    order: 1,
    timeRange: "0–5p",
    title: "Khởi động & Định vị Không gian",
    description: "Khám phá câu hỏi dẫn dắt và định vị trục không gian Đại Nội trên bản đồ trực giao.",
    badge: "Định vị không gian (S1)",
  },
  2: {
    order: 2,
    timeRange: "5–12p",
    title: "Giải mã Manh mối Di sản",
    description: "Thám tử di sản: đọc câu đố và suy luận để xác định điểm xuất phát của hành trình.",
    badge: "Thám tử di sản (S1 & S3)",
  },
  3: {
    order: 3,
    timeRange: "12–25p",
    title: "Quan sát Chi tiết Mỹ thuật & Sử liệu",
    description: "Khảo sát cận cảnh 2 chi tiết mỹ thuật cung đình, đối chiếu chính sử triều Nguyễn.",
    badge: "Khảo cứu sử liệu (S2 & S3)",
  },
  4: {
    order: 4,
    timeRange: "25–35p",
    title: "Đối chiếu Ý nghĩa & Thử thách Hiểu sâu",
    description: "Phân tích ý nghĩa biểu tượng quyền lực và hoàn thành câu hỏi củng cố 'Vì sao'.",
    badge: "Năng lực lập luận (S4)",
  },
  5: {
    order: 5,
    timeRange: "35–45p",
    title: "Kết luận M-E-E & Nộp Exit Ticket",
    description: "Trình bày kết luận cá nhân theo mô hình M-E-E và nộp phiếu đánh giá năng lực.",
    badge: "Đánh giá chuẩn Rubric",
  },
};

export default function JourneyPlayerClient({ trail }: JourneyPlayerClientProps) {
  const [currentStage, setCurrentStage] = useState<JourneyStage>(1);
  const [completedStages, setCompletedStages] = useState<number[]>([]);
  const [isSubmissionOpen, setIsSubmissionOpen] = useState(false);
  const [clueSolved, setClueSolved] = useState(false);
  const [earnedXp, setEarnedXp] = useState(0);

  // Storage key for saving progress
  const storageKey = `journey_progress_${trail.slug}`;

  // Load saved progress from localStorage on mount
  useEffect(() => {
    try {
      const saved = localStorage.getItem(storageKey);
      if (saved) {
        const parsed = JSON.parse(saved);
        if (parsed.currentStage) setCurrentStage(parsed.currentStage);
        if (parsed.completedStages) setCompletedStages(parsed.completedStages);
        if (parsed.earnedXp) setEarnedXp(parsed.earnedXp);
      }
    } catch {
      // Local storage not available
    }
  }, [storageKey]);

  // Save progress helper
  const saveProgress = (stage: JourneyStage, completed: number[], xp: number) => {
    try {
      localStorage.setItem(
        storageKey,
        JSON.stringify({
          currentStage: stage,
          completedStages: completed,
          earnedXp: xp,
          updatedAt: new Date().toISOString(),
        }),
      );
    } catch {
      // Ignore write errors
    }
  };

  const handleStageComplete = (stage: JourneyStage, bonusXp = 0) => {
    const nextCompleted = completedStages.includes(stage)
      ? completedStages
      : [...completedStages, stage];
    const newXp = earnedXp + bonusXp;

    setCompletedStages(nextCompleted);
    setEarnedXp(newXp);

    if (stage < 5) {
      const nextStage = (stage + 1) as JourneyStage;
      setCurrentStage(nextStage);
      saveProgress(nextStage, nextCompleted, newXp);
    } else {
      saveProgress(stage, nextCompleted, newXp);
    }
  };

  const activeClue: ImperialClue = useMemo(() => {
    return (
      FALLBACK_CLUES.find((c) => c.target_slug === trail.stops[0]?.monument_slug) ||
      FALLBACK_CLUES[0]
    );
  }, [trail.stops]);

  const activeArtDetails: ImperialArtDetail[] = useMemo(() => {
    return FALLBACK_ART_DETAILS.slice(0, 2);
  }, []);

  const progressPercent = Math.round((completedStages.length / 5) * 100);

  return (
    <div className="min-h-screen bg-background flex flex-col selection:bg-primary/20 selection:text-primary">
      <ImperialHeader />

      <main className="flex-1 max-w-6xl w-full mx-auto px-4 py-6 sm:px-6 space-y-6">
        {/* Navigation Breadcrumb & Back */}
        <div className="flex flex-wrap items-center justify-between gap-3">
          <Link
            href="/dai-noi/tuyen-duong"
            className="inline-flex items-center gap-1.5 text-xs text-muted-foreground hover:text-foreground transition-colors"
          >
            <ChevronLeft className="size-4" />
            <span>Quay lại danh sách tuyến học</span>
          </Link>

          <div className="flex items-center gap-2">
            <Badge className="bg-primary/10 text-primary border-primary/20 text-xs font-semibold gap-1">
              <Clock className="size-3" />
              <span>Thời lượng: 35–45 phút</span>
            </Badge>

            <Badge className="bg-amber-500/15 text-amber-700 dark:text-amber-300 border-amber-500/30 text-xs font-bold gap-1">
              <Trophy className="size-3 text-amber-500" />
              <span>+{earnedXp} XP</span>
            </Badge>
          </div>
        </div>

        {/* Journey Header Card */}
        <div className="rounded-2xl border border-border/80 bg-gradient-to-r from-card via-card to-primary/5 p-5 sm:p-6 shadow-md space-y-3">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <div>
              <span className="text-[10px] uppercase font-bold text-muted-foreground tracking-wider block">
                Hành Trình Khảo Cứu Di Sản (GDPT 2018)
              </span>
              <h1 className="font-serif font-bold text-xl sm:text-2xl text-foreground">
                {trail.title}
              </h1>
            </div>

            <span className="text-xs font-semibold text-primary">
              Tiến độ hoàn thành: {progressPercent}%
            </span>
          </div>

          <p className="text-xs sm:text-sm text-muted-foreground leading-relaxed">
            {trail.description}
          </p>

          {/* 5-Stage Interactive Stepper */}
          <div className="grid grid-cols-5 gap-1.5 sm:gap-2 pt-2 border-t border-border/60">
            {([1, 2, 3, 4, 5] as JourneyStage[]).map((stage) => {
              const cfg = STAGE_CONFIG[stage];
              const isCurrent = currentStage === stage;
              const isDone = completedStages.includes(stage);

              return (
                <button
                  key={stage}
                  onClick={() => setCurrentStage(stage)}
                  className={cn(
                    "p-2 rounded-xl border text-left transition-all space-y-1 relative",
                    isCurrent
                      ? "border-primary bg-primary/10 ring-2 ring-primary/40 font-semibold"
                      : isDone
                      ? "border-emerald-500/50 bg-emerald-500/5 text-foreground"
                      : "border-border/60 hover:bg-muted/40 opacity-75",
                  )}
                >
                  <div className="flex items-center justify-between">
                    <span className="text-[10px] font-bold text-muted-foreground uppercase">
                      {cfg.timeRange}
                    </span>
                    {isDone && (
                      <CheckCircle2 className="size-3 text-emerald-500 shrink-0" />
                    )}
                  </div>
                  <span className="block text-[11px] font-medium truncate leading-tight">
                    {cfg.title.split("&")[0]?.trim()}
                  </span>
                </button>
              );
            })}
          </div>
        </div>

        {/* ============================================================== */}
        {/* STAGE 1: 0–5p DRIVING QUESTION & AERIAL MAP ORIENTATION        */}
        {/* ============================================================== */}
        {currentStage === 1 && (
          <Card className="border border-border/80 shadow-md">
            <CardHeader className="p-5 sm:p-6 border-b border-border/60 bg-muted/20">
              <div className="flex items-center justify-between">
                <Badge className="bg-primary/15 text-primary text-xs">
                  Chặng 1 (0–5 phút)
                </Badge>
                <span className="text-xs text-muted-foreground">Mục tiêu: S1 Không gian</span>
              </div>
              <CardTitle className="font-serif text-xl mt-1">
                Câu Hỏi Dẫn Dắt & Định Vị Không Gian
              </CardTitle>
              <CardDescription className="text-xs sm:text-sm">
                Xác định trục nghi lễ trung tâm và các công trình tiền tiêu của Đại Nội.
              </CardDescription>
            </CardHeader>

            <CardContent className="p-5 sm:p-6 space-y-5">
              <div className="rounded-xl border border-primary/20 bg-primary/5 p-4 space-y-2">
                <span className="text-[11px] font-bold uppercase text-primary tracking-wider block">
                  Câu hỏi nghiên cứu trọng tâm:
                </span>
                <p className="font-serif font-bold text-base sm:text-lg text-foreground italic">
                  &ldquo;Khi bước qua cửa Ngọ Môn vào Hoàng Thành, vì sao trục chính đạo lại dẫn thẳng qua cầu Trung Đạo tới sân Đại Triều và Điện Thái Hòa?&rdquo;
                </p>
              </div>

              {/* Aerial Map Snapshot / Orientation */}
              <div className="relative rounded-2xl overflow-hidden border border-border/70 aspect-[16/9] max-h-[380px] bg-muted/30">
                <Image
                  src="/panoramas/the-mieu.jpg"
                  alt="Không ảnh trực giao Đại Nội Huế"
                  fill
                  className="object-cover"
                />
                <div className="absolute inset-0 bg-gradient-to-t from-black/70 via-transparent to-transparent flex items-end p-4">
                  <div className="text-white space-y-1">
                    <span className="text-xs font-semibold flex items-center gap-1.5">
                      <Compass className="size-3.5 text-primary" />
                      Trục Nam - Bắc (Trục Dũng Đạo Hoàng Thành)
                    </span>
                    <p className="text-[11px] opacity-90">
                      Từ Ngọ Môn (Nam) ➔ Cầu Trung Đạo ➔ Sân Đại Triều Nghi ➔ Điện Thái Hòa (Bắc)
                    </p>
                  </div>
                </div>
              </div>

              <div className="flex items-center justify-between pt-2">
                <span className="text-xs text-muted-foreground italic">
                  💡 Hãy ghi nhớ cấu trúc trục trước khi bước vào giải mã manh mối tiếp theo.
                </span>
                <Button
                  onClick={() => handleStageComplete(1, 20)}
                  className="gap-2 bg-primary text-primary-foreground font-semibold text-xs h-9"
                >
                  <span>Hoàn thành & Đi tiếp (5–12p)</span>
                  <ArrowRight className="size-3.5" />
                </Button>
              </div>
            </CardContent>
          </Card>
        )}

        {/* ============================================================== */}
        {/* STAGE 2: 5–12p HERITAGE DETECTIVE CLUE                         */}
        {/* ============================================================== */}
        {currentStage === 2 && (
          <Card className="border border-border/80 shadow-md">
            <CardHeader className="p-5 sm:p-6 border-b border-border/60 bg-muted/20">
              <div className="flex items-center justify-between">
                <Badge className="bg-primary/15 text-primary text-xs">
                  Chặng 2 (5–12 phút)
                </Badge>
                <span className="text-xs text-muted-foreground">Mục tiêu: S1 & S3</span>
              </div>
              <CardTitle className="font-serif text-xl mt-1">
                Giải Mã Manh Mối Thám Tử Di Sản
              </CardTitle>
              <CardDescription className="text-xs sm:text-sm">
                Đọc kỹ câu đố bí mật dưới đây để suy luận ra công trình xuất phát của chuyến khảo sát.
              </CardDescription>
            </CardHeader>

            <CardContent className="p-5 sm:p-6 space-y-5">
              <HeritageDetectiveWidget
                clue={activeClue}
                currentSiteSlug={trail.stops[0]?.monument_slug || "ngo-mon"}
                onClueSolved={(_, pts) => {
                  setClueSolved(true);
                  setEarnedXp((prev) => prev + pts);
                }}
              />

              <div className="flex items-center justify-between pt-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setCurrentStage(1)}
                  className="text-xs gap-1"
                >
                  <ArrowLeft className="size-3.5" />
                  Quay lại chặng 1
                </Button>

                <Button
                  onClick={() => handleStageComplete(2, 30)}
                  className="gap-2 bg-primary text-primary-foreground font-semibold text-xs h-9"
                >
                  <span>Tiếp tục chặng 3 (12–25p)</span>
                  <ArrowRight className="size-3.5" />
                </Button>
              </div>
            </CardContent>
          </Card>
        )}

        {/* ============================================================== */}
        {/* STAGE 3: 12–25p OBSERVE 2 ART DETAILS & READ SOURCES           */}
        {/* ============================================================== */}
        {currentStage === 3 && (
          <Card className="border border-border/80 shadow-md">
            <CardHeader className="p-5 sm:p-6 border-b border-border/60 bg-muted/20">
              <div className="flex items-center justify-between">
                <Badge className="bg-primary/15 text-primary text-xs">
                  Chặng 3 (12–25 phút)
                </Badge>
                <span className="text-xs text-muted-foreground">Mục tiêu: S2 & S3</span>
              </div>
              <CardTitle className="font-serif text-xl mt-1">
                Khảo Sát 2 Chi Tiết Mỹ Thuật & Đối Chiếu Sử Liệu
              </CardTitle>
              <CardDescription className="text-xs sm:text-sm">
                Quan sát các cấu kiện mỹ thuật cung đình và đọc các đoạn trích từ Đại Nam Thực Lục.
              </CardDescription>
            </CardHeader>

            <CardContent className="p-5 sm:p-6 space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
                {activeArtDetails.map((detail, idx) => (
                  <div
                    key={detail.slug}
                    className="rounded-2xl border border-border/80 bg-card p-4 space-y-3 shadow-sm flex flex-col justify-between"
                  >
                    <div className="space-y-2">
                      <div className="flex items-center justify-between">
                        <Badge variant="outline" className="text-[10px] font-semibold">
                          Chi tiết {idx + 1}: {detail.kind}
                        </Badge>
                        <span className="text-xs text-primary font-medium">{detail.motif}</span>
                      </div>

                      <h4 className="font-serif font-bold text-base text-foreground">
                        {detail.title}
                      </h4>

                      <p className="text-xs text-muted-foreground leading-relaxed line-clamp-3">
                        {detail.description_observation}
                      </p>

                      <div className="rounded-xl border border-border/60 bg-muted/30 p-2.5 text-xs text-foreground/90 space-y-1">
                        <strong className="block text-[11px] text-primary">Điển tích & Sự kiện:</strong>
                        <p className="line-clamp-3 italic font-serif opacity-95">
                          {detail.story_body}
                        </p>
                      </div>
                    </div>

                    {detail.claim_sources && detail.claim_sources.length > 0 && (
                      <div className="rounded-lg border border-primary/20 bg-primary/5 p-2 text-[11px] text-muted-foreground flex items-center gap-1.5">
                        <BookOpen className="size-3 text-primary shrink-0" />
                        <span className="truncate">
                          <strong>Sử liệu:</strong> {detail.claim_sources[0].source_title} ({detail.claim_sources[0].source_locator})
                        </span>
                      </div>
                    )}
                  </div>
                ))}
              </div>

              <div className="flex items-center justify-between pt-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setCurrentStage(2)}
                  className="text-xs gap-1"
                >
                  <ArrowLeft className="size-3.5" />
                  Quay lại chặng 2
                </Button>

                <Button
                  onClick={() => handleStageComplete(3, 30)}
                  className="gap-2 bg-primary text-primary-foreground font-semibold text-xs h-9"
                >
                  <span>Chuyển sang chặng 4 (25–35p)</span>
                  <ArrowRight className="size-3.5" />
                </Button>
              </div>
            </CardContent>
          </Card>
        )}

        {/* ============================================================== */}
        {/* STAGE 4: 25–35p COMPARE MEANINGS & REINFORCEMENT QUIZ          */}
        {/* ============================================================== */}
        {currentStage === 4 && (
          <Card className="border border-border/80 shadow-md">
            <CardHeader className="p-5 sm:p-6 border-b border-border/60 bg-muted/20">
              <div className="flex items-center justify-between">
                <Badge className="bg-primary/15 text-primary text-xs">
                  Chặng 4 (25–35 phút)
                </Badge>
                <span className="text-xs text-muted-foreground">Mục tiêu: S4 Lập luận</span>
              </div>
              <CardTitle className="font-serif text-xl mt-1">
                Đối Chiếu Ý Nghĩa & Thử Thách Hiểu Sâu
              </CardTitle>
              <CardDescription className="text-xs sm:text-sm">
                Vận dụng kiến thức quan sát để trả lời câu hỏi lý giải bản chất và ý nghĩa di sản.
              </CardDescription>
            </CardHeader>

            <CardContent className="p-5 sm:p-6 space-y-6">
              <HeritageGames
                siteSlug={trail.stops[0]?.monument_slug || "ngo-mon"}
                onGameComplete={(pts) => setEarnedXp((prev) => prev + pts)}
              />

              <div className="flex items-center justify-between pt-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setCurrentStage(3)}
                  className="text-xs gap-1"
                >
                  <ArrowLeft className="size-3.5" />
                  Quay lại chặng 3
                </Button>

                <Button
                  onClick={() => handleStageComplete(4, 30)}
                  className="gap-2 bg-primary text-primary-foreground font-semibold text-xs h-9"
                >
                  <span>Sang chặng cuối: Nộp Exit Ticket (35–45p)</span>
                  <ArrowRight className="size-3.5" />
                </Button>
              </div>
            </CardContent>
          </Card>
        )}

        {/* ============================================================== */}
        {/* STAGE 5: 35–45p M-E-E CONCLUSION & EXIT TICKET                 */}
        {/* ============================================================== */}
        {currentStage === 5 && (
          <Card className="border border-border/80 shadow-md">
            <CardHeader className="p-5 sm:p-6 border-b border-border/60 bg-muted/20">
              <div className="flex items-center justify-between">
                <Badge className="bg-emerald-600 text-white text-xs">
                  Chặng 5 (35–45 phút)
                </Badge>
                <span className="text-xs text-muted-foreground">Chuẩn Rubric S1–S4</span>
              </div>
              <CardTitle className="font-serif text-xl mt-1">
                Tổng Kết M-E-E & Nộp Bài Exit Ticket
              </CardTitle>
              <CardDescription className="text-xs sm:text-sm">
                Đúc kết nhận thức của bản thân bằng mô hình Mệnh đề (Claim) - Bằng chứng (Evidence) - Diễn giải (Explanation).
              </CardDescription>
            </CardHeader>

            <CardContent className="p-5 sm:p-6 space-y-6">
              <div className="rounded-2xl border border-emerald-500/30 bg-emerald-500/5 p-5 space-y-3">
                <h4 className="font-serif font-bold text-base text-foreground flex items-center gap-2">
                  <FileCheck2 className="size-5 text-emerald-600 dark:text-emerald-400" />
                  <span>Nhiệm vụ đúc kết bài học:</span>
                </h4>
                <p className="text-xs sm:text-sm text-foreground/90 leading-relaxed font-serif">
                  Dựa vào các quan sát ở Ngọ Môn và Điện Thái Hòa cùng tư liệu trích dẫn từ Đại Nam Thực Lục Chính Biên, hãy viết một đoạn lập luận ngắn (150–250 từ) giải thích: <strong>Vì sao trục chính đạo Đại Nội Huế lại được quy hoạch theo trật tự đối xứng nghiêm ngặt hướng về phía Nam?</strong>
                </p>

                <div className="pt-2 flex justify-end">
                  <Button
                    onClick={() => setIsSubmissionOpen(true)}
                    className="gap-2 bg-emerald-600 hover:bg-emerald-700 text-white font-semibold text-xs h-9 shadow-md"
                  >
                    <Send className="size-3.5" />
                    <span>Mở khung nộp bài M-E-E</span>
                  </Button>
                </div>
              </div>

              <div className="flex items-center justify-between pt-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setCurrentStage(4)}
                  className="text-xs gap-1"
                >
                  <ArrowLeft className="size-3.5" />
                  Quay lại chặng 4
                </Button>

                <Button
                  onClick={() => handleStageComplete(5, 50)}
                  disabled={completedStages.includes(5)}
                  className="gap-2 bg-primary text-primary-foreground font-semibold text-xs h-9"
                >
                  <CheckCircle2 className="size-4" />
                  <span>{completedStages.includes(5) ? "Đã hoàn thành toàn bộ hành trình" : "Xác nhận hoàn tất hành trình"}</span>
                </Button>
              </div>
            </CardContent>
          </Card>
        )}
      </main>

      {/* Student Submission Modal */}
      <StudentSubmissionModal
        open={isSubmissionOpen}
        onOpenChange={setIsSubmissionOpen}
        monumentSlug={trail.stops[0]?.monument_slug || "ngo-mon"}
        monumentName={trail.stops[0]?.monument_name_vi || "Ngọ Môn"}
        trailSlug={trail.slug}
        trailTitle={trail.title}
        taskPrompt="Giải thích vì sao trục chính đạo Đại Nội Huế lại được quy hoạch theo trật tự đối xứng nghiêm ngặt hướng về phía Nam dựa trên bằng chứng chính sử triều Nguyễn."
        onSuccess={() => {
          handleStageComplete(5, 50);
          setIsSubmissionOpen(false);
        }}
      />
    </div>
  );
}
