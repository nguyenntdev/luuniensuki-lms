"use client";

import React, { useState, useEffect, useCallback } from "react";
import Image from "next/image";
import Link from "next/link";
import {
  Compass,
  Route,
  Camera,
  Layers,
  ChevronLeft,
  ChevronRight,
  Sparkles,
  ArrowDown,
  BookOpen,
  Landmark,
  ShieldCheck,
  CheckCircle2,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

interface HeroSlide {
  id: string;
  imageSrc: string;
  title: string;
  tagline: string;
  era: string;
  badge: string;
  slug: string;
}

const HERO_SLIDES: HeroSlide[] = [
  {
    id: "hero-ngo-mon",
    imageSrc: "/assets/imperial/heritage/ngomon.jpg",
    title: "Cổng Ngọ Môn & Lầu Ngũ Phụng",
    tagline: "Nghi môn biểu tượng tối cao của Hoàng Thành Huế — nơi diễn ra lễ Ban Sóc và Truyền Loa tiến sĩ",
    era: "Khởi dựng: Minh Mạng thứ 14 (1833)",
    badge: "Tiền tiêu Trục Dũng Đạo",
    slug: "ngo-mon",
  },
  {
    id: "hero-thai-hoa",
    imageSrc: "/assets/imperial/heritage/dienthaihoa.jpg",
    title: "Điện Thái Hòa — Trùng Thiềm Điệp Ốc",
    tagline: "Trái tim vương quyền triều Nguyễn, bảo tồn 80 cột gỗ lim dát vàng và thi văn 'nhất thi nhất họa'",
    era: "Khởi dựng: Gia Long năm 1805 • Đại trùng tu 2025",
    badge: "Chính điện thiết Đại triều",
    slug: "dien-thai-hoa",
  },
  {
    id: "hero-kien-trung",
    imageSrc: "/assets/imperial/heritage/dienkientrung.jpg",
    title: "Điện Kiến Trung — Đỉnh Cao Khảm Sành Sứ",
    tagline: "Cung điện giao thoa kiến trúc Phục hưng Ý, cổ điển Pháp và nghệ thuật đắp nổi gốm sứ Cung đình",
    era: "Khởi dựng: Khải Định năm 1923 • Phục hồi 2023",
    badge: "Cung điện Hoàng gia",
    slug: "dien-kien-trung",
  },
  {
    id: "hero-dien-tho",
    imageSrc: "/assets/imperial/heritage/truongduta.jpg",
    title: "Tạ Trường Du — Cung Diên Thọ",
    tagline: "Nhà thủy tạ thanh bình bên hồ sen, nơi các bậc Hoàng Thái Hậu ngắm hoa, thưởng trà và tĩnh dưỡng",
    era: "Khởi dựng: Tự Đức năm 1849",
    badge: "Không gian sinh hoạt Mẫu nghi",
    slug: "cung-dien-tho",
  },
];

interface ImperialCinematicHeroProps {
  onExploreMap?: () => void;
  className?: string;
}

export function ImperialCinematicHero({
  onExploreMap,
  className = "",
}: ImperialCinematicHeroProps) {
  const [currentSlideIndex, setCurrentSlideIndex] = useState(0);
  const [isPaused, setIsPaused] = useState(false);

  const handleNextSlide = useCallback(() => {
    setCurrentSlideIndex((prev) => (prev + 1) % HERO_SLIDES.length);
  }, []);

  const handlePrevSlide = useCallback(() => {
    setCurrentSlideIndex((prev) => (prev - 1 + HERO_SLIDES.length) % HERO_SLIDES.length);
  }, []);

  // Auto-advance slides every 6 seconds unless paused by mouse hover
  useEffect(() => {
    if (isPaused) return;
    const interval = setInterval(handleNextSlide, 6500);
    return () => clearInterval(interval);
  }, [isPaused, handleNextSlide]);

  const activeSlide = HERO_SLIDES[currentSlideIndex];

  return (
    <section
      aria-label="Màn chào di sản Đại Nội Huế"
      className={cn(
        "relative w-full overflow-hidden rounded-3xl border-2 border-[#8E2323]/50 shadow-2xl bg-neutral-950 mb-8",
        className,
      )}
      onMouseEnter={() => setIsPaused(true)}
      onMouseLeave={() => setIsPaused(false)}
    >
      {/* Decorative Traditional Hue Imperial Corner Ornaments (Triện góc hoàng triều) */}
      <span className="pointer-events-none absolute top-3 left-3 h-5 w-5 border-t-2 border-l-2 border-[#D4AF37] z-20" />
      <span className="pointer-events-none absolute top-3 right-3 h-5 w-5 border-t-2 border-r-2 border-[#D4AF37] z-20" />
      <span className="pointer-events-none absolute bottom-3 left-3 h-5 w-5 border-b-2 border-l-2 border-[#D4AF37] z-20" />
      <span className="pointer-events-none absolute bottom-3 right-3 h-5 w-5 border-b-2 border-r-2 border-[#D4AF37] z-20" />

      {/* Main Slideshow Stage */}
      <div className="relative aspect-[16/10] sm:aspect-[21/9] lg:aspect-[24/9] min-h-[380px] sm:min-h-[440px] w-full overflow-hidden select-none">
        {HERO_SLIDES.map((slide, idx) => {
          const isActive = idx === currentSlideIndex;
          return (
            <div
              key={slide.id}
              className={cn(
                "absolute inset-0 transition-opacity duration-1000 ease-in-out",
                isActive ? "opacity-100 z-10 scale-100" : "opacity-0 z-0 pointer-events-none",
              )}
            >
              <Image
                src={slide.imageSrc}
                alt={slide.title}
                fill
                className="object-cover object-center transition-transform duration-7000 ease-linear transform scale-105"
                sizes="100vw"
                priority={idx === 0}
              />
            </div>
          );
        })}

        {/* Imperial Vignette & Atmosphere Gradient (Đỏ đô trầm bordeaux sang tối) */}
        <div className="absolute inset-0 bg-gradient-to-r from-[#3B0A0A]/95 via-[#5C1010]/85 to-black/40 z-10 pointer-events-none" />
        <div className="absolute inset-0 bg-gradient-to-t from-black/85 via-transparent to-black/30 z-10 pointer-events-none" />

        {/* Content Overlay */}
        <div className="relative z-20 h-full flex flex-col justify-between p-6 sm:p-8 lg:p-12 max-w-4xl text-white">
          {/* Top Tagline Row */}
          <div className="flex flex-wrap items-center gap-2.5">
            <span className="inline-flex items-center gap-1.5 rounded-full border border-[#D4AF37]/50 bg-[#6B1414]/85 backdrop-blur-md px-3 py-1 text-xs font-bold text-[#FDF8EE] shadow-md">
              <Sparkles className="h-3.5 w-3.5 text-[#D4AF37]" />
              Đại Nội Hoàng Thành — Lưu Niên Di Sản
            </span>
            <span className="rounded-full bg-black/60 backdrop-blur-md px-2.5 py-1 text-xs font-mono font-medium text-[#D4AF37] border border-[#D4AF37]/30">
              {activeSlide.badge}
            </span>
          </div>

          {/* Main Title & Driving Description */}
          <div className="space-y-3.5 my-auto py-4">
            <h1 className="font-serif text-2xl sm:text-4xl lg:text-5xl font-black tracking-tight text-white leading-tight drop-shadow-md">
              {activeSlide.title}
            </h1>
            <p className="font-serif italic text-xs sm:text-sm lg:text-base text-[#FDF8EE]/90 leading-relaxed max-w-2xl drop-shadow">
              &ldquo;{activeSlide.tagline}&rdquo;
            </p>
            <div className="flex items-center gap-2 text-xs text-[#D4AF37] font-mono">
              <Landmark className="h-3.5 w-3.5 shrink-0" />
              <span>{activeSlide.era}</span>
            </div>
          </div>

          {/* Bottom CTAs & Stat Counters */}
          <div className="space-y-4 pt-2">
            <div className="flex flex-wrap items-center gap-3">
              <Button
                type="button"
                onClick={onExploreMap}
                className="h-10 px-5 text-xs font-bold gap-2 rounded-xl bg-[#C68A2C] hover:bg-[#D4AF37] text-stone-950 shadow-lg border border-amber-300/40"
              >
                <Compass className="h-4 w-4" />
                <span>Mở bản đồ không ảnh Đại Nội</span>
                <ArrowDown className="h-3.5 w-3.5" />
              </Button>

              <Button
                asChild
                className="h-10 px-4 text-xs font-semibold gap-2 rounded-xl bg-[#851C1C] hover:bg-[#A62B2B] text-white shadow-md border border-red-500/30"
              >
                <Link href="/dai-noi/tuyen-duong/truc-dung-dao-quyen-luc">
                  <Route className="h-4 w-4" />
                  <span>Khảo sát Tuyến Dũng Đạo</span>
                </Link>
              </Button>

              <Button
                asChild
                variant="outline"
                className="h-10 px-4 text-xs font-medium gap-2 rounded-xl bg-black/50 text-[#FDF8EE] hover:bg-black/80 border-white/20 backdrop-blur-md"
              >
                <Link href="/dai-noi/thu-vien-anh">
                  <Camera className="h-4 w-4 text-[#D4AF37]" />
                  <span>Kho 27 ảnh di sản</span>
                </Link>
              </Button>
            </div>

            {/* Quick Metrics Bar */}
            <div className="flex flex-wrap items-center gap-y-1 gap-x-6 text-[11px] text-[#FDF8EE]/80 pt-1 border-t border-white/15">
              <span>🏛️ <strong>16</strong> Công trình kiến trúc</span>
              <span>🧭 <strong>4</strong> Cụm không gian quyền lực</span>
              <span>📸 <strong>27</strong> Tư liệu ảnh thực tế</span>
              <span>📜 <strong>10</strong> Bộ sử liệu Quốc Sử Quán</span>
            </div>
          </div>
        </div>

        {/* Slide Controls (Arrows & Dot Indicators) */}
        <div className="absolute right-4 bottom-4 z-20 flex items-center gap-2">
          {/* Thumbnail Preview Buttons */}
          <div className="hidden sm:flex items-center gap-1.5 mr-2">
            {HERO_SLIDES.map((slide, idx) => (
              <button
                key={slide.id}
                type="button"
                onClick={() => setCurrentSlideIndex(idx)}
                className={cn(
                  "relative h-10 w-14 rounded-lg overflow-hidden border-2 transition-all",
                  idx === currentSlideIndex
                    ? "border-[#D4AF37] scale-110 shadow-md ring-2 ring-[#D4AF37]/50"
                    : "border-white/30 opacity-60 hover:opacity-100",
                )}
                title={slide.title}
              >
                <Image
                  src={slide.imageSrc}
                  alt={slide.title}
                  fill
                  className="object-cover"
                  sizes="60px"
                />
              </button>
            ))}
          </div>

          <button
            type="button"
            onClick={handlePrevSlide}
            className="flex h-8 w-8 items-center justify-center rounded-lg bg-black/60 text-white hover:bg-[#851C1C] transition-colors border border-white/20 backdrop-blur-md"
            title="Ảnh trước"
          >
            <ChevronLeft className="h-4 w-4" />
          </button>
          <button
            type="button"
            onClick={handleNextSlide}
            className="flex h-8 w-8 items-center justify-center rounded-lg bg-black/60 text-white hover:bg-[#851C1C] transition-colors border border-white/20 backdrop-blur-md"
            title="Ảnh kế tiếp"
          >
            <ChevronRight className="h-4 w-4" />
          </button>
        </div>
      </div>
    </section>
  );
}
