"use client";

import React, { useState } from "react";
import Link from "next/link";
import {
  Award,
  BookOpen,
  Compass,
  Crosshair,
  GraduationCap,
  HelpCircle,
  Layers,
  Link as LinkIcon,
  MapPin,
  Route,
  Search,
  Sparkles,
  Trophy,
} from "lucide-react";
import ImperialHeader from "@/components/imperial/shell/ImperialHeader";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { HeritageGames } from "@/components/imperial/games/HeritageGames";
import { HeritageDetectiveModal } from "@/components/imperial/detective/HeritageDetectiveModal";

export default function GamesPageClient() {
  const [isDetectiveModalOpen, setIsDetectiveModalOpen] = useState(false);
  const [totalXpEarned, setTotalXpEarned] = useState(0);

  const handleGameComplete = (score: number) => {
    setTotalXpEarned((prev) => prev + score);
  };

  return (
    <div className="min-h-screen bg-background flex flex-col selection:bg-primary/20 selection:text-primary">
      <ImperialHeader />

      <main className="flex-1 max-w-6xl w-full mx-auto px-4 py-8 sm:px-6 space-y-8">
        {/* Hero Banner */}
        <div className="rounded-3xl border border-border/80 bg-gradient-to-br from-card via-card/90 to-primary/5 p-6 sm:p-8 shadow-xl space-y-4">
          <div className="flex flex-wrap items-center justify-between gap-4">
            <div className="space-y-1.5 max-w-2xl">
              <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-primary/10 text-primary border border-primary/20">
                <Sparkles className="size-3.5" />
                <span>Trò Chơi Tương Tác Lịch Sử & Đánh Giá Năng Lực (SPEC V5.1)</span>
              </div>
              <h1 className="font-serif font-bold text-2xl sm:text-4xl text-foreground">
                Đấu Trường Di Sản Đại Nội Huế
              </h1>
              <p className="text-xs sm:text-sm text-muted-foreground leading-relaxed">
                Hệ thống 4 trò chơi tương tác giáo dục chuẩn hóa theo khung năng lực lịch sử: <strong>Trắc nghiệm di sản</strong> (Hiểu sâu &ldquo;Vì sao&rdquo;), <strong>Thám tử cổ vật</strong> (Giải mã manh mối), <strong>Sắp xếp niên biểu</strong> (Dòng thời gian biến thiên), và <strong>Giải mã mật mã cung đình</strong> (Thơ văn & hoành phi ngự chế). Mọi thử thách đều có giải thích sư phạm và trích dẫn chính sử triều Nguyễn.
              </p>
            </div>

            <div className="flex flex-wrap items-center gap-2.5">
              <Button
                onClick={() => setIsDetectiveModalOpen(true)}
                className="gap-2 bg-primary text-primary-foreground shadow-md font-semibold text-xs h-9"
              >
                <Compass className="size-4" />
                <span>Thám tử di sản (Manh mối)</span>
              </Button>

              <Link href="/dai-noi/tuyen-duong">
                <Button variant="outline" size="sm" className="gap-2 text-xs h-9">
                  <Route className="size-4" />
                  <span>Tuyến học 45 phút</span>
                </Button>
              </Link>
            </div>
          </div>

          {/* Quick Metrics */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 pt-4 border-t border-border/60">
            <div className="p-3 rounded-xl bg-background/60 border border-border/60">
              <span className="text-[10px] uppercase font-bold text-muted-foreground tracking-wider block">
                Năng lực S1 (Không gian)
              </span>
              <span className="text-xs font-semibold text-foreground flex items-center gap-1 mt-0.5">
                <Crosshair className="size-3.5 text-primary" />
                Định vị cấu kiện chuẩn xác
              </span>
            </div>
            <div className="p-3 rounded-xl bg-background/60 border border-border/60">
              <span className="text-[10px] uppercase font-bold text-muted-foreground tracking-wider block">
                Năng lực S2 (Thời gian)
              </span>
              <span className="text-xs font-semibold text-foreground flex items-center gap-1 mt-0.5">
                <GraduationCap className="size-3.5 text-amber-500" />
                Niên đại & Biến thiên di sản
              </span>
            </div>
            <div className="p-3 rounded-xl bg-background/60 border border-border/60">
              <span className="text-[10px] uppercase font-bold text-muted-foreground tracking-wider block">
                Năng lực S3 (Sử liệu)
              </span>
              <span className="text-xs font-semibold text-foreground flex items-center gap-1 mt-0.5">
                <BookOpen className="size-3.5 text-blue-500" />
                Thực Lục & Hội Điển Sự Lệ
              </span>
            </div>
            <div className="p-3 rounded-xl bg-background/60 border border-border/60">
              <span className="text-[10px] uppercase font-bold text-muted-foreground tracking-wider block">
                Năng lực S4 (Lập luận)
              </span>
              <span className="text-xs font-semibold text-foreground flex items-center gap-1 mt-0.5">
                <Trophy className="size-3.5 text-emerald-500" />
                Lập luận M-E-E & Giải thích vì sao
              </span>
            </div>
          </div>
        </div>

        {/* Interactive Games Main Component */}
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="font-serif font-bold text-xl text-foreground flex items-center gap-2">
              <Award className="size-5 text-amber-500" />
              <span>Thử Thách Đang Kích Hoạt</span>
            </h2>
            <Badge variant="outline" className="text-xs font-medium">
              4 mini-game tương tác chuẩn hóa
            </Badge>
          </div>

          <HeritageGames onGameComplete={handleGameComplete} />
        </div>
      </main>

      {/* Heritage Detective Full Clue Modal */}
      <HeritageDetectiveModal
        open={isDetectiveModalOpen}
        onOpenChange={setIsDetectiveModalOpen}
      />
    </div>
  );
}
