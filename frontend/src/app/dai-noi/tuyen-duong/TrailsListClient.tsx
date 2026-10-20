"use client";

import React, { useState } from "react";
import Link from "next/link";
import Image from "next/image";
import {
  ArrowRight,
  BookOpen,
  Calendar,
  Camera,
  CheckCircle2,
  Clock,
  Compass,
  Footprints,
  GraduationCap,
  Layers,
  MapPin,
  Route,
  ShieldCheck,
  Sparkles,
  Target,
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { IMPERIAL_TRAILS } from "@/lib/imperial/trails-data";

const TRAIL_COVER_IMAGES: Record<string, string> = {
  "truc-dung-dao-quyen-luc": "/assets/imperial/heritage/dainoihue.jpg",
  "khong-gian-ky-uc-tuong-niem": "/assets/imperial/heritage/dainoi.jpg",
  "tu-cam-thanh-bien-doi-phuc-hoi": "/assets/imperial/heritage/dienkientrung.jpg",
  "doi-song-cung-dinh-dien-tho": "/assets/imperial/heritage/truongduta.jpg",
};

export default function TrailsListClient() {
  const [filterSlug, setFilterSlug] = useState<string>("all");

  const filteredTrails = filterSlug === "all"
    ? IMPERIAL_TRAILS
    : IMPERIAL_TRAILS.filter((t) => t.slug === filterSlug);

  return (
    <div className="min-h-screen bg-background">
      {/* Hero Header */}
      <section className="relative overflow-hidden border-b border-border/70 bg-secondary/30 py-12 md:py-16">
        <div className="absolute inset-0 bg-radial-gradient pointer-events-none opacity-40" />
        <div className="mx-auto max-w-7xl px-4 lg:px-8 relative z-10">
          <div className="max-w-3xl space-y-4">
            <div className="flex flex-wrap items-center gap-2">
              <Badge variant="outline" className="border-primary/40 bg-primary/10 text-primary text-xs font-semibold py-1 px-3 gap-1.5">
                <Footprints className="h-3.5 w-3.5" />
                Học tập thực địa & Khám phá ảo
              </Badge>
              <Badge variant="secondary" className="text-xs font-medium">
                Khung năng lực GDPT 2018 • Rubric S1-S4
              </Badge>
            </div>

            <h1 className="font-serif text-3xl font-extrabold tracking-tight text-foreground md:text-5xl">
              Tuyến Đường Khảo Sát Lịch Sử Đại Nội
            </h1>

            <p className="text-sm leading-relaxed text-muted-foreground md:text-base">
              Hành trình học tập di sản có định hướng tại Hoàng Thành và Tử Cấm Thành Huế.
              Học sinh đóng vai nhà nghiên cứu lịch sử thực địa: quan sát hiện trường, truy vấn chính sử
              Quốc Sử Quán triều Nguyễn, và giải quyết câu hỏi phát vấn theo quy trình <strong>M-E-E</strong> (Mệnh đề — Bằng chứng — Diễn giải).
            </p>

            <div className="flex flex-wrap items-center gap-3 pt-2">
              <Button asChild className="gap-2 font-semibold">
                <Link href={`/dai-noi/tuyen-duong/${IMPERIAL_TRAILS[0].slug}`}>
                  <Route className="h-4 w-4" />
                  Bắt đầu Tuyến 1: Trục Dũng Đạo
                </Link>
              </Button>
              <Button asChild variant="outline" className="gap-2">
                <Link href="/dai-noi/giao-vien">
                  <GraduationCap className="h-4 w-4 text-primary" />
                  Bảng Đánh Giá Giáo Viên (Rubric S1-S4)
                </Link>
              </Button>
            </div>
          </div>
        </div>
      </section>

      {/* Main Content Area */}
      <div className="mx-auto max-w-7xl px-4 py-8 md:py-12 lg:px-8 space-y-10">
        {/* Filter bar */}
        <div className="flex flex-wrap items-center justify-between gap-4 border-b border-border/60 pb-4">
          <div className="flex items-center gap-2">
            <Route className="h-5 w-5 text-primary" />
            <span className="font-serif text-lg font-bold text-foreground">
              4 Tuyến học tập chuyên đề
            </span>
            <span className="text-xs text-muted-foreground">({IMPERIAL_TRAILS.length} lộ trình)</span>
          </div>

          <div className="flex flex-wrap gap-1.5">
            <Button
              variant={filterSlug === "all" ? "default" : "outline"}
              size="sm"
              onClick={() => setFilterSlug("all")}
              className="text-xs rounded-full h-8 px-3"
            >
              Tất cả tuyến
            </Button>
            {IMPERIAL_TRAILS.map((trail) => (
              <Button
                key={trail.slug}
                variant={filterSlug === trail.slug ? "default" : "outline"}
                size="sm"
                onClick={() => setFilterSlug(trail.slug)}
                className="text-xs rounded-full h-8 px-3"
              >
                {trail.title.split("&")[0].trim()}
              </Button>
            ))}
          </div>
        </div>

        {/* Trail Cards Grid */}
        <div className="grid grid-cols-1 gap-8 lg:grid-cols-2">
          {filteredTrails.map((trail, index) => {
            const coverSrc = TRAIL_COVER_IMAGES[trail.slug] || "/assets/imperial/maps/dai-noi-aerial-v1.webp";

            return (
              <Card
                key={trail.slug}
                className="flex flex-col overflow-hidden border border-border/80 bg-card hover:border-primary/50 hover:shadow-lg transition-all duration-200 rounded-2xl group"
              >
                {/* Visual Cover Banner */}
                <div className="relative aspect-[21/9] sm:aspect-[24/9] w-full overflow-hidden bg-neutral-950">
                  <Image
                    src={coverSrc}
                    alt={trail.title}
                    fill
                    className="object-cover group-hover:scale-105 transition-transform duration-500 opacity-90"
                    sizes="(max-width: 1024px) 100vw, 50vw"
                  />
                  <div className="absolute inset-0 bg-gradient-to-t from-black/85 via-black/25 to-black/20 pointer-events-none" />

                  {/* Top Badges */}
                  <div className="absolute top-3 left-3 flex items-center gap-2">
                    <Badge className="font-mono text-[10px] font-bold bg-amber-500 text-stone-950 shadow">
                      Tuyến số {index + 1}
                    </Badge>
                    <span className="rounded-md bg-black/70 backdrop-blur-md px-2 py-0.5 text-[10px] font-mono text-white/90 shadow border border-white/10">
                      {trail.difficulty}
                    </span>
                  </div>

                  {/* Bottom Image Overlay Title */}
                  <div className="absolute bottom-3 left-4 right-4 text-white pointer-events-none space-y-0.5">
                    <span className="text-[10px] font-serif italic text-amber-300 drop-shadow block">
                      {trail.subtitle}
                    </span>
                    <h3 className="font-serif text-lg sm:text-xl font-bold text-white drop-shadow line-clamp-1">
                      {trail.title}
                    </h3>
                  </div>
                </div>

                <CardHeader className="p-6 pb-3 space-y-2">
                  <div className="flex items-center justify-between text-xs text-muted-foreground border-b border-border/50 pb-2.5">
                    <span className="flex items-center gap-1 font-medium">
                      <Clock className="h-3.5 w-3.5 text-primary" />
                      {trail.duration_minutes} phút
                    </span>
                    <span className="flex items-center gap-1 font-medium">
                      <MapPin className="h-3.5 w-3.5 text-primary" />
                      {trail.stops.length} trạm dừng
                    </span>
                    <span className="flex items-center gap-1 font-medium">
                      <GraduationCap className="h-3.5 w-3.5 text-primary" />
                      {trail.target_grade}
                    </span>
                  </div>
                </CardHeader>

              <CardContent className="flex-1 p-6 space-y-5">
                <p className="text-xs leading-relaxed text-muted-foreground">
                  {trail.description}
                </p>

                {/* Stepper Roadmap Ribbon */}
                <div className="space-y-2">
                  <div className="flex items-center justify-between text-[11px] font-bold uppercase tracking-wider text-muted-foreground">
                    <span>Lộ trình di chuyển ({trail.stops.length} di tích):</span>
                  </div>
                  <div className="rounded-xl border border-border/60 bg-secondary/25 p-3">
                    <div className="flex flex-wrap items-center gap-2 text-xs font-semibold text-foreground">
                      {trail.stops.map((stop, sIdx) => (
                        <React.Fragment key={stop.monument_slug}>
                          <span className="inline-flex items-center gap-1.5 rounded-lg bg-background px-2.5 py-1 border border-border/70 shadow-2xs">
                            <span className="flex h-4 w-4 items-center justify-center rounded-full bg-primary/15 text-[10px] font-bold text-primary">
                              {sIdx + 1}
                            </span>
                            <span>{stop.monument_name_vi}</span>
                          </span>
                          {sIdx < trail.stops.length - 1 && (
                            <ArrowRight className="h-3.5 w-3.5 text-muted-foreground/60 shrink-0" />
                          )}
                        </React.Fragment>
                      ))}
                    </div>
                  </div>
                </div>

                {/* Pedagogical Objectives */}
                <div className="space-y-2">
                  <div className="flex items-center gap-1.5 text-xs font-bold text-foreground">
                    <Target className="h-3.5 w-3.5 text-primary" />
                    <span>Mục tiêu năng lực sư phạm:</span>
                  </div>
                  <ul className="space-y-1.5 text-xs text-muted-foreground">
                    {trail.pedagogical_objectives.map((obj, oIdx) => (
                      <li key={oIdx} className="flex items-start gap-2 leading-relaxed">
                        <CheckCircle2 className="h-3.5 w-3.5 text-emerald-600 dark:text-emerald-400 shrink-0 mt-0.5" />
                        <span>{obj}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              </CardContent>

              <CardFooter className="p-6 pt-3 border-t border-border/60 bg-secondary/10 flex items-center justify-between gap-3">
                <span className="text-[11px] text-muted-foreground">
                  Chế độ: Thực địa hiện trường hoặc Phòng học ảo
                </span>
                <Button asChild size="sm" className="gap-2 font-semibold">
                  <Link href={`/dai-noi/tuyen-duong/${trail.slug}`}>
                    <span>Bắt đầu khảo sát</span>
                    <ArrowRight className="h-4 w-4" />
                  </Link>
                </Button>
              </CardFooter>
            </Card>
          );
        })}
        </div>

        {/* Pedagogical Methodology Banner */}
        <section className="rounded-3xl border border-primary/30 bg-primary/5 p-6 md:p-10 space-y-6">
          <div className="flex items-center gap-3">
            <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-primary/15 text-primary">
              <ShieldCheck className="h-6 w-6" />
            </div>
            <div>
              <h2 className="font-serif text-xl font-bold text-foreground md:text-2xl">
                Khung Phương Pháp Khảo Sát Lịch Sử: M-E-E & Rubric S1-S4
              </h2>
              <p className="text-xs text-muted-foreground">
                Được phát triển bám sát chuẩn đánh giá phẩm chất và năng lực lịch sử của Bộ GD&ĐT
              </p>
            </div>
          </div>

          <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-4">
            <div className="rounded-xl border border-border/70 bg-card p-4 space-y-1.5">
              <Badge className="bg-blue-500/10 text-blue-700 dark:text-blue-300 border-blue-500/20 text-[11px]">
                S1 • Năng lực Không gian
              </Badge>
              <p className="text-xs text-muted-foreground leading-relaxed">
                Đọc bản đồ trực giao, xác định trục Dũng Đạo, định vị hướng nhìn và phân tích trật tự phân tầng không gian phong kiến.
              </p>
            </div>

            <div className="rounded-xl border border-border/70 bg-card p-4 space-y-1.5">
              <Badge className="bg-amber-500/10 text-amber-700 dark:text-amber-300 border-amber-500/20 text-[11px]">
                S2 • Năng lực Thời gian
              </Badge>
              <p className="text-xs text-muted-foreground leading-relaxed">
                Đặt di tích vào dòng chảy lịch sử: khởi dựng thời Gia Long - Minh Mạng, biến chuyển thời Khải Định, tàn phá chiến tranh và phục hồi hôm nay.
              </p>
            </div>

            <div className="rounded-xl border border-border/70 bg-card p-4 space-y-1.5">
              <Badge className="bg-emerald-500/10 text-emerald-700 dark:text-emerald-300 border-emerald-500/20 text-[11px]">
                S3 • Năng lực Sử liệu
              </Badge>
              <p className="text-xs text-muted-foreground leading-relaxed">
                Khai thác chính ngạch: Đại Nam Thực Lục, Hội Điển Sự Lệ, bia ký, hoành phi và tư liệu ảnh lưu trữ Pháp, ảnh viễn thám.
              </p>
            </div>

            <div className="rounded-xl border border-border/70 bg-card p-4 space-y-1.5">
              <Badge className="bg-purple-500/10 text-purple-700 dark:text-purple-300 border-purple-500/20 text-[11px]">
                S4 • Năng lực Lập luận
              </Badge>
              <p className="text-xs text-muted-foreground leading-relaxed">
                Cấu trúc câu trả lời theo công thức M-E-E: <strong>Mệnh đề (Claim)</strong> rõ ràng, <strong>Bằng chứng (Evidence)</strong> cụ thể, và <strong>Diễn giải (Explanation)</strong> thuyết phục.
              </p>
            </div>
          </div>

          <div className="flex flex-wrap items-center justify-between gap-4 pt-2 border-t border-primary/15">
            <span className="text-xs text-muted-foreground">
              Dành cho giáo viên: Sử dụng hệ thống để giao bài tập thực địa, theo dõi tiến độ và chấm điểm trực tiếp.
            </span>
            <Button asChild variant="outline" size="sm" className="gap-2 font-semibold">
              <Link href="/dai-noi/giao-vien">
                <GraduationCap className="h-4 w-4 text-primary" />
                Vào Bảng Đánh Giá Giáo Viên
              </Link>
            </Button>
          </div>
        </section>
      </div>
    </div>
  );
}
