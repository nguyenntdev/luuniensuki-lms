"use client";

/**
 * JourneyHub — surfaces the main learning journeys as rich, tappable cards on
 * the dashboard so students can jump straight into the 3D explorer, the live AI
 * teacher, the 360° tour, or a practice session.
 */

import Link from "next/link";
import { Compass, Sparkles, Globe, Brain, ArrowRight } from "lucide-react";
import type { LucideIcon } from "lucide-react";

interface Journey {
  href: string;
  icon: LucideIcon;
  title: string;
  desc: string;
  tint: string;
}

const JOURNEYS: Journey[] = [
  {
    href: "/explore",
    icon: Compass,
    title: "Khám phá Cửu Đỉnh 3D",
    desc: "Xoay mô hình, mở từng họa tiết",
    tint: "from-amber-500/18 to-amber-500/5 text-amber-300",
  },
  {
    href: "/ai",
    icon: Sparkles,
    title: "Lớp cùng Cô giáo AI",
    desc: "Hỏi đáp giọng nói, có avatar",
    tint: "from-sky-500/18 to-sky-500/5 text-sky-300",
  },
  {
    href: "/vr360",
    icon: Globe,
    title: "Tham quan ảo 360°",
    desc: "Đi dạo Hoàng thành Huế",
    tint: "from-emerald-500/18 to-emerald-500/5 text-emerald-300",
  },
  {
    href: "/practice",
    icon: Brain,
    title: "Ôn tập nhanh",
    desc: "Phiên ngắn theo trí nhớ",
    tint: "from-violet-500/18 to-violet-500/5 text-violet-300",
  },
];

export default function JourneyHub() {
  return (
    <section className="mt-5" aria-label="Khám phá nhanh">
      <div className="mb-3 flex items-baseline justify-between">
        <h2 className="font-display text-lg font-semibold text-foreground">Khám phá nhanh</h2>
        <span className="text-xs text-muted-foreground">Chọn một trải nghiệm để bắt đầu</span>
      </div>
      <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
        {JOURNEYS.map((j) => {
          const Icon = j.icon;
          return (
            <Link
              key={j.href}
              href={j.href}
              className="group hover-lift focus-card relative flex flex-col gap-3 p-4 outline-none focus-visible:ring-2 focus-visible:ring-primary"
            >
              <span
                className={`grid h-11 w-11 place-items-center rounded-xl bg-gradient-to-br ${j.tint}`}
              >
                <Icon className="h-5 w-5" />
              </span>
              <div>
                <div className="flex items-center gap-1 text-sm font-semibold text-foreground">
                  {j.title}
                  <ArrowRight className="h-3.5 w-3.5 -translate-x-1 opacity-0 transition-all group-hover:translate-x-0 group-hover:opacity-100" />
                </div>
                <div className="mt-0.5 text-xs text-muted-foreground">{j.desc}</div>
              </div>
            </Link>
          );
        })}
      </div>
    </section>
  );
}
