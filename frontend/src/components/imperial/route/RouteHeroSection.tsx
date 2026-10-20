"use client";

import React from "react";
import Link from "next/link";
import Image from "next/image";
import {
  Compass,
  Clock,
  GraduationCap,
  Sparkles,
  HelpCircle,
  FileText,
  MapPin,
  CheckCircle2,
  ChevronRight,
  BookOpen,
  Camera,
  AlertCircle,
  Info,
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import type { ImperialTrail } from "@/lib/imperial/map-types";

interface RouteHeroSectionProps {
  trail: ImperialTrail;
  completedStopsCount: number;
  onOpenGuide: () => void;
  onOpenImageReport: () => void;
}

export function RouteHeroSection({
  trail,
  completedStopsCount,
  onOpenGuide,
  onOpenImageReport,
}: RouteHeroSectionProps) {
  const totalStops = trail.stops.length;
  const progressPercent = Math.round((completedStopsCount / (totalStops || 1)) * 100);

  return (
    <div className="relative overflow-hidden rounded-3xl border border-border/80 bg-gradient-to-b from-card via-background to-background p-6 shadow-sm md:p-8 lg:p-10 mb-8">
      {/* Decorative Traditional Hue Imperial Corner Ornaments */}
      <span className="pointer-events-none absolute top-3 left-3 h-4 w-4 border-t-2 border-l-2 border-primary/40" />
      <span className="pointer-events-none absolute top-3 right-3 h-4 w-4 border-t-2 border-r-2 border-primary/40" />
      <span className="pointer-events-none absolute bottom-3 left-3 h-4 w-4 border-b-2 border-l-2 border-primary/40" />
      <span className="pointer-events-none absolute bottom-3 right-3 h-4 w-4 border-b-2 border-r-2 border-primary/40" />

      {/* Subtle background imperial texture */}
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-amber-500/5 via-transparent to-transparent pointer-events-none" />

      <div className="relative z-10 flex flex-col gap-6 lg:flex-row lg:items-center lg:justify-between">
        {/* Left column: Title & Pedagogical Scope */}
        <div className="space-y-4 max-w-3xl">
          {/* Badge Group */}
          <div className="flex flex-wrap items-center gap-2">
            <span className="inline-flex items-center gap-1.5 rounded-full border border-amber-500/30 bg-amber-500/10 px-3 py-1 text-xs font-semibold text-amber-700 dark:text-amber-400">
              <Compass className="h-3.5 w-3.5" />
              Tuyến Khảo Sát Di Sản Thực Địa • GDPT 2018
            </span>
            <Badge variant="outline" className="text-xs font-mono">
              Trục Thần Đạo Nam - Bắc
            </Badge>
            <span className="inline-flex items-center gap-1 rounded-full bg-emerald-500/10 border border-emerald-500/30 px-2.5 py-0.5 text-xs font-medium text-emerald-700 dark:text-emerald-400">
              <CheckCircle2 className="h-3 w-3" />
              {completedStopsCount}/{totalStops} Trạm hoàn thành ({progressPercent}%)
            </span>
          </div>

          {/* Main Title & Subtitle */}
          <div>
            <h1 className="font-display text-2xl sm:text-3xl lg:text-4xl font-extrabold tracking-tight text-foreground">
              {trail.title}
            </h1>
            <p className="mt-2 text-sm sm:text-base font-serif italic text-muted-foreground leading-relaxed">
              &ldquo;{trail.subtitle}&rdquo;
            </p>
          </div>

          <p className="text-xs sm:text-sm text-foreground/80 leading-relaxed">
            {trail.description}
          </p>

          {/* Quick Info Grid */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 pt-2 text-xs border-t border-border/50 text-muted-foreground">
            <div className="flex items-center gap-2">
              <Clock className="h-4 w-4 text-primary shrink-0" />
              <div>
                <span className="block text-[10px] uppercase font-semibold text-muted-foreground/80">Thời lượng</span>
                <strong className="text-foreground">{trail.duration_minutes} Phút</strong>
              </div>
            </div>

            <div className="flex items-center gap-2">
              <MapPin className="h-4 w-4 text-primary shrink-0" />
              <div>
                <span className="block text-[10px] uppercase font-semibold text-muted-foreground/80">Quy mô</span>
                <strong className="text-foreground">{totalStops} Trạm dừng</strong>
              </div>
            </div>

            <div className="flex items-center gap-2">
              <GraduationCap className="h-4 w-4 text-primary shrink-0" />
              <div>
                <span className="block text-[10px] uppercase font-semibold text-muted-foreground/80">Đối tượng</span>
                <strong className="text-foreground">Lớp 10 - 12</strong>
              </div>
            </div>

            <div className="flex items-center gap-2">
              <FileText className="h-4 w-4 text-primary shrink-0" />
              <div>
                <span className="block text-[10px] uppercase font-semibold text-muted-foreground/80">Đầu ra bài học</span>
                <strong className="text-foreground">Exit Ticket M-E-E</strong>
              </div>
            </div>
          </div>
        </div>

        {/* Right column: Action Controls & Guide Trigger */}
        <div className="flex flex-col sm:flex-row lg:flex-col gap-2.5 shrink-0 justify-center">
          <Button
            type="button"
            onClick={onOpenGuide}
            variant="default"
            className="h-10 px-4 text-xs font-semibold gap-2 rounded-xl shadow-sm bg-primary text-primary-foreground hover:bg-primary/90"
          >
            <HelpCircle className="h-4 w-4" />
            <span>Hướng dẫn lộ trình (4 bước)</span>
          </Button>

          <Button
            type="button"
            onClick={onOpenImageReport}
            variant="outline"
            className="h-10 px-4 text-xs font-semibold gap-2 rounded-xl border-border/80 hover:bg-secondary/70"
          >
            <Camera className="h-4 w-4 text-primary" />
            <span>Báo cáo tư liệu ảnh di sản</span>
          </Button>

          <Button
            asChild
            variant="ghost"
            size="sm"
            className="h-9 px-3 text-xs gap-1.5 text-muted-foreground hover:text-foreground justify-center"
          >
            <Link href="/dai-noi/thu-vien-anh">
              <BookOpen className="h-3.5 w-3.5" />
              <span>Xem toàn bộ 27 ảnh di sản</span>
              <ChevronRight className="h-3.5 w-3.5 opacity-60" />
            </Link>
          </Button>
        </div>
      </div>
    </div>
  );
}
