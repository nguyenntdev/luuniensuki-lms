"use client";

import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import {
  ArrowRight,
  Brain,
  Flame,
  Gauge,
  Sparkles,
  Target,
  BookOpen,
} from "lucide-react";

import { usePracticeStore } from "@/stores/practiceStore";
import { useAuthStore } from "@/stores/authStore";

export default function PracticePage() {
  const router = useRouter();
  const { isAuthenticated } = useAuthStore();
  const { stats, loadStats, loadDueCards, error } = usePracticeStore();
  const [isLoadingData, setIsLoadingData] = useState(true);

  useEffect(() => {
    if (!isAuthenticated()) {
      router.push("/login");
      return;
    }

    async function loadData() {
      try {
        await Promise.all([loadStats(), loadDueCards()]);
      } catch (err) {
        console.error("Failed to load practice data:", err);
      } finally {
        setIsLoadingData(false);
      }
    }

    loadData();
  }, [isAuthenticated, router, loadStats, loadDueCards]);

  const masteryRate = useMemo(() => {
    if (!stats?.total_cards) return 0;
    return Math.round((stats.mastered_cards / stats.total_cards) * 100);
  }, [stats]);

  if (isLoadingData) {
    return (
      <main className="mx-auto flex min-h-screen max-w-6xl items-center justify-center px-6 pb-28 pt-8">
        <div className="rounded-3xl border border-border/70 bg-card/70 p-8 text-center shadow-[0_18px_50px_-22px_hsl(0_0%_0%_/_0.45)] backdrop-blur-xl">
          <div className="mx-auto h-12 w-12 animate-spin rounded-full border-b-2 border-primary" />
          <p className="mt-4 text-sm text-muted-foreground">Đang tải dữ liệu ôn tập...</p>
        </div>
      </main>
    );
  }

  if (error) {
    return (
      <main className="mx-auto min-h-screen max-w-6xl px-6 pb-28 pt-8">
        <div className="rounded-3xl border border-destructive/40 bg-destructive/10 p-6 text-destructive">
          <p className="text-sm font-semibold uppercase tracking-wider">Lỗi</p>
          <p className="mt-2 text-sm">{error}</p>
        </div>
      </main>
    );
  }

  const modeCards = [
    {
      title: "Ôn tập thông minh",
      description: "Hệ thống tự chọn thẻ cần ôn theo mức độ quên",
      href: "/practice/smart",
      icon: Brain,
      tone: "primary",
      badge: stats?.due_cards || 0,
    },
    {
      title: "Ôn theo lộ trình",
      description: "Đi lại các họa tiết trong lộ trình học hiện tại",
      href: "/collection",
      icon: BookOpen,
      tone: "info",
    },
    {
      title: "Ôn yếu điểm",
      description: "Tập trung vào câu bạn thường trả lời sai",
      href: "/practice/results?focus=weak",
      icon: Target,
      tone: "warning",
    },
    {
      title: "Thử thách tốc độ",
      description: "Làm nhanh các câu ôn trong phiên rút gọn",
      href: "/practice/smart?mode=speed",
      icon: Gauge,
      tone: "success",
    },
  ];

  return (
    <main className="mx-auto min-h-screen max-w-6xl px-5 pb-28 pt-8 md:px-7 md:pt-10">
      <section className="relative overflow-hidden rounded-3xl border border-border/70 bg-card/70 p-6 shadow-[0_18px_50px_-22px_hsl(0_0%_0%_/_0.45)] backdrop-blur-xl md:p-8">
        <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_10%_10%,hsl(var(--primary)/0.16),transparent_45%)]" />
        <div className="relative">
          <div className="inline-flex items-center gap-2 rounded-full border border-primary/30 bg-primary/10 px-3 py-1 text-xs font-semibold uppercase tracking-[0.12em] text-primary">
            Practice Hub
          </div>
          <h1 className="mt-3 text-3xl font-display font-bold text-foreground">Ôn Tập Chủ Động</h1>
          <p className="mt-2 max-w-2xl text-sm text-muted-foreground md:text-base">
            Hệ thống ôn tập thông minh giúp bạn ghi nhớ họa tiết lâu hơn với các phiên học ngắn,
            rõ mục tiêu, và theo sát tiến độ.
          </p>
        </div>
      </section>

      <section className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard label="Cần ôn ngay" count={stats?.due_cards || 0} tone="warning" icon={Flame} />
        <StatCard label="Đang học" count={stats?.learning_cards || 0} tone="info" icon={Brain} />
        <StatCard label="Đã thành thạo" count={stats?.mastered_cards || 0} tone="success" icon={Sparkles} />
        <StatCard label="Tỷ lệ thành thạo" count={`${masteryRate}%`} tone="primary" icon={Target} />
      </section>

      <section className="mt-8 grid grid-cols-1 gap-5 md:grid-cols-2">
        {modeCards.map((mode) => (
          <PracticeModeCard key={mode.title} {...mode} onClick={() => router.push(mode.href)} />
        ))}
      </section>

      {stats ? (
        <section className="mt-8 rounded-3xl border border-border/70 bg-card/70 p-6 shadow-[0_12px_28px_-16px_rgba(0,0,0,0.55)] backdrop-blur-xl">
          <h2 className="text-lg font-display font-semibold text-foreground">Tổng Quan Phiên Ôn</h2>
          <div className="mt-4 grid grid-cols-2 gap-4 md:grid-cols-4">
            <MetricItem label="Tổng thẻ" value={stats.total_cards} />
            <MetricItem label="Ôn hôm nay" value={stats.reviewed_today} />
            <MetricItem label="Tổng lần ôn" value={stats.total_reviews} />
            <MetricItem label="Đã thành thạo" value={stats.mastered_cards} />
          </div>
        </section>
      ) : null}
    </main>
  );
}

function StatCard({ label, count, tone, icon: Icon }) {
  const toneClasses = {
    warning: "border-warning/40 bg-warning/10 text-warning",
    info: "border-info/40 bg-info/10 text-info",
    success: "border-success/40 bg-success/10 text-success",
    primary: "border-primary/40 bg-primary/10 text-primary",
  };

  return (
    <div className={`rounded-2xl border p-5 ${toneClasses[tone]}`}>
      <div className="flex items-center justify-between">
        <div>
          <p className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">{label}</p>
          <p className="mt-2 text-3xl font-display font-bold">{count}</p>
        </div>
        <Icon className="h-8 w-8" />
      </div>
    </div>
  );
}

function PracticeModeCard({ title, description, icon: Icon, tone, badge, onClick }) {
  const toneClasses = {
    primary: "border-primary/35 bg-primary/10",
    info: "border-info/35 bg-info/10",
    warning: "border-warning/35 bg-warning/10",
    success: "border-success/35 bg-success/10",
  };

  return (
    <button
      onClick={onClick}
      className={`group rounded-3xl border p-6 text-left shadow-[0_10px_24px_-14px_rgba(0,0,0,0.6)] transition duration-300 hover:-translate-y-1 ${toneClasses[tone]}`}
      type="button"
    >
      <div className="flex items-start justify-between gap-4">
        <div className="flex-1">
          <div className="inline-flex h-10 w-10 items-center justify-center rounded-2xl border border-border/60 bg-background/70">
            <Icon className="h-5 w-5 text-foreground" />
          </div>
          <h3 className="mt-3 text-xl font-display font-semibold text-foreground">{title}</h3>
          <p className="mt-2 text-sm text-muted-foreground">{description}</p>
        </div>
        {badge ? (
          <span className="rounded-full border border-destructive/40 bg-destructive/10 px-2.5 py-1 text-xs font-bold text-destructive">
            {badge}
          </span>
        ) : null}
      </div>
      <div className="mt-4 inline-flex items-center gap-1.5 text-sm font-semibold text-primary">
        Bắt đầu phiên
        <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-1" />
      </div>
    </button>
  );
}

function MetricItem({ label, value }) {
  return (
    <div className="rounded-2xl border border-border/60 bg-background/70 p-4">
      <p className="text-xs text-muted-foreground">{label}</p>
      <p className="mt-1 text-2xl font-display font-semibold text-foreground">{value}</p>
    </div>
  );
}
